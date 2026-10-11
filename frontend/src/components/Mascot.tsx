type Mood = "idle" | "hero" | "wait" | "cheer";

/** The raccoon. Decorative, so no alt text. Pose changes are CSS-only. */
export default function Mascot({ mood = "idle", className = "" }: { mood?: Mood; className?: string }) {
  return (
    <img src="/mascot.webp" alt="" width={640} height={640} draggable={false}
      className={`mascot mascot-${mood} select-none object-contain ${className}`} />
  );
}
