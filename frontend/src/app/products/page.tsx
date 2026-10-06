"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ProductSummary } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Star } from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listProducts()
      .then(setProducts)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load products"));
  }, []);

  if (error) {
    return <Card className="max-w-lg text-negative">{error}</Card>;
  }

  if (!products) {
    return <div className="text-muted">Loading products&hellip;</div>;
  }

  if (products.length === 0) {
    return (
      <Card className="max-w-lg text-center text-muted">
        No data yet. <Link href="/" className="text-[var(--accent)]">Upload a review CSV</Link> to get started.
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Products</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((p) => (
          <Link key={p.product_id} href={`/products/${p.product_id}`}>
            <Card className="h-full transition-transform hover:-translate-y-0.5">
              <CardTitle>{p.product_id}</CardTitle>
              <CardValue className="text-lg">{p.product_name}</CardValue>
              <div className="mt-3 flex items-center justify-between text-sm text-muted">
                <span>{p.review_count} reviews</span>
                <span className="flex items-center gap-1">
                  <Star size={14} className="fill-[var(--neutral)] text-[var(--neutral)]" />
                  {p.avg_rating.toFixed(2)}
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
