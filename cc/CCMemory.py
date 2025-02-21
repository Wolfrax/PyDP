from CCError import CCError
import struct

class Memory:
    def __init__(self):
        self.memory = bytearray(0)

        # Memory struture is mapped to PDP 11/40 architecture
        self.byte_order = '<'  # little endian, see https://docs.python.org/3/library/struct.html
        self.mem_format = {
            'int':    self.byte_order + 'h',   # short, 2 bytes
            'char':   self.byte_order + 'c',   # char,  1 byte
            'float':  self.byte_order + 'e',   # float, 2 bytes
            'double': self.byte_order + 'f'    # float, 4 bytes
        }
        self.chr_enc = 'ascii'

        self.sp = 0
        self.counters = {'read': 0, 'write': 0}

    def write(self, value, double=False, byte=False):
        if not byte and self.sp % 2 != 0:  # write on even memory boundary
            self.sp += 1
            self.memory.extend(bytes(1))

        pos = self.sp

        if isinstance(value, str):
            if len(value) > 1:
                for ch in value:
                    self.write(ch, byte=True)
                return pos
            else:
                ba = bytearray(struct.pack(self.mem_format['char'], value.encode(self.chr_enc)))
        elif isinstance(value, float):
            ba = bytearray(struct.pack(self.mem_format['double' if double else 'float'],value))
        elif isinstance(value, int):
            ba = bytearray(struct.pack(self.mem_format['int'], value))
        else:
            raise CCError(f"Memory write: unknown type ({type(value)})")

        self.memory.extend(ba)
        self.sp += len(ba)
        self.counters['write'] += len(ba)

        return pos

    def read(self, pos, type, double=False):
        self.counters['read'] += 1

        if type == str:
            return struct.unpack_from(self.mem_format['char'], bytes(self.memory), pos)[0].decode(self.chr_enc)
        elif type == float:
            return struct.unpack_from(self.mem_format['double' if double else 'float'], bytes(self.memory), pos)[0]
        elif type == int:
            return struct.unpack_from(self.mem_format['int'], bytes(self.memory), pos)[0]
        else:
            raise CCError(f"Memory read: unknown type ({type})")

    def get_counters(self):
        return self.counters['read'], self.counters['write']

if __name__ == "__main__":
    # test memory write/read

    memory = Memory()

    pos = memory.write(12345)
    print(f'{memory.read(pos, int)} [{pos}]')

    pos = memory.write(5.1)
    print(f'{memory.read(pos, float)} [{pos}]')
    pos = memory.write(3.14, double=True)
    print(f'{memory.read(pos, float, double=True)} [{pos}]')

    pos = memory.write('a')
    print(f'{memory.read(pos, str)} [{pos}]')
    pos = memory.write('def')
    for i in range(len('def')):
        print(f'{memory.read(pos, str)} [{pos}]')
        pos += 1

    print(memory.counters)