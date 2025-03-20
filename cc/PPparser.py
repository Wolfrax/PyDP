from sly import Parser
import pprint
from cc.CClexer import PPLexer, CLexer
from cc.CCconf import CCDecl

class PPparser(Parser):
    start = 'translation_unit'
    tokens = PPLexer.tokens
    #debugfile = 'PPparser.out'

    def __init__(self):
        self.defines = []
        self.includes = {}
        self.result = None
        self.lex = PPLexer()

    def visited(self, k):
        return self.includes[k]['_visited']

    def set_visited(self, k, val=True):
        self.includes[k]['_visited'] = val

    def preprocess(self, fn):
        with open(fn, 'r') as f:
            print(f"Preprocessing {fn}")
            self.result = self.parse(self.lex.tokenize(f.read()))
            self.restart()

        for k in self.includes:
            with open(k, 'r') as f:
                print(f"Preprocessing {k}")
                if self.visited(k): continue
                self.result = self.parse(self.lex.tokenize(f.read()))
                self.restart()
                self.set_visited(k)

        for k in self.includes:
            self.set_visited(k, False)

        return self.result

    def error(self, p):
        print("Error in preprocessing")
        if not p:
            print("End of File!")
            return

    @_('list_of_tokens')
    def translation_unit(self, p): pass

    @_('token', 'list_of_tokens token')
    def list_of_tokens(self, p): pass

    @_('define', 'include', 'ID', 'EXPR', 'STRING_LITERAL')
    def token(self, p): pass

    @_('DEFINE ID EXPR')
    def define(self, p):
        if p.EXPR.isnumeric():
            val = int(p.EXPR)
        else:
            try:
                val = float(p.EXPR)
            except ValueError:
                val = None

        # NB EXPR can be a constant integer number, or an expression such as "(03<<3)", then val is None
        self.defines.append([CCDecl().setattr(ctx=['const'], lineno=p.lineno, name=p.ID, expression=p.EXPR, value=val)])

    @_('INCLUDE STRING_LITERAL')
    def include(self, p):
        if not p.STRING_LITERAL in self.includes:
            self.includes[p.STRING_LITERAL.strip('"')] = {'_lineno': p.lineno, '_visited': False}

if __name__ == '__main__':
    dir = './src/'
    #fn = ['c0_tot.c', 'c1_tot.c', 'c2_tot.c', 'cvopt.c']
    fn = ['c00.c']

    pp_parser = PPparser()
    for i in range(len(fn)):
        print(pp_parser.preprocess(fn[i], wd=dir))

    print("Includes")
    pprint.pp(pp_parser.includes)
    print("Defines")
    pprint.pp(pp_parser.defines)
