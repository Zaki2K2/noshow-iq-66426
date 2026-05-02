"""
test_api.py — Integration tests for the FastAPI endpoints.

We use FastAPI's TestClient so no real server needs to be running.
The ML model is replaced with a simple stub so the tests are fast
and don't depend on a trained model file being present.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from noshow_iq.api import app


# ──────────────────────────────────────────────
# Shared fixture: a TestClient with a stubbed model
# ──────────────────────────────────────────────

@pytest.fixture
def client():
    """
    Provide a TestClient where the global _model is replaced with a mock
    so /predict works without a real .joblib file.
    """
    stub_result = {
        "probability":    0.75,
        "risk_level":     "HIGH",
        "recommendation": "Send SMS reminder + phone call.",
    }

    # Patch the module-level _model variable and model_predict function
    with patch("noshow_iq.api._model", new=MagicMock()):
        with patch("noshow_iq.api.model_predict", return_value=stub_result):
            with patch("noshow_iq.api.database.insert_prediction", return_value="fake_id"):
                yield TestClient(app)


# ──────────────────────────────────────────────
# Test 10 — GET /health returns 200 and expected keys
# ──────────────────────────────────────────────

def test_health_endpoint(client):
    """
    /health should always return HTTP 200 with a JSON body that
    contains 'status', 'version', and 'model_loaded'.
    """
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version"      in body
    assert "model_loaded" in body


# ──────────────────────────────────────────────
# Test 11 — POST /predict returns prediction keys
# ──────────────────────────────────────────────

def test_predict_endpoint(client):
    """
    /predict should return HTTP 200 and a JSON body with
    probability, risk_level, and recommendation.
    """
    payload = {
        "age":                 45,
        "scholarship":          0,
        "hypertension":         1,
        "diabetes":             0,
        "alcoholism":           0,
        "handicap":             0,
        "sms_received":         1,
        "days_in_advance":      5,
        "appointment_weekday":  3,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "probability"    in body
    assert "risk_level"     in body
    assert "recommendation" in body


# ──────────────────────────────────────────────
# Test 12 — POST /predict rejects bad input
# ──────────────────────────────────────────────

def test_predict_rejects_invalid_age(client):
    """
    Sending age = -5 (below the ge=0 constraint) should return HTTP 422
    (Unprocessable Entity), not 200.
    """
    payload = {
        "age":                 -5,   # INVALID
        "scholarship":          0,
        "hypertension":         0,
        "diabetes":             0,
        "alcoholism":           0,
        "handicap":             0,
        "sms_received":         0,
        "days_in_advance":      0,
        "appointment_weekday":  0,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 422, "Should reject age < 0"
