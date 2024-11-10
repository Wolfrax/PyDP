from sly import Parser
import lexer

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
    def define(self, p): pass

    @_('INCLUDE STRING_LITERAL')
    def include(self, p): pass


if __name__ == '__main__':
    fn = ['./src/c0_tot.c', './src/c1_tot.c', './src/c2_tot.c', './src/cvopt.c', './src/c0h.c', './src/c1h.c', './src/c2h.c']
    ind = 0

    for i in range(ind, len(fn)):
        print(f'Parsing file {fn[i]}')

        with open(fn[i], 'r') as f:
            prg = f.read()

        pp_lex = lexer.PPLexer()
        pp_parser = PPparser()
        result = pp_parser.parse(pp_lex.tokenize(prg))
        print(f'Preprocessor {fn[i]}: {result}\n')
