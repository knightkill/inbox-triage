"""Processed-message state + an audit log of every decision.

M3 backs these with local files; M5 swaps the same interface to Azure Blob.
  1. Idempotency: remember which message ids we've already triaged so re-runs and
     the scheduled timer don't reprocess the same mail.
  2. Audit: append one JSON line per decision so you can prove exactly what the
     agent did — and undo if needed.
"""

from __future__ import annotations

import json
import os

STATE_DIR = "state"
PROCESSED_FILE = os.path.join(STATE_DIR, "processed.json")
AUDIT_FILE = os.path.join(STATE_DIR, "decisions.audit.jsonl")


def _ensure_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def load_processed_ids() -> set[str]:
    """Return the set of message ids already triaged (empty on first run)."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, encoding="utf-8") as handle:
        return set(json.load(handle))


def mark_processed(message_id: str) -> None:
    """Record that message_id has been triaged (idempotent)."""
    _ensure_dir()
    ids = load_processed_ids()
    ids.add(message_id)
    with open(PROCESSED_FILE, "w", encoding="utf-8") as handle:
        json.dump(sorted(ids), handle)


def append_audit(record: dict) -> None:
    """Append one decision record as a JSON line to the audit log."""
    _ensure_dir()
    with open(AUDIT_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
