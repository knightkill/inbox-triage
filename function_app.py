"""Azure Functions v2 entrypoints — the "automation" layer.

M5: you write this. Two triggers over the SAME triage pipeline:
  - a Timer trigger (cron) so triage runs unattended every ~10 min — this is what
    makes it an *automation*, not a script.
  - an HTTP trigger for on-demand/demo runs (so you can fire it live on stage).

Keep these thin: parse the trigger, then call one run_triage() function that does
the real work (list → classify → act). The pipeline itself lives in src/ and stays
testable without Functions (HARP-3.1, HARP-4.1).
"""

from __future__ import annotations

# import azure.functions as func

# app = func.FunctionApp()


# TODO(M5): Timer trigger — runs the triage pipeline on a schedule.
# @app.timer_trigger(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
# def handle_scheduled_triage(timer) -> None:
#     run_triage()


# TODO(M5): HTTP trigger — manual/demo run, returns a small JSON summary.
# @app.route(route="triage", auth_level=func.AuthLevel.FUNCTION)
# def handle_manual_triage(req) -> func.HttpResponse:
#     summary = run_triage()
#     return func.HttpResponse(body=..., mimetype="application/json")


# TODO(M5): the shared pipeline. Reuse src/gmail, src/triage, src/docs, src/store.
# def run_triage() -> dict:
#     """List new mail → classify against policy → apply verdicts → return counts."""
#     ...
