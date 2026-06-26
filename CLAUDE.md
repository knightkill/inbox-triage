# personal-prompt-to-productivity

Demo project for the Azure-meetup talk **"AI-powered automation with Azure: From
Prompt to Productivity."** An inbox-triage automation: you write a triage policy
once in plain English (`policy.md` — the *Prompt*), and a scheduled Azure Function
reads inbound Gmail, classifies each message against the policy with Azure OpenAI,
labels it, and keeps only what matters in Primary (the *Productivity*).

It also solves a real problem — Hardip's huge Gmail unread backlog — so the live
before/after on a real inbox *is* the talk.

## Architecture (5 Azure services — honestly "Azure-native")

```
Timer trigger (~10 min) on Azure Functions          ← "automation"
  ├─ Gmail API: list new/unread; skip already-processed (state in Blob)
  ├─ per message:
  │    ├─ headers + body/snippet
  │    ├─ if PDF/image attachment → Blob → Document Intelligence → text/fields
  │    └─ Azure OpenAI (gpt-4o-mini, pydantic structured output):
  │         { category, importance, labels[], keep_in_primary, reason }
  └─ Gmail API: ensure+apply labels; if not keep_in_primary → remove INBOX (archive)
       guarded by dry_run + never-touch allowlist + idempotency
Secrets → Key Vault via Managed Identity
```

Azure OpenAI · Azure Functions · Document Intelligence · Blob Storage · Key Vault (+ Managed Identity).

## Coding standard

WHEN writing or reviewing code → ALWAYS adhere to HARP v1.0.1 at
https://github.com/knightkill/harp/blob/v1.0.1/HARP.md. Cite rule IDs in PR
review (e.g. "fails HARP-1.1").

**Python adaptation:** HARP is TS-first. Its file-naming rule (HARP-1.10, kebab-case)
and function-casing rule (HARP-1.3, camelCase) conflict with Python imports/PEP 8, so
here we adopt the *spirit*, not the letter: `snake_case` modules and functions, but
functions are still named as **verbs** (`classify_email`, `apply_labels`, not
`email_classifier`). Everything else (HARP-1.7 banned generic names, HARP-2.2 WHY-comments
on secrets, HARP-3.1 one-reason-to-change, HARP-5.x imports) applies verbatim.

## Secrets (HARP-2.2)

Never commit `token.json`, `credentials.json`, `.env`, or `local.settings.json`
(all in `.gitignore`). Locally, secrets come from `.env` / `local.settings.json`.
In Azure, they come from **Key Vault via Managed Identity** — no fallback to env
in the deployed function. Comment every secret read with the WHY.

## Layout

| Path | Role | Built in |
|---|---|---|
| `policy.md` | the natural-language triage policy (THE "prompt") | M1 |
| `src/config.py` | settings + secret resolution (env locally / Key Vault in cloud) | M0/M5 |
| `src/triage/models.py` | `TriageVerdict` pydantic model | M1 |
| `src/triage/classifier.py` | Azure OpenAI structured classifier | M1 |
| `src/gmail/client.py` | auth + read + label name→ID cache | M2 |
| `src/gmail/actions.py` | label/archive with dry_run + guards + idempotency | M3 |
| `src/docs/intelligence.py` | Document Intelligence on attachments | M4 |
| `src/store/state.py` | Blob-backed processed-state + audit log | M3/M5 |
| `function_app.py` | Azure Functions v2 entrypoints (timer + http) | M5 |
| `scripts/check_setup.py` | M0 done-check (Azure + Gmail reachable) | M0 |
| `scripts/run_local.py` | local dry-run driver | M2+ |

## Patterns reused from Hardip's own repos (don't reinvent)

- **Azure OpenAI client** → `~/Code/trainGemma` (`AzureOpenAI`, env `AZURE_OPENAI_*`, `gpt-4o-mini`).
- **Gmail auth/read** → `~/Code/personal-invoice-fetcher/src/gmail_api.py`
  (`gmail_authenticate()`, `search_messages()`, `get_message()`, base64url decode).
- **Document Intelligence** → `~/Code/personal-test-ms-doc-int/app.py`
  (`azure-ai-formrecognizer` `DocumentAnalysisClient`, `prebuilt-document`, bytes input).

## Run (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in your endpoints/keys
python scripts/check_setup.py   # M0 done-check
```
