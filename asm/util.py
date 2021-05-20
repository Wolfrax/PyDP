def to_2_compl(val, byte=True):
    if byte:
        return val

    bits = 8 if byte else 16
    return val if val >= 0 else (1 << bits) + val


def from_2_compl(val, byte=True):
    if byte:
        return val

    bits = 8 if byte else 16
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def to_byte(val):
    return -(abs(val) & 0xFF) if val < 0 else val & 0xFF


def xor(a, b):
    return (a or b) and not (a and b)
