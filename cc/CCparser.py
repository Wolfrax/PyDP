from sly import Parser
import CClexer
from CCast import *

ptype = lambda p: p._slice[0].type

class CCParser(Parser):
    start = 'translation_unit'
    tokens = CClexer.CLexer.tokens
    debugfile = 'CCparser.out'

    prg = []

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
        return PostfixExpressionSubscript(p.lineno, p[0], p[2])

    @_('postfix_expression "(" ")"',
       'postfix_expression "(" argument_expression_list ")"')
    def postfix_expression_function_call(self, p):
        args = p[2] if len(p) > 2 else None
        return PostfixExpressionFunctionCall(p.lineno, p.postfix_expression, args)

    @_('postfix_expression "." ID', 'postfix_expression POINTER ID')
    def postfix_expression_member_of_structure(self, p):
        return PostfixExpressionMemberOfStructure(p.lineno, p.postfix_expression, p[1], p.ID)

    @_('postfix_expression INCR', 'postfix_expression DECR')
    def postfix_expression_incr_decr(self, p):
        return PostfixExpressionIncrDecr(p.lineno, p.postfix_expression, p[1])

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
    def struct_specifier(self, p):
        if len(p) == 2:
            return StructSpecifier(p.lineno, p[0], None)
        elif len(p) == 4:
            return StructSpecifier(p.lineno, None, p[2])
        else:
            return StructSpecifier(p.lineno, p[0], p[3])

    @_('struct_declaration', 'struct_declaration_list struct_declaration')
    def struct_declaration_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])


    @_('specifier_qualifier_list struct_declarator_list ";"')
    def struct_declaration(self, p):
        return StructDeclaration(p.lineno, p[0], p[1])

    @_('type_specifier', 'specifier_qualifier_list type_specifier')
    def specifier_qualifier_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])


    @_('struct_declarator', 'struct_declarator_list "," struct_declarator')
    def struct_declarator_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('declarator')
    def struct_declarator(self, p):
        return StructDeclarator(p.lineno, p[0])

    @_('pointer direct_declarator', 'direct_declarator')
    def declarator(self, p):
        return Declarator(p.lineno, p[0]) if len(p) == 1 else Declarator(p.lineno, p[1], p[0])

    # Note, direct declarator are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('ID',
    #    '"(" declarator ")"',
    #    'direct_declarator "[" constant_expression "]"',
    #    'direct_declarator "[" "]"',
    #    'direct_declarator "(" parameter_type_list ")"',
    #    'direct_declarator "(" identifier_list ")"',
    #    'direct_declarator "(" ")"')
    # def direct_declarator(self, p):
    #     pass

    @_('ID', '"(" declarator ")"')
    def direct_declarator_ID(self, p):
        return DirectDeclaratorID(p.lineno, p[0]) if len(p) == 1 else DirectDeclaratorID(p.lineno, p[1])

    @_('direct_declarator "[" constant_expression "]"', 'direct_declarator "[" "]"')
    def direct_declarator_constant_expression(self, p):
        if len(p) == 4:
            return DirectDeclaratorConstantExpression(p.lineno, p[0], p[2])
        else:
            return DirectDeclaratorConstantExpression(p.lineno, p[0])

    @_('direct_declarator "(" parameter_type_list ")"')
    def direct_declarator_parameter_type_list(self, p):
        return DirectDeclaratorParameterTypeList(p.lineno, p[0], p[2])

    @_('direct_declarator "(" identifier_list ")"', 'direct_declarator "(" ")"')
    def direct_declarator_identifier_list(self, p):
        if len(p) == 4:
            return DirectDeclaratorIdentifierList(p.lineno, p[0], p[2])
        else:
            return DirectDeclaratorIdentifierList(p.lineno, p[0])

    @_('direct_declarator_ID',
       'direct_declarator_constant_expression',
       'direct_declarator_parameter_type_list',
       'direct_declarator_identifier_list')
    def direct_declarator(self, p):
        return DirectDeclarator(p.lineno, p[0])

    @_('"*"', '"*" pointer')
    def pointer(self, p):
        return Pointer(p.lineno, p[1])if len(p) == 2 else Pointer(p.lineno)

    @_('parameter_list')
    def parameter_type_list(self, p):
        return ParameterTypeList(p.lineno, p[0])

    @_('parameter_declaration', 'parameter_list "," parameter_declaration')
    def parameter_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('declaration_specifiers declarator',
       'declaration_specifiers pointer',
       'declaration_specifiers')
    def parameter_declaration(self, p):
        return ParameterDeclaration(p.lineno, p[0], p[1]) if len(p) == 1 else ParameterDeclaration(p.lineno, p[0])

    @_('ID', 'identifier_list "," ID')
    def identifier_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('specifier_qualifier_list', 'specifier_qualifier_list pointer')
    def type_name(self, p):
        return TypeName(p.lineno, p[0]) if len(p) == 1 else TypeName(p.lineno, p[0], p[1])

    @_('labeled_statement',
       'compound_statement',
       'expression_statement',
       'selection_statement',
       'iteration_statement',
       'jump_statement')
    def statement(self, p):
        return Statement(p.lineno, p[0])

    @_('ID ":" statement',
       'CASE constant_expression ":" statement',
       'DEFAULT ":" statement')
    def labeled_statement(self, p):
        return LabeledStatement(p.lineno, p[0], None, p[2]) if len(p) == 3 \
            else LabeledStatement(p.lineno, p[0], p[1], p[3])

    # Note, compound statement are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('"{" statement_list "}"',
    #    '"{" declaration_list "}"',
    #    '"{" declaration_list statement_list "}"')
    # def compound_statement(self, p): pass

    @_('"{" statement_list "}"')
    def compound_statement_statement_list(self, p):
        return CompoundStatementStatementList(p.lineno, p[1])

    @_('"{" declaration_list "}"')
    def compound_statement_declaration_list(self, p):
        return CompoundStatementDeclarationList(p.lineno, p[1])

    @_('"{" declaration_list statement_list "}"')
    def compound_statement_declaration_list_statement_list(self, p):
        return CompoundStatementDeclarationListStatementList(p.lineno, p[0], p[1])

    @_('compound_statement_statement_list',
       'compound_statement_declaration_list',
       'compound_statement_declaration_list_statement_list')
    def compound_statement(self, p):
        return CompoundStatement(p.lineno, p[0])

    @_('declaration', 'declaration_list declaration')
    def declaration_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('statement', 'statement_list statement')
    def statement_list(self, p):
        # Note, construction for lists;
        #   return first production as a new list
        #   return list with last element added to list
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('";"', 'expression ";"')
    def expression_statement(self, p):
        if len(p) == 2:
            return ExpressionStatement(p.lineno, p[0])
        else:
            pass

    # https://stackoverflow.com/questions/12731922/reforming-the-grammar-to-remove-shift-reduce-conflict-in-if-then-else
    # Note, selection statement are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('IF "(" expression ")" statement %prec THEN',
    #    'IF "(" expression ")" statement ELSE statement',
    #    'SWITCH "(" expression ")" statement')
    # def selection_statement(self, p): pass

    @_('IF "(" expression ")" statement %prec THEN', 'IF "(" expression ")" statement ELSE statement')
    def selection_statement_if_then_else(self, p):
        if len(p) == 5:
            return SelectionStatementIfThenElse(p.lineno, None, p[2], p[4])
        else:
            return SelectionStatementIfThenElse(p.lineno, p[5], p[2], p[4], p[6])

    @_('SWITCH "(" expression ")" statement')
    def selection_statement_switch(self, p):
        return SelectionStatementSwitch(p.lineno, p[2], p[4])

    @_('selection_statement_if_then_else',
       'selection_statement_switch')
    def selection_statement(self, p):
        return SelectionStatement(p.lineno, p[0])

    # Note, iteration statement are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('WHILE "(" expression ")" statement',
    #    'DO statement WHILE "(" expression ")" ";"',
    #    'FOR "(" expression_statement expression_statement ")" statement',
    #    'FOR "(" expression_statement expression_statement expression ")" statement')
    # def iteration_statement(self, p): pass

    @_('WHILE "(" expression ")" statement',
       'DO statement WHILE "(" expression ")" ";"')
    def iteration_statement_while(self, p):
        if len(p) == 5:
            return IterationStatementWhile(p.lineno, p[0], p[2], p[4])
        else:
            return IterationStatementWhile(p.lineno, p[0], p[4], p[1])

    @_('FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement')
    def iteration_statement_for(self, p):
        if len(p) == 6:
            return IterationStatementFor(p.lineno, None, p[2], p[3], p[5])
        else:
            return IterationStatementFor(p.lineno, p[4], p[2], p[3], p[6])

    @_('iteration_statement_while',
       'iteration_statement_for')
    def iteration_statement(self, p):
        return IterationStatement(p.lineno, p[0])

    @_('GOTO ID ";"',
       'CONTINUE ";"',
       'BREAK ";"',
       'RETURN ";"',
       'RETURN expression ";"')
    def jump_statement(self, p):
        if len(p) == 2:
            return JumpStatement(p.lineno, p[0])
        else:
            return JumpStatement(p.lineno, p[0], p[1])

    @_('external_declaration', 'translation_unit external_declaration')
    def translation_unit(self, p):
        self.prg.append(p[0]) if len(p) == 1 else self.prg.append(p[1])

    @_('function_definition', 'declaration')
    def external_declaration(self, p):
        return ExternalDeclaration(p.lineno, p[0])

    # Note, function definition are split into several production to distinguish them in AST
    # If not split, the combined production is as below
    # @_('declaration_specifiers declarator declaration_list compound_statement',
    #    'declaration_specifiers declarator compound_statement',
    #    'declarator declaration_list compound_statement',
    #    'declarator compound_statement')
    # def function_definition(self, p): pass

    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement')
    def function_definition_declaration_specifiers(self, p):
        if len(p) == 4:
            return FunctionDefinitionDeclarationSpecifier(p.lineno, p[0], p[1], p[2], p[3])
        else:
            return FunctionDefinitionDeclarationSpecifier(p.lineno, p[0], p[1], None, p[2])

    @_('declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition_declarator(self, p):
        if len(p) == 3:
            return FunctionDefinitionDeclarator(p.lineno, p[0], p[1], p[2])
        else:
            return FunctionDefinitionDeclarator(p.lineno, p[0], None, p[1])

    @_('function_definition_declaration_specifiers',
       'function_definition_declarator')
    def function_definition(self, p):
        return FunctionDefinition(p.lineno, p[0])

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
