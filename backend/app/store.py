"""
Minimal in-memory store for the currently-uploaded, cleaned dataset.

This assessment app is intentionally single-dataset / single-process: one
upload replaces the previous dataset. That's a deliberate scope decision
(see README "Known limitations") -- a production version would persist to a
real database and scope data per user/session.
"""
import threading
from typing import Optional

import pandas as pd

from .cleaning import CleaningReport


class DataStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._df: Optional[pd.DataFrame] = None
        self._report: Optional[CleaningReport] = None

    def set(self, df: pd.DataFrame, report: CleaningReport) -> None:
        with self._lock:
            self._df = df
            self._report = report

    def get_df(self) -> Optional[pd.DataFrame]:
        with self._lock:
            return None if self._df is None else self._df.copy()

    def get_report(self) -> Optional[CleaningReport]:
        with self._lock:
            return self._report

    def update_status(self, student_id: int, status: str) -> Optional[dict]:
        with self._lock:
            if self._df is None:
                return None
            mask = self._df["id"] == student_id
            if not mask.any():
                return None
            self._df.loc[mask, "Status"] = status
            return _row_to_record(self._df.loc[mask].iloc[0])

    def is_empty(self) -> bool:
        with self._lock:
            return self._df is None


def _row_to_record(row) -> dict:
    record = row.to_dict()
    for key, value in record.items():
        if pd.isna(value):
            record[key] = None
    return record


def df_to_records(df: pd.DataFrame) -> list:
    return [_row_to_record(row) for _, row in df.iterrows()]


store = DataStore()
