# This is the declaration object interfacing the AST and the Symbol tables
class CCDecl:
    def __init__(self):
        pass

    def setattr(self, **kwargs):
        for key, value in kwargs.items():
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
    def __init__(self):
        self.file = None
        self.verbose = None
        self.interpreter =  None
        self.symbols = None
        self.pp_parser = None
        self.cc_parser = None

    def setup(self, fn, verbose, interpreter, symbols, pp_parser, cc_parser):
        self.file = fn
        self.verbose = verbose
        self.interpreter = interpreter
        self.symbols = symbols
        self.pp_parser = pp_parser
        self.cc_parser = cc_parser

compiler = CC()