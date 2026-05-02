"""
scripts/generate_data.py — Generate a synthetic appointments dataset.

Use this when you don't have the real Kaggle CSV yet. Produces 2 000
rows that mirror the original column structure so the pipeline works
exactly the same way.

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --rows 5000 --out data/raw/appointments.csv
"""

import argparse
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)

    base_date = datetime(2016, 4, 1)

    # Scheduled day: random day within a 60-day window
    scheduled_offsets = rng.integers(0, 60, n_rows)
    scheduled_days = [
        (base_date + timedelta(days=int(d))).strftime("%Y-%m-%dT%H:%M:%SZ")
        for d in scheduled_offsets
    ]

    # Appointment day: 0–14 days AFTER the scheduled day
    advance = rng.integers(0, 15, n_rows)
    appointment_days = [
        (
            datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=int(a))
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        for s, a in zip(scheduled_days, advance)
    ]

    # Age: realistic clinic distribution (skewed toward older patients)
    ages = rng.integers(0, 95, n_rows)

    # Binary features with realistic prevalence rates
    scholarship   = rng.choice([0, 1], n_rows, p=[0.90, 0.10])
    hypertension  = rng.choice([0, 1], n_rows, p=[0.80, 0.20])
    diabetes      = rng.choice([0, 1], n_rows, p=[0.93, 0.07])
    alcoholism    = rng.choice([0, 1], n_rows, p=[0.97, 0.03])
    handcap       = rng.choice([0, 1], n_rows, p=[0.98, 0.02])
    sms_received  = rng.choice([0, 1], n_rows, p=[0.68, 0.32])

    # No-show: ~20 % rate (higher when booked far ahead or no SMS)
    no_show_prob = (
        0.12
        + 0.08 * (advance > 7)
        + 0.05 * (sms_received == 0)
        + 0.03 * (scholarship == 1)
    )
    no_show_prob = np.clip(no_show_prob, 0, 1)
    no_show_flag = rng.random(n_rows) < no_show_prob
    no_show = ["Yes" if f else "No" for f in no_show_flag]

    neighbourhoods = [
        "JARDIM DA PENHA", "MATA DA PRAIA", "PONTAL DE CAMBURI",
        "REPÚBLICA", "GOIABEIRAS", "CONQUISTA", "UNIVERSITÁRIO",
    ]

    return pd.DataFrame({
        "PatientId":      rng.integers(1_000_000, 9_999_999, n_rows),
        "AppointmentID":  rng.integers(5_000_000, 6_000_000, n_rows),
        "Gender":         rng.choice(["F", "M"], n_rows),
        "ScheduledDay":   scheduled_days,
        "AppointmentDay": appointment_days,
        "Age":            ages,
        "Neighbourhood":  rng.choice(neighbourhoods, n_rows),
        "Scholarship":    scholarship,
        "Hipertension":   hypertension,   # keep original typo
        "Diabetes":       diabetes,
        "Alcoholism":     alcoholism,
        "Handcap":        handcap,        # keep original typo
        "SMS_received":   sms_received,
        "No-show":        no_show,
    })


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic appointments CSV")
    parser.add_argument("--rows", type=int, default=2000, help="Number of rows")
    parser.add_argument("--out",  default="data/raw/appointments.csv", help="Output path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = generate(n_rows=args.rows)
    df.to_csv(args.out, index=False)

    no_show_rate = (df["No-show"] == "Yes").mean()
    print(f"Generated {len(df)} rows -> {args.out}")
    print(f"No-show rate: {no_show_rate:.1%}")


if __name__ == "__main__":
    main()
