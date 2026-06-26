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

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # needed for label/archive (M3)
]

TOKENFILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def authenticate_gmail():  # -> Resource
    """Return an authorized Gmail service (adapt invoice-fetcher gmail_authenticate)."""
    creds = None
    if os.path.exists(TOKENFILE):
        creds = Credentials.from_authorized_user_file(TOKENFILE, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKENFILE, "w") as token_file:
            token_file.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def list_message_ids(service, query: str, max_results: int = 50) -> list[str]:
    """Return up to max_results message ids matching a Gmail search query.

    Example query for the demo: 'in:inbox is:unread' or 'newer_than:7d in:inbox'.
    """
    message_ids: list[str] = []
    page_token = None
    while len(message_ids) < max_results:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                pageToken=page_token,
                maxResults=min(100, max_results - len(message_ids)),
            )
            .execute()
        )
        message_ids.extend(message["id"] for message in response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return message_ids[:max_results]


def fetch_message(service, message_id: str) -> dict:
    """Return the full message dict (format='full')."""
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


def extract_fields(message: dict) -> dict:
    """Pull {sender, subject, snippet, has_attachment} from a full message.

    Headers live in message['payload']['headers'] (case-insensitive lookup of
    'From' / 'Subject'). 'snippet' is on the message. Attachments => walk
    payload['parts'] for a part with a filename + body.attachmentId.
    """
    headers = message.get("payload", {}).get("headers", [])

    def header(name: str) -> str:
        target = name.lower()
        return next(h["value"])


def build_label_index(service) -> dict[str, str]:
    """Return {label_name: label_id} from users().labels().list().

    Cache this once per run — modify() needs IDs, not names (HARP-5.3: explicit).
    """
    raise NotImplementedError("TODO(M2): list labels and map name->id")
