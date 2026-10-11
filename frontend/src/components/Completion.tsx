import { useState } from "react";
import type { AnalyzeResult, ChannelResult, Quest, SlotId } from "../types";
import { channelBonus, slotPoints } from "../points";
import Mascot from "./Mascot";

interface Props {
  location: string;
  quest: Quest;
  results: Partial<Record<SlotId, AnalyzeResult>>;
  channels: Partial<Record<SlotId, ChannelResult>>;
  points: number;
}

export default function Completion({ location, quest, results, channels, points }: Props) {
  const [copied, setCopied] = useState(false);

  const rows = quest.slots.flatMap((s) => {
    const r = results[s.slot];
    if (!r) return [];
    const c = channels[s.slot];
    return [{
      key: s.slot,
      category: s.title,
      issue: r.issue.type.replace(/_/g, " "),
      pts: slotPoints(r, c),
      bonus: channelBonus(c),
      url: c?.found ? c.url : null,
    }];
  });

  async function copy() {
    const lines = rows.map((x, i) =>
      `${i + 1}. ${x.issue} (${x.category}): ${x.pts} pts${x.bonus ? ` incl. +${x.bonus} channel bonus` : ""}` +
      (x.url ? `\n   Report at: ${x.url}` : ""));
    const text = `Civic Lens · ${location}\nGrass Touched 🌱 3/3 problems found · ${points} points\n\n${lines.join("\n")}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard blocked by browser */ }
  }

  return (
    <section className="on-light rounded-2xl bg-flash p-4 text-ink sm:p-5">
      <div className="flex items-center gap-3">
        <Mascot mood="cheer" className="size-20 shrink-0" />
        <div>
          <h2 className="font-display text-2xl font-extrabold leading-tight">Grass Touched 🌱</h2>
          <p>3/3 problems found, {points} points</p>
        </div>
      </div>
      <ul className="mt-4 divide-y divide-ink/15 rounded-xl bg-paper/70 text-sm">
        {rows.map((x) => (
          <li key={x.key} className="flex items-center justify-between gap-3 p-3">
            <span className="min-w-0"><b className="capitalize">{x.issue}</b>
              <span className="block text-xs text-muted">{x.category}</span></span>
            <span className="shrink-0 font-display text-base font-bold">{x.pts} pts</span>
          </li>
        ))}
      </ul>
      <button onClick={copy} className="btn btn-ink mt-4 w-full">{copied ? "Copied ✓" : "Copy summary"}</button>
    </section>
  );
}
