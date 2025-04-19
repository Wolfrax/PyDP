from sly import Parser

import CClexer
# from cc import CClexer

from CCast import *
#from cc.CCast import *

import json

ptype = lambda p: p._slice[0].type

class CCparser(Parser):
    start = 'translation_unit'
    tokens = CClexer.CLexer.tokens
    #debugfile = 'CCparser.out'

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

    def __init__(self):
        self.prg = Program()
        self.result = None
        self.lex = CClexer.CLexer()

    def compile(self, fn=None, src=None):
        if fn is None:
            print(f"Compiling {src}")
            self.result = self.parse(self.lex.tokenize(src))
            self.restart()
        else:
            with open(fn, 'r') as f:
                print(f"Compiling {fn}")
                self.result = self.parse(self.lex.tokenize(f.read()))
                self.restart()
        return self.result

    def dumps(self):
        return json.dumps(self.prg, indent=2, default=lambda o: o.__dict__, sort_keys=True)

    def dump(self, fn):
        with open(fn, 'w') as f:
            json.dump(self.prg, f, indent=2, default=lambda o: o.__dict__, sort_keys=True)

    def error(self, p):
        if not p:
            print("End of File!")
            return

        raise CCError(f'Error parsing {p}')

    @_('')
    def empty(self, p): pass

    @_('ID', 'CONSTANT', 'STRING_LITERAL', '"(" expression ")"')
    def primary_expression(self, p):
        if len(p) == 1:
            return PrimaryExpression(p.lineno, constant=p[0])
        else:
            return PrimaryExpression(p.lineno, expression=p[1])

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
        return PostfixExpression(p.lineno, postfix_expression=p[0], expression=p[2], op=p[1])

    @_('postfix_expression "(" ")"',
       'postfix_expression "(" argument_expression_list ")"')
    def postfix_expression_function_call(self, p):
        if len(p) == 4:
            return PostfixExpression(p.lineno, postfix_expression=p[0],
                                     argument_expression_list=ASTList(p.lineno, items=p[2]), op=p[1])
        else:
            return PostfixExpression(p.lineno, postfix_expression=p[0], op=p[1])

    @_('postfix_expression "." ID', 'postfix_expression POINTER ID')
    def postfix_expression_member_of_structure(self, p):
        return PostfixExpression(p.lineno, postfix_expression=p[0], op=p[1], id=p[2])

    @_('postfix_expression INCR', 'postfix_expression DECR')
    def postfix_expression_incr_decr(self, p):
        return PostfixExpression(p.lineno, postfix_expression=p[0], op=p[1])

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
            return UnaryExpression(p.lineno, op=p[0], expression=p[1])
        else:
            return UnaryExpression(p.lineno, op=p[0], type_name=p[2])

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
        return p[0] if len(p) == 2 else Declaration(p.lineno, decl_specifier=p[0],
                                                    initializer=ASTList(p.lineno, items=p[1]))

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
        return DeclarationSpecifiers(p.lineno, storage_class=p[0]) if len(p) == 1 else (
            DeclarationSpecifiers(p.lineno, storage_class=p[0], type=p[1]))

    @_('type_specifier', 'type_specifier storage_class_specifier')
    def declaration_specifiers_type_specifier(self, p):
        return DeclarationSpecifiers(p.lineno, type=p[0]) if len(p) == 1 else (
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

    @_('CONSTANT', '"-" CONSTANT', '"{" constant_expression_list "}"', '"&" expression', 'STRING_LITERAL', 'ID')
    def initializer(self, p):
        if len(p) == 1:  # int a 1; or char c 'a'; or char *c "ABC"; or char *a b; (b is a variable)
            if isinstance(p[0], str):
                if len(p[0]) == 3 and p[0][0] == "'" and p[0][2] == "'":
                    const = ord(p[0].replace("'", ''))  # 'a' => a => 97
                else:
                    const = p[0]
            else:
                const = p[0]
            return Initializer(p.lineno, constant=const)
        elif len(p) == 2:
            if p[0] == '-':  # int a -1;
                return Initializer(p.lineno, constant=-p[1])
            else:  # p[0] = '&', int *a &b; => Equivalent to int *a { b };
                return Initializer(p.lineno, constant_expression_list=ASTList(p.lineno, items=[p[1]]))
        else:  # int *a { b }; => Equivalent to int *a &b;
             return Initializer(p.lineno, constant_expression_list=ASTList(p.lineno, items=p[1]))

    @_('constant_init_expression', 'constant_expression_list "," constant_init_expression')
    def constant_expression_list(self, p):
        """
        Note that p[2] will be None if the list of constant expression ends with "," which is syntactically Ok.
        Example: { 1, 2, 3, } <= Notice the last trailing "," in the constant expression list
        This is because production constant_expression_list have 'empty' where the pass-statement implies None returned
        by SLY. We need to have 'empty' there to allow for the trailing "," to be parsed Ok.

        To avoid to have a None element in the list created by this production (constant_expression_list), we test on
        this condition below.
        """
        if len(p) == 1:
            return [p[0]]
        if len(p) == 3:
            if p[2] is not None:
                return (p[0] + [p[2]])
            else:
                return p[0]  # This is where p[2] is None (trailing ",") => return the list created so far

    @_('expression', 'empty')
    def constant_init_expression(self, p):
        if ptype(p) == 'empty':
            pass
        else:
            return p[0]

    @_('EXTERN', 'STATIC', 'AUTO', 'REG')
    def storage_class_specifier(self, p):
        return p[0]

    @_('CHAR', 'INT', 'LONG', 'FLOAT', 'DOUBLE', 'struct_specifier')
    def type_specifier(self, p):
        return TypeSpecifier(p.lineno, type_name=p[0], type=ptype(p))

    @_('STRUCT ID "{" struct_declaration_list "}"',
       'STRUCT "{" struct_declaration_list "}"',
       'STRUCT ID')
    def struct_specifier(self, p):
        if len(p) == 2:
            return StructSpecifier(p.lineno, id=p[1])
        elif len(p) == 4:
            return StructSpecifier(p.lineno, struct_declaration_list=ASTList(p.lineno, items=p[2]))
        else:
            return StructSpecifier(p.lineno, id=p[1], struct_declaration_list=ASTList(p.lineno, items=p[3]))

    @_('struct_declaration', 'struct_declaration_list struct_declaration')
    def struct_declaration_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('specifier_qualifier_list struct_declarator_list ";"')
    def struct_declaration(self, p):
        return StructDeclaration(p.lineno,
                                 specifier_qualifiers=ASTList(p.lineno, items=p[0]),
                                 declarators=ASTList(p.lineno, items=p[1]))

    @_('type_specifier', 'specifier_qualifier_list type_specifier')
    def specifier_qualifier_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[1]])

    @_('declarator', 'struct_declarator_list "," declarator')
    def struct_declarator_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('pointer direct_declarator', 'direct_declarator')
    def declarator(self, p):
        return Declarator(p.lineno, direct_declarator=p[0] if len (p) == 1 else p[1],
                          pointer=None if len(p) == 1 else ASTList(p.lineno, p[0]))

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
        if len(p) == 1:
            return DirectDeclarator(p.lineno, id=p[0], op='id')
        else:
            return DirectDeclarator(p.lineno, declarator=p[1], op='declarator')

    @_('direct_declarator "[" constant_expression "]"', 'direct_declarator "[" "]"')
    def direct_declarator_array(self, p):
        if len(p) == 4:
            return DirectDeclarator(p.lineno, direct_declarator=p[0], constant_expression=p[2], op=p[1])
        else:
            return DirectDeclarator(p.lineno, direct_declarator=p[0], op=p[1])

    @_('direct_declarator "(" identifier_list ")"', 'direct_declarator "(" ")"')
    def direct_declarator_function(self, p):
        if len(p) == 4:
            return DirectDeclarator(p.lineno, direct_declarator=p[0],
                                    identifier_list=ASTList(p.lineno, items=p[2]), op=p[1])
        else:
            return DirectDeclarator(p.lineno, direct_declarator=p[0], op=p[1])

    @_('direct_declarator_ID',
       'direct_declarator_array',
       'direct_declarator_function')
    def direct_declarator(self, p):
        return p[0]

    @_('"*"', '"*" pointer')
    def pointer(self, p):
        return [p[0]] if len(p) == 1 else (p[1] + [p[0]])

    @_('ID', 'identifier_list "," ID')
    def identifier_list(self, p):
        return [p[0]] if len(p) == 1 else (p[0] + [p[2]])

    @_('specifier_qualifier_list', 'specifier_qualifier_list pointer')
    def type_name(self, p):
        return TypeName(p.lineno, specifier_qualifier_list=ASTList(p.lineno, items=p[0])) if len(p) == 1 \
            else TypeName(p.lineno, specifier_qualifier_list=ASTList(p.lineno, items=p[0]),pointer=p[1])

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
        return LabeledStatement(p.lineno, label=p[0], constant_expression=None, statement=p[2]) if len(p) == 3 \
            else LabeledStatement(p.lineno, label=p[0], constant_expression=p[1], statement=p[3])

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
        return CompoundStatement(p.lineno, statement_list=ASTList(p.lineno, items=p[1]))

    @_('"{" declaration_list "}"')
    def compound_statement_declaration_list(self, p):
        return CompoundStatement(p.lineno, declaration_list=ASTList(p.lineno, items=p[1]))

    @_('"{" declaration_list statement_list "}"')
    def compound_statement_declaration_list_statement_list(self, p):
        return CompoundStatement(p.lineno,
                                 declaration_list=ASTList(p.lineno, items=p[1]),
                                 statement_list=ASTList(p.lineno, items=p[2]))

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
            return SelectionStatement(p.lineno, op=p[0], expression=p[2], statement=p[4])
        else:
            return SelectionStatement(p.lineno,op=p[0], expression=p[2], statement=p[4], else_statement=p[6])

    @_('SWITCH "(" expression ")" statement')
    def selection_statement_switch(self, p):
        return SelectionStatement(p.lineno, op=p[0], expression=p[2], statement=p[4])

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
            return IterationStatement(p.lineno, op=p[0], expression=p[2], statement=p[4])
        else:
            return IterationStatement(p.lineno, op=p[0], expression=p[4], statement=p[1])

    @_('FOR "(" expression_statement expression_statement ")" statement',
       'FOR "(" expression_statement expression_statement expression ")" statement')
    def iteration_statement_for(self, p):
        if len(p) == 6:
            return IterationStatement(p.lineno, op=p[0], expression=p[2], expression_statement1=p[3], statement=p[5])
        else:
            return IterationStatement(p.lineno, op=p[0], expression=p[2],
                                      expression_statement1=p[3], expression_statement2=p[4], statement=p[6])

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
            return JumpStatement(p.lineno, op=p[0])
        else:
            return JumpStatement(p.lineno, op=p[0], expression=p[1])

    @_('external_declaration', 'translation_unit external_declaration')
    def translation_unit(self, p):
        self.prg.translation_unit.add(p[0]) if len(p) == 1 else self.prg.translation_unit.add(p[1])

    @_('function_definition', 'declaration')
    def external_declaration(self, p):
        return ExternalDeclaration(p.lineno, declaration=p[0], type=ptype(p))

    """
    Note, function definition are split into several production to distinguish them in AST
    If not split, the combined production is as below
    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement',
       'declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition(self, p): pass
    """

    @_('declaration_specifiers declarator declaration_list compound_statement',
       'declaration_specifiers declarator compound_statement')
    def function_definition_declaration_specifiers(self, p):
        """
        declaration_specifiers: function returning... (type)
        declarator: possibly pointer and function name and formal parameters
        declaration_list: formal parameters (name and type)
        compound_statement: list of statements in function body (including local variable)
        """
        if len(p) == 4:
            return FunctionDefinition(p.lineno,
                                      declaration_specifiers=p[0],
                                      declarator=p[1],
                                      declaration_list=ASTList(p.lineno, items=p[2]),
                                      compound_statement=p[3])
        else:
            return FunctionDefinition(p.lineno,
                                      declaration_specifiers=p[0],
                                      declarator=p[1],
                                      declaration_list=None,  # No formal parameters
                                      compound_statement=p[2])

    @_('declarator declaration_list compound_statement',
       'declarator compound_statement')
    def function_definition_declarator(self, p):
        if len(p) == 3:
            return FunctionDefinition(p.lineno,
                                      declarator=p[0],
                                      declaration_specifiers=None,
                                      declaration_list=ASTList(p.lineno, items=p[1]),
                                      compound_statement=p[2])
        else:
            return FunctionDefinition(p.lineno,
                                      declarator=p[0],
                                      declaration_specifiers=None,
                                      declaration_list=None,
                                      compound_statement=p[1])

    @_('function_definition_declaration_specifiers',
       'function_definition_declarator')
    def function_definition(self, p):
        return p[0]

if __name__ == '__main__':
    dir = './src/'
    #fn = ['c0_tot.c', 'c1_tot.c', 'c2_tot.c', 'cvopt.c', 'c0h.c', 'c1h.c', 'c2h.c']
    fn = ['c00.c']
    #fn = ['c0h.c']
    #fn = ['cc_test.c']

    cc_parser = CCparser()
    for i in range(len(fn)):
        result = cc_parser.compile(fn[i], wd=dir)
        cc_parser.dump("CCParser.json")
        #cc_parser.prg.print()

        pprint.pp(cc_parser.prg.decl(), compact=True)

