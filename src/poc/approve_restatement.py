"""Simulate Finance's restatement approval workflow by appending approval rows to the approvals feed.

In production this feed comes from the approval tool Finance uses (with who approved and when); the
pipeline only reads it. A line held as LATE_BEYOND_WINDOW is released when an approval matches its
sale month and source system and the line arrived before the approval time (ADR-004).

    python src/poc/approve_restatement.py --id RST-001 --period 2026-06 --source POS --decision RESTATE
    python src/poc/approve_restatement.py --id RST-002 --period 2026-08 --source ECOM \\
        --decision BOOK_IN_CURRENT --booking-month 2026-10
    python src/poc/approve_restatement.py --demo     # the two approvals above
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

FEED = Path("data/raw/landing/restatements/approvals/approvals.csv")
COLS = ["restatement_id", "period", "source_system", "decision", "booking_month", "approved_by", "approved_at", "note"]
DEMO = [
    dict(restatement_id="RST-001", period="2026-06", source_system="POS", decision="RESTATE", booking_month="",
         note="S012 POS terminal offline 10-11 Jun; lines above materiality - restate June"),
    dict(restatement_id="RST-002", period="2026-08", source_system="ECOM", decision="BOOK_IN_CURRENT",
         booking_month="2026-10", note="E-commerce quantity corrections below materiality - book in October"),
]


def append(rows: list[dict]) -> None:
    if not FEED.exists():
        sys.exit(f"{FEED} not found - run `make data` first.")
    existing = {r["restatement_id"] for r in csv.DictReader(FEED.open())}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with FEED.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        for r in rows:
            if r["restatement_id"] in existing:
                print(f"{r['restatement_id']} already approved - skipped")
                continue
            if r["decision"] not in ("RESTATE", "BOOK_IN_CURRENT"):
                sys.exit("decision must be RESTATE or BOOK_IN_CURRENT")
            for k in ("period", "booking_month"):
                if r.get(k) and not re.fullmatch(r"\d{4}-\d{2}", r[k]):
                    sys.exit(f"{k} must be YYYY-MM")
            if r["decision"] == "BOOK_IN_CURRENT" and not r.get("booking_month"):
                sys.exit("BOOK_IN_CURRENT needs --booking-month")
            w.writerow({**r, "approved_by": r.get("approved_by") or "finance.controller", "approved_at": now})
            print(f"Approved {r['restatement_id']}: {r['period']} {r['source_system']} {r['decision']}"
                  + (f" -> booked in {r['booking_month']}" if r.get("booking_month") else ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--id"); ap.add_argument("--period"); ap.add_argument("--source", default="ALL")
    ap.add_argument("--decision"); ap.add_argument("--booking-month", default=""); ap.add_argument("--note", default="")
    a = ap.parse_args()
    if a.demo:
        append(DEMO)
    else:
        if not (a.id and a.period and a.decision):
            ap.error("--id, --period and --decision are required (or --demo)")
        append([dict(restatement_id=a.id, period=a.period, source_system=a.source.upper(), decision=a.decision.upper(),
                     booking_month=a.booking_month, note=a.note)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
