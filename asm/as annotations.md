#How "as" works

## Grammer

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

### close (6, o6)
file descriptor  in r0

```text
movb	pof,r0
sys	close
```
### exec (11, o13)

```text
sys	exec; 2f; 1f
1:
	2f
	a.tmp1
	a.tmp2
	a.tmp3
unglob:
	3f
	0
2:
fpass2:
	</lib/as2\0>
3:
	<-g\0>
```
Call exec with arguments referenced by labels 2 and 1:
* Label 2: string "/lib/as2"
* Label 1: (reference to label 2) string "/lib/as2", 
   * a.tmp1: label with string constant "/tmp/atm1a"
   * a.tmp2: label with string constant "/tmp/atm2a"
   * a.tmp3: label with string constant "/tmp/atm3a"
   * label 3: "-g"
   * 0

C equivalent `execl("/lib/as2", "/lib/as2", "/tmp/atm1a", "/tmp/atm2a", "/tmp/atm3a", "-g", 0)`

```text
char *init "/etc/init";
main ( ) {
  execl (init, init, 0);
  while (1);
}
```

The equivalent assembler program is
```text
sys exec
    init
    initp
    br   .
initp: init
    0
init:  </etc/init\0>
```

"sys exec" is a call to the trap instruction, that will execute the system call exec with 3 arguments:

1. init - the string "/etc/init0" (terminated by 0-byte). 
Is the parameter passed as a reference or as value? Likely as a reference to avoid copying.

TODO - Understand calling conventions

2. initp - pointer to init
3. 0 - standard by exec (in C execl) to have the last argument as 0

"br ." is "branch to location counter (.)" - "while (1)"

### signal (48, o60)

as11.s
======
pass 0 - start file and initializations?
Jump to "start"-label (in as19.s)

labels: go, aexit

aexit: 
- delete (sys unlink) files a.tmp1, a.tmp2, a.tmp3
- exit (sys exit)

define data segment

as12.s
======
pass 1 - 

labels: error, betwen, putw

as13.s
======
pass 1 - 

labels: assem, ealoop, assem1, fbcheck, checkeos

assem1: jump to assem

as14.s
======
pass 1 - 

labels: rname, number, rch

as15.s
======
pass 1 - read/parse char/strings?

labels: readop, _readop, escp, esctab, fixor, retread, rdname, rdnum, squote, dquote, skip, garb, string, rsch, schar

squote: Handle single quote constant char ('a)
dquote: Handle double quote constant char ("aa)
garb: Found garbage character (Error G)

string: Process string statement start (<...)
rsch: Process string statement end (...>)
schar: define two-character escape sequence to represent certain non-grapic characters as bytes:
\n (NL, 012), \t (HT, 011), \e (EOT, 004), \O (NUL, 000), \r (CR, 015), \a (ACK, 006), \p (PFX, 033)

as16.s
======
pass 1 - main parser of expressions

labels: opline, xpr, opl35 (jbr), opl36 (jeq etc), opl13 (double), opl7 (double), op2, opl15 (single operand),
        opl31 (sob), opl6 (branch), opl10 (branch), opl11 (branch), opl16 (.byte), opl17 (< (.ascii)), opl20 (.even),
        opl21 (.if), opl22 (endif), opl23 (.globl), opl25, opl26, opl27, opl32 (.common), address, getx, alp, amin,
        adoll, astar, errora, checkreq, errore, checkrp

errora: Error in address (Error A)
errore: Error in expression (Error E)
checkrp: Error in parentheses (Error ))

as17.s
======
pass 1 - 

labels: expres, advanc, esw1, binop, exnum, brack, oprand, exsw2, excmbin (^), exrsh, exlsh, exmod (%), exadd (+), 
        exsub (-), exand (&), exor (|), exmul (*), exdiv (/), exnot (!), eoprnd, combin, 
        
as18.s
======
pass 1 - 

labels: chartab, namedone, curfb, obufp, symend, curfbr, savdot, bufcnt, hshsiz, hshtab, pof, wordf, fin, fbfil,
        fileflg, errflg, ch, symbol, obufc, outbuf, line, inbfcnt, ifflg, inbfp, nargs, curarg, opfound, savop, numval,
        nxtfb, usymtab, end
        
curfb - usymtab (except hshsiz and hshtab): change value of location (.) operator

as19.s
======
pass 1 - 

labels: symtab, ebsymtab, start, setup