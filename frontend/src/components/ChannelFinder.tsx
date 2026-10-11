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
      <div className="rounded-xl border-2 border-moss bg-moss/10 p-4">
        <h3 className="font-display font-bold">Official reporting page found, +{channel.bonus} pts</h3>
        <p className="mt-1 break-words">{channel.title}</p>
        <p className="break-all text-xs text-muted">{channel.source}</p>
        <a href={channel.url} target="_blank" rel="noopener noreferrer" className="btn btn-ink mt-3 w-full sm:w-auto">
          Open reporting page
        </a>
      </div>
    );
  }

  if (channel) {
    return (
      <div className="rounded-xl border-2 border-ink/15 p-4">
        <h3 className="font-display font-bold">No official channel found</h3>
        <p className="mt-1 text-muted">
          We couldn't find an official government page for this. Try your city's municipal website or helpline.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border-2 border-dashed border-ink/30 p-4">
      <h3 className="font-display font-bold">Where to report it</h3>
      <p className="mt-1 text-muted">Find the official page to report this and earn +2 bonus points.</p>
      {error && <p role="alert" className="mt-3 rounded-lg bg-red-100 p-3 text-sm text-red-900">{error}</p>}
      <button onClick={search} disabled={loading} className="btn btn-ink mt-3 w-full sm:w-auto">
        {loading ? "Searching official sites…" : error ? "Try again" : "Find reporting channel"}
      </button>
    </div>
  );
}
