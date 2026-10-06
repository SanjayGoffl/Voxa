import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const TIER_STYLES: Record<string, string> = {
  High: "bg-[var(--positive)]/15 text-positive",
  Medium: "bg-[var(--neutral)]/15 text-neutral-sentiment",
  Ambiguous: "bg-[var(--negative)]/15 text-negative",
};

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "bg-[var(--positive)]/15 text-positive",
  negative: "bg-[var(--negative)]/15 text-negative",
  neutral: "bg-[var(--muted)]/15 text-muted",
};

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: string }) {
  const style = TIER_STYLES[variant ?? ""] ?? SENTIMENT_STYLES[variant ?? ""] ?? "bg-[var(--accent-soft)] text-[var(--accent)]";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        style,
        className
      )}
      {...props}
    />
  );
}
