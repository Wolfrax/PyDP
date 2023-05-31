# Introduction

This is an experiment of learning a bit more on computer architecture and UNIX.
The selection of targets is simply made from practical perspectives:

* Availability of information and source code
* Comprehensibility, to manage complexity

This converged into using UNIX v6 and PDP 11/40 for this project.
Some reference material (UNIX v6 source code and manuals) cann be found [here](https://github.com/memnoth/unix-v6).

This document is annotations of findings, relevant for the understanding and implementation of the project.

As a starting point, is to make the assembler working. All source code for the UNIX v6 assembler is available.
There is an implementation to parse and interpret the source code for the assembler. Executing this will create a
binary file in the aout-format. The next step is to be able to execute this binary file. If the latter step is done
correctly we can use this to correctly assemble any UNIX v6 assembler file into a binary file.

Below, the text is referring to 'parsing and interpretation' and 'executing'. These are 2 different modes of using
the same implementation. In the first case, we parse the source code of the assembler files and interpret the 
instructions to generate the outcome. In the latter case, we are executing from a binary file in aout-format.

# Table of contents*
* [Overview](#overview)
* [Configuration](#config)
* [Executing](#exec)
* [System calls](#syscalls)
   * [File handling read/write](#rwsyscalls)
* [Addressing modes](#addrmodes)
   * [General Register Addressing](#regaddr)
   * [Program Counter Addressing](#pcaddr)
* [Instructions](#instructions)
   * [Single Operand](#so_instr)
   * [Double Operand](#double_instr)
   * [Program Control](#prgctrl_instr)
   * [Miscellaneous](#misc_instr)
* [Pseudo operations](#pseudo_op)
   * [.byte](#pseudo_op_byte)
* [Appendix](#appendix)
   * [Grammar](#grammar)

# Overview <a name="overview"></a>
In what follows is an analysis of all PDP 11/40 instructions with a few exceptions. Special consideration is taken to
understand the impact of negative operand values in 2's complement format. 

PDP 11/40 use 2's complement (as most computer architectures), which means that negative numbers are stored through the
following transformations: 
* 8-bit: To 2's complement: 256 + value, from 2's complement: value - 256.
  * Example: value is -12, to 2's complement: 256 + (-12) = 244, from 2's complement: 244 - 256 = -12
* 16-bit: To 2's complement: 65536 + value, from 2's complement: value - 65536
  * Example: value is -12, to 2's complement: 65536 + (-12) = 65524, from 2's complement: 65524 - 65536 = -12

To test if a value is negative or not, this can be used:
* 8-bit: value & 0x80 is True
* 16-bit: value & 0x8000 is True

These functions are available as utilities.

```python
def to_2_compl(val, byte=True):
    bits = 8 if byte else 16
    return val if val >= 0 else (1 << bits) + val

def from_2_compl(val, byte=True):
    bits = 8 if byte else 16
    if val < 0:
        return val
   
    if (val & (1 << (bits - 1))) != 0:  # Test if high-bit (sign) is set
        return val - (1 << bits)
    return val
```

Operations that involves arithmetics or bit-operations in general needs to ensure proper handling of 2's complement
formats. Also, reading and writing through system calls to files needs to ensure proper handling, which is analyzed
below.

# Configuration <a name="config"></a>
Configuration is made by using a YAML file, default name is "config.yml".
When instantiating the class VM, it is possible to set the name of the configuration file. If the file is not found
the logger will issue that as information then set default values of configuration parameters.

The parameter is:
* work_dir: Set the directory where files to be used during parsing/interpreting or execution are stored. Also, the
putput files will be generated in this directory. Typically, files used for parsing/interpreting are the
assembler source files (like a11.s, a12.s, ...). Output files are for example "a.out" or dump/trace files.

# Executing <a name="exec"></a>
The implementation of asm has led to several variants:
* Running asm.py from command line
* Running asm.py with a simple GUI using tkinter
* Running asm.py with a web-GUI (using react), in this case an API-server is needed (using Flask)
* Running aout_dump.py to dump an a.out file
* Running aout_exec.py to execute an a.out formatted file (under construction)

The first 3 options are parsing/interpreting assembler files, the two variants with GUI enables simple debugging by
functions such as stepping and setting breakpoints. Also, visualization of registers, processor status word, stack etc 
is available.

Running asm.py from command line is done so: `$ python asm.py as as1?.s`, this will parse/interpret the assembler code
for the first pass of UNIX v6 assembler (ie the files as11.s, as12.s, as13.s, as14.s, as15.s, as16.s, as17.s, as18.s and
as19.s). If the first pass should start the second pass, the environment variable `ASM_PASS2` should be set.
If not set, the first pass will terminate. If set, the first pass will trigger execution of the second pass by executing
`/lib/as2` (as the first pass will execute a system call to `/lib/as2`). `/lib/as2` is linked to the file `as2.bash`.
as2 can be manually executed by issuing `$ python asm.py as2 /tmp/atm1i /tmp/atm2i /tmp/atm3h` (or equivalent names of
tmp-files).

Running with tkinter GUI is done as so: `$ python asm_gui.py as as1?.s`.

Running with web-GUI is a two-step approach. First, the API-server should be started.
Using Flask version 2.0.2 this is done like so (remember to activate the virtual environment first):
```commandline
$ export FLASK_APP=asm_api_server
$ flask run
```
Then, the client - written in react - can be started like so:
```commandline
$ cd /home/mm/dev/PyDP/gui/client
$ npm start
```
If everything is working, the GUI should be visible in the default web-brower. Initially, we need to tell the gui 
which part of the UNIX v6 assembler we will use. Assuming it is the first pass, simply write "as1?.s". A GUI should then
be visible.

Note that above is also set as configurations in PyCharm.

# System calls <a name="syscalls"></a>
## File handling read/write <a name="rwsyscalls"></a>
A correctly generated binary file in aout-format should have all negative numbers in 2's complement already.
Thus, **reading** a file into a memory buffer should not do any transformation to/from 2's complement.
As well, **writing** to a file from a memory buffer should not do any transformation to/from 2's complement.

**Reading** is made in a byte oriented way.
Read the address to a buffer to store read bytes, then read the number of bytes to read (`nbytes`).
Then read `nbytes` from file (FD in 'r0') into `byte_str`-buffer. Then read each byte from `byte_str` and write
to `vm.mem` as a byte. There is no need to transform into 2's complement as we assume all bytes/words already are
in 2's complement format.

```python
buffer_addr = vm.mem.read(vm.get_PC(), 2)

vm.incr_PC()
nbytes = vm.mem.read(vm.get_PC(), 2)

byte_str = os.read(vm.register['r0'], nbytes)
for ch in byte_str:
    vm.mem.write(buffer_addr, ch, byte=True)
    buffer_addr += 1
vm.register['r0'] = len(byte_str)
```
**Writing** is made in a byte oriented way.
Write `nbytes` to file, each byte is read from memory one by one and appended to a byte_string-buffer.
Convert to bytes, and write to file (FD in 'r0', which will hold the number of bytes written).
There is no need to transform into 2's complement as we assume all bytes in `vm.mem`-buffer are already in that format.

```python

for i in range(nbytes):
    val = vm.mem.read(buffer_addr + i, 1)
    byte_string.append(val)
    
byte_string = bytes(byte_string)

bytes_written = os.write(vm.register['r0'], byte_string)
vm.register['r0'] = bytes_written
```

# Addressing modes <a name="addrmodes"></a>
PDP 11/40 has in total 8 "general register addressing" modes. In addition, there are 4 "program counter addressing"
modes. Each is analyzed below with respect to handling of 2's complement.

Addressing modes refers to how we access the operands for instructions. 

In general, an address is the value for a location which cannot be negative by definition. However, doing address 
arithmetics operands can have negative values which is analyzed below.

Note that when interpreting or executing an instruction operand(s) are evaluated first, then the instruction is
performed and the result from the instruction is updated.

When parsing/interpreting source code, the operands are not necessarily stored in memory.
For example, the instruction `jmp start` is in this mode parsed to a `KeywordStmt` class instance, which in turn
refer to an `Expression` instance with the string "start". When interpreting this instruction, a lookup of the location
to "start" is made, and we jump to the location for further interpretations.

When executing the same instruction, the value for "start" is stored in the word following the `jmp`-instruction.
So, here we read the location from memory and jump to that location.

## General register addressing <a name="regaddr"></a>
**Mode 0 (Register)**: Register contains operand. 
There is no issue with 2's complement for this mode since the value in the register is assumed to be in 2's complement 
already. The instructions that update the register with the value is responsible for ensuring that the right format is 
applied.

**Mode 1 (Register deferred)**: Register contains address.
There is no issue with 2's complement for this mode, the value in the register is an address which by definition is
not negative. The instructions that updated the register with the address is responsible for the right format is
applied.

**Mode 2 (Auto-increment)**: Register contains address, the register is incremented by 1 or 2 (dependent if a byte or
word instruction is used). In principle, the increment could 'wrap around' to a negative value. In reality, we assume
that this is not the case. The instructions that updated the register with the address is responsible for the right format is
applied.

**Mode 3 (Auto-increment deferred)**: Register contains address of address, the register s incremented by 1 or 2 
(dependent if a byte or word instruction is used). In principle, the increment could 'wrap around' to a negative value. 
In reality, we assume that this is not the case. The instructions that updated the register with the address is 
responsible for the right format is applied.

**Mode 4 (Auto-decrement)**: Register contains address, the register is decremented by 1 or 2 (dependent if a byte or
word instruction is used). In principle, the decrement could 'wrap around' to a negative value. In reality, we assume
that this is not the case. The instructions that updated the register with the address is responsible for the right 
format is applied.

**Mode 5 (Auto-decrement deferred)**: Register contains address of address, the register s decremented by 1 or 2 
(dependent if a byte or word instruction is used). In principle, the decrement could 'wrap around' to a negative value. 
In reality, we assume that this is not the case. The instructions that updated the register with the address is 
responsible for the right format is applied.

**Mode 6 (Index)**: Register contains address which is added to the value (X) following the current instruction.
The address to the operand is calculated as "register-value + X". 
Note that register-value and/or X can be negative! Thus, we need to care of this when making the addition to form the
address. In implementation this is made `AddrIndex eval`-method, see below.

Assume RO has value 65524 (-12) and the instruction is `JMP 100.(R0)`. The decimal value 100 is stored in the word 
following the JMP-instruction. The address should be calculated as: -12 + 100 = 88, and we should jump to that address.
Similar if R0 = 100 and the instruction is `JMP -12.(R0)`; address is 100 + (-12) = 88.
The case where both operands are negative is not valid as an address cannot be negative. See implementation below from
`AddrIndex`-class.

```python
def eval(self, vm, byte=False):
    # op: X(R), (R) + X is address
    # op: A
    if self.reg:
        op1 = util.from_2_compl(vm.register[self.reg], byte)
        op2 = self.expr.eval(vm)
        address = op1 + op2
        
        assert address > 0, f"Addressing error: {address}"
        
        val = vm.mem.read(address, 1 if byte else 2)
    else:
        address = self.expr.eval(vm)
        val = vm.mem.read(address, 1 if byte else 2)

    return val

def set(self, vm, val, byte=False):
    if self.reg:
        address = self.expr.eval(vm) + util.from_2_compl(vm.register[self.reg], byte)
    else:
        address = self.expr.eval(vm)

    assert address > 0, f"Addressing error: {address}"
    
    vm.mem.write(address, val, byte)

def eval_address(self, vm, byte=False):
    if self.reg:
        address = self.expr.eval(vm) + util.from_2_compl(vm.register[self.reg], byte)
    else:
        address = self.expr.eval(vm)
    
    assert address > 0, f"Addressing error: {address}"
    
    return address
```
Additional comments:

* When executing, the expr-value (X) is set in `Instr new_expr`-method, where the value is read from memory. The value 
is assumed to be in 2's complement format in memory. Thus, no conversion is needed here.
* When parsing and interpreting, the value (X) is part of the source code, for example `JMP -12.(R0)` where X is -12.
The `util.from_2_compl` implementation will test if the operand is negative already and then return that as a result. 
* If `self.reg` is **None**, we are dealing with a `branch`-instruction which can jump to an instruction in forward
direction or backwards. In the latter case the offset value in the branch-instruction word is negative.
When executing, a negative offset in 2's complement is first handled in `InstrBranch __init__`-method, then in 
`Instr new_expr`-method the expr-value (X) is calculated as `expr = self.vm.get_PC() + 2 + (2 * offset)`, where `offset`
is negative if branch is backwards. The expr value must not be negative.

**Mode 7 (Index deferred)**: The address to the operand is calculated as "register-value + (X)", which is a new address 
that is in turn the address to the operand. 
Similar comments as for Index mode, the operands is the address calculations can be negative, either the register-value
or X. So considerations to 2's complement is needed. The implementation of `AddrIndexDeferred eval`-method is below.

Assume RO has value 65524 (-12) and the instruction is `JMP *100.(R0)`. The decimal value 100 is stored in the word 
following the JMP-instruction. The first address should be calculated as: -12 + 100 = 88, and we should use that 
address to calculate the next address which is stored at location 88. The second address is pointing to the operand and
should not be negative.

Similar if R0 = 100 and the instruction is `JMP *-12.(R0)`; address is 100 + (-12) = 88 which points to the operand
The case where both operands are negative is not valid as an address cannot be negative. See implementation below.

```python
def eval(self, vm, byte=False):
    # op: *X(R): (X + R) is address to address
    if self.expr:
        op1 = util.from_2_compl(vm.register[self.reg], byte)
        op2 = self.expr.eval(vm)
        address = op1 + op2
    else:
        address = vm.register[self.reg]

    assert address > 0, f"Addressing error: {address}"
    
    address = vm.mem.read(address, 2)
    val = vm.mem.read(address, 1 if byte else 2)
    return val
    
def set(self, vm, val, byte=False):
    address = self.expr.eval(vm) + util.from_2_compl(vm.register[self.reg], byte)
    
    assert address > 0, f"Addressing error: {address}"
    
    address = vm.mem.read(address, 2)
    vm.mem.write(address, val, byte)
    
def eval_address(self, vm, byte=False):
    if self.expr is None:
        # In this case, the value in register cannot be negative
        address = vm.register[self.reg]
    else:
        # Note that value in register can be negative!
        address = self.expr.eval(vm) + util.from_2_compl(vm.register[self.reg], byte)
    
    assert address > 0, f"Addressing error: {address}"
    
    address = vm.mem.read(address, 2)
    return address
```
Additional comment:
* X in front of register might be missing (eg `JMP *(R0)`), which is handled in the else-branch above.

## Program counter addressing <a name="pcaddr"></a>
These are the addressing modes where addressing is made relative the program counter.

**Mode 2 (Immediate)**: Operand follow instruction.
An example is `mov $-12. ,r4`, where the decimal value -12 is moved into register 4. The first operand value is stored 
in the word following the mov-instruction. In memory the operand should be stored as 65524, so we move that value to r4.
When parsing the first operand it will be a string "-12." in the class UnaryExpression. When interpreting, the string
will be evaluated to an integer in the `eval`-method of `UnaryExpression`-class and converted to 2' complement.

```python
def eval(self, vm, byte=False, update=True):
    val = int(self.expr[:-1]) if self.expr[-1] == '.' else int(self.expr.replace("8", "10").replace("9", "11"), 8)
    if self.op == "-":
        return util.to_2_compl(val, byte)
    elif self.op == "!":
        val = util.to_byte(val) if byte else val
        return ~int(val) & 0xFFFF
```
Note that the unary operator might be "!" (not-operator), which is inverting bits in value.

When executing an instruction with an operand in Immediate mode, we assume that the operand is already in 
2's complement format. From `Instr new_expr`-method
```python
elif mode == self.AUTOINCREMENT or mode == self.IMMEDIATE:
    if reg == 'pc':  # mode == IMMEDIATE
        expr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
        name = self.aout.sym_table.find(expr) 
        return as_expr.AddrImmediate(as_expr.Expression(str(expr) + "."), sym_name=name)
```

**Mode 3 (Absolute)**: Address follow instruction.
An example is `mov *$1000., r4`, which will move the value at address 1000 (decimal) to register 4.
As the operand is an address it can by definition not be negative, so there is no issue with 2's complement mode when
either parsing/interpreting or executing.

**Mode 6 (Relative)**: Address follow instruction, the value of "address + PC + 4" is the address to the operand.
An example is `jmp start`, which will make a jump and execute from the address of label `start`.
The sum of "address + PC + 4" must be > 0, but this also means that "address" can be negative. For example, if
address is -12 and PC is 100, the calculation will be "-12 + 100 + 4" = 92, ie a jump backwards relative current
instruction.

When parsing/interpreting there is no issue with negative values, the implementation will look up the address of "start"
and jump to that address.

When executing we need to take negative values in consideration. At the `Instr new_expr`-method, the part for this mode
should be as below. The value following the instruction word should already be in 2's complement format.

```python
if reg == 'pc':  # RELATIVE
    addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
    addr = util.from_2_compl(addr, False) + self.vm.get_PC() + 4
    name = self.aout.sym_table.find(addr)
    return as_expr.AddrRelative(as_expr.Expression(str(addr) + "."), sym_name=name)
```
Additional comment:
* Note the "offset" parameter when reading from memory. This is needed since the instruction might be a 
double-operand instruction, for example `mov $2, start`. Here "$2" is stored in the word following the mov-instruction,
while "start" is the second word following the mov-instruction. This is true for any addressing mode that assume that
the operand or address is following current instruction-word.

**Mode 7 (Relative deferred)**: Address follow instruction, the value of "address + PC + 4" is a new address to the
operand. An example is `clr *A`, which will clear the operand.

Here, the first operand might have a negative value, let's say -12 (decimal) and assume PC = 100. The first address
is calculated as "-12 + 100 + 4" = 92. At address 92 a new address is stored, pointing to the operand. The second
address must (by definition) be positive. Hence, we only need to consider the first address calculation for negative
value.

In the `Instr new_expr`-method this mode is implemented as below.

```python
if reg == 'pc':  # RELATIVE DEFERRED
    addr = self.vm.mem.read(self.vm.get_PC() + 2 + offset)
    addr = self.vm.get_PC() + 4 + util.from_2_compl(addr, False)
    addr = util.from_2_compl(addr, False)
    name = self.aout.sym_table.find(addr)
    return as_expr.AddrRelativeDeferred(as_expr.Expression(str(addr) + "."), sym_name=name)
```

# Instructions <a name="instructions"></a>
Instructions are grouped into these categories:
* Single Operand
* Double Operand
* Program Control
* Miscellaneous

The analysis below will comment specifically on negative values for operands.

Operands are assumed to be in 2' complement format when evaluated.
Note that when parsing/interpreting the operands, if negative, will be of class `UnaryExpression`. The `eval`-method
of this class will return a negative value in 2's complement format (see above).

## Single Operand <a name="so_instr"></a>
**CLR(B)**: Clear operand, ie set to zero.
As the operand is set to zero, no consideration needed for negative values.

```python
elif self.expr in ['clr', 'clrb']:
    # Clear
    self.src.set(vm, 0, byte=byte)

    PSW['N'] = 0
    PSW['Z'] = 1
    PSW['V'] = 0
    PSW['C'] = 0
```

**COM(B)**: Complement operand, ie invert bit-values
Assume operand value is 244 (-12), after operation the value will be ~244 = -245, we convert to 
2's complement and get 11. For a positive operand, 11 we get ~11 = -12, converting to 2's complement we get 244.

```python
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
```

**INC(B)**: Increment operand with 1.
Assume operand value is 244 (-12), after operation the value is 245 (-11). 
If operand value is 255 (-1), we increment with 1, and we need to mask with 0xFF and will have the value of 0. 
If operand value is 127, we get 128 (-128) which means that we wrap around, the overflow flag is set to detect this.

```python
elif self.expr in ['inc', 'incb']:
    # Increment
    val = self.src.eval(vm, byte=byte)

    overflow = val == (msb - 1)
    val += 1
    val = val & 0xFF if byte else val & 0xFFFF

    self.src.set(vm, val, byte=byte)

    PSW['N'] = 1 if val & msb else 0
    PSW['Z'] = 1 if val == 0 else 0
    PSW['V'] = 1 if overflow else 0
```

**DEC(B)**: Decrement operand with 1.
Assume operand value is 244 (-12), after operation the value is 243 (-13). 
If operand value is 0, we decrement with 1, and we get -1 which needs to be transformed into 2's complement format 
to 255. If operand value is 128 (-128), we get 127 which means that we wrap-around, the overflow flag is set to 
detect this.

```python
elif self.expr in ['dec', 'decb']:
  # Decrement
  val = self.src.eval(vm, byte=byte)
  
  overflow = val == msb
  val -= 1

  val = util.to_2_compl(val, byte=byte)
  self.src.set(vm, val, byte=byte)
  
  PSW['N'] = 1 if val & msb else 0
  PSW['Z'] = 1 if val == 0 else 0
  PSW['V'] = 1 if overflow else 0
```

**NEG(B)**: Replace the operands value with its 2's complement.
Assume operand value is 244 (-12), after operation the value is 12. Similar, if operand value is 12 
we get 244 (-12).

```python
elif self.expr in ['neg', 'negb']:
    val = self.src.eval(vm, byte=byte)

    val = util.from_2_compl(val, byte)
    val = -val
    val = util.to_2_compl(val, byte)

    self.src.set(vm, val, byte=byte)
    
    PSW['N'] = 1 if val & msb else 0
    PSW['Z'] = 1 if val == 0 else 0
    PSW['C'] = 0 if val == 0 else 1
    PSW['V'] = 1 if val & msb else 0
```

**TST(B)**: Set condition codes N and Z according to operand value.
We convert from 2's complement and test to set condition codes.

```python
elif self.expr in ['tst', 'tstb']:
    # Test, set condition flags
    val = self.src.eval(vm, byte=byte)

    PSW['N'] = 1 if val & msb else 0
    PSW['Z'] = 1 if val == 0 else 0
    PSW['V'] = 0
    PSW['C'] = 0
```

**ASR(B)**: Arithmetic shift right one place with bit 15/7 replicated, the C-bit is loaded from bit 0 of operand.
Assume operand value is 244 (-12), we convert from 2's complement to get -12 and shift right to get -6.

```python
elif self.expr in ['asr', 'asrb']:
    # Arithmetic shift right
    val = self.src.eval(vm, byte=byte)

    PSW['C'] = val & 1
    
    val = util.from_2_compl(val, byte)
    val = (val >> 1) | (val & msb)
    val = util.to_2_compl(val, byte=byte)
    self.src.set(vm, val, byte=byte)
    
    PSW['N'] = 1 if val & msb else 0
    PSW['Z'] = 1 if val == 0 else 0
    PSW['V'] = PSW['N'] ^ PSW['C']
```

**ASL(B)**: Arithmetic shift left one place, bit 0 is loaded with zero, the C-bit is loaded from the most 
significant bit.
Assume operand value is 244 (-12), we convert from 2's complement to get -12 and shift left to get -24.

```python
elif self.expr in ['asl', 'aslb']:
    # Arithmetic shift left
    val = self.src.eval(vm, byte=byte)

    if byte:
        # The manual is ambiguous on byte operation, when general registers is used, byte operates on bit 0 - 7
        PSW['C'] = (val & msb) >> 7
    else:
        PSW['C'] = (val & msb) >> 15

    val = util.from_2_compl(val, byte=byte)
    val <<= 1
    val = util.to_2_compl(val, byte=False)
    self.src.set(vm, val, byte=False)

    PSW['N'] = 1 if val & msb else 0    
    PSW['Z'] = 1 if val == 0 else 0
    PSW['V'] = PSW['N'] ^ PSW['C']
```

**ROR(B)**: Rotate all bits right one place, the C-bit is loaded with bit 0, the previous content of C-bit is loaded
into the most significant bit.
Assume operand value is 244 (-12), which has bit sequence "1111 0100", assume C = 1. The operation will generate 
"1111 1010" = 250 (-6) with C = 0.

```python
elif self.expr in ['ror', 'rorb']:
    # Rotate right, shift operand right, move the lowest bit in carry
    val = self.src.eval(vm, byte=byte)
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
```

**ROL(B)**: Rotate all bits left one place, the most significant bit is loaded into C-bit, and the previous content of
C-bit is loaded into bit 0 of the operand.
Assume operand value is 244 (-12), which has bit sequence "1111 0100", assume C = 1. The operation will generate
"1110 1001" = 233 (-23) with C = 1.

```python
elif self.expr in ['rol', 'rolb']:
    # Rotate right, shift operand left, move the lowest bit in carry
    val = self.src.eval(vm, byte=byte)
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
```

**SWAB**: Swap high-order byte and low-order byte of operand. Note this instruction only works on word sized operand.
Assume operand value is 65524 (-12) = 0xFFF4, swapping bytes will generate  0xF4FF = 62719 (-2817).

```python
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
```

**ADC(B)**: Add the C-bit into operand.
Assume operand value is 244 (-12) and C = 1, this will result in 243 (-11).
Assume operand value is 255 (-1) and C = 1, the result will be 0, and we detect overflow of the operation.
Assume operand value is 127 and C = 1, the result will be 128 (-128), there is a wrap-around.

```python
elif self.expr in ['adc', 'adcb']:
    # Add carry
    val = self.src.eval(vm, byte=byte)

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
```

**SBC(B)**: Subtract the C-bit from operand - Not implemented!
**SXT**:Sign extend - Not implemented!

## Double Operand <a name="double_instr"></a>

**MOV(B)**: Move source operand to destination operand.
Assume source operand is 244 (-12), the dest operand will be 244 (-12).

```python
if self.expr in ['mov', 'movb']:
    # Move
    val = self.src.eval(vm, byte=byte)
    if self.expr == 'movb' and val & msb and isinstance(self.dst, as_expr.AddrRegister): # sign extend
        val = 0xFF00 | val
        self.dst.set(vm, val, byte=False)
    else:
        self.dst.set(vm, val, byte=byte)

    PSW['N'] = 1 if val & msb else 0
    PSW['Z'] = 1 if val == 0 else 0
    PSW['V'] = 0
```

**CMP(B)**: Compare source and dest operands and set condition codes, both source and dest operands are unchanged.
Assume source operand value is 244 (-12) and dest operand value is 12, we get 244 - 12 = 232 (-24). Set condition codes
accordingly (see manual).

```python
elif self.expr in ['cmp', 'cmpb']:
    # Compare
    src_val = self.src.eval(vm, byte=byte)
    src = util.from_2_compl(src_val, byte=byte)

    dst_val = self.dst.eval(vm, byte=byte)
    dst = util.from_2_compl(dst_val, byte=byte)

    res = src - dst
    res_val = src_val - dst_val

    PSW['N'] = 1 if res < 0 else 0
    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 1 if ((src_val ^ dst_val) & msb) and not ((dst_val ^ res_val) & msb) else 0
    PSW['C'] = 1 if src_val < dst_val else 0
```

**ADD**: Add source and dest operands and store result in dest.
Assume source operand is 25 000 and dest operand is 10 000. Result will be 35 000 (overflow). The V-bit is set to 1,

```python
elif self.expr == 'add':
    # Add :-)
    src_val = self.src.eval(vm)
    src = util.from_2_compl(src_val, byte=byte)

    dst_val = self.dst.eval(vm)
    dst = util.from_2_compl(dst_val, byte=byte)

    res_val = src_val + dst_val
    res = src + dst

    self.dst.set(vm, res_val)

    PSW['N'] = 1 if res < 0 else 0
    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 1 if not ((src_val ^ dst_val) & msb) and ((dst_val ^ res_val) & msb) else 0
    PSW['C'] = 1 if res_val >= 0xFFFF else 0
```
**SUB**: Subtract the source operand from the dest operand and store result in dest.
V-bit is set to 1 if operands are of opposite signs and the sign of the source operand is the same as the sign of the
result.

Assume source operand is 1 and dest operand is 0. Result will be -1 which needs to be re-transformed to 2's complement
(65535). The V-bit is set to 0; operands are of equal sign.

Assume source operand is 32767 and dest operand is 32768 (-32768), the result will be -32768 - 32767 = -65535, this 
value is transformed back to 2's complement and will become 1.
The V-bit is set to 0; operands are of opposite signs, the source operand is positive and so is the result.

```python
elif self.expr == 'sub':
    # Subtract
    src_val = self.src.eval(vm)
    src = util.from_2_compl(src_val, byte=byte)

    dst_val = self.dst.eval(vm)
    dst = util.from_2_compl(dst_val, byte=byte)

    res_val = dst_val - src_val
    res = dst - src

    PSW['N'] = 1 if res < 0 else 0

    res = util.to_2_compl(res, byte)
    self.dst.set(vm, res)

    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 1 if ((src_val ^ dst_val) & msb) and not ((dst_val ^ res_val) & msb) else 0
    PSW['C'] = 1 if src_val > dst_val else 0
```

**BIT(B)**: Perform logical AND comparison of source operand and dest operand, condition codes is modified.
No issue with 2's complement.

```python
elif self.expr in ['bit', 'bitb']:
    # Bit and
    src = self.src.eval(vm, byte=byte)
    dst = self.dst.eval(vm, byte=byte)

    res = src & dst

    PSW['N'] = 1 if res & msb else 0
    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 0
```

**BIC(B)**: Clear each bit in the dest operand that corresponds to a set bit in the source operand.
No issue with 2's complement.

```python
elif self.expr in ['bic', 'bicb']:
    # Bit clear
    src = self.src.eval(vm)
    dst = self.dst.eval(vm)

    res = (max ^ src) & dst
    self.dst.set(vm, res, byte=byte)

    PSW['N'] = 1 if res & msb else 0
    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 0
```

**BIS(B)**: Perform XOR between source and dest operands.
No issue with 2's complement.

```python
elif self.expr in ['bis', 'bisb']:
    # Bit set
    src = self.src.eval(vm, byte=byte)
    dst = self.dst.eval(vm, byte=byte)

    res = src | dst
    self.dst.set(vm, res, byte=byte)

    PSW['N'] = 1 if res & msb else 0
    PSW['Z'] = 1 if res == 0 else 0
    PSW['V'] = 0
```

**MUL**: The contents of dest and source operands are taken as 2's complement integers and are multiplied in 
dest operand and succeeding register.

```python
elif self.expr in ['mul', 'mpy']:
    # Multiply
    src_val = self.src.eval(vm)
    src = util.from_2_compl(src_val, byte=byte)

    reg_list = list(vm.register)
    dst_reg = reg_list[reg_list.index(self.dst.reg)]
    dst_val = vm.register[dst_reg]
    dst = util.from_2_compl(dst_val, byte=byte)

    res_val = dst_val * src_val
    res = dst * src
    res = util.to_2_compl(res, byte)
    
    if reg_list.index(self.dst.reg) % 2 == 0:
        vm.register[dst_reg + 1] = (res & 0xFFFF0000) >> 16
    vm.register[dst_reg] = res & 0xFFFF

    PSW['N'] = 1 if res_val & 0x80000000 else 0
    PSW['Z'] = 1 if (res_val & 0xFFFFFFFF) == 0 else 0
    PSW['V'] = 0
    PSW['C'] = 1 if res_val < (1 << 15) or res_val >= ((1 << 15) - 1) else 0
```

**DIV**: The 32-bit 2's complement integer in R and Rv1 is divided u the src operand. The quotient is left in R, 
the reminder in Rv1. Division will be performed so that the reminder is of the same sign as the dividend.

```python
elif self.expr in ['div', 'dvd']:
    # Divide
    reg_list = list(vm.register)

    src_val = self.src.eval(vm)
    src = util.from_2_compl(src_val, byte)
    
    dst_val = vm.register[reg_list[reg_list.index(self.dst.reg) + 1]]
    dst = util.from_2_compl(dst_val, byte)

    if src_val == 0:
        PSW['C'] = 1
    else:
        qt, mod = divmod(dst, src)

        self.dst.set(vm, qt)
        vm.register[reg_list[reg_list.index(self.dst.reg) + 1]] = mod

        PSW['N'] = 1 if qt < 0 else 0
        PSW['Z'] = 1 if qt == 0 else 0
        PSW['V'] = 0
        PSW['C'] = 0
```

**ASH**: The contents of the register are shifted right or left the number of times specified by the shift count.
The shift count is taken as the low order 6 bits of the src operand. This number ranges from -32 to +31. 
Negative is a right shift and positive is a left shift.

```python
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
```

**ASHC**: The contents of the register and the register ORed with one are treated as one 32 bit word, R + 1 
(bits 0 - 15) and R (bits 16 - 31) are shifted right or left the number of times specified by the shift count.
The shift count is taken as the low order 6 bits of the src operand. This number ranges from -32 to +31. Negative is a
right shift and positive is a left shift. When the register chosen is an odd number the register and the register
ORer with one are the same. In this case the right shift becomes a rotate (for up to a shift of 16). The 16 bit word is
rotated right the number of bits specified by the shift count.

```python
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
```

**XOR**: The exclusive OR of the register and dst operand is stored in the dst address.

Not implemented!

## Program Control <a name="prgctrl_instr"></a>

**BR, BNE, BEQ, BPL, BMI, BVC, BVS, BCC, BCS, BGE, BLT, BGT, BLE, BHI, BLOS, BHIS, BLO, JMP**:
Branch instruction causes a jump to a location defined by the sum of the offset (multiplied by 2) and the current
contents of the program counter. Note that the offset can be negative or positive, so consideration on 
2's complement is needed.

Note the operation `self.src.eval_address`, this will evaluate the address to jump to.

When parsing/interpreting, a branch instruction in source code will state an expression or a named label to jump to,
for example `br 1b` (jump backwards to the label 1). When assembling the source code the location of the label
is resolved. Another example is `br .+4`, this is instruction will branch from current location + 4 locations forward.

When executing, the offset is stored in the instruction word (except for the JMP instruction). Here we need to 
evaluate offset as 2's complement value. This is done as below. `aout.word` is the instruction word.

```python
offset = aout.word & 0o0377
if offset & 0o0200:
    offset = -((offset & 0o0177 ^ 0o177) + 1)  # sign bit set, make offset negative through 2's complement
```

Branch and jump instructions are done as below.
Note that
* **BHI, BLOS, BHIS, BLO** are considered as "unsigned conditional branches": The unsigned conditional branches provides
a means for testing the result of comparison operations in which the operands are considered as unsigned values
* **BGE, BLT, BGT, BLE** are considered as "signed conditional branches": Particular combinations of the condition code
bits are tested with the signed conditional branches. These instructions are used to test the results of instructions in 
which the operands were considered as signed (2's complement) values.

JMP doesn't have offset in the instruction word, instead the operand uses addressing modes, where mode 0 (register mode)
is illegal.

```python
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
```

**SOB**: Subtract one and branch if result is not 0. The 6-bit offset is interpreted as a positive number.

Note that care needed for negative values (even if offset is interpreted as a positive value, hence conversion 
to/from 2's complement. This is the case when offset is zero, which is not the likely or intended case.

```python
elif self.expr == 'sob':
    # Subtract 1 and branch if not 0
    src = self.src.eval(vm)
    src_val = util.from_2_compl(src, byte)
    src_val -= 1
    src = util.to_2_compl(src_val)
    self.src.set(vm, src)

    if src != 0:
        dst_val = self.dst.eval_address(vm)
        vm.set_PC(dst_val)
    else:
        vm.incr_PC()
```

## Miscellaneous <a name="misc_instr"></a>
**JSR**: Jump to subroutine. In execution of JSR, the content of specified register are pushed to stack, the return
location are loaded into that register. Destination are provided by the dst operand.

Note that dst operand will use the addressing modes, when executing code it will follow the rules applied for these 
modes. When parsing/interpreting the same comment as for branch instructions apply.

```python
elif self.expr == 'jsr':
    # Jump subroutine
    pc_val = vm.incr_PC(1 + self.src.words() + self.dst.words())

    src_val = self.src.eval(vm)
    dst_val = self.dst.eval_address(vm)

    vm.stack_push(src_val)
    self.src.set(vm, pc_val)

    vm.set_PC(dst_val)
```

**RTS**: Return from subroutine. Load content from register into PC and pops the top statement of the stack into the 
specified register.

Note that only register mode is applicable.

```python
elif self.expr == 'rts':
    # Return from subroutine
    op = self.src.eval(vm)
    vm.set_PC(op)
    self.src.set(vm, vm.stack_pop())
```

**MARK**: Not implemented!

**SEV**: Set overflow (V) bit.
```python
if self.expr == 'sev':
    PSW['V'] = 1
```

**CLN, CLZ, CLV, CLC, CCC, SEN, SEZ, SEC, SCC**: Not implemented!

# Pseudo Op <a name="pseudo_op"></a>
Pseudo operations are used in assembler source code to denote statements that generate data in unusual forms or
influence the later operations of the assembler.

Note that pseudo operations is only applicable when parsing/interpreting from source code. When executing from a
binary file, these operations is non-existent.

## .byte <a name="pseudo_op_byte"></a>
The **.byte** operation is followed by a lsit of expressions (possibly only one expression).
The expressions are truncated to 8 bits and assembled in successive bytes.

When parsing the expressions, they can be as a negative ocatal or decimal value.
For example `.byte -14`, note that "-14" is octal and equals -12 in decimal notation.

Here we place "-14" in memory as a negative value, thus we need to convert to 2's complement notation. In the 
example above this will become 244 (-12).

Another example is `.byte 'n, 012`. Here we place the ordinal value for "n" in the first byte, followed by the octal
integer value "12" (10 decimal).

```python
if self.expr == '.byte':
    self.loc = vm.location_counter
    for op in self.operands:
        val = op.eval(vm)
        if isinstance(val, int):
            val = util.to_2_compl(val, byte=True)
            vm.mem.write(vm.location_counter, val, byte=True)
        else:
            op = op.get(vm)
            vm.mem.write(vm.location_counter, ord(op[-1]), byte=True)
        vm.location_counter += 1
    vm.variables.add(".", vm.location_counter)
```

# Appendix <a name="appendix"></a>

## Grammar <a name="grammar"></a>

See also [https://en.wikipedia.org/wiki/PDP-11_architecture]

```text
<statements> ::= <statement> <separator> <statements> *
<statement> ::= <labels> <statement_type> *
<statement_type ::= "\n" | <expression> | <assignment_statement> | <string_statement> | 
                    <keyword_statement> | <pseudo_operation> *
<labels> ::= <label> <separator> <labels> *
<label> ::= <identifier> ":" | <number> ":" *

<expression> ::= <expression_operand> | <double_op_expression> | <bracket_expression> *
<double_op_expression> ::= <expression_operand> <expression_operator> <expression_operand>
<bracket_expression> ::= "[" <expression> "]"
<expression_operand> ::= <identifier> | <number> | <decimal_constant> | <temporary_symbol> *

<assignment_statement> ::= <identifier_assignment_statement> | <location_counter_assignment_statement>
<identifier_assignment_statement> ::= <identifier> "=" <expression>
<location_counter_assignment_statement> ::= "." "=" <expression>

<string_statement> ::= "<" <identifier> ">"

<keyword_statement> ::= <simple_keyword> | <branch_instr> | <ext_branch_instr> | <single_op_instr> | <double_op_instr> | 
                        <misc_instr> | <fp_instr> | <sys_call>

<branch_instr> ::= <branch_keyword> <expression> 
<ext_branch_instr> ::= <ext_branch_keyword> <expression>

<single_op_instr> ::= <single_op_keyword> <operand>
<double_op_instr> ::= <double_op_keyword> <operand> "," <operand>

<misc_instr> ::= <misc_single_op_instr> | <misc_double_op_instr>
<misc_single_op_instr> ::= <misc_single_op_keyword> <operand>
<misc_double_op_instr> ::= <misc_double_op_keyword> <operand> "," <operand>

<fp_instr> ::= <fp_simple_op_keyword> | <fp_single_op_instr> | <fp_double_op_instr>
<fp_single_op_instr> ::= <fp_single_op_keyword> <operand>
<fp_double_op_instr> ::= <fp_double_op_keyword> <operand> "," <operand>

<sys_call> ::= "sys" <sys_call_simple_keyword> | <sys_call_single_op_instr> | <sys_call_double_op_instr> |
                     <sys_call_tertiery_op_instr>
<sys_call_single_op_instr> ::= <sys_call_single_op_keyword> ";" <sys_call_operand>
<sys_call_double_op_instr> ::= <sys_call_double_op_keyword> ";" <sys_call_operand> ";" <sys_call_operand>
<sys_call_tertiery_op_instr> ::= "mount" ";" <sys_call_operand> ";" <sys_call_operand> ";" <sys_call_operand>
<sys_call_operand> ::= <identifier> | <temporary_symbol> | <label>

<pseudo_operation> ::= <byte_op> | ".even" | <if_op> | ".endif" | <globl_op> | ".text" | ".data" | ".bss" | <comm_op>
<byte_op> ::= ".byte" <byte_expressions>
<byte_expressions> ::= <expression> | "," <byte_expressions>
<if_op> ::= ".if" <expression>
<globl_op> ::= ".globl" <globl_names><sys_keyword>
<globl_names> ::= <identifier> | "," <globl_names>
<comm_op> ::= ".comm" <identifier> "," <expression>

<operand> ::= <identifier> | <temporary_symbol> | <temporary_symbol> ".." | <temporary_symbol> <identifier> | 
              <expression> | <address> | <register> | <number>

<address> ::= <direct_addressing> | <indirect_addressing> | <immediate_addressing>
<direct_addressing> ::= <register> | <autoincrement_address> | <autodecrement_address> | <index_address>
<autoincrement_address> ::= "(" <register> ")" "+"
<autodecrement_address> ::= "-" "(" <register> ")"
<index_address> ::= <expression> "(" <register> ")"
<indirect_addressing> ::= <register_deferred> | <autoincrement_deferred> | <autodecrement_deferred> | <index_deferred>
<register_deferred> ::= "(" <register> ")" | "*" <register>
<autoincrement_deferred> ::= "*" "(" <register> ")" "+"
<autodecrement_deferred> ::= "*" "-" "(" <register> ")"
<index_deferred> ::= "*" "(" <register> ")" | "*" <expression> "(" <register> ")"
<immediate_addressing> ::= <relative> | <immediate> | <relative_deferred> | <absolute> 
<relative> ::= <expression>
<immediate> ::= "$" <expression>
<relative_deferred> ::= "*" <expression>
<absolute> ::= "*" "$" <expression>
 
<register> ::= <reg_keyword> | <fp_reg_keyword>

<temporary_symbol> :== <number> "f" | "b"
<separator> ::= ";" | "\n"

# Terminals
<simple_keyword> ::= "clc" | "clv" | "clz" | "cln" | "sec" | "sev" | "sen"
<branch_keyword> ::= "br" | "bne" | "beq" | "bge" | "blt" | "bgt" | "ble" | "bpl" | "bmi" | "bhi" | "blos" | "bvc" | "bvs" | "bhis" | "bec" | 
                     "bcc" | "blo" | "bcs" | "bes"
<ext_branch_keyword> ::= "jbr" | "jne" | "jeq" | "jge" | "jlt" | "jgt" | "jle" | "jpl" | "jmi" | "jhi" | "jlos" | "jvc" | "jvs" | "jhis" | "jec" | 
                         "jcc" | "jlo" | "jcs" | "jes"
<single_op_keyword> ::= "clr" | "clrb" | "com" | "comb" | "inc" | "incb" | "dec" | "decb" | "neg" | "negb" | "adc" | "adcb" | "sbc" | "sbcb" | 
<double_op_keyword> ::= "mov" | "movb" | "cmp" | "cmpb" | "bit" | "bitb" | "bic" | "bicb" | "bis" | "bisb" | "add" | "sub"
                       "ror" | "rorb" | "rol" | "rolb" | "asr" | "asrb" | "asl" | "aslb" | "jmp" | "swab" | "tst" | "tstb"

<misc_single_op_keyword> ::= "rts" | "sxt" | "mark"
<misc_double_op_keyword> ::= "jsr" | "ash" | "als" | "ashc" | "alsc" | "mul" | "mpy" | "div" | "dvd" | "xor" | "sob"

<fp_simple_keyword> ::= "cfcc" | "setf" | "setd" | "seti" | "setl"
<fp_single_op_keyword> ::= "clrf" | "negf" | "absf" | "tstf" | "ldfps" | "stfps" | "sts"
<fp_double_op_keyword> ::= "movf" | "ldf" | "stf" | "movif" | "ldcif" | "movfi" | "stcfi" | "movof" | "ldcdf" | "movfo" | "stcfd" | "movie" |
                           "ldexp" | "movei" | "stexp" | "addf" | "subf" | "mulf" | "divf" | "cmpf" | "modf"

<sys_call_simple_keyword> ::= "close" | "exit" | "fork" | "getuid" | "nice" | "setuid" | "stime" | "time" | "wait"
<sys_call_single_op_keyword> ::= "break" | "chdir" | "fstat" | "gtty" | "stty" | "umount" | "unlink"
<sys_call_double_op_keyword> ::= "chmod" | "chown" | "creat" | "exec" | "link" | "makdir" | "open" | "read" | "seek" |
                                 "signal" | "seek" | "tell" | "write"

<reg_keyword> ::= "r0" | "r1" | "r2" | "r3" | "r4" | "r5" | "sp" | "pc"
<fp_reg_keyword> ::= "fr0" | "fr1" | "fr2" | "fr3" | "fr4" | "fr5"
<identifier> ::= [A-Za-z._~][A-Za-z._~0-9]+ | <escape_sequence>
<escape_sequence> ::= "\n" | "\t" | "\e" | "\0" | "\r" | "\a" | "\p" | "\\" | "\>"
<expression_operator> ::= " " | "+" | "-" | "*" | "\/" | "&" | "|" | ">>" | "<<" | "%" | "!" | "^" *
<number> ::= [0-9]+  # Can be octal constant!
<decimal_constant> ::= [0-9]+"."
<single_char_constant> ::= "'"[A-Za-z]  # Should be any ASCII character except newline
<double_char_constant> ::= """[A-Za-z]{2}  # Should be any ASCII character except newline
```
##System calls
```text
# sys break; addr
# sys chdir; dirname
# sys chmod; name; mode
# sys chown; name; owner
# sys close (file descriptor in r0)
# sys creat; name; mode (file descriptor in r0)
# sys exec; name; args 
#           name: <...\0>
#                 args: arg0; arg1; ...; 0
#                       arg0: <...\0>
#                             arg1: <...\0>
# sys exit (status in r0)
# sys fork
# sys fstat; buf (file descriptor in r0)
# sys getuid
# sys gtty, arg (file descriptor in r0) (arg: .=.+6)
# sys link; name1; name2
# sys makdir; name; mode
# sys mount; special; name; rwflag
# sys nice (priority in r0)
# sys open; name; mode (file descriptor in r0)
# sys read; buffer; nbytes (file descriptor in r0)
# sys seek; offset; ptrname (file descriptor in r0)
# sys setuid (user ID in r0)
# sys signal; sig; label (old value in r0)
# sys stat; name; buf 
# sys stime (time in r0-r1)
# sys stty; arg (file descriptor in r0)
# sys tell; offset; ptrname
# sys time
# sys umount; special
# sys unlink; name
# sys wait (process ID in r0) (status in r1)
# sys write; buffer; nbytes (file descriptor in r0)
```
[Reference](http://man.cat-v.org/unix-6th/2/)
[Kernel source](https://pages.lip6.fr/Pierre.Sens/srcv6/)
