from sly import Parser
import CClexer
from CCast import *

ptype = lambda p: p._slice[0].type

class CCParser(Parser):
    start = 'translation_unit'
    tokens = CClexer.CLexer.tokens
    debugfile = 'CCparser.out'

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
        ('left', "(", ")", "[", "]", ".", POINTER)
    )

    @_('')
    def empty(self, p): pass

    @_('ID', 'CONSTANT', 'STRING_LITERAL', '"(" expression ")"')
    def primary_expression(self, p):
        return PrimaryExpression(p.lineno, p[0]) if len(p) == 1 else p[1]

    # Note, postfix expressions are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    #        @_('primary_expression',
    #            'postfix_expression "[" expression "]"',
    #            'postfix_expression "(" ")"',
    #            'postfix_expression "(" argument_expression_list ")"',
    #            'postfix_expression "." ID',
    #            'postfix_expression POINTER ID',
    #            'postfix_expression INCR',
    #            'postfix_expression DECR')
    #        def postfix_expression(self, p): pass

    @_('postfix_expression "[" expression "]"')
    def postfix_expression_subscript(self, p):
        return PFESubscript(p.lineno, p.postfix_expression, p.expression)

    @_('postfix_expression "(" ")"',
       'postfix_expression "(" argument_expression_list ")"')
    def postfix_expression_function_call(self, p):
        args = p[2] if len(p) > 2 else None
        return PFEFunctionCall(p.lineno, p.postfix_expression, args)

    @_('postfix_expression "." ID', 'postfix_expression POINTER ID')
    def postfix_expression_member_of_structure(self, p):
        return PFEMemberOfStructure(p.lineno, p.postfix_expression, p[1], p.ID)

    @_('postfix_expression INCR', 'postfix_expression DECR')
    def postfix_expression_incr_decr(self, p):
        return PFEIncrDecr(p.lineno, p.postfix_expression, p[1])

    @_('primary_expression',
       'postfix_expression_subscript',
       'postfix_expression_function_call',
       'postfix_expression_member_of_structure',
       'postfix_expression_incr_decr')
    def postfix_expression(self, p):
        return PostfixExpression(p.lineno, p[0])  # return p[0]?

    @_('assignment_expression',
       'argument_expression_list "," assignment_expression')
    def argument_expression_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    # Note, unary expressions are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('postfix_expression',
    #    'INCR unary_expression',
    #    'DECR unary_expression',
    #    'unary_operator cast_expression',
    #    'SIZEOF unary_expression',
    #    'SIZEOF "(" type_name ")"')
    # def unary_expression(self, p): pass

    @_('INCR unary_expression', 'DECR unary_expression')
    def unary_expression_incr_decr(self, p):
        return UnaryExpressionIncrDecr(p.lineno, p.unary_expression, p[0])

    @_('unary_operator cast_expression')
    def unary_operator_cast_expression(self, p):
        return UnaryExpressionCastExpr(p.lineno, p.cast_expression, p.unary_operator)

    @_('SIZEOF unary_expression')
    def unary_expression_sizeof(self, p):
        return UnaryExpressionSizeof(p.lineno, p.unary_expression)

    @_('SIZEOF "(" type_name ")"')
    def unary_expression_sizeof_typename(self, p):
        return UnaryExpressionSizeofType(p.lineno, p.type_name)

    @_('postfix_expression',
       'unary_expression_incr_decr',
       'unary_operator_cast_expression',
       'unary_expression_sizeof',
       'unary_expression_sizeof_typename')
    def unary_expression(self, p):
        return UnaryExpression(p.lineno, p[0])  # return p[0]

    @_('"&"', '"*"', '"+"', '"-"', '"~"', '"!"')
    def unary_operator(self, p):
        return p[0]

    @_('unary_expression')
    def cast_expression(self, p):
        return CastExpression(p.lineno, p.unary_expression)

    @_('cast_expression',
       'multiplicative_expression "*" cast_expression',
       'multiplicative_expression "/" cast_expression',
       'multiplicative_expression "%" cast_expression')
    def multiplicative_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('multiplicative_expression',
       'additive_expression "+" multiplicative_expression',
       'additive_expression "-" multiplicative_expression')
    def additive_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('additive_expression',
       'shift_expression SHIFT_LEFT additive_expression',
       'shift_expression SHIFT_RIGHT additive_expression')
    def shift_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('shift_expression',
       'relational_expression "<" shift_expression',
       'relational_expression ">" shift_expression',
       'relational_expression LE shift_expression',
       'relational_expression GE shift_expression')
    def relational_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('relational_expression',
       'equality_expression EQ relational_expression',
       'equality_expression NE relational_expression')
    def equality_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('equality_expression', 'and_expression "&" equality_expression')
    def and_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('and_expression', 'exclusive_or_expression "^" and_expression')
    def exclusive_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('exclusive_or_expression', 'inclusive_or_expression "|" exclusive_or_expression')
    def inclusive_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('inclusive_or_expression', 'logical_and_expression AND inclusive_or_expression')
    def logical_and_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('logical_and_expression', 'logical_or_expression OR logical_and_expression')
    def logical_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

    @_('logical_or_expression', 'logical_or_expression "?" expression ":" conditional_expression')
    def conditional_expression(self, p):
        return p[0] if len(p) == 1 else ConditionalExpression(p.lineno, p[0], p[2], p[4])

    @_('conditional_expression', 'unary_expression assignment_operator assignment_expression')
    def assignment_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, p[0], p[2], p[1])

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
       'ASSIGN_OR')
    def assignment_operator(self, p):
        return p[0]

    @_('assignment_expression')
    def expression(self, p):
        return p[0]

    @_('conditional_expression')
    def constant_expression(self, p):
        return p[0]

    @_('declaration_specifiers ";"', 'declaration_specifiers init_declarator_list ";"')
    def declaration(self, p):
        return Declaration(p.lineno, p[0]) if len(p) == 2 else Declaration(p.lineno, p[0], p[1])

    # Note, declaration specifiers are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('storage_class_specifier',
    #    'storage_class_specifier declaration_specifiers',
    #    'type_specifier',
    #    'type_specifier declaration_specifiers')
    # def declaration_specifiers(self, p):
    #     pass

    @_('storage_class_specifier', 'storage_class_specifier declaration_specifiers')
    def declaration_specifiers_storage_class(self, p):
        decl = None if len(p) == 1 else p[1]
        return DeclarationSpecifierStorageClass(p.lineno, decl, p[0])

    @_('type_specifier', 'type_specifier declaration_specifiers')
    def declaration_specifiers_type_specifier(self, p):
        decl = None if len(p) == 1 else p[1]
        return DeclarationSpecifierTypeSpecifier(p.lineno, decl, p[0])

    @_('declaration_specifiers_storage_class', 'declaration_specifiers_type_specifier')
    def declaration_specifiers(self, p):
        return DeclarationSpecifier(p.lineno, p[0])

    @_('init_declarator', 'init_declarator_list "," init_declarator')
    def init_declarator_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('declarator', 'declarator initializer')
    def init_declarator(self, p):
        initializer = None if len(p) == 1 else p[1]
        return InitDeclarator(p.lineno, p[0], initializer)

    @_('CONSTANT', '"-" CONSTANT', '"{" constant_expression_list "}"')
    def initializer(self, p):
        if len(p) == 1:
            return Initializer(p.lineno, p[0])
        elif len(p) == 2:
            return Initializer(p.lineno, -p[1])
        else:
            return Initializer(p.lineno, None, p[1])


    @_('constant_init_expression', 'constant_expression_list "," constant_init_expression')
    def constant_expression_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('expression', 'empty')
    def constant_init_expression(self, p):
        if ptype(p) == 'empty':
            pass
        else:
            return ConstantInitExpression(p.lineno, p[0])

    @_('EXTERN', 'STATIC', 'AUTO', 'REG')
    def storage_class_specifier(self, p):
        return p[0]

    @_('CHAR', 'INT', 'FLOAT', 'DOUBLE', 'struct_specifier')
    def type_specifier(self, p):
        return p[0]

    @_('STRUCT ID "{" struct_declaration_list "}"',
       'STRUCT "{" struct_declaration_list "}"',
       'STRUCT ID')
    def struct_specifier(self, p): pass

    @_('struct_declaration', 'struct_declaration_list struct_declaration')
    def struct_declaration_list(self, p): pass

    @_('specifier_qualifier_list struct_declarator_list ";"')
    def struct_declaration(self, p): pass

    @_('type_specifier specifier_qualifier_list', 'type_specifier')
    def specifier_qualifier_list(self, p): pass

    @_('struct_declarator', 'struct_declarator_list "," struct_declarator')
    def struct_declarator_list(self, p): pass

    @_('declarator')
    def struct_declarator(self, p): pass

    @_('pointer direct_declarator', 'direct_declarator')
    def declarator(self, p): pass

    @_('ID',
       '"(" declarator ")"',
       'direct_declarator "[" constant_expression "]"',
       'direct_declarator "[" "]"',
       'direct_declarator "(" parameter_type_list ")"',
       'direct_declarator "(" identifier_list ")"',
       'direct_declarator "(" ")"')
    def direct_declarator(self, p):
        pass

    @_('"*"', '"*" pointer')
    def pointer(self, p): pass

    @_('parameter_list')
    def parameter_type_list(self, p): pass

    @_('parameter_declaration', 'parameter_list "," parameter_declaration')
    def parameter_list(self, p): pass

    @_('declaration_specifiers declarator',
       'declaration_specifiers abstract_declarator',
       'declaration_specifiers')
    def parameter_declaration(self, p): pass

    @_('ID', 'identifier_list "," ID')
    def identifier_list(self, p): pass

    @_('specifier_qualifier_list', 'specifier_qualifier_list abstract_declarator')
    def type_name(self, p): pass

    @_('pointer', 'direct_abstract_declarator', 'pointer direct_abstract_declarator')
    def abstract_declarator(self, p): pass

    @_('"(" abstract_declarator ")"',
       '"[" "]"',
       '"[" constant_expression "]"',
       'direct_abstract_declarator "[" "]"',
       'direct_abstract_declarator "[" constant_expression "]"',
       '"(" ")"',
       '"(" parameter_type_list ")"',
       'direct_abstract_declarator "(" ")"',
       'direct_abstract_declarator "(" parameter_type_list ")"')
    def direct_abstract_declarator(self, p): pass

    @_('labeled_statement',
       'compound_statement',
       'expression_statement',
       'selection_statement',
       'iteration_statement',
       'jump_statement')
    def statement(self, p): pass

    @_('ID ":" statement',
       'CASE constant_expression ":" statement',
       'DEFAULT ":" statement')
    def labeled_statement(self, p): pass

    @_('"{" statement_list "}"',
       '"{" declaration_list "}"',
       '"{" declaration_list statement_list "}"')
    def compound_statement(self, p): pass

    @_('declaration', 'declaration_list declaration')
    def declaration_list(self, p): pass

    @_('statement', 'statement_list statement')
    def statement_list(self, p): pass

    @_('";"', 'expression ";"')
    def expression_statement(self, p): pass

    # https://stackoverflow.com/questions/12731922/reforming-the-grammar-to-remove-shift-reduce-conflict-in-if-then-else
    @_('IF "(" expression ")" statement %prec THEN',
       'IF "(" expression ")" statement ELSE statement',
       'SWITCH "(" expression ")" statement')
    def selection_statement(self, p): pass

    @_('WHILE "(" expression ")" statement',
       'DO statement WHILE "(" expression ")" ";"',
       'FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement')
    def iteration_statement(self, p): pass

    @_('GOTO ID ";"',
       'CONTINUE ";"',
       'BREAK ";"',
       'RETURN ";"',
       'RETURN expression ";"')
    def jump_statement(self, p): pass

    @_('external_declaration', 'translation_unit external_declaration')
    def translation_unit(self, p): pass

    @_('function_definition', 'declaration')
    def external_declaration(self, p): pass

    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement',
       'declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition(self, p): pass

if __name__ == '__main__':
    fn = ['./src/c0_tot.c', './src/c1_tot.c', './src/c2_tot.c', './src/cvopt.c', './src/c0h.c', './src/c1h.c', './src/c2h.c']
    ind = 0

    for i in range(ind, len(fn)):
        print(f'Parsing file {fn[i]}')

        with open(fn[i], 'r') as f:
            prg = f.read()

        lex = CClexer.CLexer()
        parser = CCParser()
        result = parser.parse(lex.tokenize(prg))
        print(f'CCParser {fn[i]}: {result}')
