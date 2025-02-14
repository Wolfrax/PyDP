from CC import CCError

class Memory:
    def __init__(self, size):
        self.size = size * 1024
        self.memory = [0] * self.size
        self.sp = 0
        self.counters = {'read': 0, 'write': 0}

    def __len__(self):
        return len(self.memory)

    def init(self, data):
        if len(data) >= self.size:
            raise CCError(f"Initialization of memory out of bound ({len(data)})")
        self.memory[0:len(data)] = data

    def init_slize(self, start_ind, size, data):
        self.memory[start_ind: start_ind + size] = data

    def write(self, pos, value, byte=False):
        if pos < 0 or pos > self.size:
            raise CCError(f"Writing of memory out of bound ({pos})")
        if not isinstance(value, int):
            raise CCError(f"Writing of memory of type {type(value)}")
        """
        Memory is little endian
        >>> (2496065).to_bytes(3, 'little')
        b'A\x16&'
        >>> s
        [65, 22, 38]
        >>> s[2] << 16 | s[1] << 8 | s[0]
        2496065
        """

        self.counters['write'] += 1

        pos = self.sp
        if value <= 0xFF:
            if byte:
                self.memory[self.sp] = value
                self.sp += 1
            else:
                self.memory[self.sp] = value
                self.memory[self.sp + 1] = 0
                self.sp += 2
        else:
            length = 0
            v = value
            while v != 0:
                length += 1
                v >>= 8
            if length % 2 != 0:
                # Pad with 0 to make it even (store on word boundary), most significant byte first (little endian)
                self.memory[self.sp] = 0
                self.sp += 1
                ret_length = length + 1
            else:
                ret_length = length

            value_bytes = value.to_bytes(length, 'little')

            for byte_pos in range(length):
                self.memory[pos] = value_bytes[byte_pos]
                pos += 1

            return ret_length

    def read(self, pos, nr=2):
        if pos < 0 or pos > self.size:
            raise CCError(f"Reading of memory out of bound ({pos})")

        self.counters['read'] += 1

        ret_val = 0
        for i in range(nr - 1, -1, -1):
            mem_val = self.memory[pos + i]
            ret_val = ret_val << 8 | mem_val

        return ret_val

    def get_counters(self):
        return self.counters['read'], self.counters['write']

class CCinterpreter:
    def __init__(self):
        self.memory = Memory(64)
