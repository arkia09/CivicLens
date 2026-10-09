import type { AnalyzeResult, Quest, SlotId } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// 422 = photo rejected / wrong category, 409 = photo reused, 502/503 = AI trouble.
// The backend's `detail` text is always user-friendly, so we just show it.
async function request<T>(path: string, init: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, init);
  } catch {
    throw new Error("Can't reach the server. Is the backend running?");
  }
  if (!res.ok) {
    let msg = "Something went wrong. Please try again.";
    try {
      const detail = (await res.json()).detail;
      if (typeof detail === "string") msg = detail;
    } catch { /* non-JSON error body */ }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export const getQuest = (location: string) =>
  request<Quest>("/api/quest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location }),
  });

export function analyze(image: File, location: string, slot: SlotId, solution: string) {
  const form = new FormData();
  form.append("image", image);
  form.append("location", location);
  form.append("quest_slot", slot);
  form.append("user_solution", solution);
  return request<AnalyzeResult>("/api/analyze", { method: "POST", body: form });
}