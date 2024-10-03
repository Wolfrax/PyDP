#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'

from sly import Lexer


class BNFLexer(Lexer):

    tokens = {DEF, EXPR}

    literals = {'@', '_', '(', ')', ','}

    ignore = ' \t'


    DEF = 'def'
    EXPR = r"'(\w+)'"
#    EXPR = r"([\"'])((?:\\\1|(?:(?!\1)).)*)(\1)"
#    EXPR = /'[^'"]*'(?=(?:[^"]*"[^"]*")*[^"]*$)/g

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1

if __name__ == '__main__':
    with open('test_parser.py') as f:
        data = f.read()

    lexer = BNFLexer()
    for tok in lexer.tokenize(data):
        print(tok)
