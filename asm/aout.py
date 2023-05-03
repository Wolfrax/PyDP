import instr_codes as ic
import sys
import asm
import as_stmt
import as_expr
import glob
import util
import atexit

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
        self.VM = vm
        self.table = {}

        ind = start_addr
        while ind < end_addr:
            sym = ''
            for i in range(8):
                ch = self.VM.mem.read(ind + i, 1)
                if ch != 0:
                    sym += chr(ch)

            type = self.VM.mem.read(ind + 8)
            type_str = self.types[type] if type in self.types else str(type)

            val = self.VM.mem.read(ind + 10)

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

    def find(self, val, abs=False):
        if val is None:
            return val

        val = val if abs else (val + self.VM.get_PC())
        for sym in self.table.values():
            if sym['value'] == val:
                return sym['name']
        return None

    def get(self, val):
        for sym in self.table.values():
            if sym['value'] == val:
                return sym


class Operand:
    def __init__(self, vm, reg):
        self.VM = vm
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
    def __init__(self, vm, reg):
        super().__init__(vm, reg)

    def __str__(self):
        return "{:>8}".format("R" + str(self.reg))


class OpRegDef(Operand):
    def __init(self, vm, reg):
        super().__init__(vm, reg)

    def __str__(self):
        return "{:>8}".format("(R" + str(self.reg) + ")")


class OpAutoIncr(Operand):
    def __init__(self, vm, reg):
        super().__init__(vm, reg)
        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.reg]
        self.addr = self.VM.mem.read(vm.register[reg])

    def __str__(self):
        return "{:>8}".format("(R" + str(self.reg)+ ")+")


class OpAutoIncrDef(Operand):
    def __init__(self, vm, reg):
        super().__init__(vm, reg)

    def __str__(self):
        return "{:>8}".format("*(R" + str(self.reg) + ")+")


class OpAutoDecr(Operand):
    def __init__(self, vm, reg):
        super().__init__(vm, reg)

    def __str__(self):
        return "{:>8}".format("-(R" + str(self.reg) + ")")


class OpAutoDecrDef(Operand):
    def __init__(self, vm, reg):
        super().__init__(vm, reg)

    def __str__(self):
        return "{:>8}".format("*-(R" + str(self.reg) + ")")


class OpIndex(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(vm, reg)
        self.size = 2
        self.name = None

        self.addr = self.VM.mem.read(addr + 2)
        if self.reg == 7:
            self.addr += 4
        self.addr = util.from_2_compl(self.addr, False)


    def __str__(self):
        name = self.name if self.name else str(self.addr)

        if self.reg == 7:
            return "{:>8}".format(name)
        else:
            return "{:>8}".format(name + "(R" + str(self.reg) + ")")


class OpIndexDef(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(vm, reg)
        self.size = 2
        self.name = None

        self.addr = self.VM.mem.read(addr + 2)
        if self.reg == 7:
            self.addr += (addr + 4)

    def __str__(self):
        name = self.name if self.name else str(self.addr)

        if self.reg == 7:
            return "{:>8}".format("*" + name)
        else:
            return "{:>8}".format("*" + name + "(R" + str(self.reg) + ")")


class OpImmediate(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(vm, reg)
        self.size = 2
        self.name = None
        self.addr = vm.mem.read(addr + self.size)

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("$" + name)


class OpAbsolute(Operand):
    def __init__(self, vm, reg, addr):
        super().__init__(vm, reg)
        self.size = 2
        self.name = None

        self.addr = addr + self.size

    def __str__(self):
        name = self.name if self.name else str(self.addr)
        return "{:>8}".format("*$" + name)


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
        self.VM = vm
        self.op = op
        self.src_op = None
        self.dst_op = None
        self.pc = self.VM.get_PC()
        self.word = self.VM.mem.read(self.pc, 2)
        self.size = 2
        self.mode = None
        self.stmt = None


    def new_operand(self, mode, reg, addr):
        if mode == self.REGISTER:
            return OpReg(self.VM, reg)
        elif mode == self.REGISTER_DEFERRED:
            return OpRegDef(self.VM, reg)
        elif mode == self.AUTOINCREMENT:
            return OpImmediate(self.VM, reg, addr) if reg == 7 else OpAutoIncr(self.VM, reg)
        elif mode == self.AUTOINCREMENT_DEFERRED:
            return OpAbsolute(self.VM, reg, addr) if reg == 7 else OpAutoIncrDef(self.VM, reg)
        elif mode == self.AUTODECREMENT:
            return OpAutoDecr(self.VM, reg)
        elif mode == self.AUTODECREMENT_DEFERRED:
            return OpAutoDecrDef(self.VM, reg)
        elif mode == self.INDEX:
            return OpIndex(self.VM, reg, addr)
        elif mode == self.INDEX_DEFERRED:
            return OpIndexDef(self.VM, reg, addr)
        else:
            assert False, "Wrong mode"

    def new_expr(self, mode, reg, expr=None):
        if mode == self.REGISTER:
            return as_expr.AddrRegister(reg)
        elif mode == self.REGISTER_DEFERRED:
            return as_expr.AddrRegisterDeferred(reg)
        elif mode == self.AUTOINCREMENT:
            return as_expr.AddrImmediate(as_expr.Expression(expr)) if reg == 'pc' else as_expr.AddrAutoIncrement(reg)
        elif mode == self.AUTOINCREMENT_DEFERRED:
            return as_expr.AddrAbsolute(as_expr.Expression(expr)) if reg == 'pc' else \
                as_expr.AddrAutoIncrementDeferred(reg)
        elif mode == self.AUTODECREMENT:
            return as_expr.AddrAutoDecrement(reg)
        elif mode == self.AUTODECREMENT_DEFERRED:
            return as_expr.AddrAutoDecrementDeferred(reg)
        elif mode == self.INDEX:
            # Note, if reg == 'pc' we should return AddrRelative object, but we use AddrIndex instead
            return as_expr.AddrIndex(reg, as_expr.Expression(expr))
        elif mode == self.INDEX_DEFERRED:
            return as_expr.AddrRelativeDeferred(as_expr.Expression(expr)) if reg == 'pc' else \
                as_expr.AddrIndexDeferred(reg, as_expr.Expression(expr))

    def __str__(self):
        pass

    def exec(self):
        if self.stmt:
            self.VM.trace(self.stmt)
            self.stmt.exec(self.VM)
            self.VM.post_trace()

        else:
            assert False, "Non-executable statement"


class InstrAddr(Instr):
    def __init__(self, vm, op):
        super().__init__(vm, op)

    def __str__(self):
        return "{:<8}".format(self.op)

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


class InstrSingle(Instr):
    # CLR(B), COM(B), INC(B), DEC(B), NEG(B), TST(B), ASR(B), ASL(B), ROR(B), ROL(B), SWAB, ADC(B), SBC(B), SXT

    def __init__(self, vm, op):
        super().__init__(vm, op)

        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)
        addr = self.VM.get_PC()
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, addr)

        self.size += self.dst_op.size

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
        if self.dst_op.addr is not None:
            addr = str(self.dst_op.addr) + "."  # Decimal
        else:
            addr = None

        dst_expr = self.new_expr(self.dst_mode, reg, addr)

        self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op, dst_expr)

    def __str__(self):
        return "{:<8} {:>8}".format(self.op, str(self.dst_op))


class InstrDouble(Instr):
    # MOV(B), CMP(B), ADD, SUB, BIT(B), BIC, BIS(B), MUL, DIV, ASH, ASHC, XOR

    def __init__(self, vm, op):
        super().__init__(vm, op)

        self.src_mode = (self.word & 0o7000) >> 9
        self.src_reg  = (self.word & 0o0700) >> 6
        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)

        addr = self.VM.get_PC()  # This is the address of the instruction
        self.src_op = self.new_operand(self.src_mode, self.src_reg, addr)
        addr += self.src_op.size
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, addr)

        if (self.dst_mode == self.INDEX or self.dst_mode == self.INDEX_DEFERRED) and \
            (self.src_mode == self.INDEX or self.src_mode == self.INDEX_DEFERRED):
            self.src_op.addr += 2

        self.size += (self.src_op.size + self.dst_op.size)

        ## NEW
        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.src_reg]
        if self.src_op.addr is not None:
            addr = str(self.src_op.addr) + "."  # Decimal
        else:
            addr = None

        src_expr = self.new_expr(self.src_mode, reg, addr)

        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
        if self.dst_op.addr is not None:
            addr = str(self.dst_op.addr) + "."  # Decimal
        else:
            addr = None

        dst_expr = self.new_expr(self.dst_mode, reg, addr)

        self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op, src_expr, dst_expr)

    def __str__(self):
        return "{:<8} {:>8}, {:>8}".format(self.op, str(self.src_op), str(self.dst_op))


class InstrBranch(Instr):
    # BR, BNE, BEQ, BPL, BMI, BVC, BVS, BCC, BCS, BGE, BLT, BGT, BLE, BHI, BLOS

    def __init__(self, vm, op):
        super().__init__(vm, op)
        self.offset = self.word & 0o0377
        self.name = None

        # Note, branch use offset, and it thus limited in range. offset needs to be multiplied by 2 and is relative
        # to current pc, hence we need to add 2 to the PC as well. Finally, add "." for decimal. AddrIndex is always
        # used for the statement expression.
        #
        # Note that offset might be negative, hence a conversion from 2-compl is needed, NOT DONE YET
        #
        expr = as_expr.AddrIndex(None, as_expr.Expression(str(2 * self.offset + self.VM.get_PC() + 2) + "."))
        self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op, expr)
    def __str__(self):
        return "{:<8} {:>8}".format(self.op, self.offset if self.name is None else self.name)


class InstrSyscall(Instr):
    # indir, exit, fork, read, write, open, close, wait, creat, link, unlink, exec, chdir, time, makdir, chmod,
    # chown, break, stat, seek, tell, mount, umout, setuid, getuid, stime, fstat, mdate, stty, gtty, nice, signal

    def __init__(self, vm, op):
        super().__init__(vm, op)

        sys_word = self.VM.mem.read(self.VM.get_PC())
        self.syscall = instrLUT.get_syscall(sys_word & 0o0077)

        if self.syscall in ['exit', 'fork', 'close', 'wait', 'time', 'getpid',
                            'setuid', 'getuid', 'stime', 'fstat', 'mdate', 'nice']:
            self.par = []

        elif self.syscall in ['indir', 'unlink', 'chdir', 'break', 'umount', 'stty', 'gtty']:
            sys_addr = self.VM.mem.read(self.VM.get_PC() + 2)
            self.par = [
                {'addr': sys_addr, 'name': None}
            ]

        elif self.syscall in ['read', 'write', 'open', 'creat', 'link', 'exec',
                              'chmod', 'chown', 'stat', 'seek', 'signal']:
            sys_addr1 = self.VM.mem.read(self.VM.get_PC() + 2)
            sys_addr2 = self.VM.mem.read(self.VM.get_PC() + 4)
            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None}
            ]

        elif self.syscall in ['makdir', 'mount']:
            sys_addr1 = self.VM.mem.read(self.VM.get_PC() + 2)
            sys_addr2 = self.VM.mem.read(self.VM.get_PC() + 4)
            sys_addr3 = self.VM.mem.read(self.VM.get_PC() + 6)
            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None},
                {'addr': sys_addr3, 'name': None}
            ]

        self.size += len(self.par) * 2
        if self.syscall == 'gtty':
            self.size += 4

        self.stmt = as_stmt.SyscallStmt(self.VM.get_PC(), self.syscall)

        # 'sys indir' is an indirect system call
        # From UNIX v6 manual:
        #
        # SYNOPSIS
        #      (indir = 0.; not in assembler)
        #      sys indir; syscall
        #
        # DESCRIPTION
        #      The system call at the location syscall is executed.  Execution resumes after the indir call.
        #
        #      The main purpose of indir is to allow a program to store arguments in system calls and execute them
        #      out of line in the data segment.  This preserves the purity of the text segment.
        #
        #      If indir is executed indirectly, it is a no-op.  If the instruction at the indirect location is not
        #      a system call, the executing process will get a fault.
        #
        # An example:
        # 	mov	r4,0f
        # 1:
        # 	sys	indir; 9f
        # 	.data
        # 9:	sys	stat; 0:..; outbuf
        # 	.text
        #
        # In the example above, the value of register r4 is moved to the address of label 0f(orward).
        # The relocation counter ("..") allocates an empty memory position (1 word) when assembling.
        # Thus, to content of r4 is moved into this empty position, and we make a systemcall as:
        #   sys stat; r4; outbuf
        #
        # r4 is the address to a 0-terminated string which is the name-parameter to stat system-call
        # "sys stat" instruction have the value of 35090 (0o104422)
        #
        # When executing the self.stmt-statement object (sys indir), it will read the value at current PC (2882),
        # then use this value as an address and read the value 35090 (0o10422), which is the encoded value for sys stat.
        # It will then use value (35090) to look up the indirect statement (sys stat) in VM.prg.instructions-list.
        #
        # In reality, the binary code and its parameters are stored in the data-segment starting at position 2882.
        #
        # We can try to solve this in some ways:
        # 1. Try to keep as_stmt.py unchanged and adapt to its way of solving this through prg.instructions-list.
        #    Then we need to patch prg.instruction at position 35090 with a 'sys stat' instruction, and in the following
        #    positions patch for its parameters. All indirect calls to 'sys stat' can be made to the same position,
        #    however the parameters will vary.
        #    We could patch a 'sys stat'-stmt object at position 35090 in prg.instruction list, this could be made static
        #    as the code-word for 'sys stat' is always 35090 (we need to enlarge prg.instruction-list upto
        #    35090 entries though, in __init__ of vm, this list is filled with the parsed syntax tree of the source
        #    code of the binary file we are trying to execute. Of course, this is pointless, we might not even have
        #    the source code, and we will not make use of it when executed - Needs to be changed when initializing vm
        #    from aout.py).So the issue here is the actual values of the 2 'sys stat' parameters: name and buf.
        #    We know that the parameters are always two, so we would need to patch positions
        #    - 35090: with a 'sys stat'-stmt object
        #    - 35092: with the actual value of the address to the name-parameter
        #    - 35094: with the actual value of the address to the buf
        #
        #    The actual value for the name-parameter are stored in the binary file at memory location 2884, and the
        #    actual value of the buf-parameter are stored at memory location 2886. So we can patch these values into
        #    prg.instruction-list locations 35092 and 35094.
        #
        #   We would need to patch all other syscalls that can be called indirectly in the same way...
        #   ...and here we can have an issue that there will be an overlap between the sys call statements and parmeters
        #   For example, 'sys stat' and its parameters takes position 35090 - 35094, but another sys call might start
        #   on 35092...

        if self.syscall == 'indir':
            self.VM.prg.instructions[35090] = as_stmt.SyscallStmt(self.VM.get_PC(), 'stat')

            sys_addr1 = self.VM.mem.read(sys_addr + 2)
            self.VM.prg.instructions[35092] = sys_addr1

            sys_addr2 = self.VM.mem.read(sys_addr + 4)
            self.VM.prg.instructions[35094] = sys_addr2
    def __str__(self):
        par_str = ""
        for par in self.par:
            par_str += "{:>8}".format(par['name'] if par['name'] is not None else par['addr'])

        return "{:<8} {:>8}{} {:>8}".format(self.op, self.syscall, ";" if par_str != "" else "", par_str)


class InstrPrgCntrl(Instr):
    # JMP, JSR, RTS, MARK, SOB, BPT, IOT, RTI, RTT

    def __init__(self, vm, op):
        super().__init__(vm, op)

        self.dst_mode = (self.word & 0o0070) >> 3
        self.dst_reg  = (self.word & 0o0007)
        addr = self.VM.get_PC()
        self.dst_op = self.new_operand(self.dst_mode, self.dst_reg, addr)

        self.src_mode = Instr.REGISTER  # For these instructions, src operand mode is always register (0)
        if op == 'jsr':
            self.src_reg  = (self.word & 0o700) >> 6
        else:
            self.src_reg = 0

        self.src_op = self.new_operand(self.src_mode, self.src_reg, None)
        self.size += self.dst_op.size


        if op == 'jsr':
            # Adjusting dst_op.addr with -4 is an ugly patch and is due to the implementation of the jsr-instruction
            # in as_stmt.
            # Using the instruction "jsr fcreat" as an example. fcreat is a label at absolute address 154.
            # In the instruction, the word following jsr is -5014, which is relative to the address of pc + 4.
            # So if pc is 5164, we get (5164 + 4) - 5014 = 154, which is the absolute address of fcreat.
            #
            # In this file implementation the address of dst_op is (pc is 5164):
            #   - Read value at address pc + 2, which is 60522 (a negative number in two's complement => -5014)
            #   - Add 4 => 60526 => Convert to negative number => -5010
            #
            # In the as_stmt exc implementation of jsr:
            #   - pc is updated with 4, from 5164 to 5168
            #   - the address to jump to is calculated as pc - 5010 => 5168 - 5010 = 158, which is wrong!
            #
            # It is wrong because we have added 4 twice.
            # As I don't want to change the implementation in as_stmt (this implementation has been proven since long),
            # I need to patch the address with -4 below.
            #
            # Note that this is only valid for 'jsr'-instruction, not for jmp-instruction. For jmp, the implementation
            # in as_stmt the address to jump to is calculated as pc + supplied address.

            addr = str(self.dst_op.addr - 4) + "."  # Decimal
            reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
            dst_expr = self.new_expr(self.dst_mode, reg, addr)
            reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.src_reg]
            src_expr = self.new_expr(self.src_mode, reg, addr)
            self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op, src_expr, dst_expr)
        else:
            addr = str(self.dst_op.addr) + "."  # Decimal
            reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][self.dst_reg]
            dst_expr = self.new_expr(self.dst_mode, reg, addr)
            self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op, dst_expr)


    def __str__(self):
        if self.op == 'jsr':
            return "{: <8} {: >8}, {: >8}".format(self.op, str(self.src_op), str(self.dst_op))
        else:
            return "{:<8} {:>8}".format(self.op, str(self.dst_op))


class InstrMisc(Instr):
    # HALT, WAIT, RESET, MFPI, MTPI, CLC, CLV, CLZ, CLN, SEC, SEV, SEZ, SEN, SCC, CCC, NOP

    def __init__(self, vm, op):
        super().__init__(vm, op)
        self.stmt = as_stmt.KeywordStmt(self.VM.get_PC(), self.op)

    def __str__(self):
        return "{:<8}".format(self.op)


class AOut:
    def __init__(self, name):
        self.name = name
        with open(self.name, 'rb') as f:
            bytes = f.read()

        self.head = Head(bytes[0:16])

        fnList = sorted(glob.glob(sys.argv[2]))
        cmd = sys.argv[1] + ' ' + ''.join(elem + ' ' for elem in fnList)

        self.VM = asm.VM(cmd)
        self.VM.memory(bytes[self.head.size:])

        self.VM.prg.instructions.extend(35090*[None]) # Temp

        sym_start = (1 if self.head.get('reloc') else 2) * (self.head.get('txt') + self.head.get('data'))
        self.sym_table = SymTable(self.VM, sym_start, sym_start + self.head.get('sym'))

        for sym in self.sym_table:
            symbol = self.sym_table.get(sym)
            self.VM.named_labels.add(symbol['name'], symbol['value'])

    def exec(self):
        while True:
            instr = self.decode_instr()
            print(instr.stmt.dump(self.VM))
            instr.exec()

    def decode_instr(self):
        pc = self.VM.get_PC()
        word = self.VM.mem.read(pc)

        sym = self.sym_table.find(word)
        if sym:
            return InstrAddr(self.VM, sym)

        op = instrLUT.get(word)
        if op:
            if instrLUT.isSingle(op):
                instr = InstrSingle(self.VM, op)
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isDouble(op):
                instr = InstrDouble(self.VM, op)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isBranch(op):
                instr = InstrBranch(self.VM, op)
                instr.name = self.sym_table.find(2 * instr.offset + (pc + 2))
                return instr

            elif instrLUT.isSys(op):
                instr = InstrSyscall(self.VM, op)
                for par in instr.par:
                    # Note, syscall parameter addresses is always absolute,not relative PC
                    par['name'] = self.sym_table.find(par['addr'], abs=True)
                return instr

            elif instrLUT.isPrgCntrl(op):
                instr = InstrPrgCntrl(self.VM, op)
                instr.src_op.set_name(self.sym_table.find(instr.src_op.get_addr()))
                instr.dst_op.set_name(self.sym_table.find(instr.dst_op.get_addr()))
                return instr

            elif instrLUT.isMisc(op):
                return InstrMisc(self.VM, op)

            else:
                return None
        else:
            return None


    def dump(self):
        print(self.head)
        print(self.sym_table)
        print(2*"\n" + "--X--" + 2*"\n")

        spaces = 8 * " "

        txt_end = self.head.get('txt')
        pc = self.VM.get_PC()
        while pc < txt_end:
            instr = self.decode_instr()
            if instr is not None:
                word_str = f"{instr.word:#08o}"
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
                print(f"{pc:0<#8o} [{pc:0>8}] -> {{{word_str: <29}}} => {str(instr): <50}")

                self.VM.set_PC(pc + instr.size)
            else:
                self.VM.set_PC(pc + 2)

            pc = self.VM.get_PC()

    def exit(self):
        fn = "aout_trace.txt"
        print(f"Dumping trace to {fn}")
        self.VM.dump_trace(fn)


if __name__ == '__main__':
    instrLUT = ic.InstrLUT()

    aout = AOut("a.out")
    atexit.register(aout.exit)
    aout.exec()
