import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.models import ExamSession

client = TestClient(app)

def test_api_root_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "TAMPER RESISTANT" in data["system"].upper()
    assert data["status"] == "OPERATIONAL"

def test_api_dashboard_stats():
    response = client.get("/api/exams/dashboard-stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_exams"] >= 1
    assert data["total_answer_sheets"] >= 1

def test_api_list_exams():
    response = client.get("/api/exams")
    assert response.status_code == 200
    exams = response.json()
    assert len(exams) >= 1
    assert "Computer Networks" in exams[0]["subject"]
