"""Local dry-run driver — the thing you run between milestones to see triage working.

  python scripts/run_local.py --samples         # M1: classify sample_emails/*.json
  python scripts/run_local.py --query "in:inbox is:unread" --limit 20   # M2+: real Gmail, dry-run

It prints a decision table and NEVER mutates Gmail (action is left to the Function /
M3 with dry_run off). This file grows with each milestone; it imports the modules
you write, so it will raise the relevant TODO until that milestone is done.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def _print_row(sender: str, subject: str, verdict) -> None:
    keep = "KEEP " if getattr(verdict, "keep_in_primary", False) else "arch."
    labels = ",".join(getattr(verdict, "labels", []) or [])
    print(f"  [{keep}] {getattr(verdict, 'importance', '?'):>3}  {labels:<18} {sender[:28]:<28} {subject[:46]}")


def run_samples() -> None:
    """M1 path: classify the JSON fixtures in sample_emails/ against policy.md."""
    from src.triage.classifier import classify_email, load_policy

    policy = load_policy()
    files = sorted(glob.glob("sample_emails/*.json"))
    if not files:
        print("No sample_emails/*.json found.")
        return
    print(f"Classifying {len(files)} sample emails against policy.md:\n")
    for path in files:
        with open(path, encoding="utf-8") as sample_file:
            email = json.load(sample_file)
        verdict = classify_email(email["subject"], email["sender"], email["body"], policy)
        _print_row(email["sender"], email["subject"], verdict)
        print(f"        reason: {getattr(verdict, 'reason', '')}")


def run_gmail(query: str, limit: int) -> None:
    """M2+ path: pull real Gmail, classify, print a dry-run table (no mutations)."""
    from src.gmail.client import (
        authenticate_gmail,
        extract_fields,
        fetch_message,
        list_message_ids,
    )
    from src.triage.classifier import classify_email, load_policy

    policy = load_policy()
    service = authenticate_gmail()
    ids = list_message_ids(service, query, max_results=limit)
    print(f"Triaging {len(ids)} messages matching {query!r} (DRY RUN):\n")
    for message_id in ids:
        fields = extract_fields(fetch_message(service, message_id))
        verdict = classify_email(fields["subject"], fields["sender"], fields["snippet"], policy)
        _print_row(fields["sender"], fields["subject"], verdict)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local dry-run triage driver")
    parser.add_argument("--samples", action="store_true", help="classify sample_emails/*.json (M1)")
    parser.add_argument("--query", default="in:inbox is:unread", help="Gmail search query (M2+)")
    parser.add_argument("--limit", type=int, default=20, help="max messages (M2+)")
    args = parser.parse_args()

    if args.samples:
        run_samples()
    else:
        run_gmail(args.query, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
