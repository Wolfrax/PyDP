# This is the implementation of the abstract syntax tree (AST) created during parsing (CCParser)
#

from llvmlite import ir

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

xstr = lambda s: '' if s is None else str(s)

class StrPrefix:
    def __init__(self):
        self.indent = 0
        self.do_indent = True

    def lvl(self):
        if self.do_indent:
            s = '\n' + ' ' * self.indent
            self.indent += 1
        else:
            s = ""
        return s

    def reset_indent(self):
        self.indent = 0

pstr = StrPrefix()

class Node:
    def __init__(self, lineno):
        self.lineno = lineno

    def __str__(self):
       return ''

    def exec(self):
        pass

    def ir(self):
        return ""

class ASTList(Node):
    def __init__(self, lineno, items):
        super().__init__(lineno)
        self.list = items

    def __str__(self):
        pstr.do_indent = False
        string = " ["
        for item in self.list:
            string += (str(item) + ", ")
        pstr.do_indent = True
        return string[:-2] + "]"

    def ir(self):
        for item in self.list:
            item.ir()

class Expression(Node):  # Note, not used in Parser
    def __init__(self, lineno, expr, args=None):
        super().__init__(lineno)
        self.expr = expr
        self.args = args
        self.ir_expr = None

    def __str__(self):
        return f"{pstr.lvl()}Expression({super().__str__()}{xstr(self.expr)} {xstr(self.args)})"

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

class PrimaryExpression(Expression):
    """
    A primary expression can be tokens ID, CONSTANT, STRING_LITERAL or an expression, referenced in attribute expr
    """
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

    def __str__(self):
        return f"{pstr.lvl()}PrimaryExpression({super().__str__()})"

    def ir(self):
        super().ir()
        print(f"{self.ir_expr}")
        # self.expr.ir() if self.expr is not None else None

class PostfixExpression(Expression):
    def __init__(self, lineno, expr, args, op, id):
        super().__init__(lineno, expr, args)
        self.op = op
        self.id = id

    def __str__(self):
        return f"{pstr.lvl()}PostfixExpression({super().__str__()}{xstr(self.op)} {xstr(self.id)})"

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class UnaryExpression(Expression):
    def __init__(self, lineno, op, expr):
        super().__init__(lineno, expr)
        self.op = op

    def __str__(self):
        return f"{pstr.lvl()}UnaryExpression({super().__str__()}{xstr(self.op)})"

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class CastExpression(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

    def __str__(self):
        return f"{pstr.lvl()}CastExpression({super().__str__()})"

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class BinOpExpression(Expression):
    def __init__(self, lineno, expr_l, expr_r, op):
        super().__init__(lineno, None)
        self.expr_l = expr_l
        self.expr_r = expr_r
        self.op = op

    def __str__(self):
        return (f"{pstr.lvl()}BinOpExpression({super().__str__()}{xstr(self.expr_l)} {xstr(self.op)} "
                f"{xstr(self.expr_r)})")

    def ir(self):
        super().ir()
        self.expr_l.ir() if self.expr_l is not None else None
        self.expr_r.ir() if self.expr_r is not None else None

class ConditionalExpression(Expression):
    def __init__(self, lineno, expr1, expr2, expr3):
        super().__init__(lineno, expr1)
        self.expr2 = expr2
        self.expr3 = expr3

    def __str__(self):
        return f"{pstr.lvl()}ConditionalExpression({super().__str__()} {xstr(self.expr2)} {xstr(self.expr3)})"

    def ir(self):
        super().ir()
        self.expr2.ir() if self.expr2 is not None else None
        self.expr3.ir() if self.expr3 is not None else None

class ArgumentExpressionList(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

    def __str__(self):
        return f"{pstr.lvl()}ArgumentExpressionList({super().__str__()})"

class ConstantInitExpression(Expression):
    def __init__(self, lineno, expr):
        super().__init__(lineno, expr)

    def __str__(self):
        return f"{pstr.lvl()}ConstantInitExpression({super().__str__()})"

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

    def __str__(self):
        return f"{pstr.lvl()}Declaration({super().__str__()} {xstr(self.decl_specifier)} {xstr(self.initializer)})"

class Declarator(Declaration):
    def __init__(self, lineno, direct_declarator, pointer):
        super().__init__(lineno, None)
        self.direct_declarator = direct_declarator
        self.pointer = pointer

    def __str__(self):
        return f"{pstr.lvl()}Declarator({super().__str__()} {xstr(self.direct_declarator)} {xstr(self.pointer)})"

    def ir(self):
        super().ir()
        self.direct_declarator.ir() if self.direct_declarator is not None else None
        self.pointer.ir() if self.pointer is not None else None

class DeclarationSpecifiers(Declaration):
    def __init__(self, lineno, storage_class, type):
        super().__init__(lineno, None, None)
        self.storage_class = storage_class
        self.type = type

    def __str__(self):
        return f"{pstr.lvl()}DeclarationSpecifiers({super().__str__()} {xstr(self.storage_class)} {xstr(self.type)})"

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

class InitDeclarator(Declaration):
    def __init__(self, lineno, declarator, initializer):
        super().__init__(lineno, declarator, initializer)

    def __str__(self):
        return f"{pstr.lvl()}InitDeclarator({super().__str__()})"

    def ir(self):
        super().ir()

class DirectDeclarator(Declaration):
    def __init__(self, lineno, id, identifiers, decl, expr):
        super().__init__(lineno, decl)
        self.id = id
        self.identifiers = identifiers
        self.expr = expr

    def __str__(self):
        return (f"{pstr.lvl()}DirectDeclarator({super().__str__()} {xstr(self.id)} {xstr(self.identifiers)} "
                f"{xstr(self.expr)})")

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class StructSpecifier(Declaration):
    def __init__(self, lineno, id, decl_specifier):
        super().__init__(lineno, decl_specifier)
        self.id = id

    def __str__(self):
        return f"{pstr.lvl()}StructSpecifier({super().__str__()} {xstr(self.id)})"

    def ir(self):
        super().ir()

class StructDeclaration(Declaration):
    def __init__(self, lineno, specifier_qualifiers, declarators):
        super().__init__(lineno, None)
        self.declarators = declarators
        self.specifier_qualifiers = specifier_qualifiers

    def __str__(self):
        return (f"{pstr.lvl()}StructDeclaration({super().__str__()} {xstr(self.specifier_qualifiers)} "
                f"{xstr(self.declarators)})")

    def ir(self):
        super().ir()
        self.declarators.ir() if self.declarators is not None else None
        self.specifier_qualifiers.ir() if self.specifier_qualifiers is not None else None

class ParameterDeclaration(Declaration):
    def __init__(self, lineno, declaration_specifiers, declarator=None):
        super().__init__(lineno, declarator)
        self.declaration_specifiers = declaration_specifiers

    def __str__(self):
        return f"{pstr.lvl()}ParameterDeclaration({super().__str__()} {xstr(self.declaration_specifiers)})"

    def ir(self):
        super().ir()
        self.declaration_specifiers.ir() if self.declaration_specifiers is not None else None

class Initializer(Node):
    def __init__(self, lineno, value, expr):
        super().__init__(lineno)
        self.value = value
        self.expr = expr

    def __str__(self):
        return f"{pstr.lvl()}Initializer({super().__str__()} {xstr(self.expr)} {xstr(self.value)})"

    def ir(self):
        self.expr.ir() if self.expr is not None else None

class Pointer(Node):
    def __init__(self, lineno, pointer):
        super().__init__(lineno)
        self.pointer = pointer

    def __str__(self):
        return f"{pstr.lvl()}Pointer({super().__str__()} {xstr(self.pointer)})"

    def ir(self):
        self.pointer.ir() if self.pointer is not None else None

class ParameterTypeList(Node):
    def __init__(self, lineno, parameter_list):
        super().__init__(lineno)
        self.parameter_list = parameter_list

    def __str__(self):
        return f"{pstr.lvl()}ParameterTypeList({super().__str__()} {xstr(self.parameter_list)})"

    def ir(self):
        self.parameter_list.ir() if self.parameter_list is not None else None

class TypeName(Node):
    def __init__(self, lineno, specifier_qualifier_list, abstract_decl):
        super().__init__(lineno)
        self.specifier_qualifier_list = specifier_qualifier_list
        self.abstract_decl = abstract_decl

    def __str__(self):
        return (f"{pstr.lvl()}TypeName({super().__str__()} {xstr(self.specifier_qualifier_list)} "
                f"{xstr(self.abstract_decl)})")

    def ir(self):
        self.abstract_decl.ir() if self.abstract_decl is not None else None
        self.specifier_qualifier_list.ir() if self.specifier_qualifier_list is not None else None

class Statement(Node):
    def __init__(self, lineno, stmt=None):
        super().__init__(lineno)
        self.stmt = stmt

    def __str__(self):
        return f"{pstr.lvl()}Statement({super().__str__()} {xstr(self.stmt)})"

    def ir(self):
        self.stmt.ir() if self.stmt is not None else None

class LabeledStatement(Statement):
    def __init__(self, lineno, lbl, expr, stmt):
        super().__init__(lineno, stmt)
        self.lbl = lbl
        self.const_expr = expr

    def __str__(self):
        return f"{pstr.lvl()}LabeledStatement({xstr(self.lbl)} {xstr(self.const_expr)} {super().__str__()} )"

    def ir(self):
        super().ir()
        self.lbl.ir() if self.lbl is not None else None
        self.const_expr.ir() if self.const_expr is not None else None

class CompoundStatement(Statement):
    def __init__(self, lineno, decl, stmt):
        super().__init__(lineno, stmt)
        self.decl = decl

    def __str__(self):
        return f"{pstr.lvl()}CompoundStatement({xstr(self.decl)} {super().__str__()} )"

    def ir(self):
        super().ir()
        self.decl.ir() if self.decl is not None else None

class ExpressionStatement(Statement):
    def __init__(self, lineno, expr):
        super().__init__(lineno)
        self.expr = expr

    def __str__(self):
        return f"{pstr.lvl()}ExpressionStatement({xstr(self.expr)} {super().__str__()})"

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class SelectionStatement(Statement):
    def __init__(self, lineno, op, expr, stmt, else_stmt):
        super().__init__(lineno, stmt)
        self.op = op
        self.expr = expr
        self.else_stmt = else_stmt

    def __str__(self):
        return (f"{pstr.lvl()}SelectionStatement({super().__str__()} {xstr(self.expr)} "
                f"{xstr(self.op)} {xstr(self.else_stmt)})")

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None
        self.else_stmt.ir() if self.else_stmt is not None else None

class IterationStatement(Statement):
    def __init__(self, lineno, op, expr1, expr2, expr3, stmt):
        super().__init__(lineno, stmt)
        self.op = op
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3

    def __str__(self):
        return (f"{pstr.lvl()}IterationStatement({super().__str__()} {xstr(self.expr1)} "
                f"{xstr(self.expr2)} {xstr(self.expr3)})")

    def ir(self):
        super().ir()
        self.expr1.ir() if self.expr1 is not None else None
        self.expr2.ir() if self.expr2 is not None else None
        self.expr3.ir() if self.expr3 is not None else None

class JumpStatement(Statement):
    def __init__(self, lineno, op, expr):
        super().__init__(lineno)
        self.op = op
        self.expr = expr

    def __str__(self):
        return f"{pstr.lvl()}JumpStatement({super().__str__()} {xstr(self.expr)} {xstr(self.op)})"

    def ir(self):
        super().ir()
        self.expr.ir() if self.expr is not None else None

class ExternalDeclaration(Node):
    def __init__(self, lineno, decl):
        super().__init__(lineno)
        self.decl = decl

    def __str__(self):
        return f"{pstr.lvl()}ExternalDeclaration({super().__str__()} {xstr(self.decl)})"

    def ir(self):
        self.decl.ir() if self.decl is not None else None

class FunctionDefinition(Node):
    def __init__(self, lineno, decl, decl_specifiers, decl_list, stmt):
        super().__init__(lineno)
        self.decl = decl
        self.decl_specifiers = decl_specifiers
        self.decl_list = decl_list
        self.stmt = stmt

    def __str__(self):
        return (f"{pstr.lvl()}FunctionDefinition({super().__str__()} {xstr(self.decl)} {xstr(self.decl_specifiers)} "
                f"{xstr(self.decl_list)} {xstr(self.stmt)})")

    def ir(self):
        self.decl_list.ir() if self.decl_list is not None else None
        self.decl_specifiers.ir() if self.decl_specifiers is not None else None
        self.decl.ir() if self.decl is not None else None
        self.stmt.ir() if self.stmt is not None else None