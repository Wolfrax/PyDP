from src.CCconf import compiler
from src.CCinterpreter import CCinterpreter
from src.PPparser import PPparser
from src.CCparser import CCparser
from src.CCSymbols import CCSymbols

import pytest

class Compiler:
    def __init__(self):
        self.src = None
        self.interpreter = CCinterpreter()
        self.compiler = compiler.setup('', True, CCinterpreter(), CCSymbols(self.interpreter.memory),
                                       PPparser(), CCparser())

    def compile(self, src):
        self.__init__()
        self.src = src
        self.compiler.pp_parser.preprocess(src=self.src)

        for c in self.compiler.pp_parser.defines:
            self.compiler.symbols.add(c)

        result = self.compiler.cc_parser.compile(src=self.src)
        ext_decl = self.compiler.cc_parser.prg.decl()
        return result, ext_decl

    def sz(self, type):
        return self.interpreter.memory.sz_of[type]


@pytest.fixture()
def CCompiler():
    return Compiler()