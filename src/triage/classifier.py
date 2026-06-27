"""Classify one email against the natural-language policy using Azure OpenAI.
"""

from __future__ import annotations

from functools import lru_cache
from openai import AzureOpenAI
from src.config import get_settings
from src.triage.models import TriageVerdict

MAX_BODY_CHARS = 2000

@lru_cache(maxsize=1)
def _client() -> AzureOpenAI:
    """Build an AzureOpenAI client from get_settings()."""
    settings = get_settings()
    return AzureOpenAI(
        azure_endpoint=settings.openai_endpoint,
        api_key=settings.openai_key,
        api_version=settings.openai_api_version,
    )

def load_policy(path: str = "policy.md") -> str:
    """Read the triage policy that will be injected as the system prompt."""
    with open(path, encoding="utf-8") as policy_file:
        return policy_file.read()


def classify_email(subject: str, sender: str, body: str, policy: str):  # -> TriageVerdict
    """Return a TriageVerdict for one email, judged against `policy`.
    """
    settings = get_settings()
    email = f"From: {sender}\nSubject: {subject}\n\n{body[:MAX_BODY_CHARS]}"

    completion = _client().beta.chat.completions.parse(
        model=settings.openai_deployment,
        messages=[
            {"role": "system", "content": policy},
            {"role": "user", "content": email},
        ],
        response_format=TriageVerdict,
        max_completion_tokens=2000,
    )
    verdict = completion.choices[0].message.parsed
    if verdict is None:
        raise RuntimeError(f"Classifier returned no structured verdict for {subject!r}")
    return verdict
