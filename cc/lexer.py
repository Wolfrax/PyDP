#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'

from sly import Lexer


class CLexer(Lexer):
    # This is the lexer for UNIX v6 C-language
    # References:
    #   https://sly.readthedocs.io/en/latest/
    #   https://docs.python.org/3/library/re.html

    tokens = {
        AND, ASSIGN_PLUS, ASSIGN_MINUS, ASSIGN_TIMES, ASSIGN_DIVIDE, ASSIGN_MOD, ASSIGN_RIGHT, ASSIGN_LEFT,
        ASSIGN_AND, ASSIGN_XOR, ASSIGN_OR, AUTO,
        BREAK,
        CASE, CHAR, CONST, CONSTANT, CONTINUE,
        DECR, DEFAULT, DO, DOUBLE,
        ELLIPSIS, ELSE, ENUM, EQ, EXTERN,
        FLOAT, FOR,
        GE, GOTO,
        ID, IF, INCR, INT,
        LE, LONG,
        NE,
        OR,
        POINTER,
        REG, RETURN,
        SHIFT_LEFT, SHIFT_RIGHT, SHORT, SIGNED, SIZEOF, STATIC, STRING_LITERAL, STRUCT, SWITCH,
        TYPEDEF, TYPE_NAME,
        UNION, UNSIGNED,
        VOID, VOLATILE,
        WHILE,
    }

    literals = {'+', '-', '/', '*', ';', '?', ':', '%', '.', '&', '!', '^', '~', ',', '|', '<', '>', '=',
                '(', ')', '{', '}', '[', ']'}

    ignore = ' \t'


    # https://stackoverflow.com/questions/2130097/difficulty-getting-c-style-comments-in-flex-lex
    ignore_comment = r'\/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+\/'   # Match everything within /* ... */
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    ignore_hash = r'\#.*\n'
    def ignore_hash(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # 1.0, -1.0, +1., -.1, -1.0e23, +1e-23, -1e-23
    # https://stackoverflow.com/questions/13252101/regular-expressions-match-floating-point-number-but-not-integer
    @_(# r'[-|+]?0[0-7]+',  # Octal
       # r'[-|+]?\d+',  # Decimal
       # r'[+-]?(?=\d*[.e])(?=\.?\d)\d*\.?\d*(?:[e][+-]?\d+)?',  # FLOAT_CONST
       # Note, we should not scan signs in front of digits, if we do expressions such as "a-1" will be scanned
       # as ID CONSTANT (which is grammatically wrong), but should be scanned as ID "-" CONSTANT
       # A declaration with intializations, such as "int peeksym -1;"  should be scanned as
       # INT ID "-" CONSTANT (value = 1), not as INT ID CONSTANT (value = -1)
       r'0[0-7]+',  # Octal
       r'\d+',  # Decimal
       r'(?=\d*[.e])(?=\.?\d)\d*\.?\d*(?:[e][+-]?\d+)?',  # FLOAT_CONST
       r'\'\\.\'', # ESCAPECHR
       r'\'.?\'',  # SINGLECHR
       r'\'\\[0-7]{1,3}\''  # ESCAPEOCT
       )
    def CONSTANT(self, t):
        # NB, a constant starting with 0 is interpreted as octal.
        if t.value[0].isdigit():
            if t.value.startswith('0'):
                if len(t.value) == 1:  # Number is 0 only
                    t.value = 0
                else:
                    t.value = int(t.value[1:], 8)
            else:
                t.value = int(t.value)
        print(f"CONSTANT = {t.value} @lineno: {t.lineno}")
        return t

    STRING_LITERAL = r'"[^"]*"'

    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    ID['auto'] = AUTO
    ID['break'] = BREAK
    ID['case'] = CASE
    ID['char'] = CHAR
    ID['const'] = CONST
    ID['continue'] = CONTINUE
    ID['default'] = DEFAULT
    ID['do'] = DO
    ID['double'] = DOUBLE
    ID['else'] = ELSE
    ID['enum'] = ENUM
    ID['extern'] = EXTERN
    ID['float'] = FLOAT
    ID['for'] = FOR
    ID['goto'] = GOTO
    ID['if'] = IF
    ID['int'] = INT
    ID['long'] = LONG
    ID['register'] = REG
    ID['return'] = RETURN
    ID['short'] = SHORT
    ID['signed'] = SIGNED
    ID['sizeof'] = SIZEOF
    ID['static'] = STATIC
    ID['struct'] = STRUCT
    ID['switch'] = SWITCH
    ID['typedef'] = TYPEDEF
    ID['type_name'] = TYPE_NAME
    ID['union'] = UNION
    ID['unsigned'] = UNSIGNED
    ID['void'] = VOID
    ID['volatile'] = VOLATILE
    ID['while'] = WHILE

#    @_(r'#\n')
#    def HASH(self, t):
#        # Single '#'-character (on first row) => Invoke preprocessor)
#        self.lineno += 1
#        return t

#    INCLUDE = r'#[ \t]*include'
#    DEFINE = r'#[ \t]*define'

    POINTER = r'->'
    OR = r'\|\|'
    AND = r'&&'
    SHIFT_RIGHT = r'>>'
    SHIFT_LEFT = r'<<'
    LE = r'<='
    GE = r'>='
    EQ = r'=='
    NE = r'!='
    INCR = r'\+\+'
    DECR = r'--'
    ASSIGN_PLUS = r'=\+'
    ASSIGN_MINUS = '=-'
    ASSIGN_TIMES = r'=\*'
    ASSIGN_DIVIDE = r'=/'
    ASSIGN_MOD = r'=%'
    ASSIGN_RIGHT = r'=>>'
    ASSIGN_LEFT = r'=<<'
    ASSIGN_AND = r'=&'
    ASSIGN_XOR = r'=\^'
    ASSIGN_OR = r'=\|'
    ELLIPSIS = r'\.\.\.'


    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1

if __name__ == '__main__':
#    with open('./src/c00.c') as f:
    with open('cc_test.c') as f:
        data = f.read()

    lexer = CLexer()
    for tok in lexer.tokenize(data):
        print(tok)