"""
test_model.py — Unit tests for model training, inference, and persistence.

These tests use a tiny synthetic dataset so they run fast without the
real 100 k-row CSV.
"""

import os
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from noshow_iq.model import load_model, predict, evaluate
from noshow_iq.preprocess import get_feature_columns


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_tiny_dataset(tmp_path):
    """
    Write a minimal appointments CSV to tmp_path and return its path.
    We create 40 rows — enough for an 80/20 train-test split.
    """
    import numpy as np

    rng = np.random.default_rng(0)
    n = 40

    data = {
        "PatientId":      range(n),
        "AppointmentID":  range(1000, 1000 + n),
        "Gender":         ["F"] * n,
        "ScheduledDay":   ["2016-04-29T18:38:08Z"] * n,
        "AppointmentDay": ["2016-05-03T00:00:00Z"] * n,
        "Age":            rng.integers(18, 80, n),
        "Neighbourhood":  ["JARDIM"] * n,
        "Scholarship":    rng.integers(0, 2, n),
        "Hipertension":   rng.integers(0, 2, n),
        "Diabetes":       rng.integers(0, 2, n),
        "Alcoholism":     rng.integers(0, 2, n),
        "Handcap":        rng.integers(0, 2, n),
        "SMS_received":   rng.integers(0, 2, n),
        # ~25 % no-shows
        "No-show":        ["Yes" if i % 4 == 0 else "No" for i in range(n)],
    }

    csv_path = tmp_path / "appointments.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return str(csv_path)


# ──────────────────────────────────────────────
# Test 6 — train() produces a sklearn Pipeline
# ──────────────────────────────────────────────

def test_train_returns_pipeline(tmp_path):
    """train() must return an sklearn Pipeline object."""
    from noshow_iq.model import train

    csv_path = _make_tiny_dataset(tmp_path)
    save_path = str(tmp_path / "model.joblib")

    model = train(csv_path, save_path=save_path)

    assert isinstance(model, Pipeline), "train() should return an sklearn Pipeline"


# ──────────────────────────────────────────────
# Test 7 — model is saved and can be reloaded
# ──────────────────────────────────────────────

def test_model_saved_and_loadable(tmp_path):
    """After train(), the .joblib file must exist and be loadable."""
    from noshow_iq.model import train

    csv_path  = _make_tiny_dataset(tmp_path)
    save_path = str(tmp_path / "model.joblib")

    train(csv_path, save_path=save_path)

    assert os.path.exists(save_path), "model.joblib was not written to disk"

    reloaded = load_model(save_path)
    assert isinstance(reloaded, Pipeline)


# ──────────────────────────────────────────────
# Test 8 — predict() returns expected keys
# ──────────────────────────────────────────────

def test_predict_output_shape(tmp_path):
    """predict() must return a dict with probability, risk_level, recommendation."""
    from noshow_iq.model import train

    csv_path  = _make_tiny_dataset(tmp_path)
    save_path = str(tmp_path / "model.joblib")

    model = train(csv_path, save_path=save_path)

    sample_features = {
        "age":                 35,
        "scholarship":          0,
        "hypertension":         0,
        "diabetes":             0,
        "alcoholism":           0,
        "handicap":             0,
        "sms_received":         1,
        "days_in_advance":      4,
        "appointment_weekday":  2,
    }

    result = predict(model, sample_features)

    assert "probability"    in result
    assert "risk_level"     in result
    assert "recommendation" in result
    assert 0.0 <= result["probability"] <= 1.0
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


# ──────────────────────────────────────────────
# Test 9 — load_model raises on missing file
# ──────────────────────────────────────────────

def test_load_model_raises_if_missing(tmp_path):
    """load_model() must raise FileNotFoundError when no file exists."""
    with pytest.raises(FileNotFoundError):
        load_model(str(tmp_path / "nonexistent.joblib"))
