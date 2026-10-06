"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, type ProductInsights } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SentimentDonut, ThemeBars, TrendLine } from "@/components/charts";
import { EvidencePanel } from "@/components/evidence-panel";
import { ExplainDrawer } from "@/components/explain-drawer";

export default function ProductDashboardPage() {
  const params = useParams<{ id: string }>();
  const productId = params.id;

  const [insights, setInsights] = useState<ProductInsights | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedReview, setSelectedReview] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    setInsights(null);
    setError(null);
    api
      .productInsights(productId)
      .then(setInsights)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load insights"));
  }, [productId]);

  if (error) return <Card className="max-w-lg text-negative">{error}</Card>;
  if (!insights) return <div className="text-muted">Loading insights&hellip;</div>;

  const totalReviews = insights.review_count;
  const exportUrl = `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/export?product=${insights.product_id}&format=csv`;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{insights.product_name}</h1>
          <p className="text-muted">{insights.product_id}</p>
        </div>
        <a href={exportUrl} target="_blank" rel="noreferrer">
          <Button variant="outline">Export report</Button>
        </a>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Card>
          <CardTitle>Reviews</CardTitle>
          <CardValue>{totalReviews}</CardValue>
        </Card>
        <Card>
          <CardTitle>Avg rating</CardTitle>
          <CardValue>{insights.avg_rating?.toFixed(2) ?? "-"}</CardValue>
        </Card>
        <Card>
          <CardTitle>Avg text sentiment</CardTitle>
          <CardValue>{insights.avg_text_sentiment?.toFixed(2) ?? "-"}</CardValue>
        </Card>
        <Card>
          <CardTitle>Rating&ndash;sentiment gap</CardTitle>
          <CardValue className={Math.abs(insights.rating_sentiment_gap ?? 0) > 0.3 ? "text-negative" : ""}>
            {insights.rating_sentiment_gap?.toFixed(2) ?? "-"}
          </CardValue>
        </Card>
        <Card>
          <CardTitle>Needs review</CardTitle>
          <CardValue className={insights.needs_review_count > 0 ? "text-negative" : "text-positive"}>
            {insights.needs_review_count}
          </CardValue>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="font-medium">Sentiment distribution</h2>
          <SentimentDonut distribution={insights.sentiment_distribution} />
          <div className="flex justify-center gap-4 text-xs text-muted">
            <span className="text-positive">&#9679; Positive {insights.sentiment_distribution.positive}</span>
            <span className="text-neutral-sentiment">&#9679; Neutral {insights.sentiment_distribution.neutral}</span>
            <span className="text-negative">&#9679; Negative {insights.sentiment_distribution.negative}</span>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="font-medium">Theme breakdown (positive vs negative mentions)</h2>
          <ThemeBars themes={insights.theme_summary} />
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="font-medium">Top positive themes</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {insights.top_positive_themes.map((t) => (
              <li key={t.theme} className="flex items-center justify-between">
                <span>{t.theme}</span>
                <Badge variant="positive">{t.positive_count} mentions</Badge>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-medium">Top issues</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {insights.top_issues.map((t) => (
              <li key={t.theme} className="flex items-center justify-between">
                <span>{t.theme}</span>
                <Badge variant="negative">
                  {t.negative_count} mentions &middot; {(t.negative_share * 100).toFixed(0)}% negative
                </Badge>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {insights.trend.length > 0 && (
        <Card>
          <h2 className="font-medium">Monthly sentiment trend</h2>
          <TrendLine trend={insights.trend} />
        </Card>
      )}

      <Card className="flex items-center gap-6">
        <h2 className="font-medium">Confidence tiers</h2>
        <div className="flex gap-4 text-sm">
          <Badge variant="High">High {insights.confidence_tier_counts.High}</Badge>
          <Badge variant="Medium">Medium {insights.confidence_tier_counts.Medium}</Badge>
          <Badge variant="Ambiguous">Ambiguous {insights.confidence_tier_counts.Ambiguous}</Badge>
        </div>
      </Card>

      <EvidencePanel insights={insights} onSelectReview={setSelectedReview} />

      <ExplainDrawer
        reviewId={selectedReview}
        open={selectedReview !== null}
        onOpenChange={(open) => !open && setSelectedReview(null)}
      />
    </div>
  );
}
