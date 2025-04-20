from src.CCError import CCError

import struct

class Memory:
    def __init__(self):
        self.memory = bytearray(0)

        # Memory structure is mapped to PDP 11/40 architecture
        self.byte_order_str = 'little'
        self.byte_order = '<'  # little endian, see https://docs.python.org/3/library/struct.html
        self.mem_format = {
            'int':     self.byte_order + 'h',   # short,  2 bytes
            'long':    self.byte_order + 'l',   # long,   4 bytes
            'byte':    self.byte_order + 'c',   # byte,   1 byte
            'char':    self.byte_order + 'c',   # char,   1 byte
            'float':   self.byte_order + 'f',   # float,  4 bytes
            'double':  self.byte_order + 'd',   # float,  8 bytes
            'pointer': self.byte_order + 'h'    # as int, 2 bytes
        }
        self.sz_of = {
            'int':     struct.calcsize(self.mem_format['int']),
            'long':    struct.calcsize(self.mem_format['long']),
            'byte':    struct.calcsize(self.mem_format['byte']),
            'char':    struct.calcsize(self.mem_format['char']),
            'float':   struct.calcsize(self.mem_format['float']),
            'double':  struct.calcsize(self.mem_format['double']),
            'pointer': struct.calcsize(self.mem_format['int']),
        }

        self.chr_enc = 'ascii'

        self.sp = 0
        self.counters = {'read': 0, 'write': 0}

    def write(self, value, type, byte=False):
        if not byte and self.sp % 2 != 0:  # write on even memory boundary
            self.sp += 1
            self.memory.extend(bytes(1))

        pos = self.sp

        if type == 'char':
            if isinstance(value, int):
                if value > 0xFF:
                    raise CCError(f'Value {value} is out of range')
                ba = bytearray(struct.pack(self.mem_format['int'], value))
            elif len(value) > 1:
                for ch in value:
                    self.write(ch, type, byte=True)
                self.write('\x00', type, byte=True)  # This is null-byte for string
                return pos
            else:
                ba = bytearray(struct.pack(self.mem_format['char'], value.encode()))
        elif type in ['int', 'long', 'float', 'double', 'pointer']:
            if type == 'int' and isinstance(value, str):
                value = ord(value)
            ba = bytearray(struct.pack(self.mem_format[type], value))
        else:
            raise CCError(f"Memory write: unknown type ({type})")

        self.memory.extend(ba)
        self.sp += len(ba)
        self.counters['write'] += len(ba)

        return pos

    def update(self, pos, value, type, byte=False):
        if type == 'char':
            if isinstance(value, int):
                if value > 0xFF:
                    raise CCError(f'Value {value} is out of range')
                ba = bytearray(struct.pack(self.mem_format['char'], value.to_bytes(1, self.byte_order_str)))
            elif len(value) > 1:
                for ch in value:
                    self.update(pos, ch, type, byte=True)  # Note, we don't update null-byte for string, already there
                    pos += 1
                return
            else:
                ba = bytearray(struct.pack(self.mem_format['char'], value.encode()))
        elif type in ['int', 'long', 'float', 'double', 'pointer']:
            if type == 'int' and isinstance(value, str):
                value = ord(value)
            ba = bytearray(struct.pack(self.mem_format[type], value))
        else:
            raise CCError(f"Memory update: unknown type ({type})")

        for ind, b in enumerate(ba):
            self.memory[pos + ind] = b

        self.counters['write'] += len(ba)


    def read(self, pos, type):
        self.counters['read'] += 1

        if type == 'char':
            return struct.unpack_from(self.mem_format['char'], bytes(self.memory), pos)[0].decode(self.chr_enc)
        elif type in ['int', 'long', 'float', 'double', 'pointer']:
            return struct.unpack_from(self.mem_format[type], bytes(self.memory), pos)[0]
        else:
            raise CCError(f"Memory read: unknown type ({type})")

    def read_indirect(self, pos, type):
        self.counters['read'] += 1

        pos = struct.unpack_from(self.mem_format['pointer'], bytes(self.memory), pos)[0]
        return self.read(pos, type)

    def read_string(self, pos):
        self.counters['read'] += 1
        str = ''
        ch = struct.unpack_from(self.mem_format['char'], bytes(self.memory), pos)[0].decode(self.chr_enc)
        while ch != '\x00':
            str += ch
            pos += 1
            ch = struct.unpack_from(self.mem_format['char'], bytes(self.memory), pos)[0].decode(self.chr_enc)
        return str

    def init_mem(self, size=1, type='int'):
        if type != 'char' and self.sp % 2 != 0:  # write on even memory boundary
            self.sp += 1
            self.memory.extend(bytes(1))

        if type in ['byte', 'char', 'int', 'long', 'float', 'double', 'pointer']:
            self.memory.extend(size * bytearray(self.sz_of[type]))
            pos = self.sp
            self.sp += (size * self.sz_of[type])
            return pos
        else:
            raise CCError(f"Memory init: unknown type ({type})")


    def get_counters(self):
        return self.counters['read'], self.counters['write']

if __name__ == "__main__":
    # test memory write/read

    memory = Memory()

    pos = memory.write(12345, 'int')
    print(f"{memory.read(pos, 'int')} [{pos}]")

    pos = memory.write(5.1, 'float')
    print(f"{memory.read(pos, 'float')} [{pos}]")
    pos = memory.write(3.14, 'double')
    print(f"{memory.read(pos, 'double')} [{pos}]")

    pos = memory.write('a', 'char')
    print(f"{memory.read(pos, 'char')} [{pos}]")
    pos = memory.write('def', 'char')
    for i in range(len('def')):
        print(f"{memory.read(pos, 'char')} [{pos}]")
        pos += 1

    print(memory.counters)