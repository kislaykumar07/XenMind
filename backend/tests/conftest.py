import os
import pathlib

# Use an isolated test database BEFORE app modules import settings/engine.
TEST_DB = pathlib.Path(__file__).resolve().parent.parent / "xenmind_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.services.auth import make_session

    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {make_session('test@xenmind.local', 'Test User')}"
        yield c


@pytest.fixture(scope="session")
def anon_client():
    with TestClient(app) as c:
        yield c
