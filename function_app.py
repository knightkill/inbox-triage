"""Azure Functions v2 entrypoints — the "automation" layer.

Two triggers over the SAME triage pipeline:
  - a Timer trigger (cron) so triage runs unattended every ~10 min — this is what
    makes it an *automation*, not a script.
  - an HTTP trigger for on-demand / demo runs.

The triggers stay thin; the real work lives in src/ and is testable without
Functions (HARP-3.1, HARP-4.1). Safety: dry_run comes from settings and defaults
to True, so a fresh deploy won't touch the inbox until TRIAGE_DRY_RUN=false.
"""

from __future__ import annotations

import json
import logging

import azure.functions as func

from src.config import get_settings
from src.gmail.actions import apply_verdict
from src.gmail.client import (
    authenticate_gmail,
    build_label_index,
    extract_fields,
    fetch_message,
    list_message_ids,
)
from src.store.state import append_audit, load_processed_ids, mark_processed
from src.triage.classifier import classify_email, load_policy

app = func.FunctionApp()

DEFAULT_QUERY = "in:inbox is:unread"


def run_triage(query: str = DEFAULT_QUERY, limit: int = 25) -> dict:
    """List new mail → classify against policy → apply verdicts → return counts.

    Idempotent (skips already-processed ids) and audited. Honours settings.dry_run.
    """
    settings = get_settings()
    policy = load_policy()
    service = authenticate_gmail()
    label_index = build_label_index(service)
    seen = load_processed_ids()

    counts = {"processed": 0, "kept": 0, "archived": 0, "skipped": 0, "dry_run": settings.dry_run}
    for message_id in list_message_ids(service, query, max_results=limit):
        if message_id in seen:
            continue
        message = fetch_message(service, message_id)
        fields = extract_fields(message)
        verdict = classify_email(fields["subject"], fields["sender"], fields["snippet"], policy)
        record = apply_verdict(service, message, fields, verdict, label_index, dry_run=settings.dry_run)

        counts["processed"] += 1
        if record["action"] == "skipped":
            counts["skipped"] += 1
        elif verdict.keep_in_primary:
            counts["kept"] += 1
        elif record.get("archive"):
            counts["archived"] += 1

        append_audit({
            "id": message_id, "sender": fields["sender"], "subject": fields["subject"],
            **record,
        })
        if not settings.dry_run:
            mark_processed(message_id)
    return counts


@app.timer_trigger(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
def handle_scheduled_triage(timer: func.TimerRequest) -> None:
    """Run the triage pipeline on a schedule (every 10 minutes)."""
    summary = run_triage()
    logging.info("scheduled triage complete: %s", summary)


@app.route(route="triage", auth_level=func.AuthLevel.FUNCTION)
def handle_manual_triage(req: func.HttpRequest) -> func.HttpResponse:
    """Manual / demo run. Optional ?limit=N. Returns a small JSON summary."""
    try:
        limit = int(req.params.get("limit", "25"))
    except ValueError:
        limit = 25
    summary = run_triage(limit=limit)
    return func.HttpResponse(json.dumps(summary), mimetype="application/json")
