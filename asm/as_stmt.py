import os
import stat
import sys
import util
import as_expr


class Stmt:
    def __init__(self, lineno, expr):
        self.lineno = lineno
        self.loc = None
        self.expr = expr

    def __str__(self):
        return str(self.expr)

    def dump(self, vm):
        return str(self)

    def type(self):
        return type(self).__name__

    def exec(self, vm):
        pass

    def assemble(self, vm):
        pass

    def resolve(self, vm):
        pass


class LabelStmt(Stmt):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr[:-1])

    def assemble(self, vm):
        # For labels, we identify if it is numeric or named and register this in the right table
        # location counter is not updated as the label is not executed as an instruction, it is only a location
        # When an instruction is referring to a label (eg "jmp start"), the instruction will lookup the location in
        # the table. For example "start" has the value 10 in the named_labels table, "jmp" will set the
        # program counter to 10

        if self.expr.isdigit():
            vm.numeric_labels.add(self.expr, vm.location_counter)
        else:
            vm.named_labels.add(self.expr, vm.location_counter)


class ExpressionStmt(Stmt):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

    def assemble(self, vm):
        # ExpressionStmt's are typically statements like: outbuf, 512., 9f etc.
        # * outbuf: A named label, hence a symbolic name for a location
        # * 512.: Decimal value 512
        # * 9f: Numeric label 9 in forward direction relative current pc
        # * 'x or '/n: Character constant, one byte stored in memory location, null-padded if needed
        #
        # This type of Statement occupies memory, 2 bytes - hence the location counter is updated by 2
        # Examples are:
        #   "jsr r5 fcreat; a.tmp1"
        #   a.tmp1 is the ExpressionStmt, which is a label (symbolic name for a location, for example 100)
        #   When jsr is executed, r5 will have the value of a.tmp1 (100). The label can be constructed like this:
        #   "a.tmp1: </tmp/atm1a\0>" - a string of 11 bytes starting at location 100. Thus, a statement following "jsr"
        #   like "mov(r5)+,r4", will read the value at location 100 (ie the ordinal value of "/", 1 byte - 47) will be
        #   moved to r4. The location of a label is stored in named_labels or numeric_labels, not written to memory
        #
        #   "sys write; outbuf; 512."
        #   The ExpressionStmt's are "outbuf" and "512.". The implementation of the system call "write" will use these
        #   as parameter. outbuf is a label, thus a name for a location (eg 200). 512. is a decimal constant.
        #   If current value of location counter is 10, then "sys write" will be on this location, "outbuf" on
        #   location 12, with the value 200 stored in named_lables (not emory), and "512." on location 14 with value
        #   "512" written in memory.
        #
        #   "sys	indir; 9f"
        # 	".data"
        #   "9: sys	write; 0:0; 1:0"
        #   We are making an indirect system call to "write" (located in the data-segment, instead
        #   of text-segment) and is referring to this by the forward numeric label "9f". We look up the label "9" in
        #   numeric_labels and choose the one closest to the current value of pc in forward direction. Before that an
        #   instruction like "mov r4, 0f" and "move r0, 1f" has been executed. The first instruction will move the
        #   location of the string to write to the file, the second is the number of characters to write.
        #   We look up the locations of "9f", "0f" and "1f" labels in numeric_labels table and for "0" and "1" update
        #   the memory locations with the values in r4 and r0 respectively.
        #

        self.loc = vm.location_counter

        expr = self.expr.get(vm)

        if expr.isdigit():  # octal number
            expr = int(expr.replace("8", "10").replace("9", "11"), 8)
        elif expr[:-1].isdigit() and expr[-1] == ".":  # Decimal number
            expr = int(expr[:-1])
        elif expr[0] == '-' and expr[1:-1].isdigit() and expr[-1] == ".":
            expr = int(expr[:-1])

        if isinstance(expr, int):
            vm.mem.write(self.loc, expr)

        elif isinstance(expr, str):
            if len(expr) >= 2 and expr[0] == "'":  # Single character constant, eg 'x or '\n
                # Single char constants are stored in the statement (1 word = 2 bytes), with null-padding
                const = self.expr.eval(vm)
                const = const.replace('\\n', '\n')
                vm.mem.write(self.loc, ord(const[1]), byte=True)
                vm.mem.write(self.loc + 1, 0, byte=True)

        # Note, ExpressionStmt's that is a label (for example 'aexit' or '9f'), the location for the label is possibly
        # not known yet. For example, 'aexit' is stated, but the 'aexit:'-label statement is further ahead.
        # The locations for labels are written to memory in a second pass, where the resolve method is called.

        vm.location_counter += 2
        vm.variables.add(".", vm.location_counter)

    def resolve(self, vm):
        expr = self.expr.get(vm)

        var = vm.variables.get(expr)
        if var:
            vm.mem.write(self.loc, var)
            return

        lbl = vm.named_labels.get(expr)
        if lbl:
            vm.mem.write(self.loc, lbl)
            return

        if expr[:-1].isdigit() and (expr[-1] == 'f' or expr[-1] == 'b'):
            # We want to find the statement that the numeric label statement is referring to.
            # For example:
            #       sys indir; 9f               1168: [204] [206]
            #       .data                             [208]
            #   9:  sys stat; 0:..; outbuf            [210][212][214][216][218]
            #       .text
            #
            #   Above is interpreted as:
            #       prg.instructions[204] = sys indir, the value 204 is written on memory location 1168
            #       prg.instructions[206] = 9f
            #       prg.instructions[208] = .data
            #       prg.instructions[210] = 9:
            #       prg.instructions[212] = sys stat
            #       ...etc
            #
            # On memory location 1170 (the one following 1168, where the value 204 is written) we want to write the
            # memory location that contain the program index for "sys stat" (this is what "9:" is referring to) - 212.
            # "sys stat" memory location is located in the data-segment, location 4948 (due to the
            # ".data" pseudo statement).
            # So, memory[1170] = 4948 and memory[4948] = 212, and prg.instructions[212] = "sys stat".
            #
            # The logic below is:
            #   - get the array for the numeric label "9" into numeric_lbls variable, these are memory locations
            #   - for each value/memory location in numeric_lbls, read the memory value, these are indexes into
            #     prg.instructions, and store in variable lbl_instr_locations.
            #   - for forward labels, find the value closest, but bigger than the current statements index,
            #     into instr_loc variable. Example:
            #       current statement index is 206, the closest but bigger value in lbl_instr_locations is 212.
            #       Using the index for value 212 in lbl_instr_locations, that is 4, we look up the 4th value in
            #       numeric_lbls.
            #
            #       numeric_lbls[9] = [4918, 496, 4942, 4948, 4954, 4968, 4972]
            #       lbl_instr_locations = [46, 154, 178, 212, 234, 804, 1082]
            #       instr_loc = 212, value closest but bigger than 206
            #       val = numeric_lbls[index for 212 in lbl_instr_locations = 4] = 4948
            #       write 4948 on self.loc = 1170
            #

            instr = None
            label_prg_index = None
            this_prg_index = vm.prg.instructions.index(self)
            if expr[-1] == 'f':
                for instr in vm.prg.instructions[this_prg_index:]:
                    if instr is None:
                        continue

                    if instr.type() == 'LabelStmt' and instr.expr == expr[0]:
                        label_prg_index = vm.prg.instructions.index(instr) + 2
                        break
                for instr in vm.prg.instructions[label_prg_index:]:
                    if instr is None:
                        continue

                    if instr.type() != 'LabelStmt':
                        break
            else:
                for instr in vm.prg.instructions[this_prg_index::-1]:
                    if instr is None:
                        continue

                    if instr.type() == 'LabelStmt' and instr.expr == expr[0]:
                        label_prg_index = vm.prg.instructions.index(instr) - 0  # 2
                        break
                for instr in vm.prg.instructions[label_prg_index:]:
                    if instr is None:
                        continue

                    if instr.type() != 'LabelStmt':
                        break
            vm.mem.write(self.loc, instr.loc)


class StringStmt(Stmt):
    def __init__(self, lineno, expr):
        s = expr[1:-1]  # skip "<" and ">" markers
        s = s.replace("\\0", "\x00")
        s = s.replace("\\n", "\n")

        super().__init__(lineno, s)

    def assemble(self, vm):
        # String statements, for example, <abc\0> (4 bytes, brackets not included), each character is stored on
        # consecutive memory locations (thus, location counter might be odd as a result).

        self.loc = vm.location_counter
        for ch in self.expr:
            vm.mem.write(vm.location_counter, ord(ch), byte=True)
            vm.location_counter += 1
        vm.variables.add(".", vm.location_counter)


class KeywordStmt(Stmt):
    def __init__(self, lineno, expr, src=None, dst=None):
        super().__init__(lineno, expr)
        self.src = src
        self.dst = dst
        self.address = None

    def dump(self, vm):
        lineno_str = str(self.lineno) + ": "
        kw_str = str(self)
        byte = self.expr[-1] == 'b' and self.expr != 'swab'  # Assume byte-type keywords ends with 'b', except swab

        if self.src is not None and self.dst is not None:
            self.src.pre_dump_update(vm, byte=byte)
            self.dst.pre_dump_update(vm, byte=byte)

            if self.expr in ['jsr', 'sob']:
                dst_str = str(self.dst.eval_address(vm))
            else:
                dst_str = str(self.dst.eval(vm, byte=False))


            dump_str = "{:<8}{:<30}{:<15}{:<15}".format(lineno_str, kw_str,
                                                        "src: " + str(self.src.eval(vm, byte=False)),
                                                        "dst: " + dst_str)

            self.src.post_dump_update(vm, byte=byte)
            self.dst.post_dump_update(vm, byte=byte)

            return dump_str

        if self.src is not None:
            self.src.pre_dump_update(vm, byte=byte)

            if self.expr in ['jmp', 'br', 'bcs', 'bne', 'bec', 'bes', 'blos', 'bpl', 'bge',
                             'beq', 'bhi', 'blo', 'blt', 'bgt', 'ble', 'bhis', 'bcc', 'bvs', 'bmi']:
                src_str = str(self.src.eval_address(vm, byte=byte))
            else:
                src_str = str(self.src.eval(vm, byte=byte))

            dump_str = "{:<8}{:<30}{:<15}{:<15}".format(lineno_str,
                                                        kw_str,
                                                        "src: " + src_str,
                                                        "")

            self.src.post_dump_update(vm, byte=byte)

            return dump_str

        else:
            return "{:<8}{:<30}{:<15}{:<15}".format(str(self.lineno), self.expr, "", "")

    def __str__(self):
        if self.src is not None and self.dst is not None:
            return self.expr + " " + str(self.src) + ", " + str(self.dst)
        if self.src is not None:
            return self.expr + " " + str(self.src)
        else:
            return self.expr

    def assemble(self, vm):
        # KeywordStmt's can be "mov r0, r1" or "jsr start" etc. They normally update location counter by 2.
        # However, for certain modes of the src/dst operators additional updates is needed, this is returned by
        # the operators words-method. Nothing is written to memory for keywords.

        self.loc = vm.location_counter
        vm.mem.write(self.loc, vm.prg.instructions.index(self))
        vm.location_counter += 2

        if self.src:
            if self.expr not in ['br', 'bcs', 'bne', 'bec', 'bes', 'blos', 'bpl', 'bge',
                                 'beq', 'bhi', 'blo', 'blt', 'bgt', 'ble', 'bhis', 'bcc', 'bvs', 'bmi']:
                vm.location_counter += (self.src.words() * 2)

        if self.dst:
            if self.expr not in ['sob']:
                vm.location_counter += (self.dst.words() * 2)

        vm.variables.add(".", vm.location_counter)

    def _exec_simple(self, vm):
        PSW = vm.PSW.get()
        if self.expr == 'sev':
            PSW['V'] = 1
        else:
            assert False, "exec_simple, not implemented {}".format(self.expr)
        vm.PSW.set(PSW)
        vm.incr_PC()

    def _exec_single(self, vm):
        byte = self.expr in ['rorb', 'rolb', 'adcb', 'negb', 'tstb', 'incb', 'decb', 'clrb', 'comb', 'aslb', 'asrb']
        msb = 0x80 if byte else 0x8000

        self.src.pre_addr_update(vm, byte=byte)

        PSW = vm.PSW.get()

        if self.expr in ['jmp', 'br', 'bcs', 'bne', 'bec', 'bes', 'blos', 'bpl', 'bge',
                         'beq', 'bhi', 'blo', 'blt', 'bgt', 'ble', 'bhis', 'bcc', 'bvs', 'bmi']:
            # branch and jump instructions
            op = self.src.eval_address(vm)

            if self.expr == 'jmp':
                do_branch = True
            elif self.expr == 'br':
                do_branch = True
            elif self.expr in ['bcs', 'bes', 'blo']:
                do_branch = PSW['C'] == 1
            elif self.expr == 'bne':
                do_branch = PSW['Z'] == 0
            elif self.expr == 'bec':
                do_branch = PSW['C'] == 0
            elif self.expr == 'blos':
                do_branch = (PSW['C'] | PSW['Z']) == 1
            elif self.expr == 'beq':
                do_branch = PSW['Z'] == 1
            elif self.expr == 'bhi':
                do_branch = (PSW['C'] | PSW['Z']) == 0
            elif self.expr == 'blt':
                do_branch = (PSW['N'] ^ PSW['V']) == 1
            elif self.expr == 'bge':
                do_branch = (PSW['N'] ^ PSW['V']) == 0
            elif self.expr == 'bgt':
                do_branch = (PSW['Z'] | (PSW['N'] ^ PSW['V'])) == 0
            elif self.expr == 'ble':
                do_branch = (PSW['Z'] | (PSW['N'] ^ PSW['V'])) == 1
            elif self.expr in ['bhis', 'bcc']:
                do_branch = PSW['C'] == 0
            elif self.expr == 'bpl':
                do_branch = PSW['N'] == 0
            elif self.expr == 'bvs':
                do_branch = PSW['V'] == 1
            elif self.expr == 'bmi':
                do_branch = PSW['N'] == 1
            else:
                do_branch = False

            vm.set_PC(op) if do_branch else vm.incr_PC()

        elif self.expr == 'rts':
            # Return from subroutine
            op = self.src.eval(vm)
            vm.set_PC(op)
            self.src.set(vm, vm.stack_pop())

        elif self.expr in ['ror', 'rorb']:
            # Rotate right, shift operand right, move the lowest bit in carry
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF
            carry = PSW['C']
            PSW['C'] = val & 1

            if byte:
                # The manual is ambiguous on byte operation, when general registers is used, byte operates on bit 0 - 7
                val = (val >> 1) | ((val & 1) << 7)
            else:
                val = (val >> 1) | (carry << 15)

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0

            PSW['V'] = PSW['N'] ^ PSW['C']

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['rol', 'rolb']:
            # Rotate right, shift operand left, move the lowest bit in carry
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF
            carry = val & msb
            PSW['C'] = carry

            if byte:
                # The manual is ambiguous on byte operation, when general registers is used, byte operates on bit 0 - 7
                val = ((val & 0xFF) << 1) | carry
            else:
                val = (val << 1) | carry

            self.src.set(vm, val, byte=False)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['C'] = carry
            PSW['V'] = PSW['N'] ^ PSW['C']

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['adc', 'adcb']:
            # Add carry
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            val = val + PSW['C']
            overflow = val == msb

            if byte:
                carry = val == 0x100
            else:
                carry = val == 0x10000

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['C'] = 1 if carry else 0
            PSW['V'] = 1 if overflow else 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['neg', 'negb']:
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            val = util.from_2_compl(val, byte)
            val = -val
            val = util.to_2_compl(val, byte)

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['C'] = 0 if val == 0 else 1
            PSW['V'] = 1 if val & msb else 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['tst', 'tstb']:
            # Test, set condition flags
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = 0
            PSW['C'] = 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['inc', 'incb']:
            # Increment
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            overflow = val == (msb - 1)
            val += 1
            val = val & 0xFF if byte else val & 0xFFFF

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = 1 if overflow else 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['dec', 'decb']:
            # Decrement
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            overflow = val == msb
            val -= 1

            val = util.to_2_compl(val, byte=byte)
            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = 1 if overflow else 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['clr', 'clrb']:
            # Clear
            self.src.set(vm, 0, byte=byte)

            PSW['N'] = 0
            PSW['Z'] = 1
            PSW['V'] = 0
            PSW['C'] = 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr == 'swab':
            # Swap bytes
            val = self.src.eval(vm)

            low_byte = val & 0xFF
            high_byte = val & 0xFF00
            val = (low_byte << 8) | (high_byte >> 8)
            self.src.set(vm, val)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val & 0xFF == 0 else 0
            PSW['V'] = 0
            PSW['C'] = 0

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['com', 'comb']:
            # Complement
            val = self.src.eval(vm)

            val = ~val
            val = util.to_2_compl(val, byte)

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = 0
            PSW['C'] = 1

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['asl', 'aslb']:
            # Arithmetic shift left
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            if byte:
                # The manual is ambiguous on byte operation, when general registers is used, byte operates on bit 0 - 7
                PSW['C'] = (val & msb) >> 7
            else:
                PSW['C'] = (val & msb) >> 15

            val <<= 1

            self.src.set(vm, val, byte=False)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = PSW['N'] ^ PSW['C']

            vm.incr_PC(1 + self.src.words())

        elif self.expr in ['asr', 'asrb']:
            # Arithmetic shift right
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF

            PSW['C'] = val & 1

            val = (val >> 1) | (val & msb)

            self.src.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = PSW['N'] ^ PSW['C']

            vm.incr_PC(1 + self.src.words())

        else:
            assert False, "exec_single, not implemented {}".format(self.expr)

        self.src.post_addr_update(vm, byte=byte)
        vm.PSW.set(PSW)

    def _exec_double(self, vm):
        byte = self.expr in ['movb', 'cmpb', 'bicb', 'bisb', 'bitb']
        msb = 0x80 if byte else 0x8000
        max = 0xFF if byte else 0xFFFF

        self.src.pre_addr_update(vm, byte=byte)
        self.dst.pre_addr_update(vm, byte=byte)

        PSW = vm.PSW.get()

        if self.expr in ['mov', 'movb']:
            # Move
            val = self.src.eval(vm)
            val &= 0xFF if byte else 0xFFFF
            if self.expr == 'movb' and val & msb and isinstance(self.dst, as_expr.AddrRegister): # sign extend
                val = 0xFF00 | val
                self.dst.set(vm, val)
            else:
                self.dst.set(vm, val, byte=byte)

            PSW['N'] = 1 if val & msb else 0
            PSW['Z'] = 1 if val == 0 else 0
            PSW['V'] = 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())
        elif self.expr in ['cmp', 'cmpb']:
            # Compare
            src = self.src.eval(vm)
            src &= 0xFF if byte else 0xFFFF

            dst = self.dst.eval(vm)
            dst &= 0xFF if byte else 0xFFFF

            res = src - dst

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 1 if ((src ^ dst) & msb) and not ((dst ^ res) & msb) else 0
            PSW['C'] = 1 if src < dst else 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr == 'jsr':
            # Jump subroutine
            pc_val = vm.incr_PC(1 + self.src.words() + self.dst.words())

            src = self.src.eval(vm)
            dst = self.dst.eval_address(vm)

            vm.stack_push(src)
            self.src.set(vm, pc_val)

            vm.set_PC(dst)

        elif self.expr == 'add':
            # Add :-)
            src = self.src.eval(vm)
            dst = self.dst.eval(vm)

            res = src + dst
            res = util.to_2_compl(res, byte=False)

            self.dst.set(vm, res)

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 1 if not ((src ^ dst) & msb) and ((dst ^ res) & msb) else 0
            PSW['C'] = 1 if res >= 0xFFFF else 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr == 'sub':
            # Subtract
            src = self.src.eval(vm)
            dst = self.dst.eval(vm)

            res = dst + ~src + 1
            res = util.to_2_compl(res, byte=False)

            self.dst.set(vm, res)

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 1 if ((src ^ dst) & msb) and not ((dst ^ res) & msb) else 0
            PSW['C'] = 1 if src > dst else 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['mul', 'mpy']:
            # Multiply
            src = self.src.eval(vm)

            reg_list = list(vm.register)
            dst_reg = reg_list[reg_list.index(self.dst.reg)]
            dst = vm.register[dst_reg]

            res = dst * src
            res = util.to_2_compl(res, byte=False)

            if reg_list.index(self.dst.reg) % 2 == 0:
                vm.register[dst_reg + 1] = (res & 0xFFFF0000) >> 16
            vm.register[dst_reg] = res & 0xFFFF

            PSW['N'] = 1 if res & 0x80000000 else 0
            PSW['Z'] = 1 if (res & 0xFFFFFFFF) == 0 else 0
            PSW['V'] = 0
            PSW['C'] = 1 if res < (1 << 15) or res >= ((1 << 15) - 1) else 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['div', 'dvd']:
            # Divide
            reg_list = list(vm.register)

            src = self.src.eval(vm)

            dst = vm.register[reg_list[reg_list.index(self.dst.reg) + 1]]

            if src == 0:
                PSW['C'] = 1
            else:
                qt, mod = divmod(dst, src)
                qt = util.to_2_compl(qt, byte=False)
                mod = util.to_2_compl(mod, byte=False)

                self.dst.set(vm, qt)
                vm.register[reg_list[reg_list.index(self.dst.reg) + 1]] = mod

                PSW['N'] = 1 if qt & msb else 0
                PSW['Z'] = 1 if qt == 0 else 0
                PSW['V'] = 0
                PSW['C'] = 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr == 'sob':
            # Subtract 1 and branch if not 0
            src = self.src.eval(vm)
            src -= 1
            src = util.to_2_compl(src)
            self.src.set(vm, src)

            if src != 0:
                dst_val = self.dst.eval_address(vm)
                vm.set_PC(dst_val)
            else:
                vm.incr_PC()

        elif self.expr == 'ashc':
            # Arithmetic shift combined
            src_val = self.src.eval(vm)
            dst_val = self.dst.eval(vm)

            shift = src_val & 0x3F  # Only six bits are valid

            reg_list = list(vm.register)
            reg_low = reg_list[reg_list.index(self.dst.reg) + 1]
            reg_low_val = vm.register[reg_low]

            if shift & 0x20:  # Right shift
                shift = (0x3F ^ src_val) + 1

                high_carry = dst_val & 0x0001

                res_low = ((high_carry << 16) | (reg_low_val >> shift)) & 0xFFFF
                res_high = (dst_val >> shift) & 0xFFFF
                res = res_high << 16 | res_low

                vm.register[reg_low] = res_low
                self.dst.set(vm, res_high)

                carry = 1 if reg_low_val & 0x0001 else 0
            else:  # left shift
                low_carry = reg_low_val & 0x8000

                res_high = ((dst_val << shift) | low_carry) & 0xFFFF
                res_low = (reg_low_val << shift) & 0xFFFF
                res = res_high << 16 | res_low

                vm.register[reg_low] = res_low
                self.dst.set(vm, res_high)
                carry = 1 if dst_val & 0x8000 else 0

            PSW['N'] = 1 if res & 0x80000000 else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 1 if util.xor(res & 0x80000000, dst_val & 0x80000000) else 0
            PSW['C'] = carry

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['als', 'ash']:
            # Arithmetic shift left
            src_val = self.src.eval(vm)
            dst_val = self.dst.eval(vm)

            shift = src_val & 0x3F  # Only six bits are valid

            if shift & 0x20:  # Right shift
                shift = (0x3F ^ src_val) + 1
                carry = dst_val & 0x01
                res = dst_val >> shift
            else:
                carry = 1 if dst_val & 0x8000 else 0
                res = dst_val << shift

            self.dst.set(vm, res)

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 1 if util.xor(res & 0x8000, dst_val & 0x8000) else 0
            PSW['C'] = carry

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['bic', 'bicb']:
            # Bit clear
            src = self.src.eval(vm)
            src &= 0xFF if byte else 0xFFFF

            dst = self.dst.eval(vm)
            dst &= 0xFF if byte else 0xFFFF

            res = (max ^ src) & dst
            self.dst.set(vm, res, byte=byte)

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['bis', 'bisb']:
            # Bit set
            src = self.src.eval(vm)
            src &= 0xFF if byte else 0xFFFF

            dst = self.dst.eval(vm)
            dst &= 0xFF if byte else 0xFFFF

            res = src | dst
            self.dst.set(vm, res, byte=byte)

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        elif self.expr in ['bit', 'bitb']:
            # Bit and
            src = self.src.eval(vm)
            src &= 0xFF if byte else 0xFFFF

            dst = self.dst.eval(vm)
            dst &= 0xFF if byte else 0xFFFF

            res = src & dst

            PSW['N'] = 1 if res & msb else 0
            PSW['Z'] = 1 if res == 0 else 0
            PSW['V'] = 0

            vm.incr_PC(1 + self.src.words() + self.dst.words())

        else:
            assert False, "exec_double, not implemented {}, lineno: {}".format(self.expr, self.lineno)

        self.src.post_addr_update(vm, byte=byte)
        self.dst.post_addr_update(vm, byte=byte)
        vm.PSW.set(PSW)

    def exec(self, vm):
        # NB! Set the location counter value when we execute this instruction
        # This is because operands to instructions might use the location counter, for example "br .+4"
        # eval_address will resolve this (using BinaryExpression) and lookup "." as a variable, hence we need to
        # set the value for every instruction.
        vm.variables.add('.', self.loc)

        if not self.src and not self.dst:
            self._exec_simple(vm)
        elif self.src and not self.dst:
            self._exec_single(vm)
        elif self.src and self.dst:
            self._exec_double(vm)
        else:
            assert False, "KeywordStmt, Unknown statement type: {}".format(str(self))


class AssignmentStmt(Stmt):
    def __init__(self, lineno, left, right):
        super().__init__(lineno, None)
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.left) + "=" + str(self.right)

    def assemble(self, vm):
        # AssignmentStmt's are "a = 1". The left operator is added to variables together with the assigned value.
        # One case of assignments can be to assign the location operator ("."), like ". = . + 2" (location operator
        # is updated with 2 in the code). The "right.eval(vm)"-call will take of unary/binary expressions and return
        # a value.
        # Note that the instruction as such is not assembled into memory, there is no op-code for this instruction.
        # Thus, it is resolved before execution. An implication of this is that assignments is for static variables.
        left = self.left.get(vm)
        right = self.right.eval(vm)
        vm.variables.add(left, right)

        self.loc = vm.location_counter
        if left == '.':
            vm.location_counter = right


class ConstStmt(Stmt):
    def __init__(self, lineno, const):
        super().__init__(lineno, const[1:].replace('\\n', '\n'))

    def assemble(self, vm):
        # A ConstStmt is "ab", ie always 2 characters (with a "-prefix in the code, but stripped during parsing).
        # We write the value of the 2 characters to memory
        self.loc = vm.location_counter
        for ch in self.expr:
            vm.mem.write(vm.location_counter, ord(ch), byte=True)
            vm.location_counter += 1
        vm.variables.add(".", vm.location_counter)


class SyscallStmt(Stmt):
    def __init__(self, lineno, syscall, operands=None):
        super().__init__(lineno, syscall)
        self.operands = operands

    def dump(self, vm):
        lineno_str = str(self.lineno) + ": "
        kw_str = "sys " + self.expr
        op_str = ""
        if self.operands and type(self.operands) == list:
            for op in self.operands:
                op_str += (str(op) + ", ")
        else:
            if self.operands:
                op_str = str(self.operands)

        return "{:<8}{:<30}{:<15}{:<15}".format(lineno_str, kw_str, "ops:", op_str, "")

    def __str__(self):
        op_str = ""
        if self.operands and type(self.operands) == list:
            for op in self.operands:
                op_str += (str(op) + "\t")
        else:
            if self.operands:
                op_str = str(self.operands)
        return "sys" + "\t" + self.expr + "\t" + op_str

    def assemble(self, vm):
        # SyscallStmt can be "sys write", thus like a keyword statement. Update location counter but don't
        # write to memory.
        self.loc = vm.location_counter
        vm.mem.write(self.loc, vm.prg.instructions.index(self))
        vm.location_counter += 2
        vm.variables.add(".", vm.location_counter)

    def exec(self, vm):
        vm.variables.add('.', self.loc)

        if self.expr == 'signal':
            # sys  signal; sig; label;  See http://man.cat-v.org/unix-6th/2/signal
            # Note, sig and label are parameters to the signal syscall, as 2 statements. These statements
            # are written to memory in the first assemble pass or in the second resolve pass (if a named label is used)
            # Hence we read the values directly from memory below.

            vm.incr_PC()
            sig = vm.mem.read(vm.get_PC(), 2)

            vm.incr_PC()
            lbl = vm.mem.read(vm.get_PC(), 2)

            action_str = "terminate and jump to {} (location {}) on ".format(vm.named_labels.get_key(lbl), lbl) \
                if lbl % 2 == 0 else "ignore "
            vm.sys_sig_status[vm.sig_list[sig]] = action_str

            vm.incr_PC()

        elif self.expr == 'indir':
            # sys indir; syscall
            vm.incr_PC()

            syscall_address = vm.mem.read(vm.get_PC(), 2)
            syscall_instr_ind = vm.mem.read(syscall_address, 2)

            current_pc = vm.get_PC()
            vm.set_PC(syscall_address)

            if vm.prg:
                vm.logger.debug(f"sys indir, calling {vm.prg.instructions[syscall_instr_ind]}")
                vm.prg.instructions[syscall_instr_ind].exec(vm)
                vm.set_PC(current_pc)
                vm.incr_PC()

        elif self.expr == 'stat':
            # sys stat; name; buf
            vm.incr_PC()

            PSW = vm.PSW.get()

            fn_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(fn_addr, 1)
            fn = ""
            while ch != 0:
                fn += chr(ch)
                fn_addr += 1
                ch = vm.mem.read(fn_addr, 1)

            vm.logger.debug('sys stat {}'.format(fn))

            try:
                statinfo = os.stat(fn)

                st_dev = statinfo[stat.ST_DEV]

                modtime = statinfo[stat.ST_MTIME] & 0xFFFFFFFF  # 4 bytes
                val = modtime
                byte_offset = 4 * 8

                actime = statinfo[stat.ST_ATIME] & 0xFFFFFFFF  # 4 bytes
                val = val | (actime << byte_offset)
                byte_offset = (4 + 4) * 8

                addr = statinfo.st_blocks & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # 16 bytes
                val = val | (addr << byte_offset)
                byte_offset = (4 + 4 + 16) * 8

                size = statinfo[stat.ST_SIZE] & 0xFFFFFF  # 3 bytes
                val = val | (size << byte_offset)
                byte_offset = (4 + 4 + 16 + 3) * 8

                gid = statinfo[stat.ST_GID] & 0xFF  # 1 byte
                val = val | (gid << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1) * 8

                uid = statinfo[stat.ST_UID] & 0xFF  # 1 byte
                val = val | (uid << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1 + 1) * 8

                nlinks = statinfo[stat.ST_NLINK] & 0xFF  # 1 byte
                val = val | (nlinks << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1 + 1 + 1) * 8

                flags = statinfo[stat.ST_MODE] & 0xFFFF  # 2 bytes
                val = val | (flags << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1 + 1 + 1 + 2) * 8

                inumber = statinfo[stat.ST_INO] & 0xFFFF  # 2 bytes
                val = val | (inumber << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1 + 1 + 1 + 2 + 2) * 8

                major = int(st_dev >> 8 & 0xFF)  # 1 byte
                val = val | (major << byte_offset)
                byte_offset = (4 + 4 + 16 + 3 + 1 + 1 + 1 + 2 + 2 + 1) * 8

                minor = int(st_dev & 0xFF)  # 1 byte
                val = val | (minor << byte_offset)

                vm.incr_PC()

                buf_addr = vm.mem.read(vm.get_PC(), 2)
                vm.mem.write(buf_addr, val)

                PSW['C'] = 0

            except FileNotFoundError:
                PSW['C'] = 1
            finally:
                vm.PSW.set(PSW)

        elif self.expr == 'creat':
            # sys creat; name; mode
            # (file descriptor in r0)

            vm.incr_PC()

            PSW = vm.PSW.get()

            fn_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(fn_addr, 1)
            fn = ""
            while ch != 0:
                fn += chr(ch)
                fn_addr += 1
                ch = vm.mem.read(fn_addr, 1)

            vm.incr_PC()

            mode = vm.mem.read(vm.get_PC(), 2)

            fd = os.open(fn, os.O_CREAT | os.O_RDWR, mode)
            vm.logger.info('sys creat {} (fd={})'.format(fn, fd))

            PSW['C'] = 0
            vm.register['r0'] = fd
            vm.files[fd] = fn

            vm.PSW.set(PSW)

            vm.incr_PC()

        elif self.expr == 'write':
            # (file descriptor in r0)
            # sys  write; buffer; nbytes

            vm.incr_PC()

            buffer_addr = vm.mem.read(vm.get_PC(), 2)

            vm.incr_PC()
            nbytes = vm.mem.read(vm.get_PC(), 2)

            byte_string = []
            for i in range(nbytes):
                val = vm.mem.read(buffer_addr + i, 1)
                byte_string.append(val)

            byte_string = bytes(byte_string)

            bytes_written = os.write(vm.register['r0'], byte_string)
            vm.logger.debug('sys write {} (fd={}), {} bytes'.format(vm.files[vm.register['r0']],
                                                                    vm.register['r0'], bytes_written))

            vm.register['r0'] = bytes_written

            vm.incr_PC()

        elif self.expr == 'open':
            # sys open; name; mode
            # (file descriptor in r0)

            PSW = vm.PSW.get()

            vm.incr_PC()

            fn_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(fn_addr, 1)
            fn = ""
            while ch != 0:
                fn += chr(ch)
                fn_addr += 1
                ch = vm.mem.read(fn_addr, 1)

            vm.incr_PC()
            mode = vm.mem.read(vm.get_PC(), 2)

            try:
                fd = os.open(fn, mode)
                vm.register['r0'] = fd
                vm.files[fd] = fn
                vm.logger.info('sys open {} (fd={})'.format(fn, fd))
                PSW['C'] = 0

            except FileNotFoundError:
                vm.logger.warning('sys open: file {} not found'.format(fn))
                PSW['C'] = 1
            finally:
                vm.PSW.set(PSW)

            vm.incr_PC()

        elif self.expr == 'unlink':
            # sys  unlink; name
            PSW = vm.PSW.get()

            vm.incr_PC()

            fn_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(fn_addr, 1)
            fn = ""
            while ch != 0:
                fn += chr(ch)
                fn_addr += 1
                ch = vm.mem.read(fn_addr, 1)

            try:
                os.unlink(fn)
                vm.logger.debug('sys unlink {}'.format(fn))
                PSW['C'] = 0

            except FileNotFoundError:
                PSW['C'] = 1
            finally:
                vm.PSW.set(PSW)

            vm.incr_PC()

        elif self.expr == 'read':
            # (file descriptor in r0)
            # sys read; buffer; nbytes

            PSW = vm.PSW.get()

            vm.incr_PC()
            buffer_addr = vm.mem.read(vm.get_PC(), 2)

            vm.incr_PC()
            nbytes = vm.mem.read(vm.get_PC(), 2)

            try:
                byte_str = os.read(vm.register['r0'], nbytes)
                vm.logger.debug('sys read {} (fd={}) {} bytes'.format(vm.files[vm.register['r0']],
                                                                      vm.register['r0'], len(byte_str)))
                for ch in byte_str:
                    vm.mem.write(buffer_addr, ch, byte=True)
                    buffer_addr += 1
                vm.register['r0'] = len(byte_str)

                PSW['C'] = 0
            except:
                PSW['C'] = 1
            finally:
                vm.PSW.set(PSW)

            vm.incr_PC()

        elif self.expr == 'chmod':
            # sys chmod; name; mode

            PSW = vm.PSW.get()

            vm.incr_PC()

            fn_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(fn_addr, 1)
            fn = ""
            while ch != 0:
                fn += chr(ch)
                fn_addr += 1
                ch = vm.mem.read(fn_addr, 1)

            vm.incr_PC()
            mode = vm.mem.read(vm.get_PC(), 2)

            vm.logger.debug('sys chmod {} {}'.format(fn, mode))
            os.chmod(fn, mode)

            PSW['C'] = 0

            vm.incr_PC()

        elif self.expr == 'close':
            # (file descriptor in r0)
            # sys close

            vm.logger.debug('sys close {} (fd={})'.format(vm.files[vm.register['r0']], vm.register['r0']))
            os.close(vm.register['r0'])
            vm.incr_PC()

        elif self.expr == 'exec':
            #      sys exec; name; args
            #      name: <...\0>
            #      args: arg0; arg1; ...; 0
            #      arg0: <...\0>
            #      arg1: <...\0>
            #         ...
            PSW = vm.PSW.get()

            vm.incr_PC()
            name_addr = vm.mem.read(vm.get_PC(), 2)
            ch = vm.mem.read(name_addr, 1)
            name = ""
            while ch != 0:
                name += chr(ch)
                name_addr += 1
                ch = vm.mem.read(name_addr, 1)

            vm.incr_PC()  # args
            arg_addr = vm.mem.read(vm.get_PC(), 2)
            arg = vm.mem.read(arg_addr, 2)
            args_list = [arg]
            while arg != 0:
                arg_addr += 2
                arg = vm.mem.read(arg_addr, 2)
                if arg != 0:
                    args_list.append(arg)

            arg_names = ''
            args = []
            for arg in args_list:
                ch = vm.mem.read(arg, 1)
                arg_str = ""
                while ch != 0:
                    arg_str += chr(ch)
                    arg += 1
                    ch = vm.mem.read(arg, 1)
                args.append(arg_str)
                arg_names += (arg_str + ' ')

            vm.stats()

            if 'ASM_EXEC' in os.environ:
                vm.logger.info('ASM_EXEC ({}), {} {}'.format(os.environ['ASM_EXEC'], name, arg_names))
            else:
                vm.logger.info('sys exec {} {}'.format(name, arg_names))
                os.execv(name, args)

            vm.incr_PC()

            PSW['C'] = 0

        elif self.expr == 'exit':
            if 'ASM_EXIT' in os.environ:
                vm.logger.info('ASM_EXIT ({}), sys exit {}'.format(os.environ['ASM_EXIT'], vm.register['r0']))
                vm.exit = True
            else:
                vm.logger.info('sys exit {}'.format(vm.register['r0']))
                vm.exit = True
                sys.exit(vm.register['r0'] & 0xFF)

        elif self.expr == 'break':
            # sys break; addr
            PSW = vm.PSW.get()

            vm.incr_PC()
            addr = vm.mem.read(vm.get_PC(), 2)

            vm.logger.debug('sys break {}'.format(addr))

            PSW['C'] = 0

        elif self.expr == 'seek':
            # (file descriptor in r0)
            # sys seek; offset; ptrname

            PSW = vm.PSW.get()

            vm.incr_PC()
            offset = vm.mem.read(vm.get_PC(), 2)

            vm.incr_PC()
            ptrname = vm.mem.read(vm.get_PC(), 2)

            vm.logger.debug('sys seek, file={} (fd={}), offset={}, how={}'.format(vm.files[vm.register['r0']],
                                                                                  vm.register['r0'], offset, ptrname))
            os.lseek(vm.register['r0'], offset, ptrname)

            PSW['C'] = 0

            vm.PSW.set(PSW)

            vm.incr_PC()

        else:
            vm.logger.warning('sys, {} not implemented'.format(self.expr))
            vm.incr_PC()


class PseudoOpStmt(Stmt):
    def __init__(self, lineno, op, operands=None):
        super().__init__(lineno, op)
        self.operands = operands

    def assemble(self, vm):
        if self.expr == '.byte':
            self.loc = vm.location_counter
            for op in self.operands:
                val = op.eval(vm, byte=True)
                if isinstance(val, int):
                    vm.mem.write(vm.location_counter, val, byte=True)
                else:
                    op = op.get(vm)
                    vm.mem.write(vm.location_counter, ord(op[-1]), byte=True)
                vm.location_counter += 1
            vm.variables.add(".", vm.location_counter)
        elif self.expr == '.even':
            pass  # Treated vm.assemble_segment
        elif self.expr in ['.data', '.text', '.bss']:
            pass  # Treated vm.assemble_segment
        elif self.expr in ['.if', '.endif']:
            pass  # Treated vm.assemble_segment
        else:
            vm.logger.warning('Pseudo op, {} not implemented'.format(self.expr))

    def get(self):
        return self.expr
