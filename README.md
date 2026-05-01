# Payment Microservice

A FastAPI-based microservice for handling payments. Currently supports **ABA PayWay Deep Link**.

## Features
- **ABA PayWay Integration**: Specifically designed for Deep Link payments.
- **FastAPI**: High performance, easy to document (Swagger/Redoc).
- **Plug-and-Play**: Can be called from any other backend (Node.js, Go, Python, etc.) via REST API.
- **Environment Driven**: Configurable via `.env`.

## Setup

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure environment**:
    Edit `.env` and provide your ABA PayWay credentials:
    - `ABA_PAYWAY_MERCHANT_ID`
    - `ABA_PAYWAY_API_KEY`

3.  **Run the service**:
    ```bash
    uvicorn app.main:app --reload
    ```

## API Usage

### Create ABA Deep Link
**Endpoint**: `POST /api/v1/aba/create-deeplink`

**Request Body**:
```json
{
  "tran_id": "ORD-123456",
  "amount": 10.50,
  "currency": "USD",
  "firstname": "John",
  "lastname": "Doe",
  "email": "john@example.com",
  "items": [
    {"name": "Item 1", "quantity": 1, "price": 10.50}
  ]
}
```

**Response**:
```json
{
  "status": 0,
  "description": "Success",
  "qr_code": "...",
  "abapay_deeplink": "abapay://...",
  "app_deeplink": "https://link.ababank.com/..."
}
```

## Integration with other Backends

Since this is a microservice, your other backend (e.g., a Rental Management System) can simply make an HTTP POST request to this service's `create-deeplink` endpoint when a user wants to pay.

Example in Node.js (Axios):
```javascript
const response = await axios.post('http://payment-service:8000/api/v1/aba/create-deeplink', {
    tran_id: order.id,
    amount: order.total,
    // ... other fields
});
const deeplink = response.data.abapay_deeplink;
// Send deeplink to your Mobile App
```

## ABA Sandbox
- Documentation: [https://developer.payway.com.kh/](https://developer.payway.com.kh/)
- Sandbox Transactions: [https://sandbox.payway.com.kh/transactions](https://sandbox.payway.com.kh/transactions)
