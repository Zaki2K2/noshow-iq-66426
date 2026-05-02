"""
preprocess.py — Clean and transform the raw appointments dataset.

The raw Kaggle dataset has messy column names and needs several fixes
before a model can learn from it. This module does all of that.

Typical usage:
    from noshow_iq.preprocess import load_and_clean, get_feature_columns

    df = load_and_clean("data/raw/appointments.csv")
    X = df[get_feature_columns()]
    y = df["no_show"]
"""

import pandas as pd


# ──────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────

def load_and_clean(csv_path: str) -> pd.DataFrame:
    """
    Load the raw CSV and return a clean DataFrame ready for modelling.

    Steps performed:
      1. Rename messy columns to snake_case.
      2. Parse date columns.
      3. Drop invalid ages (negative values).
      4. Engineer two new features: days_in_advance, appointment_weekday.
      5. Encode the target as binary (1 = no-show, 0 = showed up).

    Parameters
    ----------
    csv_path : str
        Path to the raw appointments CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with engineered features.
    """
    df = pd.read_csv(csv_path)

    # Step 1 — fix column names (the dataset has typos and hyphens)
    df = _rename_columns(df)

    # Step 2 — parse date strings into proper datetime objects
    df["scheduled_day"] = pd.to_datetime(df["scheduled_day"], utc=True)
    df["appointment_day"] = pd.to_datetime(df["appointment_day"], utc=True)

    # Step 3 — remove rows where age makes no sense
    df = df[df["age"] >= 0].copy()

    # Step 4 — engineer features
    df = _engineer_features(df)

    # Step 5 — convert "Yes"/"No" target to 1/0
    # 1 means the patient did NOT show up (the "bad" outcome we want to predict)
    df["no_show"] = (df["no_show_raw"] == "Yes").astype(int)

    return df


def get_feature_columns() -> list:
    """
    Return the list of column names used as model input features.

    Keeping this in one place means the API and training code
    always use exactly the same features.
    """
    return [
        "age",
        "scholarship",
        "hypertension",
        "diabetes",
        "alcoholism",
        "handicap",
        "sms_received",
        "days_in_advance",
        "appointment_weekday",
    ]


# ──────────────────────────────────────────────
# Private helpers (used only inside this module)
# ──────────────────────────────────────────────

def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise all column names to lowercase snake_case."""
    rename_map = {
        "PatientId":        "patient_id",
        "AppointmentID":    "appointment_id",
        "Gender":           "gender",
        "ScheduledDay":     "scheduled_day",
        "AppointmentDay":   "appointment_day",
        "Age":              "age",
        "Neighbourhood":    "neighbourhood",
        "Scholarship":      "scholarship",
        # The dataset has a typo: "Hipertension" instead of "Hypertension"
        "Hipertension":     "hypertension",
        "Diabetes":         "diabetes",
        "Alcoholism":       "alcoholism",
        # Another typo: "Handcap" instead of "Handicap"
        "Handcap":          "handicap",
        "SMS_received":     "sms_received",
        # Keep the raw string so we can inspect it before encoding
        "No-show":          "no_show_raw",
    }
    # Only rename columns that actually exist (makes unit-testing easier)
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(columns=existing)


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns that help the model learn patterns."""

    # Feature 1: how many days ahead was the appointment booked?
    # Patients who book far in advance might be more likely to forget.
    df["days_in_advance"] = (
        df["appointment_day"] - df["scheduled_day"]
    ).dt.days

    # Clip negative values that arise from timezone edge cases
    df["days_in_advance"] = df["days_in_advance"].clip(lower=0)

    # Feature 2: which weekday is the appointment on? (0=Monday … 6=Sunday)
    # Friday appointments may have different no-show rates than Mondays.
    df["appointment_weekday"] = df["appointment_day"].dt.weekday

    return df
