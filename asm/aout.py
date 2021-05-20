import asm.aout


class InstrLUT:
    def __init__(self):
        Op = {}

        self.Masks = {
            0o170000: [
                0o110000, 0o010000,   # MOVB, MOV
                0o120000, 0o020000,   # CMPB, CMP
                0o130000, 0o030000,   # BITB, BIT
                0o140000, 0o040000,   # BICB, BIC
                0o150000, 0o050000,   # BISB, BIS
                          0o060000,   # ADD
                0o160000              # SUB
            ],

            0o177000: [
                          0o004000,   # JSR
                          0o070000,   # MUL
                          0o071000,   # DIV
                          0o072000,   # ASH
                          0o073000,   # ASHC
                          0o074000,   # XOR
                          0o077000    # SOB
            ],

            0o177700: [
                0o105000, 0o005000,   # CLRB, CLR
                0o105100, 0o005100,   # COMB, COM
                0o105200, 0o005200,   # INCB, INC
                0o105300, 0o005300,   # DECB, DEC
                0o105400, 0o005400,   # NEGB, NEG
                0o105500, 0o005500,   # ADCB, ADC
                0o005600, 0o005600,   # SBCB, SBC
                0o105700, 0o005700,   # TSTB, TST
                0o106000, 0o006000,   # RORB, ROR
                0o106100, 0o006100,   # ROLB, ROL
                0o106200, 0o006200,   # ASRB, ASR
                0o106300, 0o006300,   # ASLB, ASL
                          0o006700,   # SXT
                          0o000100,   # JMP
                          0o000300,   # SWAB
                          0o006400,   # MARK
                          0o006500,   # MFPI
                          0o006600    # MTPI
            ],

            0o177770: [
                          0o000200    # RTS
            ],

            0o177400: [
                          0o000400,   # BR
                          0o001000,   # BNE
                          0o001400,   # BEQ
                          0o002000,   # BGE
                          0o002400,   # BLT
                          0o003000,   # BGT
                          0o003400,   # BLE
                0o100000,             # BPL
                0o100400,             # BMI
                0o101000,             # BHI
                0o101400,             # BLOS
                0o102000,             # BVC
                0o102400,             # BVS
                0o103000,             # BCC
                0o103400,             # BCS
                0o104400              # SYS/TRAP
            ],

            0o000277: [
                          0o000240,   # NOP
                          0o000241,   # CLC
                          0o000242,   # CLV
                          0o000244,   # CLZ
                          0o000250,   # CLN
                          0o000261,   # SEC
                          0o000262,   # SEV
                          0o000264,   # SEZ
                          0o000270,   # SEN
                          0o000277,   # SCC
                          0o000257    # CCC
            ],

            0o000007: [
                          0o000000,   # HALT
                          0o000001,   # WAIT
                          0o000002,   # RTI
                          0o000003,   # BPT
                          0o000004,   # IOT
                          0o000005,   # RESET
                          0o000006,   # RTT
            ]
        }

        self.singleOp = {
            0o105000: 'CLRB',  #
            0o005000: 'CLR',   #
            0o105100: 'COMB',  #
            0o005100: 'COM',   #
            0o105200: 'INCB',  #
            0o005200: 'INC',   #
            0o105300: 'DECB',  #
            0o005300: 'DEC',   #
            0o105400: 'NEGB',  #
            0o005400: 'NEG',   #
            0o105700: 'TSTB',  #
            0o005700: 'TST',   #
            0o106200: 'ASRB',  #
            0o006200: 'ASR',   #
            0o106300: 'ASLB',  #
            0o006300: 'ASL',   #
            0o106000: 'RORB',  #
            0o006000: 'ROR',   #
            0o106100: 'ROLB',  #
            0o006100: 'ROL',   #
            0o000300: 'SWAB',  #
            0o105500: 'ADCB',  #
            0o005500: 'ADC',   #
            0o105600: 'SBCB',  #
            0o005600: 'SBC',   #
            0o006700: 'SXT'    #
        }
        self.test = {}
        for k, v in self.singleOp.items():
            for val in range(k, k + 0o100):
                self.test[val] = v

        Op.update(self.singleOp)

        self.doubleOp = {
            0o110000: 'MOVB',  #
            0o010000: 'MOV',   #
            0o120000: 'CMPB',  #
            0o020000: 'CMP',   #
            0o060000: 'ADD',   #
            0o160000: 'SUB',   #
            0o130000: 'BITB',  #
            0o030000: 'BIT',   #
            0o140000: 'BICB',  #
            0o040000: 'BIC',   #
            0o150000: 'BISB',  #
            0o050000: 'BIS',   #
            0o070000: 'MUL',   #
            0o071000: 'DIV',   #
            0o072000: 'ASH',   #
            0o073000: 'ASHC',  #
            0o074000: 'XOR'    #
        }
        Op.update(self.doubleOp)

        self.prgCntrlOp = {
            0o000400: 'BR',    #
            0o001000: 'BNE',   #
            0o001400: 'BEQ',   #
            0o100000: 'BPL',   #
            0o100400: 'BMI',   #
            0o102000: 'BVC',   #
            0o102400: 'BVS',   #
            0o103000: 'BCC',   # BHIS
            0o103400: 'BCS',   # BLO
            0o002000: 'BGE',   #
            0o002400: 'BLT',   #
            0o003000: 'BGT',   #
            0o003400: 'BLE',   #
            0o101000: 'BHI',   #
            0o101400: 'BLOS',  #
            0o000100: 'JMP',   #
            0o004000: 'JSR',   #
            0o000200: 'RTS',   #
            0o006400: 'MARK',  #
            0o077000: 'SOB',   #
            0o104400: 'SYS',   # TRAP
            0o000003: 'BPT',   #
            0o000004: 'IOT',   #
            0o000002: 'RTI',   #
            0o000006: 'RTT',   #
        }
        Op.update(self.prgCntrlOp)

        self.miscOp = {
            0o000000: 'HALT',  #
            0o000001: 'WAIT',  #
            0o000005: 'RESET', #
            0o006500: 'MFPI',  #
            0o006600: 'MTPI',  #
            0o000241: 'CLC',   #
            0o000242: 'CLV',   #
            0o000244: 'CLZ',   #
            0o000250: 'CLN',   #
            0o000261: 'SEC',   #
            0o000262: 'SEV',   #
            0o000264: 'SEZ',   #
            0o000270: 'SEN',   #
            0o000277: 'SCC',   #
            0o000257: 'CCC',   #
            0o000240: 'NOP'    #
        }
        Op.update(self.miscOp)
        self.Op = dict(sorted(Op.items()))

        self.syscall = {
            0o0000000: 'indir',
            0o0000001: 'exit',
            0o0000002: 'fork',
            0o0000003: 'read',
            0o0000004: 'write',
            0o0000005: 'open',
            0o0000006: 'close',
            0o0000007: 'wait',
            0o0000010: 'creat',
            0o0000011: 'link',
            0o0000012: 'unlink',
            0o0000013: 'exec',
            0o0000014: 'chdir',
            0o0000015: 'time',
            0o0000016: 'makdir',  # mknod
            0o0000017: 'chmod',
            0o0000020: 'chown',
            0o0000021: 'break',
            0o0000022: 'stat',
            0o0000023: 'seek',
            0o0000024: 'tell',    # getpid
            0o0000025: 'mount',
            0o0000026: 'umount',
            0o0000027: 'setuid',
            0o0000030: 'getuid',
            0o0000031: 'stime',
            0o0000034: 'fstat',
            0o0000036: 'mdate',   # ??, not documented
            0o0000037: 'stty',
            0o0000040: 'gtty',
            0o0000042: 'nice',
            0o0000060: 'signal'
        }

    def isSingleOp(self, op):
        return op in self.singleOp.values()

    def isDoubleOp(self, op):
        return op in self.doubleOp.values()

    def isPrgCntrlOp(self, op):
        return op in self.prgCntrlOp.values()

    def isMiscOp(self, op):
        return op in self.miscOp.values()

    def get(self, word):
        for mask, ops in self.Masks.items():
            bits = word & mask
            if bits in ops:
                return self.Op[bits]

#        for mask in self.Masks:
#            ind = word & mask
#            if ind != 0 and ind in self.Op:
#                return self.Op[ind]

#        if word in self.Op:
#            return self.Op[word]

        return None
        #return self.Op[max([i for i in self.Op if i <= word])]

    def get_syscall(self, word):
        return self.syscall[word]


class Head:
    def __init__(self, data):
        # Header in a.out format is 8 words/16 bytes at the start of the file.
        # Each word as specified below

        self.size = len(data)  # bytes
        header = [(data[i + 1] << 8) | data[i] for i in range(0, self.size, 2)]

        self.magic = header[0]
        self.txt = header[1]
        self.data = header[2]
        self.bss = header[3]
        self.sym = header[4]
        self.entry_loc = header[5]
        self.unused = header[6]
        self.reloc = header[7]

    def dump(self):
        print("magic: {}, text size: {}, data size: {}, bss size: {}, symbol table size: {}, "
              "entry location: {}, unused: {}, relocation flag: {}".format(self.magic,
                                                                           self.txt,
                                                                           self.data,
                                                                           self.bss,
                                                                           self.sym,
                                                                           self.entry_loc,
                                                                           self.unused,
                                                                           self.reloc))


class Symbol:
    def __init__(self, data):
        sym = ''
        for i in range(8):
            ch = data[i]
            if ch != 0:
                sym += chr(ch)
        self.name = sym
        self.type = data[9] << 8 | data[8]
        self.val = data[11] << 8 | data[10]

    def dump(self):
        print("{} (type: {}, val: {})".format(self.name, self.type, self.val))


class SymTable:
    def __init__(self, data):
        self.table = {}

        ind = 0
        while ind < len(data):
            sym = Symbol(data[ind:ind + 12])
            self.table[sym.val] = sym
            ind += 12

    def dump(self):
        for key in self.table:
            self.table[key].dump()

    def find_val(self, val):
        for sym in self.table.values():
            if sym.val == val:
                return sym.name


class SyscallInstr:
    def __init__(self, data):
        self.syscall = instrLUT.get_syscall(((data[1] << 8) | data[0]) & 0o77)
        #self.syscall = instrLUT.get_syscall(((data[1] << 8) | data[0]))

        if self.syscall in ['exit', 'fork', 'close', 'wait', 'time', 'getpid', 'setuid', 'getuid', 'stime', 'fstat',
                            'mdate', 'nice']:
            self.par = []
        elif self.syscall in ['indir', 'unlink', 'chdir', 'break', 'umount', 'stty', 'gtty']:
            self.par = [(data[3] << 8) | data[2]]
        elif self.syscall in ['read', 'write', 'open', 'creat', 'link', 'exec', 'chmod', 'chown', 'stat', 'seek',
                              'signal']:
            self.par = [(data[3] << 8) | data[2], (data[5] << 8) | data[4]]
        elif self.syscall in ['makdir', 'mount']:
            self.par = [(data[3] << 8) | data[2], (data[5] << 8) | data[4], (data[7] << 8) | data[6]]

        self._size = len(self.par) * 2
        if self.syscall == 'gtty':
            self._size += 4

    def size(self):
        return self._size


class Instr:
    def __init__(self, data, pc):
        self.word = (data[1] << 8) | data[0]
        self.pc = pc

        self.op = None

        self.src_index = None
        self.src_mode = None
        self.src_reg = None

        self.dst_index = None
        self.dst_mode = None
        self.dst_reg = None

        self.syscall = None

        self.size = None

        op = instrLUT.get(self.word)
        if op:
            self.op = op
            self.size = 2

            if instrLUT.isSingleOp(op):
                self.dst_mode = (self.word & 0o70) >> 3

                if self._is_index_mode(self.dst_mode):
                    self.dst_index = (data[3] << 8) | data[2]
                self.dst_reg = self.word & 0o7
                self.size += self._size(self.dst_mode, self.dst_reg)
            elif instrLUT.isDoubleOp(op):
                self.src_mode = (self.word & 0o7000) >> 9
                self.src_reg = (self.word & 0o700) >> 6
                self.dst_mode = (self.word & 0o70) >> 3
                self.dst_reg = self.word & 0o7

                if self._is_index_mode(self.src_mode):
                    self.src_index = (data[3] << 8) | data[2]

                if self._is_index_mode(self.dst_mode):
                    self.dst_index = (data[5] << 8) | data[4]

                self.size += (self._size(self.src_mode, self.src_reg) +
                              self._size(self.dst_mode, self.dst_reg))
            elif instrLUT.isPrgCntrlOp(op):
                if op == 'SYS':
                    self.syscall = SyscallInstr(data[0:])
                    self.size += self.syscall.size()
                else:
                    self.dst_mode = (self.word & 0o70) >> 3

                    if self._is_index_mode(self.dst_mode):
                        self.dst_index = (data[3] << 8) | data[2]
                    self.dst_reg = self.word & 0o7
                    self.size += self._size(self.dst_mode, self.dst_reg)
                if op == 'JSR':
                    self.src_reg = (self.word & 0o700) >> 6
                    self.src_mode = 0

    def dump(self):
        if self.op:
            op_src = self._op_str(self.src_reg, self.src_mode, self.src_index)
            op_dst = self._op_str(self.dst_reg, self.dst_mode, self.dst_index)
            if self.syscall is not None:
                syscall = self.syscall.syscall
            else:
                syscall = ""
            return self.op + 2 * "\t" + syscall +"\t" + op_src + "\t" + op_dst

        else:
            return None

    def _op_str(self, reg, mode, index):
        if mode == 0:
            return "R" + str(reg)
        elif mode == 1:
            return "(R" + str(reg) + ")"
        elif mode == 2:
            if reg <= 6:
                return "(R" + str(reg) + ")+"
            else:
                return "$" + str(index)
        elif mode == 3:
            if reg <= 6:
                return "*(R" + str(reg) + ")+"
            else:
                return "*$R" + str(reg)
        elif mode == 4:
            return "-(R" + str(reg) + ")"
        elif mode == 5:
            return "*-(R" + str(reg) + ")"
        elif mode == 6:
            if reg <= 6:
                return str(index) + "(R" + str(reg) + ")"
            else:
                index_name = asm.aout.SymTable.find_val(aout.sym_table, index + self.pc + 4)
                if index_name is not None:
                    return index_name + " (" + str(index + self.pc + 4) + ")"
                else:
                    return str(index + self.pc + 4)

        elif mode == 7:
            if reg <= 6:
                return "*" + str(index) + "(R" + str(reg) + ")"
            else:
                return "*" + str(index + self.pc + 4)
        else:
            return ""

    @staticmethod
    def _size(mode, reg):
        if mode is None or reg is None:
            return 0

        if mode >= 6 and reg <= 6:
            return 2
        elif mode <= 3 and reg == 7:
            return 2
        elif mode >= 6 and reg == 7:
            return 2
        else:
            return 0

    @staticmethod
    def _is_index_mode(mode):
        return mode >= 6


class Text:
    def __init__(self, data):
        self.instr = []
        i = 0
        while i < len(data):
            instr = Instr(data[i:], i)
            if instr.op is not None:
                i += instr.size
                self.instr.append(instr)
            else:
                i += 2

    def dump(self):
        pos = 0
        for instr in self.instr:
            dump_str = instr.dump()
            if dump_str:
                print(str(pos) + ":\t" + dump_str)
            pos += instr.size


class Aout:
    def __init__(self, name):
        self.name = name
        with open(self.name, 'rb') as f:
            self.data = f.read()

        self.head = Head(self.data[0:16])

        self.text = Text(self.data[16:self.head.txt])

        sym_start = self.head.size + (1 if self.head.reloc else 2) * (self.head.txt + self.head.data)
        self.sym_table = SymTable(self.data[sym_start:sym_start + self.head.sym])

    def dump(self):
        self.head.dump()
        self.sym_table.dump()
        self.text.dump()


if __name__ == '__main__':
    instrLUT = InstrLUT()
    aout = Aout('a1.out')
    aout.dump()
