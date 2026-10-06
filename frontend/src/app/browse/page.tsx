"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ProductSummary } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Star, ShieldCheck } from "lucide-react";

export default function BrowsePage() {
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
        No products yet.{" "}
        <Link href="/brand/import" className="text-[var(--accent)]">
          Brands can import review data
        </Link>{" "}
        to populate the catalog.
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Browse products</h1>
        <p className="text-muted">Every product&apos;s rating, sentiment, and themes, backed by its reviews.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((p) => (
          <Link key={p.product_id} href={`/browse/${p.product_id}`}>
            <Card className="h-full transition-transform hover:-translate-y-0.5">
              <div className="flex items-start justify-between gap-2">
                <CardTitle>{p.product_id}</CardTitle>
                {p.verified_brand && (
                  <Badge variant="positive" className="flex items-center gap-1">
                    <ShieldCheck size={12} /> {p.verified_brand}
                  </Badge>
                )}
              </div>
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
