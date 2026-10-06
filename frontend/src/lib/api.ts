const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type ImportReport = {
  total_rows: number;
  valid_rows: number;
  dropped_rows: number;
  dropped_reviewer_columns: string[];
  column_mapping: Record<string, string>;
  row_errors: { row: number; review_id: string; reason: string }[];
  used_synthetic_product_id: boolean;
};

export type ProductSummary = {
  product_id: string;
  product_name: string;
  review_count: number;
  avg_rating: number;
};

export type ThemeSummary = {
  theme: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  total_mentions: number;
  negative_share: number;
};

export type EvidenceClause = {
  review_id: string;
  text: string;
  sentiment: string;
  confidence_tier: string;
};

export type TrendPoint = {
  month: string;
  review_count: number;
  positive: number;
  neutral: number;
  negative: number;
  theme_negative_rate: Record<string, number>;
};

export type ProductInsights = {
  product_id: string;
  product_name: string;
  review_count: number;
  sentiment_distribution: { negative: number; neutral: number; positive: number };
  top_positive_themes: ThemeSummary[];
  top_issues: ThemeSummary[];
  theme_summary: ThemeSummary[];
  avg_rating: number | null;
  avg_text_sentiment: number | null;
  rating_sentiment_gap: number | null;
  confidence_tier_counts: { High: number; Medium: number; Ambiguous: number };
  needs_review_count: number;
  evidence: Record<string, { positive: EvidenceClause[]; negative: EvidenceClause[] }>;
  trend: TrendPoint[];
};

export type ThemeScoreDetail = {
  theme: string;
  fused_score: number;
  semantic_score: number;
  lexical_score: number;
  lexical_negated: boolean;
};

export type ExplainClause = {
  clause_index: number;
  text: string;
  contrast_cue: string | null;
  sentiment: { label: string; probs: Record<string, number> };
  assigned_themes: ThemeScoreDetail[];
  all_theme_scores: Record<string, number>;
  confidence_tier: string;
  confidence_agreement: number;
};

export type ReviewExplain = {
  review_id: string;
  product_id: string;
  rating: number;
  review_text: string;
  review_level_sentiment: { label: string; probs: Record<string, number> };
  clauses: ExplainClause[];
};

export type NeedsReviewItem = {
  review_id: string;
  product_id: string;
  clause_index: number;
  text: string;
  sentiment: string;
  theme_scores: Record<string, number>;
  confidence_agreement: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  upload: async (file: File): Promise<{ message: string; report: ImportReport }> => {
    const form = new FormData();
    form.append("file", file);
    return request("/upload", { method: "POST", body: form });
  },
  listProducts: () => request<ProductSummary[]>("/products"),
  productInsights: (productId: string) =>
    request<ProductInsights>(`/products/${encodeURIComponent(productId)}/insights`),
  compare: (a: string, b: string) =>
    request<{ a: ProductInsights; b: ProductInsights }>(
      `/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`
    ),
  explainReview: (reviewId: string) =>
    request<ReviewExplain>(`/review/${encodeURIComponent(reviewId)}/explain`),
  needsReview: (limit = 100) => request<NeedsReviewItem[]>(`/needs-review?limit=${limit}`),
};
