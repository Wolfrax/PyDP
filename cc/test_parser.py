from sly import Parser
import lexer
import logging

class CCParser(Parser):
    start = 'translation_unit'
    tokens = lexer.CLexer.tokens
    debugfile = 'test_parser.out'

    def plog(self):
        def function_wrapper():
            log.debug(f'{self.production}\n  {self.symstack}')

        return function_wrapper

    def error(self, p):
        print(f'\n*** ERROR ***\n')
        if p:
            print(f'Syntax error at [{p.lineno}:{p.index}] @token {p.type} = {p.value}')
            print(f'\tProduction: {self.production}')
            print(f'\tsymstack is:')
            for sym in self.symstack:
                print(f'\t{sym}')

        else:
            print("Syntax error at EOF")

    @plog
    @_('declaration')
    def translation_unit(self, p): pass

    @plog
    @_('type_specifier')
    def declaration(self, p): pass

    @plog
    @_('VOID', 'CHAR', 'SHORT', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'SIGNED', 'UNSIGNED',
       'struct_or_union_specifier'
       )
    def type_specifier(self, p): pass

    @plog
    @_('struct_or_union ID "{" struct_declaration_list "}"')
    def struct_or_union_specifier(self, p): pass

    @plog
    @_('STRUCT', 'UNION')
    def struct_or_union(self, p): pass

    @plog
    @_('struct_declaration',
       'struct_declaration_list struct_declaration'
       )
    def struct_declaration_list(self, p): pass

    @plog
    @_('struct_declarator',
       'struct_declarator_list "," struct_declarator')
    def struct_declarator_list(self, p): pass

    @plog
    @_('struct_declarator_list ";"')
    def struct_declaration(self, p): pass

    @plog
    @_('declarator')
    def struct_declarator(self, p): pass

    @plog
    @_('direct_declarator')
    def declarator(self, p): pass

    @plog
    @_('ID',
       'direct_declarator "[" constant_expression "]"',
       'direct_declarator "[" "]"',
       )
    def direct_declarator(self, p): pass

    @plog
    @_('ID', 'CONSTANT')
    def constant_expression(self, p): pass


if __name__ == '__main__':
    with open('cc_test.c', 'r') as f:
        prg = f.read()

    logging.basicConfig(filename='test_parser.log', filemode='w', level=logging.DEBUG, format='%(message)s')
    log = logging.getLogger('CC_SLYLogger')

    lex = lexer.CLexer()
    parser = CCParser()
    result = parser.parse(lex.tokenize(prg))
    print(result)