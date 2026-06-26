# From Prompt to Productivity

> AI-powered automation with Azure. Write one plain-English policy; a scheduled
> Azure Function triages your inbox against it — labels what matters, archives
> the noise. This repo is the live demo for the talk *and* a real fix for a real
> 5,000-unread inbox.

## The idea in one line
**The policy file is the prompt.** Edit `policy.md` in English, and the behaviour
of the whole automation changes — no code, no redeploy of logic. That live edit is
the centrepiece of the talk.

## Architecture

```
            ┌──────────────────────── Azure ────────────────────────┐
 Timer ────▶│  Azure Function (Python)                              │
 (~10 min)  │    1. Gmail API  → list new/unread (skip processed)   │
            │    2. attachment? → Blob → Document Intelligence      │
            │    3. Azure OpenAI (gpt-4o-mini, structured output)   │
            │         └─ judge vs policy.md → TriageVerdict         │
            │    4. Gmail API  → apply labels / archive (guarded)   │
            │   secrets ← Key Vault (Managed Identity)              │
            └───────────────────────────────────────────────────────┘
```

**Five Azure services:** Azure OpenAI · Functions · Document Intelligence · Blob · Key Vault.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # fill endpoints/keys
# put your Google OAuth client at credentials.json (see M0 below)
python scripts/check_setup.py         # M0 done-check: Azure + Gmail reachable
python scripts/run_local.py --samples # M1: classify the sample emails
```

## Build order (each milestone is demoable)
| | Milestone | You build | Demo |
|---|---|---|---|
| M0 | Scaffold + prerequisites | (scaffolded) + Azure/Google setup | `check_setup.py` green |
| M1 | Classifier core | `triage/models.py`, `triage/classifier.py`, `policy.md` | edit policy → verdict flips |
| M2 | Read real Gmail | `gmail/client.py` | dry-run table over real inbox |
| M3 | Act safely | `gmail/actions.py`, `store/state.py` | labels applied, idempotent |
| M4 | Attachment-aware | `docs/intelligence.py` | invoice PDF → Finance/high |
| M5 | Azure automation | `function_app.py` + Key Vault | runs on a schedule in Azure |
| M6 | Talk polish | metrics + demo mode + 3 slides | 30-min dress rehearsal |

## Safety
`TRIAGE_DRY_RUN=true` by default — nothing in Gmail is touched until you opt in,
and a never-touch allowlist (starred / VIP / your own threads) is enforced in code.

Coding standard: [HARP v1.0.1](https://github.com/knightkill/harp/blob/v1.0.1/HARP.md) (see `CLAUDE.md`).
