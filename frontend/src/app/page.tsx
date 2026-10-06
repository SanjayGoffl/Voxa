"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import {
  Search,
  MessageSquareText,
  BarChart3,
  ShieldCheck,
  TrendingUp,
  FileSearch,
} from "lucide-react";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-5xl space-y-16">
      <section className="space-y-6 py-10 text-center">
        <span className="inline-flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-medium text-[var(--accent)]">
          Product-level insight, not reviewer profiling
        </span>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Know what customers actually think &mdash; by theme, not by guesswork
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-muted">
          Browse products, read real reviews and discussion threads, and see sentiment, recurring
          themes, and trends extracted from the text itself &mdash; every claim backed by a
          quoted excerpt.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link href="/browse">
            <Button className="px-6 py-3 text-base">
              <Search size={18} /> Browse products
            </Button>
          </Link>
          {user?.role === "brand" ? (
            <Link href="/brand/import">
              <Button variant="outline" className="px-6 py-3 text-base">
                <ShieldCheck size={18} /> Import your product reviews
              </Button>
            </Link>
          ) : (
            <Link href="/signup">
              <Button variant="outline" className="px-6 py-3 text-base">
                <ShieldCheck size={18} /> For brands &amp; retailers
              </Button>
            </Link>
          )}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <FeatureCard
          icon={<Search size={20} />}
          title="Discover &amp; compare"
          body="Search the catalog, open any product's full review breakdown, and compare two products side by side."
        />
        <FeatureCard
          icon={<MessageSquareText size={20} />}
          title="Discuss"
          body="A Reddit-style comment thread on every product &mdash; ask questions, share your own experience, upvote the most useful replies."
        />
        <FeatureCard
          icon={<ShieldCheck size={20} />}
          title="Verified brands"
          body="Brands import their own review data directly and get a verified badge, so you know it isn't a random anonymous dump."
        />
        <FeatureCard
          icon={<BarChart3 size={20} />}
          title="Theme-level analytics"
          body="Quality, delivery, packaging, size/fit, value, usability &mdash; sentiment and mention counts broken out per theme, not just a star average."
        />
        <FeatureCard
          icon={<TrendingUp size={20} />}
          title="Trends over time"
          body="Monthly sentiment and per-theme negative-rate trends show whether an issue is improving or getting worse."
        />
        <FeatureCard
          icon={<FileSearch size={20} />}
          title="Explainable, always"
          body="Every label traces back to the exact clause and signal scores that produced it &mdash; open 'Why this label?' on any excerpt."
        />
      </section>

      <section className="solid-panel p-8 text-center">
        <h2 className="text-xl font-semibold">Running your own review data?</h2>
        <p className="mt-2 text-muted">
          Create a brand account to import your product reviews as a verified source, or sign up
          as a customer to browse, compare, and join the discussion.
        </p>
        <div className="mt-4 flex justify-center gap-3">
          <Link href="/signup">
            <Button>Create an account</Button>
          </Link>
          <Link href="/browse">
            <Button variant="outline">Browse without an account</Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  body,
}: {
  icon: ReactNode;
  title: string;
  body: string;
}) {
  return (
    <Card className="space-y-2">
      <div className="text-[var(--accent)]">{icon}</div>
      <h3 className="font-medium">{title}</h3>
      <p className="text-sm text-muted">{body}</p>
    </Card>
  );
}
