
Declarations

Declarations can be of different types:
1. Declaration of simple variables with a basic type, such as: int a;
2. Declaration of pointers, such as: int *a;
3. Declaration of arrays, such as: int a[10];

   Note that arrays variables can have a rank, for example: int a[10][10], which has rank 2

4. Declaration of a structure, such as struct a {int x; char y};
5. Declaration of functions, such as: int a(x, y);
6. Declaration of a pointer to a function, such as: int (*a);

Of course, above declaration types can be mixed, for example: struct a {int x, char y} a[10];
An array of rank 1 with 10 elements of [x, y].

A declaration can have several attributes:
* Name: always present
* Type: Basic types (int, char, float, double), struct type. If type is missing it is implicitly int.
* Storage class: auto, static, extern, register. If storage class is missing it is assumed to be auto
* Initializer, might be or not be present
* Pointer prefix: One or several * as a prefix to the name (e.g int **a, a pointer to a pointer to int)
* Array suffix: One or several [] as a suffix to the name (e.g. int a[10][10], a 10 by 10 matrix). An array has a rank.
  If the parenthesis has no constant expression, it is assumed to be one, thus a[] means an array with 
  one element (of type int)

It is possible to have a list of declared variables, such as int a, b, c; The variables a, b and c are int's.

A declaration can have different scope:
* External to current translation unit, indicated by storage class extern.
* Within current translation unit, global to all functions within this unit
* As a parameter to a function, note additional comments below
* As a local variable to a function, same scope as for a parameter

Function declaration have a return type (if not stated, return type is int), a function name and
formal parameters. Parameters are stated in the function declaration but are declared after the function decaration
and before the function body.
Example:
    char abc(x, y)
    char x;
The funcion abc returns a char, has 2 formal parameters, one that is declared as a char. The second parameter are
implicitly declared as an int.

Note that the declaration of parameters can include pointers and arrays, such as
    main(argc, argv)
    char *argv[];

argc is implicitly declared as int, the second parameter (argv) is declared as a pointer to an array of char.

---

When parsing declarations a complex structure of node objects of different types are created in the
abstract syntax tree.

The following AST object types are created for declarations:
* DeclarationSpecifiers: has the attributes storage class and/or type
* Declaration: has a DeclarationSpecifier as an attribute and used if there is an initializer
* Declarator: a Declarator object refers to a DirectDeclarator object and has the attribute pointer if existent,
otherwise pointer attribute is None.

Thus, an "int a" declaration creates a DirectDeclarator object for the variable a, then a Declarator object is created
that refer to the DirectDeclarator object.

=> a Declarator object only has information if it is a pointer or not in the declaration and refers to a DirectDeclarator

* DirectDeclarator: created when there is a declaration of an 1) identifier 2) array 3) function 4) pointer to function

  * A DirectDeclarator for an array includes brackets and possible expression within brackets. 
  * A DirectDeclarator for a function includes the list of parameters to the function (but not their declarations)

=> a DirectDeclarator is 'basic'

A Declarator tells if the DirectDeclarator is a pointer or not. 
A DeclarationSpecifier tells the type and/or storage class of a DirectDeclarator.

---

A DirectDeclarator object is referenced by Declarator, DirectDeclarator:

1. Declarator.decl()
   
   Declarator object refer to a DirectDeclarator object with a possible pointer. 
   The DirectDeclarator ctx can be 'id', 'array', 'function', 'declarator'
   
```
attr = self.direct_declarator.decl()
ctx = attr[0]

if ctx == 'id':
  name = attr[1]
  return ctx, name, self.pointer
elif ctx = 'array':
  direct_declarator = attr[1]
  array_name = direct_declarator.decl()
  return ctx, array_name, self.pointer, self.constant_expression
elif ctx = 'function':
  direct_declarator = attr[1]
  function_name = direct_declarator.decl()
  return ctx, function_name, self.pointer
elif ctx = 'declarator':
  declarator = attr[1]
  return ctx, declarator
else: # error...unknown ctx
```

2. DirectDeclarator.decl()
```
ctx = self._ctx
if ctx == 'id':
   return ctx, self.id
elif ctx == 'array':
   return ctx, self.direct_declarator.decl(), self.constant_expression
elif ctx == 'function':
   return ctx, self.direct_declarator.decl(), self.identifier_list
elif ctx == 'declarator':
   return ctx, self.declarator.decl()
else:  # error...unknown ctx
```

A Declarator object is referenced by an InitDeclarator, DirectDeclarator (when "(declarator)"), FunctionDefinition.

1. InitDeclarator.decl()
```
attr = self.declarator.decl()
ctx = attr[0]

if ctx == 'id':
   name = attr[1]
elif ctx == 'array':
   array_name = attr[1]
   constant_expression = attr[2]
elif ctx == 'function':
   function_name = attr[1]
   identifiers = attr[2]
elif ctx == 'declarator':
   declarator = attr[1]
else:  # error...unknown ctx
```
2. DirectDeclarator.decl(), see above
3. FunctionDefinition

---
int a;
Symbol table: {'a': {'pointer': None, 'pointer to': None, 'storage class': None, 'type': 'int', 'Initializer': None}}
```
TranslationUnit:
    ExternalDeclaration:  self.declaration.decl()=(ctx='id', type='int', storage_class=None, name='a', pointer=None, initializer=None) => SymbolTable
        Declaration: return (ctx='id', type_specifier.decl()='int', storage_class=None, init_declarator_list[:].decl()[1]=('id', 'a', None, None), .decl()[2]=('id', 'a', None, None), .decl()[3]=('id', 'a', None, None))
            Declarator: return (ctx='id', direct_declarator.decl()[1]=name='a', pointer=None, intializer=None)
                DirectDeclarator(ctx='id'): return (ctx='id', self.id='a')
            TypeSpecifier("int")
```
int a 0;
Symbol table: {'a': {'pointer': None, 'pointer to': None, 'storage class': None, 'type': 'int', 'Initializer': None}}
```
TranslationUnit:
    ExternalDeclaration: self.declaration.decl()=(ctx='id', type='int', storage_class=None, name='a', pointer=None, initializer=0) => SymbolTable
        Declaration: return (ctx='id', type_specifier.decl()='int', storage_class=None, init_declarator_list[:].decl()[1]=('id, 'a', None, 0), .decl()[2]=('id', 'a', None, 0), .decl()[3]=('id', 'a', None, 0))
            InitDeclarator: return (ctx='id', declarator.decl()[1]=name='a', pointer=None, Initializer.decl()[0]=(0, None))
                Declarator: return (ctx='id', direct_declarator.decl()[1]='a', pointer=None)
                    DirectDeclarator(ctx='id'): return (ctx='id', self.id='a')
                Initializer: return (self.constant=0, self.constant_expression=None)
            TypeSpecifier("int")
```

int (*a)()
Symbol table: {'a': {'pointer': '*', 'pointer to': 'function', 'storage class': None, 'type': 'int', 'parameters': None}}
'a' is a 'pointer' that points to 'function', (return) type (of function) is int, it has no parameters
```
TranslationUnit: 
    ExternalDeclaration: self.declaration.decl()=('int', None, ('function, 'declarator', 'abc1', ['*'], None), None)
        Declaration: return (ctx='function', type_specifier.decl()='int', storage_class=None, init_declarator_list[:].decl()=('function', 'declarator', 'a', ['*'], None), initializer=None)
            Declarator: return (ctx='function', attr[1][0]=declarator='declarator', attr[1][1]=function_name='a'), attr[1][2]=[*], attr[2]=parameters=None)
                DirectDeclarator(ctx='function'): return (ctx='function', self.direct_declarator.decl()[1]=('declarator', 'a', [*]), self.identifier_list=None) 
                    DirectDeclarator(ctx='declarator'): return (ctx='declarator', declarator.decl()[1]=('id', 'a', ['*']), .decl()[2]=('id', 'a', ['*']), .decl()[3]=('id', 'a', ['*']))
                        Declarator: return (ctx='id', direct_declarator.decl()[1]=('id', a'), pointers=['*'])
                            DirectDeclarator(ctx='id'): return (ctx='id', self.id='a')
        TypeSpecifier("int")
```

DirectDeclarator returns (ctx: 'id', 'function', 'array', 'declarator')

```
if ctx == 'id': 
    return {'ctx': 'id', 'name': 'a'(self.id)} 

if ctx == 'function'
    attr = self.declarator.decl()
    return {'ctx': 'function', 'name': 'a' (attr['name'], 'parameters': None/['a', 'b'](self.identifier_list)}
    
if ctx == 'declarator' (DirectDeclarator -> Declarator -> DirectDeclarator)
    attr = self.declarator.decl()
    return {'ctx': 'declarator', 'name': 'a' (attr[1]), 'pointers': None/['*'], 'initializer': None}

if ctx == 'array'
```
Declarator returns
```
attr = self.direct_declarator.decl()
ctx = attr[0]
{'ctx': ctx, 
 'name': attr[1] ('a'), 
 'pointers': self.pointer (None/['*']), 
 'initializer': None (always),
 'parameters': attr[2] if ctx == 'function' else None}
```

Declaration returns
```
attr = self.init_declarator_list[].decl()
type = type_specifier.decl() ('int')
{'ctx': attr[0}, 
 'type': type, 
 'storage_class': self.storage_class,
 'pointer to': attr[0] if attr[1] == 'declarator' else type
 'pointer': attr[3] (['*']),
 'parameters': attr[4],
 'initializer': attr[...]
 }
```

---

Declaration object is only used when there is a list of initializers for the declared variable
Example: int a 0; 
    A Declaration object is created with attribute initializer of type list
    The attribute initializer has one element of type InitDeclarator, which in turn 
    refers to a Declarator object (see paragraph below) which in turn refers to direct_declarator 
    which has attribute id == 'a'.
    The InitDeclarator also refers to a Initializer object which contains 0.

Declarator object is used when there is pointer(s) in front of a direct_declarator, 
if there is no pointer in front of the variable, the Declarator object is still created but is referring to
a direct_declarator.
Example: int *a; 
    A Declarator object is created with attribute self.pointer = ['*'] and self.direct_declarator referring to 
    a DirectDeclarator object.
Example: int **a; 
    A Declarator object is created with attribute self.pointer = ['**']
Example: int a; 
    A Declarator object is created with attribute self.pointer = None
