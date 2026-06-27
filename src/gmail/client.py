"""Gmail read access + label name→ID cache.
"""

from __future__ import annotations

import json
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


def _cloud_token_json() -> str | None:
    """Return stored token.json contents when running headless (cloud), else None.

    The deployed Function has no browser, so the OAuth refresh token is supplied via
    Key Vault (resolved through get_settings) or a GMAIL_TOKEN_JSON env var — never
    the interactive flow. We only touch get_settings when KEY_VAULT_URI is set so
    local OAuth minting doesn't need full app settings.
    """
    if os.environ.get("GMAIL_TOKEN_JSON"):
        return os.environ["GMAIL_TOKEN_JSON"]
    if os.environ.get("KEY_VAULT_URI"):
        from src.config import get_settings

        return get_settings().gmail_token_json
    return None


def authenticate_gmail():  # -> Resource
    """Return an authorized Gmail service.

    Cloud (headless): build credentials from the stored token (Key Vault / env) and
    refresh — no browser. Local: cache in token.json, running the interactive OAuth
    flow on first use.
    """
    token_json = _cloud_token_json()
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), GMAIL_SCOPES)
        if not creds.valid and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)

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
        return next((h["value"] for h in headers if h["name"].lower() == target), "")

    return {
        "sender": header("From"),
        "subject": header("Subject"),
        "snippet": message.get("snippet", ""),
        "has_attachment": _has_attachment(message.get("payload", {})),
    }


def _has_attachment(part: dict) -> bool:
    """True if this MIME part (or any child) is a real attachment."""
    if part.get("filename") and part.get("body", {}).get("attachmentId"):
        return True
    return any(_has_attachment(child) for child in part.get("parts", []))


def build_label_index(service) -> dict[str, str]:
    """Return {label_name: label_id} so modify() can resolve names to ids (M3)."""
    response = service.users().labels().list(userId="me").execute()
    return {label["name"]: label["id"] for label in response.get("labels", [])}
