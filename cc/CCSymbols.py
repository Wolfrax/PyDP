import pprint
from CC import CCError

class CCSymbols:
    def __init__(self, memory):
        self.constants = {}
        self.variables = {}
        self.structures = {}
        self.unions = {}
        self.functions = {}
        self.memory = memory

    def add(self, symbols):
        for symbol in symbols:
            ctx = symbol.ctx[-1]

            if ctx == 'const':
                if symbol.name in self.constants:
                    raise CCError(f"Duplicate constant name: {symbol.name ({symbol.lineno})}")

                # const will not occupy any memory
                self.constants[symbol.name] = symbol
            elif ctx == 'struct_specifier':
                if symbol.struct_tag != '':
                    if symbol.struct_tag in self.structures:
                        raise CCError(f"Duplicate struct tag: {symbol.struct_tag} ({symbol.lineno})")

                    self.structures[symbol.struct_tag] = symbol
                else:  # No struct tag, treat members as unions.
                    for decl in symbol.declaration_list:
                        if decl.name in self.unions:
                            raise CCError(f"Duplicate union member name: {decl.name} ({symbol.lineno})")

                        self.unions[decl.name] = decl
            elif ctx == 'id':
                # Note that no check is made of duplicate names, an identifier might be declared
                # several times. the last occurrence will overwrite previous entries in symbol table
                self.variables[symbol.name] = symbol

                # For now, assume int => need to consider char, float, double
                if symbol.hasattr('initializer'):
                    mempos = self.memory.write(symbol.initializer)

            elif ctx == 'function':
                if symbol.name in self.functions:
                    raise CCError(f"Duplicate function name: {symbol.name} ({symbol.lineno})")

                self.functions[symbol.name] = symbol

    def get(self, name):
        if name in self.constants:
            return self.constants[name].value
        elif name in self.variables:
            return self.variables[name].value
        elif name in self.structures:
            return self.structures[name].value
        elif name in self.unions:
            return self.unions[name].value
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
        print('=== no name structures ===')
        pprint.pprint(self.unions)
        print('=== functions ===')
        pprint.pprint(self.functions)
