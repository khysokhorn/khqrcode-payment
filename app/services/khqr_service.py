import qrcode
import io
import base64
import cv2
import numpy as np
from bakong_khqr import KHQR
from bakong_khqr.sdk.emv_parser import EMVParser
from app.core.config import settings
from app.schemas.payment import KHQRGenerateRequest, KHQRDecodeResponse

class KHQRService:
    def __init__(self):
        # The library uses bakong_token as the argument name
        self.khqr = KHQR(bakong_token=settings.BAKONG_TOKEN)
        self.default_account = settings.BAKONG_ACCOUNT_ID

    def generate_qr(self, request: KHQRGenerateRequest):
        # Determine which account to use
        bank_account = request.bank_account or self.default_account
        
        # 1. Generate the KHQR payload string
        qr_string = self.khqr.create_qr(
            bank_account=bank_account,
            merchant_name=request.merchant_name,
            merchant_city=request.merchant_city,
            amount=request.amount,
            currency=request.currency,
            store_label=request.store_label,
            terminal_label=request.terminal_label
        )
        
        # 2. Generate MD5 hash
        md5 = self.khqr.generate_md5(qr_string)
        
        # 3. Generate QR Image base64 using the library's built-in method
        img_base64 = self.khqr.qr_image(qr_string, format="base64")
        
        return {
            "qr_string": qr_string,
            "md5": md5,
            "qr_image_base64": img_base64,
            "tran_id": request.tran_id
        }

    def decode_from_image(self, image_bytes: bytes) -> KHQRDecodeResponse:
        # 1. Decode QR from image using OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image file")
            
        detector = cv2.QRCodeDetector()
        qr_string, _, _ = detector.detectAndDecode(img)
        
        if not qr_string:
            raise ValueError("No QR code found in image")
            
        return self.decode_from_string(qr_string)

    def decode_from_string(self, qr_string: str) -> KHQRDecodeResponse:
        # 2. Parse EMV tags
        parser = EMVParser(qr_string)
        tags = parser.parsed
        
        # 3. Extract common KHQR fields
        amount = tags.get("54")
        currency_code = tags.get("53")
        currency = "USD" if currency_code == "840" else "KHR" if currency_code == "116" else currency_code
        
        # Parse Account Info (Tag 29)
        account_info_raw = tags.get("29", "")
        bakong_account = None
        if account_info_raw:
            acc_parser = EMVParser(account_info_raw)
            bakong_account = acc_parser.get("01")
            
        # Parse Additional Data (Tag 62)
        store_label = None
        terminal_label = None
        additional_data_raw = tags.get("62", "")
        if additional_data_raw:
            add_parser = EMVParser(additional_data_raw)
            store_label = add_parser.get("05")
            terminal_label = add_parser.get("07")

        return KHQRDecodeResponse(
            qr_string=qr_string,
            bakong_account=bakong_account,
            merchant_name=tags.get("59"),
            merchant_city=tags.get("60"),
            amount=float(amount) if amount else None,
            currency=currency,
            store_label=store_label,
            terminal_label=terminal_label,
            country_code=tags.get("58"),
            raw_tags=tags
        )

    async def verify_transaction(self, md5: str):
        """
        Verify transaction status using Bakong API.
        """
        # The library method is check_payment
        return self.khqr.check_payment(md5)

khqr_service = KHQRService()
