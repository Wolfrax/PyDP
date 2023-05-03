import util


class Expression:
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return str(self.expr)

    def type(self):
        return type(self).__name__

    def value(self, vm):
        if self.expr.isdigit():
            # This is octal number
            val = int(self.expr.replace("8", "10").replace("9", "11"), 8)
            return val

        if self.expr[:-1].lstrip('-').isdigit() and self.expr[-1] == ".":
            # This is a decimal number
            val = int(self.expr[:-1])
            return val

        val = vm.variables.get(self.expr)
        if val is not None:
            return val

        return None

    def addr(self, vm):
        val = vm.named_labels.get(self.expr)
        if val:
            return val

        if self.expr[:-1].isdigit() and (self.expr[-1] == 'f' or self.expr[-1] == 'b'):
            # We want to find the statement that this numeric label expression is referring to.
            # For example:
            #       mov r4, 0f              [200]
            #   1:                          [202]
            #       sys	indir; 9f           [204][206]
            #       .data                   [208]
            #   9:	sys	stat; 0:..; outbuf  [210][212][214][216][218]
            #       .text
            #
            # Above is interpreted as:
            #       prg.instructions[200] = mov r4, 0f
            #       prg.instructions[202] = 1:
            #       prg.instructions[204] = sys indir, the value 204 is written on memory location 1168
            #       prg.instructions[206] = 9f
            #       prg.instructions[208] = .data
            #       prg.instructions[210] = 9:
            #       prg.instructions[212] = sys stat
            #       prg.instructions[214] = 0:
            #       prg.instructions[216] = ..
            #       prg.instructions[218] = outbuf
            #       ...etc
            #
            # For "mov r4, 0f", 0f is referring to the location of instruction 216 (.. the relocation operator), and
            # we want to move the value of register r4 to the memory location of instruction 216.
            # We can get the array of memory locations to label 0 from numeric_labels, this is the value of
            # variable numeric_lables == [4922, 4938, 4944, 4950, 4956, 4970, 4974].
            # The values in numeric_lables is the memory locations, so we need to transform these memory locations to
            # program indexes, this is made by calling the method get_instruction_indexes(numeric_lbls).
            # This method loops through all prg.instructions and finds all instructions with "loc" equal to one of
            # the values in numeric_lbls. The method then takes the index of this instructions and adds this to the
            # return value. lbl_instr_locations = [52, 158, 182, 216, 238, 808, 1086].
            # Then, for forward labels, we can take the closest but bigger value comparing to the instruction index
            # of "mov r4, 0f", stored in variable instr_ind = 200. So we find value 216, then we map 216 to 4950 in
            # numeric_lbls (the 4th element) and return this.
            # For backward labels, we find the closest but smaller value.

            numeric_lbls = vm.numeric_labels.get(self.expr[:-1])
            lbl_instr_locations = vm.get_instruction_indexes(numeric_lbls)

            ind = vm.get_statement_index()
            if self.expr[-1] == 'f':  # forward label, find the closest but bigger value
                instr_loc = min([i for i in lbl_instr_locations if i > ind])
            else:  # backward label, find the closest but smaller value
                instr_loc = max([i for i in lbl_instr_locations if i < ind])

            val = numeric_lbls[lbl_instr_locations.index(instr_loc)]
            return val

        return None

    def eval(self, vm, byte=False, update=True):
        val = self.value(vm)
        if val is not None:
            return val

        addr = self.addr(vm)
        if addr is not None:
            return addr

        return self.expr

    def get(self, vm):
        return self.expr

    def set(self, vm, val):
        # Someone is trying to set a value of this expression, for example a 'mov' instruction

        var = vm.variables.get(self.expr)
        if var:
            vm.variables.add(self.expr, val)
            return

        lbl = vm.named_labels.get(self.expr)
        if lbl:
            vm.mem.write(lbl, val)
            return

        lbl = vm.numeric_labels.get(self.expr)
        if lbl:
            vm.mem.write(lbl, val)
            return

        lbl = self.eval(vm)
        vm.mem.write(lbl, val)

    def resolve(self, vm):
        pass

    def words(self):
        return 0

    def pre_addr_update(self, vm, byte=False):
        pass

    def post_addr_update(self, vm, byte=False):
        pass


class UnaryExpression:
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __str__(self):
        return self.op + str(self.expr)

    def type(self):
        return type(self).__name__

    def get(self, vm):
        return self.op + self.expr

    def eval(self, vm, byte=False, update=True):
        val = int(self.expr[:-1]) if self.expr[-1] == '.' else int(self.expr.replace("8", "10").replace("9", "11"), 8)
        if self.op == "-":
            return util.to_byte(val) if byte else -val
        elif self.op == "!":
            val = util.to_byte(val) if byte else val
            return ~int(val) & 0xFFFF


class BinaryExpression:
    def __init__(self, operator, left, right):
        if len(operator) == 2 and operator[0] == '\\':
            operator = '/'
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.left) + self.operator + str(self.right)

    def type(self):
        return type(self).__name__

    def set(self, vm, val, byte=False):
        address = self.eval(vm)
        vm.mem.write(address, val, byte)

    def eval_address(self, vm, byte=False):
        return self.eval(vm, byte)

    def eval(self, vm, byte=False, update=True):
        left_val = self.left.eval(vm, byte, update=update)
        right_val = self.right.eval(vm, byte, update=update)

        if self.operator == "+":
            return left_val + right_val
        elif self.operator == "-":
            return left_val - right_val
        elif self.operator == "*":
            return left_val * right_val
        elif self.operator == "/":
            assert right_val != 0, "BinaryExpression, divide by zero"
            return left_val // right_val
        else:
            assert False, "BinaryExpression, unknown operator {}".format(self.operator)

    def words(self):
        return 0


class LabelExpression:
    def __init__(self, lbl, expr):
        self.expr = expr
        self.label = lbl

    def __str__(self):
        return str(self.label) + str(self.expr)

    def type(self):
        return type(self).__name__

    def eval(self, vm, update=True):
        # Not implemented
        return self.label + self.expr


class TempSymExpression:
    def __init__(self, temp_sym, expr):
        self.temp_sym = temp_sym
        self.expr = expr

    def __str__(self):
        return self.temp_sym + self.expr

    def type(self):
        return type(self).__name__

    def eval(self, vm, update=True):
        # Not implemented
        return self.temp_sym + self.expr


class Reg:
    def __init__(self, reg):
        self.reg = reg
        self.mode = 0
        self.addr_words = 0

    def __str__(self):
        return self.reg

    def eval(self, vm, byte=False):
        pass

    def set(self, vm, val, byte=False):
        pass

    def type(self):
        return type(self).__name__

    def words(self):
        return self.addr_words

    def reg(self):
        return self.reg

    def pre_addr_update(self, vm, byte=False):
        pass

    def post_addr_update(self, vm, byte=False):
        pass

    def pre_dump_update(self, vm, byte=False):
        pass

    def post_dump_update(self, vm, byte=False):
        pass


class AddrRegister(Reg):
    def __init__(self, reg):
        super().__init__(reg)

    def eval(self, vm, byte=False):
        # op: R, R contains operand
        return vm.register[self.reg]

    def set(self, vm, val, byte=False):
        vm.register[self.reg] = util.to_byte(val) if byte else val


class AddrRegisterDeferred(Reg):
    def __init__(self, reg):
        super().__init__(reg)
        self.mode = 1

    def __str__(self):
        return "(" + self.reg + ")"

    def eval(self, vm, byte=False):
        # op: (R), R is address
        address = vm.register[self.reg]
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = vm.register[self.reg]
        vm.mem.write(address, val, byte)


class AddrAutoIncrement(Reg):
    def __init__(self, reg):
        super().__init__(reg)
        self.mode = 2

    def __str__(self):
        return "(" + self.reg + ")+"

    def eval(self, vm, byte=False):
        # op: (R)+, R contains address, then increment (R)
        address = vm.register[self.reg]
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = vm.register[self.reg]
        vm.mem.write(address, val, byte)

    def post_addr_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] + 1 if byte else vm.register[self.reg] + 2


class AddrAutoIncrementDeferred(Reg):
    def __init__(self, reg):
        super().__init__(reg)
        self.mode = 3

    def __str__(self):
        return "*(" + self.reg + ")+"

    def eval(self, vm, byte=False):
        # op: *(R)+, R contains address of address, increment (R)
        address = vm.register[self.reg]
        address = vm.mem.read(address, 2)
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = vm.register[self.reg]
        address = vm.mem.read(address, 2)
        vm.mem.write(address, val, byte)

    def post_addr_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] + 1 if byte else vm.register[self.reg] + 2


class AddrAutoDecrement(Reg):
    def __init__(self, reg):
        super().__init__(reg)
        self.mode = 4

    def __str__(self):
        return "-(" + self.reg + ")"

    def eval(self, vm, byte=False):
        # op: -(R), decrement (R), R contains address
        address = vm.register[self.reg]
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = vm.register[self.reg]
        vm.mem.write(address, val, byte)

    def pre_addr_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] - 1 if byte else vm.register[self.reg] - 2

    def pre_dump_update(self, vm, byte=False):
        self.pre_addr_update(vm, byte)

    def post_dump_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] + 1 if byte else vm.register[self.reg] + 2


class AddrAutoDecrementDeferred(Reg):
    def __init__(self, reg):
        super().__init__(reg)
        self.mode = 5

    def __str__(self):
        return "*-(" + self.reg + ")"

    def eval(self, vm, byte=False):
        # op: *-(R), decrement R, R contains address
        address = vm.register[self.reg]
        address = vm.mem.read(address, 2)
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = vm.register[self.reg]
        address = vm.mem.read(address, 2)
        vm.mem.write(address, val, byte)

    def pre_addr_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] - 1 if byte else vm.register[self.reg] - 2

    def pre_dump_update(self, vm, byte=False):
        self.pre_addr_update(vm, byte)

    def post_dump_update(self, vm, byte=False):
        vm.register[self.reg] = vm.register[self.reg] + 1 if byte else vm.register[self.reg] + 2


class AddrIndex(Reg):
    def __init__(self, reg, expr, sym_name=None):
        super().__init__(reg)
        self.expr = expr
        self.mode = 6
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.reg:
            if self.name:
                s = self.name + " [" + str(self.expr) + "]"
            else:
                s = str(self.expr)
            return s + "(" + self.reg + ")"
        else:
            if self.name:
                return self.name + " [" + str(self.expr) + "]"
            else:
                return str(self.expr)

    def eval(self, vm, byte=False):
        # op: X(R), (R) + X is address
        # op: A
        if self.reg:
            address = vm.register[self.reg] + self.expr.eval(vm)
            val = vm.mem.read(address, 1 if byte else 2)
        else:
            address = self.expr.eval(vm)
            val = vm.mem.read(address, 1 if byte else 2)

        return val

    def eval_address(self, vm, byte=False):
        if self.reg:
            address = vm.register[self.reg] + self.expr.eval(vm)
        else:
            address = self.expr.eval(vm)

        return address

    def set(self, vm, val, byte=False):
        if self.reg:
            address = vm.register[self.reg] + self.expr.eval(vm)
        else:
            address = self.expr.eval(vm)
        vm.mem.write(address, val, byte)


class AddrIndexDeferred(Reg):
    def __init__(self, reg, expr, sym_name=None):
        super().__init__(reg)
        self.expr = expr
        self.mode = 7
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.name:
            return "*" + self.name + " [" + str(self.expr) + "]" + " (" + self.reg + ")" \
                if self.expr else "*(" + self.reg + ")"
        else:
            return "*" + str(self.expr) + "(" + self.reg + ")" if self.expr else "*(" + self.reg + ")"

    def eval(self, vm, byte=False):
        # op: *X(R): (X + R) is address to address
        if self.expr:
            address = self.expr.eval(vm) + vm.register[self.reg]
        else:
            address = vm.register[self.reg]
        address = vm.mem.read(address, 2)
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = self.expr.eval(vm) + vm.register[self.reg]
        address = vm.mem.read(address, 2)
        vm.mem.write(address, val, byte)

    def eval_address(self, vm, byte=False):
        if self.expr is None:
            address = vm.register[self.reg]
        else:
            address = self.expr.eval(vm) + vm.register[self.reg]
        address = vm.mem.read(address, 2)
        return address


class AddrImmediate(Reg):
    def __init__(self, expr, sym_name=None):
        super().__init__(None)
        self.expr = expr
        self.mode = 2
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.name:
            return "$" + self.name
        else:
            return "$" + str(self.expr)

    def eval(self, vm, byte=False):
        # op: $n, return n
        val = self.expr.eval(vm, byte=byte)

        if isinstance(val, str):
            if val[0] == "'":
                if val[1:] == '\\n':
                    return ord('\n')
                if val[1:] == '\\e':
                    return 4
                return ord(val[1])

        return val

    def set(self, vm, val, byte=False):
        assert False, "AddrImmediate, not possible to set value"


class AddrAbsolute(Reg):
    def __init__(self, expr, sym_name=None):
        super().__init__(None)
        self.expr = expr
        self.mode = 3
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.name:
            return "*$" + self.name + " ["+ str(self.expr) + "]"
        return "*$" + str(self.expr)

    def eval(self, vm, byte=False):
        # op: *$A, A is address
        address = self.expr.eval(vm)[2:]  # Strip leading *$
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = self.expr.eval(vm)[2:]  # Strip leading *$
        vm.mem.write(address, val, byte)

class AddrRelative(Reg):
    def __init__(self, expr, sym_name=None):
        super().__init__(None)
        self.expr = expr
        self.mode = 6
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.name:
            return self.name + " [" + str(self.expr) + "]"
        else:
            return str(self.expr)

    def eval(self, vm, byte=False):
        # op: A, A is address relative to PC + 4
        address = self.expr.eval(vm)
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def eval_address(self, vm, byte=False):
        address = self.expr.eval(vm)
        return address

    def set(self, vm, val, byte=False):
        if self.reg:
            address = vm.register[self.reg] + self.expr.eval(vm)
        else:
            address = self.expr.eval(vm)
        vm.mem.write(address, val, byte)

class AddrRelativeDeferred(Reg):
    def __init__(self, expr, sym_name=None):
        super().__init__(None)
        self.expr = expr
        self.mode = 7
        self.addr_words = 1
        self.name = sym_name

    def __str__(self):
        if self.name:
            return "*" + self.name + " [" + str(self.expr) + "]"
        else:
            return "*" + str(self.expr)

    def eval(self, vm, byte=False):
        # op: *A
        address = self.expr.eval(vm)
        address = vm.mem.read(address, 2)
        val = vm.mem.read(address, 1 if byte else 2)
        return val

    def set(self, vm, val, byte=False):
        address = self.expr.eval(vm)
        address = vm.mem.read(address, 2)
        vm.mem.write(address, val, byte)
