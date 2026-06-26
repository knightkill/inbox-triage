"""Classify one email against the natural-language policy using Azure OpenAI.

M1: you write classify_email(). This is the heart of the talk — the policy text
(policy.md) is injected as the system prompt, the email is the user message, and
Azure OpenAI returns a TriageVerdict. Changing policy.md changes behaviour with
zero code change. That is the "Prompt" in "From Prompt to Productivity".

Reuse the AzureOpenAI client idiom from ~/Code/trainGemma (env-driven endpoint/key/
deployment/api-version — already surfaced via src.config.get_settings()).

For structured output, prefer the parse helper:
    client.beta.chat.completions.parse(model=..., messages=[...], response_format=TriageVerdict)
which validates the reply against the pydantic model and hands you a typed object.
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

    M1 steps:
      1. Build an AzureOpenAI client from get_settings() (see trainGemma).
      2. system = policy ; user = the email's sender/subject/body (truncate body —
         you don't need the whole thing; HARP: keep token cost honest).
      3. Call ...parse(..., response_format=TriageVerdict). NOTE gpt-5-family rules
         (we're on gpt-5.4-nano): pass max_completion_tokens (NOT max_tokens) and do
         NOT set temperature (only the default is supported). Give it enough tokens
         (e.g. 256) so structured output isn't truncated by the reasoning pass.
      4. Return the parsed verdict. If .parse() isn't supported on nano, fall back to
         response_format={"type":"json_schema", ...} or to gpt-5-mini with more tokens.
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
