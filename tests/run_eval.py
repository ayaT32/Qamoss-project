"""
Run the test set against a running instance of the API (local or Render)
and print accuracy + the all-important false-acceptance rate.

Usage:
    python tests/run_eval.py http://127.0.0.1:8000
    python tests/run_eval.py https://your-app.onrender.com
"""
import json
import sys
from pathlib import Path

import requests

TESTS_PATH = Path(__file__).parent / "test_cases.json"


def main(base_url: str):
    with open(TESTS_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    correct = 0
    false_accepts = 0  # predicted exact_match/minor_difference when expected was mismatch/not_found
    rows = []

    for case in cases:
        resp = requests.post(f"{base_url}/verify", json={"text": case["text"]}, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        predicted = result.get("status")
        expected = case["expected"]
        is_correct = predicted == expected
        correct += is_correct

        bad_statuses = {"exact_match", "minor_difference"}
        if expected in {"mismatch", "not_found"} and predicted in bad_statuses:
            false_accepts += 1

        rows.append((case["id"], expected, predicted, "✓" if is_correct else "✗"))

    print(f"{'ID':<5}{'Expected':<20}{'Predicted':<20}{'OK'}")
    for r in rows:
        print(f"{r[0]:<5}{r[1]:<20}{r[2]:<20}{r[3]}")

    total = len(cases)
    print(f"\nAccuracy: {correct}/{total} ({100*correct/total:.1f}%)")
    print(f"False-acceptance rate: {false_accepts}/{total} ({100*false_accepts/total:.1f}%)  <- keep this near zero")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    main(url.rstrip("/"))
