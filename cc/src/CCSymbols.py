import pprint

from CCError import CCError
# from cc.CCError import CCError

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
        self.locals = {}
        self.memory = memory

    def size(self, symbol):
        if symbol.pointer:
            return self.memory.sz_of['pointer']
        elif symbol.type_name in ['char', 'int', 'long', 'float', 'double', 'pointer']:
            return self.memory.sz_of[symbol.type_name]
        else:
            raise CCError(f'Unknown symbol type {symbol.type_name [{symbol.lineno}]}')

    def variable2Memory(self, symbol):
        mempos = self.memory.init_mem(type='pointer' if symbol.pointer or 'function' in symbol.ctx else symbol.type_name)

        init_val = None
        if symbol.hasattr('initializer'):
            if isinstance(symbol.initializer, list):  # Example: int a { 1 };
                if len(symbol.initializer) != 1:
                    raise CCError(f'Initializer should be a list with one element, length = {len(symbol.initializer)} '
                                  f'[{symbol.lineno}]')

                # If initializer is a string, memory.write will loop the string and add a null-byte at end
                init_val = symbol.initializer[0]
            else:  # no list as initializer, either variable, string, address
                if symbol.initializer in self.variables:  # char a[10]; char *b a; => b have the address to a[0]
                    if not symbol.pointer:
                        raise CCError(f'Symbol {symbol.name} no pointer type, initialized to {symbol.initializer} '
                                      f'[{symbol.lineno}]')
                    init_val = self.variables[symbol.initializer].mempos
                elif isinstance(symbol.initializer, str):  # char *c "abc"; int c 'a';
                    if not symbol.pointer and symbol.type_name not in ['char', 'int']:
                        raise CCError(f'Symbol {symbol.name} no pointer type [{symbol.lineno}]')

                    if not symbol.initializer:  # char *c "";
                        raise CCError(f'Symbol {symbol.name} has empty initializer string constant [{symbol.lineno}]')

                    if symbol.pointer:
                        init_val = self.memory.write(symbol.initializer, type=symbol.type_name, byte=True)
                    else:
                        init_val = symbol.initializer
                else:  # Initializer is not string: int i 1; or int *i 1; <= pointer i initialized to address 1
                    # TODO, check case 9 when PostfixExpression.eval() is implemented
                    init_val = symbol.initializer

        if init_val is not None:
            isByte = ((isinstance(symbol.initializer, str) and symbol.type_name in ['char', 'int']) or
                      (isinstance(symbol.initializer, list) and symbol.type_name == 'char') or
                      (isinstance(symbol.initializer, int) and symbol.type_name == 'char'))
            type_name = 'pointer' if symbol.pointer else symbol.type_name
            self.memory.update(mempos, init_val, type_name, byte=isByte)

        return mempos

    def arrayRank(self, symbol):
        rank = 1
        if 'struct_specifier' in symbol.ctx:  # struct a {int m1; int m2} v[] {1, 2, 3, 4}; => rank 2
            if symbol.struct_tag in self.struct_tags:
                nr_of_struct_members = len(self.struct_tags[symbol.struct_tag].declaration_list)
            else:
                nr_of_struct_members = len(symbol.declaration_list)

            if symbol.hasattr('initializer'):
                nr_of_initializers = len(symbol.initializer)
                if nr_of_initializers % nr_of_struct_members != 0:
                    raise CCError(f"nr of initializers ({nr_of_initializers}) does not match "
                                  f"nr_of_struct members ({nr_of_struct_members}). ")

                if symbol.hasattr('subscript'):
                    if len(symbol.subscript) > 1:
                        raise CCError(f"Initialization of multi-dimensional array of structs not implemented.")

                    rank = max(symbol.subscript[0], nr_of_initializers // nr_of_struct_members)
                else:
                    rank = nr_of_initializers // nr_of_struct_members

        # Get rank and calculate total array size
        if symbol.hasattr('subscript'):
            for subscript in symbol.subscript:
                rank *= subscript

        """
        If an array has initializer, we need to compare the number of elements in the initializer vs the subscript
        (if any) of the array. If there are more initializers than what is indicated by the subscript, we set the size
        of the array to max the max value of either initializer or subscript.
        
        Note the special case below, this is if we have an array of char that is initialized with a string, either in 
        a list ({ "abc" }) or without ("abc"). We need to test if it is a list, string, array of char-type and no 
        pointer to char.
        """
        if symbol.hasattr('initializer') and isinstance(symbol.initializer, list): # int a[2] {1, 2, 3}; => 3 elements
            if (len(symbol.initializer) == 1 and isinstance(symbol.initializer[0], str) and
                    symbol.type_name == 'char' and not symbol.pointer):
                # char str[] { "abc" }; => 4 elements - 3 chars + null-byte
                rank = max(len(symbol.initializer[0]) + 1, rank)
            else:
                rank = max(len(symbol.initializer), rank)
        else:
            if (symbol.hasattr('initializer') and isinstance(symbol.initializer, str) and
                    len(symbol.initializer) >= 1 and symbol.type_name == 'char' and not symbol.pointer):
                # char str[] "abc"; => 4 elements - 3 chars + null-byte
                rank = max(len(symbol.initializer) + 1, rank)

        return rank

    def arraySize(self, symbol):
        return self.size(symbol) * self.arrayRank(symbol)

    def array2Memory(self, symbol):
        """
        Memory layout for int a[2]; - array of 2 integers
            n:     a (2 bytes) = first element
            n + 2: 0 (2 bytes) = second element
        a will hold mempos = n, which is returned by this method

        Note for the cases: char str[] { "abc" }; and char str[] "abc"; str is an array of 4 elements (including
        null byte terminating the string). Thus, the length is 4.
        According to the C-reference manual: "By definition, the subscript
        operator [] is interpreted in such a way that "E1[E2]" is identical to *((E1) + (E2))"-
        This means that str[0] (which is "a") is identical to *((str) + (0)) = *str, thus str hold the address to "a"
        with the additional characters in the initializer string in ascending order in memory.

        str.mempos = n
        n    : "a"
        n + 1: "b"
        n + 2: "c"
        n + 3: "\x00" (null byte)

        We might come here when a struct member is of array type.
        Example:
            struct a { int a1; int a2; };
            struct b { struct a b1[10]; int b2; } b;
        symbol in this case is the first member of struct b (struct a b1[10])
        Here we are called from struct2Memory, we initialize memory to the symbol.size which is in bytes
        Note that below also cover if we have: struct a *b1[10] as a first member.

        We initiate memory using symbol.size, which is pre-calculated in bytes, hence type='byte' irrespectively
        of struct tag size or if pointer.

        If we have: struct a array[2]; it is covered in struct2Memory, not here
        """

        mempos = self.memory.init_mem(size=symbol.size, type='byte')

        if symbol.hasattr('initializer'):  # int a[2] { 1, 2 };
            init_values = []

            if isinstance(symbol.initializer, list):
                for ind, initializer in enumerate(symbol.initializer):
                    if isinstance(initializer, str):  # char *str[] { "abc", "def", 0 }; or char str[] { "abc" };
                        if symbol.pointer: # char *str[] { "abc", "def", 0 };
                            # Write string to memory, not char-by-char, memory.write will 0-terminate the string
                            init_values += [self.memory.write(symbol.initializer[ind], type='char', byte=True)]
                        else:  # char str[] { "abc" };
                            init_values = symbol.initializer[0] + "\x00"
                    else:
                        if symbol.pointer:
                            if symbol.type_name == 'char' and isinstance(initializer, int): # char *str[] { 0 };
                                init_values += [self.memory.write(symbol.initializer[ind], type='char', byte=True)]
                            else: # int *a[2] { 1, 2 };
                                init_values += [initializer]
                        else: # int a[2] { 1, 2 };
                            init_values += [initializer]
            elif isinstance(symbol.initializer, str):  # char str[] "abc";
                init_values = symbol.initializer + "\x00"
            else:  # No list, no str: int a[] 1; or int *a[] 1;
                init_values = [symbol.initializer]  # a is pointer with value/address set to 1


            array_pos = mempos
            for value in init_values:
                self.memory.update(array_pos, value,
                                   type=symbol.type_name if not symbol.pointer else 'pointer',
                                   byte=symbol.type_name in ['char'] and not symbol.pointer)
                array_pos += self.memory.sz_of[symbol.type_name if not symbol.pointer else 'pointer']

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

        rank = self.arrayRank(symbol)  # Assume we have a struct variable of array type, if not => rank = 1

        # Now loop all members in the struct, calculate the size if the struct
        struct_size = 0
        for i in range(rank):
            if symbol.declaration_list:  # Only loop if there is a declaration_list (list of struct members)
                for ind, member in enumerate(symbol.declaration_list):
                    if 'array' in member.ctx:  # member is an array: struct a { int m1[10]; } b;
                        member.rank = self.arrayRank(member)
                        member.size = self.arraySize(member)
                    elif 'id' in member.ctx:  # member is a variable: struct a { int m1; } b;
                        member.size = self.size(member)
                    elif 'struct_specifier' in member.ctx:  # member is a struct
                        if member.pointer:
                            if member.hasattr('subscript'):  # array of pointers to struct
                                """
                                Example:
                                    struct a { int a1[10]; int a2; };
                                    struct b { struct a b1[10]; int b2; } b;
                                The first member of struct b has a size of 10 pointers = 2 * 10 = 20 bytes
                                """
                                member.rank = self.arrayRank(member)
                                member.size = self.arraySize(member)
                            else:  # No subscript but a pointer to struct
                                """
                                Example:
                                    struct a { int a1[10]; int a2; };
                                    struct b { struct a *b1; int b2; } b;
                                The first member of struct b has a size of a pointer = 2 * 1 = 2 bytes
                                """
                                member.size = self.size(member)
                        elif member.struct_tag in self.struct_tags:  # No pointer
                            """
                            check if size of this struct_tag already exist
                            Example:
                              struct a { int a1; int a2; }; => struct 'a' has size 2 + 2 = 4 bytes
                              struct b { struct a b1; int b2; } b; => struct 'b' has size 4 + 2 = 6 bytes
                              struct c { struct a c1[10]; int c2 } c; => struct 'c' has size 4 * 10 + 2 = 42 bytes
                            """
                            member.size = self.struct_tags[member.struct_tag].struct_size
                            if member.hasattr('subscript'):
                                member.rank = self.arrayRank(member)
                                member.size = member.size * member.rank
                        else:  # No pointer and struct member not declared before
                            """
                            recursive call if there is no previous struct size for this struct_tag
                            Example:
                                struct b { struct a { int a1; int a2; } b1; int b2; } b;  => (2 + 2) + 2 = 6 bytes
                                struct b { struct a { int a1; int a2; } b1[10]; int b2; } b;  => (2 + 2) * 10 + 2 = 42
                            Note that for "b1[10]", the rank of 10 is managed in the recursive call to structSize.
                            Thus, we are not call arrayRank and calculate member.size here.
                            """
                            member.size = self.structSize(member)
                    else:
                        raise CCError(f'Unknown member combination for size calculations: {member} [{member.lineno}]')

                    struct_size += member.size

                    symbol.struct_size = struct_size
                    self.struct_tags[symbol.struct_tag] = symbol
            else:  # No declaration list
                """
                No declaration_list, but symbol is still of struct type
                Example:
                    struct a { int a1; int a2; };
                    struct a b;
                We are referring to "struct a" here. struct_size is  (2 + 2) = 4 bytes
                """
                if symbol.struct_tag in self.struct_tags:
                    struct_size += self.struct_tags[symbol.struct_tag].struct_size
                else:
                    raise CCError(f'Unknown struct tag: {symbol.struct_tag}')

        return struct_size

    def structMember2Memory(self, symbol):
        rank = self.arrayRank(symbol)

        # Now loop all members in the struct and add to memory
        for i in range(rank):
            for ind, member in enumerate(symbol.declaration_list):
                if 'array' in member.ctx:  # member is an array
                    """
                    Note that this member is of basic type: struct a { int m[10]; }; => array of 10 int's.
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

        return symbol

    def checkMemberTypes(self, symbol):
        # Check member type vs initializer type
        if symbol.declaration_list:
            decl_list = symbol.declaration_list
        else:
            if symbol.struct_tag not in self.struct_tags:
                raise CCError(f"{symbol.struct_tag} is not declared [{symbol.lineno}]")

            decl_list = self.struct_tags[symbol.struct_tag].declaration_list

        match = True
        for ind, initializer in enumerate(symbol.initializer):
            member = decl_list[ind % len(decl_list)]
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
            raise CCError(f"checkMemberTypes: member types does not match initializer "
                          f"types [{symbol.lineno}]")
        return match

    def checkMembersAndInitilizers(self, symbol):
        if symbol.struct_tag in self.struct_tags:
            nr_of_struct_members = len(self.struct_tags[symbol.struct_tag].declaration_list)
        else:
            nr_of_struct_members = len(symbol.declaration_list)

        nr_of_initializers = len(symbol.initializer)
        if nr_of_initializers % nr_of_struct_members != 0:
            raise CCError(f"nr of initializers ({nr_of_initializers}) does not match "
                          f"nr_of_struct members ({nr_of_struct_members}). ")

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
            symbol.rank = [max(subscript, symbol.subscript[0])]
        else:
            symbol.rank = subscript

        return nr_of_struct_members

    def structMembersAndInitializers2Memory(self, symbol):
        """
        First we loop all initializers to the array of struct variables, in this loop we only reserve
        a memory position if the member is a pointer. If not a pointer, we write the value from the
        initializer as the initial value for this member.

        All memory positions are saved into a list - mempos. The first element of mempos will be the
        memory position of the first element to the fist member of the array.

        In a second loop, we once more loop all initializers and take care of members which are pointers.
        Now we write the value of the initializer to memory and update the pointer to this memory
        position. This means that the values that is referenced from a member in the array comes
        in memory positions after the array.

        Example: struct a { char *id; int i; } c[] { "abc", 1, "def", 2 };
        c is an array of 2 elements, each element is of struct type with 2 members (id and i)
        => Memory layout:
        n   : n+8    (*id first element)
        n+2 : 1      (i first element)
        n+4 : n+12   (*id second element)
        n+6 : 2      (i second element)
        n+8 : "abc0" (first initializer, null-byte terminated
        n+12: "def0" (second initializer, null-byte terminated)

        Note that we also can refer to a previous declared struct:
            struct a { char *id; int i; };
            struct a c[] { "abc", 1, "def", 2 };
        If so, we lookup struct a and refer to this in 'sym' variable below to find out the struct members.
        We still need to refer to the variable c through 'symbol' as this variable holds the
        initializer list.
        """

        self.checkMemberTypes(symbol)
        nr_of_struct_members = self.checkMembersAndInitilizers(symbol)

        sym = symbol if symbol.declaration_list else self.struct_tags[symbol.struct_tag]
        mempos = []
        # First loop
        for ind, initializer in enumerate(symbol.initializer):
            struct_member = sym.declaration_list[ind % nr_of_struct_members]
            if struct_member.pointer:
                mempos += [self.memory.init_mem(type='pointer')]
            else:
                mempos += [self.memory.write(initializer, type=struct_member.type_name,
                                             byte=(struct_member.type_name == 'char'))]
            struct_member.mempos = mempos[ind]

        # Second loop
        for ind, initializer in enumerate(symbol.initializer):
            struct_member = sym.declaration_list[ind % nr_of_struct_members]
            if struct_member.pointer:
                pos = self.memory.write(initializer, type=struct_member.type_name,
                                        byte=(struct_member.type_name == 'char'))
                self.memory.update(mempos[ind], pos, 'pointer')
        return mempos

    def struct2Memory(self, symbol):
        if not symbol.hasattr('name'):
            return None

        """
        First allocate the struct variable in memory. Other struct members are allocate sequentially in memory
        after this variable. This is equivalent: a->m1 = 1; and (*a).m1 = 1
        
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

        if symbol.hasattr('initializer'):
            """
            As we know that nr of struct members and their type matches those of initializers
            we write the initializers to memory, saving their memory positions in a list (mempos).

            Note that we don't use structMember2Memory, as initializer syntax are restricted; they cannot
            contain structs or arrays, only basic types.
            Example:
                struct a { int a1; int a2; }
                struct b { struct a b1; int b2; } b { { 1, 2 }, 3 } <= nested initializers not allowed
                struct c { int c1[2]; int c2; } c { 1, 2, 3 )  <= 1, 2 initialize c1, but not possible 

            Note that this example is applicable: struct a { char *id; int i; } c { "abc", 1 };
            See comment for array above on this example.
            
            Another example:
                struct a { char *id; int i; };
                struct a c { "abc", 1 }
            We end up here for the second row of this example.
            Look up 'a' (struct_tag) in self.struct_tags.
            """
            mempos = self.structMembersAndInitializers2Memory(symbol)
            return mempos[0]
        else:  # struct variable is not array and have no initializers: struct a { int a1; int a2; } a;
            if 'array' not in symbol.ctx and symbol.declaration_list:
                """
                Note that the struct variable can be a pointer to a struct and have no declaration list, 
                Example: struct a *ap;
                """
                symbol = self.structMember2Memory(symbol)  # sets mempos for all members
                return symbol.declaration_list[0].mempos

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
                logger.debug(f"added constant {symbol.name} to symbol table")
            elif ctx == 'id':
                symbol.size = self.size(symbol)
                symbol.mempos = self.variable2Memory(symbol)
                self.variables[symbol.name] = symbol
                logger.debug(f"added variable {symbol.name} to symbol table")
            elif ctx == 'array':
                symbol.rank = self.arrayRank(symbol)
                symbol.size = self.arraySize(symbol)
                symbol.mempos = self.array2Memory(symbol)
                self.variables[symbol.name] = symbol
                logger.debug(f"added array {symbol.name} to symbol table")
            elif ctx == 'struct_specifier':
                symbol.struct_size = self.structSize(symbol)
                mempos = self.struct2Memory(symbol)
                if mempos is not None:
                    symbol.mempos = mempos
                    self.variables[symbol.name] = symbol
                self.structures[symbol.struct_tag] = symbol
                logger.debug(f"added struct {symbol.struct_tag} to symbol table")
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

    def add_locals(self, symbols):
        """
        Used for parameters to a function and for local variables to that function.
        These are stored into memory (in the call frame) and use the memory function as for external declarations.
        Locals (parameters + local variables) are not stored into the symbol table however.

        Actual values to parameters are treated as initializers.
        """
        if not isinstance(symbols, list):
            symbols = [symbols]

        for symbol in symbols:
            ctx = symbol.ctx[-1]

            if ctx == 'id':
                symbol.size = self.size(symbol)
                symbol.mempos = self.variable2Memory(symbol)
                name = symbol.name
            elif ctx == 'array':
                symbol.rank = self.arrayRank(symbol)
                symbol.size = self.arraySize(symbol)
                symbol.mempos = self.array2Memory(symbol)
                name = symbol.name
            elif ctx == 'struct_specifier':
                symbol.struct_size = self.structSize(symbol)
                mempos = self.struct2Memory(symbol)
                if mempos is not None:
                    symbol.mempos = mempos
                name = symbol.struct_tag
                self.locals[symbol.struct_tag] = symbol
            elif ctx == 'function':
                if 'declarator' in symbol.ctx:
                    symbol.size = self.size(symbol)
                    symbol.mempos = self.variable2Memory(symbol)

                name = symbol.name
            else:
                raise CCError(f"Unknown ctx: {ctx} ({symbol.lineno})")

            self.locals[name] = symbol
            logger.debug(f"added local variable/parameter {name} to symbol table")

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

    def get_ref(self, name):
        if name in self.locals:
            return self.locals[name]
        elif name in self.variables:
            return self.variables[name]
        elif name in self.structures:
            return self.structures[name]
        elif name in self.functions:
            return self.functions[name]
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
