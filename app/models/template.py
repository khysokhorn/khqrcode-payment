from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class BankTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    bakong_account: str
    merchant_name: str
    merchant_city: str = "Phnom Penh"
    currency: str = "USD"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
