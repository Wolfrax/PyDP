# Introduction

This document is notes of an implementation of pre-K&R C compiler written entirely in Python.
It aims to correct compile the C-compiler source code as distributed with Unix v6.
Addionally, it should be able to correctly interprete the same C-ode, thereby bootstraping the compiler.

The implementation does not claim to be optimized or correct, some ambitions are made do make it readable.
It has grown organically over time, adding piece by piece, so 'readable' can perhaps be disputed, therefore these
annotations are made to complement the implementation.

The document reflect minly the thought process encountered when doing the implementation and make no claim of being
accurate, but is tried to be kept up to date.

# General Links

- [Dennis Ritchie page](https://www.nokia.com/bell-labs/about/dennis-m-ritchie/)
- [Collection of documents](https://doc.cat-v.org/unix/v6/operating-systems-lecture-notes/v6/)
- [C Reference Manual](https://doc.cat-v.org/unix/v6/operating-systems-lecture-notes/v6/doc/c.ps)
- [C6T](https://github.com/popeyeotaku/c6t/tree/master)

# External declarations

## Overview

External declarations are derived from the abstract syntax tree (AST) build-up during parsing of C-code.
The nodes are several and complex in hierarchy. The implementation of the AST is in **CCast.py**.
Nodes dealing with declarations have a **decl** method, that will call connected nodes decl-methods and aggregate
information into a **CCDecl**-object (or several). The CCDecl-class is implemented in **CCconf.py** and is used as a
intermediary object between the AST and a symbol table. The attributes to a CCDecl-object is added dynamically when
traversing the AST. An important attribute is **ctx**, that helps to identify which type of declaration we are dealing
with.

Nevertheless, declarations can be complex beasts with many permutations of 'basic' declarations. The various types
of declarations and how to handle them are described below as reference to the implementations made in **CCSymbols.py**

These types of declarations are identified:

- Variables, such as __int a__
- Arrays, such as __int a[10]__
- Structures, such as __struct a { int b; int c; } d;__
- Combinations and additional attributes to above declaration type, such as
  - initializers: __int a 1;__
  - array of structures: __struct a { int b; int c; } d[10];::
  - etc

A symbol table have different entries depending on which variant of declaration we are dealing with. At the end of
processing a declaration through a CCDecl-object, we should have added a symbol using its **name** as key.
We will also have allocated memory for the declaration (implementation in **CCMemory.py**), accurate in position and size
in memory (using a PDP 11/40 architecture; little endian, 2 bytes integers etc - see **CCMemory.py**).
Memory positions is needed when we deal with declarations using pointers.

We distinguish between various types of declarations using the ctx-attribute in the CCDecl-object:

- Variables: __ctx is ['id']__
- Arrays: __ctx is ['id', 'array']__
- Structures: __ctx is ['id', 'array', 'struct_specifier']__

Below are details on the logic for different types of declarations.

### Symbolic constans

No declaration as such, simple __#define CONST 1__, any __CONST__ is replaced by 1 during compile time.
Note that __#define__ can have constant expressions, such as __#define XTYPE (03<<3)__, which needs to be evaluated
to a constant during compilation.

Constants are stored in symbol table using its symbolic name as key.

### Variables

A variable declaration has:
- __type__
    - basic type (int, long, char, float, double)
    - reference/pointer type (int *a[1] - array with one element, pointer to int)
- __name__
- __initializer__ (optional, see below)

Note that no check is made of duplicate names, an identifier might be declared several times. The last occurrence 
will overwrite previous entries in symbol table.

An initializer of a variable can be different kinds, depending on the type of variable:

#### Basic type

1. __int a 1;__ 
   - a is 2 bytes in memory, initialized to 1
2. __char c 'a';__
   - c is 1 byte in memory, initialized to 97 (ord(a))
3. __char c 97;__ 
   - c is 1 byte in memory, initialized to 97, same as above

#### Pointer type

4. __int *a 1;__ 
   - a is 2 bytes in memory (type 'pointer') initialized to memory position 1
5. __char *c 'a';__ 
   - c is 2 bytes in memory (type 'pointer') initialized to a memory position 'a' (97)
6. __char *c 97;__
   - same as above
   
Cases 4 - 6 is semantically meaningless, but syntactically Ok, but we can't distinguish them from case 8.
     
7. __char *c "abc";__ 
   - c is 2 bytes in memory (type 'pointer') referring to a memory position for 'abc' (97 98 99 0 - 4 bytes). 
   A null byte (\0) is added at the end of the string. Thus, the extent for the string is 3 + 1 = 4 bytes in memory.
8. __int *a &b;__ 
   - a is 2 bytes in memory (type 'pointer') referring to a memory position for for b.
   b has been previously declared and should be of type int, a is initialized to the memory position for b.
9. __int b[2] { 1, 2 }; int *a &b[1];__ 
   - a is a pointer that is initialized to the address of the second element of the array b. 
   NOT IMPLEMENTED yet, see CCast::Initializer, need to implement PostfixExpression.eval()

#### List

When initializer is __{ constant expression }__

10. __int a { 1 + 1 };__ 
    - During parsing the constant expression will be a BinOpExpression in AST.
    When evaluating this expression (when creating declaration object), it will be evaluated to 2. 
    Hence, the initializer will be 2. Same thing applies if the operators would be a constant or variable 
    (previously declared), such as { 1 + b }, evaluation of BinOpExpression will resolve b into a value.
    Hence, such expression will be a constant. Thus, the initializer will be a one element list with a value.
11. __int *b { a };__ 
    - same case as 2.e above, different syntax. initializer will be a list with one element, mempos for 'a'. 
    Thus, 'a' is already resolved to its address/mempos by the AST Initializer object and will be a number, 
    not a symbolic constant.
12. __char *c { "ABC" };__ 
    - same case as 2.d above, different syntax. c is a pointer to the string ABC

### Arrays

An array object has type, subscript and rank, initializers which is described below.

#### Type

- basic type (__int, char, float, double__)
- reference/pointer type (int __*a[1]__ - array with one element, pointer to int)
- composite type (__struct__)

Note that an array can have structs as elements, for example __struct a b[10]__.
This will have ctx __['id', 'array', 'struct_specifier']__, so this combination is not handled as an array
but as a structure, which in turn manages the array part.

#### Subscript and rank

- one-dimensional (for example, __int a[1]__ - rank one)
- multi-dimensions (for example, __int a[1][1]__ - rank two)

From C Reference Manual §8.3:

    A subscript can be a constant-expression "whose value is determinable at compile time,
    and whose type is int." If there is no subscript, "the constant 1 is used".

Thus, __int a[b + c];__ is valid. a and c should be constants (#define) and not variables.

#### Initializer

For example, __int a[1] {0}__, initialize a one-dimensional array of one element with 0

From C Reference Manual §10,2:

    An initializer for an array may contain a comma-separated list of compile-time expressions.
    The length of the array is taken to be the maximum number of expressions in the list
    [initializer list] and the square-bracketed constant in the array's declarator.

Thus, __int a[1] { 1, 2 }__, size of array is 2, not 1.

The initializer list may include symbolic constants and expressions that can be calculated at compile time
and need to be compatible with the array type.

A single string may be given as the initializer for an array of char's; in this case, the characters
in the string are taken as the initializing values.

Thus, __char a[] "ABC";__ is valid and identical to __char *a "abc";__

__char *a[] {"abc", "def", 0};__ 

This is an array of pointers to character strings.
The size of the array is 6 bytes; 2 pointers to the character strings and one pointer to 0.
Hence, we need to read the strings, store them into memory, then initialize the array with the
addresses to these strings.

Note, array initializer can have a symbolic constant which is turned into a value in AST for Initializer. 
See class Initializer(Node): in CCast.py.

Examples:

```
#define A 1
int b;
int a[] { A, b, 3 }; /* => int a[] { 1, 0, 3 } in CCast::Initializer.decl() */
```

In the example, b is seen as a reference and will be replaced by its memory position (in this example 0).
This is not intention (I assume) in C, but syntax is allowed (for now) in this implementation.
Semantically correct would be int a[] { A, &b, 3 }, but in general this is not correct either as the
initializer list should be a list of constant expressions.    
It is still allowed since we need to handle: int *a { b }; which is semantically correct.

If an array is of pointer type and have initializers it needs to point to char.

This is valid:
```
char *a[] { "abc", def", 0 };
```

This is not valid:
```
int *a[] { 1, 2, 3 };
```
Semantically, this would mean an array of 3 pointers, initialized to memory addresses 1, 2 and 3. It is not allowed.

### Structures

In this setting, structures can be seen as a collection of variables, and can be declared as an array.
The semantics of structures is somewhat unclear, and the combinations of different types of declarations are many.

A struct declaration can have an optional tag name in front of the declaration of its members. It can also optionally 
declare a variable, which may be of array type. If no variable is declared with the struct, its members are still 
declared and will occupy memory space. A struct declaration might be lacking both tag and variable, which therefore
be seen just as a number of variables kept together. See more below.

The CCDecl.ctx list-attribute will always end with __'struct_specifier'__, but may contain additional elements.

Below, we try to sort out some of the cases, and the end result in memory.

Struct-symbol cases:

1. __with/without struct_tag__ (examples with struct tag):
    - ctx has 1 element  ['struct_specifier']: struct a { int b; }
    - ctx has 2 elements ['id', 'struct_specifier']: struct a c; or struct a { int b; } c;
    - ctx has 3 elements ['id', 'array', 'struct_specifier']: struct a c[10];
2. __with initializer__
    - struct a { char *id; int i; } c[] { "abc", 1, "def", 2 }; Initialize c with 2 elements
3. __as an array__
4. __self-referential__, struct a { struct a *ptr1, *ptr2; };
5. __member is of type array__, struct a { char b[10]; } c;

Note
- that if a struct-variable is a pointer, this is indicated by the attribute symbol.pointer (list type).
- the struct tag (struct a) in the attribute symbol.struct_tag

#### Struct Members

Structs can be seen as a container for variables and arrays, the following logic applies.

According to C Reference Manual, §8.5:
    
    The same member name can appear in different structures only if the two members are of the same type and if
    their origin with respect to their structure is the same; thus separate structures can share a common
    initial segment.

This is an example, what is possible (even if not explained by above paragraph):

```
struct {int a1; char a2}
struct b {int a1; int a3;}
struct b *c;
```

This would declare 3 members: a1, a2 and a3, with unique memory positions (2 bytes each).
The following operation is possible from above declarations: __c->a2++;__

Thus, c can reference member a2, even if it is not part for struct b declaration(!)

In the original compiler, it looks like members of structures are treated as variables, but with a "."
prepended to the name. Thus, struct {int a1; char a2}; would become ".a1" and ".a2" variables. In this implementation
we are not using this naming, but it is an indication that members are seen as variables.

How about arrays of structures? For example, `struct a {int a1; char a2;} b[10];`

This declares an array of 10 a1- and a2-members. In memory, it would like so (memory positions to the left):

```
n  : first a1 (2 bytes)
n+2: first a2 (1 byte)
n+3: padding (1 byte)
n+4: second a1 (2 bytes)
n+6: second a2 (1 byte)
n+7: padding (1 byte)
```

and so on... 40 bytes in total reserved in memory. __b[1].a1__ would refer to the second a1 at memory position 4.
Syntactically, this is the same as __*(b+1).a1__
Note that b, as an array of structs, occupy memory positions before the members, so

```
n-20: b[0}
n-18: b[1]
...
n   : first a1
```

How does that work with the following example?

```
struct a {int a1; char a2} b[10]; 
struct c {int a1; int a3;} d[10];
```

Would d be of same size as b? Yes!

But would __d[1].a2__ be possible?
Would that refer to the 1-byte (char) at offset 6 in memory? 
__d[1].a3__ would refer to the 2-bytes (int) at offset 6 in memory.

Let's assume this is the intended logic, it is not clearly stated in manuals.

As a consequence, if a member name is already declared in the symbol table, we need to check that type and
position within the struct is the same.

#### Initialization

Overall, the C reference manual states in §10:

    Structures can be initialized, but this operation is incompletely implemented and machine-dependent. Basically
    the structure is regarded as a sequence of words and the initializers are placed into those words. Structure
    initialization, using a comma-separated list in braces is safe if all the memers of the structure are integers
    or pointers but is otherwise ill-advised.

Example, `struct a { char *id; int i; } c[] { "abc", 1, "def", 2 };`

First loop all struct members to know
- type and size for each member
- how many members, then we know the total size for the struct, __struct size__ 
  (from example: 1 byte (char) + 1 byte (padding) + 2 bytes (int) = 4 bytes)

Then check if there is a variable (symbol.name exists and is 'd') and check if it is of array type 
(__len(ctx) == 3__ and __ctx[1] == 'array'__). 

Check if there is subscript(s), if so calculate the array size.
If there is no subscript, but still of array type, it is either of size 1 (no initializer) or the size 
of the initializer.

Now we need to loop the initializer (if existing) and map each value (which might be a constant expression)
vs the members (check type vs member type). We count the number of initializer and make sure that the
total count match count of members (__'initializer count' % 'member count' == 0__).

If all is well so far, we can calculate the array size through 
__'array size' = 'initializer count' / 'member count'.__, from the example this will be 4 / 2 = 2.

If there has been a subscript, the 'array size' should match the subscript. If no subscript, 'array size' is used.

Now we can calculate the 'total struct size' as __'struct size' * 'array size'__, by example: 4 * 2 = 8 bytes in total.

Then reiterate the initializers and store them in memory, sequentially after each other. Note that the example
have strings as initializers, they are stored in memory with a null byte, then the first struct member (id) 
refers/points to these strings.

The struct variable 'c' should be stored in memory as a pointer to the first element.

A memory layout for above example can look as follows:

```
0:  abc0 (first initializer string with null byte, 4 bytes)
4:  def0 (second initializer string with null byte, 4 bytes)
8:  0 (*id, first struct member, with a reference to the first array element initializer, 2 bytes)
10: 1 (i, second struct member, first array element with value 1, 2 bytes)
12: 4 (*id, first struct member, with a reference to the second array element initializer, 2 bytes)
14: 2 (i, second struct member, second array element with value 2, 2 bytes)
16: 8 (c[], struct/array variable with a reference to the first struct member of the first array element, 2 bytes)
```

Note that struct members can not have initializers, according to the grammar it is not syntactically correct.

#### Nested structures

Nested struct declarations are allowed, examples.

```
struct a {
    struct b { 
        struct c { int c1; } c;
    } b;
} a;  /* size 2 bytes */

struct b {
    struct a { int a1; int a2; } b1;
    int b2;
} b;  /* Size 6 bytes */

struct a { int a1; int a2; };
struct b { struct a b1; int b2; } b;  /* size 6 bytes */
```

Note that in the last example, if the declaration is changed to `struct b { struct a *b1; int b2; } b;` the size of
struct b is 4 bytes, as B1 is a pointer to struct a.

To handle structures whose members are referring to previous declared structs an entry in the symbol-table 
implementation exists, using the struct tag as key.
Thus, to handle `struct b { struct a b1; int b2; } b;`, the implementation will look-up `struct a`and get the size
from there.

Self-referential struct declarations are allowed.

```
struct a { int m1; struct a *p1; struct a *p2; } b;  /* size 2 + 2 + 2 = 6 bytes */ 
```

#### Structures and arrays

```
struct a { int a1 };
struct b { struct a b1[]; } b;
struct c { struct a c1[10]; } c;
struct d { struct a d1[10]; } d[10];
```

#### Implementation

To keep the implementation clean, the declaration is looped several times; checking, calculating, laying out in memory
etc in several pass. It may seem unnecessary, but the intention is to keep the code clean and logical.

First, check for nested struct declarations.

Secondly, determine types and size of members and the entire struct declaration, taking into account if the
struct variable is of array type.

Thirdly, layout out the struct in memory, including any initializers.

Finally, layout the struct variable, it should be a reference to the first member of the struct.
If the struct variable is not of array type, it should not occupy any memory space. If it is of array type, or a 
pointer, it should occupy memory. If array type, one memory reference for each array element.
