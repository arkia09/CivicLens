import { useState } from "react";
import { findChannel } from "../api";
import type { AnalyzeResult, ChannelResult } from "../types";

interface Props {
  r: AnalyzeResult;
  location: string;
  channel?: ChannelResult;
  onChannel: (c: ChannelResult) => void;
}

export default function ChannelFinder({ r, location, channel, onChannel }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search() {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      onChannel(await findChannel(location, r.issue.type, r.authority.type));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (channel?.found && channel.url && /^https?:\/\//i.test(channel.url)) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-3">
        <p className="font-medium">Official reporting page found · +{channel.bonus} pts</p>
        <p className="mt-1 break-words text-slate-600">{channel.title}</p>
        <p className="break-all text-xs text-slate-500">{channel.source}</p>
        <a href={channel.url} target="_blank" rel="noopener noreferrer"
          className="mt-3 inline-block rounded bg-green-600 px-3 py-1.5 text-white">
          Open reporting page
        </a>
      </div>
    );
  }

  if (channel) {
    return (
      <div className="rounded-lg border border-slate-200 p-3">
        <p className="font-medium">No official channel found</p>
        <p className="mt-1 text-slate-600">
          We couldn't find an official government page for this. Try your city's municipal website or helpline.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <p className="font-medium">Where to report it</p>
      <p className="mt-1 text-slate-600">Find the official page to report this, and earn +2 bonus points.</p>
      {error && <p className="mt-2 rounded bg-red-50 p-2 text-red-700">{error}</p>}
      <button onClick={search} disabled={loading}
        className="mt-3 rounded bg-slate-800 px-3 py-1.5 text-white disabled:opacity-50">
        {loading ? "Searching official sites…" : error ? "Try again" : "Find reporting channel"}
      </button>
    </div>
  );
}
