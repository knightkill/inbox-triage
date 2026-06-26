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

load_dotenv(override=True)


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


def run_gmail(query: str, limit: int, *, apply: bool = False, dry_run: bool = True) -> None:
    """M2+ path: pull real Gmail, classify, print a table.

    With apply=True it runs M3's guarded label/archive (still dry-run unless
    dry_run=False). Idempotent and audited.
    """
    from src.gmail.client import (
        authenticate_gmail,
        extract_fields,
        fetch_message,
        list_message_ids,
        build_label_index,
    )
    from src.gmail.actions import apply_verdict
    from src.store.state import append_audit, load_processed_ids, mark_processed
    from src.triage.classifier import classify_email, load_policy

    policy = load_policy()
    service = authenticate_gmail()
    label_index = build_label_index(service) if apply else {}
    ids = list_message_ids(service, query, max_results=limit)
    mode = ("APPLY (DRY-RUN)" if dry_run else "APPLY (LIVE — mutating Gmail)") if apply else "DRY RUN (read only)"
    print(f"Triaging {len(ids)} messages matching {query!r} [{mode}]:\n")

    seen = load_processed_ids() if apply else set()
    for message_id in ids:
        if message_id in seen:
            continue  # idempotent: already triaged in a previous run
        message = fetch_message(service, message_id)
        fields = extract_fields(message)
        verdict = classify_email(fields["subject"], fields["sender"], fields["snippet"], policy)
        _print_row(fields["sender"], fields["subject"], verdict)
        if apply:
            record = apply_verdict(service, message, fields, verdict, label_index, dry_run=dry_run)
            print(f"        action: {record['action']}"
                  + (f" (archive={record['archive']})" if 'archive' in record else ""))
            if not dry_run:
                append_audit({"id": message_id, "sender": fields["sender"],
                              "subject": fields["subject"], **record})
                mark_processed(message_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local triage driver (read-only, or apply with guards)")
    parser.add_argument("--samples", action="store_true", help="classify sample_emails/*.json (M1)")
    parser.add_argument("--query", default="in:inbox is:unread", help="Gmail search query (M2+)")
    parser.add_argument("--limit", type=int, default=20, help="max messages (M2+)")
    parser.add_argument("--apply", action="store_true", help="apply labels/archive (M3) instead of just printing")
    parser.add_argument("--live", action="store_true",
                        help="actually mutate Gmail (default is dry-run even with --apply)")
    args = parser.parse_args()

    if args.samples:
        run_samples()
    else:
        run_gmail(args.query, args.limit, apply=args.apply, dry_run=not args.live)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
