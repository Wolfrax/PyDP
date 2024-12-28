# This is the implementation of the abstract syntax tree (AST) created during parsing (CCParser)
#

from llvmlite import ir
import pprint
import json

"""
Classes

Node:Generic class that is inherited by other nodes for ast.
Attributes and methods
    lineno: The line number of the c file from where the node is derived
    exec: 'Execute' the node
    __repr__: The string representation of the node

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
        #self.attr = {'line': lineno, 'name': self.__class__.__name__}
        self._lineno = lineno
        self.node = self.__class__.__name__

    def exec(self):
        pass

    def ir(self):
        return ""

class ASTList(Node):

    def __init__(self, lineno, items):
        super().__init__(lineno)
        self.list = items

    def ir(self):
        for item in self.list:
            item.ir()

class Expression(Node):  # Note, not used in Parser
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno)
        self.expr = expr
        self.args = args
        self.ir_expr = None

    def ir(self):
        if type(self.expr) is str:
            self.ir_expr = ir.Constant(ir.IntType(16), self.expr)
            """
            if self.decl_specifier == 'int':
                self.ir_type = ir.IntType(16)
            elif self.decl_specifier == 'char':
                self.ir_type = ir.IntType(8)
            elif self.decl_specifier == 'float':
                self.ir_type = ir.FloatType()  # HalfType?
            elif self.decl_specifier == 'double':
                self.ir_type = ir.DoubleType()
            else:
                pass
            """
        #self.expr.ir() if self.expr is not None else None
        #self.args.ir() if self.args is not None else None

class PrimaryExpression(Node):
    """
    A primary expression can be tokens ID, CONSTANT, STRING_LITERAL or an expression, referenced in attribute expr
    """
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

    def ir(self):
        super().ir()
        # self.expr.ir() if self.expr is not None else None

class PostfixExpression(Node):
    def __init__(self, lineno, expr, args, op, id):
        super().__init__(lineno)
        self.expr = expr
        self.args = args
        self.op = op
        self.id = id

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class UnaryExpression(Node):
    def __init__(self, lineno, op, expr):
        super().__init__(lineno)
        self.op = op
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class CastExpression(Node):
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class BinOpExpression(Node):
    def __init__(self, lineno, expr_l, expr_r, op):
        super().__init__(lineno)
        self.expr_l = expr_l
        self.expr_r = expr_r
        self.op = op

    def ir(self):
        super().ir()
        self.expr_l.ir() if self.expr_l is not None else None
        self.expr_r.ir() if self.expr_r is not None else None

class ConditionalExpression(Node):
    def __init__(self, lineno, expr1, expr2, expr3):
        super().__init__(lineno)
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3

    def ir(self):
        super().ir()
        self.expr2.ir() if self.expr2 is not None else None
        self.expr3.ir() if self.expr3 is not None else None

class ArgumentExpressionList(Node):
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

class ConstantInitExpression(Node):
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class Declaration(Node):
    def __init__(self, lineno, decl_specifier, initializer=None):
        super().__init__(lineno)
        self.decl_specifier = decl_specifier
        self.initializer = initializer
        self.ir_type = None

    def ir(self):
        # derive type from decl_specifier: type and or storage class
        if type(self.decl_specifier) is str:
            if self.decl_specifier == 'int':
                self.ir_type = ir.IntType(16)
            elif self.decl_specifier == 'char':
                self.ir_type = ir.IntType(8)
            elif self.decl_specifier == 'float':
                self.ir_type = ir.FloatType()  # HalfType?
            elif self.decl_specifier == 'double':
                self.ir_type = ir.DoubleType()
            else:
                pass

            print(self.ir_type)
        elif self.decl_specifier is None:
            pass
        else:
            ir_decl_spec = self.decl_specifier.ir()
            print(ir_decl_spec)

class Declarator(Node):
    def __init__(self, lineno, direct_declarator, pointer):
        super().__init__(lineno)
        self.direct_declarator = direct_declarator
        self.pointer = pointer

    def ir(self):
        super().ir()
        self.direct_declarator.ir() if self.direct_declarator is not None else None
        self.pointer.ir() if self.pointer is not None else None

class DeclarationSpecifiers(Node):
    def __init__(self, lineno, storage_class, type):
        super().__init__(lineno)
        self.storage_class = storage_class
        self.type = type

    def ir(self):
        super().ir()
        if self.type == 'int':
            self.ir_type = ir.IntType(16)
        elif self.type == 'char':
            self.ir_type = ir.IntType(8)
        elif self.type == 'float':
            self.ir_type = ir.FloatType()  # HalfType?
        elif self.type == 'double':
            self.ir_type = ir.DoubleType()
        else:
            pass
            # raise NotImplementedError

class InitDeclarator(Node):
    def __init__(self, lineno, declarator, initializer):
        super().__init__(lineno)
        self.declarator = declarator
        self.initializer = initializer

    def ir(self):
        super().ir()

class DirectDeclarator(Node):
    def __init__(self, lineno, identifiers, decl, expr):
        super().__init__(lineno)
        self.identifiers = identifiers
        self.decl = decl
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class StructSpecifier(Node):
    def __init__(self, lineno, id, decl_specifier):
        super().__init__(lineno)
        self.id = id
        self.decl_specifier = decl_specifier

    def ir(self):
        super().ir()

class StructDeclaration(Node):
    def __init__(self, lineno, specifier_qualifiers, declarators):
        super().__init__(lineno)
        self.declarators = declarators
        self.specifier_qualifiers = specifier_qualifiers

    def ir(self):
        super().ir()
        self.declarators.ir() if self.declarators is not None else None
        self.specifier_qualifiers.ir() if self.specifier_qualifiers is not None else None

class ParameterDeclaration(Node):
    def __init__(self, lineno, declaration_specifiers, declarator=None):
        super().__init__(lineno)
        self.declaration_specifiers = declaration_specifiers
        self.declarator = declarator

    def ir(self):
        super().ir()
        self.declaration_specifiers.ir() if self.declaration_specifiers is not None else None

class Initializer(Node):
    def __init__(self, lineno, value, expr):
        super().__init__(lineno)
        self.value = value
        self.expr = expr

    def ir(self):
        self.expr.ir() if self.expr is not None else None

class Pointer(Node):
    def __init__(self, lineno, pointer):
        super().__init__(lineno)
        self.pointer = pointer

    def ir(self):
        self.pointer.ir() if self.pointer is not None else None

class ParameterTypeList(Node):
    def __init__(self, lineno, parameter_list):
        super().__init__(lineno)
        self.parameter_list = parameter_list

    def ir(self):
        self.parameter_list.ir() if self.parameter_list is not None else None

class TypeName(Node):
    def __init__(self, lineno, specifier_qualifier_list, abstract_decl):
        super().__init__(lineno)
        self.specifier_qualifier_list = specifier_qualifier_list
        self.abstract_decl = abstract_decl

    def ir(self):
        self.abstract_decl.ir() if self.abstract_decl is not None else None
        self.specifier_qualifier_list.ir() if self.specifier_qualifier_list is not None else None

class Statement(Node):
    def __init__(self, lineno, stmt=None):
        super().__init__(lineno)
        self.stmt = stmt

    def ir(self):
        self.stmt.ir() if self.stmt is not None else None

class LabeledStatement(Node):
    def __init__(self, lineno, lbl, expr, stmt):
        super().__init__(lineno)
        self.lbl = lbl
        self.const_expr = expr
        self.stmt = stmt

    def ir(self):
        super().ir()
        self.lbl.ir() if self.lbl is not None else None
        self.const_expr.ir() if self.const_expr is not None else None

class CompoundStatement(Node):
    def __init__(self, lineno, decl, stmt):
        super().__init__(lineno)
        self.decl = decl
        self.stmt = stmt

    def ir(self):
        super().ir()
        self.decl.ir() if self.decl is not None else None

class ExpressionStatement(Node):
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class SelectionStatement(Node):
    def __init__(self, lineno, op, expr, stmt, else_stmt):
        super().__init__(lineno)
        self.op = op
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None
        self.else_stmt.ir() if self.else_stmt is not None else None

class IterationStatement(Node):
    def __init__(self, lineno, op, expr1, expr2, expr3, stmt):
        super().__init__(lineno)
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3
        self.stmt = stmt

    def ir(self):
        super().ir()
        self.expr1.ir() if self.expr1 is not None else None
        self.expr2.ir() if self.expr2 is not None else None
        self.expr3.ir() if self.expr3 is not None else None

class JumpStatement(Node):
    def __init__(self, lineno, op, expr):
        super().__init__(lineno)
        self.op = op
        self.expr = expr

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class ExternalDeclaration(Node):
    def __init__(self, lineno, decl):
        super().__init__(lineno)
        self.decl = decl

    def ir(self):
        self.decl.ir() if self.decl is not None else None

class FunctionDefinition(Node):
    def __init__(self, lineno, decl, decl_specifiers, decl_list, stmt):
        super().__init__(lineno)
        self.decl = decl
        self.decl_specifiers = decl_specifiers
        self.decl_list = decl_list
        self.stmt = stmt

    def ir(self):
        self.decl_list.ir() if self.decl_list is not None else None
        self.decl_specifiers.ir() if self.decl_specifiers is not None else None
        self.decl.ir() if self.decl is not None else None
        self.stmt.ir() if self.stmt is not None else None

class TranslationUnit(Node):
    def __init__(self, lineno):
        super().__init__(lineno)
        self.external_declarations = []

    def add(self, decl):
        self.external_declarations.append(decl)

class Program:
    def __init__(self):
        self.translation_unit = TranslationUnit(1)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self.translation_unit.external_declarations):
            item = self.translation_unit.external_declarations[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration

    def __str__(self):
        return (json.dumps(
            {'translation_unit': self.translation_unit},
            # filter out fields with '_' prefix and None values
            default=lambda n: {k: v for k, v in n.__dict__.items() if not k.startswith('_') and v is not None}))

    def json(self):
        return json.loads(str(self))

    def print(self):
        pprint.pprint(self.json(), width=80, compact=True)
