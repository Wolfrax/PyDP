from enum import IntEnum
import argparse
import sys
import asm
import as_stmt
import as_expr


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
            0o105000: 'clrb',  #
            0o005000: 'clr',   #
            0o105100: 'comb',  #
            0o005100: 'com',   #
            0o105200: 'incb',  #
            0o005200: 'inc',   #
            0o105300: 'decb',  #
            0o005300: 'dec',   #
            0o105400: 'negb',  #
            0o005400: 'neg',   #
            0o105700: 'tstb',  #
            0o005700: 'tst',   #
            0o106200: 'asrb',  #
            0o006200: 'asr',   #
            0o106300: 'aslb',  #
            0o006300: 'asl',   #
            0o106000: 'rorb',  #
            0o006000: 'ror',   #
            0o106100: 'rolb',  #
            0o006100: 'rol',   #
            0o000300: 'swab',  #
            0o105500: 'adcb',  #
            0o005500: 'adc',   #
            0o105600: 'sbcb',  #
            0o005600: 'sbc',   #
            0o006700: 'sxt'    #
        }

        Op.update(self.singleOp)

        self.doubleOp = {
            0o110000: 'movb',  #
            0o010000: 'mov',   #
            0o120000: 'cmpb',  #
            0o020000: 'cmp',   #
            0o060000: 'add',   #
            0o160000: 'sub',   #
            0o130000: 'bitb',  #
            0o030000: 'bit',   #
            0o140000: 'bicb',  #
            0o040000: 'bic',   #
            0o150000: 'bisb',  #
            0o050000: 'bis',   #
            0o070000: 'mul',   #
            0o071000: 'div',   #
            0o072000: 'ash',   #
            0o073000: 'ashc',  #
            0o074000: 'xor'    #
        }
        Op.update(self.doubleOp)

        self.branchOp = {
            0o000400: 'br',    #
            0o001000: 'bne',   #
            0o001400: 'beq',   #
            0o100000: 'bpl',   #
            0o100400: 'bmi',   #
            0o102000: 'bvc',   #
            0o102400: 'bvs',   #
            0o103000: 'bcc',   # bhis
            0o103400: 'bcs',   # blo
            0o002000: 'bge',   #
            0o002400: 'blt',   #
            0o003000: 'bgt',   #
            0o003400: 'ble',   #
            0o101000: 'bhi',   #
            0o101400: 'blos'   #
        }
        Op.update(self.branchOp)

        self.sysOp = {
            0o104400: 'sys'    # TRAP
        }
        Op.update(self.sysOp)

        self.prgCntrlOp = {
            0o000100: 'jmp',   #
            0o004000: 'jsr',   #
            0o000200: 'rts',   #
            0o006400: 'mark',  #
            0o077000: 'sob',   #
            0o000003: 'bpt',   #
            0o000004: 'iot',   #
            0o000002: 'rti',   #
            0o000006: 'rtt',   #
        }
        Op.update(self.prgCntrlOp)

        self.miscOp = {
            0o000000: 'halt',  #
            0o000001: 'wait',  #
            0o000005: 'reset', #
            0o006500: 'mfpi',  #
            0o006600: 'mtpi',  #
            0o000241: 'clc',   #
            0o000242: 'clv',   #
            0o000244: 'clz',   #
            0o000250: 'cln',   #
            0o000261: 'sec',   #
            0o000262: 'sev',   #
            0o000264: 'sez',   #
            0o000270: 'sen',   #
            0o000277: 'scc',   #
            0o000257: 'ccc',   #
            0o000240: 'nop'    #
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

    def isSingle(self, op):
        return op in self.singleOp.values()

    def isDouble(self, op):
        return op in self.doubleOp.values()

    def isBranch(self, op):
        return op in self.branchOp.values()

    def isSys(self, op):
        return op in self.sysOp.values()

    def isPrgCntrl(self, op):
        return op in self.prgCntrlOp.values()

    def isMisc(self, op):
        return op in self.miscOp.values()

    def get(self, word):
        for mask, ops in self.Masks.items():
            bits = word & mask
            if bits in ops:
                return self.Op[bits]

        return None

    def get_syscall(self, word):
        return self.syscall[word]


class Head:
    def __init__(self, data):
        # Header in a.out format is 8 words/16 bytes at the start of the file.
        # Each word as specified below

        self.size = len(data)  # bytes
        header = [(data[i + 1] << 8) | data[i] for i in range(0, self.size, 2)]
        if header[0] not in [0o407, 0o410, 0o411]:
            print(f"Wrong magic number: {header[0]:#o}")
            sys.exit(0)

        self.head = {'magic': header[0], 'txt': header[1], 'data': header[2], 'bss': header[3],
                     'sym': header[4], 'entry': header[5], 'unused': header[6], 'reloc': header[7]}

    def __str__(self):
        s = ""
        for k, v in self.head.items():
            s += f"{v:#06o} [{v:06}]: {k}\n"
        return s

    def get(self, key):
        if key in self.head:
            return self.head[key]
        else:
            return None


class Symbol:
    types = {0: 'u', 1: 'a', 2: 't', 3: 'd', 4: 'b', 31: 'F', 32: 'U', 33: 'A', 34: 'T', 35: 'D', 36: 'B'}

    def __init__(self, data):
        sym = ''
        for i in range(8):
            ch = data[i]
            if ch != 0:
                sym += chr(ch)
        self.name = sym

        self.type = data[9] << 8 | data[8]
        self.type_str = Symbol.types[self.type] if self.type in Symbol.types else str(self.type)

        self.val = data[11] << 8 | data[10]


    def __str__(self):
        return f"{self.val:#08o} [{self.val:08}] {self.type_str:>8} {self.name:>8}"


class SymTable:
    def __init__(self, data):
        self.table = {}

        ind = 0
        while ind < len(data):
            sym = Symbol(data[ind:ind + 12])
            self.table[sym.val] = sym
            ind += 12

    def __str__(self):
        headers = ["Sym val", "Type", "Name"]
        s = f"{headers[0]:^19} {headers[1]:>9} {headers[2]:>7}\n"
        s += len(s[1:])*"=" + "\n"
        for key in self.table:
            s += (str(self.table[key]) + "\n")
        return s[:-1]

    def find(self, val):
        for sym in self.table.values():
            if sym.val == val:
                return sym.name
        return None


class AddrMode(IntEnum):
    REGISTER = 0
    REGISTER_DEFERRED = 1
    AUTOINCREMENT = 2
    AUTOINCREMENT_DEFERRED = 3
    AUTODECREMENT = 4
    AUTODECREMENT_DEFERRED = 5
    INDEX = 6
    INDEX_DEFERRED = 7


class Operand:
    def __init__(self, reg):
        self.reg = reg
        self.size = 0
        self.addr = None
        self.name = None

    def get_addr(self):
        return self.addr

    def set_name(self, name):
        self.name = name

    def __str__(self):
        pass


class OpReg(Operand):
    def __init__(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("R" + str(self.reg))


class OpRegDef(Operand):
    def __init(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("(R" + str(self.reg) + ")")


class OpAutoIncr(Operand):
    def __init__(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("(R" + str(self.reg)+ ")+")


class OpAutoIncrDef(Operand):
    def __init__(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("*(R" + str(self.reg) + ")+")


class OpAutoDecr(Operand):
    def __init__(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("-(R" + str(self.reg) + ")")


class OpAutoDecrDef(Operand):
    def __init__(self, reg):
        super().__init__(reg)

    def __str__(self):
        return "{:>8}".format("*-(R" + str(self.reg) + ")")


class OpIndex(Operand):
    def __init__(self, reg, pc):
        super().__init__(reg)
        self.size = 2
        self.name = None

        self.addr = aout.VM.mem.read(pc + 2, 2) #(data[pc + 3] << 8) | data[pc + 2]
        if self.reg == 7:
            self.addr += (pc + 4)

    def __str__(self):
        name = self.name if self.name else str(self.addr)

        if self.reg == 7:
            return "{:>8}".format(name)
        else:
            return "{:>8}".format(name + "(R" + str(self.reg) + ")")


class OpIndexDef(Operand):
    def __init__(self, reg, pc):
        super().__init__(reg)
        self.size = 2
        self.name = None

        self.addr = aout.VM.mem.read(pc + 2, 2)  #(data[pc + 3] << 8) | data[pc + 2]
        if self.reg == 7:
            self.addr += (pc + 4)

    def __str__(self):
        name = self.name if self.name else str(self.addr)

        if self.reg == 7:
            return "{:>8}".format("*" + name)
        else:
            return "{:>8}".format("*" + name + "(R" + str(self.reg) + ")")


class OpImmediate(Operand):
    def __init__(self, reg, pc):
        super().__init__(reg)
        self.size = 2
        self.name = None

        self.addr = aout.VM.mem.read(pc + 2, 2) #(data[pc + 3] << 8) | data[pc + 2]

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("$" + name)


class OpAbsolute(Operand):
    def __init__(self, reg, pc):
        super().__init__(reg)
        self.size = 2
        self.name = None

        self.addr = aout.VM.mem.read(pc + 2, 2) #(data[pc + 3] << 8) | data[pc + 2]

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("*$" + name)


class Instr:
    def __init__(self, op, word, pc):
        self.op = op
        self.src_op = None
        self.dst_op = None
        self.pc = pc
        self.word = word #(data[pc + 1] << 8) | data[pc]
        self.size = 2
        self.mode = None
        self.stmt = None

    @staticmethod
    def new_operand(mode, reg, data, pc):
        if mode == AddrMode.REGISTER:
            return OpReg(reg)
        elif mode == AddrMode.REGISTER_DEFERRED:
            return OpRegDef(reg)
        elif mode == AddrMode.AUTOINCREMENT:
            return OpImmediate(reg, data, pc) if reg == 7 else OpAutoIncr(reg)
        elif mode == AddrMode.AUTOINCREMENT_DEFERRED:
            return OpAbsolute(reg, data, pc) if reg == 7 else OpAutoIncrDef(reg)
        elif mode == AddrMode.AUTODECREMENT:
            return OpAutoDecr(reg)
        elif mode == AddrMode.AUTODECREMENT_DEFERRED:
            return OpAutoDecrDef(reg)
        elif mode == AddrMode.INDEX:
            return OpIndex(reg, data, pc)
        elif mode == AddrMode.INDEX_DEFERRED:
            return OpIndexDef(reg, data, pc)
        else:
            assert False, "Wrong mode"

    def __str__(self):
        pass

    def exec(self):
        if self.stmt:
            self.stmt.exec(aout.VM)
        else:
            assert False, "Non-executable statement"


class InstrAddr(Instr):
    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)

    def __str__(self):
        return "{:<8}".format(self.op)


class InstrSingle(Instr):
    # CLR(B), COM(B), INC(B), DEC(B), NEG(B), TST(B), ASR(B), ASL(B), ROR(B), ROL(B), SWAB, ADC(B), SBC(B), SXT

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)

        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, data, pc)

        self.size += self.dst_op.size

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
        addr = str(self.dst_op.addr)
        if self.dst_op.addr is None:
            expr = as_expr.AddrRegister(reg)
        else:
            expr = as_expr.AddrIndex(reg, as_expr.Expression(addr))

        self.stmt = as_stmt.KeywordStmt(pc, self.op, expr)

    def __str__(self):
        return "{:<8} {:>8}".format(self.op, str(self.dst_op))


class InstrDouble(Instr):
    # MOV(B), CMP(B), ADD, SUB, BIT(B), BIC, BIS(B), MUL, DIV, ASH, ASHC, XOR

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)

        self.src_mode = (self.word & 0o7000) >> 9
        self.src_reg  = (self.word & 0o0700) >> 6
        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)

        self.src_op = self.new_operand(self.src_mode, self.src_reg, data, pc)
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, data, pc + 2)

        if (self.dst_mode == AddrMode.INDEX or self.dst_mode == AddrMode.INDEX_DEFERRED) and \
            (self.src_mode == AddrMode.INDEX or self.src_mode == AddrMode.INDEX_DEFERRED):
            self.src_op.addr += 2

        self.size += (self.src_op.size + self.dst_op.size)

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.src_reg]
        addr = str(self.src_op.addr)
        if self.src_op.addr is None:
            expr0 = as_expr.AddrRegister(reg)
        else:
            expr0 = as_expr.AddrIndex(reg, as_expr.Expression(addr))

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
        addr = str(self.dst_op.addr)
        if self.dst_op.addr is None:
            expr1 = as_expr.AddrRegister(reg)
        else:
            expr1 = as_expr.AddrIndex(reg, as_expr.Expression(addr))

        self.stmt = as_stmt.KeywordStmt(pc, self.op, expr0, expr1)

    def __str__(self):
        return "{:<8} {:>8}, {:>8}".format(self.op, str(self.src_op), str(self.dst_op))


class InstrBranch(Instr):
    # BR, BNE, BEQ, BPL, BMI, BVC, BVS, BCC, BCS, BGE, BLT, BGT, BLE, BHI, BLOS

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)
        self.offset = self.word & 0o0377
        self.name = None

        expr = as_expr.AddrIndex(None, as_expr.Expression(str(self.offset)))
        self.stmt = as_stmt.KeywordStmt(pc, self.op, expr)
    def __str__(self):
        return "{:<8} {:>8}".format(self.op, self.offset if self.name is None else self.name)


class InstrSyscall(Instr):
    # indir, exit, fork, read, write, open, close, wait, creat, link, unlink, exec, chdir, time, makdir, chmod,
    # chown, break, stat, seek, tell, mount, umout, setuid, getuid, stime, fstat, mdate, stty, gtty, nice, signal

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)

        self.syscall = instrLUT.get_syscall(((data[pc + 1] << 8) | data[pc]) & 0o0077)

        if self.syscall in ['exit', 'fork', 'close', 'wait', 'time', 'getpid',
                            'setuid', 'getuid', 'stime', 'fstat', 'mdate', 'nice']:
            self.par = []

        elif self.syscall in ['indir', 'unlink', 'chdir', 'break', 'umount', 'stty', 'gtty']:
            self.par = [
                {'addr': (data[pc + 3] << 8) | data[pc + 2], 'name': None}
            ]

        elif self.syscall in ['read', 'write', 'open', 'creat', 'link', 'exec',
                              'chmod', 'chown', 'stat', 'seek', 'signal']:
            self.par = [
                {'addr': (data[pc + 3] << 8) | data[pc + 2], 'name': None},
                {'addr': (data[pc + 5] << 8) | data[pc + 4], 'name': None}
            ]

        elif self.syscall in ['makdir', 'mount']:
            self.par = [
                {'addr': (data[pc + 3] << 8) | data[pc + 2], 'name': None},
                {'addr': (data[pc + 5] << 8) | data[pc + 4], 'name': None},
                {'addr': (data[pc + 7] << 8) | data[pc + 6], 'name': None}
            ]

        self.size += len(self.par) * 2
        if self.syscall == 'gtty':
            self.size += 4

        self.stmt = as_stmt.SyscallStmt(pc, self.syscall)

    def __str__(self):
        par_str = ""
        for par in self.par:
            par_str += "{:>8}".format(par['name'] if par['name'] is not None else par['addr'])

        return "{:<8} {:>8}{} {:>8}".format(self.op, self.syscall, ";" if par_str != "" else "", par_str)


class InstrPrgCntrl(Instr):
    # JMP, JSR, RTS, MARK, SOB, BPT, IOT, RTI, RTT

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)

        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, data, pc)

        self.src_mode = 0
        if op == 'JSR':
            self.src_reg  = (self.word & 0o700) >> 6
        else:
            self.src_reg = 0

        self.src_op = self.new_operand(self.src_mode, self.src_reg, data, pc)
        self.size += self.dst_op.size

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
        addr = str(self.dst_op.addr) + "."
        if self.dst_op.addr is None:
            expr = as_expr.AddrRegister(reg)
        else:
            expr = as_expr.AddrIndex(reg, as_expr.Expression(addr))

        self.stmt = as_stmt.KeywordStmt(pc, self.op, expr)


    def __str__(self):
        if self.op == 'JSR':
            return "{: <8} {: >8}, {: >8}".format(self.op, str(self.src_op), str(self.dst_op))
        else:
            return "{:<8} {:>8}".format(self.op, str(self.dst_op))


class InstrMisc(Instr):
    # HALT, WAIT, RESET, MFPI, MTPI, CLC, CLV, CLZ, CLN, SEC, SEV, SEZ, SEN, SCC, CCC, NOP

    def __init__(self, op, data, pc):
        super().__init__(op, data, pc)
        self.stmt = as_stmt.KeywordStmt(pc, self.op)

    def __str__(self):
        return "{:<8}".format(self.op)


class Text:
    def __init__(self, data, sym_table):
        self.sym_table = sym_table
        self.instr = []
        self.data = data

    def exec(self):
        while True:
            instr = self.decode_instr(aout.VM.mem.memory, aout.VM.get_PC())
            if instr:
                instr.exec()



    def decode(self):
        pc = 0
        while pc < len(self.data):
            instr = self.decode_instr(self.data, pc)
            if instr:
                self.instr.append({'addr': pc, 'instr': instr})
                pc += instr.size
            else:
                pc += 2

    def decode_instr(self, data, pc):
        word = (data[pc + 1] << 8) | data[pc]

        sym = self.sym_table.find(word)
        if sym:
            return InstrAddr(sym, data, pc)

        op = instrLUT.get(word)
        if op:
            if instrLUT.isSingle(op):
                instr = InstrSingle(op, data, pc)
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isDouble(op):
                instr = InstrDouble(op, data, pc)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isBranch(op):
                instr = InstrBranch(op, data, pc)
                instr.name = self.sym_table.find(2 * instr.offset + (pc + 2))
                return instr

            elif instrLUT.isSys(op):
                instr = InstrSyscall(op, data, pc)
                for par in instr.par:
                    par['name'] = self.sym_table.find(par['addr'])
                return instr

            elif instrLUT.isPrgCntrl(op):
                instr = InstrPrgCntrl(op, data, pc)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isMisc(op):
                return InstrMisc(op, data, pc)

            else:
                return None

    def __str__(self):
        s  = ""
        spaces = 8 * " "
        for instr in self.instr:
            word_str = f"{instr['instr'].word:#08o}"

            if instr['instr'].src_op:
                src_op_str = f"{instr['instr'].src_op.addr:0<#8o}" if instr['instr'].src_op.addr else spaces
            else:
                src_op_str = spaces

            if instr['instr'].dst_op:
                dst_op_str = f"{instr['instr'].dst_op.addr:0>#8o}" if instr['instr'].dst_op.addr else spaces
            else:
                dst_op_str = spaces

            and_str = 3 * " "
            if src_op_str and dst_op_str:
                if src_op_str != spaces and dst_op_str != spaces:
                    and_str = " & "

            word_str += (": " + src_op_str + and_str + dst_op_str)
            s += f"{instr['addr']:0<#8o} [{instr['addr']:0>8}] -> {{{word_str: <29}}} => {str(instr['instr']): <50}" + "\n"
        return s


class AOut:
    def __init__(self, name):
        self.name = name
        with open(self.name, 'rb') as f:
            bytes = f.read()

        self.head = Head(bytes[0:16])

        self.VM = asm.VM("run")
        self.VM.memory(bytes[self.head.size:])

        sym_start = self.head.size + (1 if self.head.get('reloc') else 2) * (self.head.get('txt') + self.head.get('data'))
        self.sym_table = SymTable(bytes[sym_start:sym_start + self.head.get('sym')])

        self.text = Text(bytes[16:self.head.get('txt')], self.sym_table)

    def exec(self):
        while True:
            instr = self.decode_instr(self.VM.get_PC())
            if instr:
                instr.exec()

    def decode_instr(self, pc):
        word = self.VM.mem.read(pc, 2)
        #word = (data[pc + 1] << 8) | data[pc]

        sym = self.sym_table.find(word)
        if sym:
            return InstrAddr(sym, word, pc)

        op = instrLUT.get(word)
        if op:
            if instrLUT.isSingle(op):
                instr = InstrSingle(op, word, pc)
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isDouble(op):
                instr = InstrDouble(op, word, pc)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isBranch(op):
                instr = InstrBranch(op, word, pc)
                instr.name = self.sym_table.find(2 * instr.offset + (pc + 2))
                return instr

            elif instrLUT.isSys(op):
                instr = InstrSyscall(op, word, pc)
                for par in instr.par:
                    par['name'] = self.sym_table.find(par['addr'])
                return instr

            elif instrLUT.isPrgCntrl(op):
                instr = InstrPrgCntrl(op, word, pc)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isMisc(op):
                return InstrMisc(op, word, pc)

            else:
                return None


    def dump(self):
        print(self.head)
        print(self.sym_table)
        print(2*"\n" + "--X--" + 2*"\n")
        self.text.decode()
        print(self.text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, required=True)
    args = parser.parse_args()

    instrLUT = InstrLUT()
    aout = AOut(args.file)
    aout.exec()

    #aout.dump()
