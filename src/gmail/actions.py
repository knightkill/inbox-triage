"""Safe Gmail mutations: create labels, apply them, archive out of Primary.

Mutating a real inbox is the scary part, so safety is the feature here, not an
afterthought:
  - dry_run (default True): log what WOULD happen, change nothing.
  - never-touch allowlist: starred / important / VIP senders / threads I sent in.
  - idempotent: a label already present (or already archived) is a no-op.

Archive = remove the 'INBOX' label via messages.modify(removeLabelIds=['INBOX']).
Apply label = add the label id (create it first if missing).
"""

from __future__ import annotations

# Senders we will never archive, regardless of the verdict (bare emails, lowercase).
VIP_SENDERS: set[str] = set()

# System labels whose presence means "leave this message alone".
PROTECTED_LABELS = frozenset({"STARRED", "IMPORTANT", "SENT"})


def sender_email(sender: str) -> str:
    """Extract the bare lowercase email from a 'Name <email>' From header."""
    if "<" in sender and ">" in sender:
        sender = sender.split("<", 1)[1].split(">", 1)[0]
    return sender.strip().lower()


def ensure_label(service, label_name: str, label_index: dict[str, str]) -> str:
    """Return the id of label_name, creating it via labels().create() if absent.

    Updates label_index in place so repeated calls in one run stay cheap.
    """
    if label_name in label_index:
        return label_index[label_name]
    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    label_index[label_name] = created["id"]
    return created["id"]


def is_protected(message: dict, fields: dict) -> bool:
    """True if this message must never be touched (HARP-2.2: WHY = don't nuke real mail).

    Protected when a STARRED/IMPORTANT/SENT label is present, or the sender is on
    the VIP allowlist. These override the verdict — safety beats the model.
    """
    if PROTECTED_LABELS & set(message.get("labelIds", [])):
        return True
    return sender_email(fields.get("sender", "")) in VIP_SENDERS


def apply_verdict(service, message, fields, verdict, label_index, *, dry_run=True):
    """Apply a TriageVerdict to one message; return a record of what was done.

    `message` is the full Gmail message (needs labelIds); `fields` is extract_fields
    output (for sender). Idempotent: only adds labels not already present, only
    archives if still in INBOX.
    """
    if is_protected(message, fields):
        return {"action": "skipped", "reason": "protected", "id": message.get("id")}

    current = set(message.get("labelIds", []))

    # Resolve target labels to ids. In dry-run we never create labels.
    target_names = [label.value for label in verdict.labels]
    add_ids = []
    for name in target_names:
        if dry_run:
            lid = label_index.get(name)  # may be None for a not-yet-created label
        else:
            lid = ensure_label(service, name, label_index)
        if lid and lid not in current:
            add_ids.append(lid)

    remove_ids = ["INBOX"] if (not verdict.keep_in_primary and "INBOX" in current) else []

    record = {
        "id": message.get("id"),
        "labels": target_names,
        "archive": bool(remove_ids),
        "add_ids": add_ids,
        "remove_ids": remove_ids,
    }

    if not add_ids and not remove_ids and not (dry_run and target_names):
        record["action"] = "noop"
        return record

    if dry_run:
        record["action"] = "dry-run"
        return record

    service.users().messages().modify(
        userId="me",
        id=message["id"],
        body={"addLabelIds": add_ids, "removeLabelIds": remove_ids},
    ).execute()
    record["action"] = "applied"
    return record
