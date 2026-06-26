"""Gmail read access + label name→ID cache.

M2: you write this, adapting ~/Code/personal-invoice-fetcher/src/gmail_api.py:
  - gmail_authenticate()  (lines 26-42): installed-app OAuth + token.json refresh.
    CHANGE the scopes to include gmail.modify (we'll mutate labels in M3).
  - search_messages()     (lines 45-61): list message ids with pagination.
  - get_message()         (lines 83-85): fetch a full message.

New here (not in invoice-fetcher): a label name→ID cache. Gmail's modify API needs
label IDs (e.g. "Label_12"), not display names, so we list labels once and map.
"""

from __future__ import annotations

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # needed for label/archive (M3)
]


def authenticate_gmail():  # -> Resource
    """Return an authorized Gmail service (adapt invoice-fetcher gmail_authenticate)."""
    raise NotImplementedError("TODO(M2): adapt gmail_authenticate() with gmail.modify scope")


def list_message_ids(service, query: str, max_results: int = 50) -> list[str]:
    """Return up to max_results message ids matching a Gmail search query.

    Example query for the demo: 'in:inbox is:unread' or 'newer_than:7d in:inbox'.
    """
    raise NotImplementedError("TODO(M2): adapt search_messages() (drop the date args)")


def fetch_message(service, message_id: str) -> dict:
    """Return the full message dict (format='full')."""
    raise NotImplementedError("TODO(M2): adapt get_message()")


def extract_fields(message: dict) -> dict:
    """Pull {sender, subject, snippet, has_attachment} from a full message.

    Headers live in message['payload']['headers'] (case-insensitive lookup of
    'From' / 'Subject'). 'snippet' is on the message. Attachments => walk
    payload['parts'] for a part with a filename + body.attachmentId.
    """
    raise NotImplementedError("TODO(M2): parse headers/snippet/attachment flag")


def build_label_index(service) -> dict[str, str]:
    """Return {label_name: label_id} from users().labels().list().

    Cache this once per run — modify() needs IDs, not names (HARP-5.3: explicit).
    """
    raise NotImplementedError("TODO(M2): list labels and map name->id")
