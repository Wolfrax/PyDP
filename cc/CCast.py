# This is the implementation of the abstract syntax tree (AST) created during parsing (CCParser)

import pprint
import json
import CCconf
from CC import CCError

#from llvmlite.binding import StorageClass

class Node:
    def __init__(self, lineno):
        self._lineno = lineno
        name = self.__class__.__name__
        self._node = None if name == 'ASTList' else name

class ASTList(Node):
    def __init__(self, lineno, items):
        super().__init__(lineno)
        self.list = items
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self.list):
            item = self.list[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration

    def get(self):
        return self.list

class PrimaryExpression(Node):
    def __init__(self, lineno, constant=None, expression=None):
        super().__init__(lineno)

        if constant is None and expression is None:
            raise CCError(f'{self.__class__.__name__}: '
                          f'PrimaryExpression: constant and expression cannot be None ({self._lineno})')

        if constant is not None:
            if isinstance(constant, str):
                if constant[0] == "\"" and constant[-1] == "\"":
                    self._ctx = 'string_literal'
                else:
                    self._ctx = 'id'
            elif isinstance(constant, int):
                self._ctx = 'int'
            elif isinstance(constant, float):
                self._ctx = 'float'
            else:
                raise CCError(f'{self.__class__.__name__}: '
                              f'PrimaryExpression: unsupported constant type: {constant} ({self._lineno})')
        else:
            self._ctx = 'expr'

        if self._ctx in ['string_literal', 'id', 'int', 'float']:
            self.value = constant
        else:
            self.value = None

        self.expression = expression

    def eval(self):
        if self._ctx in ['string_literal', 'id', 'int', 'float']:
            return self.value

        return self.expression.eval()

class PostfixExpression(Node):
    __ctx = {'[': 'subscript', '(': 'func', '.': 'struct', '->': 'pointer', '++': 'incr', '--': 'decr'}

    def __init__(self, lineno, op, postfix_expression=None, expression=None, argument_expression_list=None, id=None):
        super().__init__(lineno)

        if op in self.__ctx:
            self._ctx = self.__ctx[op]
        else:
            raise CCError(f'{self.__class__.__name__}: '
                          f'Postfix expression: Unknown operator {op} ({self._lineno})')

        self.postfix_expression = postfix_expression  # Should be PrimaryExpression: id
        self.expression = expression  # Used in subscript, such as a[b+1], expression == b+1
        self.argument_expression_list = argument_expression_list  # Used for functions calls, actual parameters
        self.id = id  # Used for struct members or pointers, eg a.ID or a->ID

    def eval(self):
        return self.id

    def stmt(self):
        if self._ctx == 'func':
            args = ''
            if self.argument_expression_list is not None:
                for arg in self.argument_expression_list:
                    args += str(arg.eval())
            return f"{self._ctx} {self.postfix_expression.eval()} {args}"
        return ''

class UnaryExpression(Node):
    def __init__(self, lineno, op, unary_expression=None, type_name=None):
        super().__init__(lineno)
        self.op = op
        self.unary_expression = unary_expression
        self.type_name = type_name

    def eval(self):
        return None

    def stmt(self):
        return f"{self.op} {self.type_name} {self.unary_expression}"

class BinOpExpression(Node):
    def __init__(self, lineno, op, expr_l, expr_r):
        super().__init__(lineno)
        self.expr_l = expr_l
        self.expr_r = expr_r
        self.op = op

    def eval(self):
        left = self.expr_l.eval()
        right = self.expr_r.eval()

        type_l = type(left)
        type_r = type(right)

        if type_l != type_r:
            if (isinstance(left, int) and isinstance(right, float)) or (isinstance(left, float) and isinstance(right, int)):
                pass
            elif (isinstance(left, int) and isinstance(right, str)) or (isinstance(left, str) and isinstance(right, int)):
                if isinstance(right, str):
                    right = CCconf.compiler.symbols.get(right)
                else:
                    left = CCconf.compiler.symbols.get(left)
            else:
                raise CCError(f'{self.__class__.__name__}: not compatible types ({self._lineno})')

        if self.op == '+':
            return left + right
        elif self.op == '-':
            return left - right
        elif self.op == '*':
            return left * right
        elif self.op == '/':
            return left / right
        elif self.op == '<<':
            return left << right
        elif self.op == '>>':
            return left >> right
        elif self.op == '|':
            return left | right
        else:
            raise CCError(f'{self.__class__.__name__}: unsupported operator ({self._lineno})')

    def stmt(self):
        return f"{self.op} {self.expr_l} {self.expr_r}"

class ConditionalExpression(Node):
    def __init__(self, lineno, expr1, expr2, expr3):
        super().__init__(lineno)
        # expr1 ? expr2 : expr3
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3

class Declaration(Node):
    def __init__(self, lineno, decl_specifier, initializer):
        super().__init__(lineno)
        self.declaration_specifiers = decl_specifier
        self.init_declarator_list = initializer

    def decl(self):
        declaration = []
        for declarator in self.init_declarator_list:
            decl = declarator.decl()
            specifiers_decl = self.declaration_specifiers.decl()
            for key, value in specifiers_decl[0].items():
                attr_item = {key: value}
                decl = decl.setattrs(**attr_item)
            declaration.append(decl)

        return declaration

class Declarator(Node):
    def __init__(self, lineno, direct_declarator, pointer):
        super().__init__(lineno)
        self.direct_declarator = direct_declarator
        self.pointer = pointer

    def decl(self):
        """
        Logic for pointer and return_type attributes.

        Examples of what is returned.
            int f(); => 'f' (name) is a function (ctx[-1]) that returns an 'int' (type)
              {'ctx': ['id', 'function'],
               'initializer': [],
               'name': 'f',
               'parameters': [],
               'pointer': [],
               'return_type': [],
               'storage_class': 'auto',
               'type': 'int'}

            int *fip(); => 'fip' (name) is a function (ctx[-1]) that returns a pointer (return_type) to 'int' (type)
              {'ctx': ['id', 'function'],
               'initializer': [],
               'name': 'fip',
               'parameters': [],
               'pointer': [],
               'return_type': ['*'],
               'storage_class': 'auto',
               'type': 'int'}

            int (*pfi) () => 'pfi' (name) is a pointer (pointer) to a function (ctx[-1]) that returns an 'int' (type)
              {'ctx': ['id', 'declarator', 'function'],
               'initializer': [],
               'name': 'pfi',
               'parameters': [],
               'pointer': ['*'],
               'return_type': [],
               'storage_class': 'auto',
               'type': 'int'}

            int *(*pfpi) (); => 'pfpi' (name) is a pointer (pointer) to a function (ctx[-1])
                                that returns a pointer (return_type) to 'int' (type)
              {'ctx': ['id', 'declarator', 'function'],
               'initializer': [],
               'name': 'pfpi',
               'parameters': [],
               'pointer': ['*'],
               'return_type': ['*'],
               'storage_class': 'auto',
               'type': 'int'}
        """

        decl = self.direct_declarator.decl()

        if decl.ctx[-1] == 'function': # We have a declaration of a function, it can return simple type or a pointer
            return_type = self.pointer.get() if self.pointer is not None else []
            decl.setattrs(pointer=[])
        else:
            return_type = None
            decl.setattrs(pointer=self.pointer.get() if self.pointer is not None else [])

        if return_type is not None:
            return decl.setattrs(return_type=return_type)
        else:
            return decl


class DeclarationSpecifiers(Node):
    def __init__(self, lineno, storage_class=None, type=None):
        super().__init__(lineno)
        self.storage_class = storage_class if storage_class is not None else 'auto'
        self.type = TypeSpecifier(lineno, 'int', 'INT') if type is None else type

    def decl(self):
        decl = self.type.decl()
        return [decl.setattrs(storage_class=self.storage_class)]

class InitDeclarator(Node):
    def __init__(self, lineno, declarator, initializer):
        super().__init__(lineno)
        self.declarator = declarator
        self.initializer = initializer

    def decl(self):
        decl = self.declarator.decl()
        if self.initializer is not None:
            decl.setattrs(initializer=self.initializer.decl())
        return decl


class DirectDeclarator(Node):
    _op = {'[': 'array', '(': 'function', 'id': 'id', 'declarator': 'declarator'}

    def __init__(self, lineno, op, id=None, declarator=None, direct_declarator=None,
                 constant_expression=None, identifier_list=None):
        super().__init__(lineno)
        self.id = id
        self.declarator = declarator
        self.direct_declarator = direct_declarator
        self.constant_expression = constant_expression
        self.identifier_list = identifier_list
        self._ctx = self._op[op]

    def decl(self):
        ctx = self._ctx

        if ctx == 'id':
            # This is where we create a declaration object that is cascaded upwards with added attriutes
            # The object is used as an interface to the symbol tables.
            return CCconf.CCDecl().setattrs(ctx=[ctx], name=self.id, lineno=self._lineno)

        if ctx == 'function':
            decl = self.direct_declarator.decl()
            parameters = self.identifier_list.get() if self.identifier_list is not None else []
            return decl.setattrs(ctx=[ctx], parameters=parameters, initializer=[])

        if ctx == 'declarator':
            decl = self.declarator.decl()
            return decl.settattrs(ctx=[ctx], intializer=[])

        if ctx == 'array':
            decl = self.direct_declarator.decl()
            if self.constant_expression is not None:
                expr = self.constant_expression.eval()
                subscript = decl.subscript + [expr] if decl.hasattr('subscript') else [expr]
                return decl.setattrs(ctx=[ctx], subscript=subscript)
            else:
                return decl.setattrs(ctx=[ctx])

class StructSpecifier(Node):
    def __init__(self, lineno, id=None, struct_declaration_list=None):
        super().__init__(lineno)
        self.id = id
        self.struct_declaration_list = struct_declaration_list

    def decl(self):
        decl_list = []
        if self.struct_declaration_list:
            for d in self.struct_declaration_list:
                decl = d.decl()
                for elem in decl:
                    decl_list.append(elem)

        id = '' if self.id is None else self.id
        return CCconf.CCDecl().setattrs(struct_tag=id, declaration_list=decl_list)

class StructDeclaration(Node):
    def __init__(self, lineno, specifier_qualifiers, declarators):
        super().__init__(lineno)
        self.declarators = declarators
        self.specifier_qualifiers = specifier_qualifiers

    def decl(self):
        """
        Note that self.specifier_qualifiers is a list, but have only one element.
        This means that we retrieve the list through get() and use the only element (index: 0), then calls its decl()
        which returns a CCDecl instance.

        self.declarators can include more than one element, so we need to loop this as a list, calling
        each elements decl(). The return value is added to decl-list.

        At then end we loop the decl-list and merge each element with the spec-dictionary

        An example of a declaration causing self.declarators to have more than one element is:
            struct a { int a, b };
        """

        decls = []
        spec = self.specifier_qualifiers.get()[0].decl()

        for d in self.declarators:
            decls.append(d.decl())

        for i in range(len(decls)):
            dict_items = decls[i].__dict__ | spec.__dict__
            for key, value in dict_items.items():
                attr = {key: value}
                decls[i] = decls[i].setattrs(**attr)

        return decls

class ParameterDeclaration(Node):
    def __init__(self, lineno, declaration_specifiers, declarator=None):
        super().__init__(lineno)
        self.declaration_specifiers = declaration_specifiers
        self.declarator = declarator

class Initializer(Node):
    def __init__(self, lineno, constant=None, constant_expression_list=None):
        super().__init__(lineno)
        self.constant = constant
        self.constant_expression_list = constant_expression_list

    def decl(self):
        if self.constant is not None:
            return self.constant

        if self.constant_expression_list:
            c_expr = []
            for c in self.constant_expression_list:
                c_expr.append(c.eval())

            return c_expr

        return None

class Pointer(Node):
    def __init__(self, lineno, pointer):
        super().__init__(lineno)
        self.pointer = pointer

    def eval(self):
        return self.pointer

class ParameterTypeList(Node):
    def __init__(self, lineno, parameter_list):
        super().__init__(lineno)
        self.parameter_list = parameter_list

class TypeSpecifier(Node):
    def __init__(self, lineno, type_name, type):
        super().__init__(lineno)
        self.type_name = 'int' if type_name is None else type_name
        self._ctx = type

    def decl(self):
        if self._ctx == 'struct_specifier':
            decl = CCconf.CCDecl().setattrs(ctx=[self._ctx])
            for key, value in self.type_name.decl().items():
                attr = {key: value}
                decl.setattrs(**attr)

            return  decl

        return CCconf.CCDecl().setattrs(type=self.type_name)

class TypeName(Node):
    def __init__(self, lineno, specifier_qualifier_list, pointer=None):
        super().__init__(lineno)
        self.specifier_qualifier_list = specifier_qualifier_list
        self.pointer = pointer

"""
class Statement(Node):
    def __init__(self, lineno, stmt=None):
        super().__init__(lineno)
        self.stmt = stmt
"""

class LabeledStatement(Node):
    def __init__(self, lineno, label, constant_expression, statement):
        super().__init__(lineno)
        self.label = label
        self.constant_expression = constant_expression
        self.statement = statement

    def stmt(self):
        return f"{self.label} {self.statement.stmt()} {self.constant_expression}"

class CompoundStatement(Node):
    def __init__(self, lineno, declaration_list=None, statement_list=None):
        super().__init__(lineno)
        self.declaration_list = declaration_list
        self.statement_list = statement_list

    def decl(self):
        decl = []
        if self.declaration_list:
            for d in self.declaration_list:
                decl.append(d.decl())
            return decl
        else:
            return None

    def stmt(self):
        if self.statement_list:
            statements = []
            for stmt in self.statement_list:
                statements += [stmt.stmt()]
            return statements
        else:
            return None

class SelectionStatement(Node):
    def __init__(self, lineno, op, expression, statement, else_statement=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression
        self.statement = statement
        self.else_statement = else_statement

    def stmt(self):
        if self.else_statement is not None:
            else_statement = self.else_statement.stmt()
        else:
            else_statement = ''
        return f"{self.op} {self.expression} {self.statement.stmt()} {else_statement}"

class IterationStatement(Node):
    def __init__(self, lineno, op, statement, expression, expression_statement1=None, expression_statement2=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression
        self.expression_statement1 = expression_statement1
        self.expression_statement2 = expression_statement2
        self.statement = statement

    def stmt(self):
        return f"{self.op} {self.expression_statement1} {self.expression_statement2} {self.statement.stmt()}"

class JumpStatement(Node):
    def __init__(self, lineno, op, expression=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression

    def stmt(self):
        return f"{self.op} {self.expression}"

class ExternalDeclaration(Node):
    def __init__(self, lineno, declaration, type):
        super().__init__(lineno)
        self.declaration = declaration
        self._ctx = type

    def decl(self):
        if self.declaration:
            return self.declaration.decl()
        return None

    def stmt(self):
        if self.declaration:
            if self._ctx == 'function_definition':
                return self.declaration.stmt()
        return None

class FunctionDefinition(Node):
    """
    declaration_specifiers: function returning... (type)
    declarator: function name and formal parameters
    declaration_list: formal parameters (name and type)
    compound_statement: list of statements in function body (including local variable)
    """

    def __init__(self, lineno, declarator, declaration_specifiers, declaration_list, compound_statement):
        super().__init__(lineno)
        if declaration_specifiers is None:
            declaration_specifiers = TypeSpecifier(lineno, 'int', 'INT')
        self.declarator = declarator
        self.declaration_specifiers = declaration_specifiers
        self.declaration_list = declaration_list
        self.compound_statement = compound_statement

    def decl(self):
        """
        Note, the names of formal parameters to a function are located in self.declarator to this function.
        Then, the declaration (type) of these parameters are in self.declaration_list.
        If a formal parameter are not declared in self.declaration_list the type are implicitly assumed to be int.
        
        Example: 
            abc(x, y, z) <-- function abc with 3 formal parameters: x, y, z located in self.declarator
            char *y[];   <-- located in self.declaration_list, type is pointer to array of characters
            float z;     <-- located in self.declaration_list
            
            x is not declared, hence type is assumed to be int, x is NOT in self.declaration_list but in self.declarator

        Below is somewhat :-) complicated, perhaps overly...
        - First we get the declarator declaration-object (decl variable)
        - Then we loop the parameters in decl, these are the formal parameters (x, y, z above), and add them to a
          temporary list (parameters). For each parameter, we create a new declaration object (decl_obj) and
          set the attributes (par_dict -> **par_dict)
        - Then we loop declared parameters (y, z above) and add them to declared_parameters list, if there are any.
          For each element in declaration_list, we get the declaration (decl_pars.decl()).
        - Now we have 2 lists that we compare by the name of parameters. The parameter list (formal parameters) should
          always be >= then declared_parameters. If there is a match by name (elem.name == par.name), we copy
          elem into parameters list (parameters[ind] = elem). Thus, the list are merged, and parmeters have
          all information.
        - As a final step, we update the decl-object with the parameters list. However, the attribute 'parameters'
          might already exist in decl object, so we remove this first (decl.delattr('parameters')).
          delattr implementation will first check if that attribute exists, then remove it.
          After that we set attributes in decl object by calling setattr, noting that the implementation of
          setattr will add lists together if an attribute of list type exists in decl. Therefore, we need
          to remove the parameters-attribute first. We also add the return_type attribute and return decl-object.

        """

        decl = self.declarator.decl()

        # Create a list of parameters with standard/implicit type.
        parameters = []
        for pname in decl.parameters:
            decl_obj = CCconf.CCDecl()
            par_dict = {'type': 'int', 'storage_class': 'auto', 'ctx': ['id'], 'name': pname, 'pointer': []}
            parameters.append(decl_obj.setattrs(**par_dict))

        # Now loop through all declared parameters, if any
        declared_parameters = []
        if self.declaration_list is not None:
            for decl_pars in self.declaration_list:
                declared_parameters.append(decl_pars.decl())

        if len(declared_parameters) > len(parameters):
            raise CCError(f'{self.__class__.__name__}: '
                          f'declared_parameters={len(declared_parameters)} > parameters={len(parameters)} '
                          f'({self._lineno})')
        # Merge declared parameters into parameters list
        for par in parameters:
            for row in declared_parameters:
                for elem in row:
                    if elem.name == par.name:
                        ind = parameters.index(par)
                        parameters[ind] = elem

        decl.delattr('parameters')
        return decl.setattrs(parameters=parameters, return_type=self.declaration_specifiers.decl())

    def stmt(self):
        return self.compound_statement.stmt()

class TranslationUnit(Node):
    def __init__(self, lineno):
        super().__init__(lineno)
        self.external_declarations = []

    def add(self, decl):
        self.external_declarations.append(decl)

    def decl(self):
        if self.external_declarations:
            decl = []
            for d in self.external_declarations:
                declaration = d.decl()
                decl.append(declaration)
                CCconf.compiler.symbols.add(declaration)
            return decl
        else:
            return None

    def stmt(self):
        if self.external_declarations:
            stmts = []
            for s in self.external_declarations:
                statement = s.stmt()
                if statement:
                    stmts.append(statement)
            return stmts
        else:
            return None

class Program:
    def __init__(self):
        self.translation_unit = TranslationUnit(lineno=1)
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
        # filter out keys with '_' prefix or values equal 'ASTList' and None values
        flt_hard = ''

        if flt_hard:
            flt=lambda n: {k: v for k, v in n.__dict__.items()
                           if not (k.startswith('_') or v == 'ASTList') and v is not None}
        else:
            flt=lambda n: {k: v for k, v in n.__dict__.items() if v != 'ASTList' and v is not None}


        return json.dumps({'translation_unit': self.translation_unit}, default=flt)

    def json(self):
        return json.loads(str(self))

    def print(self):
        pprint.pprint(self.json(), width=80, compact=True)

    def decl(self):
        if self.translation_unit:
            return self.translation_unit.decl()

    def stmt(self):
        if self.translation_unit:
            return self.translation_unit.stmt()