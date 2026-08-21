from typing import Literal, Optional

from pydantic import BaseModel


class StatusUpdate(BaseModel):
    status: Literal["Active", "Debarred"]


class CleaningReportModel(BaseModel):
    rows_in: int
    rows_out: int
    exact_duplicates_removed: int
    names_normalized: int
    gender_unmapped: int
    grade_invalid: int
    marks_invalid: dict
    totals_corrected: int
    rows_incomplete: int


class Student(BaseModel):
    id: int
    Name: Optional[str] = None
    Gender: Optional[str] = None
    Grade: Optional[int] = None
    Math: Optional[int] = None
    Science: Optional[int] = None
    English: Optional[int] = None
    Total: Optional[int] = None
    Status: str = "Active"


class UploadResponse(BaseModel):
    students: list[Student]
    report: CleaningReportModel
