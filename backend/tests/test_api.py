import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CSV = (
    "Name,Gender,Grade,Math,Science,English,Total\n"
    "Navya',male,11,47,63,74,184\n"
    "ROHAN,F,Grade 3,16,77,8,101\n"
    "Aditi',0,Grade 11,28 marks,43 marks,46,117\n"
)


def _upload(csv_text=SAMPLE_CSV, filename="students.csv"):
    return client.post(
        "/api/upload",
        files={"file": (filename, io.BytesIO(csv_text.encode()), "text/csv")},
    )


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_export_with_no_upload_returns_404():
    # Must run before any test uploads data -- the store is a module-level
    # singleton shared across this whole test session (mirrors the app's
    # actual single-process, single-dataset scope; see README).
    from app.store import store as shared_store
    assert shared_store.is_empty()
    resp = client.get("/api/export")
    assert resp.status_code == 404


def test_upload_cleans_and_returns_students():
    resp = _upload()
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["students"]) == 3
    assert body["students"][0]["Name"] == "Navya"
    assert body["students"][0]["Gender"] == "Male"
    assert body["report"]["rows_in"] == 3


def test_upload_rejects_unsupported_file_type():
    resp = client.post(
        "/api/upload",
        files={"file": ("students.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_missing_columns():
    bad_csv = "Name,Gender\nA,M\n"
    resp = _upload(csv_text=bad_csv)
    assert resp.status_code == 400


def test_get_students_after_upload():
    _upload()
    resp = client.get("/api/students")
    assert resp.status_code == 200
    assert len(resp.json()["students"]) == 3


def test_status_toggle_updates_and_persists():
    upload_resp = _upload()
    student_id = upload_resp.json()["students"][0]["id"]

    resp = client.patch(f"/api/students/{student_id}/status", json={"status": "Debarred"})
    assert resp.status_code == 200
    assert resp.json()["Status"] == "Debarred"

    resp2 = client.get("/api/students")
    updated = next(s for s in resp2.json()["students"] if s["id"] == student_id)
    assert updated["Status"] == "Debarred"


def test_status_toggle_rejects_unknown_value():
    upload_resp = _upload()
    student_id = upload_resp.json()["students"][0]["id"]
    resp = client.patch(f"/api/students/{student_id}/status", json={"status": "Graduated"})
    assert resp.status_code == 422  # pydantic Literal validation


def test_status_toggle_404_for_unknown_id():
    _upload()
    resp = client.patch("/api/students/999999/status", json={"status": "Active"})
    assert resp.status_code == 404


def test_export_respects_min_total_and_active_only():
    upload_resp = _upload()
    students = upload_resp.json()["students"]
    debarred_id = students[0]["id"]  # Navya, Total=184
    client.patch(f"/api/students/{debarred_id}/status", json={"status": "Debarred"})

    resp = client.get("/api/export", params={"min_total": 100, "active_only": True})
    assert resp.status_code == 200
    csv_text = resp.text
    assert "Navya" not in csv_text  # debarred, excluded even though Total >= 100
    assert "Rohan" in csv_text  # Total 101, active
    assert "Aditi" in csv_text  # Total 117, active
