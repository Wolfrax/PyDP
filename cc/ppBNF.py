#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'

import sys
import re
import os.path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Need a file name")
        sys.exit()
    else:
        infile = sys.argv[1]
        if os.path.isfile(infile):
            outfile = re.sub('.py', '.bnf', infile)  # Assume extension always as py
        else:
            print(f"File {infile} does not exist")
            sys.exit()

    with open(infile) as f:
        print(f'Opening {infile}\n')
        text = f.read().rstrip()

    rules = []
    lhs_start = -1

    # A production rule in sly follow this scheme:
    #   @_(A, B) def prod(...) which translate to BNF
    #   prod ::= A | B
    # Below: lhs = left hand side, rhs = right hand side

    while True:
        # find the string @_(, the start of a production rule in sly
        lhs_start = text.find('@_(', lhs_start + 1)
        if lhs_start == -1:
            break  # Not found, end the loop
        else:
            lhs_start += 3  # Adjust index to the first char after @_(, the start of the first left hand side rule

        # find end of lhs, exclude the string ")" (negative lookahead in regex below)
        lhs_end = re.search(r'(?!\")\)(?!\")', text[lhs_start:]).span()[0] + lhs_start
        lhs = (text[lhs_start:lhs_end].
               replace('\n', '').
               replace('  ', '').
               replace('\'', ''))
        lhs = re.sub(r',(?!\")', ' |', lhs)  # replace ',' with '|' except when ","
        lhs = re.sub(r'#.*', '', lhs)  # remove any line comments
        rstrip_lhs = re.search(r'\s*\|\s*$', lhs)  # remove trailing |, if any
        if rstrip_lhs:
            lhs = lhs[:rstrip_lhs.span()[0]]

        rhs_start = text.find('def', lhs_end + 1)
        if rhs_start == -1:
            print(f'def not found from {rhs_start}, should not be')
            break
        else:
            rhs_start += 3
        rhs_end = text.find('(', rhs_start)

        rules.append({'rhs': text[rhs_start+1:rhs_end], 'lhs': lhs })

    with open(outfile, 'w') as f:
        i = 1
        for rule in rules:
            f.write(f'{i}: {rule["rhs"]} ::= {rule["lhs"]}\n\n')
            print(f'{i} {rule["rhs"]} ::= {rule["lhs"]}\n')
            i +=1

        print(f'\nWritten to {outfile}')

