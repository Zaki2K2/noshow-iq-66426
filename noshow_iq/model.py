"""
model.py — Train, evaluate, save, load, and run inference on the
           no-show prediction model.

The model is a LogisticRegression with class_weight="balanced" so
that the minority class (no-show) is not ignored during training.

Typical usage:
    from noshow_iq.model import train, predict, evaluate, load_model

    model = train("data/raw/appointments.csv")
    proba  = predict(model, feature_dict)
    metrics = evaluate(model, X_test, y_test)
"""

import os
import joblib
import pandas as pd
from datetime import datetime, timezone
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from noshow_iq.preprocess import load_and_clean, get_feature_columns
from noshow_iq.config import settings


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def train(csv_path: str, save_path: str | None = None) -> Pipeline:
    """
    Load data, train a LogisticRegression pipeline, save it to disk,
    and store training metrics in MongoDB.

    Parameters
    ----------
    csv_path  : path to the raw appointments CSV.
    save_path : where to write model.joblib (defaults to settings.MODEL_PATH).

    Returns
    -------
    Trained sklearn Pipeline object.
    """
    save_path = save_path or settings.MODEL_PATH

    # 1. Load and clean the dataset
    print(f"[train] Loading data from {csv_path} …")
    df = load_and_clean(csv_path)

    features = get_feature_columns()
    X = df[features]
    y = df["no_show"]

    print(f"[train] Dataset shape: {X.shape} | No-show rate: {y.mean():.2%}")

    # 2. Split into train / test sets (80 / 20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Build a Pipeline: scale features → logistic regression
    #    class_weight="balanced" compensates for the imbalance between
    #    show-ups (~80 %) and no-shows (~20 %).
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )),
    ])

    # 4. Fit the model
    print("[train] Fitting model …")
    pipeline.fit(X_train, y_train)

    # 5. Evaluate and print a human-readable report
    metrics = evaluate(pipeline, X_test, y_test)
    print("[train] Classification report:")
    print(metrics["report"])

    # 6. Persist the trained pipeline to disk
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(pipeline, save_path)
    print(f"[train] Model saved to {save_path}")

    # 7. Store this run's metrics in MongoDB (best-effort; don't crash if DB is down)
    _store_training_run(metrics, csv_path)

    return pipeline


def load_model(model_path: str | None = None) -> Pipeline:
    """
    Load a previously trained Pipeline from disk.

    Parameters
    ----------
    model_path : path to model.joblib (defaults to settings.MODEL_PATH).
    """
    model_path = model_path or settings.MODEL_PATH
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No model found at '{model_path}'. "
            "Run `python -m noshow_iq.model` to train first."
        )
    return joblib.load(model_path)


def predict(model: Pipeline, features: dict) -> dict:
    """
    Return a prediction dict for a single appointment.

    Parameters
    ----------
    model    : trained sklearn Pipeline.
    features : dict with keys matching get_feature_columns().

    Returns
    -------
    dict with keys: probability, risk_level, recommendation.
    """
    feature_order = get_feature_columns()

    # Build a single-row DataFrame in the correct column order
    row = pd.DataFrame([features])[feature_order]

    # Probability of class 1 (= no-show)
    proba = float(model.predict_proba(row)[0][1])

    risk_level, recommendation = _interpret(proba)

    return {
        "probability": round(proba, 4),
        "risk_level": risk_level,
        "recommendation": recommendation,
    }


def evaluate(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Compute precision, recall, and F1 for both classes.

    Returns a dict containing the full text report and per-class scores.
    """
    y_pred = model.predict(X_test)

    report = classification_report(y_test, y_pred, target_names=["showed_up", "no_show"])

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average=None, labels=[0, 1]
    )

    return {
        "report": report,
        "showed_up": {
            "precision": round(float(precision[0]), 4),
            "recall":    round(float(recall[0]), 4),
            "f1":        round(float(f1[0]), 4),
        },
        "no_show": {
            "precision": round(float(precision[1]), 4),
            "recall":    round(float(recall[1]), 4),
            "f1":        round(float(f1[1]), 4),
        },
    }


# ──────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────

def _interpret(proba: float) -> tuple[str, str]:
    """Map a probability score to a human-readable risk label and advice."""
    if proba >= 0.70:
        return (
            "HIGH",
            "Send SMS reminder + phone call 24 h before the appointment.",
        )
    elif proba >= 0.40:
        return (
            "MEDIUM",
            "Send an SMS reminder the day before the appointment.",
        )
    else:
        return (
            "LOW",
            "No special action required.",
        )


def _store_training_run(metrics: dict, csv_path: str) -> None:
    """Persist training metrics to MongoDB. Silently skips if DB is unavailable."""
    try:
        from noshow_iq.db import insert_training_run

        insert_training_run({
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "csv_path": csv_path,
            "no_show_f1": metrics["no_show"]["f1"],
            "showed_up_f1": metrics["showed_up"]["f1"],
        })
    except Exception as exc:
        # Do not crash the training run just because MongoDB is down
        print(f"[train] Warning: could not store metrics in MongoDB — {exc}")


# ──────────────────────────────────────────────
# Allow running as a script: python -m noshow_iq.model
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    csv = sys.argv[1] if len(sys.argv) > 1 else "data/raw/appointments.csv"
    train(csv)
