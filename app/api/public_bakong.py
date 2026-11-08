"""Public Bakong Open API routes, independent of local transaction records."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.public_bakong_open_api import public_bakong_open_api

router = APIRouter(prefix="/public-bakong", tags=["Public Bakong Open API"])


@router.get("/check")
def check_transaction(
    search_type: str = Query("SHORT_HASH", alias="type", description="SHORT_HASH, HASH, or MD5"),
    value: Optional[str] = Query(None, description="Transaction identifier"),
    hash_value: Optional[str] = Query(None, alias="hash", description="Alias for value"),
    amount: Optional[str] = Query(None, description="Required for SHORT_HASH"),
    ccy: str = Query("KHR", description="KHR or USD, for SHORT_HASH"),
):
    """Return the gateway's txResult/txError envelope with UTC ISO timestamps.

    Invalid lookup parameters return HTTP 400. Upstream failures return HTTP 200
    with txResult=null and details in txError; they do not indicate payment.
    """
    identifier = value if value is not None else hash_value
    if not identifier or not identifier.strip():
        raise HTTPException(400, "Missing required parameter 'value' or 'hash'")
    try:
        # A sync route lets FastAPI run the blocking urllib request in a worker.
        return public_bakong_open_api.check_transaction(
            search_type=search_type, value=identifier, amount=amount, ccy=ccy,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/health")
def health():
    """Check local service availability without querying the gateway."""
    return {"status": "ok", "service": "public-bakong"}
