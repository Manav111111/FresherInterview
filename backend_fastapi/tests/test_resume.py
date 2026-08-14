import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from app.main import app

client = TestClient(app)


def _create_sample_pdf() -> bytes:
    """Creates a sample PDF in-memory for testing."""
    writer = PdfWriter()
    # Add a blank page
    page = writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    stream.seek(0)
    return stream.getvalue()


def test_resume_upload_and_get_flow():
    # 1. Login to establish authenticated session
    login_resp = client.post("/api/auth/login", json={"token": "test_candidate_token"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    user_id = login_resp.json()["user"]["userId"]
    print(f"Authenticated as user {user_id}")

    # 2. Generate sample PDF
    pdf_bytes = _create_sample_pdf()

    # 3. Test POST /api/resume/upload
    files = {
        "resume": ("candidate_resume.pdf", pdf_bytes, "application/pdf"),
    }
    upload_resp = client.post("/api/resume/upload", files=files)
    assert upload_resp.status_code == 200, f"Resume upload failed: {upload_resp.text}"
    upload_data = upload_resp.json()

    assert upload_data["success"] is True
    assert "data" in upload_data
    resume = upload_data["data"]
    assert "skills" in resume
    assert "score" in resume
    assert isinstance(resume["score"], int)
    assert "summary" in resume
    print(f"Resume analyzed successfully! Candidate: {resume['name']}, ATS Score: {resume['score']}/100")
    print(f"Detected Skills: {resume['skills']}")

    # 4. Test GET /api/resume/get-resume
    get_resp = client.get("/api/resume/get-resume")
    assert get_resp.status_code == 200, f"Get resume failed: {get_resp.text}"
    get_data = get_resp.json()
    assert get_data["success"] is True
    assert get_data["data"]["score"] == resume["score"]
    assert get_data["data"]["name"] == resume["name"]
    print(f"Retrieved cached resume successfully (Source: {get_data.get('source')})")

    print("\nALL PHASE 3 RESUME TESTS PASSED!")


if __name__ == "__main__":
    test_resume_upload_and_get_flow()
