import pprint
from distutils.fancy_getopt import neg_alias_re

from CCError import CCError
import cc
import logging

logger = logging.getLogger(__name__)

class CCSymbols:
    def __init__(self, memory):
        self.constants = {}
        self.variables = {}
        self.structures = {}
        self.struct_members = {}
        self.struct_tags = {}
        self.functions = {}
        self.memory = memory

    def size(self, symbol):
        if symbol.pointer:
            return self.memory.sz_of['pointer']
        elif symbol.type_name in ['char', 'int', 'long', 'float', 'double', 'pointer']:
            return self.memory.sz_of[symbol.type_name]
        else:
            raise CCError(f'Unknown symbol type {symbol.type_name [{symbol.lineno}]}')


    def variable2Memory(self, symbol):
        # See Annotations, Variables
        if symbol.hasattr('initializer'):
            if isinstance(symbol.initializer, list):  # Example: int a { 1 };
                if len(symbol.initializer) != 1:
                    raise CCError(f'Initializer should be a list with one element, length = {len(symbol.initializer)} '
                                  f'[{symbol.lineno}]')

                # If initializer is a string, memory.write will loop the string and add a null-byte at end
                mempos = self.memory.write(symbol.initializer[0], type=symbol.type_name, byte=(symbol.type_name == 'char'))
                mempos = self.memory.write(mempos, type='pointer') if symbol.pointer else mempos
            else: # cases 1 to 9 in Annotations
                if isinstance(symbol.initializer, str): # char *c "abc";
                    if not symbol.pointer:
                        raise CCError(f'Symbol {symbol.name} has no pointer [{symbol.lineno}]')

                    if not symbol.initializer:
                        raise CCError(f'Symbol {symbol.name} has empty initializer string constant [{symbol.lineno}]')

                    mempos = self.memory.write(symbol.initializer, type='char', byte=True)
                    mempos = self.memory.write(mempos, type='pointer')
                else:  # Initializer is not string
                    # TODO, check case 9 when PostfixExpression.eval() is implemented
                    mempos = self.memory.write(symbol.initializer, type=symbol.type_name)
        else: # No initializer
            if 'function' in symbol.ctx: # variable is a function pointer
                mempos = self.memory.init_mem(type='pointer')
            else:
                mempos = self.memory.init_mem(type='pointer' if symbol.pointer else symbol.type_name)

        logger.debug(f"variable2Memory {symbol.name} [{symbol.lineno}]: mempos = {mempos}")

        return mempos

    def arraySize(self, symbol):
        if 'struct_specifier' in symbol.ctx:
            """
            Array is of struct type: struct a b[10];
            call struct_size to get size of struct a, then later handle that this is repeated 10 times for subscript
            """
            size_elem = self.structSize(symbol)
        else:
            size_elem = self.size(symbol)  # int a[10]; => size of int = 2

        # Get rank and calculate total array size
        array_size = 1
        if symbol.hasattr('subscript'):
            for subscript in symbol.subscript:
                array_size *= subscript
            array_size *= size_elem  # int a[10] => size = 2 * 10 = 20
        else:  # int a[]; => size 1
            array_size = size_elem

        """
        If an array has initializer, we need to compare the number of elements in the initializer vs the subscript
        (if any) of the array. If there are more initializers than what is indicated by the subscript, we set the size
        of the array to max the max value of either initializer or subscript.
        """
        if symbol.hasattr('initializer'):
            if symbol.hasattr('subscript'):  # int a[2] {1, 2, 3}; => integer array of size 3 integers (6 byte)
                array_size = len(symbol.initializer) * size_elem
            else:
                if isinstance(symbol.initializer, str):  # char str[] "ABC";
                    array_size = size_elem
                elif array_size != (size_elem * len(symbol.initializer)):  # int a[1] { 1, 2, 3 }
                    array_size = max(len(symbol.initializer), array_size) * size_elem

        return array_size

    def array2Memory(self, symbol):
        # See Annotations, Arrays
        if symbol.hasattr('initializer'):  # int a[2} { 1, 2 };
            # Error check, an array variable of pointer type with initializers need to have strings
            # This is illegal: int *a[2] { 1, 2 }; not possible to initializer with addresses
            if symbol.pointer:
                if symbol.type_name != 'char':
                    raise CCError(f'Array pointer symbol {symbol.name} with initializer, wrong type [{symbol.lineno}]')
                else:
                    for initializer in symbol.initializer:
                        if not (isinstance(initializer, str) or isinstance(initializer, int)):
                            raise CCError(f'Array pointer "{symbol.name}", initializers need to be string or int '
                                          f'[{symbol.lineno}]')

            initializer_mempos = []

            for ind, initializer in enumerate(symbol.initializer):
                if isinstance(initializer, str):  # char *str[] { "abc", "def", 0 }; and char str[] "abc";
                    # Write string to memory, not char-by-char, memory.write will 0-terminate the string
                    init_str = symbol.initializer[ind] if isinstance(symbol.initializer, list) else symbol.initializer
                    initializer_mempos += [self.memory.write(init_str, type='char', byte=True)]
                else:  # int a[] { 1, 2 };
                    initializer_mempos += [self.memory.write(initializer, type=symbol.type_name)]

            if symbol.pointer:
                for pos in initializer_mempos[1:]:
                    # char str[] { "ABC", "DEF" }; str[0] - address to "ABC0", str[1] - address to "DEF0"
                    self.memory.write(pos, type='pointer')

            mempos = initializer_mempos[0]
        else:  # No initializer, int *a[10]; or int a[10]
            if 'struct_specifier' in symbol.ctx:
                """
                Example:
                    struct a { int a1; int a2; };
                    struct b { struct a b1[10]; int b2; } b;
                symbol in this case is the first member of struct b (struct a b1[10])
                Here we are called from struct2Memory, we initialize memory to the symbol.size which is in bytes
                Note that below also cover if we have: struct *b1[10]as a first member.
                
                If we have: struct a array[2]; it is covered in struct2Memory, not here
                """
                sz = 1
                for subscript in symbol.subscript:  # multiple subscripts
                    sz *= subscript

                if symbol.pointer:
                    mempos = self.memory.init_mem(size=sz, type='pointer')
                else:
                    mempos = self.memory.init_mem(size=symbol.size * sz, type='byte')
            else:  # No struct_specifier: int a[2];
                """
                Memory layout for int a[2]; - array of 2 integers
                    n:     a (2 bytes) = first element
                    n + 2: 0 (2 bytes) = second element
                a will hold mempos = n, which is returned by this method
                """
                mempos = self.memory.init_mem(size=symbol.size, type='pointer' if symbol.pointer else symbol.type_name)

        logger.debug(f"array2Memory {symbol.name} [{symbol.lineno}]: mempos = {mempos}")

        return mempos

    def structSize(self, symbol):
        """
        If struct variable is array, find out how many elements.

        Note that below is only referring to the 'outer' struct variable
        Example:
            struct a { int a1; int a2; };
            struct b { struct a m[10]; } b[10];
        The 'outer' struct variable is b[10]. m[10] is an 'inner' struct member of array type.
        For the 'inner' struct member the symbol (for this member) has a subscript (10) but ctx is 'struct_specifier'
        only ('array' not included in ctx).
        Hence, "if 'array' in symbol.ctx and symbol.hasattr('subscript'):" is True only for the 'outer' struct variable.

        The 'inner' struct member of array type is handled by calling arraySize.
        """

        array_sz = 1
        if 'array' in symbol.ctx and symbol.hasattr('subscript'):
            for subscript in symbol.subscript:
                array_sz *= subscript

        # Now loop all members in the struct, calculate the size if the struct
        struct_size = 0
        for i in range(array_sz):
            if symbol.declaration_list:  # Only loop if there is a declaration_list (list of struct members)
                for ind, member in enumerate(symbol.declaration_list):
                    """
                    member cases:
                        array: ctx = ['id', 'array']
                        variable: ctx = ['id']
                        struct: ctx = ['struct_specifier']
                    """

                    if 'array' in member.ctx:  # member is an array
                        """
                        Note that this member is of struct type: struct a { struct b m[10]; };
                        array_size is called for this member, taking care of the subscript of 10.
                        array_size will in turn call struct_size to get the size of struct b
                        So recursive call...
                        """

                        member.size = self.arraySize(member)  # This will take care of array of pointers also
                    elif 'id' in member.ctx:  # member is a variable
                        member.size = self.size(member)
                    elif 'struct_specifier' in member.ctx:  # member is a struct
                        if member.pointer:
                            if member.hasattr('subscript'):  # array of pointers to struct
                                """
                                Example:
                                    struct a { int a1[10]; int a2; };
                                    struct b { struct a *b1[10]; int b2; } b;
                                The first member of struct b has a size of 10 pointers = 2 * 10 = 20 bytes
                                """
                                size = 1
                                for subscript in member.subscript:
                                    size *= subscript
                                member.size = size * self.memory.sz_of['pointer']
                            else:  # pointer to struct
                                """
                                Example:
                                    struct a { int a1[10]; int a2; };
                                    struct b { struct a *b1; int b2; } b;
                                The first member of struct b has a size of a pointer = 2 * 1 = 2 bytes
                                """
                                member.size = self.memory.sz_of['pointer']
                        elif member.struct_tag in self.struct_tags:  # No pointer
                            """
                            check if size of this struct_tag already exist
                            Example:
                              struct a { int a1; int a2; } => struct 'a' has size 2 + 2 = 4 bytes
                              struct b { struct a b1; int b2; } b; => struct 'b' has size 4 + 2 = 6 bytes
                            """
                            member.size = self.struct_tags[member.struct_tag].struct_size
                        else:  # No pointer and struct member not declared before
                            """
                            recursive call if there is no previous struct size for this struct_tag
                            Example:
                                struct b {
                                    struct a { int a1; int a2; } b1;
                                    int b2;
                                } b;  => 2 + 2 + 2 = 6 bytes
                            """
                            member.size = self.structSize(member)
                    else:
                        raise CCError(f'Unknown member combination for size calculations: {member} [{member.lineno}]')

                    struct_size += member.size

                    symbol.struct_size = struct_size
                    self.struct_tags[symbol.struct_tag] = symbol
            else:
                """
                No declaration_list, but symbol is still a struct
                Example:
                    struct a { int a1; int a2; };
                    struct b { struct a m[10]; } b;
                We are referring to "struct a m[10];" here. struct_size is be (2 + 2) = 4 bytes
                
                Note that we are not updating symbol.struct_size or self.struct_tags with symbol here as we are
                called recursively on this else branch.
                """
                if symbol.struct_tag in self.struct_tags:
                    struct_size += self.struct_tags[symbol.struct_tag].struct_size
                else:
                    raise CCError(f'Unknown struct tag: {symbol.struct_tag}')

        return struct_size

    def structMember2Memory(self, symbol):
        array_sz = 1
        if 'array' in symbol.ctx and symbol.hasattr('subscript'):
            for subscript in symbol.subscript:
                array_sz *= subscript

        # Now loop all members in the struct and add to memory
        for i in range(array_sz):
            for ind, member in enumerate(symbol.declaration_list):
                """
                member cases:
                    array: ctx = ['id', 'array']
                    variable: ctx = ['id']
                    struct: ctx = ['struct_specifier']
                """
                if 'array' in member.ctx:  # member is an array
                    """
                    Note that this member is of basic type: struct a { int m[10]; };
                    array2memory is called for this member, which will initialize memory to the size of this member
                    """

                    member.mempos = self.array2Memory(member)
                elif 'id' in member.ctx:  # member is variable
                    if member.name in self.struct_members:
                        if (member.type_name != self.struct_members[member.name].type_name or
                                ind != self.struct_members[member.name].index):
                            raise CCError(f"Error struct {symbol.struct_tag} [{member.lineno}] "
                                          f"type_name: {member.type_name} index: {ind}, "
                                          f"does not match previous type: {self.struct_members[member.name].type_name} "
                                          f"or index: {self.struct_members[member.name].index}")
                        else:
                            member.mempos = self.variable2Memory(member)  # member exists and match type and index
                    else:  # New member
                        member.index = ind
                        member.mempos = self.variable2Memory(member)  # Add struct member to memory
                        self.struct_members[member.name] = member
                elif 'struct_specifier' in member.ctx:
                    """
                    Here we need to do the work of handling arrays and pointers
                    First we treat if the member is a pointer, and array or a single pointer
                    """
                    if member.pointer:
                        if member.hasattr('subscript'): # member is a pointer to an array of struct-type
                            member.mempos = self.array2Memory(member)
                        else:  # no subscript, member is a pointer to a struct
                            member.mempos = self.memory.init_mem(type='pointer')
                    else:  # No pointer
                        if member.hasattr('subscript'):  # member is an array of structs
                            """
                            Note that this member is of struct type: struct a { struct b m[10]; };
                            array2memory is called which will initialize memory to the size of this member.
                            """
                            member.mempos = self.array2Memory(member)
                        else:  # Ok, not a pointer, not an array => member is of struct type
                            """
                            check if this struct_tag already exist
                            Example:
                              struct a { int a1; int a2; }
                              struct b { struct a b1; int b2; } b;
                            """
                            if member.struct_tag in self.struct_tags:
                                member.mempos = self.memory.init_mem(size=member.size, type='byte')
                            else:  # new member of struct type
                                """
                                Recursive call...
                                Example:
                                  struct b {
                                      struct a { int a1; int a2; } b1;
                                      int b2;
                                  } b;
                                """
                                self.structMember2Memory(member)
                else:
                    raise CCError(f'Unknown member combination for adding to memory: {member} [{member.lineno}]')

        logger.debug(f"structMember2Memory {symbol.struct_tag}")
        return symbol

    def checkMemberTypes(self, symbol):
        # Check member type vs initializer type
        if symbol.declaration_list:
            declaration_list = symbol.declaration_list
        else:
            declaration_list = self.struct_tags[symbol.struct_tag].declaration_list

        for initializer_ind, initializer in enumerate(symbol.initializer):
            member = declaration_list[initializer_ind % len(declaration_list)]
            initializer_type = type(initializer).__name__
            if initializer_type == 'int':
                match = member.type_name in ['int', 'long']
                if not match:
                    """
                    Note that an initializer can be 'int' while the member type is 'char'
                    Example:
                        struct a { char *str; int a1; } a[] { "ABC", 1, 0, 0 };
                    The third initializer (0), is 'int', while the member type is 'char'.
                    """
                    match = member.type_name in ['char']
            elif initializer_type == 'float':
                match = member.type_name in ['float', 'double']
            elif initializer_type == 'str':
                match = member.type_name == 'char' and len(member.pointer) > 0
            else:
                match = False

            if not match:
                return False
        return True

    def struct2Memory(self, symbol):
        """
        First allocate the struct variable in memory. Other struct members are allocate sequentially in memory
        after this variable. This is equivalent: a->m1 = 1; and (*a).m1 = 1
        """
        if symbol.hasattr('name'):
            """
            Reserve memory for the struct variable, which will be of type 'pointer', as it is referring to the
            members of the structure.
            
            If the struct variable have an initializer, the members should be initialized with the elements from
            the initializer, assuming the number and types agree.
            Example:
                struct a { char *m1; int m2 } a { "ABC", 1 };
            m1 will point to "ABC" and m2 will have the value 1.
            
            It becomes even more complex when the struct-variable is of type array without any subscript value present.
            Example:
                struct a {char *m1; int m2 } a[] { "ABC", 1, "DEF", 2 };
            By reading above example we see that the size of the array will be 2, because the struct have 2 members
            and the initializer have 4 elements. So, "(nr of initializer elements) % (number of struct members) == 0",
            then "(size of array) = (nr of initializer elements) / (number of struct members)" for the initializer
            and the array of structs to match each other. The type of initializer values must match the types of
            struct members.
            """

            """
            Note that we can have: struct a *ap;
            Then ap is already a pointer.
            But if we have: struct a a; then a will have the address to the first member of struct a
            """
            if len(symbol.pointer) == 0:
                symbol.type_name = 'pointer'
                symbol.pointer = ['*']

            if symbol.struct_tag in self.struct_tags:
                nr_of_struct_members = len(self.struct_tags[symbol.struct_tag].declaration_list)
            else:
                nr_of_struct_members = len(symbol.declaration_list)

            if 'array' in symbol.ctx:
                if symbol.hasattr('initializer'):
                    if not self.checkMemberTypes(symbol):
                        raise CCError(f"checkMemberTypes: member types does not match initializer "
                                      f"types [{symbol.lineno}]")


                    # Check that number of initializers match number of struct members
                    nr_of_initializers = len(symbol.initializer)
                    if nr_of_initializers % nr_of_struct_members != 0:
                        raise CCError(f"nr of initializers ({nr_of_initializers}) does not match "
                                      f"nr_of_struct members ({nr_of_struct_members}). ")
                    else:
                        # Calculate array subscript, even if it is declared
                        subscript = nr_of_initializers // nr_of_struct_members

                    # Now check if struct variable of array type have a declared subscript
                    if symbol.hasattr('subscript'):
                        if len(symbol.subscript) > 1:
                            raise CCError(f"Initialization of multi-dimensional array of structs not implemented.")

                        """
                        Use either calculated subscript or the declared, depending on the size of initializers
                        Example:
                            struct a {int a1; int a2} a[3] { 1, 2 ,3, 4 };
                        The calculated subscript is len(initializers) = 4, divided by number of members (2) => 4 / 2 = 2
                        The declared subscript is 3, use max(3, 2) = 3.
                        This implies that the struct is only partially initialized (last struct element will be 0).
                        
                        The other way apply also: struct a {int a1; int a2} a[1] { 1, 2, 3, 4 };
                        Here subscript will be 2.
                        """
                        symbol.subscript = [max(subscript, symbol.subscript[0])]
            else:  # struct variable not of array type
                if symbol.hasattr('initializer'):
                    if symbol.declaration_list:
                        if not self.checkMemberTypes(symbol):
                            raise CCError(f"checkMemberTypes: member types does not match initializer "
                                          f"types [{symbol.lineno}]")

                        nr_of_initializers = len(symbol.initializer)
                        if nr_of_initializers != nr_of_struct_members:
                            raise CCError(f"nr of initializers ({nr_of_initializers}) does not match "
                                          f"nr_of_struct members ({nr_of_struct_members}). ")
                        """
                        First we write the struct variable to memory, initialized to zero. 
                        The struct variable should have the base address of the struct and be placed in memory
                        before the struct members. the base address is the mempos of the first struct member.
                        
                        As we know that nr of struct members and their type matches nr of initializers and their type
                        we write the initializers to memory, saving their memory positions in a list (mempos).
                        
                        Then, when all members are written to memory, we update the struct variable with the mempos
                        of the first struct member. So, only the first member of mempos-list is used.
                        
                        Note that we don't use structMember2Memory, as initializer syntax are restricted; they cannot
                        contain structs or arrays, only basic types.
                        Example:
                            struct a { int a1; int a2; }
                            struct b { struct a b1; int b2; } b { { 1, 2 }, 3 } <= nested initializers not allowed
                            struct c { int c1[2]; int c2; } c { 1, 2, 3 )  <= 1, 2 initialize c1, but not possible  
                        """
                        structvar_mempos = self.memory.init_mem(size=1, type='pointer')

                        mempos = []
                        for ind, member in enumerate(symbol.declaration_list):
                            mempos += [self.memory.write(symbol.initializer[ind],
                                                         type=member.type_name,
                                                         byte=(member.type_name == 'char'))]
                        self.memory.update(structvar_mempos, mempos[0], type='pointer')
                    else:  # struct variable have initializer but no declaration_list
                        """
                        Example:
                            struct a { int a1; int a2; };
                            struct a b { 1, 2 };
                        We end up here for the second row of this example.
                        Look up 'a' (struct_tag) in self.struct_tags.
                        """
                        if symbol.struct_tag not in self.struct_tags:
                            raise CCError(f"{symbol.struct_tag} is not declared [{symbol.lineno}]")
                        if not self.checkMemberTypes(symbol):
                            raise CCError(f"checkMemberTypes: member types does not match initializer "
                                          f"types [{symbol.lineno}]")

                        nr_of_initializers = len(symbol.initializer)
                        if nr_of_initializers != nr_of_struct_members:
                            raise CCError(f"nr of initializers ({nr_of_initializers}) does not match "
                                          f"nr_of_struct members ({nr_of_struct_members}). ")

                        structvar_mempos = self.memory.init_mem(size=1, type='pointer')

                        mempos = []
                        for ind, member in enumerate(self.struct_tags[symbol.struct_tag].declaration_list):
                            mempos += [self.memory.write(symbol.initializer[ind],
                                                         type=member.type_name,
                                                         byte=(member.type_name == 'char'))]
                        self.memory.update(structvar_mempos, mempos[0], type='pointer')
                else:  # struct variable is not array and have no initializers: struct a { int a1; int a2; } a;
                    symbol.mempos = self.memory.init_mem(size=1, type='pointer')
                    """
                    Note that the struct variable can be a pointer to a struct and have no declaration list, 
                    Example: struct a *ap;
                    """
                    if symbol.declaration_list:
                        symbol = self.structMember2Memory(symbol)  # sets mempos for all members
                        self.memory.update(symbol.mempos, symbol.declaration_list[0].mempos, type='pointer')

                symbol.size = self.size(symbol)

            self.variables[symbol.name] = symbol

        logger.debug(f"struct2Memory {symbol.struct_tag}")
        return symbol

    def add(self, symbols):
        """
        Some symbols might not be in a list, if so add them to a list to make it work in the loop below
        DeclarationSpecifier object does not return a list
        """
        if not isinstance(symbols, list):
            symbols = [symbols]

        """
        Adding symbol to a symbol table is dependent of which type it is, this is expressed in 'ctx'
        ctx can have several elements, thus a symbol cal be composite.
            struct a b[10] => ctx is ['id', 'array', 'struct_specifier']
        We start analyzing a symbol using the last ctx-element, but need to take into account any other elements
        """
        for symbol in symbols:
            ctx = symbol.ctx[-1]

            if ctx == 'const':  # This comes from preprocessor (#define a 10)
                if symbol.name in self.constants:
                    raise CCError(f"Duplicate constant name: {symbol.name ({symbol.lineno})}")

                self.constants[symbol.name] = symbol   # const will not occupy any memory
            elif ctx == 'id':
                symbol.size = self.size(symbol)
                symbol.mempos = self.variable2Memory(symbol)
                self.variables[symbol.name] = symbol
            elif ctx == 'array':
                symbol.size = self.arraySize(symbol)
                symbol.mempos = self.array2Memory(symbol)
                self.variables[symbol.name] = symbol
            elif ctx == 'struct_specifier':
                symbol.struct_size = self.structSize(symbol)
                symbol = self.struct2Memory(symbol)
                self.structures[symbol.struct_tag] = symbol
            elif ctx == 'function':
                if 'declarator' in symbol.ctx:
                    symbol.size = self.size(symbol)
                    symbol.mempos = self.variable2Memory(symbol)
                    self.variables[symbol.name] = symbol
                else:
                    logger.debug(f"function: {symbol.name}")
                    self.functions[symbol.name] = symbol
            else:
                raise CCError(f"Unknown ctx: {ctx} ({symbol.lineno})")

    def get_constant(self, name):
        return self.constants[name].value if name in self.constants else None

    def get_mempos(self, name):
        return self.variables[name].mempos if name in self.variables else None

    def get(self, name):
        if name in self.constants:
            return self.constants[name].value
        elif name in self.variables:
            return self.variables[name].value
        elif name in self.structures:
            return self.structures[name].value
        elif name in self.functions:
            return self.functions[name].value
        else:
            return None

    def dump(self):
        print('=== constants ===')
        pprint.pprint(self.constants)
        print('=== variables ===')
        pprint.pprint(self.variables)
        print('=== structures ===')
        pprint.pprint(self.structures)
        print('=== functions ===')
        pprint.pprint(self.functions)
