# Voxa - Retail Review Insights & Customer-Brand Portal

Voxa is an intelligent retail review analytics platform and portal that bridges brands and shoppers. It ingests customer feedback, performs granular clause-level sentiment and theme extraction, and delivers actionable product insights alongside customer discussion spaces.

---

## 🚀 Key Features

- **Interactive Landing Page (`/`)**: Modern showcase with feature highlights, quick-start entrypoints, and portal overviews.
- **Dual-Role Authentication (`/signup`, `/login`)**: Dedicated onboarding for **Customers** and **Brands** (with brand verification tag).
- **Customer Portal (`/browse` & `/browse/[id]`)**:
  - Browse verified brand products and real-time sentiment analytics.
  - Granular clause breakdowns (quality, delivery, packaging, sizing, value).
  - Reddit-style interactive discussion threads with nested replies and voting.
- **Brand Management Portal (`/brand/import`)**:
  - Authenticated ingestion pipeline for CSV and Excel files.
  - Auto-detected header mapping with live preview and confirmation.
  - Attaches verified brand provenance to imported products.
- **Granular Review Processing**: Splitting compound review sentences into clauses to accurately map sentiment across distinct themes.
- **Explainability & Verification (`/compare`, `/needs-review`)**: Evidence panels and low-confidence flags for human-in-the-loop review.
- **Full-Stack Architecture**:
  - **Backend**: FastAPI (Python 3.10+) with modular pipelines, comments, auth, and analytics.
  - **Frontend**: Next.js 15 (App Router), React, TypeScript, Tailwind CSS, Lucide Icons.

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── config/          # Pipeline configurations & theme definitions
│   │   ├── data/            # Data generators & synthetic datasets
│   │   ├── pipeline/        # Ingest, clause splitting, sentiment, theme fusion, LLM rewrite
│   │   ├── analytics.py     # Aggregation and metric calculations
│   │   ├── auth.py          # Account authentication & role management
│   │   ├── comments.py      # Discussion threads, nested replies, voting
│   │   ├── export.py        # CSV & PDF export utilities
│   │   ├── main.py          # FastAPI application routes
│   │   └── store.py         # In-memory / storage management
│   ├── requirements.txt     # Python dependencies
│   └── sample_reviews.csv   # Sample test dataset (100 synthetic reviews)
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (Landing, Browse, Brand, Login, Signup)
│   │   ├── components/      # UI components (Charts, Comments, Evidence, Nav)
│   │   └── lib/             # API client, auth context, and utilities
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
2. Browse pre-seeded products under **Browse** or sign up as a **Brand** and upload `backend/sample_reviews.csv` in **Import Reviews**.
3. Check out the interactive sentiment breakdown, trends, and product discussion threads.
