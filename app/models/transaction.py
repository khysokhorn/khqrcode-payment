from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tran_id: str = Field(index=True, unique=True)
    amount: float
    currency: str = "USD"
    status: str = "PENDING" # PENDING, SUCCESS, FAILED
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    aba_aprt: Optional[str] = None # ABA Approval Reference
    raw_response: Optional[str] = None # JSON string of full callback
