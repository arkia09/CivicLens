import type { AnalyzeResult, ChannelResult } from "./types";

const MAX_BONUS = 2;

/** Bonus for a slot: only a found channel counts, once, capped at +2. */
export function channelBonus(channel?: ChannelResult): number {
  return channel?.found ? Math.min(MAX_BONUS, Math.max(0, channel.bonus)) : 0;
}

/** Points for one slot: the backend's score plus the channel bonus. */
export function slotPoints(result: AnalyzeResult, channel?: ChannelResult): number {
  return result.score.total + channelBonus(channel);
}
