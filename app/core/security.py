import hmac
import hashlib
import base64

def generate_aba_hash(api_key: str, data: str) -> str:
    """
    Generates ABA PayWay hash. Treats the api_key as a plain text string.
    """
    key_bytes = api_key.encode('utf-8')
        
    signature = hmac.new(
        key_bytes,
        data.encode('utf-8'),
        hashlib.sha512
    ).digest()
    return base64.b64encode(signature).decode('utf-8')
