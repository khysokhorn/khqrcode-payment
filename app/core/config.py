import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ABA_PAYWAY_MERCHANT_ID = os.getenv("ABA_PAYWAY_MERCHANT_ID", "sandbox_merchant")
    ABA_PAYWAY_API_KEY = os.getenv("ABA_PAYWAY_API_KEY", "sandbox_key")
    ABA_PAYWAY_API_URL = os.getenv(
        "ABA_PAYWAY_API_URL",
        "https://sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase",
    )
    ABA_PAYWAY_RETURN_URL = os.getenv(
        "ABA_PAYWAY_RETURN_URL", "http://localhost:8000/api/v1/payment/callback"
    )
    ABA_PAYWAY_CONTINUE_SUCCESS_URL = os.getenv(
        "ABA_PAYWAY_CONTINUE_SUCCESS_URL", "http://localhost:3000/success"
    )

    # Bakong / KHQR Settings
    BAKONG_ACCOUNT_ID = os.getenv("BAKONG_ACCOUNT_ID", "your_bakong_id@aba")
    BAKONG_TOKEN = os.getenv("BAKONG_TOKEN", "")  # Optional developer token


settings = Settings()
