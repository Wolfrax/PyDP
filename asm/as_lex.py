#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2020-10-14
__author__ = 'mm'

from sly import Lexer


class AsLexer(Lexer):
    # This is the lexer for UNIX v6 assembler
    # See also: https://en.wikipedia.org/wiki/PDP-11_architecture

    tokens = {ID,
              SIMPLE_KEYWORD, BRANCH_KEYWORD, EXT_BRANCH_KEYWORD, SINGLE_OP_KEYWORD, DOUBLE_OP_KEYWORD,
              MISC_SINGLE_OP_KEYWORD, MISC_DOUBLE_OP_KEYWORD,
              FP_SIMPLE_KEYWORD, FP_SINGLE_OP_KEYWORD, FP_DOUBLE_OP_KEYWORD,
              SYSCALL, SYSCALL_SERVICE,
              REG_KEYWORD, FP_REG_KEYWORD,
              PSEUDO_OP_SIMPLE, PSEUDO_OP_IF, PSEUDO_OP_GLOBL, PSEUDO_OP_COMM, PSEUDO_OP_BYTE,
              DIV, SHIFT_R, SHIFT_L,
              TEMP_SYM, CONST_DEC, CONST_OCT, CONST_CHAR, CONST_CHAR_META, CONST_DCHAR,
              RELOCATION_OP, LOCATION_OP,
              NAME_LABEL, NUM_LABEL, STR, SEPARATOR}

    literals = {',', ';', ':', '$', '(', ')', '[', ']', '=', '+', '-', '*', '&', '|', '%', '!', '^'}

    ignore = ' \t'
    ignore_comment = r'/.*'

    DIV     = r'\\/'
    SHIFT_R = r'>>'
    SHIFT_L = r'<<'

    NUM_LABEL = r'[0-9]?:'
    NAME_LABEL = r'[\._a-zA-Z0-9]+:'

    SYSCALL = r'sys'
    SYSCALL_SERVICE = r'close|exit|fork|getuid|nice|setuid|stime|time|wait|' \
                      r'break|chdir|fstat|gtty|stty|umount|unlink|' \
                      r'chmod|chown|creat|exec|link|makdir|open|read\s|seek|signal|stat|tell|write|mount'

    REG_KEYWORD = r'r0|r1|r2|r3|r4|r5|sp|pc'
    FP_REG_KEYWORD = r'fr0|fr1|fr2|fr3|fr4|fr5'

    SIMPLE_KEYWORD = r'clc|clv|clz|cln|sec|sen|sev'

    # NB, keyword are identifed by ending on word-boundary (\b) and must no start with $ (?<!\$)
    # Ie, "abrc" will not be identified asm "br" keyword, neither will "$br" (this exists)
    BRANCH_KEYWORD = r'(?<!\$)br\b|' \
                     r'(?<!\$)bne\b|' \
                     r'(?<!\$)beq\b|' \
                     r'(?<!\$)bge\b|' \
                     r'(?<!\$)blt\b|' \
                     r'(?<!\$)bgt\b|' \
                     r'(?<!\$)ble\b|' \
                     r'(?<!\$)bpl\b|' \
                     r'(?<!\$)bmi\b|' \
                     r'(?<!\$)bhis\b|' \
                     r'(?<!\$)bhi\b|' \
                     r'(?<!\$)blos\b|' \
                     r'(?<!\$)bvc\b|' \
                     r'(?<!\$)bvs\b|' \
                     r'(?<!\$)bec\b|' \
                     r'(?<!\$)bcc\b|' \
                     r'(?<!\$)blo\b|' \
                     r'(?<!\$)bcs\b|' \
                     r'(?<!\$)bes\b'
    EXT_BRANCH_KEYWORD = r'(?<!\$)jbr\b|' \
                         r'(?<!\$)jne\b|' \
                         r'(?<!\$)jeq\b|' \
                         r'(?<!\$)jge\b|' \
                         r'(?<!\$)jlt\b|' \
                         r'(?<!\$)jgt\b|' \
                         r'(?<!\$)jle\b|' \
                         r'(?<!\$)jpl\b|' \
                         r'(?<!\$)jmi\b|' \
                         r'(?<!\$)jhis\b|' \
                         r'(?<!\$)jhi\b|' \
                         r'(?<!\$)jlos\b|' \
                         r'(?<!\$)jvc\b|' \
                         r'(?<!\$)jvs\b|' \
                         r'(?<!\$)jec\b|' \
                         r'(?<!\$)jcc\b|' \
                         r'(?<!\$)jlo\b|' \
                         r'(?<!\$)jcs\b|' \
                         r'(?<!\$)jes\b'
    SINGLE_OP_KEYWORD = r'(?<!\$)clrb\b|' \
                        r'(?<!\$)clr\b|' \
                        r'(?<!\$)comb\b|' \
                        r'(?<!\$)com\b|' \
                        r'(?<!\$)incb\b|' \
                        r'(?<!\$)inc\b|' \
                        r'(?<!\$)decb\b|' \
                        r'(?<!\$)dec\b|' \
                        r'(?<!\$)negb\b|' \
                        r'(?<!\$)neg\b|' \
                        r'(?<!\$)adcb\b|' \
                        r'(?<!\$)adc\b|' \
                        r'(?<!\$)sbcb\b|' \
                        r'(?<!\$)sbc\b|' \
                        r'(?<!\$)rorb\b|' \
                        r'(?<!\$)ror\b|' \
                        r'(?<!\$)rolb\b|' \
                        r'(?<!\$)rol\b|' \
                        r'(?<!\$)asrb\b|' \
                        r'(?<!\$)asr\b|' \
                        r'(?<!\$)aslb\b|' \
                        r'(?<!\$)asl\b|' \
                        r'(?<!\$)jmp\b|' \
                        r'(?<!\$)swab\b|' \
                        r'(?<!\$)tstb\b|' \
                        r'(?<!\$)tst\b'
    DOUBLE_OP_KEYWORD = r'(?<!\$)movb\b|' \
                        r'(?<!\$)mov\b|' \
                        r'(?<!\$)cmpb\b|' \
                        r'(?<!\$)cmp\b|' \
                        r'(?<!\$)bitb\b|' \
                        r'(?<!\$)bit\b|' \
                        r'(?<!\$)bicb\b|' \
                        r'(?<!\$)bic\b|' \
                        r'(?<!\$)bisb\b|' \
                        r'(?<!\$)bis\b|' \
                        r'(?<!\$)add\b|' \
                        r'(?<!\$)sub\b'
    MISC_SINGLE_OP_KEYWORD = r'(?<!\$)rts\b|' \
                             r'(?<!\$)sxt\b|' \
                             r'(?<!\$)mark\b'
    MISC_DOUBLE_OP_KEYWORD = r'(?<!\$)jsr\b|' \
                             r'(?<!\$)ashc\b|' \
                             r'(?<!\$)ash\b|' \
                             r'(?<!\$)alsc\b|' \
                             r'(?<!\$)als\b|' \
                             r'(?<!\$)mul\b|' \
                             r'(?<!\$)mpy\b|' \
                             r'(?<!\$)div\b|' \
                             r'(?<!\$)dvd\b|' \
                             r'(?<!\$)xor\b|' \
                             r'(?<!\$)sob\b'

    # For definitions, see floating point emulator (s3/fp1-3.s)
    FP_SIMPLE_KEYWORD = r'(?<!\$)cfcc\b|' \
                        r'(?<!\$)setf\b|' \
                        r'(?<!\$)setd\b|' \
                        r'(?<!\$)seti\b|' \
                        r'(?<!\$)setl\b'
    FP_SINGLE_OP_KEYWORD = r'(?<!\$)clrf\b|' \
                           r'(?<!\$)negf\b|' \
                           r'(?<!\$)absf\b|' \
                           r'(?<!\$)tstf\b|' \
                           r'(?<!\$)ldfps\b|' \
                           r'(?<!\$)stfps\b|' \
                           r'(?<!\$)sts\b'
    FP_DOUBLE_OP_KEYWORD = r'(?<!\$)movf\b|' \
                           r'(?<!\$)ldf\b|' \
                           r'(?<!\$)stf\b|' \
                           r'(?<!\$)movif\b|' \
                           r'(?<!\$)ldcif\b|' \
                           r'(?<!\$)movfi\b|' \
                           r'(?<!\$)stcfi\b|' \
                           r'(?<!\$)movof\b|' \
                           r'(?<!\$)ldcdf\b|' \
                           r'(?<!\$)movfo\b|' \
                           r'(?<!\$)stcfd\b|' \
                           r'(?<!\$)movie\b|' \
                           r'(?<!\$)ldexp\b|' \
                           r'(?<!\$)movei\b|' \
                           r'(?<!\$)stexp\b|' \
                           r'(?<!\$)addf\b|' \
                           r'(?<!\$)subf\b|' \
                           r'(?<!\$)mulf\b|' \
                           r'(?<!\$)divf\b|' \
                           r'(?<!\$)cmpf\b|' \
                           r'(?<!\$)modf\b'

    PSEUDO_OP_SIMPLE = r'\.even|\.endif|\.text|\.data|\.bss'
    PSEUDO_OP_IF     = r'\.if'
    PSEUDO_OP_GLOBL  = r'\.globl'
    PSEUDO_OP_COMM   = r'\.comm'
    PSEUDO_OP_BYTE   = r'\.byte'

    RELOCATION_OP = r'\.\.'
    LOCATION_OP = r'\.'

    STR = r'<.+>'

    # < escape_sequence >::= "\n" | "\t" | "\e" | "\0" | "\r" | "\a" | "\p" | "\\" | "\>"
    ID = r'[a-zA-Z._~][a-zA-Z0-9._~]*'

    TEMP_SYM    = r'[0-9][f|b]'
    CONST_DEC   = r'[0-9]+[\.]'
    CONST_OCT   = r'[0-9]+'
    CONST_DCHAR = r'".{2}[\\n]?'

    @_(r'\n+|;')
    def SEPARATOR(self, t):
        self.lineno += t.value.count('\n')
        return t

    CONST_CHAR_META = r'\'\\.'
    CONST_CHAR  = r'\'.'


if __name__ == '__main__':
    data_str = """/
/

/ PDP-11 assembler pass 0

indir	= 0

    jmp	start
go:
    jsr	pc,assem
    movb	pof,r0
    sys	write; outbuf; 512.

    <r0\0\0\0\0\0\>;    24;000000
"""
    data_str2 = """
    clr	*curarg
    jsr	r5,filerr; '\Statementn
    mov	(sp)+,r0
    """
    data_str3 = """add	$'0,r3"""
    data_str4 = """cmp	r4,$'\n"""
    data_str5 = """add	$'0,r3"""
    data_str6 = """fpass2:"""
    data_str7 = """mov	(r5)+,r0"""
    data_str8 = """jsr	pc,readop"""
    data_str9 = """bhis	1f"""
    data_str10 = """asl	r0"""
    data_str11 = """sys	close"""
    data_str12 = """bic	$!37,r3"""
    data_str13 = """9:	sys	break; 0:end"""
    data_str14 = """jmp	*1f-2(r1)"""
    data_str15 = """jsr	pc,addres"""
    data_str16 = """mov	savdot-[2*25](r0),dot"""
    data_str17 = """br .+4"""
    data_str18 = """a.tmp1:	</tmp/atm1a\0>"""
    data_str19 = """br	oprand"""
    data_str20 = """curfbr:	.=.+10."""
    data_str21 = """mov	$..,dotdot"""
    data_str22 = """9:	sys	write; 0:..; .."""
    data_str23 = """cmp	(sp),$br """
    data_str24 = """cmp	r4,$5"""
    data_str25 = """jsr	r5,fcreat; a.tmp3"""
    data_str26 = """9:	sys	write; 0:0; 1:0"""
    data_str27 = """9:	sys	stat; 0:..; outbuf """
    data_str28 = """02"""
    with open('src/as18.s', 'r') as f:
        data = f.read()
    lexer = AsLexer()
    for tok in lexer.tokenize(data_str28):
        print('type=%r, value=%r, lineno=%r' % (tok.type, tok.value, tok.lineno))
    print('No of lines {}'.format(lexer.lineno))