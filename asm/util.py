def to_2_compl(val, byte=True):
    bits = 8 if byte else 16

    return val if val >= 0 else (1 << bits) + val


def from_2_compl(val, byte=True):
    bits = 8 if byte else 16

    if val < 0:
        return val

    if (val & (1 << (bits - 1))) != 0:  # Test if high-bit (sign) is set
        return val - (1 << bits)
    return val

def to_byte(val):
    return -(abs(val) & 0xFF) if val < 0 else val & 0xFF


def xor(a, b):
    return (a or b) and not (a and b)
