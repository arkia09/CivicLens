// Mirrors backend/models.py. Keep in sync.
export type SlotId =
  | "safety_infrastructure"
  | "cleanliness_environment"
  | "accessibility_public_space";

export interface QuestSlot { slot: SlotId; title: string; hint: string }
export interface Quest { briefing: string; slots: QuestSlot[] }

export interface Score {
  problem_validity: number;
  solution_quality: number;
  bonus: number;
  total: number;
  feedback: string;
}

export interface AnalyzeResult {
  issue: { type: string; severity: "low" | "medium" | "high"; description: string; public_impact: string[] };
  authority: { type: string; reason: string };
  score: Score;
  action_plan: string[];
  complaint: { subject: string; body: string };
}
