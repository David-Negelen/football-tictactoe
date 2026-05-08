#!/usr/bin/env python3
"""
Fetch real match lineups from ESPN and store them in the database.

Usage:
    python import_matches.py
    python import_matches.py --delay 0.6   # slower if hitting rate limits
    python import_matches.py --db data/other.db
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from src.match_importer import run_import

parser = argparse.ArgumentParser(description="Import match lineups from ESPN API.")
parser.add_argument("--db", default="data/tictactoe.db")
parser.add_argument("--delay", type=float, default=0.4, help="Seconds between requests.")
args = parser.parse_args()

print(f"Importing into {args.db} …\n")
n = run_import(args.db, delay=args.delay, verbose=True)
print(f"\nDone — {n} new matches added.")
