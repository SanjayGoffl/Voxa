"use client";

import { useState } from "react";
import type { ProductInsights } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export function EvidencePanel({
  insights,
  onSelectReview,
}: {
  insights: ProductInsights;
  onSelectReview: (reviewId: string) => void;
}) {
  const themes = Object.keys(insights.evidence);
  const [active, setActive] = useState(themes[0] ?? "");
  const group = insights.evidence[active];

  return (
    <Card className="space-y-4">
      <h2 className="font-medium">Evidence by theme</h2>
      <div className="flex flex-wrap gap-1">
        {themes.map((theme) => (
          <button
            key={theme}
            onClick={() => setActive(theme)}
            className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
              active === theme
                ? "bg-[var(--accent)] text-white"
                : "bg-[var(--accent-soft)] text-[var(--accent)] hover:opacity-80"
            }`}
          >
            {theme}
          </button>
        ))}
      </div>

      {group && (
        <div className="grid gap-4 sm:grid-cols-2">
          <ExcerptColumn title="Positive" items={group.positive} onSelectReview={onSelectReview} tone="positive" />
          <ExcerptColumn title="Negative" items={group.negative} onSelectReview={onSelectReview} tone="negative" />
        </div>
      )}
    </Card>
  );
}

function ExcerptColumn({
  title,
  items,
  tone,
  onSelectReview,
}: {
  title: string;
  items: { review_id: string; text: string; sentiment: string; confidence_tier: string }[];
  tone: "positive" | "negative";
  onSelectReview: (reviewId: string) => void;
}) {
  return (
    <div>
      <div className={`text-sm font-medium ${tone === "positive" ? "text-positive" : "text-negative"}`}>
        {title}
      </div>
      <div className="mt-2 space-y-2">
        {items.length === 0 && <div className="text-sm text-muted">No excerpts.</div>}
        {items.map((item, i) => (
          <button
            key={i}
            onClick={() => onSelectReview(item.review_id)}
            className="block w-full rounded-lg border border-[var(--border)] p-3 text-left text-sm transition-colors hover:bg-[var(--accent-soft)]"
          >
            <div>&ldquo;{item.text}&rdquo;</div>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant={item.confidence_tier}>{item.confidence_tier}</Badge>
              <span className="text-xs text-muted">{item.review_id}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
