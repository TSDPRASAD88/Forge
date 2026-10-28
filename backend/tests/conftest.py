import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.db.mongo import get_db
from app.main import app


@pytest.fixture
def client():
    db = AsyncMongoMockClient()["test_db"]          # in-memory fake Mongo
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()