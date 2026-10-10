import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { getQuest } from "./api";
import type { AnalyzeResult, ChannelResult, Quest, SlotId } from "./types";
import { slotPoints } from "./points";
import SlotCard from "./components/SlotCard";
import Completion from "./components/Completion";

const KEY = "civic-lens-v1";
type Saved = {
  location: string;
  quest: Quest | null;
  results: Partial<Record<SlotId, AnalyzeResult>>;
  channels: Partial<Record<SlotId, ChannelResult>>;
};
const EMPTY: Saved = { location: "", quest: null, results: {}, channels: {} };

function load(): Saved {
  try { return { ...EMPTY, ...JSON.parse(localStorage.getItem(KEY) ?? "{}") }; } catch { return EMPTY; }
}

export default function App() {
  const [saved, setSaved] = useState<Saved>(load);
  const [input, setInput] = useState(saved.location);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch { /* storage unavailable */ }
  }, [saved]);

  const { quest, results, channels, location } = saved;
  const done = Object.keys(results).length;
  const points = (Object.keys(results) as SlotId[]).reduce(
    (n, id) => n + (results[id] ? slotPoints(results[id], channels[id]) : 0), 0);

  async function start(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const place = input.trim();
      setSaved({ ...EMPTY, location: place, quest: await getQuest(place) });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-green-50 text-slate-800">
      <div className="mx-auto max-w-2xl space-y-4 px-4 py-8">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">🌱 Civic Lens</h1>
          {quest && (
            <button onClick={() => { setSaved(EMPTY); setInput(""); }} className="text-sm text-slate-500 underline">
              Start over
            </button>
          )}
        </header>

        {!quest ? (
          <form onSubmit={start} className="space-y-3 rounded-xl bg-white p-4 shadow-sm">
            <p>Go outside. Find 3 real problems in your neighbourhood. Get scored for fixing them.</p>
            <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={100}
              placeholder="Your area, e.g. Rohini, Delhi" className="w-full rounded-lg border border-slate-300 p-2" />
            {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
            <button disabled={input.trim().length < 2 || loading}
              className="w-full rounded-lg bg-green-600 py-2 font-medium text-white disabled:opacity-40">
              {loading ? "Preparing your quest…" : "Start my quest"}
            </button>
          </form>
        ) : (
          <>
            <div className="rounded-xl bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-600">{quest.briefing}</p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full bg-green-600 transition-all" style={{ width: `${(done / 3) * 100}%` }} />
              </div>
              <p className="mt-1 text-xs text-slate-500">{done}/3 problems found · {points} points</p>
            </div>

            {done === 3 && <Completion location={location} quest={quest} results={results}
              channels={channels} points={points} />}

            {quest.slots.map((s) => (
              <SlotCard key={s.slot} slot={s} location={location} result={results[s.slot]}
                channel={channels[s.slot]}
                onDone={(r) => setSaved((p) => ({ ...p, results: { ...p.results, [s.slot]: r } }))}
                // ignored if the user pressed "Start over" while the search was running
                onChannel={(c) => setSaved((p) => p.results[s.slot]
                  ? { ...p, channels: { ...p.channels, [s.slot]: c } } : p)} />
            ))}
          </>
        )}
      </div>
    </main>
  );
}
