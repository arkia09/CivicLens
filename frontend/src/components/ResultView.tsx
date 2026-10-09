import { useState } from "react";
import type { AnalyzeResult } from "../types";

const SEVERITY = {
  low: "bg-yellow-100 text-yellow-800",
  medium: "bg-orange-100 text-orange-800",
  high: "bg-red-100 text-red-800",
};

export default function ResultView({ r }: { r: AnalyzeResult }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(`Subject: ${r.complaint.subject}\n\n${r.complaint.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard blocked by browser */ }
  }

  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold capitalize">{r.issue.type.replace(/_/g, " ")}</span>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY[r.issue.severity]}`}>
          {r.issue.severity} severity
        </span>
      </div>
      <p>{r.issue.description}</p>
      <div className="flex flex-wrap gap-1">
        {r.issue.public_impact.map((p) => (
          <span key={p} className="rounded bg-slate-100 px-2 py-0.5 text-xs">{p}</span>
        ))}
      </div>

      <div className="rounded-lg bg-green-50 p-3">
        <div className="flex justify-between font-medium">
          <span>Problem {r.score.problem_validity}/10 · Your fix {r.score.solution_quality}/10</span>
          <span>{r.score.total} pts</span>
        </div>
        <p className="mt-1 text-slate-600">{r.score.feedback}</p>
      </div>

      <div>
        <p className="font-medium">Who handles this</p>
        <p className="text-slate-600"><b>{r.authority.type}.</b> {r.authority.reason}</p>
      </div>

      <div>
        <p className="font-medium">What you can do</p>
        <ol className="list-decimal space-y-1 pl-5 text-slate-600">
          {r.action_plan.map((s) => <li key={s}>{s}</li>)}
        </ol>
      </div>

      <div className="rounded-lg border border-slate-200 p-3">
        <p className="font-medium">Subject: {r.complaint.subject}</p>
        <p className="mt-2 whitespace-pre-wrap break-words text-slate-600">{r.complaint.body}</p>
        <button onClick={copy} className="mt-3 rounded bg-slate-800 px-3 py-1.5 text-white">
          {copied ? "Copied ✓" : "Copy complaint"}
        </button>
      </div>
    </div>
  );
}
