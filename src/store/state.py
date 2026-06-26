"""Processed-message state + an audit log of every decision.

Local dev uses files under state/. In Azure the Function filesystem is ephemeral,
so when a storage connection is configured we persist to Blob instead (same
interface — nothing upstream changes, HARP-3.1):
  1. Idempotency: which message ids we've already triaged, so re-runs and the timer
     don't reprocess the same mail.
  2. Audit: one JSON line per decision (append blob) to prove what the agent did.
"""

from __future__ import annotations

import json
import os

STATE_DIR = "state"
PROCESSED_FILE = os.path.join(STATE_DIR, "processed.json")
AUDIT_FILE = os.path.join(STATE_DIR, "decisions.audit.jsonl")
PROCESSED_BLOB = "processed.json"
AUDIT_BLOB = "decisions.audit.jsonl"


def _blob_container():
    """Return (BlobServiceClient, container_name) when storage is configured, else (None, None)."""
    from src.config import get_settings

    settings = get_settings()
    if not settings.storage_connection_string:
        return None, None
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(settings.storage_connection_string)
    container = settings.state_container
    try:
        service.create_container(container)
    except Exception:  # noqa: BLE001 — already exists
        pass
    return service, container


def _ensure_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def load_processed_ids() -> set[str]:
    """Return the set of message ids already triaged (empty on first run)."""
    service, container = _blob_container()
    if service is not None:
        client = service.get_blob_client(container, PROCESSED_BLOB)
        try:
            return set(json.loads(client.download_blob().readall()))
        except Exception:  # noqa: BLE001 — blob not created yet
            return set()
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, encoding="utf-8") as handle:
        return set(json.load(handle))


def mark_processed(message_id: str) -> None:
    """Record that message_id has been triaged (idempotent)."""
    ids = load_processed_ids()
    ids.add(message_id)
    payload = json.dumps(sorted(ids))
    service, container = _blob_container()
    if service is not None:
        service.get_blob_client(container, PROCESSED_BLOB).upload_blob(payload, overwrite=True)
        return
    _ensure_dir()
    with open(PROCESSED_FILE, "w", encoding="utf-8") as handle:
        handle.write(payload)


def append_audit(record: dict) -> None:
    """Append one decision record as a JSON line to the audit log."""
    line = json.dumps(record) + "\n"
    service, container = _blob_container()
    if service is not None:
        client = service.get_blob_client(container, AUDIT_BLOB)
        if not client.exists():
            client.create_append_blob()
        client.append_block(line)
        return
    _ensure_dir()
    with open(AUDIT_FILE, "a", encoding="utf-8") as handle:
        handle.write(line)
