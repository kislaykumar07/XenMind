"""
Automated tests for the health endpoint.

TestClient calls the app in-process — no server needs to be running.
Run from backend/:   pytest -v
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert "environment" in body


def test_cors_allows_frontend_dev_origin():
    # Simulates the browser's CORS "preflight" check from the Vite dev server.
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_blocks_unknown_origin():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_unknown_route_returns_404():
    assert client.get("/api/does-not-exist").status_code == 404
