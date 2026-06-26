"""Processed-message state + an audit log of every decision.

M3 (local file) → M5 (Azure Blob). Two jobs:
  1. Idempotency: remember which message ids we've already triaged so re-runs and
     the scheduled timer don't reprocess the same mail.
  2. Audit: append one JSON line per decision (message id, verdict, action) so you
     can prove on stage exactly what the agent did — and undo if needed.

Start with local files (state/processed.json + state/decisions.audit.jsonl).
In M5 swap the storage backend for azure-storage-blob using the same interface,
so nothing upstream changes (HARP-3.1: one reason to change).
"""

from __future__ import annotations

# import json, os
# from azure.storage.blob import BlobServiceClient   # M5


def load_processed_ids() -> set[str]:
    """Return the set of message ids already triaged (empty on first run)."""
    raise NotImplementedError("TODO(M3): read processed ids from local state file")


def mark_processed(message_id: str) -> None:
    """Record that message_id has been triaged."""
    raise NotImplementedError("TODO(M3): persist message_id")


def append_audit(record: dict) -> None:
    """Append one decision record as a JSON line to the audit log."""
    raise NotImplementedError("TODO(M3): append record to decisions.audit.jsonl")
