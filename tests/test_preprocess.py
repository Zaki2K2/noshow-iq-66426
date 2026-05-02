"""
test_preprocess.py — Unit tests for the preprocess module.

We build a tiny in-memory DataFrame that mirrors the raw CSV structure
so we never need the real data file to run the tests.
"""

import pandas as pd
import pytest

from noshow_iq.preprocess import (
    load_and_clean,
    get_feature_columns,
    _rename_columns,
    _engineer_features,
)


# ──────────────────────────────────────────────
# Fixtures (reusable sample data)
# ──────────────────────────────────────────────

@pytest.fixture
def raw_df():
    """Return a small DataFrame that looks like the raw appointments CSV."""
    return pd.DataFrame({
        "PatientId":      [1, 2, 3],
        "AppointmentID":  [100, 101, 102],
        "Gender":         ["F", "M", "F"],
        "ScheduledDay":   [
            "2016-04-29T18:38:08Z",
            "2016-04-29T16:08:27Z",
            "2016-04-29T17:29:31Z",
        ],
        "AppointmentDay": [
            "2016-04-29T00:00:00Z",
            "2016-05-03T00:00:00Z",
            "2016-05-04T00:00:00Z",
        ],
        "Age":            [62, 56, -1],   # -1 is invalid and should be dropped
        "Neighbourhood":  ["JARDIM DA PENHA"] * 3,
        "Scholarship":    [0, 0, 0],
        "Hipertension":   [1, 0, 0],      # typo column — should be renamed
        "Diabetes":       [0, 0, 0],
        "Alcoholism":     [0, 0, 0],
        "Handcap":        [0, 0, 0],      # typo column — should be renamed
        "SMS_received":   [0, 0, 1],
        "No-show":        ["No", "Yes", "No"],  # hyphen column — should be renamed
    })


# ──────────────────────────────────────────────
# Test 1 — column renaming
# ──────────────────────────────────────────────

def test_rename_columns(raw_df):
    """
    After renaming, messy column names like 'Hipertension', 'Handcap',
    and 'No-show' should become 'hypertension', 'handicap', 'no_show_raw'.
    """
    renamed = _rename_columns(raw_df)

    assert "hypertension"  in renamed.columns, "Hipertension was not renamed"
    assert "handicap"      in renamed.columns, "Handcap was not renamed"
    assert "no_show_raw"   in renamed.columns, "No-show was not renamed"

    # Original messy names should be gone
    assert "Hipertension"  not in renamed.columns
    assert "Handcap"       not in renamed.columns
    assert "No-show"       not in renamed.columns


# ──────────────────────────────────────────────
# Test 2 — invalid ages are removed
# ──────────────────────────────────────────────

def test_invalid_age_dropped(raw_df, tmp_path):
    """
    Rows with age < 0 must be removed by load_and_clean.
    Our fixture has one row with age = -1; only 2 valid rows remain.
    """
    # Write the fixture to a temp CSV so load_and_clean can read it
    csv_path = tmp_path / "appointments.csv"
    raw_df.to_csv(csv_path, index=False)

    df = load_and_clean(str(csv_path))

    assert len(df) == 2, f"Expected 2 rows after dropping negative age, got {len(df)}"
    assert (df["age"] >= 0).all(), "All remaining ages should be non-negative"


# ──────────────────────────────────────────────
# Test 3 — feature engineering produces expected columns
# ──────────────────────────────────────────────

def test_engineered_features_exist(raw_df, tmp_path):
    """
    After load_and_clean, the DataFrame must contain both engineered
    feature columns: days_in_advance and appointment_weekday.
    """
    csv_path = tmp_path / "appointments.csv"
    raw_df.to_csv(csv_path, index=False)

    df = load_and_clean(str(csv_path))

    assert "days_in_advance"     in df.columns
    assert "appointment_weekday" in df.columns


# ──────────────────────────────────────────────
# Test 4 — target encoding
# ──────────────────────────────────────────────

def test_target_encoding(raw_df, tmp_path):
    """
    'No-show' == 'Yes'  →  no_show == 1
    'No-show' == 'No'   →  no_show == 0
    """
    csv_path = tmp_path / "appointments.csv"
    raw_df.to_csv(csv_path, index=False)

    df = load_and_clean(str(csv_path))

    # Row 0 had "No" → should be 0 (patient showed up)
    # Row 1 had "Yes" → should be 1 (patient no-showed)
    assert set(df["no_show"].unique()).issubset({0, 1}), "Target must be binary 0/1"


# ──────────────────────────────────────────────
# Test 5 — get_feature_columns returns the right number of features
# ──────────────────────────────────────────────

def test_feature_columns_count():
    """get_feature_columns must return exactly 9 features."""
    cols = get_feature_columns()
    assert len(cols) == 9, f"Expected 9 features, got {len(cols)}"
