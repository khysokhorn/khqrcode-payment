# Claude's KHQR Payment Guide & Troubleshooting

This document explains the KHQR code structure used in this project, details the bank compatibility issues (specifically for ABA Bank), and provides guidance on how to generate and verify valid KHQR codes.

---

## 1. KHQR Tag 29 vs. Tag 30 Structures

The Bakong KHQR standard distinguishes between **Individual/Solo Merchant** accounts and **Corporate Merchant** accounts by using different EMV tags.

### A. Individual / Solo Merchant Format (Tag 29)

Used for personal/individual accounts (e.g. `sokhorn_chea@abaa`). Tag 29 must contain **only** a single sub-tag `00` that holds the full Bakong account ID:

- **Sub-tag 00**: Full Bakong account ID (e.g. `sokhorn_chea@abaa`)
- **Example Tag 29 Payload**: `29170017sokhorn_chea@abaa`

### B. Corporate Merchant Format (Tag 30)

Used for bank account numbers (e.g. `000269355@abaa`). Tag 30 contains sub-tags mapping the bank's Acquirer AID, the account number, and the bank name:

- **Sub-tag 00**: Acquirer Bank BIC / AID (e.g. `abaakhppxxx@abaa` for ABA)
- **Sub-tag 01**: Merchant Account Number / ID (e.g. `000269355`)
- **Sub-tag 02**: Merchant Name / Bank Name (e.g. `ABA Bank`)
- **Example Tag 30 Payload**: `30450016abaakhppxxx@abaa01090002693550208ABA Bank`

---

## 2. Dynamic Tag Selection & Normalization

The server dynamically detects whether to generate **Tag 29** or **Tag 30**:

1. **Normalizes** the bank domain suffix (e.g., mapping `@aba` $\rightarrow$ `@abaa`).
2. Checks if the account ID (before `@`) is **purely numeric** and **9-10 digits long** (representing a merchant bank account number like `000269355`).
3. If it's numeric, it uses **Tag 30 (Corporate Merchant)** with the mapped bank AID, preventing `"account not found"` errors.
4. If it's alphanumeric (like `sokhorn_chea`) or a phone number, it uses **Tag 29 (Solo/Individual)**.

---

## 3. Troubleshooting ABA App Errors

### Error 1: "Invalid QR merchant data aba"

- **Cause**: This happens when scanning a Merchant QR where the data inside Tag 30 (such as the acquirer bank BIC or merchant account structure) is malformed, has incorrect lengths, or has mismatched checksums (CRC16).

- **Fix**: Ensure that the lengths of sub-tags are formatted exactly to 2 digits (e.g., `len("ABA Bank")` is 8, so it must be formatted as `0208ABA Bank`).

### Error 2: "Bank Not Found" / "Account Not Found"

- **Cause**: This happens when the scanned QR points to an invalid account ID or if a merchant account number was generated as an Individual QR (Tag 29) instead of a Merchant QR (Tag 30).

- **Fix**: Make sure you use Tag 30 for numeric bank accounts.
  
  > [!NOTE]
  > The server now automatically normalizes the input account domain for popular banks (e.g., mapping `@aba` -> `@abaa`) and automatically routes numeric accounts to Tag 30 to prevent this error.

---

## 4. Verification Script

You can verify and parse any generated KHQR string using the `claude_test.py` script:

```bash
python3 claude_test.py
```

This will print the exact tags and sub-tags parsed from the QR code, allowing you to ensure the EMV compliance before scanning it.
