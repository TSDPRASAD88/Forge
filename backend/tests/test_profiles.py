from fastapi.testclient import TestClient

from app.domain.enums import ExamType
from app.domain.profiles import PROFILES
from app.main import app


def test_every_exam_has_a_profile():
    for exam in ExamType:
        assert exam in PROFILES


def test_profiles_endpoint():
    with TestClient(app) as client:
        res = client.get("/api/profiles")
        assert res.status_code == 200
        assert len(res.json()) == len(ExamType)

        res = client.get("/api/profiles/ssc_cgl")
        assert res.status_code == 200
        assert res.json()["exam"] == "ssc_cgl"