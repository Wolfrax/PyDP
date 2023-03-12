# Introduction
_Once upon a time..._ a 16-bit mini-computer architecture by Digital Equipment Cooperation existed. 
It was named **PDP-11**.

Beside its commercial success, it had impact for the future as it was the target for **UNIX** operating system.
Although UNIX had been developed in its initial versions on predecessors of PDP-11, the version 6 of UNIX is probably 
fundamental for the coming evolution of UNIX and its branches.

This is not the place to describe the history of UNIX.

At the first job I had as a professional computer engineer, by chance I saved some old manuals that were going to the
garbage bin. No one cared, this was at a hospital in Sweden, so the interest were on medicine. Of course.
So, I saved the manuals and stored them with the aim of reading them. The years went by, I had almost forgotten about
them (but visible in my bookshelf).

During the autumn 2020, at a work meeting winning in boredom, I started to flick through the manuals and got the 
idea: Let's use them!

In parallel to this, by coincidence (at least I think so, but coincidence is seldom as coincidental as it occurs) I
found some source code and other documents for UNIX v6 on websites. Not very hard to find, but here is a 
[link](https://github.com/memnoth/unix-v6).

So, I had access to the user space source code and an architectural description of the target system for the software.
In theory, I should be able to simulate the PDP-11 architecture and have the source code running there.

After all, this was code made for a 16-bit computer in the beginning of the 1970-ies, how hard could that be (I naively
thought)? As it turned out...more complicated than anticipated.

The project grow organically, as I learned more along the way. If I had known, what I know now, the structure of the
code I produced would look differently. At least I think so.

But as this is a hobby project, and not for any product usage in any sense. I will not go back and redo.

So, it needs to be stressed, if some choices of implementation looks strange...yes, it is and can be probably be made
much better.

My implementation language of choice was easy - Python! Of course. I am reasonbly comfortable with Python and its 
ecosystem. I have no need to optimize the code and it allowed me to go directly to the point what I wanted to do.

My starting point was the assembler for PDP-11/40, which for UNIX v6 is written in PDP-11 assembler syntax.
Starting here, I quickly realized that the assembler source code was hardly not commented at all, and thus difficult to 
understand at all. And I could not find any documentation for the assmembler (besides how to call for it in the UNIX v6
shell).

I can't claim that I understand the code in all details now either, but some I have learned. And at this stage, I have
a Python program that can read, parse and execute the assembler code and produce an executable file that I believe is
valid. More on that to come in this documentation later on.
