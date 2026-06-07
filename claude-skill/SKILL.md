---
name: claude-skill
description: >-
  Helper skill to troubleshoot, validate, and generate Bakong KHQR codes in the rental payment microservice. Helps ensure correct EMV Tag 29 account structures for ABA and other banks to prevent scanning errors.
---

# KHQR Payment Generator & Troubleshooting Skill

## Overview
This skill guides the developer or agent on how to correctly generate, parse, and troubleshoot Bakong KHQR codes within this project. It ensures that Tag 29 (Merchant Account Information) is formatted correctly depending on the bank and account type.

## Quick Start

### 1. Generating Individual QR Code
To generate a valid individual KHQR code, use the standard `khqr` library instance in Python:
```python
from bakong_khqr import KHQR

khqr = KHQR()
qr_string = khqr.create_qr(
    bank_account="006992218@aba",
    merchant_name="SOK KHORN KHY",
    merchant_city="Phnom Penh",
    amount=0.10,
    currency="USD",
    static=False,
    expiration=10
)
```

### 2. Checking Generated QR Tags
You can verify the generated QR code using the local verification script:
```bash
python3 claude_test.py
```

## Utility Scripts

### `claude_test.py`
A local Python script in the root directory that generates a test QR code string and parses all its EMV tags to confirm correct structure. Run it with:
```bash
python3 claude_test.py
```

## Common Mistakes & Troubleshooting

* **Wrong Tag 29 Sub-tags for Personal Accounts**: Adding SWIFT/BIC codes or splitting the account username and domain for personal accounts will cause **"Bank Not Found"** errors in mobile banking apps. For personal accounts, Tag 29 must only contain sub-tag `00` with the full account ID (e.g. `006992218@aba`).
* **Incorrect KHR Formatting**: For KHR currency, the transaction amount (Tag 54) must be rounded to an integer (no decimals). For USD, it can have up to 2 decimal places.
* **Mismatched CRC16**: Modifying the QR payload manually without recalculating the CRC16 checksum at the end (Tag 63) will make the QR code invalid. Always recalculate CRC16 using `KHQRGenerator.crc16_ccitt(payload).upper()`.
