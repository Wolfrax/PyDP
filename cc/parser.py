from sly import Parser
import lexer

class CCParser(Parser):
    tokens = lexer.CLexer.tokens
    debugfile = 'parser.out'

    precedence = (
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
        ('right', "!", "~", STAR_EXPR, AND_EXPR, MINUS_EXPR, NOT_EXPR, BNOT_EXPR, INCR, DECR, SIZEOF),
        ('left', ".", POINTER),
        ('right', "=", ASSIGN_PLUS, ASSIGN_MINUS, ASSIGN_TIMES, ASSIGN_DIVIDE, ASSIGN_MOD, ASSIGN_RIGHT, ASSIGN_LEFT,
         ASSIGN_AND, ASSIGN_XOR, ASSIGN_OR)
    )

    @_('external_definition program')
    def program(self, p):
        pass

    @_('external_definition')
    def program(self, p):
        pass

    @_('function_definition', 'declaration', 'pp_hash', 'pp_include', 'pp_define') #?
    def external_definition(self, p):
        pass

    @_('HASH')
    def pp_hash(self, p):
        pass

    @_('INCLUDE CONSTANT')
    def pp_include(self, p):
        pass

    @_('DEFINE CONSTANT')
    def pp_define(self, p):
        pass

    @_('data_definition')
    def external_definition(self, p):
        pass

    @_('type_specifier_opt function_declarator function_body')
    def function_definition(self, p):
        pass

    @_('declarator "(" parameter_list_opt ")"')
    def function_declarator(self, p):
        pass

    @_('parameter_list')
    def parameter_list_opt(self, p):
        pass

    @_('empty')
    def parameter_list_opt(self, p):
        pass

    @_('ID')
    def parameter_list(self, p):
        pass

    @_('ID "," parameter_list')
    def parameter_list(self, p):
        pass

    @_('type_decl_list function_statement')
    def function_body(self, p):
        pass

    @_('"{" declarator_list_opt statement_list "}"')
    def function_statement(self, p):
        pass

    @_('declarator_list')
    def declarator_list_opt(self, p):
        pass

    @_('empty')
    def declarator_list_opt(self, p):
        pass

    @_('extern_opt type_specifier_opt init_declarator_list_opt ";"',)
    def data_definition(self, p):
        pass

    @_('init_declarator_list')
    def init_declarator_list_opt(self, p):
        pass

    @_('empty')
    def init_declarator_list_opt(self, p):
        pass

    @_('type_specifier')
    def type_specifier_opt(self, p):
        pass

    @_('empty')
    def type_specifier_opt(self, p):
        pass

    @_('EXTERN')
    def extern_opt(self, p):
        pass

    @_('empty')
    def extern_opt(self, p):
        pass

    @_('init_declarator', 'init_declarator "," init_declarator_list')
    def init_declarator_list(self, p):
        pass

    @_('declarator initializer_opt')
    def init_declarator(self, p):
        pass

    @_('initializer')
    def initializer_opt(self, p):
        pass

    @_('empty')
    def initializer_opt(self, p):
        pass

    @_('CONSTANT', '"{" constant_expression_list "}"')
    def initializer(self, p):
        pass

    @_('constant_expression', 'constant_expression "," constant_expression_list')
    def constant_expression_list(self, p):
        pass

    @_('expression')
    def constant_expression(self, p):
        pass

    @_('primary')
    def expression(self, p):
        pass

    @_('"*" expression %prec STAR_EXPR',
       '"&" expression %prec AND_EXPR',
       '"-" expression %prec MINUS_EXPR',
       '"!" expression %prec NOT_EXPR',
       '"~" expression %prec BNOT_EXPR')
    def expression(self, p):
        pass

    @_('INCR lvalue', 'DECR lvalue')
    def expression(self, p):
        pass

    @_('lvalue INCR', 'lvalue DECR')
    def expression(self, p):
        pass

    @_('SIZEOF expression')
    def expression(self, p):
        pass

    @_('expression binop expression')
    def expression(self, p):
        pass

    @_('expression "?" expression ":" expression')
    def expression(self, p):
        pass

    @_('lvalue asgnop expression')
    def expression(self, p):
        pass

    @_('expression "," expression')
    def expression(self, p):
        pass

    @_('ID')
    def primary(self, p):
        pass

    @_('CONSTANT')
    def primary(self, p):
        pass

    @_('"(" expression ")"')
    def primary(self, p):
        pass

    @_('primary "(" expression_list_opt ")"')
    def primary(self, p):
        pass

    @_('expression_list')
    def expression_list_opt(self, p):
        pass

    @_('empty')
    def expression_list_opt(self, p):
        pass

    @_(' expression', 'expression "," expression_list')
    def expression_list(self, p):
        pass

    @_('primary "[" expression "]"')
    def primary(self, p):
        pass

    @_('lvalue "." ID')
    def primary(self, p):
        pass

    @_('primary POINTER ID')
    def primary(self, p):
        pass

    @_('ID')
    def lvalue(self, p):
        pass

    @_('primary "[" expression "]"')
    def lvalue(self, p):
        pass

    @_('lvalue "." ID')
    def lvalue(self, p):
        pass

    @_('primary POINTER ID')
    def lvalue(self, p):
        pass

    @_('"*" expression')
    def lvalue(self, p):
        pass

    @_('"(" lvalue ")"')
    def lvalue(self, p):
        pass

    @_('"*"', '"/"', '"%"' )
    def binop(self, p):
        pass

    @_('"+"', '"-"')
    def binop(self, p):
        pass

    @_('SHIFT_LEFT', 'SHIFT_RIGHT')
    def binop(self, p):
        pass

    @_('"<"', '">"', 'LE', 'GE')
    def binop(self, p):
        pass

    @_('EQ', 'NE')
    def binop(self, p):
        pass

    @_('"&"')
    def binop(self, p):
        pass

    @_('"^"')
    def binop(self, p):
        pass

    @_('"|"')
    def binop(self, p):
        pass

    @_('AND')
    def binop(self, p):
        pass

    @_('OR')
    def binop(self, p):
        pass

    @_('"="', 'ASSIGN_PLUS', 'ASSIGN_MINUS', 'ASSIGN_TIMES', 'ASSIGN_DIVIDE', 'ASSIGN_MOD',
       'ASSIGN_RIGHT', 'ASSIGN_LEFT', 'ASSIGN_AND', 'ASSIGN_XOR', 'ASSIGN_OR')
    def asgnop(self, p):
        pass

    @_('empty')
    def type_specifier(self, p):
        pass

    @_('decl_specifiers declarator_list ";"', 'decl_specifiers')
    def declaration(self, p):
        pass

    @_('type_specifier', 'sc_specifier', 'type_specifier sc_specifier', 'sc_specifier type_specifier')
    def decl_specifiers(self, p):
        pass

    @_('AUTO', 'STATIC', 'EXTERN', 'REG')
    def sc_specifier(self, p):
        pass

    @_('INT', 'CHAR', 'FLOAT', 'DOUBLE')
    def type_specifier(self, p):
        pass

    @_('STRUCT "{" type_decl_list "}"')
    def type_specifier(self, p):
        pass

    @_('STRUCT ID "{" type_decl_list "}"')
    def type_specifier(self, p):
        pass

    @_('STRUCT ID')
    def type_specifier(self, p):
        pass

    @_('declarator', 'declarator "," declarator_list')
    def declarator_list(self, p):
        pass

    @_('ID', '"*" declarator %prec STAR_EXPR', 'declarator "(" ")"',
       'declarator "[" constant_expression_opt "]"', '"(" declarator ")"')
    def declarator(self, p):
        pass

    @_('constant_expression')
    def constant_expression_opt(self, p):
        pass

    @_('empty')
    def constant_expression_opt(self, p):
        pass

    @_('type_declaration', 'type_declaration type_decl_list')
    def type_decl_list(self, p):
        pass

    @_('type_specifier declarator_list ";"')
    def type_declaration(self, p):
        pass

    @_('expression ";"', '"{" statement_list "}"')
    def statement(self, p):
        pass

    @_('IF "(" expression ")" statement')
    def statement(self, p):
        pass

    @_('IF "(" expression ")" statement ELSE statement')
    def statement(self, p):
        pass

    @_('WHILE "(" expression ")" statement')
    def statement(self, p):
        pass

    @_('FOR "(" for_expression ";" for_expression ";" for_expression ")" statement')
    def statement(self, p):
        pass

    @_('expression')
    def for_expression(self, p):
        pass

    @_('empty')
    def for_expression(self, p):
        pass

    @_('SWITCH "(" expression ")" statement')
    def statement(self, p):
        pass

    @_('CASE constant_expression ":" statement')
    def statement(self, p):
        pass

    @_('DEFAULT ":" statement')
    def statement(self, p):
        pass

    @_('BREAK ";"')
    def statement(self, p):
        pass

    @_('CONTINUE ";"')
    def statement(self, p):
        pass

    @_('RETURN ";"')
    def statement(self, p):
        pass

    @_('RETURN "(" expression ")" ";"')
    def statement(self, p):
        pass

    @_('GOTO expression ";"')
    def statement(self, p):
        pass

    @_('ID ":" statement')
    def statement(self, p):
        pass

    @_('";"')
    def statement(self, p):
        pass

    @_('statement', 'statement statement_list')
    def statement_list(self, p):
        pass

    @_('')
    def empty(self, p):
        pass


if __name__ == '__main__':
    with open('./src/c0_tot.c', 'r') as f:
        prg = f.read()

    lex = lexer.CLexer()
    parser = CCParser()
    result = parser.parse(lex.tokenize(prg))
    print(result)
