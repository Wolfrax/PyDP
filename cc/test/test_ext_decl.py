import sys
sys.path.append('..')

from cc.CCconf import compiler
from cc.CCinterpreter import CCinterpreter
from cc.PPparser import PPparser
from cc.CCparser import CCparser
from cc.CCSymbols import CCSymbols

interpreter = CCinterpreter()
symbols = CCSymbols(interpreter.memory)
pp_parser = PPparser()
cc_parser = CCparser()

compiler.setup('', True, interpreter, symbols,  pp_parser, cc_parser)

def compile(src_str):
    compiler.pp_parser.preprocess(src_str=src_str)

    for c in compiler.pp_parser.defines:
        compiler.symbols.add(c)

    result = compiler.cc_parser.compile(src_str=src_str)
    ext_decl = compiler.cc_parser.prg.decl()
    return result

def test_var_decl():
    compile("int i;")

