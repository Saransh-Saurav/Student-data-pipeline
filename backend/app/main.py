"""
FastAPI backend for the Student Data Pipeline & UI app.

Endpoints
---------
GET    /api/health                 liveness check
POST   /api/upload                 upload a raw CSV/XLSX, clean it, store it
GET    /api/students                the currently-cleaned dataset (+ report)
PATCH  /api/students/{id}/status    toggle a single student Active/Debarred
GET    /api/export                 CSV of the current shortlist (server-side
                                    alternative to the frontend's client-side
                                    export -- see README "Architecture")

Design note: the heavy lifting (parsing, regex normalization, validation,
dedup, Total recalculation) happens once per upload, here, in pandas. Everyday
interactions -- moving the score slider, toggling a status, exporting -- are
handled by the React frontend against the already-cleaned in-memory dataset,
which is what keeps them feeling instant even at thousands of rows. This
endpoint set exists so the *same* filtering/export logic is also available
server-side (e.g. for a non-JS client, or to verify the frontend's math).
"""
import io
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .cleaning import clean_dataframe
from .schemas import StatusUpdate
from .store import df_to_records, store

app = FastAPI(title="Student Data Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo scope; restrict to your deployed frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_upload(filename: str, raw_bytes: bytes) -> pd.DataFrame:
    lower = filename.lower()
    try:
        if lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(raw_bytes))
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(raw_bytes))
    except Exception as exc:  # pragma: no cover - defensive, exercised via API tests
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}") from exc
    raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a .csv or .xlsx file.")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_df = _read_upload(file.filename or "", raw_bytes)

    try:
        cleaned_df, report = clean_dataframe(raw_df)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.set(cleaned_df, report)
    return {"students": df_to_records(cleaned_df), "report": report.to_dict()}


@app.get("/api/students")
def get_students():
    df = store.get_df()
    report = store.get_report()
    if df is None:
        raise HTTPException(status_code=404, detail="No dataset uploaded yet.")
    return {"students": df_to_records(df), "report": report.to_dict()}


@app.patch("/api/students/{student_id}/status")
def update_status(student_id: int, body: StatusUpdate):
    updated = store.update_status(student_id, body.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Student not found or no dataset uploaded yet.")
    return updated


@app.get("/api/export")
def export_csv(min_total: int = 0, active_only: bool = True):
    df = store.get_df()
    if df is None:
        raise HTTPException(status_code=404, detail="No dataset uploaded yet.")

    filtered = df[df["Total"] >= min_total]
    if active_only:
        filtered = filtered[filtered["Status"] == "Active"]

    buffer = io.StringIO()
    filtered.drop(columns=["id"]).to_csv(buffer, index=False)
    buffer.seek(0)

    filename = f"shortlist_min{min_total}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
