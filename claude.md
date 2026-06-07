# Claude's KHQR Payment Guide & Troubleshooting

This document explains the KHQR code structure used in this project, details the bank compatibility issues (specifically for ABA Bank), and provides guidance on how to generate and verify valid KHQR codes.

---

## 1. KHQR Tag 29 (Merchant Account Information) Structure

Tag 29 contains the receiver's account details. The format differs significantly depending on whether the QR is for an **Individual (Personal)** account or a **Merchant** account.

### A. Individual / Personal QR Format
For personal accounts (e.g., `006992218@aba`), Tag 29 must contain only a single sub-tag `00` that holds the full Bakong account ID:
- **Sub-tag 00**: Full Bakong account ID (e.g., `006992218@aba`)
- **Example Tag 29 Payload**: `29170013006992218@aba`

> [!IMPORTANT]
> Do NOT split the username and domain, and do NOT add SWIFT/BIC codes or bank names as sub-tags for personal accounts. Doing so will cause the ABA app to show **"Bank Not Found"** or similar scanning errors.

### B. Merchant QR Format
For merchants, Tag 29 contains sub-tags mapping to the bank's unique identifier and the account ID:
- **Sub-tag 00**: Acquirer Bank BIC / AID (e.g., `abaakhppxxx@abaa` for ABA, `wingkhppxxx@wing` for Wing)
- **Sub-tag 01**: Merchant Account Number / ID (e.g., `006992218`)
- **Sub-tag 02**: Merchant Name / Bank Name (e.g., `ABA Bank`)
- **Example Tag 29 Payload**: `29480016abaakhppxxx@abaa0112sokhorn_chea0208ABA Bank`

---

## 2. Troubleshooting ABA App Errors

### Error 1: "Invalid QR merchant data aba"
* **Cause**: This happens when scanning a Merchant QR where the data inside Tag 29 (such as the acquirer bank BIC or merchant account structure) is malformed, has incorrect lengths, or has mismatched checksums (CRC16).
* **Fix**: Ensure that the lengths of sub-tags are formatted exactly to 2 digits (e.g., `len("ABA Bank")` is 8, so it must be formatted as `0208ABA Bank`).

### Error 2: "Bank Not Found"
* **Cause**: This happens when the scanned QR Tag 29 points to an invalid account ID (like using `@aba` instead of `@abaa` if the bank registered it as `@abaa`), or if you used individual formatting for a merchant account (or vice versa).
* **Fix**: Double-check the bank account domain. For ABA Bank, the Bakong domain identifier is typically `@abaa`.

---

## 3. Verification Script

You can verify and parse any generated KHQR string using the `claude_test.py` script:

```bash
python3 claude_test.py
```

This will print the exact tags and sub-tags parsed from the QR code, allowing you to ensure the EMV compliance before scanning it.
