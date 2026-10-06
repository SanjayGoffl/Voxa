"""Exportable insight report: CSV (flat tables) and PDF (readable summary)."""
from __future__ import annotations

import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_csv(insights: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Product", insights["product_name"]])
    writer.writerow(["Product ID", insights["product_id"]])
    writer.writerow(["Review count", insights["review_count"]])
    writer.writerow(["Avg rating", insights["avg_rating"]])
    writer.writerow(["Avg text sentiment", insights["avg_text_sentiment"]])
    writer.writerow(["Rating-sentiment gap", insights["rating_sentiment_gap"]])
    writer.writerow(["Needs review count", insights["needs_review_count"]])
    writer.writerow([])
    writer.writerow(["Summary"])
    writer.writerow([insights["summary_text"]])
    writer.writerow([])

    writer.writerow(["Theme", "Positive", "Negative", "Neutral", "Total", "Negative share"])
    for t in insights["theme_summary"]:
        writer.writerow(
            [t["theme"], t["positive_count"], t["negative_count"], t["neutral_count"],
             t["total_mentions"], t["negative_share"]]
        )
    writer.writerow([])

    writer.writerow(["Theme", "Sentiment", "Review ID", "Excerpt", "Confidence"])
    for theme, groups in insights["evidence"].items():
        for sentiment, items in groups.items():
            for item in items:
                writer.writerow([theme, sentiment, item["review_id"], item["text"], item["confidence_tier"]])

    return buf.getvalue()


def build_pdf(insights: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"{insights['product_name']} — Review Insights", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(insights["summary_text"], styles["BodyText"]))
    story.append(Spacer(1, 16))

    kpi_rows = [
        ["Reviews", "Avg rating", "Avg text sentiment", "Rating-sentiment gap", "Needs review"],
        [
            insights["review_count"],
            insights["avg_rating"],
            insights["avg_text_sentiment"],
            insights["rating_sentiment_gap"],
            insights["needs_review_count"],
        ],
    ]
    kpi_table = Table(kpi_rows, hAlign="LEFT")
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Theme breakdown", styles["Heading2"]))
    theme_rows = [["Theme", "Positive", "Negative", "Neutral", "Negative share"]]
    for t in insights["theme_summary"]:
        theme_rows.append(
            [t["theme"], t["positive_count"], t["negative_count"], t["neutral_count"],
             f"{t['negative_share'] * 100:.0f}%"]
        )
    theme_table = Table(theme_rows, hAlign="LEFT")
    theme_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )
    story.append(theme_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Representative excerpts", styles["Heading2"]))
    for theme, groups in insights["evidence"].items():
        for sentiment, items in groups.items():
            if not items:
                continue
            story.append(Paragraph(f"<b>{theme}</b> — {sentiment}", styles["Heading4"]))
            for item in items:
                story.append(Paragraph(f'&ldquo;{item["text"]}&rdquo; ({item["confidence_tier"]})', styles["BodyText"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()
