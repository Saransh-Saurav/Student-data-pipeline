"""
Data cleaning pipeline for the Student Data Pipeline & UI app.

Every rule is a small, pure, independently-testable function operating on a
single raw value. `clean_dataframe` orchestrates them over a full CSV/XLSX
upload and returns both the cleaned data and a transparency report describing
exactly what was changed, so the UI can show the user what the pipeline did
(not just the end result).

Design notes / assumptions (see README "Data Cleaning Logic" for the full
write-up):

- Names: stray quote/apostrophe/whitespace characters are stripped and the
  result is Title-cased. Repeated first names across rows are NOT treated as
  duplicates on their own -- a cohort of students legitimately shares first
  names. A "duplicate" is only ever a fully-identical row.
- Gender: the raw data mixes text (Male/Female/M/F, mixed case) with a
  numeric code (0/1) that has no codebook attached. We adopt the common
  convention `1 = Male, 0 = Female`. This is an explicit, documented
  assumption -- flip GENDER_MAP if the real codebook says otherwise.
- Grade: accepts both "7" and "Grade 7" and normalizes to an int 1-12.
- Marks: accepts both "28" and "28 marks" and normalizes to an int 0-100.
- Total: always recalculated as Math + Science + English *after* cleaning.
  If the recalculated value differs from the value in the source file, the
  recalculated value wins (and the row is counted in `totals_corrected`).
  This is deliberately defensive: in the provided sample dataset every row's
  Total already matches once the marks are parsed, but the pipeline must not
  assume that will always be true.
- Missing/unparseable values are never silently zero-filled. They become
  null and the row is counted as `rows_incomplete` so the UI can surface it.
- Duplicates: only an *exact*, fully-identical row (all 7 fields match after
  cleaning) is treated as a duplicate and dropped (keep first). We deliberately
  do NOT flag rows that merely share Name+Grade+Gender: this cohort is drawn
  from a pool of ~20 first names across 3000 rows, so those collisions are
  statistically expected between different real students, not evidence of a
  duplicate entry. Flagging them would bury a genuine signal in thousands of
  false positives. A stable per-student ID (roll number/email) would be
  needed for reliable identity-based fuzzy-dup detection; see README
  "Known limitations".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Tuple

import pandas as pd

REQUIRED_COLUMNS = ["Name", "Gender", "Grade", "Math", "Science", "English", "Total"]

# Documented assumption -- see module docstring.
GENDER_MAP = {
    "m": "Male", "male": "Male", "1": "Male",
    "f": "Female", "female": "Female", "0": "Female",
}

MARK_MIN, MARK_MAX = 0, 100
GRADE_MIN, GRADE_MAX = 1, 12

_STRIP_CHARS = "'\" \t\n\r"


def _is_missing(raw) -> bool:
    if raw is None:
        return True
    if isinstance(raw, float) and pd.isna(raw):
        return True
    if isinstance(raw, str) and raw.strip() == "":
        return True
    return False


def clean_name(raw) -> Optional[str]:
    """Strip stray quote/apostrophe/whitespace junk and Title-case the name."""
    if _is_missing(raw):
        return None
    s = str(raw).strip(_STRIP_CHARS)
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    return s.title()


def clean_gender(raw) -> Tuple[str, bool]:
    """Return (canonical_gender, was_unmapped)."""
    if _is_missing(raw):
        return "Unknown", True
    key = str(raw).strip().lower()
    if key in GENDER_MAP:
        return GENDER_MAP[key], False
    return "Unknown", True


def clean_grade(raw) -> Tuple[Optional[int], bool]:
    """Return (grade 1-12, was_invalid). Accepts '7' or 'Grade 7'."""
    if _is_missing(raw):
        return None, True
    match = re.search(r"-?\d+", str(raw))
    if not match:
        return None, True
    value = int(match.group(0))
    if value < GRADE_MIN or value > GRADE_MAX:
        return None, True
    return value, False


def clean_mark(raw) -> Tuple[Optional[int], bool]:
    """Return (mark 0-100, was_invalid). Accepts '28' or '28 marks'."""
    if _is_missing(raw):
        return None, True
    match = re.search(r"-?\d+", str(raw))
    if not match:
        return None, True
    value = int(match.group(0))
    if value < MARK_MIN or value > MARK_MAX:
        return None, True
    return value, False


@dataclass
class CleaningReport:
    rows_in: int = 0
    rows_out: int = 0
    exact_duplicates_removed: int = 0
    names_normalized: int = 0
    gender_unmapped: int = 0
    grade_invalid: int = 0
    marks_invalid: dict = field(default_factory=dict)
    totals_corrected: int = 0
    rows_incomplete: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _find_column(columns, target: str) -> Optional[str]:
    lower_map = {str(c).strip().lower(): c for c in columns}
    return lower_map.get(target.lower())


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningReport]:
    """Run the full cleaning pipeline. Raises ValueError if required columns
    are missing (checked case-insensitively, whitespace-tolerant)."""
    report = CleaningReport(rows_in=len(df))

    colmap = {name: _find_column(df.columns, name) for name in REQUIRED_COLUMNS}
    missing = [k for k, v in colmap.items() if v is None]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    status_col = _find_column(df.columns, "Status")
    rename = {v: k for k, v in colmap.items()}
    work = df.rename(columns=rename).copy()

    # --- Name ---------------------------------------------------------
    original_names = work["Name"].astype(str)
    cleaned_names = work["Name"].apply(clean_name)
    report.names_normalized = int(
        sum(1 for a, b in zip(original_names, cleaned_names) if a.strip(_STRIP_CHARS) != (b or ""))
    )
    work["Name"] = cleaned_names

    # --- Gender ---------------------------------------------------------
    gender_results = work["Gender"].apply(clean_gender)
    work["Gender"] = [r[0] for r in gender_results]
    report.gender_unmapped = int(sum(r[1] for r in gender_results))

    # --- Grade ---------------------------------------------------------
    grade_results = work["Grade"].apply(clean_grade)
    report.grade_invalid = int(sum(r[1] for r in grade_results))
    work["Grade"] = pd.to_numeric(pd.Series([r[0] for r in grade_results], index=work.index), errors="coerce")

    # --- Marks -----------------------------------------------------------
    # Cast through pd.to_numeric (not plain object lists) so missing values
    # become real NaN and downstream arithmetic (the Total recalculation)
    # works without tripping over Python `None` in an object-dtype column.
    marks_invalid = {}
    for subject in ("Math", "Science", "English"):
        results = work[subject].apply(clean_mark)
        marks_invalid[subject] = int(sum(r[1] for r in results))
        work[subject] = pd.to_numeric(pd.Series([r[0] for r in results], index=work.index), errors="coerce")
    report.marks_invalid = marks_invalid

    # --- Total: recalculate, defensively -------------------------------
    has_all_marks = work[["Math", "Science", "English"]].notna().all(axis=1)
    recalculated = work[["Math", "Science", "English"]].sum(axis=1, skipna=True)
    original_total = pd.to_numeric(work["Total"], errors="coerce")
    mismatch = has_all_marks & (recalculated != original_total)
    report.totals_corrected = int(mismatch.sum())

    final_total = original_total.copy()
    final_total[has_all_marks] = recalculated[has_all_marks]
    final_total[~has_all_marks] = pd.NA
    work["Total"] = final_total

    # --- Incomplete rows (flagged, kept) --------------------------------
    check_cols = ["Name", "Gender", "Grade", "Math", "Science", "English", "Total"]
    report.rows_incomplete = int(work[check_cols].isna().any(axis=1).sum())

    # --- Exact duplicate rows: drop, keep first -------------------------
    before = len(work)
    work = work.drop_duplicates(subset=REQUIRED_COLUMNS, keep="first")
    report.exact_duplicates_removed = before - len(work)

    # --- Status: new state the app owns, default Active ----------------
    if status_col:
        work["Status"] = work[status_col].fillna("Active")
        valid_status = work["Status"].isin(["Active", "Debarred"])
        work.loc[~valid_status, "Status"] = "Active"
    else:
        work["Status"] = "Active"

    # Use pandas' nullable integer dtype so whole numbers display as ints
    # (not 47.0) while still supporting NaN for genuinely incomplete rows.
    for col in ("Grade", "Math", "Science", "English", "Total"):
        work[col] = work[col].astype("Int64")

    work = work.reset_index(drop=True)
    work.insert(0, "id", work.index + 1)

    report.rows_out = len(work)
    return work, report
