# RentPay Microservice

A FastAPI-based microservice for handling payments. Currently supports **ABA PayWay Deep Link**.

## Features

- **ABA PayWay Integration**: Specifically designed for Deep Link payments.
- **FastAPI**: High performance, easy to document (Swagger/Redoc).
- **Plug-and-Play**: Can be called from any other backend (Node.js, Go, Python, etc.) via REST API.
- **Environment Driven**: Configurable via `.env`.

## Setup

1. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

2. **Configure environment**:
    Edit `.env` and provide your ABA PayWay credentials:
    - `ABA_PAYWAY_MERCHANT_ID`
    - `ABA_PAYWAY_API_KEY`

3. **Run the service**:

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

## Public Bakong Open API (`public-bakong`)

Look up transactions through the public Bakong gateway using the new service at
`GET /api/v1/public-bakong/check`. The client uses Python's standard library and
does not require a Bakong developer token or additional dependencies.

Start the existing application with `./run.sh`, then use:

```bash
# Short hash: amount is required; currency defaults to KHR.
curl 'http://localhost:8001/api/v1/public-bakong/check?type=SHORT_HASH&value=bdf5ac24&amount=2000&ccy=KHR'

# Full transaction hash (64 hexadecimal characters).
curl 'http://localhost:8001/api/v1/public-bakong/check?type=HASH&value=YOUR_64_CHARACTER_HASH'

# QR MD5 (32 hexadecimal characters); hash is also accepted as an alias for value.
curl 'http://localhost:8001/api/v1/public-bakong/check?type=MD5&value=YOUR_32_CHARACTER_MD5'

curl 'http://localhost:8001/api/v1/public-bakong/health'
```

`SHORT_HASH` accepts 8 hexadecimal characters, a positive `amount`, and `ccy=KHR`
or `ccy=USD`. `HASH` and `MD5` require only the identifier. Invalid inputs return
HTTP 400. Lookup responses retain the gateway's `txResult` and `txError` fields.
Transaction timestamps also include UTC `createdDateIso` and
`acknowledgedDateIso` fields when available. A successful payment lookup requires
a non-null `txResult` and no `txError`.

Gateway failures use HTTP 200 with `txResult: null` and a structured `txError`:
`-1` for network errors, `-2` for a missing Nuxt payload, and `-3` for decoding
errors. Upstream business errors are preserved. This service reads the gateway's
HTML response, so gateway markup or serialization changes may require updates.
The health endpoint only checks local availability.

This lookup does not update local payment records. The existing
`/api/v1/bakong/check-transaction` flow remains separate. Running the full app
still requires its existing database and `PUBLIC_BAKONG_API` configuration.

Run the client and route tests after installing the project's dependencies:

```bash
python -m unittest discover -s tests -v
```

