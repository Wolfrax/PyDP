from sly import Parser
import lexer

Defines = {}
Includes = {}

class PPparser(Parser):
    start = 'translation_unit'
    tokens = lexer.PPLexer.tokens
    debugfile = 'PPparser.out'

    @_('list_of_tokens')
    def translation_unit(self, p): pass

    @_('token', 'list_of_tokens token')
    def list_of_tokens(self, p): pass

    @_('define', 'include', 'ID', 'EXPR', 'STRING_LITERAL')
    def token(self, p): pass

    @_('DEFINE ID EXPR')
    def define(self, p):
        if not p.ID in Defines:
            # NB EXPR can be a constant integer number, or an expression such as "(03<<3)"
            Defines[p.ID] = {'lineno': p.lineno, 'expr': p.EXPR, 'nr': int(p.EXPR) if p.EXPR.isnumeric() else None}

    @_('INCLUDE STRING_LITERAL')
    def include(self, p):
        if not p.STRING_LITERAL in Includes:
            Includes[p.STRING_LITERAL.strip('"')] = {'lineno': p.lineno, 'flag': False}


if __name__ == '__main__':
    dir = './src/'
    fn = ['c0_tot.c', 'c1_tot.c', 'c2_tot.c', 'cvopt.c']
    ind = 0

    pp_parser = PPparser()
    pp_lex = lexer.PPLexer()

    for i in range(ind, len(fn)):
        print(f'Parsing file {fn[i]}')

        with open(dir + fn[i], 'r') as f:
            result = pp_parser.parse(pp_lex.tokenize(f.read()))
            pp_parser.restart()

    for k, v in Includes.items():
        print(f'{k}')

        with open(dir + k, 'r') as f:
            if Includes[k]['flag']: continue
            result = pp_parser.parse(pp_lex.tokenize(f.read()))
            pp_parser.restart()
            Includes[k]['flag'] = True

    print(Includes)
    print(Defines)


