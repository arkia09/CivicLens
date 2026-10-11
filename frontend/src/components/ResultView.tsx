import { useState } from "react";
import type { AnalyzeResult, ChannelResult } from "../types";
import { channelBonus, slotPoints } from "../points";
import ChannelFinder from "./ChannelFinder";
import Mascot from "./Mascot";

const SEVERITY = {
  low: "bg-amber-200 text-amber-900",
  medium: "bg-orange-200 text-orange-900",
  high: "bg-red-200 text-red-900",
};

interface Props {
  r: AnalyzeResult;
  location: string;
  channel?: ChannelResult;
  onChannel: (c: ChannelResult) => void;
}

export default function ResultView({ r, location, channel, onChannel }: Props) {
  const bonus = channelBonus(channel);
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(`Subject: ${r.complaint.subject}\n\n${r.complaint.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard blocked by browser */ }
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-display text-lg font-bold capitalize">{r.issue.type.replace(/_/g, " ")}</h3>
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${SEVERITY[r.issue.severity]}`}>
            {r.issue.severity} severity
          </span>
        </div>
        <p>{r.issue.description}</p>
        <div className="flex flex-wrap gap-1.5">
          {r.issue.public_impact.map((p) => (
            <span key={p} className="rounded-full bg-ink/10 px-2.5 py-1 text-xs">{p}</span>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="stamp shrink-0 rounded-lg border-[3px] border-ink bg-flash px-3.5 py-2 text-center">
            <p className="font-display text-3xl font-extrabold leading-none">{slotPoints(r, channel)}</p>
            <p className="text-xs font-bold">points</p>
          </div>
          <div className="text-sm leading-relaxed">
            <p>Problem <b>{r.score.problem_validity}/10</b></p>
            <p>Your fix <b>{r.score.solution_quality}/10</b></p>
            {bonus > 0 && <p>Channel bonus <b>+{bonus}</b></p>}
          </div>
        </div>
        <div className="flex items-start gap-3">
          <Mascot className="size-14 shrink-0" />
          <p className="bubble bubble-sand text-sm">{r.score.feedback}</p>
        </div>
      </div>

      <div>
        <h3 className="font-display font-bold">Who handles this</h3>
        <p className="mt-1 text-muted"><b className="text-ink">{r.authority.type}.</b> {r.authority.reason}</p>
      </div>

      <ChannelFinder r={r} location={location} channel={channel} onChannel={onChannel} />

      <div>
        <h3 className="font-display font-bold">What you can do</h3>
        <ol className="mt-1 list-decimal space-y-1.5 pl-5 text-muted marker:font-bold marker:text-ink">
          {r.action_plan.map((s) => <li key={s}>{s}</li>)}
        </ol>
      </div>

      <div className="rounded-xl border-2 border-dashed border-ink/30 p-4">
        <h3 className="font-display font-bold">Complaint draft, ready to send</h3>
        <p className="mt-2 font-medium">Subject: {r.complaint.subject}</p>
        <p className="mt-2 whitespace-pre-wrap break-words text-muted">{r.complaint.body}</p>
        <button onClick={copy} className="btn btn-ink mt-4 w-full">{copied ? "Copied ✓" : "Copy complaint"}</button>
      </div>
    </div>
  );
}
