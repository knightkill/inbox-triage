"""Safe Gmail mutations: create labels, apply them, archive out of Primary.

M3: you write this. Mutating a real inbox is the scary part, so safety is the
feature here, not an afterthought:
  - dry_run (default True): log what WOULD happen, change nothing.
  - never-touch allowlist: starred / important / VIP senders / threads I replied to.
  - idempotent: applying a label that's already there is a no-op; check first.

Archive = remove the 'INBOX' label via messages.modify(removeLabelIds=['INBOX']).
Apply label = add the label id (create it first if missing).
"""

from __future__ import annotations

# Senders we will never archive, regardless of the verdict (extend freely).
VIP_SENDERS: set[str] = set()


def ensure_label(service, label_name: str, label_index: dict[str, str]) -> str:
    """Return the id of label_name, creating it via labels().create() if absent.

    Update label_index in place so repeated calls in one run stay cheap.
    """
    raise NotImplementedError("TODO(M3): return existing id or create the label")


def is_protected(message_fields: dict, label_ids: list[str]) -> bool:
    """True if this message must never be touched (HARP-2.2: WHY = avoid nuking real mail).

    Protect when: STARRED/IMPORTANT in label_ids, sender in VIP_SENDERS, or the
    thread already contains a message I sent (SENT label on the thread).
    """
    raise NotImplementedError("TODO(M3): implement the never-touch guard")


def apply_verdict(service, message_id: str, verdict, label_index, *, dry_run: bool) -> dict:
    """Apply a TriageVerdict to one message; return a record of what was done.

    Steps:
      1. If protected → return {'action': 'skipped', 'reason': 'protected'}.
      2. Resolve verdict.labels to ids (ensure_label each).
      3. addLabelIds = those ids; removeLabelIds = ['INBOX'] if not keep_in_primary.
      4. If dry_run → return the intended change WITHOUT calling modify().
      5. Else call service.users().messages().modify(...) and return the result.
    """
    raise NotImplementedError("TODO(M3): implement guarded, idempotent apply")
