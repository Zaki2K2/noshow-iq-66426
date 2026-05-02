"""
config.py — Central place to read all environment variables.

Never hardcode secrets here. All sensitive values come from the
.env file (local) or real environment variables (Docker / cloud).
"""

import os


class Settings:
    """Holds all configuration values read from environment variables."""

    # MongoDB connection string — injected by Docker / .env file
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    # Name of the MongoDB database to use
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "noshow_iq")

    # Path to the serialised model file
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/model.joblib")

    # "development", "production", "testing"
    APP_ENV: str = os.getenv("APP_ENV", "development")


# A single shared settings object imported everywhere else
settings = Settings()
