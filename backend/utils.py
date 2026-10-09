"""Image validation, duplicate detection, and score calculation."""
import hashlib
import os

from fastapi import HTTPException, UploadFile

from models import RawScores, Score

MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_MB", "8")) * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png"}
BONUS_CHANNEL_FOUND = 2

# In-memory only (resets on restart). Fine for a no-database demo.
_seen_hashes: set[str] = set()


def _looks_like_image(data: bytes) -> bool:
    """Check magic bytes so a renamed .exe can't pass as a .jpg."""
    return data.startswith(b"\xff\xd8\xff") or data.startswith(b"\x89PNG\r\n\x1a\n")


async def read_and_validate_image(upload: UploadFile) -> tuple[bytes, str]:
    """Returns (image_bytes, sha256). Raises HTTPException on bad input."""
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Unsupported file type. Please upload a JPG or PNG.")

    data = await upload.read(MAX_IMAGE_BYTES + 1)  # never read more than the limit
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, f"Image too large (max {MAX_IMAGE_BYTES // 1024 // 1024} MB).")
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if not _looks_like_image(data):
        raise HTTPException(415, "That file doesn't look like a valid JPG or PNG.")

    return data, hashlib.sha256(data).hexdigest()


def dedupe_enabled() -> bool:
    return os.getenv("DEDUPE_IMAGES", "true").lower() == "true"


def is_duplicate(image_hash: str) -> bool:
    return dedupe_enabled() and image_hash in _seen_hashes


def remember_image(image_hash: str) -> None:
    _seen_hashes.add(image_hash)


def build_score(raw: RawScores, channel_found: bool = False, slot_matches: bool = True) -> Score:
    """The ONLY place totals are computed. The model never sums points."""
    if not slot_matches:
        return Score(
            problem_validity=0, solution_quality=0, bonus=0, total=0,
            feedback=raw.feedback or "This photo doesn't match the category for this slot.",
        )
    bonus = BONUS_CHANNEL_FOUND if channel_found else 0
    return Score(
        problem_validity=raw.problem_validity,
        solution_quality=raw.solution_quality,
        bonus=bonus,
        total=raw.problem_validity + raw.solution_quality + bonus,
        feedback=raw.feedback,
    )
