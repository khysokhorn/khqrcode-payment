"""Transaction lookup through the public Bakong gateway's Nuxt SSR response.

The client uses only the Python standard library and requires no developer token.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Union


def resolve_nuxt_data(raw_data: list) -> Optional[dict[str, Any]]:
    """Resolve the tx-lookup entry in a Nuxt devalue array."""
    if not isinstance(raw_data, list):
        raise ValueError("Expected a Nuxt data array")

    def resolve(index: int, seen: set[int]) -> Any:
        # Nuxt/devalue represents undefined with the special reference -1.
        if index == -1:
            return None
        if type(index) is not int or not 0 <= index < len(raw_data):
            raise ValueError("Invalid Nuxt data reference")
        if index in seen:
            return None
        seen = seen | {index}
        value = raw_data[index]
        if isinstance(value, dict):
            return {key: resolve(ref, seen) for key, ref in value.items()}
        if isinstance(value, list):
            if value and isinstance(value[0], str) and value[0] in (
                "ShallowReactive", "Reactive", "Ref", "ShallowRef",
            ):
                if len(value) != 2:
                    raise ValueError("Invalid Nuxt wrapper")
                return resolve(value[1], seen)
            return [resolve(ref, seen) for ref in value]
        return value

    for item in raw_data:
        if isinstance(item, dict) and "tx-lookup" in item:
            result = resolve(item["tx-lookup"], set())
            if not isinstance(result, dict) or not {"txResult", "txError"} <= result.keys():
                raise ValueError("Invalid transaction lookup response")
            return result
    return None


class PublicBakongOpenAPI:
    """Client for the public-bakong transaction verification service."""

    BASE_URL = "https://api-bakong.nbc.gov.kh/"
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def check_transaction(
        self,
        search_type: str = "SHORT_HASH",
        value: str = "",
        amount: Optional[Union[str, int, float]] = None,
        ccy: Optional[str] = "KHR",
    ) -> dict[str, Any]:
        """Look up a transaction; invalid input raises ValueError.

        SHORT_HASH requires a positive amount and KHR or USD. HASH and MD5
        require only the identifier. Gateway and transport failures are returned
        in txError, using the same response envelope as the supplied client.
        """
        search_type = search_type.upper().strip()
        value = str(value).strip()
        lengths = {"SHORT_HASH": 8, "HASH": 64, "MD5": 32}
        if search_type not in lengths:
            raise ValueError("type must be SHORT_HASH, HASH, or MD5")
        if not re.fullmatch(r"[a-fA-F0-9]{%d}" % lengths[search_type], value):
            raise ValueError(f"value must be a {lengths[search_type]}-character hexadecimal identifier")

        payload = {"type": search_type, "value": value}
        if search_type == "SHORT_HASH":
            amount_text = str(amount).strip() if amount is not None else ""
            try:
                numeric_amount = Decimal(amount_text)
            except InvalidOperation:
                raise ValueError("SHORT_HASH requires a positive amount") from None
            if not numeric_amount.is_finite() or numeric_amount <= 0:
                raise ValueError("SHORT_HASH requires a positive amount")
            currency = (ccy or "").upper().strip()
            if currency not in ("KHR", "USD"):
                raise ValueError("ccy must be KHR or USD")
            payload.update(amount=amount_text, ccy=currency)

        cookie = urllib.parse.quote(json.dumps(payload, separators=(",", ":")), safe="")
        request = urllib.request.Request(self.BASE_URL, headers={
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cookie": f"tx_search={cookie}; theme=dark",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except (urllib.error.URLError, OSError) as exc:
            return {"txResult": None, "txError": {
                "errorCode": -1, "message": f"Network error: {exc}", "isNetworkError": True,
            }}

        try:
            html = body.decode("utf-8")
            match = re.search(
                r"<script\b[^>]*\bid\s*=\s*['\"]__NUXT_DATA__['\"][^>]*>(.*?)</script\s*>",
                html, re.DOTALL | re.IGNORECASE,
            )
            if not match:
                return {"txResult": None, "txError": {
                    "errorCode": -2, "message": "Failed to parse __NUXT_DATA__ from response",
                }}
            result = resolve_nuxt_data(json.loads(match.group(1)))
            if result is None:
                return {"txResult": None, "txError": {
                    "errorCode": 1, "message": "Transaction not found or invalid format",
                }}
            tx = result.get("txResult")
            if tx is not None:
                if not isinstance(tx, dict):
                    raise ValueError("Invalid transaction details")
                for field in ("createdDate", "acknowledgedDate"):
                    timestamp = tx.get(f"{field}Ms")
                    if timestamp is not None:
                        tx[f"{field}Iso"] = datetime.fromtimestamp(
                            timestamp / 1000.0, tz=timezone.utc,
                        ).isoformat()
            return result
        except (ValueError, TypeError, OverflowError, OSError, RecursionError) as exc:
            return {"txResult": None, "txError": {
                "errorCode": -3, "message": f"Error decoding data: {exc}",
            }}


public_bakong_open_api = PublicBakongOpenAPI()
