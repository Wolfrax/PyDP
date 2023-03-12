import tkinter as tk
import asm
import sys
import glob


class GUI:
    def __init__(self, root, vm):
        self.vm = vm
        self.cur_line = vm.current_lineno()
        self.root = root
        self.root.title("PDP 11/40 VM")

        self.breaklines = [] # None

        # The program window
        self.src_title = tk.Label(self.root, text="Source")
        self.src_title.grid(row=0, column=0, padx=5, sticky='w')

        self.src_txt = tk.Text(self.root, wrap='none', borderwidth=2, relief="groove", width=100, height=20)
        ys = tk.Scrollbar(self.root, orient='vertical', command=self.src_txt.yview)
        xs = tk.Scrollbar(self.root, orient='horizontal', command=self.src_txt.xview)
        self.src_txt['yscrollcommand'] = ys.set
        self.src_txt['xscrollcommand'] = xs.set
        self.src_txt.insert(tk.END, vm.get_src())  # Add to end
        self.src_txt.grid(row=1, column=0, padx=5, sticky='wens')
        xs.grid(row=2, column=0, sticky='we')
        ys.grid(row=1, column=1, sticky='ns')
        self.src_txt.config(state=tk.DISABLED)  # Not editable

        self.src_txt.bind("<ButtonRelease-1>", self._on_click)
        self.src_txt.tag_configure("highlight", background="green", foreground="black")

        # Button for stepping
        self.step_btn = tk.Button(self.root, text="Step", command=lambda:  self.highlight(step=True))
        self.step_btn.grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)

        # Button for executing
        self.go_btn = tk.Button(self.root, text="Go", command=lambda:  self.highlight(step=False))
        self.go_btn.grid(row=3, column=0, sticky=tk.W, padx=75, pady=4)

        # Checkbutton for tracing
        self.trace_on = True
        self.trace_checkbtn = tk.BooleanVar(value=self.trace_on)
        self.check = tk.Checkbutton(root, text='Trace', command=self._trace, variable=self.trace_checkbtn)
        self.check.grid(row=3, column=0, sticky=tk.W, padx=125)

        self.trace_fn = "trace.txt"
        self.tracename = tk.StringVar(value=self.trace_fn)
        self.tracename.trace_add("write", self._trace_name)
        self.tracename_entry = tk.Entry(root, textvariable=self.tracename)
        self.tracename_entry.grid(row=3, column=0, sticky=tk.W, padx=200)

        self.verbose = False
        self.verbose_checkbtn = tk.BooleanVar(value=self.verbose)
        self.verbose_check = tk.Checkbutton(root, text='Verbose logging', command=self._verbose,
                                            variable=self.verbose_checkbtn)
        self.verbose_check.grid(row=3, column=0, sticky=tk.W, padx=300)

        # System status
        self.sys_status_title = tk.Label(self.root, text="System status")
        self.sys_status_title.grid(row=4, column=0, padx=5, sticky='w')
        self.sys_status_var = tk.StringVar()
        self.sys_status_var.set(vm.get_sys_status())
        self.sys_status = tk.Label(self.root, textvariable=self.sys_status_var, borderwidth=2, relief="groove",
                                   anchor='nw')
        self.sys_status.grid(row=5, column=0, padx=5, sticky='wens')

        # The symbols window
        self.symbols_title = tk.Label(self.root, text="Symbols")
        self.symbols_title.grid(row=0, column=3, padx=5, sticky='w')
        self.symbols = tk.Text(self.root, wrap='none', borderwidth=2, relief="groove", width=25, height=20)
        ys = tk.Scrollbar(self.root, orient='vertical', command=self.symbols.yview)
        xs = tk.Scrollbar(self.root, orient='horizontal', command=self.symbols.xview)
        self.symbols['yscrollcommand'] = ys.set
        self.symbols['xscrollcommand'] = xs.set
        self.symbols.insert(tk.END, self._symbols())
        self.symbols.grid(row=1, column=3, padx=5, sticky='wens')
        xs.grid(row=2, column=3, sticky='we')
        ys.grid(row=1, column=4, sticky='ns')
        self.symbols.config(state=tk.DISABLED)  # Not editable

        # Stack window
        self.stack_title = tk.Label(self.root, text="Stack")
        self.stack_title.grid(row=0, column=5, padx=5, sticky='w')
        self.stack_var = tk.StringVar()
        self.stack_var.set(vm.get_stack())
        self.stack = tk.Label(self.root, textvariable=self.stack_var, borderwidth=2, relief="groove",
                              anchor='nw', width=20, justify=tk.LEFT)
        self.stack.grid(row=1, column=5, columnspan=1, rowspan=1, padx=5, sticky='wens')

        # The processor status window
        self.ps_title = tk.Label(self.root, text="Processor status")
        self.ps_title.grid(row=6, column=0, padx=5, sticky='w')
        self.ps_header = tk.Label(self.root, text="N Z V C")
        self.ps_header.grid(row=7, column=0, padx=60, sticky='wn')
        self.ps_var = tk.StringVar()
        self.ps_var.set(str(vm.PSW))
        self.ps_lbl = tk.Label(self.root, textvariable=self.ps_var, borderwidth=2, relief="groove", anchor='nw')
        self.ps_lbl.grid(row=7, column=0, padx=5, sticky='wn')

        # The register window
        self.registers_title_lbl = tk.Label(self.root, text="Registers")
        self.registers_title_lbl.grid(row=9, column=0, padx=5, sticky='w')
        self.registers_var = tk.StringVar()
        self.registers_var.set(vm.get_registers())
        self.registers = tk.Label(self.root, textvariable=self.registers_var, borderwidth=2,
                                  relief="groove", anchor='nw', justify=tk.LEFT)
        self.registers.grid(row=10, column=0, padx=5, sticky='wens')

        # highlight start line with grey background
        self.src_txt.tag_configure("current_line", background="#e9e9e9")
        self.src_txt.tag_add("current_line", str(self.cur_line) + ".0", str(self.cur_line) + ".end")

    def _trace(self):
        self.trace_on = not self.trace_on

    def _trace_name(self, *name):
        self.trace_fn = self.tracename.get()

    def _verbose(self):
        self.verbose = not self.verbose
        self.vm.log_level(self.verbose)

    def _on_click(self, event):
        current_line = int(self.src_txt.index(tk.CURRENT).split(".")[0])
        if current_line in self.breaklines:
            self.src_txt.tag_remove("highlight", "insert linestart", "insert lineend")
            self.breaklines.remove(current_line)
        else:
            self.src_txt.tag_add("highlight", "insert linestart", "insert lineend")
            self.breaklines.append(current_line)

    def _update(self):
        self.src_txt.tag_add("current_line", str(self.cur_line) + ".0", str(self.cur_line) + ".end")
        self.src_txt.see(str(self.cur_line) + ".0")
        self.symbols.config(state=tk.NORMAL)  # Not editable
        self.symbols.delete("1.0", tk.END)
        self.symbols.insert(tk.END, self._symbols())
        self.symbols.config(state=tk.DISABLED)  # Not editable
        self.sys_status_var.set(vm.get_sys_status())
        self.registers_var.set(vm.get_registers())
        self.ps_var.set(str(vm.PSW))
        self.stack_var.set(vm.get_stack())
        self.root.update()

    def _symbols(self):
        return "Variables\n\n" + str(vm.variables) + "\n\n" + "Labels\n\n" + str(vm.named_labels)

    def highlight(self, step):
        if step:
            self.src_txt.tag_remove("current_line", str(self.cur_line) + ".0", str(self.cur_line) + ".end")
            vm.exec()
            self.cur_line = vm.current_lineno()
            self._update()
        else:
            while True:
                vm.exec()
                self.src_txt.tag_remove("current_line", str(self.cur_line) + ".0", str(self.cur_line) + ".end")
                self.cur_line = vm.current_lineno()
                if self.cur_line in self.breaklines:
                    self.src_txt.tag_remove("current_line", str(self.cur_line) + ".0", str(self.cur_line) + ".end")
                    self._update()
                    if self.trace_on:
                        vm.dump_trace(trace_fn=self.trace_fn)
                    break


if __name__ == '__main__':
    if sys.argv[1] == 'as2':
        cmd = sys.argv[1] + ' ' + ''.join(elem + ' ' for elem in sys.argv[2:])
    else:
        fnList = sorted(glob.glob(sys.argv[2]))
        cmd = sys.argv[1] + ' ' + ''.join(elem + ' ' for elem in fnList)

    root = tk.Tk()
    vm = asm.VM(cmd)
    vm_gui = GUI(root, vm)
    root.mainloop()
