import { useState } from "react";
import type { AnalyzeResult, ChannelResult, Quest, SlotId } from "../types";
import { channelBonus, slotPoints } from "../points";

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
    <div className="space-y-3 rounded-xl bg-green-600 p-4 text-white">
      <div className="text-center">
        <p className="text-xl font-bold">Grass Touched 🌱</p>
        <p>3/3 problems found · {points} points</p>
      </div>
      <ul className="space-y-1 rounded-lg bg-white/15 p-3 text-sm">
        {rows.map((x) => (
          <li key={x.key} className="flex justify-between gap-2">
            <span className="min-w-0"><b className="capitalize">{x.issue}</b>
              <span className="block text-xs opacity-80">{x.category}</span></span>
            <span className="shrink-0 font-medium">{x.pts} pts</span>
          </li>
        ))}
      </ul>
      <button onClick={copy} className="w-full rounded-lg bg-white py-2 font-medium text-green-700">
        {copied ? "Copied ✓" : "Copy summary"}
      </button>
    </div>
  );
}
