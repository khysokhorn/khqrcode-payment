from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PaymentItem(BaseModel):
    name: str
    quantity: int
    price: float


class KHQRGenerateRequest(BaseModel):
    tran_id: str
    amount: float
    currency: str = "USD"
    bank_account: Optional[str] = None  # e.g. username@aba
    merchant_name: Optional[str] = "Merchant Name"
    merchant_city: Optional[str] = "Phnom Penh"
    store_label: Optional[str] = "Main Store"
    terminal_label: Optional[str] = "Cashier 1"
    callback_url: Optional[str] = None  # URL to return to after payment,
    expire_minutes: int = 5


class KHQRGenerateResponse(BaseModel):
    qr_string: str
    md5: str
    tran_id: str
    qr_image_url: Optional[str] = None
    bakong_deeplink: Optional[str] = None
    currency_code: Optional[str] = None
    amount: Optional[float] = None


class KHQRDecodeResponse(BaseModel):
    qr_string: str
    bakong_account: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_city: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    store_label: Optional[str] = None
    terminal_label: Optional[str] = None
    country_code: Optional[str] = None
    raw_tags: dict[str, str]


class TransactionResponse(BaseModel):
    id: int
    tran_id: str
    md5: Optional[str] = None
    amount: float
    currency: str
    status: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    aba_aprt: Optional[str] = None
    qr_code_path: Optional[str] = None
    expired_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentStatusResponse(BaseModel):
    tran_id: str
    status: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
