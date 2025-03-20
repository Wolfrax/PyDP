import argparse
import os
import logging
import cc
from cc import CCconf
import pytest

class TestCompiler:
    def __init__(self):
        self.compiler = None
    def setup(self, compiler):
        self.compiler = compiler

test_compiler = TestCompiler().setup(cc.CCconf.CC(fn='', verbose=False, interpret=False))

def compile(src_str):
    compiler = test_compiler.compiler
    compiler.pp_parser.preprocess(src_str=src_str)

    for c in compiler.pp_parser.defines:
        compiler.symbols.add(c)

    result = compiler.cc_parser.compile(src_str=src_str)
    ext_decl = compiler.cc_parser.prg.decl()
    return result

def test_var_decl():
    compile("int i;")

if __name__ == '__main__':
    compiler = test_compiler.compiler



