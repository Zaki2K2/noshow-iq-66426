"""
api.py — FastAPI application with four endpoints:

  GET  /health    — liveness probe
  POST /predict   — run inference on one appointment
  GET  /history   — last 20 predictions from MongoDB
  GET  /stats     — aggregated statistics via MongoDB pipeline

Run locally:
    uvicorn noshow_iq.api:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from noshow_iq import __version__
from noshow_iq.config import settings
from noshow_iq import db as database
from noshow_iq.model import load_model, predict as model_predict


# ──────────────────────────────────────────────
# Lifespan: load model once at startup
# ──────────────────────────────────────────────

# We store the loaded model in application state so we don't reload it
# on every request (which would be very slow).
_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ML model when the server starts; release on shutdown."""
    global _model
    try:
        _model = load_model(settings.MODEL_PATH)
        print(f"[startup] Model loaded from {settings.MODEL_PATH}")
    except FileNotFoundError as exc:
        # The server can still start without a model so you can see /health,
        # but /predict will return 503 until a model is trained.
        print(f"[startup] WARNING — {exc}")
    yield
    print("[shutdown] Goodbye.")


# ──────────────────────────────────────────────
# App instance
# ──────────────────────────────────────────────

app = FastAPI(
    title="NoShowIQ",
    description="Predict whether a clinic patient will miss their appointment.",
    version=__version__,
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Request / Response schemas  (Pydantic models)
# ──────────────────────────────────────────────

class AppointmentInput(BaseModel):
    """
    The data you send to /predict.

    All values come from the cleaned dataset columns.
    Use 1 for True, 0 for False on binary fields.
    """
    age:                  int   = Field(..., ge=0, le=115, example=35)
    scholarship:          int   = Field(..., ge=0, le=1,  example=0)
    hypertension:         int   = Field(..., ge=0, le=1,  example=0)
    diabetes:             int   = Field(..., ge=0, le=1,  example=0)
    alcoholism:           int   = Field(..., ge=0, le=1,  example=0)
    handicap:             int   = Field(..., ge=0, le=1,  example=0)
    sms_received:         int   = Field(..., ge=0, le=1,  example=1)
    days_in_advance:      int   = Field(..., ge=0,        example=7)
    appointment_weekday:  int   = Field(..., ge=0, le=6,  example=2)


class PredictionOutput(BaseModel):
    probability:      float
    risk_level:       str
    recommendation:   str
    model_version:    str


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.get("/health", tags=["Operations"])
def health():
    """
    Liveness probe — returns 200 if the API is running.
    Also reports whether a model is loaded and the current environment.
    """
    return {
        "status":       "ok",
        "version":      __version__,
        "environment":  settings.APP_ENV,
        "model_loaded": _model is not None,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }


@app.post("/predict", response_model=PredictionOutput, tags=["ML"])
def predict(appointment: AppointmentInput):
    """
    Accept one appointment's features and return a no-show risk prediction.

    The result is saved to MongoDB so you can review it later via /history.
    """
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Train a model first with: "
                   "python -m noshow_iq.model",
        )

    # Convert the Pydantic model to a plain dict for the ML pipeline
    features = appointment.model_dump()

    # Run inference
    result = model_predict(_model, features)

    # Build the response
    output = PredictionOutput(
        probability=result["probability"],
        risk_level=result["risk_level"],
        recommendation=result["recommendation"],
        model_version=__version__,
    )

    # Persist to MongoDB (best-effort — don't crash the API if DB is down)
    try:
        database.insert_prediction({**features, **result})
    except Exception as exc:
        print(f"[predict] Warning: could not save to MongoDB — {exc}")

    return output


@app.get("/history", tags=["Operations"])
def history():
    """Return the last 20 predictions stored in MongoDB."""
    try:
        records = database.get_recent_predictions(limit=20)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}")
    return {"count": len(records), "predictions": records}


@app.get("/stats", tags=["Operations"])
def stats():
    """
    Return aggregated statistics computed by a MongoDB aggregation pipeline.

    Includes:
      - total predictions made
      - average predicted probability
      - breakdown by risk level (HIGH / MEDIUM / LOW)
    """
    try:
        data = database.get_prediction_stats()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}")
    return data
