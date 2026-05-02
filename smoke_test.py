"""
smoke_test.py - Quick end-to-end test against a live deployed API.

Usage:
    python smoke_test.py https://your-space.hf.space
    python smoke_test.py http://localhost:8000

The script tests three endpoints:
  /health  -- must return status "ok"
  /predict -- must return probability between 0 and 1
  /stats   -- must return total_predictions field

Exit code 0 = all tests passed.
Exit code 1 = at least one test failed.
"""

import sys
import requests

# ----------------------------------------------------------------
# Sample payload for /predict
# ----------------------------------------------------------------
PREDICT_PAYLOAD = {
    "age": 35,
    "scholarship": 0,
    "hypertension": 0,
    "diabetes": 0,
    "alcoholism": 0,
    "handicap": 0,
    "sms_received": 1,
    "days_in_advance": 7,
    "appointment_weekday": 2,
}


def check(name: str, passed: bool, detail: str = "") -> bool:
    """Print a result line and return the pass/fail boolean."""
    status = "PASS" if passed else "FAIL"
    symbol = "[OK]" if passed else "[FAIL]"
    print(f"  {symbol} {name:<35} {status}  {detail}")
    return passed


def smoke_test(base_url: str) -> bool:
    """Run all smoke checks; return True only if every check passes."""
    base_url = base_url.rstrip("/")
    print(f"\nSmoke-testing  {base_url}")
    print("-" * 60)

    all_passed = True

    # 1. GET /health
    try:
        r = requests.get(f"{base_url}/health", timeout=10)
        body = r.json()
        ok = r.status_code == 200 and body.get("status") == "ok"
        all_passed &= check("/health returns 200 + status ok", ok, f"HTTP {r.status_code}")
    except Exception as exc:
        all_passed &= check("/health reachable", False, str(exc))

    # 2. POST /predict
    try:
        r = requests.post(
            f"{base_url}/predict",
            json=PREDICT_PAYLOAD,
            timeout=15,
        )
        body = r.json()
        has_keys = all(k in body for k in ("probability", "risk_level", "recommendation"))
        prob_ok = 0.0 <= body.get("probability", -1) <= 1.0 if has_keys else False
        all_passed &= check("/predict returns 200", r.status_code == 200, f"HTTP {r.status_code}")
        all_passed &= check("/predict has required keys", has_keys, str(list(body.keys())))
        all_passed &= check("/predict probability in [0,1]", prob_ok, str(body.get("probability")))
    except Exception as exc:
        all_passed &= check("/predict reachable", False, str(exc))

    # 3. GET /stats
    try:
        r = requests.get(f"{base_url}/stats", timeout=10)
        body = r.json()
        has_total = "total_predictions" in body
        all_passed &= check("/stats returns 200", r.status_code == 200, f"HTTP {r.status_code}")
        all_passed &= check("/stats has total_predictions", has_total, str(body))
    except Exception as exc:
        all_passed &= check("/stats reachable", False, str(exc))

    print("-" * 60)
    print(f"Result: {'ALL PASSED' if all_passed else 'SOME CHECKS FAILED'}\n")
    return all_passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <base-url>")
        print("       python smoke_test.py http://localhost:8000")
        sys.exit(1)

    success = smoke_test(sys.argv[1])
    sys.exit(0 if success else 1)
