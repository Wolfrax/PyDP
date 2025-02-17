import CCparser
import PPparser
import CCSymbols
import CCinterpreter

# This is the declaration object interfacing the AST and the Symbol tables
class CCDecl:
    def __init__(self):
        pass

    def setattrs(self, **kwargs):
        for key, value in kwargs.items():
            if self.hasattr(key) and isinstance(value, list):
                new_value = getattr(self, key) + value  # merge only if lists
                setattr(self, key, new_value)
            else:
                setattr(self, key, value)
        return self

    def hasattr(self, attr):
        return hasattr(self, attr)

    def delattr(self, attr):
        if hasattr(self, attr):
            delattr(self, attr)

    def items(self):
        return self.__dict__.items()

    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=4)

class CC:
    def __init__(self, fn, verbose, interpret):
        self.file = fn
        self.verbose = verbose
        self.interpreter = CCinterpreter.CCinterpreter() if interpret else None
        self.symbols = CCSymbols.CCSymbols(self.interpreter.memory if self.interpreter else None)
        self.pp_parser = PPparser.PPparser()
        self.cc_parser = CCparser.CCparser()

def init(fn, verbose, interpret):
    global compiler

    compiler=CC(fn=fn, verbose=verbose, interpret=interpret)