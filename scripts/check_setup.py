"""M0 done-check: prove Azure OpenAI and Gmail are reachable before we build on them.

Run after you've filled .env and minted token.json:

    python scripts/check_setup.py

It does NOT depend on the src modules you'll write later — it's deliberately
self-contained so it works the moment your credentials are in place.
"""

from __future__ import annotations

import os
import sys

# Make `src` importable when run from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

GREEN, RED, RESET = "\033[32m", "\033[31m", "\033[0m"


def _ok(msg: str) -> None:
    print(f"{GREEN}  PASS{RESET}  {msg}")


def _fail(msg: str, error: Exception) -> None:
    print(f"{RED}  FAIL{RESET}  {msg}\n        {type(error).__name__}: {error}")


def check_azure_openai() -> bool:
    """Send a one-token completion through Azure OpenAI and confirm a reply."""
    try:
        from openai import AzureOpenAI

        from src.config import get_settings

        settings = get_settings()
        client = AzureOpenAI(
            azure_endpoint=settings.openai_endpoint,
            api_key=settings.openai_key,
            api_version=settings.openai_api_version,
        )
        # gpt-5 family (incl. nano): use max_completion_tokens, and don't override
        # temperature (only the default is supported). Budget enough tokens that a
        # reasoning pass still leaves room for visible output.
        reply = client.chat.completions.create(
            model=settings.openai_deployment,
            messages=[{"role": "user", "content": "Reply with the single word: ready"}],
            max_completion_tokens=64,
        )
        text = (reply.choices[0].message.content or "").strip()
        _ok(f"Azure OpenAI '{settings.openai_deployment}' replied: {text!r}")
        return True
    except Exception as error:  # noqa: BLE001 — surface any setup failure to the user
        _fail("Azure OpenAI not reachable", error)
        return False


def check_gmail() -> bool:
    """Authenticate to Gmail and read the profile (address + message count)."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token_file:
                token_file.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        _ok(
            f"Gmail '{profile['emailAddress']}' — "
            f"{profile['messagesTotal']} messages, {profile['threadsTotal']} threads"
        )
        return True
    except Exception as error:  # noqa: BLE001
        _fail("Gmail not reachable (need credentials.json → token.json)", error)
        return False


def main() -> int:
    print("M0 setup check\n")
    results = [check_azure_openai(), check_gmail()]
    print()
    if all(results):
        print(f"{GREEN}All green — you're ready for M1.{RESET}")
        return 0
    print(f"{RED}Some checks failed — fix the above, then re-run.{RESET}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
