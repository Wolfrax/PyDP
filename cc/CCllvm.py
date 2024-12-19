from llvmlite import ir
import llvmlite.binding as llvm
from llvmlite.binding import create_mcjit_compiler


class CCllvm(object):
    def __init__(self):
        """
        Create an ExecutionEngine suitable for JIT code generation on
        the host CPU.  The engine is reusable for an arbitrary number of
        modules.
        """

        # Create a target machine representing the host
        self.target = llvm.Target.from_default_triple()
        self.target_machine = self.target.create_target_machine()
        # And an execution engine with an empty backing module
        self.backing_mod = llvm.parse_assembly("")
        self.engine = llvm.create_mcjit_compiler(self.backing_mod, self.target_machine)


    def compile_ir(self, llvm_ir):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """

        # Create a LLVM module object from the IR
        mod = llvm.parse_assembly(llvm_ir)
        mod.verify()
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod

if __name__ == '__main__':
