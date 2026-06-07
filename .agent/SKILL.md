---
name: khqr-payment-compatibility
description: >-
  Troubleshoot, validate, and generate Bakong KHQR codes with ABA Bank and other bank app compatibility. Handles EMV specifications, proprietary Tag 40 configurations, and Merchant Category Code (Tag 52) adjustments to prevent scan/payment errors.
---

# KHQR Payment Compatibility & Troubleshooting Skill

This skill documents how to correctly generate, validate, and troubleshoot Bakong KHQR codes within the rental payment microservice, ensuring compatibility with mobile banking apps (particularly the ABA Mobile App).

---

## 1. Key EMV Co. / KHQR Tag Configurations

### A. Merchant Account Information (Tag 29)

Tag 29 contains sub-tags mapping the bank's Acquirer ID/BIC, the account number, and the bank name:

* **Sub-tag 00**: Acquirer Bank BIC / AID (e.g., `abaakhppxxx@abaa` for ABA, `wingkhppxxx@wing` for Wing, `aclbkhppxxx@aclb` for ACLEDA)
* **Sub-tag 01**: Merchant Account ID / Account Number (e.g., `000269355`)
* **Sub-tag 02**: Merchant Name / Bank Name (e.g., `ABA Bank`)

> [!NOTE]
> For individual/personal accounts (e.g., alphanumeric username like `username@aba`), Tag 29 must only contain a single sub-tag `00` holding the full Bakong account ID (e.g. `29170017username@aba`).

### B. ABA Proprietary Tag (Tag 40)

To ensure that generated KHQR codes scan successfully inside the **ABA Mobile App** without throwing `"Invalid QR merchant data"` errors, Tag 40 must be appended when generating for ABA Bank:

* **Sub-tag 00**: `"abaP2P"`
* **Sub-tag 01**: `"849616A9B2D0"`
* **Sub-tag 02**: Account ID / Number (e.g., `000269355`)

### C. Merchant Category Code (Tag 52)

* Must be formatted as `52040000` (value `"0000"`).
* If set to `"5999"` or other category codes, the ABA mobile application might fail to identify the transaction type for P2P/merchant transfers.

### D. Currency (Tag 53) and Amount (Tag 54)

* **USD (Code 840)**: The amount must be formatted with a maximum of 2 decimal places, stripping trailing zeros where appropriate (e.g., `0.01` or `1.5` or `10`).
* **KHR (Code 116)**: The amount must be rounded to an integer (no decimals).

### E. Timestamp (Tag 99)

* **Sub-tag 00**: Creation timestamp in milliseconds.
* **Sub-tag 01**: Expiration timestamp in milliseconds (mandatory for dynamic QR codes).

### F. CRC Checksum (Tag 63)

* Must be calculated using CRC16-CCITT on the payload prefix + `"6304"`, and formatted in uppercase (4 hex digits).

---

## 2. Bank Mappings Reference

| Bank Name | Domain | Mapped Acquirer AID (Tag 29 Sub-tag 00) |
| :--- | :--- | :--- |
| **ABA Bank** | `aba`, `abaa` | `abaakhppxxx@abaa` |
| **Wing Bank** | `wing` | `wingkhppxxx@wing` |
| **ACLEDA Bank** | `acleda`, `aclb` | `aclbkhppxxx@aclb` |
| **Canadia Bank** | `canadia`, `cadi` | `cadikhppxxx@cadi` |
| **Sathapana Bank** | `sathapana`, `spb` | `spbkhppxxx@spb` |
| **Bakong** | `bakong` | `khqr@bakong` |

---

## 3. Code Implementation Guide

### A. Code Generation Pattern

Use the built-in generator inside `app/services/khqr_service.py` ([KHQRGenerator](file:///Users/sokhorn/Sokhorn/Project/Rental/payment/app/services/khqr_service.py#L23)):

```python
from app.services.khqr_service import KHQRGenerator

qr_payload = KHQRGenerator.generate(
    bank_account="000269355@aba",
    merchant_name="KHY SOK KHORN",
    amount=0.01,
    expire_minutes=1440, # 24 Hours
    currency="USD",
    merchant_city="Phnom Penh"
)
```

### B. Validation & Decoding QR String

To decode and verify a generated QR string or image, use the `decode` API or invoke [KHQRService.decode_from_string](file:///Users/sokhorn/Sokhorn/Project/Rental/payment/app/services/khqr_service.py#L240):

```python
from app.services.khqr_service import khqr_service

decoded_info = khqr_service.decode_from_string(qr_payload)
print(f"Decoded Bank Account: {decoded_info['bakong_account']}")
print(f"Raw EMV Tags: {decoded_info['raw_tags']}")
```

---

## 4. Troubleshooting Checklist

* **Error: "Invalid QR merchant data" (ABA App)**
  1. Verify Tag 40 is included and conforms to the structure: `0006abaP2P0112849616A9B2D00209[AccountNo]`.
  2. Verify Tag 52 is set to `"0000"` (`52040000`).
  3. Ensure Tag 63 checksum is fully upper-cased.
* **Error: "Bank Not Found" / "Account Not Found"**
  1. Ensure that the bank domain suffix is normalized correctly (e.g., `@aba` $\rightarrow$ `@abaa`).
  2. For numeric bank account IDs, make sure they are parsed correctly without alphabetic letters.
* **Error: Scanning failure on iOS/Android**
  1. Ensure the generated QR code image incorporates proper border padding and contrast.
  2. Test decoding using the API endpoint `/api/v1/khqr/decode` to confirm the QR parser recognizes all tags.
