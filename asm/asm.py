import as_parse as prs
import os
import fnmatch
from collections import deque
import logging
import atexit
import sys
import glob
import yaml


class Memory:
    def __init__(self, size):
        self.size = size * 1024
        self.memory = [0] * self.size
        self.brk_addr = 0
        self.sp = 0
        self.counters = {'read': 0, 'write': 0}

    def __len__(self):
        return len(self.memory)

    def init(self, data):
        assert len(data) <= self.size, "Initialization of memory out of bound"
        self.memory[0:len(data)] = data

    def write(self, pos, value, byte=False):
        assert pos + 1 < len(self.memory), "Memory, write outside memory {}".format(pos)
        assert isinstance(value, int), "Memory, value is not int: {}".format(value)
        # >>> (2496065).to_bytes(3, 'little')
        # b'A\x16&'
        # >>> s[0]
        # 65
        # >>> s[1]
        # 22
        # >>> s[2]
        # 38
        # >>> s[2] << 16 | s[1] << 8 | s[0]
        # 2496065

        self.counters['write'] += 1

        if value <= 0xFF:
            if byte:
                self.memory[pos] = value
                return 1
            else:
                self.memory[pos] = value
                self.memory[pos + 1] = 0
                return 2
        else:
            length = 0
            v = value
            while v != 0:
                length += 1
                v >>= 8
            if length % 2 != 0:
                # Pad with 0 to make it even (store on word boundary), most significant byte first (little endian)
                self.memory[pos] = 0
                pos += 1
                ret_length = length + 1
            else:
                ret_length = length

            value_bytes = value.to_bytes(length, 'little')

            for byte_pos in range(length):
                self.memory[pos] = value_bytes[byte_pos]
                pos += 1

            return ret_length

    def read(self, pos, nr=2):
        assert pos < len(self.memory) and pos >= 0, "Read outside memory {}".format(pos)

        self.counters['read'] += 1

        ret_val = 0
        for i in range(nr - 1, -1, -1):
            mem_val = self.memory[pos + i]
            ret_val = ret_val << 8 | mem_val

        return ret_val

    def get_counters(self):
        return self.counters['read'], self.counters['write']


class SymbolTable:
    def __init__(self):
        self.table = {}

    def __str__(self):
        result = ""
        for key, elem in self.table.items():
            result += "{}: \t\t{}\n".format(key, elem)
        return result[:-1]

    def __iter__(self):
        return iter(self.table)

    def items(self):
        return self.table.items()

    def add(self, key, val):
        if key.isdigit():
            if key in self.table:
                self.table[key].append(val)
            else:
                self.table[key] = [val]
        else:
            self.table[key] = val

    def get(self, key):
        if key in self.table:
            return self.table[key]
        else:
            return None

    def get_key(self, val):
        return list(self.table.keys())[list(self.table.values()).index(val)]

    def sort(self):
        for lbl in self.table:
            self.table[lbl] = sorted(self.table[lbl])


class PSW:
    def __init__(self):
        self.N = 0
        self.Z = 0
        self.V = 0
        self.C = 0

    def __str__(self):
        return "N: " + str(self.N) + "\tZ: " + str(self.Z) + "\tV: " + str(self.V) + "\tC: " + str(self.C)

    def dump(self):
        return "N: " + str(self.N) + " Z: " + str(self.Z) + " V: " + str(self.V) + " C: " + str(self.C)

    def set(self, PSW):
        self.N = PSW['N']
        self.Z = PSW['Z']
        self.V = PSW['V']
        self.C = PSW['C']

    def get(self):
        return {'N': self.N, 'Z': self.Z, 'V': self.V, 'C': self.C}


class VM:
    def __init__(self, cmd_line, exec=False, config_file="config.yml"):
        self.logger = logging.getLogger('pyPDP')
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.logger.info('Start')

        # --> Pure VM initialization
        try:
            with open(config_file, "rb") as cfg_file:
                self.config = yaml.safe_load(cfg_file)
        except OSError as e:
            self.logger.info(f"{config_file} not found in {os.getcwd()}")
            self.config = {'work_dir': ".", 'out_dir': "."}

        os.chdir(self.config['work_dir'])

        self.mem = Memory(64)
        self.register = {'r0': 0, 'r1': 0, 'r2': 0, 'r3': 0, 'r4': 0, 'r5': 0, 'sp': 0o177776, 'pc': 0}
        self.PSW = PSW()

        self.prg_start_address = 0
        self.register['pc'] = self.prg_start_address
        self.exit = False

        self.variables = SymbolTable()
        self.named_labels = SymbolTable()
        self.numeric_labels = SymbolTable()
        self.prg = None

        self.location_counter = self.prg_start_address
        self.variables.add('.', self.location_counter)
        self.variables.add('..', 0)

        self.sys_sig_status = {}
        self.sig_list = ['NA',
                         'hangup',
                         'interrupt',
                         'quit',
                         'illegal instruction',
                         'trace trap',
                         'IOT instruction',
                         'EMT instruction',
                         'floating point exception',
                         'kill',
                         'bus error',
                         'segmentation violation',
                         'bad argument to system call',
                         'write on a pipe with no one to read it']

        self.instr_pre_traceQ = deque(maxlen=1000000)
        self.instr_traceQ = deque(maxlen=1000000)

        self.files = {1: 'stdout'}
        self.counters = {'instr executed': 0}

        # <-- Pure VM initialization

        # --> Command line parsing
        if cmd_line[1] not in ['as', 'as2']:
            raise Exception("Wrong command: {}".format(cmd_line[1]))
        else:
            # This is when we assemble from source
            if cmd_line[1] == 'as2':
                #
                # sys exec /lib/as2 /lib/as2 /tmp/atm1e /tmp/atm2e /tmp/atm3f
                #
                # arguments from cmd_line[2:] can be of the following forms:
                # 1. Not ending with single wild card, for example ["/tmp/atm1a", "/tmp/atm2a", "/tmp/atm3a"]
                # 2. Ending with single wild card: ["/tmp/atm1?", "/tmp/atm2?", "/tmp/atm3?"]
                # In case 2 we take all files matching the wild card, create a list and select the last file
                args = [cmd_line[1]]
                for elem in cmd_line[2:]:
                    if elem[-1] == '?':
                        files = glob.glob(elem)
                        if files:
                            file = sorted(files)[-1]  # Last file matching the wild card
                        else: # files mathing elem not found, issue warning but continue.
                            self.logger.warning(f"WARNING {elem} not found! Will continue...")
                            file =''
                    else:
                        file = elem  # No wild card, use as is
                    args.append(file)
            else:  # as1
                if cmd_line[2] == '-':
                    glob_dir = cmd_line[2] + ' '
                    files = cmd_line[3]
                else:
                    glob_dir = ''
                    files = cmd_line[2]

                fnList = sorted(glob.glob(files))
                args = [cmd_line[1]] + fnList

            self.logger.info('Start {}'.format(args))

            asm_files = 'as1?.s' if args[0] == 'as' else 'as2?.s'

            asm_list = []
            for filename in os.listdir("."):
                if fnmatch.fnmatch(filename, asm_files):
                    asm_list.append(filename)

            asm_list.sort()

            if not exec:  # Parsing and interpreting
                self.src = ""
                for filename in asm_list:
                    with open(filename, 'r') as f:
                        self.src += f.read()

                self.prg = prs.parse(self.src)

                self.text_segment_start = self.location_counter
                self.assemble_segment__('.text')

                self.data_segment_start = self.location_counter
                self.variables.add('.', self.location_counter)
                self.assemble_segment__('.data')

                self.bss_segment_start = self.location_counter
                self.variables.add('.', self.location_counter)
                self.assemble_segment__('.bss')

                self.numeric_labels.sort()
                self.resolve()

                self.prg_index_LUT = {}

            stack_mempos = len(self.mem) - 1024  # Program stack i maximum 1k of memory

            # Push all arguments on internal stack in reverse order
            for arg in reversed(args):
                arg += '\x00'  # all arguments on stack need to be terminated with 0
                nr = 0
                for ch in arg:
                    nr += self.mem.write(stack_mempos + nr, ord(ch), byte=True)
                self.stack_push(stack_mempos)
                stack_mempos += nr

            self.stack_push(len(args))

            atexit.register(self.patch_aout)
            atexit.register(self.stats)
            atexit.register(self.dump_trace)

    def memory(self, data):
        self.mem.init(data)

    def log_level(self, verbose):
        logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)

    def dump_trace(self, trace_fn="trace.txt"):
        self.logger.info(f"Dumping trace to {trace_fn}")
        with open(trace_fn, "w") as f:
            header = "{:<8}{:<30}{:<15}{:<15}{:<75}{:<25}".format("lineno", "keyword", "src", "dst",
                                                                  "post instr register values",
                                                                  "post instr PSW")
            f.write(header + "\n")
            f.write("="*162 + "\n\n")
            for q_item in self.instr_traceQ:
                f.write(q_item + "\n")

    def trace(self, instr):
        if instr:
            self.instr_pre_traceQ.append(instr.dump(self))

    def post_trace(self):
        for q_item in list(self.instr_pre_traceQ):
            pre_dump = self.instr_pre_traceQ.popleft()
            dump_str ="{}{:<75}{:<25}".format(pre_dump, self.dump_registers(), self.PSW.dump())
            self.instr_traceQ.append(dump_str)

    def assemble_segment__(self, segment_type):
        assemble = segment_type == '.text'  # By default we always start with a .text segment
        for instr in self.prg.instructions:
            if instr is None: continue

            if instr.type() == "PseudoOpStmt":
                if instr.get() in ['.text', '.data', '.bss']:
                    assemble = instr.expr == segment_type
                    if self.location_counter % 2 == 1:  # Odd, adjust so it is even
                        self.location_counter += 1
                elif instr.get() == '.even':
                    if assemble and self.location_counter % 2 == 1:  # Odd, adjust so it is even
                         self.location_counter += 1
                         self.variables.add(".", self.location_counter)
                elif instr.get() == '.if':
                    expr = instr.operands.eval(self)
                    if expr == 0:
                        old_assemble_val = assemble
                        assemble = False
                elif instr.get() == '.endif':
                    assemble = old_assemble_val

            if assemble:
                loc = self.location_counter
                instr.assemble(self)

    def resolve(self):
        for instr in self.prg.instructions:
            if instr is None: continue
            instr.resolve(self)

    def stack_push(self, value):
        self.register['sp'] -= 2
        self.mem.write(self.register['sp'], value)

    def stack_pop(self):
        val = self.mem.read(self.register['sp'], 2)
        self.register['sp'] += 2
        return val

    def stack_empty(self):
        return self.register['sp'] == len(self.mem)

    def stack_len(self):
        if self.stack_empty():
            return 0
        else:
            return abs(self.register['sp'] - 1) / 2

    def stack_read(self):
        if self.stack_empty():
            return []
        else:
            res = []
            ind = self.register['sp']
            while ind < len(self.mem):
                res.append(self.mem.read(ind, 2))
                ind += 2
            return res

    def stack_read_addr(self):
        if self.stack_empty():
            return []
        else:
            res = []
            ind = self.register['sp']
            while ind < len(self.mem):
                res.append(ind)
                ind += 2
            return res

    def get_stack(self):
        result = ""
        stack = self.stack_read()
        addr = self.stack_read_addr()
        if stack:
            ind = 0
            for elem in stack:
                result += str(elem) + "\t(" + str(addr[ind]) + ")" + "\n"
                ind += 1
            return result[:-1]
        else:
            return result

    def incr_PC(self, incr=1):
        self.register['pc'] += (2 * incr)
        return self.register['pc']

    def set_PC(self, addr):
        self.register['pc'] = addr

    def get_PC(self):
        return self.register['pc']

    def get_address_PC(self):
        return self.register['pc'] + self.prg_start_address

    def get_statement(self):
        instr_loc = self.mem.read(self.register['pc'], 2)
        instr = self.prg.instructions[instr_loc]
        return instr

    def get_statement_index(self):
        return self.mem.read(self.register['pc'], 2)

    def get_instruction_indexes(self, locations):
        ret_val = []
        for loc in locations:
            if loc in self.prg_index_LUT:
                ret_val.append(self.prg_index_LUT[loc])
            else:
                for instr in self.prg.instructions:
                    if instr is None: continue
                    if instr.loc == loc:
                        ret_val.append(self.prg.instructions.index(instr))
                        self.prg_index_LUT[loc] = self.prg.instructions.index(instr)
                        break
        return ret_val

    def get_index(self, instr):
        return self.prg.instructions.index(instr) + self.prg_start_address

    def get_src(self):
        return self.src

    def current_lineno(self):
        instr_loc = self.mem.read(self.get_PC(), 2)
        return self.prg.instructions[instr_loc].lineno

    def get_registers(self):
        result = ""
        for k, v in self.register.items():
            result += k + ": " + str(v) + " \t"
        return result[:-1]

    def dump_registers(self):
        result = ""
        for k, v in self.register.items():
            result += str(k) + ": " + str(v) + " "
        return result

    def get_gui_status(self):
        result = ""
        for k, v in self.sys_sig_status.items():
            result += v + k + "\n"
        return result[:-1]  # Ignore last '\n'

    def exec(self):
        # This routine is used when we have parsed files and have all instructions in a syntax tree (prg attribute)
        instr_loc = self.mem.read(self.get_PC(), 2)
        instr = self.prg.instructions[instr_loc]
        self.trace(instr)
        instr.exec(self)
        self.post_trace()
        self.counters['instr executed'] += 1

    def patch_aout(self):
        # This is a cludge...
        # a.out format expects the first 2 bytes in the file to have a 'magic number', this number can take 3 values:
        #
        # 0o407 (0x107): If the magic number (word 0) is 407, it indicates that the text segment is not to be write-
        #      protected and shared, so the data segment is immediately contiguous with the text segment.
        #
        # 0o410 (0x108): If the magic number is 410, the data segment begins at the first 0 mod 8K byte
        #      boundary following the text segment, and the text segment is not writable by the program;
        #      if other processes are executing the same file, they will share the text segment.
        #
        # 0o411 (0x109): If the magic number is 411, the text segment is again pure, writeprotected, and shared,
        #      and moreover instruction and data space are separated; the text and data segment both begin at
        #      location 0.
        #
        # In the assembler, this is fixed in pass 2, by using the label "txtmagic", defined as (see as28s):
        #   txtmagic:
        # 	    br	.+20
        #
        # The instruction 'br' is coded as 0o000400 + offset => 0o000420. This would branch 16 bytes forward, skipping
        # the header in the file (which is 16 bytes).
        # Somewhere in the assembler (have not figured out where yet), this is however modified to one of the 3 values.
        # If an a.out does not start with the magic number, the image will be considered as broken by the OS.
        #
        # In the current implementation, the memory position referred by label txtmagic contains the value of an index
        # where the instruction is stored, not the machine code value. Thus, the a.out file generated will not have
        # the correct magic value. This is fixed in this patch-method, by simply hardcode the value 0o407 in the first
        # 2 bytes, in hex with little endian: "07 01"

        txtmagic = "0701"  # 0o407/0x107 in little endian order
        try:
            with open("a.out", "r+b") as f:
                self.logger.debug('Patching a.out with magic number')
                f.write(bytes.fromhex(txtmagic))
        except FileNotFoundError:
            pass

    def stats(self):
        mem_reads, mem_writes = self.mem.get_counters()
        self.logger.info(f"No of memory accesses: {(mem_reads + mem_writes):,} "
                         f"(read: {mem_reads:,}, write {mem_writes:,})")
        self.logger.info(f"No of instructions executed: {self.counters['instr executed']:,}")


if __name__ == '__main__':
    vm = VM(cmd_line=sys.argv)

    while True:
        vm.exec()