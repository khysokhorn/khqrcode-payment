from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.schemas.payment import ABAOrderCreate, ABAPaymentResponse, ABATransactionCheck, ABATransactionStatusResponse
from app.services.aba_service import aba_service
from app.core.db import get_session
from app.models.transaction import Transaction
import json

router = APIRouter(prefix="/aba", tags=["ABA PayWay"])

@router.post("/create-deeplink", response_model=ABAPaymentResponse)
async def create_aba_deeplink(order: ABAOrderCreate, db: Session = Depends(get_session)):
    """
    Creates an ABA PayWay deep link for payment and saves it to the database.
    """
    try:
        # 1. Create a record in our database
        new_tx = Transaction(
            tran_id=order.tran_id,
            amount=order.amount,
            currency=order.currency,
            firstname=order.firstname,
            lastname=order.lastname,
            email=order.email,
            status="PENDING"
        )
        db.add(new_tx)
        db.commit()

        # 2. Call ABA API
        result = await aba_service.initiate_payment(order)
        
        # Log for debugging
        print(f"ABA API Response: {result}")
        
        # If ABA returns an error code, we can still return it but it will now match our schema
        return result
    except Exception as e:
        print(f"Error in create_aba_deeplink: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-transaction", response_model=ABATransactionStatusResponse)
async def check_transaction(check: ABATransactionCheck, db: Session = Depends(get_session)):
    """
    Checks the status of an ABA PayWay transaction and updates our database.
    """
    try:
        result = await aba_service.check_transaction(check.tran_id)
        
        # Update database if transaction is found
        statement = select(Transaction).where(Transaction.tran_id == check.tran_id)
        tx = db.exec(statement).first()
        if tx and result.get("status") == 0:
            tx.status = "SUCCESS"
            tx.aba_aprt = result.get("aprt")
            db.add(tx)
            db.commit()
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def aba_callback(data: dict, db: Session = Depends(get_session)):
    """
    Callback URL for ABA PayWay to notify about payment status.
    """
    print(f"Received ABA Callback: {data}")
    
    tran_id = data.get("tran_id")
    if tran_id:
        statement = select(Transaction).where(Transaction.tran_id == tran_id)
        tx = db.exec(statement).first()
        if tx:
            # ABA status 0 means success
            if str(data.get("status")) == "0":
                tx.status = "SUCCESS"
            else:
                tx.status = "FAILED"
            
            tx.aba_aprt = data.get("aprt")
            tx.raw_response = json.dumps(data)
            db.add(tx)
            db.commit()
            
    return {"status": "success"}

@router.get("/transactions", response_model=list[Transaction])
async def list_transactions(db: Session = Depends(get_session)):
    """
    Returns a list of all transactions in the database.
    """
    transactions = db.exec(select(Transaction)).all()
    return transactions
