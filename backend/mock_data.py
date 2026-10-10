"""Canned responses for USE_MOCK=true, plus the static quest used if Gemma fails."""
from models import (
    AnalyzeResponse, Authority, Complaint, FindChannelResponse, Issue, QuestResponse, QuestSlot,
    RawScores, SlotId,
)
from utils import build_score


def get_mock_quest(location: str) -> QuestResponse:
    return QuestResponse(
        briefing=(
            f"Take a 15-minute walk around {location}. Leave your phone in your pocket "
            "until you spot something that needs fixing. Find three problems, one in each category."
        ),
        slots=[
            QuestSlot(slot="safety_infrastructure", title="Safety & infrastructure",
                      hint="Look at the road surface, street lights, or broken fences."),
            QuestSlot(slot="cleanliness_environment", title="Cleanliness & environment",
                      hint="Look for garbage piles, clogged drains, or standing water."),
            QuestSlot(slot="accessibility_public_space", title="Accessibility & public space",
                      hint="Check footpaths, ramps, and crossings. Could a wheelchair user get past?"),
        ],
    )


_MOCK: dict[SlotId, dict] = {
    "safety_infrastructure": dict(
        issue=Issue(type="pothole", severity="high",
                    description="A large pothole is present on the roadway, deep enough to damage tyres.",
                    public_impact=["vehicle safety", "pedestrian safety"]),
        authority=Authority(type="Municipal road authority",
                            reason="Road surface maintenance falls under the local municipal road department."),
        raw=RawScores(problem_validity=9, solution_quality=7,
                      feedback="Clear, real problem. Your fix is practical; also name who should be contacted."),
        action_plan=["Photograph the pothole with a nearby landmark for reference.",
                     "Report it through the municipal grievance channel.",
                     "Include exact location, photo, and the safety risk.",
                     "If unresolved after 7 days, follow up using the same channel."],
        subject="Complaint regarding dangerous pothole",
    ),
    "cleanliness_environment": dict(
        issue=Issue(type="garbage_accumulation", severity="medium",
                    description="Uncollected garbage is piled beside the road, spilling onto the pavement.",
                    public_impact=["public health", "odour and pests"]),
        authority=Authority(type="Sanitation department",
                            reason="Waste collection is handled by the local civic sanitation authority."),
        raw=RawScores(problem_validity=8, solution_quality=6,
                      feedback="Good catch. Suggest a collection schedule fix rather than only a one-off clean-up."),
        action_plan=["Photograph the pile and the surrounding area.",
                     "Report it to the sanitation department.",
                     "Mention how long it has been there and any health risk.",
                     "Escalate through the same channel if not cleared."],
        subject="Complaint regarding uncollected garbage",
    ),
    "accessibility_public_space": dict(
        issue=Issue(type="blocked_footpath", severity="high",
                    description="The pedestrian footpath is obstructed, forcing people onto the roadway.",
                    public_impact=["pedestrian safety", "accessibility"]),
        authority=Authority(type="Municipal civic authority",
                            reason="Footpaths are public infrastructure managed by the local civic body."),
        raw=RawScores(problem_validity=8, solution_quality=8,
                      feedback="Strong and specific fix. Mention wheelchair users in your report."),
        action_plan=["Photograph the obstruction and where pedestrians are forced to walk.",
                     "Report it through the civic grievance channel.",
                     "Describe the impact on elderly and wheelchair users.",
                     "Follow up if the obstruction remains."],
        subject="Complaint regarding blocked pedestrian footpath",
    ),
}


def get_mock_analysis(location: str, slot: SlotId, user_solution: str) -> AnalyzeResponse:
    m = _MOCK[slot]
    issue: Issue = m["issue"]
    return AnalyzeResponse(
        issue=issue,
        authority=m["authority"],
        score=build_score(m["raw"], channel_found=False),
        action_plan=m["action_plan"],
        complaint=Complaint(
            subject=m["subject"],
            body=(f"A {issue.type.replace('_', ' ')} has been observed at {location}. "
                  f"{issue.description}\n\nSuggested resolution: {user_solution}\n\n"
                  "I have attached a photograph. I request that the relevant authority "
                  "inspect the location and take appropriate action."),
        ),
    )


def get_mock_channel() -> FindChannelResponse:
    return FindChannelResponse(
        found=True, title="Mock municipal grievance portal",
        url="https://example.gov.in/grievance", source="mock", bonus=2,
    )
