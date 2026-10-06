"use client";

import { useEffect, useState } from "react";
import { api, type ProductInsights, type ProductSummary } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { ThemeBars } from "@/components/charts";

export default function ComparePage() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [a, setA] = useState<string>("");
  const [b, setB] = useState<string>("");
  const [result, setResult] = useState<{ a: ProductInsights; b: ProductInsights } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listProducts().then((list) => {
      setProducts(list);
      if (list.length >= 2) {
        setA(list[0].product_id);
        setB(list[1].product_id);
      }
    });
  }, []);

  useEffect(() => {
    if (!a || !b || a === b) {
      setResult(null);
      return;
    }
    setError(null);
    api
      .compare(a, b)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to compare"));
  }, [a, b]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Compare products</h1>

      <div className="flex gap-4">
        <ProductSelect label="Product A" value={a} onChange={setA} products={products} />
        <ProductSelect label="Product B" value={b} onChange={setB} products={products} />
      </div>

      {error && <Card className="text-negative">{error}</Card>}
      {a === b && a && <Card className="text-muted">Choose two different products.</Card>}

      {result && (
        <div className="grid gap-4 lg:grid-cols-2">
          {[result.a, result.b].map((insights) => (
            <Card key={insights.product_id} className="space-y-4">
              <div>
                <CardTitle>{insights.product_id}</CardTitle>
                <CardValue className="text-lg">{insights.product_name}</CardValue>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div>
                  <div className="text-muted">Reviews</div>
                  <div className="font-semibold">{insights.review_count}</div>
                </div>
                <div>
                  <div className="text-muted">Avg rating</div>
                  <div className="font-semibold">{insights.avg_rating?.toFixed(2) ?? "-"}</div>
                </div>
                <div>
                  <div className="text-muted">Needs review</div>
                  <div className="font-semibold">{insights.needs_review_count}</div>
                </div>
              </div>
              <ThemeBars themes={insights.theme_summary} />
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function ProductSelect({
  label,
  value,
  onChange,
  products,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  products: ProductSummary[];
}) {
  return (
    <label className="flex-1 text-sm">
      <span className="text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
      >
        {products.map((p) => (
          <option key={p.product_id} value={p.product_id}>
            {p.product_name} ({p.product_id})
          </option>
        ))}
      </select>
    </label>
  );
}
