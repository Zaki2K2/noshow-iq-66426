"""
db.py — MongoDB connection and all database operations.

Design decisions:
- One shared MongoClient is created when this module is first imported.
- Every function uses aggregation pipelines for /stats so no stats
  logic lives in Python — the database does the heavy lifting.
- All functions are safe to call even if MongoDB is unreachable;
  they raise an exception that the caller can catch.
"""

from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection

from noshow_iq.config import settings


# ──────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────

def _get_db():
    """Return a handle to the configured MongoDB database."""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
    return client[settings.MONGO_DB_NAME]


def _predictions_col() -> Collection:
    return _get_db()["predictions"]


def _training_runs_col() -> Collection:
    return _get_db()["training_runs"]


# ──────────────────────────────────────────────
# Prediction operations
# ──────────────────────────────────────────────

def insert_prediction(document: dict) -> str:
    """
    Save one prediction result to the 'predictions' collection.

    Parameters
    ----------
    document : dict — the full prediction payload (features + result).

    Returns
    -------
    str — the inserted document's _id as a string.
    """
    document["created_at"] = datetime.now(timezone.utc).isoformat()
    result = _predictions_col().insert_one(document)
    return str(result.inserted_id)


def get_recent_predictions(limit: int = 20) -> list:
    """
    Fetch the most recent `limit` predictions, newest first.

    Returns a list of dicts (MongoDB _id is converted to string).
    """
    cursor = (
        _predictions_col()
        .find({}, {"_id": 1, "created_at": 1, "risk_level": 1, "probability": 1})
        .sort("created_at", -1)
        .limit(limit)
    )
    docs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


# ──────────────────────────────────────────────
# Stats (aggregation pipeline — no Python math)
# ──────────────────────────────────────────────

def get_prediction_stats() -> dict:
    """
    Use a MongoDB aggregation pipeline to compute:
      - total number of predictions
      - count per risk_level (HIGH / MEDIUM / LOW)
      - average probability

    No arithmetic is performed in Python — the database handles it.
    """
    pipeline = [
        {
            # Group ALL documents together ($group with _id: null)
            "$group": {
                "_id": None,
                "total":            {"$sum": 1},
                "avg_probability":  {"$avg": "$probability"},
            }
        },
        {
            # Re-shape the output to drop the useless _id: null field
            "$project": {
                "_id": 0,
                "total": 1,
                "avg_probability": {"$round": ["$avg_probability", 4]},
            }
        },
    ]

    # Second pipeline: count per risk level
    by_risk_pipeline = [
        {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    col = _predictions_col()

    summary_list = list(col.aggregate(pipeline))
    summary = summary_list[0] if summary_list else {"total": 0, "avg_probability": 0.0}

    by_risk = {
        doc["_id"]: doc["count"]
        for doc in col.aggregate(by_risk_pipeline)
        if doc["_id"] is not None
    }

    return {
        "total_predictions":  summary.get("total", 0),
        "avg_probability":    summary.get("avg_probability", 0.0),
        "by_risk_level":      by_risk,
    }


# ──────────────────────────────────────────────
# Training run operations
# ──────────────────────────────────────────────

def insert_training_run(document: dict) -> str:
    """
    Persist a training-run record (metrics, timestamp, etc.) to MongoDB.

    Parameters
    ----------
    document : dict — training metadata and metric scores.

    Returns
    -------
    str — inserted document's _id as a string.
    """
    result = _training_runs_col().insert_one(document)
    return str(result.inserted_id)
