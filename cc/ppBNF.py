#!/usr/bin/python
# -*- coding: utf-8 -*-

# Mats Melander 2023-07-31
__author__ = 'mm'


if __name__ == '__main__':
    with open('test_parser.py') as f:
        data = f.read()

    rules = []
    bnf_flag = False
    def_flag = False

    for ch in data:
        if ch == '@':
            bnf_flag = True
            rules.append(ch)
            continue
        if bnf_flag:
            rules[-1] += ch
            bnf_flag = ch != ')'
            continue

    for r in rules:
        print(r)

