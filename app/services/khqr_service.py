import qrcode
import io
import base64
import cv2
import numpy as np
from bakong_khqr import KHQR
from bakong_khqr.sdk.emv_parser import EMVParser
from app.core.config import settings
from app.schemas.payment import KHQRGenerateRequest, KHQRDecodeResponse

class KHQRGenerator:
    @staticmethod
    def format_tag(tag: str, value: str) -> str:
        return f"{tag}{len(value):02}{value}"

    @staticmethod
    def generate(
        bank_account: str,
        merchant_name: str,
        merchant_city: str = "Phnom Penh",
        amount: float = None,
        currency: str = "USD",
        store_label: str = None,
        terminal_label: str = None,
        bill_number: str = None
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
                amt_str = f"{amount:.2f}".rstrip('0').rstrip('.')
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
        if poi == "12": # Dynamic
            # Expire in 30 days (Bakong standard default)
            exp_ms = str(int(time.time() * 1000) + (30 * 86400 * 1000))
            tag99_value += KHQRGenerator.format_tag("01", exp_ms)
            
        payload += KHQRGenerator.format_tag("99", tag99_value)
            
        # 63: CRC (Uppercase is safer for some apps)
        payload += "6304"
        payload += KHQRGenerator.crc16_ccitt(payload).upper()
        
        return payload

    @staticmethod
    def crc16_ccitt(data: str) -> str:
        crc = 0xFFFF
        for byte in data.encode('ascii'):
            crc ^= (byte << 8)
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

from PIL import Image, ImageDraw, ImageFont, ImageOps

class KHQRTemplateGenerator:
    @staticmethod
    def generate_poster(qr_string: str, merchant_name: str, bank_name: str = "ABA Bank") -> bytes:
        # 1. Setup Canvas
        width, height = 800, 1100
        canvas = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(canvas)
        
        # 2. Draw Decorative Elements
        # Red Header Bar
        draw.rectangle([0, 0, width, 30], fill="#D3403D")
        # Red Footer Bar
        draw.rectangle([0, height-30, width, height], fill="#D3403D")
        
        # Bottom-right red accent shape (simplified)
        draw.chord([width-300, height-300, width+100, height+100], 0, 360, fill="#D3403D")
        draw.chord([width-250, height-250, width+150, height+150], 0, 360, fill="white")
        draw.chord([width-200, height-200, width+200, height+200], 0, 360, fill="#D3403D")
        
        # 3. Text Elements
        try:
            # Use a bold font if available, else fallback
            font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            title_font = ImageFont.truetype(font_path, 80)
            subtitle_font = ImageFont.truetype(font_path, 40)
            footer_font = ImageFont.truetype(font_path, 30)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
            
        # Bank Logo Text
        draw.text((width//2, 150), bank_name.upper(), fill="#D3403D", font=title_font, anchor="mm")
        
        # "Scan. Pay. Done."
        draw.text((width//2, 280), "Scan. Pay. Done.", fill="#333333", font=subtitle_font, anchor="mm")
        
        # 4. QR Code Section
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=15,
            border=2,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((500, 500), Image.Resampling.LANCZOS)
        
        # Draw QR Frame (the brackets)
        frame_size = 540
        fx, fy = (width-frame_size)//2, 400
        draw.rectangle([fx, fy, fx+frame_size, fy+frame_size], outline="white", width=2)
        
        # Corner Brackets
        bl = 60 # bracket length
        bw = 8  # bracket width
        # Top Left
        draw.line([fx, fy+bl, fx, fy, fx+bl, fy], fill="#CCCCCC", width=bw)
        # Top Right
        draw.line([fx+frame_size-bl, fy, fx+frame_size, fy, fx+frame_size, fy+bl], fill="#CCCCCC", width=bw)
        # Bottom Left
        draw.line([fx, fy+frame_size-bl, fx, fy+frame_size, fx+bl, fy+frame_size], fill="#CCCCCC", width=bw)
        # Bottom Right
        draw.line([fx+frame_size-bl, fy+frame_size, fx+frame_size, fy+frame_size, fx+frame_size, fy+frame_size-bl], fill="#CCCCCC", width=bw)
        
        # Paste QR
        canvas.paste(qr_img, (width//2 - 250, fy + 20))
        
        # 5. Footer Branding
        draw.text((100, height-150), "Member of", fill="#999999", font=footer_font)
        draw.text((100, height-110), "KHQR", fill="#D3403D", font=title_font)
        
        # 6. Save and Return
        img_byte_arr = io.BytesIO()
        canvas.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

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
            merchant_name=request.merchant_name,
            merchant_city=request.merchant_city,
            amount=request.amount,
            currency=request.currency,
            store_label=request.store_label,
            terminal_label=request.terminal_label
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
                    appName=request.merchant_name or "Merchant"
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
            "tran_id": request.tran_id
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
        currency = "USD" if currency_code == "840" else "KHR" if currency_code == "116" else currency_code
        
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
            "raw_tags": tags
        }

    async def verify_transaction(self, md5: str):
        """
        Verify transaction status using Bakong API.
        """
        if not settings.BAKONG_TOKEN:
            return {"status": "error", "message": "Bakong Developer Token is missing. API features are disabled."}
            
        try:
            return self.khqr.check_payment(md5)
        except Exception as e:
            return {"status": "error", "message": str(e)}

khqr_service = KHQRService()
