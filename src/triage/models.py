"""The structured verdict the classifier must return for every email.

M1: you define this. Using a pydantic model (not a free-form dict) is what lets us
force Azure OpenAI into structured output — the model can't ramble, it must fill
these fields, and invalid responses are rejected before they reach Gmail.
"""

from __future__ import annotations

# from enum import Enum
# from pydantic import BaseModel, Field


# TODO(M1): define TriageVerdict.
# Fields to capture (see policy.md "Output contract"):
#   - category: str        (e.g. "Newsletter", "Client", "Receipt", "Personal")
#   - importance: int      (0-100; constrain with Field(ge=0, le=100))
#   - labels: list[str]    (Gmail label names to apply, e.g. ["News"])
#   - keep_in_primary: bool
#   - reason: str          (one line citing the policy rule)
#
# Consider an Enum for category so the model can only pick from a fixed set —
# that makes downstream label mapping deterministic (HARP-5.3: explicit > magic).
