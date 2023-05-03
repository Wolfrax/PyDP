import sys
import asm
import instr_codes as ic
import util
import as_expr
import as_stmt
import glob
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
                ch = vm.mem.read(ind + i, 1)
                if ch != 0:
                    sym += chr(ch)

            type = vm.mem.read(ind + 8)
            type_str = self.types[type] if type in self.types else str(type)

            val = vm.mem.read(ind + 10)

            self.table[val] = {'name': sym, 'type': type, 'type_str': type_str, 'value': val}
            ind += 12


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

    def __init__(self, aout, op):
        self.aout = aout
        self.vm = aout.vm
        self.op = op
        self.stmt = None
        self.indir_PC = None

    def new_expr(self, mode, reg, expr=None, offset=0):
        reg = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'sp', 'pc'][reg] if reg is not None else reg
        if mode == self.REGISTER:
            return as_expr.AddrRegister(reg)
        elif mode == self.REGISTER_DEFERRED:
            return as_expr.AddrRegisterDeferred(reg)
        elif mode == self.AUTOINCREMENT:
            if reg == 'pc':
                expr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                expr = util.from_2_compl(expr, False)
                name = self.aout.sym_table.find(expr)
                return as_expr.AddrImmediate(as_expr.Expression(str(expr) + "."), sym_name=name)
            else:
                return as_expr.AddrAutoIncrement(reg)
        elif mode == self.AUTOINCREMENT_DEFERRED:
            if reg == 'pc':
                addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                expr = self.vm.mem.read(addr)
                expr = util.from_2_compl(expr, False)
                name = self.aout.sym_table.find(addr)
                return as_expr.AddrAbsolute(as_expr.Expression(str(expr) + "."), sym_name=name)
            else:
                return as_expr.AddrAutoIncrementDeferred(reg)
        elif mode == self.AUTODECREMENT:
            return as_expr.AddrAutoDecrement(reg)
        elif mode == self.AUTODECREMENT_DEFERRED:
            return as_expr.AddrAutoDecrementDeferred(reg)
        elif mode == self.INDEX:
            if reg == 'pc':
                addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                addr = util.from_2_compl(addr, False) + self.vm.get_PC() + 4
                name = self.aout.sym_table.find(addr)
                return as_expr.AddrRelative(as_expr.Expression(str(addr) + "."), sym_name=name)
            else:
                if reg is None:  # This is when we have a branch instruction, off set is in bytes so multiply by 2
                    expr = self.vm.get_PC() + 2 + (2 * offset)
                    name = self.aout.sym_table.find(expr)
                    return as_expr.AddrIndex(None, as_expr.Expression(str(expr) + "."), sym_name=name)
                else:
                    #expr = self.vm.register[reg] + self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                    #expr = self.vm.get_PC() + 2 + offset
                    expr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                    #expr = util.from_2_compl(expr, False)
                    name = self.aout.sym_table.find(self.vm.mem.read(self.vm.get_PC() + 2 + offset))
                    return as_expr.AddrIndex(reg, as_expr.Expression(str(expr) + "."), sym_name=name)
        elif mode == self.INDEX_DEFERRED:
            if reg == 'pc':
                addr = self.vm.get_PC() + 4 + self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                addr = util.from_2_compl(addr, False)
                #expr = self.vm.mem.read(addr)
                #expr = util.from_2_compl(expr, False)
                #name = self.aout.sym_table.find(expr)
                #return as_expr.AddrRelativeDeferred(as_expr.Expression(str(expr) + "."), sym_name=name)
                name = self.aout.sym_table.find(addr)
                return as_expr.AddrRelativeDeferred(as_expr.Expression(str(addr) + "."), sym_name=name)
            else:
                # Note, we add register value to address only when trying to find the symbol name.
                # When executing the statement that refers to the expression with the address, the value of
                # the register is added there.
                #addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                #addr = util.from_2_compl(addr, False)
                #name = self.aout.sym_table.find(addr + self.vm.register[reg])
                #return as_expr.AddrIndexDeferred(reg, as_expr.Expression(str(addr) + "."), sym_name=name)

                addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
                addr = util.from_2_compl(addr, False)
                name = self.aout.sym_table.find(addr + self.vm.register[reg])
                #return as_expr.AddrIndexDeferred(reg, as_expr.Expression(str(addr) + "."), sym_name=name)
                return as_expr.AddrIndex(reg, as_expr.Expression(str(addr) + "."), sym_name=name)

    def __str__(self):
        pass


class InstrSingle(Instr):
    # CLR(B), COM(B), INC(B), DEC(B), NEG(B), TST(B), ASR(B), ASL(B), ROR(B), ROL(B), SWAB, ADC(B), SBC(B), SXT
    #
    # Note, in aout-file, negative numbers are stored in 2's complement, for example -12 will have the bit-pattern
    # of value 244. So, we must treat all values as 2-complement when reading form memory and writing to memory.
    # When interpreting assembler-files (when running asm.py) we take the lazy way out and treat negative values as
    # negative values, i e not in 2's-complement format. But somewhere in the assembler file negative values are
    # transformed to 2's complement (not figured out where this is done however).
    # Below is a systematic review of instructions with respect to 2's complement.
    #
    # 2's compl handling, assuming dst-op has value 244 (which is -12 in 2's complement):
    # Notation:
    #   => is conversion to 2's compl,
    #   !=> is conversion from 2's compl
    #   --> is the operation when executing a statement,
    #   mem(x) sets memory to x.
    #
    # CLR(B): dst-op 244 --> mem(0) - OK!
    # COM(B): dst-op 244 => 244 --> ~244 = -245, mem(-245)
    #   Check this! Should be 244 ^ 0xFFF --> 11, if positive: 3 ^ 0xFF = 252
    # INC(B): dst-op 244 => 244 --> 244+1 = 245 !=> -11, mem(-11) (should be mem(1<<8 - 11 = 245))
    # DEC(B): dst-op 244 => 244 --> 244-1 = 243 !=> -13, mem(-13) (should be mem(1<<8 - 13 = 243))
    # NEG(B): dst-op 244 --> -244, mem(-244) NOT CORRECT! Should be 12!
    #   dst-op 244 !=> -12 -->  12 =>  12, mem(12)
    #   dst-op  12 !=>  12 --> -12 => 244, mem(244)
    # TST(B): dst-op 244, set N to 1 if MSB is set, true for 244 - OK!
    # ASR(B): dst-op 244 => 244 --> (244 >> 1) | (244 & 0x80) = 250 (which is 250 - 256 = -6) OK!
    # ASL(B): dst-op 244 => 244 --> 244 << 1 = 488, mem(488) NOT CORRECT! Should be 232!
    #   dst-op (244 << 1) & 0xFF = 232, mem (232). 232 - 256 = - 24 which is correct
    # ROR(B): dst-op 244 => 244 --> (244 >> 1) | ((244 & 1) << 7) = 122 - OK!
    # ROL(B): dst-op 244 => 244 --> (244 << 1) | (1 if 244 & 0x80 else 0) = 489, mem(489) NOT CORRECT! Should be 233
    #   dst-op ((244 << 1) | 1) & 0xFF = 233
    # SWAB: dst-op 244 => 244 --> ((244 & 0xFF) << 8) | ((244 & 0xFF00) >> 8) = 62464 - OK!
    # ADC(B): dst-op 244 => 244 --> 244 + Carry = 244 or 245 !=> -12 or -11 mem (-12 or -11) (should be 244 or 245)
    # SBC(B): NOT IMPlEMENTED!

    def __init__(self, aout, op):
        super().__init__(aout, op)

        dst_mode = (aout.word & 0o0070) >> 3
        dst_reg  = (aout.word & 0o0007)
        dst_expr = self.new_expr(dst_mode, dst_reg)
        self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, dst_expr)


class InstrDouble(Instr):
    # MOV(B), CMP(B), ADD, SUB, BIT(B), BIC(B), BIS(B), MUL, DIV, ASH, ASHC, XOR
    #
    # 2's complement
    #   MOV(B): Move from src to dst, all modes possible. Thus, 2's complement needs to be managed in mode
    #   CMP(B): Compare src-op and dst-op, all modes possible.
    #   Should convert operands from 2's complement for operation
    #   a) src-op 244 (-12) & dst-op 12 --> 244 - 12 = 232 (-24) OK
    #   b) src-op 12 & dst-op 244 --> 12 - 244 = -232 NOT OK
    #   c) src-op 245 (-11) & dst-op 244 (-12) => 245 & 244 --> 245 - 244 = 1 OK
    #   ADD: Add src-op and dst-op, all modes possible
    #   Should convert from 2's complement for operation
    #   a) src-op 244 (-12) & dst-op 12 --> 244 + 12 = 256 NOT OK
    #   b) src-op 12 & dst-op 244 (-12) --> 12 + 244 = 256 NOT OK
    #   c) src-op 245 (-11) & dst-op 244 (-12) --> 245 + 244 = 489 - NOT OK
    #   SUB: Subtract src from dst (dst - src), all modes possible
    #   Should convert from 2's complement for operation
    #   a) src-op 244 (-12) & dst-op 12 --> 12 - 244 = - 232 NOT OK
    #   b) src-op 12 & dst-op 244 (-12) --> 244 - 12 = 232 (-24) OK
    #   c) src-op 245 (-11) & dst-op 244 (-12) --> 244 - 245 = -1 OK
    #   BIT(B): Bit-wise logical AND between src-op and dst-op, all modes possible
    #   Should work in 2's complement
    #   a) src-op 244 (-12) & dst-op 12 --> 244 & 12 = 4 OK
    #   b) src-op 12 & dst-op 244 (-12) --> 12 & 244 = 4 OK
    #   c) src-op 245 (-11) & dst-op 244 (-12) --> 245 & 244 = 244 OK
    #   BIC(B): Bit clear, ~src & dst ((0xFF ^ src) & dst)
    # To be continued...let's see...

    def __init__(self, aout, op):
        super().__init__(aout, op)

        if op in ['mul', 'div', 'ash', 'ashc', 'xor']:
            reg = (aout.word & 0o0700) >> 6
            src_mode = (aout.word & 0o0070) >> 3
            src_reg  = (aout.word & 0o0007)
            dst_mode = Instr.REGISTER

            src_expr = self.new_expr(src_mode, src_reg)
            dst_expr = self.new_expr(dst_mode, reg)
            self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, src_expr, dst_expr)
        else:
            src_mode = (aout.word & 0o7000) >> 9
            src_reg  = (aout.word & 0o0700) >> 6
            dst_mode = (aout.word & 0o0070) >> 3
            dst_reg  = (aout.word & 0o0007)

            src_expr = self.new_expr(src_mode, src_reg)
            dst_expr = self.new_expr(dst_mode, dst_reg, offset=src_expr.addr_words * 2)
            self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, src_expr, dst_expr)


class InstrBranch(Instr):
    # BR, BNE, BEQ, BPL, BMI, BVC, BVS, BCC, BCS, BGE, BLT, BGT, BLE, BHI, BLOS, SOB
    #
    # 2's complement:
    # All Branch instructions OK wrt 2's complement
    # SOB: src-op 244 --> 244 - 1 = 243, reg(243). 243 == -13 OK!

    def __init__(self, aout, op):
        super().__init__(aout, op)

        if op == 'sob':
            src_mode = Instr.REGISTER
            src_reg = (aout.word & 0o0700) >> 6
            src_expr = self.new_expr(src_mode, src_reg)

            offset = -(aout.word & 0o0077)  # Offset is 6-bit positive number
            dst_mode = Instr.INDEX
            dst_expr = self.new_expr(dst_mode, None, None, offset)
            self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, src_expr, dst_expr)
        else:
            mode = Instr.INDEX
            offset = aout.word & 0o0377
            if offset & 0o0200:
                offset = -((offset & 0o0177 ^ 0o177) + 1)  # sign bit set, make offset negative through 2's complement
            expr = self.new_expr(mode, None, None, offset)
            self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, expr)


class InstrSyscall(Instr):
    # indir, exit, fork, read, write, open, close, wait, creat, link, unlink, exec, chdir, time, makdir, chmod,
    # chown, break, stat, seek, tell, mount, umout, setuid, getuid, stime, fstat, mdate, stty, gtty, nice, signal
    #
    # 2's complement:
    # read and write system calls use to/from 2's complement.
    #
    # write: if value to write is < 0: Convert to 2's complement. However, if memory values are already in
    #   2's complement the condition of < 0 will never be met.
    #   But, if val < 0 (not in 2's complement format), we currently convert to 2's complement (-12 will be 244)
    #   And write the lower byte first, then the higher byte. This is strange as a small negative number will only
    #   use 1 byte and not two!? <-- INVESTIGATE
    #
    # read: all bytes read are converted from 2's complement (ie 244 will be -12) then written to memory.
    #   This should be changed of making no conversion from 2's complement, simply read bytes and store in memory

    def __init__(self, aout, op):
        super().__init__(aout, op)

        self.syscall = instrLUT.get_syscall(aout.word & 0o0077)

        if self.syscall in ['exit', 'fork', 'close', 'wait', 'time', 'getpid',
                            'setuid', 'getuid', 'stime', 'fstat', 'mdate', 'nice']:
            self.par = []

        elif self.syscall in ['indir', 'unlink', 'chdir', 'break', 'umount', 'stty', 'gtty']:
            sys_addr = aout.vm.mem.read(aout.vm.get_PC() + 2)
            self.par = [
                {'addr': sys_addr, 'name': None}
            ]

        elif self.syscall in ['read', 'write', 'open', 'creat', 'link', 'exec',
                              'chmod', 'chown', 'stat', 'seek', 'signal']:
            sys_addr1 = aout.vm.mem.read(aout.vm.get_PC() + 2)
            sys_addr2 = aout.vm.mem.read(aout.vm.get_PC() + 4)
            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None}
            ]

        elif self.syscall in ['makdir', 'mount']:
            sys_addr1 = self.vm.mem.read(self.vm.get_PC() + 2)
            sys_addr2 = self.vm.mem.read(self.vm.get_PC() + 4)
            sys_addr3 = self.vm.mem.read(self.vm.get_PC() + 6)

            self.par = [
                {'addr': sys_addr1, 'name': None},
                {'addr': sys_addr2, 'name': None},
                {'addr': sys_addr3, 'name': None}
            ]

        operands = []
        for par in self.par:
            par['name'] = aout.sym_table.find(par['addr'])
            if par['name'] is None:
                operands.append(par['addr'])
            else:
                operands.append(par['name'])

        self.stmt = as_stmt.SyscallStmt(self.vm.get_PC(), self.syscall, operands)

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
        # In the example above, the value of register r4 is moved to the address of label 0f.
        # The relocation counter ("..") have allocated an empty memory position (1 word) when assembling.
        # Thus, the content of r4 is moved into this empty position, and we make a system call as:
        #   sys stat; r4; outbuf
        #
        # r4 is the address to a 0-terminated string which is the name-parameter to stat system-call
        #
        # When executing the stmt-statement object (sys indir), it will read the value at current PC (2882) and
        # set the PC to this value. The next iteration will decode an instruction at this address and execute it.
        # However, when executed, the PC needs to be restored so execution continue after the sys indir call.

        if self.syscall == 'indir':
            self.indir_PC = self.vm.get_PC() + 4  # The return address after executing sys indir


class InstrPrgCntrl(Instr):
    # JMP, JSR, RTS, MARK, BPT, IOT, RTI, RTT
    #
    # 2's complement:
    # JMP: Will jump to an address which is not negative.
    #   JMP can be made in all addressing modes except 0 (Register). See modes for managing 2's complements
    # JSR: Same comment as for JMP
    # RTS: 2's complement no issue
    # MARK: Not implemented
    # BPT: Not implemented
    # IOT: Not implemented
    # RTI: Not implemented
    # RTT: Not implemented
    #
    # 2's complement for addressing modes.
    # In general an address is the value for a location which cannot be negative by definition.
    # However, doing address arithmetics operands can have negative values.
    #   Mode 0 (Register): Register contains operand - 2's complement no issue
    #       This is handled by the actual instruction, eg ADD RO, R1, where R0 = 1 and R1 = 244 (-12) => R1 = 245 (-11)
    #   Mode 1 (Register deferred): Register contains address - 2's complement no issue (address not negative)
    #   Mode 2 (Auto-increment): Register contains address - 2's complement no issue (address not negative)
    #   Mode 3 (Auto-increment deferred): Register contains address of address - 2's complement no issue
    #   Mode 4 (Auto-decrement): Register contains address - 2's complement no issue
    #   Mode 5 (Auto-decrement deferred): Register contains address of address - 2 2's complement no issue
    #       NB: In this mode the first address is decremented with 2, then it points to the next address.
    #       If the original address is 0, the decrement would result in a negative address, which is illegal
    #   Mode 6 (Index): Register (which contain a value that can be negative) is added to X which is located at PC + 2
    #       If R0 = 244 (-12) and we execute JMP 100.(R0) (100 is decimal), we should jump to address 100 - 12 = 88
    #       Thus, we need to manage 2's complement when doing the addition (R) + X.
    #   Mode 7 (Index deferred): (R) + X is address of address. Same comment as for Mode 6 (Index)
    #       Register might include a negative value.
    #
    #   PC addressing
    #   Mode 2 (Immediate): Operand follow instruction - 2's complement no issue
    #   Mode 3 (Absolute): Address follow instruction - 2's complement no issue
    #   Mode 6 (Relative): Address follow instruction + PC + 4 - 2's complement no issue
    #   Mode 7 (Relative deferred):  Address follow instruction + PC + 4 which is a new address - 2's complement no issue
    #


    def __init__(self, aout, op):
        super().__init__(aout, op)

        src_expr = dst_expr = None
        if op == 'jmp':
            src_mode = (aout.word & 0o0070) >> 3
            src_reg = (aout.word & 0o0007)
            src_expr = self.new_expr(src_mode, src_reg)
            dst_expr = None
        elif op == 'jsr':
            src_mode = Instr.REGISTER
            src_reg  = (aout.word & 0o0700) >> 6
            dst_mode = (aout.word & 0o0070) >> 3
            dst_reg  = (aout.word & 0o0007)
            src_expr = self.new_expr(src_mode, src_reg)
            dst_expr = self.new_expr(dst_mode, dst_reg)
        elif op == 'rts':
            src_mode = Instr.REGISTER
            src_reg = aout.word & 0o0007
            src_expr = self.new_expr(src_mode, src_reg)
            dst_expr = None
        elif op in ['mark', 'bpt', 'iot', 'rti', 'rtt']:
            assert False, f"{op} not implemented"

        self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op, src_expr, dst_expr)

class InstrMisc(Instr):
    # HALT, WAIT, RESET, MFPI, MTPI, CLC, CLV, CLZ, CLN, SEC, SEV, SEZ, SEN, SCC, CCC, NOP
    #
    # 2's complement:
    #   HALT: Not implemented
    #   WAIT: Not implemented
    #   RESET: Not implemented
    #   MFPI: Not implemented
    #   MTPI: Not implemented
    #   CLC, CLV, CLZ, CLN, SEC, SEN, SCC, CCC, NOP: Not implemented
    #   SEV: Set V - no issue with 2's complement

    def __init__(self, aout, op):
        super().__init__(aout, op)
        if op == 'sev':
            self.stmt = as_stmt.KeywordStmt(self.vm.get_PC(), self.op)
        else:
            assert False, f"{op} not implemented"


class AOut:
    def __init__(self, name):
        self.name = name
        self.word = None
        with open(self.name, 'rb') as f:
            bytes = f.read()

        self.head = Head(bytes[0:16])

        fnList = sorted(glob.glob(sys.argv[2]))
        cmd = sys.argv[1] + ' ' + ''.join(elem + ' ' for elem in fnList)

        self.vm = asm.VM(cmd,exec=True)
        self.vm.memory(bytes[self.head.size:])

        sym_start = (1 if self.head.get('reloc') else 2) * (self.head.get('txt') + self.head.get('data'))
        self.sym_table = SymTable(self.vm, sym_start, sym_start + self.head.get('sym'))

        for sym in self.sym_table:
            symbol = self.sym_table.get(sym)
            self.vm.named_labels.add(symbol['name'], symbol['value'])

    def exec(self):
        instr = None
        while True:
            PC = instr.indir_PC if instr and instr.indir_PC else None

            instr = self.decode_instr()
            print(instr.stmt.dump(self.vm))
            self.vm.trace(instr.stmt)
            instr.stmt.exec(self.vm)
            self.vm.post_trace()

            # If syscall indir is executed, we need to restore PC
            if PC:
                self.vm.set_PC(PC)

    def decode_instr(self):
        self.word = self.vm.mem.read(self.vm.get_PC())

        op = instrLUT.get(self.word)

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


    def exit(self):
        fn = "aout_trace.txt"
        print(f"Dumping trace to {fn}")
        self.vm.dump_trace(fn)


if __name__ == '__main__':
    instrLUT = ic.InstrLUT()

    aout = AOut("a.out")
    atexit.register(aout.exit)
    aout.exec()
