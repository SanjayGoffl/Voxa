"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ProductInsights, ThemeSummary, TrendPoint } from "@/lib/api";

const SENTIMENT_COLORS = { positive: "#16a34a", neutral: "#ca8a04", negative: "#dc2626" };
const THEME_COLOR_POS = "#16a34a";
const THEME_COLOR_NEG = "#dc2626";

export function SentimentDonut({ distribution }: { distribution: ProductInsights["sentiment_distribution"] }) {
  const data = [
    { name: "Positive", value: distribution.positive, color: SENTIMENT_COLORS.positive },
    { name: "Neutral", value: distribution.neutral, color: SENTIMENT_COLORS.neutral },
    { name: "Negative", value: distribution.negative, color: SENTIMENT_COLORS.negative },
  ];
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={3}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} stroke="none" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", background: "var(--surface)" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function ThemeBars({ themes }: { themes: ThemeSummary[] }) {
  const data = themes.map((t) => ({
    theme: t.theme,
    positive: t.positive_count,
    negative: -t.negative_count,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="theme" width={80} tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", background: "var(--surface)" }}
          formatter={(value) => Math.abs(Number(value ?? 0))}
        />
        <Bar dataKey="positive" fill={THEME_COLOR_POS} radius={4} />
        <Bar dataKey="negative" fill={THEME_COLOR_NEG} radius={4} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TrendLine({ trend }: { trend: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={trend}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", background: "var(--surface)" }}
        />
        <Line type="monotone" dataKey="positive" stroke={SENTIMENT_COLORS.positive} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="neutral" stroke={SENTIMENT_COLORS.neutral} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="negative" stroke={SENTIMENT_COLORS.negative} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
