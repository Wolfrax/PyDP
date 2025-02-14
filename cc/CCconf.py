import CCparser
import PPparser
import CCSymbols
import CCinterpreter

class CCError(Exception):
    def __init__(self, err):
        self.err = err

    def __str__(self):
        return repr(self.err)

# This is the declaration object interfacing the AST and the Symbol tables
class CCDecl:
    def __init__(self, decl):
        self.decl = decl

class CC:
    def __init__(self, fn, verbose, wd, interpret):
        self.file = fn
        self.verbose = verbose
        self.wd = wd
        self.interpreter = CCinterpreter.CCinterpreter() if interpret else None
        self.symbols = CCSymbols.CCSymbols(self.interpreter.memory if self.interpreter else None)
        self.pp_parser = PPparser.PPparser()
        self.cc_parser = CCparser.CCparser()

def init(fn, verbose, wd, interpret):
    global compiler

    compiler=CC(fn=fn, verbose=verbose, wd=wd, interpret=interpret)