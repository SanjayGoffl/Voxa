"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import Link from "next/link";
import { api, type ImportReport, type MappingPreview } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UploadCloud, FileWarning, CheckCircle2, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const CANONICAL_LABELS: Record<string, string> = {
  review_id: "Review ID",
  product_id: "Product ID",
  product_name: "Product name",
  rating: "Rating (1-5)",
  review_text: "Review text",
  date: "Date",
};

export default function BrandImportPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<MappingPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleFile(selected: File) {
    setLoading(true);
    setError(null);
    setReport(null);
    setPreview(null);
    setFile(selected);
    try {
      const p = await api.previewUpload(selected);
      setPreview(p);
      setMapping({ ...p.detected_mapping });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not read file");
    } finally {
      setLoading(false);
    }
  }

  async function confirmImport() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.upload(file, mapping, true);
      setReport(result.report);
      setPreview(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  if (authLoading) return <div className="text-muted">Loading&hellip;</div>;

  if (!user || user.role !== "brand") {
    return (
      <Card className="mx-auto max-w-lg space-y-3 text-center">
        <ShieldCheck size={28} className="mx-auto text-[var(--accent)]" />
        <h1 className="text-lg font-semibold">Brand account required</h1>
        <p className="text-sm text-muted">
          Importing review data as a verified brand &mdash; so your products show reviews you
          actually control, not an anonymous import &mdash; requires a brand account.
        </p>
        <div className="flex justify-center gap-2">
          <Link href="/signup">
            <Button>Create a brand account</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline">Log in</Button>
          </Link>
        </div>
      </Card>
    );
  }

  const hasProductField = Boolean(mapping.product_id || mapping.product_name);
  const requiredOk =
    hasProductField && ["review_id", "rating", "review_text", "date"].every((f) => mapping[f]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Import reviews as {user.brand_name}
        </h1>
        <p className="mt-1 text-muted">
          Upload a CSV or Excel file of customer reviews for your products. Not every file has
          clean headers &mdash; you&apos;ll confirm or fix the column mapping before anything is
          imported. Reviewer/user columns are dropped automatically. Every product in this file
          will show a verified &ldquo;{user.brand_name}&rdquo; badge to customers.
        </p>
      </div>

      {!preview && (
        <Card
          className="flex flex-col items-center justify-center gap-3 border-dashed py-12 text-center cursor-pointer"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) handleFile(f);
          }}
        >
          <UploadCloud size={32} className="text-[var(--accent)]" />
          <div className="font-medium">Drop a CSV or Excel file here, or click to browse</div>
          {file && <div className="text-sm text-muted">{file.name}</div>}
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
        </Card>
      )}

      {loading && <Card className="text-sm text-muted">Working&hellip;</Card>}

      {error && (
        <Card className="flex items-start gap-3 text-negative">
          <FileWarning size={20} className="mt-0.5 shrink-0" />
          <div>{error}</div>
        </Card>
      )}

      {preview && (
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Confirm column mapping</h2>
            <span className="text-sm text-muted">{preview.row_count} rows detected</span>
          </div>

          {preview.dropped_reviewer_columns.length > 0 && (
            <div className="rounded-lg bg-[var(--accent-soft)] p-3 text-sm">
              Dropped reviewer/user columns: {preview.dropped_reviewer_columns.join(", ")}
            </div>
          )}

          {preview.unmapped_required.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-[var(--negative)]/10 p-3 text-sm text-negative">
              <FileWarning size={16} className="mt-0.5 shrink-0" />
              <div>
                Couldn&apos;t confidently auto-detect: {preview.unmapped_required.join(", ")}.
                Map them manually below.
              </div>
            </div>
          )}

          <div className="space-y-3">
            {Object.entries(CANONICAL_LABELS).map(([field, label]) => (
              <label key={field} className="flex items-center gap-3 text-sm">
                <span className="w-40 shrink-0 text-muted">
                  {label}
                  {(field === "product_id" || field === "product_name") && (
                    <span className="ml-1 text-xs">(either)</span>
                  )}
                </span>
                <select
                  value={mapping[field] ?? ""}
                  onChange={(e) =>
                    setMapping((m) => ({ ...m, [field]: e.target.value }))
                  }
                  className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5"
                >
                  <option value="">&mdash; not mapped &mdash;</option>
                  {preview.columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                {mapping[field] && <Badge variant="positive">mapped</Badge>}
              </label>
            ))}
          </div>

          <div>
            <div className="text-sm font-medium">Preview (first rows)</div>
            <div className="mt-2 overflow-x-auto rounded-lg border border-[var(--border)]">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[var(--accent-soft)]">
                    {preview.columns.map((c) => (
                      <th key={c} className="px-2 py-1.5 text-left font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.map((row, i) => (
                    <tr key={i} className="border-t border-[var(--border)]">
                      {preview.columns.map((c) => (
                        <td key={c} className="max-w-[200px] truncate px-2 py-1.5">
                          {row[c]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <Button onClick={confirmImport} disabled={!requiredOk || loading}>
            Import with this mapping <ArrowRight size={16} />
          </Button>
        </Card>
      )}

      {report && (
        <Card className="space-y-4">
          <div className="flex items-center gap-2 text-positive">
            <CheckCircle2 size={20} />
            <span className="font-medium">Upload complete &mdash; products are now verified</span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <CardTitle>Total rows</CardTitle>
              <CardValue>{report.total_rows}</CardValue>
            </div>
            <div>
              <CardTitle>Valid rows</CardTitle>
              <CardValue className="text-positive">{report.valid_rows}</CardValue>
            </div>
            <div>
              <CardTitle>Dropped rows</CardTitle>
              <CardValue className={report.dropped_rows > 0 ? "text-negative" : ""}>
                {report.dropped_rows}
              </CardValue>
            </div>
          </div>

          {report.row_errors.length > 0 && (
            <details className="text-sm">
              <summary className="cursor-pointer text-muted">
                {report.row_errors.length} row error(s)
              </summary>
              <ul className="mt-2 space-y-1 text-muted">
                {report.row_errors.map((err, i) => (
                  <li key={i}>
                    Row {err.row} ({err.review_id}): {err.reason}
                  </li>
                ))}
              </ul>
            </details>
          )}

          <Button onClick={() => router.push("/browse")}>View in catalog</Button>
        </Card>
      )}
    </div>
  );
}
