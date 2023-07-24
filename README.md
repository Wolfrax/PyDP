# PyDP

This is the PyDP repository.

Currently, it consists of these parts:

* An interpreter of the UNIX v6 assembler. 

It will parse and execute all source code of the assembler, therefore making it possible to bootstrap UNIX v6 assembler
code. It will produce a bit-exact binary file in aout format if successful.
As the assembler is 2-pass, there are 2 parts: `as1?.s` and `as2?.s` source files. 

There is a command line interface, for example do `python asm.py as as1?.s`

* A simple GUI

It is possible to debug the assembler; setting breakpoints, execute, single step, inspect stack, registers and the
processor status word etc.

To start, use the bash-script in the gui directory: `$ sh start.bash`.
It is implemented using react and Vite, to rebuild changed components do `$ npm run build`

* An interpreter of files in aout format

This builds on the assembler interpreter implement and will execute a binary file in valid aout format.
Do for example, `$ python aout_exec.py as as2?.s`, which will execute the binary file `as` with `as2?.s` as input.

* A dump utility

Will dump information about a binary file in aout format.
For example, `aout_dump.py --file ./src/a.out`

For more details, refer to `as_annotations.md` in the asm/doc directory.
