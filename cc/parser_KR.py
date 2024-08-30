from sly import Parser
import lexer
import logging
import pprint

class CCParser(Parser):
    start = 'translation_unit'
    tokens = lexer.CLexer.tokens
    debugfile = 'parser.out'

    precedence = (
        ('nonassoc', THEN),
        ('nonassoc', ELSE),
        ('left', OR),
        ('left', AND),
        ('left', "|"),
        ('left', "^"),
        ('left', "&"),
        ('left', EQ, NE),
        ('left', "<", ">", LE, GE),
        ('left', SHIFT_LEFT, SHIFT_RIGHT),
        ('left', "+", "-"),
        ('left', "*", "/", "%"),
        ('right', "!", "~", INCR, DECR, SIZEOF),
        ('right', "=", ASSIGN_PLUS, ASSIGN_MINUS, ASSIGN_TIMES, ASSIGN_DIVIDE, ASSIGN_MOD, ASSIGN_RIGHT, ASSIGN_LEFT,
         ASSIGN_AND, ASSIGN_XOR, ASSIGN_OR),
        ('left', "(", ")", "[", "]", ".", POINTER),
    )

    @_('ID', 'CONSTANT', 'STRING_LITERAL', '"(" expression ")"')
    def primary_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('primary_expression',
       'postfix_expression "[" expression "]"',
       'postfix_expression "(" ")"',
       'postfix_expression "(" argument_expression_list ")"',
       'postfix_expression "." ID',
       'postfix_expression POINTER ID',
       'postfix_expression INCR',
       'postfix_expression DECR'
       )
    def postfix_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('assignment_expression',
       'argument_expression_list "," assignment_expression'
       )
    def argument_expression_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('postfix_expression',
       'INCR unary_expression',
       'DECR unary_expression',
       'unary_operator cast_expression',
       'SIZEOF unary_expression',
       'SIZEOF "(" type_name ")"'
       )
    def unary_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('"&"', '"*"', '"+"', '"-"', '"~"', '"!"')
    def unary_operator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('unary_expression',
       '"(" type_name ")" cast_expression')
    def cast_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('cast_expression',
       'multiplicative_expression "*" cast_expression',
       'multiplicative_expression "/" cast_expression',
       'multiplicative_expression "%" cast_expression'
       )
    def multiplicative_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('multiplicative_expression',
       'additive_expression "+" multiplicative_expression',
       'additive_expression "-" multiplicative_expression'
       )
    def additive_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('additive_expression',
       'shift_expression SHIFT_LEFT additive_expression',
       'shift_expression SHIFT_RIGHT additive_expression'
       )
    def shift_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('shift_expression',
       'relational_expression "<" shift_expression',
       'relational_expression ">" shift_expression',
       'relational_expression LE shift_expression',
       'relational_expression GE shift_expression',
       )
    def relational_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('relational_expression',
       'equality_expression EQ relational_expression',
       'equality_expression NE relational_expression'
       )
    def equality_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('equality_expression',
       'and_expression "&" equality_expression'
       )
    def and_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('and_expression',
       'exclusive_or_expression "^" and_expression'
       )
    def exclusive_or_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('exclusive_or_expression',
       'inclusive_or_expression "|" exclusive_or_expression'
       )
    def inclusive_or_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('inclusive_or_expression',
       'logical_and_expression AND inclusive_or_expression'
       )
    def logical_and_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('logical_and_expression',
       'logical_or_expression OR logical_and_expression'
       )
    def logical_or_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('logical_or_expression',
       'logical_or_expression "?" expression ":" conditional_expression'
       )
    def conditional_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('conditional_expression',
       'unary_expression assignment_operator assignment_expression',
       )
    def assignment_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('"="',
       'ASSIGN_TIMES',
       'ASSIGN_DIVIDE',
       'ASSIGN_MOD',
       'ASSIGN_PLUS',
       'ASSIGN_MINUS',
       'ASSIGN_LEFT',
       'ASSIGN_RIGHT',
       'ASSIGN_AND',
       'ASSIGN_XOR',
       'ASSIGN_OR'
       )
    def assignment_operator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('assignment_expression',
       'assignment_expression ","',
       #'expression "," assignment_expression_list'
       #'expression "," assignment_expression',
       #'expression "," assignment_expression ","'
       )
    def expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('assignment_expression delim')
    def assignment_expression_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('","', '')
    def delim(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('conditional_expression')
    def constant_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declaration_specifiers ";"',
       'declaration_specifiers init_declarator_list ";"'
       )
    def declaration(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')


    @_('storage_class_specifier',
       'storage_class_specifier declaration_specifiers',
       'type_specifier',
       'type_specifier declaration_specifiers',
       'type_qualifier',
       'type_qualifier declaration_specifiers')
    def declaration_specifiers(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')


    @_('init_declarator',
       #'init_declarator ","', # ??
       'init_declarator_list "," init_declarator')
    def init_declarator_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declarator',
       'declarator "=" initializer',  # KR initialization with "="
#       'declarator initializer',  # pre-KR initialization without "="
       'declarator pre_kr_initializer',  # pre-KR initialization without "="
       )
    def init_declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    # --- Start pre-KR initialization productions ---

    @_('CONSTANT', 'expression', # <==
       '"{" pre_kr_constant_expression_list "}"',
       )
    def pre_kr_initializer(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('pre_kr_constant_expression',
       'pre_kr_constant_expression "," pre_kr_constant_expression_list'
       )
    def pre_kr_constant_expression_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('expression')
#    @_('expression "," assignment_expression')
    def pre_kr_constant_expression(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    # --- End pre-KR initialization productions ---

    @_('TYPEDEF', 'EXTERN', 'STATIC', 'AUTO', 'REG')
    def storage_class_specifier(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('VOID', 'CHAR', 'SHORT', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'SIGNED', 'UNSIGNED',
       'struct_or_union_specifier',
       'enum_specifier',
       'typedef_name'
       )
    def type_specifier(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('struct_or_union ID "{" struct_declaration_list "}"',
       'struct_or_union "{" struct_declaration_list "}"',
       'struct_or_union ID'
       )
    def struct_or_union_specifier(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('STRUCT', 'UNION')
    def struct_or_union(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('struct_declaration',
       'struct_declaration_list struct_declaration'
       )
    def struct_declaration_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('specifier_qualifier_list struct_declarator_list ";"')
    def struct_declaration(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('type_specifier specifier_qualifier_list',
       'type_specifier',
       'type_qualifier specifier_qualifier_list',
       'type_qualifier'
       )
    def specifier_qualifier_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('struct_declarator',
       'struct_declarator_list "," struct_declarator')
    def struct_declarator_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declarator',
       '":" constant_expression',
       'declarator ":" constant_expression'
       )
    def struct_declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('ENUM "{" enumerator_list "}"',
       'ENUM ID "{" enumerator_list "}"',
       'ENUM ID'
       )
    def enum_specifier(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('enumerator',
       'enumerator_list "," enumerator')
    def enumerator_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('ID',
       'ID "=" constant_expression')
    def enumerator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('CONST', 'VOLATILE')
    def type_qualifier(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('pointer direct_declarator',
       'direct_declarator'
       )
    def declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('ID',
       '"(" declarator ")"',
       'direct_declarator "[" constant_expression "]"',
       'direct_declarator "[" "]"',
       'direct_declarator "(" parameter_type_list ")"',
       'direct_declarator "(" identifier_list ")"',
       'direct_declarator "(" ")"'
       )
    def direct_declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('"*"',
       '"*" type_qualifier_list',
       '"*" pointer',
       '"*" type_qualifier_list pointer'
       )
    def pointer(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('type_qualifier',
       'type_qualifier_list type_qualifier')
    def type_qualifier_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('parameter_list',
       'parameter_list "," ELLIPSIS')
    def parameter_type_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('parameter_declaration',
       'parameter_list "," parameter_declaration'
       )
    def parameter_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declaration_specifiers declarator',
       'declaration_specifiers abstract_declarator',
       'declaration_specifiers'
       )
    def parameter_declaration(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('ID',
       'identifier_list "," ID'
       )
    def identifier_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('specifier_qualifier_list',
       'specifier_qualifier_list abstract_declarator'
       )
    def type_name(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('pointer',
       'direct_abstract_declarator',
       'pointer direct_abstract_declarator'
       )
    def abstract_declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('"(" abstract_declarator ")"',
       '"[" "]"',
       '"[" constant_expression "]"',
       'direct_abstract_declarator "[" "]"',
       'direct_abstract_declarator "[" constant_expression "]"',
       '"(" ")"',
       '"(" parameter_type_list ")"',
       'direct_abstract_declarator "(" ")"',
       'direct_abstract_declarator "(" parameter_type_list ")"'
       )
    def direct_abstract_declarator(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('TYPE_NAME')
    def typedef_name(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('assignment_expression',
       '"{" initializer_list "}"',
       '"{" initializer_list "," "}"'
       )
    def initializer(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('initializer',
       'initializer_list "," initializer'
       )
    def initializer_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('labeled_statement',
       'compound_statement',
       'expression_statement',
       'selection_statement',
       'iteration_statement',
       'jump_statement'
       )
    def statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('ID ":" statement',
       'CASE constant_expression ":" statement',
       'DEFAULT ":" statement'
       )
    def labeled_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('"{" "}"',
       '"{" statement_list "}"',
       '"{" declaration_list "}"',
       '"{" declaration_list statement_list "}"'
       )
    def compound_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declaration',
       'declaration_list declaration'
       )
    def declaration_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('statement',
       'statement_list statement'
       )
    def statement_list(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('";"',
       'expression ";"'
       )
    def expression_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    # https://stackoverflow.com/questions/12731922/reforming-the-grammar-to-remove-shift-reduce-conflict-in-if-then-else
    @_('IF "(" expression ")" statement %prec THEN',
       'IF "(" expression ")" statement ELSE statement',
       'SWITCH "(" expression ")" statement'
    )
    def selection_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('WHILE "(" expression ")" statement',
       'DO statement WHILE "(" expression ")" ";"',
       'FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement'
       )
    def iteration_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('GOTO ID ";"',
       'CONTINUE ";"',
       'BREAK ";"',
       'RETURN ";"',
       'RETURN expression ";"'
       )
    def jump_statement(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('external_declaration',
       'translation_unit external_declaration'
       )
    def translation_unit(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('function_definition',
       'declaration'
       )
    def external_declaration(self, p):
        log.debug(f'{self.production}\n  {self.symstack}')

    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement',
       'declarator declaration_list compound_statement',
       'declarator compound_statement'
       )
    def function_definition(self, p):
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


if __name__ == '__main__':
#    with open('./src/c0_tot.c', 'r') as f:
#    with open('./src/c00.c', 'r') as f:
    with open('cc_test.c', 'r') as f:
        prg = f.read()

    logging.basicConfig(filename='parser.log', filemode='w', level=logging.DEBUG, format='%(message)s')
    log = logging.getLogger('CC_SLYLogger')

    lex = lexer.CLexer()
    parser = CCParser()
    result = parser.parse(lex.tokenize(prg))
    print(result)
