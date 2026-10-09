"""Civic Lens backend. Chunk 2: real Gemma analysis (mock mode still available via USE_MOCK=true).
Run:  uvicorn main:app --reload --port 8000"""
import os
import warnings

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

warnings.filterwarnings("ignore", message=".*protected namespace.*")
load_dotenv()

import gemma  # noqa: E402
from mock_data import get_mock_analysis, get_mock_quest  # noqa: E402  (after load_dotenv)
from models import (  # noqa: E402
    AnalyzeResponse, FindChannelRequest, FindChannelResponse, QuestRequest, QuestResponse, SlotId,
)
from utils import is_duplicate, read_and_validate_image, remember_image  # noqa: E402

def use_mock() -> bool:
    return os.getenv("USE_MOCK", "false").lower() == "true"


app = FastAPI(title="Civic Lens API", version="0.1.0")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/quest", response_model=QuestResponse)
async def create_quest(req: QuestRequest):
    location = req.location.strip()
    if len(location) < 2:
        raise HTTPException(422, "Please enter a location.")
    if use_mock():
        return get_mock_quest(location)
    return await gemma.generate_quest(location)  # falls back to a static template on failure


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    location: str = Form(..., min_length=2, max_length=100),
    quest_slot: SlotId = Form(...),
    user_solution: str = Form(..., min_length=10, max_length=1000),
):
    image_bytes, image_hash = await read_and_validate_image(image)

    if is_duplicate(image_hash):
        raise HTTPException(409, "You've already used this photo. Go find a new problem!")

    if use_mock():
        result = get_mock_analysis(location.strip(), quest_slot, user_solution.strip())
        remember_image(image_hash)
        return result

    try:
        analysis = await gemma.analyze_photo(
            image_bytes, location.strip(), quest_slot, user_solution.strip()
        )
    except gemma.GemmaUnavailable:
        raise HTTPException(503, "The AI service is busy or unavailable. Please try again in a moment.")
    except gemma.GemmaBadOutput:
        raise HTTPException(502, "We couldn't read the AI's answer. Please try again.")

    if not analysis.usable:
        default = (
            "We couldn't find a clear civic problem in this photo. Try another one."
            if not analysis.accepted
            else "This photo doesn't fit this slot's category. Try it in another slot, or find a new problem."
        )
        raise HTTPException(422, analysis.photo_check.rejection_reason or default)

    remember_image(image_hash)  # only photos that were actually scored count as used
    return gemma.to_response(analysis)


@app.post("/api/find-channel", response_model=FindChannelResponse)
def find_channel(req: FindChannelRequest):
    # Chunk 4: replace with SerpApi search (+ cache, .gov.in / .nic.in priority).
    return FindChannelResponse(
        found=True,
        title="Mock municipal grievance portal",
        url="https://example.gov.in/grievance",
        source="mock",
        bonus=2,
    )
