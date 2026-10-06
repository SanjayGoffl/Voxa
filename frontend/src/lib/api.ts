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
  verified_brand: string | null;
};

export type AuthUser = {
  id: string;
  email: string;
  role: "customer" | "brand";
  display_name: string;
  brand_name: string | null;
};

export type Comment = {
  id: string;
  product_id: string;
  author_name: string;
  text: string;
  created_at: string;
  parent_id: string | null;
  upvotes: number;
  replies: Comment[];
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
  summary_text: string;
  verified_brand: string | null;
};

export type MappingPreview = {
  columns: string[];
  sample_rows: Record<string, string>[];
  detected_mapping: Record<string, string>;
  unmapped_required: string[];
  dropped_reviewer_columns: string[];
  row_count: number;
  canonical_fields: string[];
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

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("auth_token");
  } catch {
    return null;
  }
}

async function request<T>(path: string, init?: RequestInit, auth = false): Promise<T> {
  const headers = new Headers(init?.headers);
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  signup: (data: {
    email: string;
    password: string;
    role: "customer" | "brand";
    display_name: string;
    brand_name?: string;
  }) =>
    request<{ token: string; user: AuthUser }>("/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  login: (email: string, password: string) =>
    request<{ token: string; user: AuthUser }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<AuthUser>("/auth/me", {}, true),

  previewUpload: async (file: File): Promise<MappingPreview> => {
    const form = new FormData();
    form.append("file", file);
    return request("/upload/preview", { method: "POST", body: form });
  },
  upload: async (
    file: File,
    mapping?: Record<string, string>,
    asBrand = false
  ): Promise<{ message: string; report: ImportReport }> => {
    const form = new FormData();
    form.append("file", file);
    if (mapping) form.append("mapping", JSON.stringify(mapping));
    if (asBrand) form.append("as_brand", "true");
    return request("/upload", { method: "POST", body: form }, true);
  },
  listProducts: () => request<ProductSummary[]>("/products"),
  productInsights: (productId: string, minRating?: number, maxRating?: number) => {
    const params = new URLSearchParams();
    if (minRating !== undefined) params.set("min_rating", String(minRating));
    if (maxRating !== undefined) params.set("max_rating", String(maxRating));
    const qs = params.toString();
    return request<ProductInsights>(
      `/products/${encodeURIComponent(productId)}/insights${qs ? `?${qs}` : ""}`
    );
  },
  compare: (a: string, b: string) =>
    request<{ a: ProductInsights; b: ProductInsights }>(
      `/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`
    ),
  explainReview: (reviewId: string) =>
    request<ReviewExplain>(`/review/${encodeURIComponent(reviewId)}/explain`),
  needsReview: (limit = 100) => request<NeedsReviewItem[]>(`/needs-review?limit=${limit}`),

  getComments: (productId: string) =>
    request<Comment[]>(`/products/${encodeURIComponent(productId)}/comments`),
  postComment: (productId: string, text: string, parentId?: string) =>
    request<{ id: string }>(
      `/products/${encodeURIComponent(productId)}/comments`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, parent_id: parentId ?? null }),
      },
      true
    ),
  upvoteComment: (productId: string, commentId: string) =>
    request<{ id: string; upvotes: number }>(
      `/products/${encodeURIComponent(productId)}/comments/${encodeURIComponent(commentId)}/upvote`,
      { method: "POST" },
      true
    ),
};
