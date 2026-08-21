# Student Data Pipeline & UI

A small full-stack app that takes a messy, real-world student CSV/XLSX, cleans it automatically, and gives a reviewer a live, interactive way to build a shortlist: a minimum-Total-score filter with instant stats, and an Active/Debarred toggle that removes debarred students from the shortlist in real time. The shortlist exports to CSV with one click.

Built for the RM Student Selection technical assessment, against the provided `RM_Student_Selection_Dataset` (3,000 rows).

**Video demo:** [`demo/demo.mp4`](demo/demo.mp4) (24 seconds, well under the 90s limit — click to play/download from GitHub).

**Live deployment:** not deployed for this submission (see [Deploying](#deploying-the-bonus) below for exactly how to do it — the app is deploy-ready).

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [Data cleaning logic](#data-cleaning-logic)
- [API reference](#api-reference)
- [Testing](#testing)
- [Performance](#performance)
- [Known limitations](#known-limitations)
- [Deploying (the bonus)](#deploying-the-bonus)

## Features

- Upload a raw `.csv` or `.xlsx` student file; cleaning runs automatically.
- Cleaning report showing exactly what the pipeline changed (rows read/kept, duplicates removed, names normalized, unrecognized genders, invalid grades/marks, totals corrected, incomplete rows).
- Full cleaned dataset in a paginated, searchable table.
- A minimum Total Score slider/number field that updates a shortlist and its stats (count, average, highest, lowest) live, with no page reload and no network round-trip.
- An Active/Debarred toggle per student. Flipping a student to Debarred removes them from the shortlist immediately, even if their score clears the bar.
- One-click CSV export of exactly the shortlist currently on screen (respects both the score filter and Active/Debarred status).

## Architecture

```
backend/            FastAPI + pandas
  app/cleaning.py    pure, unit-tested cleaning functions + orchestrator
  app/main.py        REST API (upload / students / status / export)
  app/store.py       in-memory store for the current cleaned dataset
  tests/             pytest — 70 tests covering cleaning rules + API

frontend/            React + Vite
  src/App.jsx         app state: students, report, filter, search
  src/components/     UploadPanel, CleaningReport, StudentTable, FilterBar, StatsCards
  src/utils/csv.js    client-side CSV export

sample_data/          the assessment dataset, exported to CSV
demo/demo.mp4          screen-recorded walkthrough
```

**Why the split is where it is:** parsing, regex normalization, dedup, and Total recalculation are one-time, CPU-bound work best done once, in Python/pandas, right after upload. Everyday interactions — moving the score slider, searching, toggling a status, exporting — need to feel instant, so they run against the already-cleaned dataset the frontend holds in memory, with zero network round-trips. That's also why "Export" is a client-side CSV Blob download rather than a server request: the browser already has exactly the rows on screen. A server-side `GET /api/export` endpoint exists too (see [API reference](#api-reference)), both to persist status changes and as a documented alternative implementation of the same filter/export logic.

## Setup

Requires Python 3.11+ and Node 18+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd frontend
cp .env.example .env             # VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

Open `http://localhost:5173`, upload `sample_data/RM_Student_Selection_Dataset.csv` (or your own file with the same columns), and use the app.

For a production build: `npm run build && npm run preview`.

## Data cleaning logic

Every rule is a small, pure function in `backend/app/cleaning.py`, independently unit-tested in `backend/tests/test_cleaning.py` against real dirty rows pulled from the provided dataset. In order:

| Field | Raw problem observed in the dataset | Rule applied |
|---|---|---|
| Name | Stray straight quotes/apostrophes (`Navya'`, `"Aarav"`), inconsistent case (`ROHAN`, `myra`) | Strip quote/apostrophe/whitespace junk, collapse internal whitespace, Title-case |
| Gender | Mixed text (`M/Male/male/m`, `F/Female/female/f`) *and* a numeric code (`0`/`1`) with no codebook | Map every variant to `Male`/`Female`. **Documented assumption: `1 = Male`, `0 = Female`** (see `GENDER_MAP` in `cleaning.py` — flip it if a real codebook says otherwise). Anything else becomes `Unknown` and is counted, never silently dropped. |
| Grade | Mixed formats: `"7"` vs `"Grade 7"` | Regex-extract the digits, validate 1–12 |
| Math / Science / English | Mixed formats: `"28"` vs `"28 marks"` | Regex-extract the digits, validate 0–100. Unparseable or out-of-range → `null`, counted, row kept (not dropped) |
| Total | In the provided file this always equals `Math+Science+English` once marks are parsed, but that's not guaranteed for every file the grader might test with | **Always recalculated** from the cleaned marks. If it disagrees with the source value, the recalculated value wins and the row is counted in `totals_corrected`. If any mark is missing, Total is left `null` rather than trusting an unverifiable source value. |
| Duplicates | None found in the provided file | Only an **exact**, fully-identical row (all 7 fields match after cleaning) is dropped, keeping the first occurrence. We deliberately do **not** flag rows that merely share Name+Grade+Gender: this dataset draws from a pool of only ~20 first names across 3,000 rows, so those collisions are statistically expected between different real students, not evidence of a duplicate entry. See [Known limitations](#known-limitations). |
| Status | Doesn't exist in the source file | New rows default to `Active`; the app owns this state from then on |

Every upload returns a **cleaning report** (`rows_in`, `rows_out`, `exact_duplicates_removed`, `names_normalized`, `gender_unmapped`, `grade_invalid`, `marks_invalid` per subject, `totals_corrected`, `rows_incomplete`) so a reviewer can see exactly what the pipeline did, not just trust the end result.

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness check |
| POST | `/api/upload` | multipart file upload → cleans and stores the dataset, returns `{ students, report }` |
| GET | `/api/students` | the currently-stored cleaned dataset + report |
| PATCH | `/api/students/{id}/status` | body `{ "status": "Active" \| "Debarred" }` |
| GET | `/api/export?min_total=&active_only=` | CSV of the matching shortlist (server-side alternative to the frontend's client-side export) |

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -v
```

70 tests: scalar cleaning-function fixtures drawn from real dirty rows in the dataset (quoted names, `"N marks"`, `Grade N` vs `N`, the `0/1` gender code), full-pipeline tests (mismatched totals, exact duplicates, unmapped genders, missing columns, whitespace/case-insensitive headers), and API-level tests (upload, status toggle + persistence, export filtering, error responses).

The full flow was also verified end-to-end against the real 3,000-row file with a Playwright script driving the built frontend against the running backend (upload → cleaning report → search → live filter → debar toggle → export) — that run is what produced `demo/demo.mp4`.

## Performance

- Cleaning a 3,000-row file (regex parsing every cell, dedup, recalculation) completes in well under a second.
- The frontend fetches the cleaned dataset once per upload; every subsequent interaction (search, slider, toggle, export) is a pure client-side array filter/reduce over data already in memory — no network round-trip, no re-cleaning.
- The dataset table paginates at 50 rows/page so the DOM stays light even at 3,000+ rows.
- Production frontend bundle is ~150KB (≈49KB gzipped) with zero UI-framework dependency beyond React itself.

## Known limitations

- **Single dataset, single process.** One upload replaces the previous dataset; there's no multi-user/session isolation or persistence across a backend restart. A production version would add a real database and scope data per user. This was a deliberate scope decision for an assessment-sized app.
- **Gender `0`/`1` coding is an assumption**, not a verified codebook (see [Data cleaning logic](#data-cleaning-logic)). Easy to flip in `GENDER_MAP` if wrong.
- **No identity-based fuzzy-duplicate detection.** With only ~20 distinct first names across 3,000 rows, Name+Grade+Gender collisions are expected and not a reliable duplicate signal (see the Duplicates row above); a stable student ID (roll number/email) would be needed to do this safely.
- **No authentication.** Fine for a local/demo reviewer tool; would need auth before handling real student data in production.

## Deploying (the bonus)

The app is deploy-ready but not deployed for this submission. To do it:

1. **Backend → Render (or Railway/Fly.io):** new Web Service from this repo, root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. **Frontend → Vercel (or Netlify):** root directory `frontend`, build command `npm run build`, output directory `dist`, environment variable `VITE_API_URL` set to the deployed backend's URL.
3. Update the CORS `allow_origins` in `backend/app/main.py` from `"*"` to the deployed frontend's exact origin.
4. Add the live URL at the top of this README.
