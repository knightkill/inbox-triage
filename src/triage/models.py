"""The structured verdict the classifier must return for every email.

M1: you define this. Using a pydantic model (not a free-form dict) is what lets us
force Azure OpenAI into structured output — the model can't ramble, it must fill
these fields, and invalid responses are rejected before they reach Gmail.
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field

# from enum import Enum
# from pydantic import BaseModel, Field


class Category(str, Enum):
    """
        The single semantic class of an email - a closed set so mapping is deterministic.

        str-mixin -> serializes as "finance", not Category.FINANCE. Drawn from policy.md
    """

    PERSONAL= "personal"
    CLIENT = "client"
    FINANCE = "finance"
    SECURITY = "security"
    LOGISTICS = "logistics"
    NEWSLETTER = "newsletter"
    PROMOTION = "promotion"
    RECEIPT = "receipt"
    NOTIFICATION = "notification"
    COLD_OUTREACH = "cold_outreach"

class Label(str, Enum):
    """
    A Gmail label to apply to an email.
    Make sure the labels exists in your gmail.
    """

    NEWSLETTER = "Newsletter"
    NOTIFICATION = "Notification"
    PAYMENT = "Payment"
    PROGRAMMING_UPDATES = "Programming Updates"
    JOB_APPLICATIONS = "Job Applications"
    PROMOTIONS = "Promotions"

class TriageVerdict(BaseModel):
    """
    The classifier's decision for one email.

    Field order = reasoning order: `reason` is first so the model justifies before it commits to the verdict ( a built-in mini chain-of-thoughts). All fields required, no defaults - strict structured outputs need every field present.
    """

    reason: str = Field(
        description="One line justifying the verdict, citing the policy rule. Decide this FIRST."
    )
    category: Category = Field(
        description="The single best fit category for this email."
    )
    labels: list[Label] = Field(
        description="Gmail labels to apply. Empty list if it stays in Primary untouched."
    )
    importance: int = Field(
        description="0-49 = noise, 50-79 = read soon, 80-100 = needs my action today",
        ge=0,
        le=100,
    )
    keep_in_primary: bool = Field(
        description="True only if needs my personal attention and should stay in Primary."
    )
