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

    def __str__(self):
        return f'PE - {self.lineno}: {self.args}'

#---------- Postfix expressions = PFE ----------

class PostfixExpression(Expression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

    def __str__(self):
        arg = '' if self.args is None else f' {self.args}'
        return f'PFE - {self.lineno}: {self.expr} {arg}'

class PFESubscript(PostfixExpression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

class PFEFunctionCall(PostfixExpression):
    def __init__(self, lineno, expr, args):
        super().__init__(lineno, expr, args)

class PFEMemberOfStructure(PostfixExpression):
    def __init__(self, lineno, expr, operator, Id):
        super().__init__(lineno, expr, Id)
        self.operator = operator

class PFEIncrDecr(PostfixExpression):
    def __init__(self, lineno, expr, operator):
        super().__init__(lineno, expr)
        self.operator = operator

#---------- Unary expressions ----------

class UnaryExpression(Expression):
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno, expr, args)

    def __str__(self):
        return f'UN - {self.lineno}: {self.expr}'

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

#---------- Other expressions ----------

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

class Initializer(Node):
    def __init__(self, lineno, value, expr=None):
        super().__init__(lineno)
        self.value = value
        self.expr = expr

class ConstantInitExpression(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)