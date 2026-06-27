# Triage policy — the "Prompt"

This file IS the prompt. The classifier reads it verbatim and decides each email
against it. Edit this file to change behaviour — no code change needed. That live
edit is the centrepiece of the talk: one English file sorts thousands of emails.

## Who I am
Hardip Patel — work at Atyantik; run anormaly labs for building personal products; work across client and personal projects.
My time is the scarce resource. Primary should only contain mail that needs *me*.

## KEEP IN PRIMARY (keep_in_primary = true)
- A real human writing to me personally (not a bulk/marketing send).
- Anything about money, invoices, payments, taxes, contracts, or legal.
- Anything about my companies or clients (e.g. Atyantik, anormaly).
- A direct reply to a thread I participated in, or where I'm the only/primary recipient.
- Security or account alerts that need action (login attempts, expiring credentials).
- Time-sensitive logistics I personally must handle (travel, interviews, deadlines).

## LABEL + ARCHIVE OUT OF PRIMARY (keep_in_primary = false)
- Newsletters, digests, blogs, "product updates"            → label: News
- Marketing, sales, promotions, discounts                    → label: Promotions
- Receipts, order confirmations, statements (no action)      → label: Finance/Receipts
- Automated app notifications (CI, social, calendar invites
  I'm only cc'd on, "someone commented")                     → label: Notifications
- Recruiter spam / cold outreach                             → label: Cold-Outreach

## IMPORTANCE (0–100)
- 80–100: needs my reply or action today (money/legal/clients/security).
- 50–79:  worth my eyes soon but not urgent.
- 0–49:   reference or noise; safe to archive.

## NEVER-TOUCH (the agent must skip these even if the policy says archive)
- Starred / important-flagged messages.
- Threads I have personally sent a reply in.
- Senders on my VIP allowlist (configured in code, M3).

## Output contract
For every email return: category, importance (0–100), labels[], keep_in_primary (bool),
and a one-line reason citing the rule above.
