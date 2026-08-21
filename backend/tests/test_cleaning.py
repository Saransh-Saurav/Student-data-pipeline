"""
Unit tests for the cleaning pipeline. Scalar-function fixtures are drawn
directly from real dirty rows found in RM_Student_Selection_Dataset.xlsx
(quoted names, mixed-case names, '<n> marks' strings, 'Grade N' vs 'N',
and the 0/1 gender code) plus synthetic edge cases (missing values,
out-of-range values, mismatched Total, exact duplicate rows).
"""
import math
import pandas as pd
import pytest

from app.cleaning import (
    clean_name,
    clean_gender,
    clean_grade,
    clean_mark,
    clean_dataframe,
    REQUIRED_COLUMNS,
)


# --------------------------------------------------------------------------
# clean_name
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Navya'", "Navya"),
        ("Aditi'", "Aditi"),
        ('"Aarav"', "Aarav"),
        ('"Anika"', "Anika"),
        ("ROHAN", "Rohan"),
        ("ISHAAN", "Ishaan"),
        ("  Myra  ", "Myra"),
        ("kabir", "Kabir"),
    ],
)
def test_clean_name(raw, expected):
    assert clean_name(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "'\"", float("nan")])
def test_clean_name_missing(raw):
    assert clean_name(raw) is None


# --------------------------------------------------------------------------
# clean_gender
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("male", "Male"), ("Male", "Male"), ("M", "Male"), ("m", "Male"),
        ("female", "Female"), ("Female", "Female"), ("F", "Female"), ("f", "Female"),
        (1, "Male"), ("1", "Male"),
        (0, "Female"), ("0", "Female"),
    ],
)
def test_clean_gender_known(raw, expected):
    value, unmapped = clean_gender(raw)
    assert value == expected
    assert unmapped is False


@pytest.mark.parametrize("raw", ["other", "nonbinary", None, "", "  "])
def test_clean_gender_unknown_is_flagged(raw):
    value, unmapped = clean_gender(raw)
    assert value == "Unknown"
    assert unmapped is True


# --------------------------------------------------------------------------
# clean_grade
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Grade 3", 3), ("Grade 11", 11), ("11", 11), (7, 7), ("Grade 1", 1), ("12", 12),
    ],
)
def test_clean_grade_valid(raw, expected):
    value, invalid = clean_grade(raw)
    assert value == expected
    assert invalid is False


@pytest.mark.parametrize("raw", ["Grade 13", "0", "abc", None, "", 99])
def test_clean_grade_invalid(raw):
    value, invalid = clean_grade(raw)
    assert value is None
    assert invalid is True


# --------------------------------------------------------------------------
# clean_mark
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("28 marks", 28), ("92 marks", 92), ("47", 47), (74, 74), ("0", 0), ("100 marks", 100),
    ],
)
def test_clean_mark_valid(raw, expected):
    value, invalid = clean_mark(raw)
    assert value == expected
    assert invalid is False


@pytest.mark.parametrize("raw", ["150 marks", "-5", None, "", "abc"])
def test_clean_mark_invalid(raw):
    value, invalid = clean_mark(raw)
    assert value is None
    assert invalid is True


# --------------------------------------------------------------------------
# clean_dataframe (full pipeline)
# --------------------------------------------------------------------------

def make_df(rows):
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def test_pipeline_normalizes_dirty_row_like_real_data():
    df = make_df([
        ["Navya'", "male", 11, 47, 63, 74, 184],
        ["ROHAN", "F", "Grade 3", 16, 77, 8, 101],
        ["Aditi'", 0, "Grade 11", "28 marks", "43 marks", 46, 117],
    ])
    cleaned, report = clean_dataframe(df)
    assert list(cleaned["Name"]) == ["Navya", "Rohan", "Aditi"]
    assert list(cleaned["Gender"]) == ["Male", "Female", "Female"]
    assert list(cleaned["Grade"]) == [11, 3, 11]
    assert list(cleaned["Math"]) == [47, 16, 28]
    assert list(cleaned["Total"]) == [184, 101, 117]
    assert report.rows_in == 3
    assert report.rows_out == 3
    assert report.totals_corrected == 0


def test_pipeline_recalculates_mismatched_total():
    # Marks sum to 150 but the source file says Total=999 -> must be corrected.
    df = make_df([["Aarav", "M", "5", 50, 50, 50, 999]])
    cleaned, report = clean_dataframe(df)
    assert cleaned.loc[0, "Total"] == 150
    assert report.totals_corrected == 1


def test_pipeline_removes_exact_duplicate_rows():
    df = make_df([
        ["Diya", "F", "6", 80, 80, 80, 240],
        ["Diya", "F", "6", 80, 80, 80, 240],  # exact duplicate of row 0
        ["Diya", "F", "6", 70, 80, 80, 230],  # same identity, different marks -> NOT a duplicate
    ])
    cleaned, report = clean_dataframe(df)
    assert report.rows_in == 3
    assert report.exact_duplicates_removed == 1
    assert report.rows_out == 2


def test_pipeline_flags_unmapped_gender_and_invalid_marks_without_dropping_rows():
    df = make_df([["Zara", "nonbinary", "5", "150 marks", 40, 40, 300]])
    cleaned, report = clean_dataframe(df)
    assert report.rows_out == 1  # row is kept, not dropped
    assert report.gender_unmapped == 1
    assert report.marks_invalid["Math"] == 1
    assert pd.isna(cleaned.loc[0, "Math"])
    assert report.rows_incomplete == 1


def test_pipeline_defaults_status_to_active():
    df = make_df([["Kabir", "M", "9", 60, 60, 60, 180]])
    cleaned, _ = clean_dataframe(df)
    assert cleaned.loc[0, "Status"] == "Active"


def test_pipeline_raises_on_missing_required_column():
    df = pd.DataFrame([{"Name": "X", "Gender": "M"}])
    with pytest.raises(ValueError):
        clean_dataframe(df)


def test_pipeline_is_case_and_whitespace_tolerant_on_headers():
    df = pd.DataFrame([{
        " name ": "Kabir", "GENDER": "M", "grade": "9",
        "Math ": 60, " Science": 60, "english": 60, "TOTAL": 180,
    }])
    cleaned, report = clean_dataframe(df)
    assert report.rows_out == 1
    assert cleaned.loc[0, "Name"] == "Kabir"
