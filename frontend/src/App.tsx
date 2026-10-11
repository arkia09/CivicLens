import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { getQuest } from "./api";
import type { AnalyzeResult, ChannelResult, Quest, SlotId } from "./types";
import { slotPoints } from "./points";
import SlotCard from "./components/SlotCard";
import Completion from "./components/Completion";
import Mascot from "./components/Mascot";

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
    <main className="min-h-screen bg-forest text-paper">
      <div className="mx-auto max-w-3xl space-y-5 px-4 pb-12 pt-5 sm:px-6">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mascot className="size-11" />
            <p className="font-display text-2xl font-extrabold">Civic Lens</p>
          </div>
          {quest && (
            <button onClick={() => { setSaved(EMPTY); setInput(""); }}
              className="min-h-11 rounded-lg px-3 text-sm text-paper/80 underline underline-offset-4 hover:text-paper">
              Start over
            </button>
          )}
        </header>

        {!quest ? (
          <div className="grid items-center gap-6 pt-2 md:grid-cols-[1fr_1.1fr] md:gap-10 md:pt-10">
            <div className="grid place-items-center">
              <div className="col-start-1 row-start-1 size-52 rounded-full bg-canopy md:size-80" />
              <Mascot mood={loading ? "wait" : "hero"}
                className="relative col-start-1 row-start-1 size-48 md:size-72" />
            </div>
            <form onSubmit={start} className="space-y-4">
              <h1 className="font-display text-4xl font-extrabold leading-[1.05] md:text-5xl">
                Find 3 problems in your neighbourhood.
              </h1>
              <p className="max-w-md text-lg text-paper/80">
                Photograph each one, say how you'd fix it, and get a score, the right authority and a complaint you can send.
              </p>
              <div>
                <label htmlFor="area" className="mb-1.5 block text-sm font-medium text-paper/80">Your area</label>
                <input id="area" value={input} onChange={(e) => setInput(e.target.value)} maxLength={100}
                  placeholder="e.g. Rohini, Delhi" className="field" />
              </div>
              {error && (
                <p role="alert" className="rounded-lg border border-red-300/40 bg-red-950/50 p-3 text-sm text-red-100">{error}</p>
              )}
              <button disabled={input.trim().length < 2 || loading} className="btn btn-flash w-full">
                {loading ? "Preparing your quest…" : "Start my quest"}
              </button>
            </form>
          </div>
        ) : (
          <div className="mx-auto w-full max-w-2xl space-y-5">
            <h1 className="sr-only">Your quest in {location}</h1>

            <section className="rounded-2xl bg-canopy p-4 sm:p-5">
              <div className="flex items-start gap-4">
                <Mascot className="size-20 shrink-0" />
                <p className="bubble text-ink">{quest.briefing}</p>
              </div>
              <div className="mt-5" role="progressbar" aria-label="Problems found"
                aria-valuemin={0} aria-valuemax={3} aria-valuenow={done}>
                <div className="grid grid-cols-3 gap-2">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className={`h-2.5 rounded-full transition-colors ${i < done ? "bg-flash" : "bg-paper/20"}`} />
                  ))}
                </div>
                <div className="mt-2 flex justify-between text-sm text-paper/80">
                  <span>{done} of 3 found</span>
                  <span className="font-display text-base font-bold text-flash">{points} pts</span>
                </div>
              </div>
            </section>

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
          </div>
        )}
      </div>
    </main>
  );
}
