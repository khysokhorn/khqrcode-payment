import time
import json
import base64
import httpx
from app.core.config import settings
from app.core.security import generate_aba_hash
from app.schemas.payment import ABAOrderCreate

class ABAPayWayService:
    def __init__(self):
        self.merchant_id = settings.ABA_PAYWAY_MERCHANT_ID
        self.api_key = settings.ABA_PAYWAY_API_KEY
        self.purchase_url = settings.ABA_PAYWAY_API_URL
        # Derive check transaction URL from purchase URL if possible, otherwise use standard
        self.check_url = self.purchase_url.replace("/purchase", "/check-transaction")

    def create_checkout_request(self, order: ABAOrderCreate):
        req_time = time.strftime("%Y%m%d%H%M%S")
        
        # Serialize items if present
        items_base64 = ""
        if order.items:
            items_list = [{"name": item.name, "quantity": str(item.quantity), "price": f"{item.price:.2f}"} for item in order.items]
            items_json = json.dumps(items_list)
            items_base64 = base64.b64encode(items_json.encode('utf-8')).decode('utf-8')

        amount_str = f"{order.amount:.2f}"
        payment_option = "abapay_deeplink"
        return_url = order.return_url or settings.ABA_PAYWAY_RETURN_URL
        continue_success_url = order.continue_success_url or settings.ABA_PAYWAY_CONTINUE_SUCCESS_URL
        transaction_type = "purchase"
        
        # Optional fields must be empty strings for the hash
        shipping = ""
        tax = ""
        cancel_url = ""
        custom_fields = ""
        top_up_option = ""

        # Hash data construction - Full 15 Fields in Strict Order
        hash_data = (
            req_time + 
            self.merchant_id + 
            order.tran_id + 
            amount_str + 
            items_base64 + 
            shipping + 
            tax + 
            transaction_type + 
            payment_option + 
            return_url + 
            cancel_url + 
            continue_success_url + 
            order.currency + 
            custom_fields + 
            top_up_option
        )
        
        hash_value = generate_aba_hash(self.api_key, hash_data)
        
        return {
            "req_time": req_time,
            "merchant_id": self.merchant_id,
            "tran_id": order.tran_id,
            "amount": amount_str,
            "items": items_base64,
            "shipping": shipping,
            "tax": tax,
            "type": transaction_type,
            "payment_option": payment_option,
            "return_url": return_url,
            "cancel_url": cancel_url,
            "continue_success_url": continue_success_url,
            "currency": order.currency,
            "custom_fields": custom_fields,
            "top_up_option": top_up_option,
            "hash": hash_value,
            "firstname": order.firstname or "Guest",
            "lastname": order.lastname or "User",
            "email": order.email or "guest@example.com",
            "phone": order.phone or "012345678"
        }

    async def initiate_payment(self, order: ABAOrderCreate):
        payload = self.create_checkout_request(order)
        async with httpx.AsyncClient() as client:
            response = await client.post(self.purchase_url, data=payload, timeout=30.0)
            return response.json()

    async def check_transaction(self, tran_id: str):
        req_time = time.strftime("%Y%m%d%H%M%S")
        hash_data = req_time + self.merchant_id + tran_id
        hash_value = generate_aba_hash(self.api_key, hash_data)
        
        payload = {
            "req_time": req_time,
            "merchant_id": self.merchant_id,
            "tran_id": tran_id,
            "hash": hash_value
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.check_url, data=payload, timeout=30.0)
            return response.json()

aba_service = ABAPayWayService()
