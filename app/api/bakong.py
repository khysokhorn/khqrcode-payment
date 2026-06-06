import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.schemas.payment import (
    BakongCheckTransactionRequest,
    BakongCheckTransactionResponse,
)
from app.services.khqr_service import khqr_service
from app.core.db import get_session
from app.models.transaction import Transaction

router = APIRouter(prefix="/bakong", tags=["Bakong"])


@router.post("/check-transaction", response_model=BakongCheckTransactionResponse)
async def check_transaction(
    request: BakongCheckTransactionRequest, db: Session = Depends(get_session)
):
    """
    Checks the status of a transaction on Bakong Open API and updates the local status.
    Accepts either `md5` or `tran_id`.
    """
    tx = None
    md5 = request.md5
    tran_id = request.tran_id

    if not md5 and not tran_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'md5' or 'tran_id' must be provided in the request body.",
        )

    if tran_id:
        tx = db.exec(select(Transaction).where(Transaction.tran_id == tran_id)).first()
        if not tx:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction with tran_id '{tran_id}' not found.",
            )
        if not md5:
            md5 = tx.md5

    if not md5:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve MD5 hash for transaction.",
        )

    if not tx:
        tx = db.exec(select(Transaction).where(Transaction.md5 == md5)).first()

    # Query Bakong API for payment status details
    raw_details = khqr_service.get_payment_details(md5)

    if raw_details:
        # Transaction is PAID
        if tx:
            tx.status = "SUCCESS"
            tx.updated_at = datetime.now(timezone.utc)
            tx.raw_response = json.dumps(raw_details)
            db.add(tx)
            db.commit()
            db.refresh(tx)

        amount = raw_details.get("amount")
        currency = raw_details.get("currency")
        bakong_txn_id = (
            raw_details.get("hash")
            or raw_details.get("transaction_id")
            or raw_details.get("externalRef")
        )

        return BakongCheckTransactionResponse(
            status="PAID",
            tran_id=tx.tran_id if tx else None,
            md5=md5,
            amount=float(amount) if amount is not None else None,
            currency=currency,
            bakong_transaction_id=bakong_txn_id,
            raw_data=raw_details,
        )
    else:
        # Transaction is not paid or not found
        status = "PENDING"
        if tx:
            if tx.status == "SUCCESS":
                status = "PAID"
            else:
                is_expired = False
                if tx.expired_at:
                    now = datetime.now(timezone.utc)
                    tx_expired_at = tx.expired_at
                    if tx_expired_at.tzinfo is None:
                        tx_expired_at = tx_expired_at.replace(tzinfo=timezone.utc)

                    if now > tx_expired_at:
                        is_expired = True

                if is_expired:
                    tx.status = "EXPIRED"
                    tx.updated_at = datetime.now(timezone.utc)
                    db.add(tx)
                    db.commit()
                    db.refresh(tx)
                    status = "EXPIRED"
                else:
                    status = tx.status

        return BakongCheckTransactionResponse(
            status=status,
            tran_id=tx.tran_id if tx else None,
            md5=md5,
            amount=tx.amount if tx else None,
            currency=tx.currency if tx else None,
            raw_data=None,
        )
