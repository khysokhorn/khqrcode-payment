from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlmodel import Session, select
from app.schemas.payment import (
    KHQRGenerateRequest, 
    KHQRGenerateResponse, 
    KHQRDecodeResponse,
    BankTemplateCreate,
    BankTemplateResponse
)
from app.services.khqr_service import khqr_service
from app.core.db import get_session
from app.models.transaction import Transaction
from app.models.template import BankTemplate
from typing import Optional
import json

router = APIRouter(prefix="/khqr", tags=["KHQR"])

@router.post("/generate", response_model=KHQRGenerateResponse)
async def generate_khqr(request: KHQRGenerateRequest, db: Session = Depends(get_session)):
    """
    Generates a KHQR code payload and saves the transaction as PENDING.
    """
    try:
        # 1. Create a record in our database
        new_tx = Transaction(
            tran_id=request.tran_id,
            amount=request.amount,
            currency=request.currency,
            status="PENDING"
        )
        db.add(new_tx)
        db.commit()

        # 2. Generate KHQR
        result = khqr_service.generate_qr(request)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/decode", response_model=KHQRDecodeResponse)
async def decode_khqr(
    file: UploadFile = File(...), 
    save_as_template: bool = Form(False),
    template_name: Optional[str] = Form(None),
    db: Session = Depends(get_session)
):
    """
    Uploads a QR code image and decodes the KHQR information.
    Optionally saves it as a Bank Template.
    """
    try:
        contents = await file.read()
        result = khqr_service.decode_from_image(contents)
        
        if save_as_template and template_name:
            # Save to database
            template = BankTemplate(
                name=template_name,
                bakong_account=result.bakong_account or "",
                merchant_name=result.merchant_name or "Unknown",
                merchant_city=result.merchant_city or "Phnom Penh",
                currency=result.currency or "USD"
            )
            db.add(template)
            db.commit()
            
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates", response_model=BankTemplateResponse)
async def create_template(template: BankTemplateCreate, db: Session = Depends(get_session)):
    """
    Manually create a Bank Template.
    """
    db_template = BankTemplate.from_orm(template)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates", response_model=list[BankTemplateResponse])
async def list_templates(db: Session = Depends(get_session)):
    """
    List all available Bank Templates.
    """
    templates = db.exec(select(BankTemplate)).all()
    return templates

@router.post("/generate-from-template/{template_id}", response_model=KHQRGenerateResponse)
async def generate_from_template(
    template_id: int, 
    amount: float,
    tran_id: str,
    db: Session = Depends(get_session)
):
    """
    Generate a KHQR code using a saved Bank Template.
    """
    template = db.get(BankTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    request = KHQRGenerateRequest(
        tran_id=tran_id,
        amount=amount,
        currency=template.currency,
        bank_account=template.bakong_account,
        merchant_name=template.merchant_name,
        merchant_city=template.merchant_city
    )
    
    # 1. Create a record in our database
    new_tx = Transaction(
        tran_id=request.tran_id,
        amount=request.amount,
        currency=request.currency,
        status="PENDING"
    )
    db.add(new_tx)
    db.commit()

    # 2. Generate KHQR
    result = khqr_service.generate_qr(request)
    return result

@router.get("/verify/{md5}")
async def verify_khqr(md5: str):
    """
    Verifies the transaction status using the Bakong MD5 hash.
    Note: Requires a valid Bakong Developer Token in settings.
    """
    try:
        result = await khqr_service.verify_transaction(md5)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
