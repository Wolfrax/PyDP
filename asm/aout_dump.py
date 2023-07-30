import argparse
import sys
import asm
import instr_codes as ic
import util


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


class SymTable:
    types = {0: 'u', 1: 'a', 2: 't', 3: 'd', 4: 'b', 31: 'F', 32: 'U', 33: 'A', 34: 'T', 35: 'D', 36: 'B'}

    def __init__(self, vm, start_addr, end_addr):
        self.table = {}

        ind = start_addr
        while ind < end_addr:
            sym = ''
            for i in range(8):
                ch = vm.memory.read(ind + i, 1)
                if ch != 0:
                    sym += chr(ch)

            type = vm.memory.read(ind + 8)
            type_str = self.types[type] if type in self.types else str(type)

            val = vm.memory.read(ind + 10)

            self.table[val] = {'name': sym, 'type': type, 'type_str': type_str, 'value': val}
            ind += 12

    def __str__(self):
        headers = ["Sym val", "Type", "Name"]
        s = f"{headers[0]:^19} {headers[1]:>9} {headers[2]:>7}\n"
        s += len(s[1:])*"=" + "\n"
        for key in self.table:
            elem = self.table[key]
            s += (f"{elem['value']:#08o} [{elem['value']:08}] {elem['type_str']:>8} {elem['name']:>8}" + "\n")
        return s[:-1]

    def __iter__(self):
        return iter(self.table)

    def find(self, val):
        for sym in self.table.values():
            if sym['value'] == val:
                return sym['name']
        return None

    def get(self, val):
        for sym in self.table.values():
            if sym['value'] == val:
                return sym


class Operand:
    def __init__(self, reg):
        self.reg = reg
        self.size = 0
        self.addr = None
        self.name = None

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
    def __init__(self, vm, reg, addr):
        super().__init__(reg)
        self.size = 2

        self.addr = vm.memory.read(addr + 2)
        if self.reg == 7:
            self.addr += (addr + 4)
        self.addr = util.from_2_compl(self.addr, False)


    def __str__(self):
        name = self.name if self.name else str(self.addr)
        if self.reg == 7:
            return "{:>8}".format(name)
        else:
            return "{:>8}".format(name + "(R" + str(self.reg) + ")")


class OpIndexDef(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(reg)
        self.size = 2

        self.addr = vm.memory.read(addr + 2)
        if self.reg == 7:
            self.addr += (addr + 4)
        self.addr = util.from_2_compl(self.addr, False)

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        if self.reg == 7:
            return "{:>8}".format("*" + name)
        else:
            return "{:>8}".format("*" + name + "(R" + str(self.reg) + ")")


class OpImmediate(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(reg)
        self.size = 2
        self.addr = vm.memory.read(addr + 2)
        self.addr = util.from_2_compl(self.addr, False)

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("$" + name)


class OpAbsolute(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(reg)
        self.size = 2
        self.addr = vm.memory.read(addr + 2)
        self.addr = util.from_2_compl(self.addr, False)


    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("*$" + name)


# Note, the pc have the address of the current instruction, if src and/or dst occupies words following the
# instruction, we need to make sure that this accounted. The mode of the instruction indicates how.
# The following applies
# (size 0 means that no memory position is used for operand, 2 that 1 word (2 bytes) is used):
#   Mode 0, register mode: register holds value of the operand (size 0)
#   Mode 1, register deferred: register holds address to value, not in memory (size 0)
#   Mode 2, auto increment: register holds address to value, incr register (size 0)
#   Mode 3, auto increment deferred: register holds address to address of value, incr register (size 0)
#   Mode 4, auto decrement: decr register, register holds address to value (size 0)
#   Mode 5, auto decrement deferred: decr register, register holds address to address of value (size 0)
#   Mode 6, index: register + mem pos after instr holds address to value (size 2)
#   Mode 7, index deferred: register + mem pos after instr holds address to address to value (size 2)
#   Mode 7 (PC), immediate: mem pos after instr holds value (size 2)
#   Mode 3 (PC), absolute: mem pos after instr holds address to value (size 2)
#   Mode 6 (PC), relative: mem pos after instr + (pc + 4) is address to operand (size 2)
#   Mode 7 (PC), relative deferred: mem pos after instr + (pc + 4) is address to address to value (size 2)
#
# Thus, an operand will take 0 or 1 words in memory after instruction.
# In case of an instruction with 2 operands, it might take up to 2 words in memory.
# For example:
#   MOV $1, label
#   move value 1 (which is stored in memory position following the instruction), to the memory position
#   for label who's address is given by the value in memory position following the memory position for 1.
#   Thus, in total this instruction will occupy 3 words in memory.
#

class Instr:
    REGISTER = 0
    REGISTER_DEFERRED = 1
    AUTOINCREMENT = 2
    AUTOINCREMENT_DEFERRED = 3
    AUTODECREMENT = 4
    AUTODECREMENT_DEFERRED = 5
    INDEX = 6
    INDEX_DEFERRED = 7

    def __init__(self, vm, op):
        self.vm = vm
        self.op = op
        self.src_op = None
        self.dst_op = None

    def new_operand(self, mode, reg):
        if mode == self.REGISTER:
            return OpReg(reg)
        elif mode == self.REGISTER_DEFERRED:
            return OpRegDef(reg)
        elif mode == self.AUTOINCREMENT:
            return OpImmediate(self.vm, reg, self.vm.pc) if reg == 7 else OpAutoIncr(reg)
        elif mode == self.AUTOINCREMENT_DEFERRED:
            return OpAbsolute(self.vm, reg, self.vm.pc) if reg == 7 else OpAutoIncrDef(reg)
        elif mode == self.AUTODECREMENT:
            return OpAutoDecr(reg)
        elif mode == self.AUTODECREMENT_DEFERRED:
            return OpAutoDecrDef(reg)
        elif mode == self.INDEX:
            return OpIndex(self.vm, reg, self.vm.pc)
        elif mode == self.INDEX_DEFERRED:
            return OpIndexDef(self.vm, reg, self.vm.pc)
        else:
            assert False, "Wrong mode"

    def __str__(self):
        pass


class InstrAddr(Instr):
    def __init__(self, vm, op):
        super().__init__(vm, op)
        vm.pc += 2

    def __str__(self):
        return "{:<8}".format(self.op)


class InstrSingle(Instr):
    # CLR(B), COM(B), INC(B), DEC(B), NEG(B), TST(B), ASR(B), ASL(B), ROR(B), ROL(B), SWAB, ADC(B), SBC(B), SXT

    def __init__(self, vm, op):
        super().__init__(vm, op)

        dst_mode = (vm.word & 0o0070) >> 3
        dst_reg  = (vm.word & 0o0007)
        self.dst_op = self.new_operand(dst_mode, dst_reg)

        if self.dst_op.addr:
            if dst_reg == 7:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr)
            else:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr + vm.pc)

        self.reloc_str = vm.decode_reloc() if vm.reloc else ""
        vm.pc += self.dst_op.size
        vm.pc += 2

    def __str__(self):
        return "{: <10} {: >10}{} {: >10} {: >32}".format(self.op, str(self.dst_op), " ", " ", self.reloc_str)


class InstrDouble(Instr):
    # MOV(B), CMP(B), ADD, SUB, BIT(B), BIC, BIS(B), MUL, DIV, ASH, ASHC, XOR

    def __init__(self, vm, op):
        super().__init__(vm, op)

        src_mode = (vm.word & 0o7000) >> 9
        src_reg  = (vm.word & 0o0700) >> 6
        dst_mode = (vm.word & 0o0070) >> 3
        dst_reg  = (vm.word & 0o0007)

        self.src_op = self.new_operand(src_mode, src_reg)
        vm.pc += self.src_op.size
        self.reloc_str = vm.decode_reloc() if vm.reloc else ""
        if self.src_op.addr:
            if src_reg == 7:
                self.src_op.name = vm.sym_table.find(self.src_op.addr)
            else:
                self.src_op.name = vm.sym_table.find(self.src_op.addr + vm.pc)


        self.dst_op = self.new_operand(dst_mode, dst_reg)
        vm.pc += self.dst_op.size
        self.reloc_str += ("; " + vm.decode_reloc()) if vm.reloc else ""
        if self.dst_op.addr:
            if dst_reg == 7:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr)
            else:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr + vm.pc)

        vm.pc += 2

    def __str__(self):
        return "{: <10} {: >10}{} {: >10} {: >32}".format(self.op, str(self.src_op), ",", str(self.dst_op),
                                                          " ", self.reloc_str)


class InstrBranch(Instr):
    # BR, BNE, BEQ, BPL, BMI, BVC, BVS, BCC, BCS, BGE, BLT, BGT, BLE, BHI, BLOS

    def __init__(self, vm, op):
        super().__init__(vm, op)
        self.offset = vm.word & 0o0377
        self.name = vm.sym_table.find(vm.pc + 2 + (2 * self.offset))
        self.reloc_str = vm.decode_reloc() if vm.reloc else ""
        vm.pc += 2


    def __str__(self):
        return "{: <10} {: >10}{} {: >10} {: >32}".format(self.op,
                                                          self.offset if self.name is None else self.name,
                                                          " ",
                                                          " ",
                                                          self.reloc_str)


class InstrSyscall(Instr):
    # indir, exit, fork, read, write, open, close, wait, creat, link, unlink, exec, chdir, time, makdir, chmod,
    # chown, break, stat, seek, tell, mount, umount, setuid, getuid, stime, fstat, mdate, stty, gtty, nice, signal

    def __init__(self, vm, op):
        super().__init__(vm, op)

        self.reloc_str = ""

        self.syscall = instrLUT.get_syscall(vm.word & 0o0077)

        if self.syscall in ['exit', 'fork', 'close', 'wait', 'time', 'getpid',
                            'setuid', 'getuid', 'stime', 'fstat', 'mdate', 'nice']:
            self.par = []

        elif self.syscall in ['indir', 'unlink', 'chdir', 'break', 'umount', 'stty', 'gtty']:
            sys_addr = vm.memory.read(vm.pc + 2)
            self.reloc_str += vm.decode_reloc(2) if vm.reloc else ""
            self.par = [
                {'addr': sys_addr, 'name': None}
            ]

        elif self.syscall in ['read', 'write', 'open', 'creat', 'link', 'exec',
                              'chmod', 'chown', 'stat', 'seek', 'signal']:
            sys_addr1 = vm.memory.read(vm.pc + 2)
            self.reloc_str += vm.decode_reloc(2) if vm.reloc else ""
            sys_addr2 = vm.memory.read(vm.pc + 4)
            self.reloc_str += vm.decode_reloc(4) if vm.reloc else ""
            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None}
            ]

        elif self.syscall in ['makdir', 'mount']:
            sys_addr1 = vm.memory.read(vm.pc + 2)
            self.reloc_str += vm.decode_reloc(2) if vm.reloc else ""
            sys_addr2 = vm.memory.read(vm.pc + 4)
            self.reloc_str += vm.decode_reloc(4) if vm.reloc else ""
            sys_addr3 = vm.memory.read(vm.pc + 6)
            self.reloc_str += vm.decode_reloc(6) if vm.reloc else ""
            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None},
                {'addr': sys_addr3, 'name': None}
            ]

        for par in self.par:
            par['name'] = vm.sym_table.find(par['addr'])

        size = len(self.par) * 2
        if self.syscall == 'gtty':
            size += 4
        vm.pc += size

        vm.pc += 2


    def __str__(self):
        par_str = ""
        for par in self.par:
            par_str += "{: >10}".format(par['name'] if par['name'] is not None else par['addr'])
        if len(par_str) < 30:
            par_str = (30 - len(par_str)) * " " + par_str

        return "{: <10} {: >10}{} {: >10} {:>12}".format(self.op,
                                                          self.syscall,
                                                          ";" if par_str != "" else "",
                                                          par_str,
                                                          self.reloc_str)


class InstrPrgCntrl(Instr):
    # JMP, JSR, RTS, MARK, SOB, BPT, IOT, RTI, RTT

    def __init__(self, vm, op):
        super().__init__(vm, op)

        dst_mode = (vm.word & 0o0070) >> 3
        dst_reg  = (vm.word & 0o0007)
        self.dst_op = self.new_operand(dst_mode, dst_reg)

        if self.dst_op.addr:
            if dst_reg == 7:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr)
            else:
                self.dst_op.name = vm.sym_table.find(self.dst_op.addr + vm.pc)

        src_reg  = (vm.word & 0o700) >> 6 if op == 'jsr' else 0
        self.src_op = self.new_operand(Instr.REGISTER, src_reg)

        vm.pc += self.dst_op.size
        self.reloc_str = vm.decode_reloc() if vm.reloc else ""

        vm.pc += 2

    def __str__(self):
        if self.op == 'jsr':
            return "{: <10} {: >10}{} {: >10} {: >32}".format(self.op, str(self.src_op), ",", str(self.dst_op),
                                                              self.reloc_str)
        else:
            return "{: <10} {: >10}{} {: >10} {: >32}".format(self.op, str(self.dst_op), " ", " ", self.reloc_str)


class InstrMisc(Instr):
    # HALT, WAIT, RESET, MFPI, MTPI, CLC, CLV, CLZ, CLN, SEC, SEV, SEZ, SEN, SCC, CCC, NOP

    def __init__(self, vm, op):
        super().__init__(vm, op)
        vm.pc += 2

    def __str__(self):
        return "{: <10}".format(self.op)


class AOut:
    def __init__(self, name):
        self.name = name
        with open(self.name, 'rb') as f:
            bytes = f.read()

        self.head = Head(bytes[0:16])
        self.memory = asm.Memory(64)
        self.memory.init(bytes[self.head.size:])
        self.pc = 0
        self.word = 0

        sym_start = (1 if self.head.get('reloc') else 2) * (self.head.get('txt') + self.head.get('data'))
        self.sym_table = SymTable(self, sym_start, sym_start + self.head.get('sym'))

        if self.head.get('reloc') == 0:  # Suppress reloc info is off
            self.reloc = self.head.get('txt') + self.head.get('data')
        else:
            self.reloc = None

    def decode_instr(self):
        self.word = self.memory.read(self.pc)

        sym = self.sym_table.find(self.word)
        if sym:
            return InstrAddr(self, sym)

        op = instrLUT.get(self.word)
        if op:
            if instrLUT.isSingle(op):
                return InstrSingle(self, op)

            elif instrLUT.isDouble(op):
                return InstrDouble(self, op)

            elif instrLUT.isBranch(op):
                return InstrBranch(self, op)

            elif instrLUT.isSys(op):
                return InstrSyscall(self, op)

            elif instrLUT.isPrgCntrl(op):
                return InstrPrgCntrl(self, op)

            elif instrLUT.isMisc(op):
                return InstrMisc(self, op)

            else:
                return None
        else:
            return None


    def decode_reloc(self, offset=0):
        reloc_word = self.memory.read(self.pc + offset + self.reloc)
        if reloc_word == 0:
            return ""

        reloc_str = "<"

        reloc_str += "r_" if reloc_word & 0x01 else "a_"
        reloc_word &= 0xE
        if reloc_word == 0:
            reloc_str += "a"
        elif reloc_word == 2:
            reloc_str += "t"
        elif reloc_word == 4:
            reloc_str += "d"
        elif reloc_word == 6:
            reloc_str += "b"
        elif reloc_word == 8:
            reloc_str += "u"
            reloc_str += str(reloc_word >> 4)
        else:
            pass

        return reloc_str + ">"


    def dump(self):
        help_text = f"""
        This will dump the file {self.name}.
        
        Dump is in 3 sections:
        1. Header information
        2. Symbol table
        3. Instructions
        
        For symbols, the following abbreviations is used for types:
        'u' - undefined symbol
        'a' - absolute symbol
        't' - text segment symbol
        'd' - data segment symbol
        'b' - bss segment symbol
        'F' - File name symbol (produced by ld)
        'U' - Undefined external (.globl) symbol
        'A' - Absolute external symbol
        'T' - Text segment external symbol
        'D' - Data segment external symbol
        'B' - Bss segement external symbol
        
        For instructions, the relocation information is shown within <>-string, using the same abbreviations as for
        symbols and a prefix. Prefixes are 'r_' for relative pc and 'a_' for actual symbol. See a.out manual page.
        
        Dump tries to do a good job of dumping instructions and looking up symbolic names of operands.
        Due to the architecture of PDP instruction set, it is impossible to tell is a word is instruction or data, so
        the output might be in error due to this.
        """

        print(help_text)
        print(self.head)
        print(self.sym_table)
        print(2*"\n" + "--X--" + 2*"\n")

        spaces = 8 * " "

        txt_end = self.head.get('txt')
        while self.pc < txt_end:
            instr = self.decode_instr()
            if instr is not None:
                word_str = f"{self.word:#08o}"
                if instr.src_op:
                    src_op_str = f"{instr.src_op.addr:0<#8o}" if instr.src_op.addr else spaces
                else:
                    src_op_str = spaces

                if instr.dst_op:
                    dst_op_str = f"{instr.dst_op.addr:0>#8o}" if instr.dst_op.addr else spaces
                else:
                    dst_op_str = spaces

                and_str = 3 * " "
                if src_op_str and dst_op_str:
                    if src_op_str != spaces and dst_op_str != spaces:
                        and_str = " & "

                word_str += (": " + src_op_str + and_str + dst_op_str)

                print(f"{self.pc:0<#8o} [{self.pc:0>8}] -> {{{word_str: <29}}} => {str(instr): <50}")
            else:
                self.pc += (self.pc + 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, required=True)
    args = parser.parse_args()

    instrLUT = ic.InstrLUT()
    aout = AOut(args.file)

    aout.dump()
