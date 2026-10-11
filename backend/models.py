"""Pydantic models. These ARE the API contract: the frontend types must match."""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

SlotId = Literal[
    "safety_infrastructure",
    "cleanliness_environment",
    "accessibility_public_space",
]
Severity = Literal["low", "medium", "high"]


class QuestRequest(BaseModel):
    location: str = Field(min_length=2, max_length=100)


class QuestSlot(BaseModel):
    slot: SlotId
    title: str
    hint: str


class QuestResponse(BaseModel):
    briefing: str
    slots: list[QuestSlot]


class Issue(BaseModel):
    type: str
    severity: Severity
    description: str
    public_impact: list[str]

    @field_validator("severity", mode="before")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class Authority(BaseModel):
    type: str
    reason: str


class RawScores(BaseModel):
    """What the model is allowed to return. No total, no bonus."""
    problem_validity: int = Field(ge=0, le=10)
    solution_quality: int = Field(ge=0, le=10)
    feedback: str

    @field_validator("problem_validity", "solution_quality", mode="before")
    @classmethod
    def _round_and_clamp(cls, v):
        """Models sometimes answer 7.5 or 11. Round and clamp instead of failing."""
        try:
            return max(0, min(10, round(float(v))))
        except (TypeError, ValueError):
            return v


class Score(BaseModel):
    problem_validity: int = Field(ge=0, le=10)
    solution_quality: int = Field(ge=0, le=10)
    bonus: int = Field(ge=0, le=2)
    total: int  # always computed by the backend
    feedback: str


class Complaint(BaseModel):
    subject: str
    body: str


class AnalyzeResponse(BaseModel):
    issue: Issue
    authority: Authority
    score: Score
    action_plan: list[str]
    complaint: Complaint


# ---------- /api/find-channel ----------
class FindChannelRequest(BaseModel):
    location: str = Field(min_length=2, max_length=100)
    issue_type: str = Field(min_length=2, max_length=100)
    authority: str = Field(min_length=2, max_length=100)


class FindChannelResponse(BaseModel):
    found: bool
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    bonus: int = 0  # +2 when found; frontend adds this to the slot's total


class PhotoCheck(BaseModel):
    is_real_outdoor_photo: bool
    shows_civic_problem: bool
    matches_slot: bool
    rejection_reason: Optional[str] = None


class GemmaAnalysis(BaseModel):
    photo_check: PhotoCheck
    issue: Optional[Issue] = None
    authority: Optional[Authority] = None
    scores: Optional[RawScores] = None
    action_plan: Optional[list[str]] = None
    complaint: Optional[Complaint] = None

    @property
    def accepted(self) -> bool:
        """A real outdoor photo that shows a civic problem."""
        return self.photo_check.is_real_outdoor_photo and self.photo_check.shows_civic_problem

    @property
    def usable(self) -> bool:
        """Accepted AND in the right category: the only case we score."""
        return self.accepted and self.photo_check.matches_slot

    @model_validator(mode="before")
    @classmethod
    def _drop_details_unless_usable(cls, data):
        """If the photo is rejected, ignore whatever half-filled details the model sent
        (e.g. a scores object full of nulls) instead of failing validation."""
        if isinstance(data, dict):
            pc = data.get("photo_check")
            ok = isinstance(pc, dict) and all(
                pc.get(k) is True for k in ("is_real_outdoor_photo", "shows_civic_problem", "matches_slot")
            )
            if not ok:
                for k in ("issue", "authority", "scores", "action_plan", "complaint"):
                    data[k] = None
        return data

    @model_validator(mode="after")
    def _require_details_when_usable(self):
        if self.usable and not all(
            [self.issue, self.authority, self.scores, self.action_plan, self.complaint]
        ):
            raise ValueError("Photo accepted but analysis fields are missing")
        return self

class GemmaQuest(BaseModel):
    briefing: str
    hints: dict[SlotId, str]