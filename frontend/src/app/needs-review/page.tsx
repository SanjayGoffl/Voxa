"use client";

import { useEffect, useState } from "react";
import { api, type NeedsReviewItem } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExplainDrawer } from "@/components/explain-drawer";

export default function NeedsReviewPage() {
  const [items, setItems] = useState<NeedsReviewItem[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api.needsReview(200).then(setItems);
  }, []);

  if (!items) return <div className="text-muted">Loading&hellip;</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Needs human review</h1>
        <p className="text-muted">
          Clauses where semantic, lexical, and rating signals disagreed enough to land in the
          Ambiguous confidence tier.
        </p>
      </div>

      {items.length === 0 && <Card className="text-muted">Nothing ambiguous &mdash; nice and clean.</Card>}

      <div className="grid gap-3">
        {items.map((item, i) => (
          <Card
            key={i}
            className="cursor-pointer transition-colors hover:bg-[var(--accent-soft)]"
            onClick={() => setSelected(item.review_id)}
          >
            <div className="flex items-center gap-2 text-xs text-muted">
              <span>{item.review_id}</span>
              <span>&middot;</span>
              <span>{item.product_id}</span>
              <Badge variant={item.sentiment}>{item.sentiment}</Badge>
              <span className="ml-auto">agreement {item.confidence_agreement.toFixed(2)}</span>
            </div>
            <div className="mt-2 text-sm">&ldquo;{item.text}&rdquo;</div>
          </Card>
        ))}
      </div>

      <ExplainDrawer reviewId={selected} open={selected !== null} onOpenChange={(open) => !open && setSelected(null)} />
    </div>
  );
}
