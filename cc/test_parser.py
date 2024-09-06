from sly import Parser
import lexer
import logging
import sys


class CCParser(Parser):
    start = 'translation_unit'
    tokens = lexer.CLexer.tokens
    debugfile = 'test_parser.out'

    def dump(self):
        log.debug(f'{self.production}\n  {self.symstack}')

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


    @_('declaration')
    def translation_unit(self, p): self.dump()

    @_('type_specifier')
    def declaration(self, p): self.dump()

    @_('VOID', 'CHAR', 'SHORT', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'SIGNED', 'UNSIGNED',
       'struct_or_union_specifier'
       )
    def type_specifier(self, p): self.dump()

    @_('struct_or_union ID ID "{" struct_declaration_list "}"')
    def struct_or_union_specifier(self, p): self.dump()

    @_('STRUCT', 'UNION')
    def struct_or_union(self, p): self.dump()

    @_('struct_declaration',
       'struct_declaration_list struct_declaration'
       )
    def struct_declaration_list(self, p): self.dump()

    @_('struct_declarator',
       'struct_declarator_list "," struct_declarator')
    def struct_declarator_list(self, p): self.dump()

    @_('struct_declarator_list ";"')
    def struct_declaration(self, p): self.dump()

    @_('declarator')
    def struct_declarator(self, p): self.dump()

    @_('direct_declarator')
    def declarator(self, p): self.dump()

    @_('ID', 'CONSTANT',
       'direct_declarator "[" constant_expression "]"',
       'direct_declarator "[" "]"',
       )
    def direct_declarator(self, p): self.dump()

    @_('ID', 'CONSTANT')
    def constant_expression(self, p): self.dump()


if __name__ == '__main__':
    with open('cc_test.c', 'r') as f:
        prg = f.read()

    logging.basicConfig(filename='test_parser.log', filemode='w', level=logging.DEBUG, format='%(message)s')
    log = logging.getLogger('CC_SLYLogger')

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    lex = lexer.CLexer()
    parser = CCParser()
    result = parser.parse(lex.tokenize(prg))
    print(result)