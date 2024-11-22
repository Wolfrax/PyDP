#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'

from sly import Lexer

class PPLexer(Lexer):  # The lexer for the preprocessor
    tokens = {DEFINE, INCLUDE, ID, EXPR, STRING_LITERAL}

    DEFINE = r'[#]define'
    INCLUDE = r'[#]include'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    EXPR = r'(\d+)|([(].*[)])'  # Either a number, or expression such as "(03<<3)"
    STRING_LITERAL = r'"[^"]*"'

    ignore = ' \t'

    @_(r'(?!\#).*\n')
    def ignore_all_but_hash(self, t):
        self.lineno += t.value.count('\n')

    @_(r'[#]\n')
    def ignore_empty_hash_line(self, t):
        self.lineno += t.value.count('\n')

    # https://stackoverflow.com/questions/2130097/difficulty-getting-c-style-comments-in-flex-lex
    @_(r'\/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+\/')  # Match everything within /* ... */
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print("Preprocess - Illegal character '%s'" % t.value[0])
        self.index += 1

class CLexer(Lexer):
    # This is the lexer for UNIX v6 C-language
    # References:
    #   https://sly.readthedocs.io/en/latest/
    #   https://docs.python.org/3/library/re.html

    tokens = {
        AND, ASSIGN_PLUS, ASSIGN_MINUS, ASSIGN_TIMES, ASSIGN_DIVIDE, ASSIGN_MOD, ASSIGN_RIGHT, ASSIGN_LEFT,
        ASSIGN_AND, ASSIGN_XOR, ASSIGN_OR, AUTO,
        BREAK,
        CASE, CHAR, CONSTANT, CONTINUE,
        DECR, DEFAULT, DO, DOUBLE,
        ELSE, EQ, EXTERN,
        FLOAT, FOR,
        GE, GOTO,
        ID, IF, INCR, INT,
        LE,
        NE,
        OR,
        POINTER,
        REG, RETURN,
        SHIFT_LEFT, SHIFT_RIGHT, SIZEOF, STATIC, STRING_LITERAL, STRUCT, SWITCH,
        WHILE}

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
        r'\'.\\?.?\'',  # SINGLECHR
        r'\'\\[0-7]{1,3}\''  # ESCAPEOCT
       )
    def CONSTANT(self, t):
        # NB, a constant starting with 0 is interpreted as octal.
        # print(f'CONSTANT: {t.value}')
        if t.value[0].isdigit():
            if t.value.startswith('0'):
                if len(t.value) == 1:  # Number is 0 only
                    t.value = 0
                else:
                    t.value = int(t.value[1:], 8)
            else:
                t.value = int(t.value)
        return t

    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    ID['auto'] = AUTO
    ID['break'] = BREAK
    ID['case'] = CASE
    ID['char'] = CHAR
    ID['continue'] = CONTINUE
    ID['default'] = DEFAULT
    ID['do'] = DO
    ID['double'] = DOUBLE
    ID['else'] = ELSE
    ID['extern'] = EXTERN
    ID['float'] = FLOAT
    ID['for'] = FOR
    ID['goto'] = GOTO
    ID['if'] = IF
    ID['int'] = INT
    ID['register'] = REG
    ID['return'] = RETURN
    ID['sizeof'] = SIZEOF
    ID['static'] = STATIC
    ID['struct'] = STRUCT
    ID['switch'] = SWITCH
    ID['while'] = WHILE

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

    STRING_LITERAL = r'"[^"]*"'

    def error(self, t):
        print('CLexer - Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1

if __name__ == '__main__':
    fn = ['cc_test.c'] #, './src/cvopt.c', 'cc_test.c']
    with open(fn[0]) as f:
        data = f.read()

    lexer = CLexer()
    for tok in lexer.tokenize(data):
        print(tok)