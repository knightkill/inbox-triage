# Talk runsheet — From Prompt to Productivity

Deck: https://present.hardippatel.com/prompt-to-productivity.html
Setup guide (for the audience): [SETUP.md](./SETUP.md)

## Pre-flight (before you walk up)
- Terminal in `~/Code/personal-prompt-to-productivity`, venv active; deck open in another window.
- Gmail open to the messy inbox (the "before").
- Local demos are dry-run unless `--live` — decide which senders/emails are OK on the projector.
- Backup video of the full flow ready (network / cold-start insurance).
- Pre-grab the function key for the live cloud call:
  ```bash
  KEY=$(az functionapp keys list -g rg-prompt2productivity -n p2p-triage-4189 --query functionKeys.default -o tsv)
  ```
- Optional: refresh the "before" inbox count for the opening.

## Flow (≈30 min)

| Slide | Say (brief) | Show / RUN | Expect |
|---|---|---|---|
| 1 Title | "We'll take how you sort mail by hand and make Azure do it." | — | — |
| 2 Who I am | 20-sec intro | — | — |
| 3 Manual loop | "This is what we all do by hand." | switch to Gmail, scroll the 5,000-unread inbox | the pain, live |
| 4 Same loop, automated | "Same four steps — different worker." | compare slide | — |
| 5 How it decides | "The policy is the only config." | `cat policy.md` → `python scripts/run_local.py --samples` | typed verdicts |
| 5 (the moment) | "I change the *rules*, not the code." | edit one line in `policy.md` (e.g. recruiter→KEEP) → re-run `--samples` | a verdict flips |
| 6 Acts safely | "Acting on real mail is the scary part." | `python scripts/run_local.py --query "in:inbox is:unread" --limit 5` (dry-run) | decision table, nothing mutated |
| 6 | "Every decision is logged + undoable." | `tail state/decisions.audit.jsonl` | audit lines |
| 7 Setup (DIY) | "You can do all of this — one guide." | open `SETUP.md`; prove it's real: `az resource list -g rg-prompt2productivity -o table` | the deployed resources |
| 8 Azure pieces | "And it runs unattended." | `curl "https://p2p-triage-4189.azurewebsites.net/api/triage?limit=5&code=$KEY"` | live `{"processed":…,"archived":…}` |
| 9 Achieved | before→after; "$0, every 10 min" | — | — |
| 10 Reproduce it | "Clone it, point it at your inbox." | repo URL + QR on screen | — |

## The "audience can do it themselves" moment (slides 7 → 10)
Don't provision live (too slow). Instead:
1. Open `SETUP.md` — "30 minutes, every command is here."
2. `az resource list -g rg-prompt2productivity -o table` — they see the real RG (Function, Key Vault, Storage).
3. Call out the two non-obvious bits the guide solves: **Gmail OAuth → refresh token → Key Vault** (headless, no browser in cloud) and **`func publish`, not zip** (Linux Consumption won't remote-build a zip).
4. Land on slide 10: scan the QR → `git clone` → `.env` → `SETUP.md`.

## Demo safety
- Slides 5–6 are dry-run (no projector mishaps).
- Slide 8's `curl` is real but tiny.
- The scheduled timer is currently throttled (2/tick) — pause anytime:
  `az functionapp config appsettings set -n p2p-triage-4189 -g rg-prompt2productivity --settings TRIAGE_DRY_RUN=true`

## Dress-rehearsal checklist
- [ ] Make the repo public: `gh repo edit knightkill/inbox-triage --visibility public --accept-visibility-change-consequences`
- [ ] Verify the QR resolves to the public repo (scan it).
- [ ] Run slides 5, 6, 8 end-to-end once on the actual demo machine/network.
- [ ] Confirm `policy.md` edit → verdict flip works live.
- [ ] Record the backup video.
- [ ] Refresh slide-9 framing / any numbers you mention from the audit log.
- [ ] Decide the demo Gmail account; mask anything private.
- [ ] Time it — target 25 min content + 5 min Q&A.

## Code tour (live walkthrough, ~4–5 min)
Follow **one email's journey**. Deep-dive the 3 starred files; just mention the rest.
Anchor on the slide snippet first, then open the real file ("here it is for real").

1. **`policy.md`** — *the input.* "Plain English; everything else just applies this." (show KEEP / ARCHIVE)
2. **`src/triage/models.py`** → `class TriageVerdict` — *the shape of an answer.* reason first · `category: Category` (closed enum, not str) · `labels: list[Label]` · `Field(ge=0, le=100)`.
3. ⭐ **`src/triage/classifier.py`** → `classify_email` — *the decision.* highlight the one line `response_format=TriageVerdict` → "this is what makes hallucination impossible."
4. ⭐ **`src/gmail/actions.py`** → `apply_verdict` — *the action, safely.* point in order: `if is_protected(msg): return skipped` → `remove = [] if keep_in_primary else ["INBOX"]` ("archive = remove one label") → `if dry_run:` → `.modify(...)`.
5. ⭐ **`function_app.py`** → `@app.timer_trigger(...)` + `run_triage` — *the automation.* the cron schedule + `if message_id in seen: continue` ("idempotent").
6. **Mention, don't open:** `config.py` (`DefaultAzureCredential` → Key Vault, "no keys in code") · `gmail/client.py` (`_cloud_token_json`, "headless, no browser") · `store/state.py` ("Blob memory").

**Tips:** bump editor font to 18–20pt; fuzzy-open (`Cmd-P`) to jump to a function, don't scroll; use **go-to-definition** to travel `run_triage` → `classify_email` → `apply_verdict` (literally the email's path); pre-open the files as tabs in this order.
