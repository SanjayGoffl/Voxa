"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { api, type ImportReport } from "@/lib/api";
import { Card, CardTitle, CardValue } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UploadCloud, FileWarning, CheckCircle2 } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File) {
    setLoading(true);
    setError(null);
    setReport(null);
    setFileName(file.name);
    try {
      const result = await api.upload(file);
      setReport(result.report);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Import review data</h1>
        <p className="mt-1 text-muted">
          Upload a CSV of customer reviews. Columns map flexibly by name (review_id, product_id
          or product_name, rating, review_text, date). Reviewer/user columns are dropped
          automatically &mdash; this tool produces product-level insights only.
        </p>
      </div>

      <Card
        className="flex flex-col items-center justify-center gap-3 border-dashed py-12 text-center cursor-pointer"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
      >
        <UploadCloud size={32} className="text-[var(--accent)]" />
        <div className="font-medium">Drop a CSV file here, or click to browse</div>
        {fileName && <div className="text-sm text-muted">{fileName}</div>}
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </Card>

      {loading && <Card className="text-sm text-muted">Processing upload and running the pipeline&hellip;</Card>}

      {error && (
        <Card className="flex items-start gap-3 text-negative">
          <FileWarning size={20} className="mt-0.5 shrink-0" />
          <div>{error}</div>
        </Card>
      )}

      {report && (
        <Card className="space-y-4">
          <div className="flex items-center gap-2 text-positive">
            <CheckCircle2 size={20} />
            <span className="font-medium">Upload complete</span>
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

          {report.dropped_reviewer_columns.length > 0 && (
            <div className="rounded-lg bg-[var(--accent-soft)] p-3 text-sm">
              Dropped reviewer/user columns: {report.dropped_reviewer_columns.join(", ")}
            </div>
          )}

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

          <Button onClick={() => router.push("/products")}>View product dashboard</Button>
        </Card>
      )}
    </div>
  );
}
