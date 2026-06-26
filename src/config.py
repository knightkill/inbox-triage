"""Central settings + secret resolution.

Locally, secrets come from environment variables (loaded from .env by scripts).
In Azure, they come from Key Vault via the Function's managed identity (M5). This
module hides that difference so the rest of the code just asks for a setting.

HARP-5.3: explicit > magic — every required secret is fetched by name and fails
loudly if missing, rather than silently defaulting.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

# Key Vault secret names (alphanumeric + dashes) for the cloud path.
_KV_SECRETS = {
    "openai_key": "azure-openai-key",
    "docintel_key": "docintel-key",
    "storage_connection_string": "storage-connection-string",
    "gmail_token_json": "gmail-token-json",
}


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


@lru_cache(maxsize=1)
def _kv_client():
    """Return a Key Vault SecretClient when KEY_VAULT_URI is set, else None.

    Uses DefaultAzureCredential so the deployed Function authenticates with its
    managed identity and local dev can use az-cli / env credentials.
    """
    uri = os.environ.get("KEY_VAULT_URI")
    if not uri:
        return None
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    return SecretClient(vault_url=uri, credential=DefaultAzureCredential())


def _secret(field: str, env_name: str, *, required: bool) -> str | None:
    """Resolve a secret: Key Vault first (cloud), then env (local)."""
    client = _kv_client()
    if client is not None:
        value = client.get_secret(_KV_SECRETS[field]).value
        if value:
            return value
    return _require(env_name) if required else os.environ.get(env_name)


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

    # Storage (state + attachment staging)
    storage_connection_string: str | None
    state_container: str

    # Gmail headless auth (M5): the token.json contents (refresh token) as a string.
    gmail_token_json: str | None

    # Behaviour / safety
    gmail_account: str
    dry_run: bool
    daily_limit: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build Settings once, resolving secrets from Key Vault (cloud) or env (local)."""
    return Settings(
        openai_endpoint=_require("AZURE_OPENAI_ENDPOINT"),
        openai_key=_secret("openai_key", "AZURE_OPENAI_KEY", required=True),
        openai_deployment=_optional("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
        openai_api_version=_optional("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        docintel_endpoint=os.environ.get("AZURE_DOCINTEL_ENDPOINT"),
        docintel_key=_secret("docintel_key", "AZURE_DOCINTEL_KEY", required=False),
        storage_connection_string=_secret(
            "storage_connection_string", "AZURE_STORAGE_CONNECTION_STRING", required=False
        ),
        state_container=_optional("TRIAGE_STATE_CONTAINER", "triage-state"),
        gmail_token_json=_secret("gmail_token_json", "GMAIL_TOKEN_JSON", required=False),
        gmail_account=_optional("GMAIL_ACCOUNT", "me"),
        dry_run=_optional("TRIAGE_DRY_RUN", "true").lower() != "false",
        daily_limit=int(_optional("TRIAGE_DAILY_LIMIT", "500")),
    )
