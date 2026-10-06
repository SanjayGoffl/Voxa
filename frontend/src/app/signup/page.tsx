"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();
  const [role, setRole] = useState<"customer" | "brand">("customer");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [brandName, setBrandName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await signup({
        email,
        password,
        role,
        display_name: displayName,
        brand_name: role === "brand" ? brandName : undefined,
      });
      router.push(role === "brand" ? "/brand/import" : "/browse");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <Card className="space-y-4">
        <h1 className="text-xl font-semibold">Create an account</h1>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setRole("customer")}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium ${
              role === "customer" ? "bg-[var(--accent)] text-white" : "bg-[var(--accent-soft)] text-[var(--accent)]"
            }`}
          >
            I&apos;m a customer
          </button>
          <button
            type="button"
            onClick={() => setRole("brand")}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium ${
              role === "brand" ? "bg-[var(--accent)] text-white" : "bg-[var(--accent-soft)] text-[var(--accent)]"
            }`}
          >
            I&apos;m a brand
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <Field label="Display name" value={displayName} onChange={setDisplayName} />
          {role === "brand" && (
            <Field label="Brand / company name" value={brandName} onChange={setBrandName} />
          )}
          <Field label="Email" type="email" value={email} onChange={setEmail} />
          <Field label="Password" type="password" value={password} onChange={setPassword} />
          {error && <div className="text-sm text-negative">{error}</div>}
          <Button type="submit" disabled={loading} className="w-full">
            Sign up
          </Button>
        </form>

        {role === "brand" && (
          <p className="text-xs text-muted">
            Brand accounts can import their own review data and get a verified badge on their
            products, so reviews aren&apos;t posted by random unverified sources.
          </p>
        )}

        <p className="text-sm text-muted">
          Already have an account? <Link href="/login" className="text-[var(--accent)]">Log in</Link>
        </p>
      </Card>
    </div>
  );
}

function Field({
  label,
  type = "text",
  value,
  onChange,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="text-muted">{label}</span>
      <input
        type={type}
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2"
      />
    </label>
  );
}
