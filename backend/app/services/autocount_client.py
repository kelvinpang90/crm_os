"""Thin HTTP client for the AutoCount Cloud Accounting Integration API.

Auth: `API-Key` + `Key-ID` request headers (self-service generated in
AutoCount Cloud Accounting under Settings > API Keys) — no OAuth.

Listing endpoints (debtor/invoice/quotation) are all paginated: each page
holds at most 100 records per the official docs, but this client doesn't
hardcode that number — it just keeps requesting the next page until one
comes back empty, so it stays correct even if that limit changes.
"""
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AutocountClientError(Exception):
    """Raised when the AutoCount API returns a non-2xx response."""


def _headers() -> dict[str, str]:
    return {
        "API-Key": settings.autocount_api_key,
        "Key-ID": settings.autocount_key_id,
    }


async def _get_all_pages(path: str, extra_params: dict[str, Any] | None = None) -> list[dict]:
    """Fetch every page of a `/listing` endpoint and concatenate `data`."""
    url = f"{settings.autocount_api_base_url}/{settings.autocount_account_book_id}{path}"
    records: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {"page": page, **(extra_params or {})}
            resp = await client.get(url, headers=_headers(), params=params)
            if resp.status_code != 200:
                raise AutocountClientError(
                    f"GET {path} page={page} failed: {resp.status_code} {resp.text}"
                )
            body = resp.json()
            batch = body.get("data") or []
            if not batch:
                break
            records.extend(batch)
            page += 1
    return records


# debtor/listing ignores the documented camelCase field names and always
# serializes PascalCase keys (confirmed empirically against the real API —
# differs from invoice/quotation listing, which do return camelCase as
# documented). AccNo/CompanyName/CurrencyCode come back even without
# requesting them; the rest must be requested explicitly via `field` or
# they're omitted.
_DEBTOR_FIELDS = [
    "AccNo", "CompanyName", "Attention", "EmailAddress", "Phone1", "Address",
    "IsActive", "NatureOfBusiness",
]


async def get_all_debtors(active_only: bool = True) -> list[dict]:
    return await _get_all_pages(
        "/debtor/listing",
        {"activeOnly": active_only, "field": _DEBTOR_FIELDS},
    )


async def get_all_invoices() -> list[dict]:
    return await _get_all_pages("/invoice/listing")


async def get_all_quotations() -> list[dict]:
    return await _get_all_pages("/quotation/listing")
