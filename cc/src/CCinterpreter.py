from cc.src.CCMemory import Memory
from cc.src.CCError import CCError


import argparse
import re

class CallFrame:
    def __init__(self, compiler, function):
        self.function = function
        self.sp = compiler.interpreter.memory.sp

        compiler.symbols.add_locals(self.function.parameters)
        for lvar in self.function.statements.declaration_list:
            compiler.symbols.add_locals(lvar.decl())

        for stmt in function.statements.statement_list:
            stmt.eval()


class CCinterpreter:
    def __init__(self, compiler=None, args=None):
        if args:
            parser = argparse.ArgumentParser()
            # https://man.cat-v.org/unix-6th/1/cc
            parser.add_argument('-c', action='store_true')
            parser.add_argument('-p', action='store_true')
            parser.add_argument('-f', action='store_true')
            parser.add_argument('-O', action='store_true')
            parser.add_argument('-S', action='store_true')
            parser.add_argument('-P', action='store_true')

            # See cc.c, not in man
            parser.add_argument('-2', dest='two', action='store_true')
            parser.add_argument('-t', action='store_true')

            parser.add_argument('file', nargs='?')

            args = parser.parse_args(args.split())
            file = args.file if args.file else ''
            if not file:
                raise CCError("No file specified")

            #file = re.split(r'\[(.*?)]', args.file)  # args.file = "c[0123].c" => ['c', '0123', '.c']

            self.args = {'c': args.c, 'p': args.p, 'f': args.f, 'O': args.O, 'S': args.S,
                         'P': args.P, '2': args.two, 't': args.t, 'file': file}

            self.argv = ['cc']
            for arg in self.args:
                if self.args[arg]:
                    self.argv += [self.args[arg]] if arg == 'file' else ['-' + arg]

            self.argc = len(self.argv)
        else:
            self.argv = None
            self.argc = None

        self.compiler = compiler
        self.memory = Memory()

    def exec(self):
        if 'main' in self.compiler.symbols.functions:
            main = self.compiler.symbols.functions['main']
        else:
            raise CCError(f"No main function")

        for par in main.parameters:
            if par.type_name == 'int':
                par.initializer = self.argc
            elif par.type_name == 'char' and par.pointer:
                par.initializer = self.argv
            else:
                raise CCError(f"Unknown argument type: {par.type_name}")

        if (self.argc is None and self.argv is not None) or (self.argc is not None and self.argv is None):
            raise CCError("Invalid argument combination for main function")

        callframe = CallFrame(self.compiler, main)

