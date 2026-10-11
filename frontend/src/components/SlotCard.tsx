import { useEffect, useMemo, useRef, useState } from "react";
import { analyze } from "../api";
import type { AnalyzeResult, ChannelResult, QuestSlot } from "../types";
import ResultView from "./ResultView";
import Mascot from "./Mascot";

const MAX_MB = 8;

interface Props {
  slot: QuestSlot;
  location: string;
  result?: AnalyzeResult;
  channel?: ChannelResult;
  onDone: (r: AnalyzeResult) => void;
  onChannel: (c: ChannelResult) => void;
}

function CameraIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" className={className}>
      <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  );
}

export default function SlotCard({ slot, location, result, channel, onDone, onChannel }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [solution, setSolution] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const camRef = useRef<HTMLInputElement>(null);
  const galRef = useRef<HTMLInputElement>(null);

  const preview = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function pick(input: HTMLInputElement) {
    const f = input.files?.[0];
    input.value = ""; // lets the same photo be picked again
    setError("");
    if (!f) return;
    if (!["image/jpeg", "image/png"].includes(f.type)) return setError("Please choose a JPG or PNG photo.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Photo is too large (max ${MAX_MB} MB).`);
    setFile(f);
  }

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      onDone(await analyze(file, location, slot.slot, solution.trim()));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const ready = !!file && solution.trim().length >= 10 && !loading;
  const missing = !file ? "Add a photo to continue." : solution.trim().length < 10 ? "Describe your fix (at least 10 characters)." : "";

  return (
    <section className="on-light relative overflow-hidden rounded-2xl bg-paper p-4 text-ink sm:p-5">
      {loading && <span className="flash-once" aria-hidden="true" />}

      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-bold leading-tight">{slot.title}</h2>
          <p className="mt-1 text-muted">{slot.hint}</p>
        </div>
        {result && <span className="shrink-0 rounded-full bg-moss px-3 py-1 text-sm font-medium text-paper">✓ Done</span>}
      </div>

      {result ? (
        <ResultView r={result} location={location} channel={channel} onChannel={onChannel} />
      ) : (
        <div className="space-y-4">
          <div className="viewfinder grid min-h-48 place-items-center rounded-lg bg-ink/5 p-5 text-center">
            {preview ? (
              <img src={preview} alt="Your photo" className="max-h-64 rounded object-contain" />
            ) : (
              <div className="text-muted">
                <CameraIcon className="mx-auto size-10" />
                <p className="mt-2 font-medium text-ink">Photograph the problem</p>
                <p className="text-sm">Get close enough to see it clearly.</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => camRef.current?.click()} disabled={loading} className="btn btn-ink">
              {file ? "Retake photo" : "Take photo"}
            </button>
            <button type="button" onClick={() => galRef.current?.click()} disabled={loading} className="btn btn-line">
              Choose from gallery
            </button>
            <input ref={camRef} type="file" accept="image/jpeg,image/png" capture="environment" className="hidden"
              onChange={(e) => pick(e.target)} />
            <input ref={galRef} type="file" accept="image/jpeg,image/png" className="hidden"
              onChange={(e) => pick(e.target)} />
          </div>

          <div>
            <label htmlFor={`fix-${slot.slot}`} className="mb-1.5 block font-medium">How would you fix it?</label>
            <textarea id={`fix-${slot.slot}`} value={solution} onChange={(e) => setSolution(e.target.value)}
              maxLength={1000} rows={3} placeholder="Be specific: who should do what, and how." className="field" />
          </div>

          {error && <p role="alert" className="rounded-lg bg-red-100 p-3 text-sm text-red-900">{error}</p>}

          {loading ? (
            <div role="status" className="flex items-center gap-3 rounded-xl bg-moss p-3 text-paper">
              <Mascot mood="wait" className="size-14 shrink-0" />
              <div>
                <p className="font-display font-bold">Analyzing your photo</p>
                <p className="text-sm text-paper/80">Scoring it and drafting your complaint. This takes about 20 seconds.</p>
              </div>
            </div>
          ) : (
            <div>
              <button onClick={submit} disabled={!ready} className="btn btn-flash w-full">Submit for scoring</button>
              {missing && <p className="mt-2 text-center text-sm text-muted">{missing}</p>}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
