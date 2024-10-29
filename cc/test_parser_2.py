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

    # translation_unit ::= type_specifier ";"
    # type_specifier ::= VOID | CHAR | SHORT | INT | LONG | FLOAT | DOUBLE | SIGNED | UNSIGNED | struct_specifier
    # struct_specifier ::= STRUCT ID variable initializer
    # variable ::= ID
    # initializer ::= "{" initializer_list "}"
    # initializer_list ::= expression | initializer_list "," expression
    # expression ::= ID | CONSTANT

    @_('type_specifier ";"')
    def translation_unit(self, p): self.dump()

    @_('VOID', 'CHAR', 'SHORT', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'SIGNED', 'UNSIGNED',
       'struct_specifier'
       )
    def type_specifier(self, p): self.dump()

    @_('STRUCT ID variable initializer')
    def struct_specifier(self, p): self.dump()

    @_('ID')
    def variable(self, p): self.dump()

    @_('"{" initializer_list "}"')
    def initializer(self, p): self.dump()

    @_('expression',
       'initializer_list "," expression')
    def initializer_list(self, p): self.dump()

    @_('ID', 'CONSTANT')
    def expression(self, p): self.dump()

class CCParser2(Parser):
    start = 'translation_unit'
    tokens = lexer.CLexer.tokens
    debugfile = 'test_parser2.out'

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

    # translation_unit ::= declaration_list
    # declaration_list ::= variable | declaration_list variable
    # variable ::= type_specifier ID initializer ";"
    # type_specifier ::= VOID | CHAR | SHORT | INT | LONG | FLOAT | DOUBLE | SIGNED | UNSIGNED | STRUCT ID
    # initializer ::= "{" initializer_list "}" | ID | CONSTANT | empty
    # initializer_list ::= expression | initializer_list "," expression
    # expression ::= ID | CONSTANT

    @_('declaration_list')
    def translation_unit(self, p): self.dump()

    @_('variable', 'declaration_list variable')
    def declaration_list(self, p): self.dump()

    @_('type_specifier ID initializer ";"')
    def variable(self, p): self.dump()

    @_('VOID', 'CHAR', 'SHORT', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'SIGNED', 'UNSIGNED', 'STRUCT ID')
    def type_specifier(self, p): self.dump()

    @_('"{" initializer_list "}"', 'ID', 'CONSTANT', '')
    def initializer(self, p): self.dump()

    @_('expression', 'initializer_list "," expression')
    def initializer_list(self, p): self.dump()

    @_('ID', 'CONSTANT')
    def expression(self, p): self.dump()


if __name__ == '__main__':
    with open('cc_test.c', 'r') as f:
        prg = f.read()

    logging.basicConfig(filename='test_parser_2.log', filemode='w', level=logging.DEBUG, format='%(message)s')
    log = logging.getLogger('CC_SLYLogger')

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    lex = lexer.CLexer()
    parser = CCParser2()
    result = parser.parse(lex.tokenize(prg))
    print(result)