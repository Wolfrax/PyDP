#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'


if __name__ == '__main__':
    with open('test_parser.py') as f:
        text = f.read().rstrip()

    rules = []
    at_flag = False
    def_flag = False

    # https://stackoverflow.com/questions/31228467/is-in-the-python-something-like-method-findnext-in-string
    pos = -1
    while True:
        pos = text.find('@_(', pos + 1)
        if pos == -1:
            break
        lhs_ind = text.find(')', pos + 1)
        lhs = (text[pos+3:lhs_ind].
               replace(')', '').
               replace('\n', '').
               replace('  ', '').
               replace('\'', ''))
        print(lhs)


    for ch in text:
        if ch.isspace():
            continue

        if ch == '@' and not at_flag:
            at_flag = True
            prod = {'rhs': '', 'lhs': ''}  # new production
            rhs = ''  # right hand side of production
            lhs = ''  # left hand side of production
            continue  # skip @-char
        if at_flag:
            if ch == '(' or ch == '_':
                continue  # skip ( and _
            if ch == ')':
                at_flag = False  # done with rhs of production
                prod['rhs'] = rhs
                def_flag = True
                continue
            else:
                rhs += ch
        if def_flag:
            if ch == '(':
                def_flag = False  # done with lhs of production
                prod['lhs'] = lhs
                rules.append(prod)
                continue
            if  ch == 'd' or ch == 'e' or ch == 'f':
                continue  # skip def
            lhs += ch

#    for r in rules:
#        print(r)

