from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Query
from sqlmodel import Session, func, select
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
    status = tx.status if tx else None
    if tx and tx.status == "PENDING":
        print(f"expired_at: {tx.expired_at}, now: {datetime.now(timezone.utc)}")
        is_expired = (
            tx.expired_at
            and db.exec(
                select(Transaction.id)
                .where(Transaction.id == tx.id)
                .where(Transaction.expired_at > func.now())
            ).first()
            is None
        )
        if not is_expired:
            khqr_code_response = khqr_service.get_KhqrCode(tx)
            return {
                "qr_string": khqr_code_response.qr_string,
                "md5": khqr_code_response.md5,
                "qr_image_url": khqr_code_response.qr_image_url,
                "tran_id": tx.tran_id,
                "currency_code": tx.currency,
                "amount": tx.amount,
            }
        else:
            request.tran_id = str(uuid.uuid4())
            request.expire_minutes = int(timedelta(days=1).total_seconds() / 60)

    if status == "PAID" and tx:
        khqr_code_response = khqr_service.get_KhqrCode(tx)
        return {
            "qr_string": khqr_code_response.qr_string,
            "md5": khqr_code_response.md5,
            "qr_image_url": khqr_code_response.qr_image_url,
            "tran_id": tx.tran_id,
            "currency_code": tx.currency,
            "amount": tx.amount,
            "status": tx.status,
        }
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
            expired_at=datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        )
        db.add(new_tx)
        db.commit()

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decode")
async def decode_khqr(
    file: Optional[UploadFile] = File(None),
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
