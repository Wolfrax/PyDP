# This is the implementation of the abstract syntax tree (AST) created during parsing (CCParser)

import pprint
import json
from src.CCconf import compiler, CCDecl
from CCError import CCError
import logging

#from cc.CCSymbols import CCSymbols

#from llvmlite.binding import StorageClass

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, lineno):
        self._lineno = lineno
        name = self.__class__.__name__
        self._node = None if name == 'ASTList' else name
        self.compiler = compiler

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
                          f'PrimaryExpression: constant and expression cannot be None [{self._lineno}]')

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
                              f'PrimaryExpression: unsupported constant type: {constant} [{self._lineno}]')
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
    _op = {'[': 'subscript', '(': 'func', '.': 'struct', '->': 'pointer', '++': 'incr', '--': 'decr'}

    def __init__(self, lineno, op, postfix_expression=None, expression=None, argument_expression_list=None, id=None):
        super().__init__(lineno)

        if op in self._op:
            self._ctx = self._op[op]
        else:
            raise CCError(f'{self.__class__.__name__}: '
                          f'Postfix expression: Unknown operator {op} [{self._lineno}]')

        self.postfix_expression = postfix_expression  # Should be PrimaryExpression: id
        self.expression = expression  # Used in subscript, such as a[b+1], expression == b+1
        self.argument_expression_list = argument_expression_list  # Used for functions calls, actual parameters
        self.id = id  # Used for struct members or pointers, eg a.ID or a->ID

    def eval(self):
        #if self._ctx == 'subscript': # array postfix_expression[expression]

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
    def __init__(self, lineno, op, expression=None, type_name=None):
        super().__init__(lineno)
        self.op = op
        self.expression = expression
        self.type_name = type_name # type_name == 'pointer' if op == '&'???

    def eval(self):
        sym = self.expression.eval()
        ref = self.compiler.symbols.get_ref(sym)
        val = self.compiler.interpreter.memory.read(ref.mempos, ref.type_name)

        if self.op == '++':
            val += 1

        self.compiler.interpreter.memory.update(ref.mempos, val, ref.type_name)
        return sym

    def stmt(self):
        return f"{self.op} {self.type_name} {self.expression}"

class BinOpExpression(Node):
    def __init__(self, lineno, op, expr_l, expr_r):
        super().__init__(lineno)
        self.expr_l = expr_l
        self.expr_r = expr_r
        self.op = op

    def get_val(self, op):
        val = None
        ref = self.compiler.symbols.get_ref(op)

        if ref is None:  # Constant
            val = self.compiler.symbols.get(op)
        else: # local parameter/variable or externally declared variable
            mempos = ref.mempos
            if ref.pointer:
                for p in ref.pointer:
                    ref = self.compiler.interpreter.memory.read(mempos, 'pointer')
                    val = self.compiler.interpreter.memory.read(ref, ref.type_name)
                    mempos = val
            else:
                val = self.compiler.interpreter.memory.read(mempos, ref.type_name)
        return val

    def eval(self):
        left = self.expr_l.eval()
        right = self.expr_r.eval()

        logger.debug(f'{self.__class__.__name__}: {left} {self.op} {right}')

        if self.op == '=': # assignment
            left_ref = self.compiler.symbols.get_ref(left)
            if isinstance(right, str):
                right = self.get_val(right)

            self.compiler.interpreter.memory.update(left_ref.mempos, right, left_ref.type_name)

            return left
        else:
            if isinstance(right, str):
                right = self.get_val(right)

            if isinstance(left, str):
                left = self.get_val(left)

            """
            Note, from C reference manual:
                If both operands are int or char, the result is int; if one is int or char and one float or double,
                the former is converted to double and the result is double; if both are float or double, the result
                is double. No other combinations are allowed.
            Currently, we are not explicitly checking this => following python conversions.
            """
            if self.op == '+':
                return left + right
            elif self.op == '-':
                return left - right
            elif self.op == '*':
                return left * right
            elif self.op == '/':
                if right == 0:
                    raise CCError(f"{self.__class__.__name__}: division by zero [{self._lineno}]")

                if isinstance(left, int) and isinstance(right, int):
                    return left // right
                else:
                    return left / right
            elif self.op == '<<':
                return left << right
            elif self.op == '>>':
                return left >> right
            elif self.op == '|':
                return left | right
            elif self.op == '<':
                return left < right
            elif self.op == '>':
                return left > right
            elif self.op == '<=':
                return left <= right
            elif self.op == '>=':
                return left >= right
            elif self.op == '%':
                # Only int should be allowed, but here float is ok. Reminder will have same sign as dividend
                return left % right
            else:
                raise CCError(f'{self.__class__.__name__}: unsupported operator {self.op} [{self._lineno}]')

    def stmt(self):
        return self

class ConditionalExpression(Node):
    def __init__(self, lineno, expr1, expr2, expr3):
        super().__init__(lineno)
        # expr1 ? expr2 : expr3
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3

class Declaration(Node):
    """
    A Declaration node specifies storage class and type name and has a list of declarators.
    Declarators have information on variable name and - depending on type - additional information such as subscripts.
    Declarators is a list, such as int, a, b; list will include a and b.

    Example: char cvtab[4][4];
    self.declaration_specifiers will have information about storage_class (auto) and type_name (char)
    self.init_declarator_list will have information about name (cvtab), and subscripts ([4][4])
    """
    def __init__(self, lineno, decl_specifier, initializer):
        super().__init__(lineno)
        self.declaration_specifiers = decl_specifier
        self.init_declarator_list = initializer

    def decl(self):
        declaration = []
        specifiers_dict = self.declaration_specifiers.decl().__dict__

        for declarator in self.init_declarator_list:
            decl = specifiers_dict | declarator.decl().__dict__
            if 'ctx' in specifiers_dict:
                decl['ctx'] += specifiers_dict['ctx']
            decl_obj = CCDecl().setattr(**decl)
            declaration.append(decl_obj)

        return declaration

class Declarator(Node):
    def __init__(self, lineno, direct_declarator, pointer):
        super().__init__(lineno)
        self.direct_declarator = direct_declarator
        self.pointer = pointer

    def decl(self):
        """
        Logic for pointer and return_type attributes.

        Examples of what is returned in a declaration object (noted as dict below)
            int f(); => 'f' (name) is a function (ctx[-1]) that returns an 'int' (return_type)
              {'ctx': ['id', 'function'],
               'name': 'f',
               'parameters': [],
               'pointer': [],
               'return_type': [],
               'storage_class': 'auto',
               'type_name': 'int'}

            int *fip(); => 'fip' (name) is a function (ctx[-1]) that returns a pointer (return_type) to 'int' (type)
              {'ctx': ['id', 'function'],
               'name': 'fip',
               'parameters': [],
               'pointer': [],
               'return_type': ['*'],
               'storage_class': 'auto',
               'type_name': 'int'}

            int (*pfi) () => 'pfi' (name) is a pointer (pointer) to a function (ctx[-1]) that returns an 'int' (type)
              {'ctx': ['id', 'declarator', 'function'],
               'name': 'pfi',
               'parameters': [],
               'pointer': ['*'],
               'return_type': [],
               'storage_class': 'auto',
               'type_name': 'int'}

            int *(*pfpi) (); => 'pfpi' (name) is a pointer (pointer) to a function (ctx[-1])
                                that returns a pointer (return_type) to 'int' (type)
              {'ctx': ['id', 'declarator', 'function'],
               'name': 'pfpi',
               'parameters': [],
               'pointer': ['*'],
               'return_type': ['*'],
               'storage_class': 'auto',
               'type_name': 'int'}
        """

        decl = self.direct_declarator.decl()

        if decl.ctx[-1] == 'function': # We have a declaration of a function, it can return simple type or a pointer
            return_type = self.pointer.get() if self.pointer is not None else []
            decl.setattr(pointer=[])
        else:
            return_type = None
            decl.setattr(pointer=self.pointer.get() if self.pointer is not None else [])

        if return_type is not None:
            return decl.setattr(return_type=return_type)
        else:
            return decl


class DeclarationSpecifiers(Node):
    def __init__(self, lineno, storage_class=None, type=None):
        super().__init__(lineno)
        self.storage_class = storage_class if storage_class is not None else 'auto'
        self.type_name = TypeSpecifier(lineno, 'int', 'INT') if type is None else type

    def decl(self):
        decl = self.type_name.decl()
        return decl.setattr(storage_class=self.storage_class)

class InitDeclarator(Node):
    def __init__(self, lineno, declarator, initializer):
        super().__init__(lineno)
        self.declarator = declarator
        self.initializer = initializer

    def decl(self):
        decl = self.declarator.decl()

        if self.initializer is not None:
            decl.setattr(initializer=self.initializer.decl())

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
        self.subscript = []

    def decl(self):
        ctx = self._ctx

        if ctx == 'id':
            return CCDecl().setattr(ctx=[ctx], name=self.id, lineno=self._lineno)

        if ctx == 'function':
            decl = self.direct_declarator.decl()
            parameters = self.identifier_list.get() if self.identifier_list is not None else []
            return decl.setattr(ctx=decl.ctx + [ctx], parameters=parameters)

        if ctx == 'declarator':
            decl = self.declarator.decl()
            return decl.setattr(ctx=decl.ctx + [ctx])

        if ctx == 'array':
            decl = self.direct_declarator.decl()
            if self.constant_expression is not None:
                expr = self.constant_expression.eval()
                expr = self.compiler.symbols.get_constant(expr) if isinstance(expr, str) else expr
                if not expr:
                    raise CCError(f'{self.__class__.__name__}: '
                                  f'expression = {expr} not found in symbol table '
                                  f'[{self._lineno}]')
                subscript = decl.subscript + [expr] if decl.hasattr('subscript') else [expr]
                return decl.setattr(ctx=decl.ctx + [ctx], subscript=subscript)
            else:
                return decl.setattr(ctx=decl.ctx + [ctx])

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
        return CCDecl().setattr(struct_tag=id, declaration_list=decl_list)

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
            decls[i] = decls[i].setattr(**(decls[i].__dict__ | spec.__dict__))

        return decls

class Initializer(Node):
    def __init__(self, lineno, constant=None, constant_expression_list=None):
        super().__init__(lineno)
        """
        - int a 0; => constant is 0
        - int *a { b }; => constant_expression_list is [PrimaryExpression.value = 'b'], 1-element list
        - int *a &b; => constant_expression_list is [PrimaryExpression.value = 'b'], 1-element list
        - int a[] { 0, 1 }; => constant_expression_list is [PrimaryExpression.value = '0'. ...=value 1], 2-element list
        - int *a &b[1]; => constant_expression_list is [PostfixExpression], 1-element list
          'a' is a pointer that is initialized to the address of the second element of the array b
          FIXME: PostfixExpression.eval() not implemented!
        - char *a[] {"abc", "def"};
        """
        if isinstance(constant, str):
            constant = constant.replace('"', '')  # "ABC" => ABC

        self.constant = constant
        self.constant_expression_list = constant_expression_list

    def decl(self):
        # FIXME, self.constant_expression_list (& operator)
        if self.constant is not None:
            return self.constant

        if self.constant_expression_list:
            # Here we should check if the c_expr is a string, and if so - is it a constant with a value?
            c_expr = []
            for c in self.constant_expression_list:
                val = c.eval()
                if isinstance(val, str) and (val[0] != '"' and val[-1] != '"'):
                    """
                    If val is a string, and starts/ends with "-character, it is simply appended as value to c_expr,
                    but remove "-characters.
                    
                    int a { 'b' };
                    Initialize a with ord(b)
                    
                    int *a { b }; or int *a &b;
                    initializer element (b) is a symbol, that can be either:
                    - a symbolic constant: #define b 1 ==> b is symbolic constant with value 1
                      symbols.get will search first in #define constants, and if found return the value
                    - a variable that must be declared before this declaration.
                      In this case, 'b' is a reference that 'a' should be initialized with.
                      Thus, we need to get the mempos for b.
                      Even if b initialized (int b 1;), the symbol table entry for b, will not have the 
                      'value' attribute, thus get() will return None. The initializer 1 is written into memory. 
                    """
                    if val[0] == "'" and val[2] == "'" and val[1].isalpha():  # int a { 'b' };
                        val = ord(val[1])
                    else:
                        name = val
                        val = self.compiler.symbols.get_constant(name)
                        if val is None:
                            val = self.compiler.symbols.get_mempos(name)
                        if val is None:
                            raise CCError(f'{self.__class__.__name__}: '
                                          f'name = {name} not found in symbol table '
                                          f'[{self._lineno}]')

                if isinstance(val, str) and (val[0] == '"' and val[-1] == '"'):
                    val = val[1:-1]  # { "ABC" } => { ABC }

                c_expr.append(val)

            return c_expr

        return None

class Pointer(Node):
    def __init__(self, lineno, pointer):
        super().__init__(lineno)
        self.pointer = pointer

    def eval(self):
        return self.pointer

class TypeSpecifier(Node):
    def __init__(self, lineno, type_name, type):
        super().__init__(lineno)
        self.type_name = 'int' if type_name is None else type_name
        self._ctx = type

    def decl(self):
        if self._ctx == 'struct_specifier':
            return CCDecl().setattr(ctx=[self._ctx], **self.type_name.decl().__dict__)

        return CCDecl().setattr(type_name=self.type_name)

class TypeName(Node):
    def __init__(self, lineno, specifier_qualifier_list, pointer=None):
        super().__init__(lineno)
        self.specifier_qualifier_list = specifier_qualifier_list
        self.pointer = pointer

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

    def eval(self):
        for stmt in self.statement_list:
            stmt.eval()

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

    def eval(self):
        if self.op == 'if':
            cond = self.expression.eval()
            if cond:
                self.statement.eval()
            else:
                self.else_statement.eval()
        pass

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

    def eval(self):
        if self.op == 'while':
            cond = self.expression.eval()
            if cond:
                self.statement.eval()

        pass

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
        - As a final step, we update the decl-object with the parameters list.
        """

        decl = self.declarator.decl()

        # Create a list of parameters with standard/implicit type.
        parameters = []
        for pname in decl.parameters:
            parameters.append(CCDecl().
            setattr(**{'type_name': 'int', 'storage_class': 'auto', 'ctx': ['id'], 'name': pname, 'pointer': []}))

        # Now loop through all declared parameters, if any
        declared_parameters = []
        if self.declaration_list is not None:
            for decl_pars in self.declaration_list:
                dp = decl_pars.decl()
                if dp[0].ctx in ['array', 'struct_specifier'] and not dp[0].pointer:
                    raise CCError(f"Illegal declaration {dp[0].name} [{dp[0].lineno}]")

                declared_parameters.append(dp)

        if len(declared_parameters) > len(parameters):
            raise CCError(f'{self.__class__.__name__}: '
                          f'declared_parameters={len(declared_parameters)} > parameters={len(parameters)} '
                          f'[{self._lineno}]')

        # Merge declared parameters into parameters list
        for par in parameters:
            for row in declared_parameters:
                for elem in row:
                    if elem.name == par.name:
                        ind = parameters.index(par)
                        parameters[ind] = elem

        return decl.setattr(parameters=parameters, return_type=self.declaration_specifiers.decl(),
                            statements=self.compound_statement)

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
                if isinstance(declaration, CCDecl):
                    decl.append(declaration)
                else:
                    decl += declaration
                self.compiler.symbols.add(declaration)
            logger.debug(f"Allocated {self.compiler.symbols.memory.sp} bytes for external declarations")
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