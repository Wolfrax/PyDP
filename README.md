# PyDP

This is the PyDP repository. It is under implementation.

It is implemented under Linux and tested only there.

The first step is to parse and execute the UNIX v6 assembler, this now looks Ok.
The Python implementation can parse all assembler files implementing the as-assembler
used in Unix V6 for PDP 11/40. The outcome is an a.out file, following the a.out file
format. The main intention is to implement enough to manage the assembler files, 
it is however possible to implement at least simple test files, run these through 
the Python implementation and produce an a.out file.

There is a simple UI connected to the implementation with possibilities to set 
breakpoints and produce trace files. The implementation is possible to execute from
command line also. You can do:

    python asm_gui.py as "as1?.s"

Note that the Unix V6 assembler have hardcoded the second pass to call for "/lib/as2"
with parameter. To manage this, the file `as2.bash` should be soft-linked to the call.

Documentation will be improved.

The next step is to implement an interpreter for a.out. This is not available yet.
When done with this step the a.out-interpreter should be able to assemble any Unix V6 
assembler source file.