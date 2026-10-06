# Voxa - Retail Review Insights

Voxa is an intelligent retail review analytics platform that ingests raw customer feedback, performs granular clause-level sentiment and theme extraction, and delivers actionable product insights through an interactive dashboard.

---

## 🚀 Key Features

- **Granular Review Processing**: Splitting compound review sentences into clauses to accurately map sentiment across distinct themes (e.g., quality, delivery, packaging, sizing, value).
- **Flexible Data Ingestion**: Auto-detects columns from CSV and Excel files, validating data and mapping fields seamlessly.
- **Product Insights & Comparison**: Side-by-side product metrics, thematic breakdowns, and trend analysis.
- **Explainability & Verification**: Drill down into review clauses with evidence panels and review flags for low confidence or ambiguous sentiments.
- **Modern Full-Stack Architecture**:
  - **Backend**: FastAPI (Python 3.10+) with analytical pipelines and data export (CSV/PDF).
  - **Frontend**: Next.js 15 (App Router), React, TypeScript, Tailwind CSS, Lucide Icons.

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── config/          # Pipeline configurations & theme definitions
│   │   ├── data/            # Data generators & synthetic datasets
│   │   ├── pipeline/        # Ingest, clause splitting, sentiment, theme fusion
│   │   ├── analytics.py     # Aggregation and metric calculations
│   │   ├── export.py        # CSV & PDF export utilities
│   │   ├── main.py          # FastAPI application routes
│   │   └── store.py         # In-memory / storage management
│   ├── requirements.txt     # Python dependencies
│   └── sample_reviews.csv   # Sample test dataset (100 synthetic reviews)
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (Upload, Products, Compare, Review)
│   │   ├── components/      # UI components (Charts, Evidence panel, Drawer, Nav)
│   │   └── lib/             # API client and utilities
│   ├── package.json         # Node.js dependencies
│   └── tsconfig.json        # TypeScript configuration
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

---

## 🧪 Testing with Sample Data
1. Open the frontend at `http://localhost:3000`.
2. Upload `backend/sample_reviews.csv`.
3. Explore the generated insights, comparison tools, and explainability features.
