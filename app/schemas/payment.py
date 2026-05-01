from pydantic import BaseModel
from typing import Optional, List

class PaymentItem(BaseModel):
    name: str
    quantity: int
    price: float

class ABAOrderCreate(BaseModel):
    tran_id: str
    amount: float
    items: Optional[List[PaymentItem]] = None
    currency: str = "USD"
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    return_url: Optional[str] = None
    continue_success_url: Optional[str] = None

class ABAPaymentResponse(BaseModel):
    status: Optional[int] = None
    description: Optional[str] = None
    qr_code: Optional[str] = None
    qr_image: Optional[str] = None
    abapay_deeplink: Optional[str] = None
    app_deeplink: Optional[str] = None

class ABATransactionCheck(BaseModel):
    tran_id: str

class ABATransactionStatusResponse(BaseModel):
    status: int
    description: Optional[str] = None
    amount: Optional[float] = None
    tran_id: Optional[str] = None
    aprt: Optional[str] = None # Approval Reference Number

class KHQRGenerateRequest(BaseModel):
    tran_id: str
    amount: float
    currency: str = "USD"
    bank_account: Optional[str] = None # e.g. username@aba
    merchant_name: Optional[str] = "Merchant Name"
    merchant_city: Optional[str] = "Phnom Penh"
    store_label: Optional[str] = "Main Store"
    terminal_label: Optional[str] = "Cashier 1"
    callback_url: Optional[str] = None # URL to return to after payment

class KHQRGenerateResponse(BaseModel):
    qr_string: str
    md5: str
    qr_image_base64: Optional[str] = None
    qr_image_url: Optional[str] = None
    bakong_deeplink: Optional[str] = None
    tran_id: str

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

class BankTemplateCreate(BaseModel):
    name: str
    bakong_account: str
    merchant_name: str
    merchant_city: str = "Phnom Penh"
    currency: str = "USD"

class BankTemplateResponse(BankTemplateCreate):
    id: int
