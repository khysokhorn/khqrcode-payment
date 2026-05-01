import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.services.aba_service import aba_service
from app.schemas.payment import ABAOrderCreate

import asyncio
from app.services.aba_service import aba_service
from app.schemas.payment import ABAOrderCreate
import uuid

async def test_real_aba_call():
    # Use a unique transaction ID each time
    unique_id = f"ORDER-{uuid.uuid4().hex[:8]}"
    
    order = ABAOrderCreate(
        tran_id=unique_id,
        amount=1.00,
        currency="USD",
        firstname="Sokhorn",
        lastname="Dev",
        email="sokhorn@example.com"
    )
    
    print(f"--- Sending Payment Request to ABA Sandbox ---")
    print(f"Transaction ID: {unique_id}")
    
    try:
        result = await aba_service.initiate_payment(order)
        print("\n--- Response from ABA PayWay ---")
        import json
        print(json.dumps(result, indent=2))
        
        if "abapay_deeplink" in result:
            print("\n✅ SUCCESS!")
            print(f"Deep Link: {result['abapay_deeplink']}")
        else:
            print("\n❌ FAILED or No Deep Link returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_aba_call())
