def crc16(data: str) -> str:
    crc = 0xFFFF
    for byte in data.encode('ascii'):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"

data = "00020101021229170013006992218@aba520459995303116540450005802KH5913SOK KHORN KHY6010Phnom Penh993400131777636615220011317777230152206304"
print(f"Calculated CRC: {crc16(data)}")
