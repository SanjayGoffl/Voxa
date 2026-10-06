"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api, type ReviewExplain } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export function ExplainDrawer({
  reviewId,
  open,
  onOpenChange,
}: {
  reviewId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [data, setData] = useState<ReviewExplain | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!reviewId || !open) return;
    setLoading(true);
    setData(null);
    api
      .explainReview(reviewId)
      .then(setData)
      .finally(() => setLoading(false));
  }, [reviewId, open]);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30" />
        <Dialog.Content className="fixed right-0 top-0 z-40 h-full w-full max-w-lg overflow-y-auto solid-panel rounded-none border-l p-6">
          <div className="flex items-center justify-between">
            <Dialog.Title className="text-lg font-semibold">Why this label?</Dialog.Title>
            <Dialog.Close asChild>
              <button className="rounded-lg p-1.5 hover:bg-[var(--accent-soft)]" aria-label="Close">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          {loading && <div className="mt-6 text-muted">Loading evidence&hellip;</div>}

          {data && (
            <div className="mt-6 space-y-5">
              <div className="rounded-lg bg-[var(--accent-soft)] p-3 text-sm">
                <div className="font-medium">{data.review_id}</div>
                <div className="mt-1 text-muted">Rating: {data.rating} / 5</div>
                <div className="mt-2">{data.review_text}</div>
              </div>

              {data.clauses.map((clause) => (
                <div key={clause.clause_index} className="rounded-lg border border-[var(--border)] p-3">
                  <div className="flex items-center gap-2 text-sm">
                    {clause.contrast_cue && (
                      <Badge>{clause.contrast_cue}</Badge>
                    )}
                    <Badge variant={clause.sentiment.label}>{clause.sentiment.label}</Badge>
                    <Badge variant={clause.confidence_tier}>{clause.confidence_tier}</Badge>
                  </div>
                  <div className="mt-2 text-sm">&ldquo;{clause.text}&rdquo;</div>

                  <div className="mt-3 space-y-1 text-xs text-muted">
                    <div className="font-medium text-[var(--foreground)]">Sentiment probabilities</div>
                    {Object.entries(clause.sentiment.probs).map(([label, p]) => (
                      <ProbBar key={label} label={label} value={p} />
                    ))}
                  </div>

                  <div className="mt-3 space-y-1 text-xs">
                    <div className="font-medium">Theme scores (fused)</div>
                    {Object.entries(clause.all_theme_scores)
                      .sort((a, b) => b[1] - a[1])
                      .map(([theme, score]) => {
                        const detail = clause.assigned_themes.find((t) => t.theme === theme);
                        return (
                          <div key={theme} className="flex items-center justify-between text-muted">
                            <span className={detail ? "text-[var(--accent)]" : ""}>
                              {theme}
                              {detail?.lexical_negated ? " (negated match)" : ""}
                            </span>
                            <span>{score.toFixed(2)}</span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function ProbBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 shrink-0">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-[var(--border)]">
        <div
          className="h-1.5 rounded-full bg-[var(--accent)]"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="w-10 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}
