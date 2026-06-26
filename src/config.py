"""Central settings + secret resolution.

Locally, secrets come from environment variables (loaded from .env by scripts).
In Azure, they come from Key Vault via Managed Identity (wired in M5). This module
hides that difference so the rest of the code just asks for a setting.

HARP-5.3: explicit > magic — every required secret is fetched by name and fails
loudly if missing, rather than silently defaulting.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _require(name: str) -> str:
    """Return env var `name` or raise — never silently default a secret (HARP-2.2)."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required setting {name!r}. Set it in .env (local) or Key Vault (Azure)."
        )
    return value


def _optional(name: str, default: str) -> str:
    return os.environ.get(name) or default


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of everything the app needs to run."""

    # Azure OpenAI (classifier)
    openai_endpoint: str
    openai_key: str
    openai_deployment: str
    openai_api_version: str

    # Document Intelligence (M4)
    docintel_endpoint: str | None
    docintel_key: str | None

    # Storage (M3/M4)
    storage_connection_string: str | None
    state_container: str

    # Behaviour / safety
    gmail_account: str
    dry_run: bool
    daily_limit: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build Settings once.

    TODO(M5): when KEY_VAULT_URI is set, resolve openai_key / docintel_key /
    storage_connection_string from Key Vault using DefaultAzureCredential instead
    of reading them from the environment. Keep the env path for local dev.
    """
    return Settings(
        openai_endpoint=_require("AZURE_OPENAI_ENDPOINT"),
        openai_key=_require("AZURE_OPENAI_KEY"),
        openai_deployment=_optional("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
        openai_api_version=_optional("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        docintel_endpoint=os.environ.get("AZURE_DOCINTEL_ENDPOINT"),
        docintel_key=os.environ.get("AZURE_DOCINTEL_KEY"),
        storage_connection_string=os.environ.get("AZURE_STORAGE_CONNECTION_STRING"),
        state_container=_optional("TRIAGE_STATE_CONTAINER", "triage-state"),
        gmail_account=_optional("GMAIL_ACCOUNT", "me"),
        dry_run=_optional("TRIAGE_DRY_RUN", "true").lower() != "false",
        daily_limit=int(_optional("TRIAGE_DAILY_LIMIT", "500")),
    )
