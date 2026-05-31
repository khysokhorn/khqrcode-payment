import string
from time import time

import qrcode
import io
import base64
import cv2
import numpy as np
from typing import Optional
from bakong_khqr import KHQR
from bakong_khqr.sdk.emv_parser import EMVParser
from app.core.config import settings
from app.models.transaction import Transaction
from app.schemas.payment import (
    KHQRGenerateRequest,
    KHQRDecodeResponse,
    KHQRGenerateResponse,
)
from PIL import Image, ImageDraw, ImageFont, ImageOps
from qrcode.image.pil import PilImage


class KHQRGenerator:
    @staticmethod
    def format_tag(tag: str, value: str) -> str:
        return f"{tag}{len(value):02}{value}"

    @staticmethod
    def generate(
        bank_account: str,
        merchant_name: str,
        amount: float,
        expire_minutes: int,
        merchant_city: str = "Phnom Penh",
        currency: str = "USD",
        store_label: Optional[str] = None,
        terminal_label: Optional[str] = None,
        bill_number: Optional[str] = None,
    ) -> str:
        payload = ""
        # 00: Payload Format Indicator
        payload += KHQRGenerator.format_tag("00", "01")
        # 01: Point of Initiation Method (12 for dynamic, 11 for static)
        poi = "12" if amount else "11"
        payload += KHQRGenerator.format_tag("01", poi)

        # 29: Merchant Account Information
        aid = "khqr@bakong"
        acc_id = bank_account
        bank_name = "Bakong"

        # Handle ABA specific identification
        if "@aba" in bank_account.lower():
            aid = "abaakhppxxx@abaa"
            acc_id = bank_account.split("@")[0]
            bank_name = "ABA Bank"

        tag29_value = KHQRGenerator.format_tag("00", aid)
        tag29_value += KHQRGenerator.format_tag("01", acc_id)
        # Add bank name as sub-tag 02 for better compatibility
        tag29_value += KHQRGenerator.format_tag("02", bank_name)

        payload += KHQRGenerator.format_tag("29", tag29_value)

        # 52: Merchant Category Code (5999 is standard)
        payload += KHQRGenerator.format_tag("52", "5999")

        # 53: Transaction Currency
        curr_code = "840" if currency == "USD" else "116"
        payload += KHQRGenerator.format_tag("53", curr_code)

        # 54: Transaction Amount
        if amount:
            if currency == "KHR":
                amt_str = str(int(amount))
            else:
                # USD: Format to max 2 decimal places, remove trailing zeros
                amt_str = f"{amount:.2f}".rstrip("0").rstrip(".")
            payload += KHQRGenerator.format_tag("54", amt_str)

        # 58: Country Code
        payload += KHQRGenerator.format_tag("58", "KH")
        # 59: Merchant Name (Max 25 chars)
        payload += KHQRGenerator.format_tag("59", merchant_name[:25])
        # 60: Merchant City (Max 15 chars)
        payload += KHQRGenerator.format_tag("60", merchant_city[:15])

        # 62: Additional Data
        tag62_value = ""
        if bill_number:
            tag62_value += KHQRGenerator.format_tag("01", bill_number[:25])
        if store_label:
            tag62_value += KHQRGenerator.format_tag("03", store_label[:25])
        if terminal_label:
            tag62_value += KHQRGenerator.format_tag("07", terminal_label[:25])

        if tag62_value:
            payload += KHQRGenerator.format_tag("62", tag62_value)

        # 99: Timestamp (Mandatory for many banks)
        import time

        now_ms = str(int(time.time() * 1000))
        # 00 is creation time, 01 is expiration time
        tag99_value = KHQRGenerator.format_tag("00", now_ms)
        if poi == "12":  # Dynamic
            # Expire in 30 days (Bakong standard default)
            exp_ms = str(int(time.time() * 1000) + (expire_minutes * 60 * 1000))
            tag99_value += KHQRGenerator.format_tag("01", exp_ms)

        payload += KHQRGenerator.format_tag("99", tag99_value)

        # 63: CRC (Uppercase is safer for some apps)
        payload += "6304"
        payload += KHQRGenerator.crc16_ccitt(payload).upper()

        return payload

    @staticmethod
    def crc16_ccitt(data: str) -> str:
        crc = 0xFFFF
        for byte in data.encode("ascii"):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return f"{crc:04X}"


class KHQRService:
    def __init__(self):
        # The library uses bakong_token as the argument name
        self.khqr = KHQR(bakong_token=settings.BAKONG_TOKEN)
        self.default_account = settings.BAKONG_ACCOUNT_ID

    def generate_qr(self, request: KHQRGenerateRequest):
        # Determine which account to use
        bank_account = request.bank_account or self.default_account
        # 1. Generate the KHQR payload string using our robust generator
        qr_string = KHQRGenerator.generate(
            bank_account=bank_account,
            merchant_name=request.merchant_name or "Unknown",
            merchant_city=request.merchant_city or "Phnom Penh",
            amount=request.amount,
            currency=request.currency,
            store_label=request.store_label or "Store",
            terminal_label=request.terminal_label or "Terminal",
            expire_minutes=request.expire_minutes,
        )

        # 2. Generate MD5 hash
        md5 = self.khqr.generate_md5(qr_string)

        # 3. Generate Styled QR Image using the library's built-in styled generator
        # This will use our custom qr_string but apply the KHQR branding (red header, logos, etc.)
        img_base64 = self.khqr.qr_image(qr_string, format="base64")

        # 4. Save image to file
        image_filename = f"{request.tran_id}.png"
        image_path = f"static/qr_codes/{image_filename}"

        img_data = base64.b64decode(img_base64)
        with open(image_path, "wb") as f:
            f.write(img_data)

        qr_image_url = f"/static/qr_codes/{image_filename}"

        # 5. Generate Bakong Deeplink
        deeplink = None
        if settings.BAKONG_TOKEN:
            try:
                # Use the provided callback_url if available
                callback = request.callback_url or "https://bakong.nbc.org.kh"

                deeplink = self.khqr.generate_deeplink(
                    qr=qr_string,
                    callback=callback,
                    appName=request.merchant_name or "Merchant",
                )
            except Exception:
                # FALLBACK: If Bakong API is down, generate a manual deep link
                # This works without an API call
                deeplink = f"https://bakong.nbc.gov.kh/qr/{qr_string}"
        else:
            # If no token, always use the manual fallback link
            deeplink = f"https://bakong.nbc.gov.kh/qr/{qr_string}"

        return {
            "qr_string": qr_string,
            "md5": md5,
            "qr_image_base64": img_base64,
            "qr_image_url": qr_image_url,
            "bakong_deeplink": deeplink,
            "tran_id": request.tran_id,
            "qr_code_path": image_path,
        }

    def decode_from_image(self, image_bytes: bytes) -> dict:
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

    def decode_from_string(self, qr_string: str) -> dict:
        # 2. Parse EMV tags
        parser = EMVParser(qr_string)
        tags = parser.parsed

        # 3. Extract common KHQR fields
        amount = tags.get("54")
        currency_code = tags.get("53")
        currency = (
            "USD"
            if currency_code == "840"
            else "KHR" if currency_code == "116" else currency_code
        )

        # Parse Account Info (Tag 29)
        # Bakong standard can store the account ID in tag 00 or 01
        account_info_raw = tags.get("29", "")
        bakong_account = None
        if account_info_raw:
            acc_parser = EMVParser(account_info_raw)
            bakong_account = acc_parser.get("01") or acc_parser.get("00")

        # Parse Additional Data (Tag 62)
        store_label = None
        terminal_label = None
        additional_data_raw = tags.get("62", "")
        if additional_data_raw:
            add_parser = EMVParser(additional_data_raw)
            # 03 is Store Label, 07 is Terminal Label, 01 is Bill Number
            store_label = add_parser.get("03") or add_parser.get("05")
            terminal_label = add_parser.get("07")

        return {
            "qr_string": qr_string,
            "bakong_account": bakong_account,
            "merchant_name": tags.get("59"),
            "merchant_city": tags.get("60"),
            "amount": float(amount) if amount else None,
            "currency": currency,
            "store_label": store_label,
            "terminal_label": terminal_label,
            "country_code": tags.get("58"),
            "raw_tags": tags,
        }

    async def verify_transaction(self, md5: str) -> dict[str, str]:
        """
        Verify transaction status using Bakong API.
        """
        if not settings.BAKONG_TOKEN:
            return {
                "status": "error",
                "message": "Bakong Developer Token is missing. API features are disabled.",
            }

        try:
            status = self.khqr.check_payment(md5)
            return {"status": status}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_KhqrCode(self, transaction: Transaction) -> KHQRGenerateResponse:
        return KHQRGenerateResponse(
            tran_id=transaction.tran_id,
            qr_string="",
            md5="",
            qr_image_url=f"/static/qr_codes/{transaction.tran_id}.png",
        )


khqr_service = KHQRService()
