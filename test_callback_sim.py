import requests
import json

def simulate_callback():
    url = "http://127.0.0.1:8000/api/v1/aba/callback"
    
    # This matches the structure ABA usually sends
    payload = {
        "tran_id": "TEST-1234",
        "status": "0", # 0 usually means success in ABA
        "amount": "1.00",
        "currency": "USD",
        "hash": "simulated_hash_for_testing",
        "aprt": "123456" # Approval code
    }
    
    print(f"Sending simulated callback to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
    except Exception as e:
        print(f"Error: {e}. Is your FastAPI server running?")

if __name__ == "__main__":
    simulate_callback()
