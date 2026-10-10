import type { AnalyzeResult, ChannelResult, Quest } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (res.ok) return res.json();
  let msg = "Something went wrong. Please try again.";
  try {
    const body = await res.json();
    if (typeof body.detail === "string") msg = body.detail;
  } catch { /* non-JSON error body */ }
  throw new Error(msg);
}

export async function getQuest(location: string): Promise<Quest> {
  const res = await fetch(`${BASE}/api/quest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location }),
  });
  return handle<Quest>(res);
}

export async function analyze(
  image: File,
  location: string,
  quest_slot: string,
  user_solution: string
): Promise<AnalyzeResult> {
  const form = new FormData();
  form.append("image", image);
  form.append("location", location);
  form.append("quest_slot", quest_slot);
  form.append("user_solution", user_solution);
  const res = await fetch(`${BASE}/api/analyze`, { method: "POST", body: form });
  return handle<AnalyzeResult>(res);
}

export async function findChannel(
  location: string,
  issue_type: string,
  authority: string
): Promise<ChannelResult> {
  const res = await fetch(`${BASE}/api/find-channel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location, issue_type, authority }),
  });
  return handle<ChannelResult>(res);
}
