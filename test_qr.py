from bakong_khqr import KHQR

khqr = KHQR()
qr = khqr.create_qr(
    bank_account="006992218@aba",
    merchant_name="SOK KHORN KHY",
    merchant_city="Phnom Penh",
    amount=5000,
    currency="KHR"
)
print(f"Generated QR: {qr}")
