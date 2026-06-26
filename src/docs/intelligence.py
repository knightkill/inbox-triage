"""Read PDF/image email attachments with Azure Document Intelligence.

M4: you write this, adapting ~/Code/personal-test-ms-doc-int/app.py:
  - SDK: azure-ai-formrecognizer (DocumentAnalysisClient), model 'prebuilt-document'.
  - Construct with endpoint + AzureKeyCredential(key) from get_settings().
  - Submit bytes directly (no temp file): begin_analyze_document('prebuilt-document', data).
  - Read result.content (raw text) and result.key_value_pairs (structured fields).

Keep the encrypted/invalid-PDF sentinel idea from invoice-fetcher: never let one bad
attachment crash the whole triage run — return a sentinel and move on.
"""

from __future__ import annotations

# from azure.ai.formrecognizer import DocumentAnalysisClient
# from azure.core.credentials import AzureKeyCredential
# from src.config import get_settings

UNREADABLE = "__UNREADABLE_ATTACHMENT__"  # sentinel: skip, don't crash


def extract_attachment_text(attachment_bytes: bytes) -> str:
    """Return extracted text + key fields from an attachment, or UNREADABLE on failure.

    M4 steps:
      1. settings = get_settings(); guard if docintel_endpoint/key are None.
      2. client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key)).
      3. poller = client.begin_analyze_document('prebuilt-document', attachment_bytes).
      4. result = poller.result(); build a compact string of result.content plus the
         key_value_pairs (so the classifier sees e.g. "Total: 12,400 INR").
      5. Wrap in try/except → return UNREADABLE on any error (encrypted, oversized).
    """
    raise NotImplementedError("TODO(M4): implement Document Intelligence extraction")
