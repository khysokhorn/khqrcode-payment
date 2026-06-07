from pydantic import BaseModel
from typing import Optional


class BakongTransactionData(BaseModel):
    hash: str
    fromAccountId: str
    toAccountId: str
    currency: str
    amount: float
    description: Optional[str] = None
    createdDateMs: int
    acknowledgedDateMs: int
    externalRef: Optional[str] = None


class BakongTransactionResponse(BaseModel):
    responseCode: int
    responseMessage: str
    errorCode: Optional[str] = None
    data: Optional[BakongTransactionData] = None
