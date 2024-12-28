from sly import Parser
import CClexer
from CCast import *
import json

"""
2024-12-04: Note that some statements are commented out in productions below. 
This is an attempt to reduce the number of nodes in the AST. However, they might be needed later on, so kept for now
"""

ptype = lambda p: p._slice[0].type

class CCParser(Parser):
    start = 'translation_unit'
    tokens = CClexer.CLexer.tokens
    debugfile = 'CCparser.out'

    prg = Program()

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

    def dumps(self):
        return json.dumps(self.prg, indent=2, default=lambda o: o.__dict__)

    def dump(self, fn):
        with open(fn, 'w') as f:
            json.dump(self.prg, f, indent=2, default=lambda o: o.__dict__)

    def generate_ir(self):
        for item in self.prg:
            item.ir()

    @_('')
    def empty(self, p): pass

    @_('ID', 'CONSTANT', 'STRING_LITERAL', '"(" expression ")"')
    def primary_expression(self, p):
        #return p[0] if len(p) == 1 else p[1]
        return PrimaryExpression(p.lineno, expr=p[0]) if len(p) == 1 else PrimaryExpression(p.lineno, expr=p[1])

    """
    Note, postfix expressions are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
           @_('primary_expression',
               'postfix_expression "[" expression "]"',
               'postfix_expression "(" ")"',
               'postfix_expression "(" argument_expression_list ")"',
               'postfix_expression "." ID',
               'postfix_expression POINTER ID',
               'postfix_expression INCR',
               'postfix_expression DECR')
           def postfix_expression(self, p): pass
    """

    @_('postfix_expression "[" expression "]"')
    def postfix_expression_subscript(self, p):
        return PostfixExpression(p.lineno, expr=p[0], args=p[2], op=p[1], id=None)

    @_('postfix_expression "(" ")"',
       'postfix_expression "(" argument_expression_list ")"')
    def postfix_expression_function_call(self, p):
        if len(p) == 4:
            return PostfixExpression(p.lineno, expr=p[0], args=ASTList(p.lineno, items=p[2]), op=p[1], id=None)
        else:
            return PostfixExpression(p.lineno, expr=p[0], args=None, op=p[1], id=None)

    @_('postfix_expression "." ID', 'postfix_expression POINTER ID')
    def postfix_expression_member_of_structure(self, p):
        return PostfixExpression(p.lineno, expr=p[0], args=None, op=p[1], id=p[2])

    @_('postfix_expression INCR', 'postfix_expression DECR')
    def postfix_expression_incr_decr(self, p):
        return PostfixExpression(p.lineno, expr=p[0], args=None, op=p[1], id=None)

    @_('primary_expression',
       'postfix_expression_subscript',
       'postfix_expression_function_call',
       'postfix_expression_member_of_structure',
       'postfix_expression_incr_decr')
    def postfix_expression(self, p):
        return p[0]

    @_('assignment_expression',
       'argument_expression_list "," assignment_expression')
    def argument_expression_list(self, p):
        """
        Note, construction for lists;
          return first production as a new list
          return list with last element added to list
        """
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('postfix_expression',
       'INCR unary_expression',
       'DECR unary_expression',
       'unary_operator unary_expression',
       'SIZEOF unary_expression',
       'SIZEOF "(" type_name ")"')
    def unary_expression(self, p):
        if len(p) == 1:
            return p[0]
        elif len(p) == 2:
            return UnaryExpression(p.lineno, op=p[0], expr=p[1])
        else:
            return UnaryExpression(p.lineno, op=p[0], expr=p[2])

    @_('"&"', '"*"', '"+"', '"-"', '"~"', '"!"')
    def unary_operator(self, p):
        return p[0]

    @_('unary_expression',
       'multiplicative_expression "*" unary_expression',
       'multiplicative_expression "/" unary_expression',
       'multiplicative_expression "%" unary_expression')
    def multiplicative_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('multiplicative_expression',
       'additive_expression "+" multiplicative_expression',
       'additive_expression "-" multiplicative_expression')
    def additive_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('additive_expression',
       'shift_expression SHIFT_LEFT additive_expression',
       'shift_expression SHIFT_RIGHT additive_expression')
    def shift_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('shift_expression',
       'relational_expression "<" shift_expression',
       'relational_expression ">" shift_expression',
       'relational_expression LE shift_expression',
       'relational_expression GE shift_expression')
    def relational_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('relational_expression',
       'equality_expression EQ relational_expression',
       'equality_expression NE relational_expression')
    def equality_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('equality_expression', 'and_expression "&" equality_expression')
    def and_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('and_expression', 'exclusive_or_expression "^" and_expression')
    def exclusive_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('exclusive_or_expression', 'inclusive_or_expression "|" exclusive_or_expression')
    def inclusive_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('inclusive_or_expression', 'logical_and_expression AND inclusive_or_expression')
    def logical_and_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('logical_and_expression', 'logical_or_expression OR logical_and_expression')
    def logical_or_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

    @_('logical_or_expression', 'logical_or_expression "?" expression ":" conditional_expression')
    def conditional_expression(self, p):
        return p[0] if len(p) == 1 else ConditionalExpression(p.lineno, expr1=p[0], expr2=p[2], expr3=p[4])

    @_('conditional_expression', 'unary_expression assignment_operator assignment_expression')
    def assignment_expression(self, p):
        return p[0] if len(p) == 1 else BinOpExpression(p.lineno, expr_l=p[0], expr_r=p[2], op=p[1])

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
        return p[0]if len(p) == 2 else \
            Declaration(p.lineno, decl_specifier=p[0], initializer=ASTList(p.lineno, items=p[1]))
#        return Declaration(p.lineno, decl_specifier=p[0], initializer=None) if len(p) == 2 else \
#            Declaration(p.lineno, decl_specifier=p[0], initializer=ASTList(p.lineno, items=p[1]))

    """ 
    Note, declaration specifiers are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
    @_('storage_class_specifier', 'storage_class_specifier type_specifier',
       'type_specifier', 'type_specifier storage_class_specifier')
    def declaration_specifiers(self, p):
        pass
    """

    @_('storage_class_specifier', 'storage_class_specifier type_specifier')
    def declaration_specifiers_storage_class(self, p):
#        return p[0] if len(p) == 1 else DeclarationSpecifiers(p.lineno, storage_class=p[0], type=p[1])
        return DeclarationSpecifiers(p.lineno, storage_class=p[0], type=None) if len(p) == 1 else (
            DeclarationSpecifiers(p.lineno, storage_class=p[0], type=p[1]))

    @_('type_specifier', 'type_specifier storage_class_specifier')
    def declaration_specifiers_type_specifier(self, p):
#        return p[0] if len(p) == 1 else DeclarationSpecifiers(p.lineno, storage_class=p[1], type=p[0])
        return DeclarationSpecifiers(p.lineno, storage_class=None, type=p[0]) if len(p) == 1 else (
            DeclarationSpecifiers(p.lineno, storage_class=p[1], type=p[0]))

    @_('declaration_specifiers_storage_class', 'declaration_specifiers_type_specifier')
    def declaration_specifiers(self, p):
        return p[0]

    @_('init_declarator', 'init_declarator_list "," init_declarator')
    def init_declarator_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('declarator', 'declarator initializer')
    def init_declarator(self, p):
        return p[0] if len(p) == 1 else InitDeclarator(p.lineno, declarator=p[0], initializer=p[1])
#        return InitDeclarator(p.lineno, declarator=p[0], initializer=None) if len(p) == 1 else \
#            InitDeclarator(p.lineno, declarator=p[0], initializer=p[1])

    @_('CONSTANT', '"-" CONSTANT', '"{" constant_expression_list "}"')
    def initializer(self, p):
        if len(p) == 1:
            return p[0]
        elif len(p) == 2:
            return -p[1]
        else:
            return Initializer(p.lineno, value=None, expr=ASTList(p.lineno, items=p[1]))
#        if len(p) == 1:
#            return Initializer(p.lineno, value=p[0], expr=None)
#        elif len(p) == 2:
#            return Initializer(p.lineno, value=-p[1], expr=None)
#        else:
#            return Initializer(p.lineno, value=None, expr=ASTList(p.lineno, items=p[1]))

    @_('constant_init_expression', 'constant_expression_list "," constant_init_expression')
    def constant_expression_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('expression', 'empty')
    def constant_init_expression(self, p):
        if ptype(p) == 'empty':
            pass
        else:
            return p[0]
#        if ptype(p) == 'empty':
#            pass
#        else:
#            return ConstantInitExpression(p.lineno, expr=p[0])

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
            return StructSpecifier(p.lineno, id=p[1], decl_specifier=None)
        elif len(p) == 4:
            return StructSpecifier(p.lineno, id=None, decl_specifier=ASTList(p.lineno, items=p[2]))
        else:
            return StructSpecifier(p.lineno, id=p[1], decl_specifier=ASTList(p.lineno, items=p[3]))

    @_('struct_declaration', 'struct_declaration_list struct_declaration')
    def struct_declaration_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('specifier_qualifier_list struct_declarator_list ";"')
    def struct_declaration(self, p):
        return StructDeclaration(p.lineno, specifier_qualifiers=ASTList(p.lineno, items=p[0]), declarators=ASTList(p.lineno, items=p[1]))

    @_('type_specifier', 'specifier_qualifier_list type_specifier')
    def specifier_qualifier_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('declarator', 'struct_declarator_list "," declarator')
    def struct_declarator_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('pointer direct_declarator', 'direct_declarator')
    def declarator(self, p):
        return p[0] if len(p) == 1 else Declarator(p.lineno, direct_declarator=p[1], pointer=p[0])
#        return Declarator(p.lineno, direct_declarator=p[0], pointer=None) if len(p) == 1 else (
#            Declarator(p.lineno, direct_declarator=p[1], pointer=p[0]))

    """
    Note, direct declarator are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
    @_('ID',
       '"(" declarator ")"',
       'direct_declarator "[" constant_expression "]"',
       'direct_declarator "[" "]"',
       'direct_declarator "(" identifier_list ")"',
       'direct_declarator "(" ")"')
    def direct_declarator(self, p):
        pass
    """

    @_('ID', '"(" declarator ")"')
    def direct_declarator_ID(self, p):
        return p[0] if len(p) == 1 else DirectDeclarator(p.lineno, identifiers=None, decl=p[1], expr=None)
#        return DirectDeclarator(p.lineno, id=p[0], identifiers=None, decl=None, expr=None) if len(p) == 1 \
#            else DirectDeclarator(p.lineno, id=None, identifiers=None, decl=p[1], expr=None)

    @_('direct_declarator "[" constant_expression "]"', 'direct_declarator "[" "]"')
    def direct_declarator_array(self, p):
        if len(p) == 4:
            return DirectDeclarator(p.lineno, identifiers=None, decl=p[0], expr=p[2])
        else:
            return p[0]
#        if len(p) == 4:
#            return DirectDeclarator(p.lineno, id=None, identifiers=None, decl=p[0], expr=p[2])
#        else:
#            return DirectDeclarator(p.lineno, id=None,identifiers= None, decl=p[0], expr=None)

    @_('direct_declarator "(" identifier_list ")"', 'direct_declarator "(" ")"')
    def direct_declarator_function(self, p):
        if len(p) == 4:
            return DirectDeclarator(p.lineno, identifiers=ASTList(p.lineno, items=p[2]), decl=p[0], expr=None)
        else:
            return p[0]
#        if len(p) == 4:
#            return DirectDeclarator(p.lineno, id=None, identifiers=ASTList(p.lineno, items=p[2]), decl=p[0], expr=None)
#        else:
#            return DirectDeclarator(p.lineno, id=None, identifiers=None, decl=p[0], expr=None)

    @_('direct_declarator_ID',
       'direct_declarator_array',
       'direct_declarator_function')
    def direct_declarator(self, p):
        return p[0]

    @_('"*"', '"*" pointer')
    def pointer(self, p):
        return Pointer(p.lineno, pointer=p[1])if len(p) == 2 else Pointer(p.lineno, pointer=None)

    @_('ID', 'identifier_list "," ID')
    def identifier_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('specifier_qualifier_list', 'specifier_qualifier_list pointer')
    def type_name(self, p):
        return TypeName(p.lineno, specifier_qualifier_list=ASTList(p.lineno, items=p[0]), abstract_decl=None) if len(p) == 1 \
            else TypeName(p.lineno, specifier_qualifier_list=ASTList(p.lineno, items=p[0]), abstract_decl=p[1])

    @_('labeled_statement',
       'compound_statement',
       'expression_statement',
       'selection_statement',
       'iteration_statement',
       'jump_statement')
    def statement(self, p):
        return p[0]

    @_('ID ":" statement',
       'CASE constant_expression ":" statement',
       'DEFAULT ":" statement')
    def labeled_statement(self, p):
        return LabeledStatement(p.lineno, lbl=p[0], expr=None, stmt=p[2]) if len(p) == 3 \
            else LabeledStatement(p.lineno, lbl=p[0], expr=p[1], stmt=p[3])

    """
    Note, compound statement are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
    @_('"{" statement_list "}"',
       '"{" declaration_list "}"',
       '"{" declaration_list statement_list "}"')
    def compound_statement(self, p): pass
    """

    @_('"{" statement_list "}"')
    def compound_statement_statement_list(self, p):
        return CompoundStatement(p.lineno, decl=None, stmt=ASTList(p.lineno, items=p[1]))

    @_('"{" declaration_list "}"')
    def compound_statement_declaration_list(self, p):
        return CompoundStatement(p.lineno, decl=ASTList(p.lineno, items=p[1]), stmt=None)

    @_('"{" declaration_list statement_list "}"')
    def compound_statement_declaration_list_statement_list(self, p):
        return CompoundStatement(p.lineno, decl=ASTList(p.lineno, items=p[1]), stmt=ASTList(p.lineno, items=p[2]))

    @_('compound_statement_statement_list',
       'compound_statement_declaration_list',
       'compound_statement_declaration_list_statement_list')
    def compound_statement(self, p):
        return p[0]

    @_('declaration', 'declaration_list declaration')
    def declaration_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('statement', 'statement_list statement')
    def statement_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('";"', 'expression ";"')
    def expression_statement(self, p):
        if len(p) == 2:
            return p[0]
        else:
            pass

    """
    Note, selection statement are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
    @_('IF "(" expression ")" statement %prec THEN',
       'IF "(" expression ")" statement ELSE statement',
       'SWITCH "(" expression ")" statement')
    def selection_statement(self, p): pass
    """

    # https://stackoverflow.com/questions/12731922/reforming-the-grammar-to-remove-shift-reduce-conflict-in-if-then-else
    @_('IF "(" expression ")" statement %prec THEN', 'IF "(" expression ")" statement ELSE statement')
    def selection_statement_if_then_else(self, p):
        if len(p) == 5:
            return SelectionStatement(p.lineno, op=p[0], expr=p[2], stmt=p[4], else_stmt=None)
        else:
            return SelectionStatement(p.lineno,op=p[0], expr=p[2], stmt=p[4], else_stmt=p[6])

    @_('SWITCH "(" expression ")" statement')
    def selection_statement_switch(self, p):
        return SelectionStatement(p.lineno, op=p[0], expr=p[2], stmt=p[4], else_stmt=None)

    @_('selection_statement_if_then_else',
       'selection_statement_switch')
    def selection_statement(self, p):
        return p[0]

    """
    Note, iteration statement are split into several production to distinguish them in AST
    If not split, the combined production is as below
    
    @_('WHILE "(" expression ")" statement',
       'DO statement WHILE "(" expression ")" ";"',
       'FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement')
    def iteration_statement(self, p): pass
    """

    @_('WHILE "(" expression ")" statement',
       'DO statement WHILE "(" expression ")" ";"')
    def iteration_statement_while(self, p):
        if len(p) == 5:
            return IterationStatement(p.lineno, op=p[0], expr1=p[2], expr2=None, expr3=None, stmt=p[4])
        else:
            return IterationStatement(p.lineno, op=p[0], expr1=p[4], expr2=None, expr3=None, stmt=p[1])

    @_('FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement')
    def iteration_statement_for(self, p):
        if len(p) == 6:
            return IterationStatement(p.lineno, op=p[0], expr1=p[2], expr2=p[3], expr3=None, stmt=p[5])
        else:
            return IterationStatement(p.lineno, op=p[0], expr1=p[2], expr2=p[3], expr3=p[4], stmt=p[6])

    @_('iteration_statement_while', 'iteration_statement_for')
    def iteration_statement(self, p):
        return p[0]

    @_('GOTO ID ";"',
       'CONTINUE ";"',
       'BREAK ";"',
       'RETURN ";"',
       'RETURN expression ";"')
    def jump_statement(self, p):
        if len(p) == 2:
            return JumpStatement(p.lineno, op=p[0], expr=None)
        else:
            return JumpStatement(p.lineno, op=p[0], expr=p[1])

    @_('external_declaration', 'translation_unit external_declaration')
    def translation_unit(self, p):
        self.prg.translation_unit.add(p[0]) if len(p) == 1 else self.prg.translation_unit.add(p[1])
        #self.prg.append(p[0]) if len(p) == 1 else self.prg.append(p[1])

    @_('function_definition', 'declaration')
    def external_declaration(self, p):
        return ExternalDeclaration(p.lineno, decl=p[0])

    """
    Note, function definition are split into several production to distinguish them in AST
    If not split, the combined production is as below
    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement',
       'declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition(self, p): pass
    """
    #FunctionDefinition(lineno, decl, decl_spec, decl_list, statement)

    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement')
    def function_definition_declaration_specifiers(self, p):
        if len(p) == 4:
            return FunctionDefinition(p.lineno,
                                      decl_specifiers=p[0],
                                      decl=p[1],
                                      decl_list=ASTList(p.lineno, items=p[2]),
                                      stmt=p[3])
        else:
            return FunctionDefinition(p.lineno,
                                      decl_specifiers=p[0],
                                      decl=p[1],
                                      decl_list=None,
                                      stmt=p[2])

    @_('declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition_declarator(self, p):
        if len(p) == 3:
            return FunctionDefinition(p.lineno,
                                      decl=p[0],
                                      decl_specifiers=None,
                                      decl_list=ASTList(p.lineno, items=p[1]),
                                      stmt=p[2])
        else:
            return FunctionDefinition(p.lineno,
                                      decl=p[0],
                                      decl_specifiers=None,
                                      decl_list=None,
                                      stmt=p[1])

    @_('function_definition_declaration_specifiers',
       'function_definition_declarator')
    def function_definition(self, p):
        return p[0]

if __name__ == '__main__':
    #fn = ['./src/c0_tot.c', './src/c1_tot.c', './src/c2_tot.c', './src/cvopt.c', './src/c0h.c', './src/c1h.c', './src/c2h.c']
    #fn = ['./src/c00.c']
    fn = ['cc_test.c']
    ind = 0

    for i in range(ind, len(fn)):
        print(f'Parsing file {fn[i]}')

        with open(fn[i], 'r') as f:
            prg = f.read()

        lex = CClexer.CLexer()
        parser = CCParser()
        result = parser.parse(lex.tokenize(prg))

        print(f'CCParser {fn[i]}: {result}')
        parser.dump("CCParser.json")
        parser.prg.print()

