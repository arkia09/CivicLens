"""Everything that talks to Gemma. The rest of the app never imports the SDK."""
import asyncio
import io
import json
import logging
import os
import re
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from mock_data import get_mock_quest
from models import (
    AnalyzeResponse, GemmaAnalysis, GemmaQuest, QuestResponse, QuestSlot, SlotId,
)
from prompts import (
    ANALYZE_SYSTEM, ANALYZE_USER, QUEST_SYSTEM, QUEST_USER, RETRY_SUFFIX, SLOT_DEFINITIONS,
)
from utils import build_score

log = logging.getLogger("civic-lens.gemma")
T = TypeVar("T", bound=BaseModel)

TIMEOUT_SECONDS = 60
MAX_IMAGE_SIDE = 1280  # phones shoot 4000px+; smaller = faster and cheaper

SLOT_TITLES = {
    "safety_infrastructure": "Safety & infrastructure",
    "cleanliness_environment": "Cleanliness & environment",
    "accessibility_public_space": "Accessibility & public space",
}


class GemmaUnavailable(Exception):
    """API key missing, network error, quota, timeout."""


class GemmaBadOutput(Exception):
    """Model replied, but not with usable JSON, even after one retry."""


# ---------- helpers ----------
def clean_user_text(text: str) -> str:
    """Stop users closing our data tags to smuggle in instructions."""
    return re.sub(r"</?\s*(user_solution|location)\s*>", "", text, flags=re.I).strip()


def extract_json(text: str) -> dict:
    """Tolerates ```json fences and chatter before/after the object."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start : end + 1])


def prepare_image(data: bytes) -> tuple[bytes, str]:
    """Fix phone rotation, shrink, re-encode as JPEG. Falls back to the original on any problem."""
    try:
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        out = io.BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=85)
        return out.getvalue(), "image/jpeg"
    except Exception:
        mime = "image/png" if data.startswith(b"\x89PNG") else "image/jpeg"
        return data, mime


# ---------- the only functions that touch the network ----------
async def _call_model(client, model: str, contents: list, config) -> str:
    resp = await asyncio.wait_for(
        client.aio.models.generate_content(model=model, contents=contents, config=config),
        timeout=TIMEOUT_SECONDS,
    )
    return resp.text or ""


def _models_to_try() -> list[str]:
    primary = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it").strip()
    fallback = os.getenv("GEMMA_FALLBACK_MODEL", "gemma-4-31b-it").strip()
    return [primary] + ([fallback] if fallback and fallback != primary else [])


async def _generate(contents: list, system: str, temperature: float) -> str:
    """Tries the primary model, then the fallback if Google returns an error (500/503/timeout)."""
    api_key = os.getenv("GEMMA_API_KEY")
    if not api_key:
        raise GemmaUnavailable("GEMMA_API_KEY is not set")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    config_kwargs = dict(
        system_instruction=system,
        temperature=temperature,
        max_output_tokens=2048,
    )
    thinking = os.getenv("GEMMA_THINKING", "minimal").strip()
    if thinking:  # leave GEMMA_THINKING blank in .env to omit thinking_config entirely
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)
    config = types.GenerateContentConfig(**config_kwargs)

    last_err: Exception | None = None
    for model in _models_to_try():
        try:
            return await _call_model(client, model, contents, config)
        except Exception as e:  # SDK errors: quota, 5xx, network, timeout
            log.warning("Gemma model %s failed: %s", model, str(e)[:200])
            last_err = e
    raise GemmaUnavailable(str(last_err)) from last_err


async def _call_validated(model_cls: Type[T], contents: list, system: str, temperature: float) -> T:
    """Call Gemma, parse JSON, validate with Pydantic. One retry on malformed output."""
    last_err: Exception | None = None
    for attempt in (1, 2):
        sys_prompt = system if attempt == 1 else system + RETRY_SUFFIX
        text = await _generate(contents, sys_prompt, temperature)
        try:
            return model_cls.model_validate(extract_json(text))
        except (ValueError, ValidationError) as e:  # JSONDecodeError is a ValueError
            last_err = e
            log.warning("Malformed Gemma output (attempt %d): %s | raw: %.300s", attempt, e, text)
    raise GemmaBadOutput(str(last_err))


# ---------- public API ----------
async def generate_quest(location: str) -> QuestResponse:
    """Text-only. Falls back to the static template, because a quest should never fail to load."""
    prompt = QUEST_USER.format(
        location=clean_user_text(location),
        safety=SLOT_DEFINITIONS["safety_infrastructure"],
        clean=SLOT_DEFINITIONS["cleanliness_environment"],
        access=SLOT_DEFINITIONS["accessibility_public_space"],
    )
    try:
        q = await _call_validated(GemmaQuest, [prompt], QUEST_SYSTEM, temperature=0.8)
    except (GemmaUnavailable, GemmaBadOutput):
        log.warning("Quest generation failed, using static template")
        return get_mock_quest(location)

    return QuestResponse(
        briefing=q.briefing,
        slots=[QuestSlot(slot=s, title=SLOT_TITLES[s], hint=q.hints[s]) for s in SLOT_TITLES],
    )


async def analyze_photo(
    image_bytes: bytes, location: str, slot: SlotId, user_solution: str
) -> GemmaAnalysis:
    from google.genai import types

    img, mime = prepare_image(image_bytes)
    prompt = ANALYZE_USER.format(
        slot_definition=SLOT_DEFINITIONS[slot],
        location=clean_user_text(location),
        user_solution=clean_user_text(user_solution),
    )
    contents = [types.Part.from_bytes(data=img, mime_type=mime), prompt]
    return await _call_validated(GemmaAnalysis, contents, ANALYZE_SYSTEM, temperature=0.2)


def to_response(a: GemmaAnalysis) -> AnalyzeResponse:
    """Backend computes the score. Only called for usable (accepted + right category) photos."""
    assert a.usable and a.issue and a.authority and a.scores and a.complaint and a.action_plan
    return AnalyzeResponse(
        issue=a.issue,
        authority=a.authority,
        score=build_score(a.scores, channel_found=False),
        action_plan=a.action_plan,
        complaint=a.complaint,
    )
