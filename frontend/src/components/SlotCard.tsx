import { useEffect, useMemo, useState } from "react";
import { analyze } from "../api";
import type { AnalyzeResult, ChannelResult, QuestSlot } from "../types";
import ResultView from "./ResultView";

const MAX_MB = 8;

interface Props {
  slot: QuestSlot;
  location: string;
  result?: AnalyzeResult;
  channel?: ChannelResult;
  onDone: (r: AnalyzeResult) => void;
  onChannel: (c: ChannelResult) => void;
}

export default function SlotCard({ slot, location, result, channel, onDone, onChannel }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [solution, setSolution] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const preview = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function pick(f?: File) {
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

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h2 className="font-semibold">{slot.title}</h2>
          <p className="text-sm text-slate-500">{slot.hint}</p>
        </div>
        {result && <span className="shrink-0 rounded-full bg-green-600 px-2 py-0.5 text-xs text-white">✓ Done</span>}
      </div>

      {result ? (
        <ResultView r={result} location={location} channel={channel} onChannel={onChannel} />
      ) : (
        <div className="space-y-3">
          <label className="block cursor-pointer rounded-lg border-2 border-dashed border-slate-300 p-3 text-center text-sm text-slate-500">
            {preview ? (
              <img src={preview} alt="Your photo" className="mx-auto max-h-56 rounded" />
            ) : (
              "Tap to take or choose a photo"
            )}
            <input type="file" accept="image/jpeg,image/png" className="hidden"
              onChange={(e) => pick(e.target.files?.[0])} />
          </label>
          <textarea value={solution} onChange={(e) => setSolution(e.target.value)} maxLength={1000} rows={3}
            placeholder="How would you fix this problem? Be specific (min 10 characters)."
            className="w-full rounded-lg border border-slate-300 p-2 text-sm" />
          {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
          <button onClick={submit} disabled={!ready}
            className="w-full rounded-lg bg-green-600 py-2 font-medium text-white disabled:opacity-40">
            {loading ? "Analyzing… this can take ~20 seconds" : "Submit for scoring"}
          </button>
        </div>
      )}
    </section>
  );
}
