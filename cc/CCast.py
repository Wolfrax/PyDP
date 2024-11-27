# This is the implementation of the abstract syntax tree (AST) created during parsing (CCParser)
#
"""
Classes

Node:Generic class that is inherited by other nodes for ast.
Attributes and methods
    lineno: The line number of the c file from where the node is derived
    exec: 'Execute' the node
    __str__: The string representation of the node

    Expression
        primary-expression:
            identifier: A declared expression
            constant: decimal, octal, character or floating (type is int in first 3 cases)
            string: pointer to first character of string
            ( expression ): simply expression
            primary-expression [ expression ]
            primary-expression ( expression-list )
            primary-lvalue . member-of-structure
            primary-expression -> member-of-structure

            Operators: (), [], ., ->


    Declaration
    Statement
    Definition

"""

class Node:
    def __init__(self, lineno):
        self.lineno = lineno

    def __str__(self):
        return str(self.lineno)

    def exec(self):
        pass

class Expression(Node):
    def __init__(self, lineno, expr=None, args=None):
        super().__init__(lineno)
        self.expr = expr
        self.args = args

class PrimaryExpression(Expression):
    def __init__(self, lineno, value):
        super().__init__(lineno, value)

class PostfixExpression(Expression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

    def __str__(self):
        arg = '' if self.args is None else f' {self.args}'
        return f'PFE - {self.lineno}: {self.expr} {arg}'

class PostfixExpressionSubscript(PostfixExpression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

class PostfixExpressionFunctionCall(PostfixExpression):
    def __init__(self, lineno, expr, args):
        super().__init__(lineno, expr, args)

class PostfixExpressionMemberOfStructure(PostfixExpression):
    def __init__(self, lineno, expr, operator, Id):
        super().__init__(lineno, expr, Id)
        self.operator = operator

class PostfixExpressionIncrDecr(PostfixExpression):
    def __init__(self, lineno, expr, operator):
        super().__init__(lineno, expr)
        self.operator = operator

class UnaryExpression(Expression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

class UnaryExpressionIncrDecr(UnaryExpression):
    def __init__(self, lineno, expr, operator):
        super().__init__(lineno, expr)
        self.operator = operator

class UnaryExpressionCastExpr(UnaryExpression):
    def __init__(self, lineno, expr, operator):
        super().__init__(lineno, expr)
        self.operator = operator

class UnaryExpressionSizeof(UnaryExpression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

class UnaryExpressionSizeofType(UnaryExpression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

class CastExpression(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

class BinOpExpression(Expression):
    def __init__(self, lineno, expr1, expr2=None,operand=None):
        super().__init__(lineno, expr1)
        self.expr2 = expr2
        self.operand = operand

class ConditionalExpression(Expression):
    def __init__(self, lineno, expr1, expr2, expr3):
        super().__init__(lineno, expr1)
        self.expr2 = expr2
        self.expr3 = expr3

class ArgumentExpressionList(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

class Declaration(Node):
    def __init__(self, lineno, decl_specifier, initializer=None):
        super().__init__(lineno)
        self.decl_specifier = decl_specifier
        self.initializer = initializer

class Declarator(Declaration):
    def __init__(self, lineno, direct_declarator, pointer=None):
        super().__init__(lineno, None)
        self.direct_declarator = direct_declarator
        self.pointer = pointer

class DeclarationSpecifierStorageClass(Declaration):
    def __init__(self, lineno, decl_specifier, storage_class):
        super().__init__(lineno, decl_specifier)
        self.storage_class = storage_class

class DeclarationSpecifierTypeSpecifier(Declaration):
    def __init__(self, lineno, decl_specifier, type_specifier):
        super().__init__(lineno, decl_specifier)
        self.type_specifier = type_specifier

class DeclarationSpecifier(Declaration):
    def __init__(self, lineno, decl_specifier):
        super().__init__(lineno, decl_specifier)

class InitDeclarator(Declaration):
    def __init__(self, lineno, declarator, initializer):
        super().__init__(lineno, declarator, initializer)

class DirectDeclaratorID(Declaration):
    def __init__(self, lineno, ID_or_declarator):
        super().__init__(lineno, None)
        self.ID_or_declarator = ID_or_declarator

class DirectDeclaratorConstantExpression(Declaration):
    def __init__(self, lineno, direct_declarator, constant_expression=None):
        super().__init__(lineno, None)
        self.direct_declarator = direct_declarator
        self.constant_expression = constant_expression

class DirectDeclaratorParameterTypeList(Declaration):
    def __init__(self, lineno, direct_declarator, parameter_type_list):
        super().__init__(lineno, None)
        self.direct_declarator = direct_declarator
        self.parameter_type_list = parameter_type_list

class DirectDeclaratorIdentifierList(Declaration):
    def __init__(self, lineno, direct_declarator, identifier_list=None):
        super().__init__(lineno, None)
        self.direct_declarator = direct_declarator
        self.identifier_list = identifier_list

class DirectDeclarator(Declaration):
    def __init__(self, lineno, declarator):
        super().__init__(lineno, declarator)

class StructSpecifier(Declaration):
    def __init__(self, lineno, id, decl_specifier):
        super().__init__(lineno, decl_specifier)
        self.id = id

class StructDeclaration(Declaration):
    def __init__(self, lineno, specifier_qualifiers, declarators):
        super().__init__(lineno, None)
        self.declarators = declarators
        self.specifier_qualifiers = specifier_qualifiers

class StructDeclarator(Declaration):
    def __init__(self, lineno, declarator):
        super().__init__(lineno, declarator)

class ParameterDeclaration(Declaration):
    def __init__(self, lineno, declaration_specifiers, declarator=None):
        super().__init__(lineno, declarator)
        self.declaration_specifiers = declaration_specifiers

class Initializer(Node):
    def __init__(self, lineno, value, expr=None):
        super().__init__(lineno)
        self.value = value
        self.expr = expr

class ConstantInitExpression(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

class Pointer(Node):
    def __init__(self, lineno, pointer=None):
        super().__init__(lineno)
        self.pointer = pointer

class ParameterTypeList(Node):
    def __init__(self, lineno, parameter_list):
        super().__init__(lineno)
        self.parameter_list = parameter_list

class TypeName(Node):
    def __init__(self, lineno, specifier_qualifier_list, abstract_declarator=None):
        super().__init__(lineno)
        self.specifier_qualifier_list = specifier_qualifier_list
        self.abstract_declarator = abstract_declarator

class Statement(Node):
    def __init__(self, lineno, statement=None):
        super().__init__(lineno)
        self.statement = statement

class LabeledStatement(Statement):
    def __init__(self, lineno, label, constant_expression, statement):
        super().__init__(lineno, statement)
        self.label = label
        self.constant_expression = constant_expression

class CompoundStatementStatementList(Statement):
    def __init__(self, lineno, statement_list):
        super().__init__(lineno)
        self.statement_list = statement_list

class CompoundStatementDeclarationList(Statement):
    def __init__(self, lineno, declaration_list):
        super().__init__(lineno)
        self.declaration_list = declaration_list

class CompoundStatementDeclarationListStatementList(Statement):
    def __init__(self, lineno, declaration_list, statement_list):
        super().__init__(lineno)
        self.declaration_list = declaration_list
        self.statement_list = statement_list

class CompoundStatement(Statement):
    def __init__(self, lineno, list):
        super().__init__(lineno)
        self.list = list

class ExpressionStatement(Statement):
    def __init__(self, lineno, expression):
        super().__init__(lineno)
        self.expression = expression

class SelectionStatementIfThenElse(Statement):
    def __init__(self, lineno, op, expression, statement1, statement2=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression
        self.statement1 = statement1
        self.statement2 = statement2

class SelectionStatementSwitch(Statement):
    def __init__(self, lineno, expression, statement):
        super().__init__(lineno)
        self.expression = expression
        self.statement = statement

class SelectionStatement(Statement):
    def __init__(self, lineno, statement):
        super().__init__(lineno)
        self.statement = statement

class IterationStatementWhile(Statement):
    def __init__(self, lineno, op, expression, statement):
        super().__init__(lineno)
        self.op = op
        self.expression = expression
        self.statement = statement

class IterationStatementFor(Statement):
    def __init__(self, lineno, expression, expression_statement1, expression_statement2, statement):
        super().__init__(lineno)
        self.expression = expression
        self.expression_statement1 = expression_statement1
        self.expression_statement2 = expression_statement2
        self.statement = statement

class IterationStatement(Statement):
    def __init__(self, lineno, statement):
        super().__init__(lineno)
        self.statement = statement

class JumpStatement(Statement):
    def __init__(self, lineno, op, expression=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression

class ExternalDeclaration(Node):
    def __init__(self, lineno, declaration):
        super().__init__(lineno)
        self.declaration = declaration

class FunctionDefinitionDeclarationSpecifier(Node):
    def __init__(self, lineno, declaration_specifiers, declarator, declaration_list, compound_statement):
        super().__init__(lineno)
        self.declaration_specifiers = declaration_specifiers
        self.declarator = declarator
        self.declaration_list = declaration_list
        self.compound_statement = compound_statement

class FunctionDefinitionDeclarator(Node):
    def __init__(self, lineno, declarator, declaration_list, compound_statement):
        super().__init__(lineno)
        self.declarator = declarator
        self.declaration_list = declaration_list
        self.compound_statement = compound_statement

class FunctionDefinition(Node):
    def __init__(self, lineno, function_definition):
        super().__init__(lineno)
        self.function_definition = function_definition