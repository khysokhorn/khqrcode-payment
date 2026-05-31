from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.schemas.payment import (
    KHQRGenerateRequest,
    KHQRGenerateResponse,
    PaymentStatusResponse,
    TransactionResponse,
)
from app.services.khqr_service import khqr_service
from app.core.db import get_session
from app.models.transaction import Transaction

router = APIRouter(prefix="/khqr", tags=["KHQR"])


@router.post("/generate", response_model=KHQRGenerateResponse)
async def generate_khqr(
    request: KHQRGenerateRequest, db: Session = Depends(get_session)
):
    query = select(Transaction)
    tx = db.exec(query.where(Transaction.tran_id == request.tran_id)).first()
    if tx and tx.status == "PENDING":
        is_expired = tx.expire_at and tx.expire_at < datetime.now(timezone.utc)
        if not is_expired:
            return khqr_service.get_KhqrCode(tx)

    """
    Generates a KHQR code payload and saves the transaction as PENDING.
    """
    try:
        expire_minutes = request.expire_minutes
        result = khqr_service.generate_qr(request)
        md5 = result.get("md5")
        qr_code_path = result.get("qr_code_path")

        new_tx = Transaction(
            tran_id=request.tran_id,
            md5=md5,
            amount=request.amount,
            currency=request.currency,
            status="PENDING",
            qr_code_path=qr_code_path,
            expire_at=datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        )
        db.add(new_tx)
        db.commit()

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decode")
async def decode_khqr(
    file: UploadFile = File(...),
    qrCode_string: Optional[str] = Form(None),
    db: Session = Depends(get_session),
):
    """
    Uploads a QR code image and decodes the KHQR information.
    Optionally saves it as a Bank Template.
    """
    try:
        if file:
            contents = await file.read()
            result = khqr_service.decode_from_image(contents)
            return result

        if qrCode_string:
            result = khqr_service.decode_from_string(qrCode_string)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    status: Optional[str] = Query(None, description="Filter by transaction status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    """
    Retrieve all KHQR transactions with optional filtering by status.
    """
    try:
        query = select(Transaction)

        if status:
            query = query.where(Transaction.status == status)

        # Order by most recent first
        query = query.offset(offset).limit(limit)

        transactions = db.exec(query).all()
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{tran_id}")
async def verify_khqr(
    tran_id: str,
    db: Session = Depends(get_session),
    response_model=PaymentStatusResponse,
):
    """
    Verifies the transaction status using the Bakong MD5 hash.
    Note: Requires a valid Bakong Developer Token in settings.
    """
    try:
        tx = db.exec(select(Transaction).where(Transaction.tran_id == tran_id)).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        md5 = tx.md5
        if not md5:
            raise HTTPException(
                status_code=400, detail="MD5 hash not found for this transaction"
            )
        result = await khqr_service.verify_transaction(md5)
        if not result or result is dict:
            raise HTTPException(
                status_code=500, detail="Failed to verify transaction with Bakong API"
            )
        return PaymentStatusResponse(
            tran_id=tran_id,
            amount=tx.amount,
            currency=tx.currency,
            status=result.get("status", "UNKNOWN"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def list_transactions(db: Session = Depends(get_session)):
    """
    Lists all transactions in our database.
    """
    transactions = db.exec(select(Transaction)).all()
    return transactions
