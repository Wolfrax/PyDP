
class InstrLUT:
    def __init__(self):
        Op = {}

        self.Masks = {
            0o170000: [
                0o110000, 0o010000,   # MOVB, MOV
                0o120000, 0o020000,   # CMPB, CMP
                0o130000, 0o030000,   # BITB, BIT
                0o140000, 0o040000,   # BICB, BIC
                0o150000, 0o050000,   # BISB, BIS
                          0o060000,   # ADD
                0o160000              # SUB
            ],

            0o177000: [
                          0o004000,   # JSR
                          0o070000,   # MUL
                          0o071000,   # DIV
                          0o072000,   # ASH
                          0o073000,   # ASHC
                          0o074000,   # XOR
                          0o077000    # SOB
            ],

            0o177700: [
                0o105000, 0o005000,   # CLRB, CLR
                0o105100, 0o005100,   # COMB, COM
                0o105200, 0o005200,   # INCB, INC
                0o105300, 0o005300,   # DECB, DEC
                0o105400, 0o005400,   # NEGB, NEG
                0o105500, 0o005500,   # ADCB, ADC
                0o005600, 0o005600,   # SBCB, SBC
                0o105700, 0o005700,   # TSTB, TST
                0o106000, 0o006000,   # RORB, ROR
                0o106100, 0o006100,   # ROLB, ROL
                0o106200, 0o006200,   # ASRB, ASR
                0o106300, 0o006300,   # ASLB, ASL
                          0o006700,   # SXT
                          0o000100,   # JMP
                          0o000300,   # SWAB
                          0o006400,   # MARK
                          0o006500,   # MFPI
                          0o006600    # MTPI
            ],

            0o177770: [
                          0o000200    # RTS
            ],

            0o177400: [
                          0o000400,   # BR
                          0o001000,   # BNE
                          0o001400,   # BEQ
                          0o002000,   # BGE
                          0o002400,   # BLT
                          0o003000,   # BGT
                          0o003400,   # BLE
                0o100000,             # BPL
                0o100400,             # BMI
                0o101000,             # BHI
                0o101400,             # BLOS
                0o102000,             # BVC
                0o102400,             # BVS
                0o103000,             # BCC
                0o103400,             # BCS
                0o104400              # SYS/TRAP
            ],

            0o000277: [
                          0o000240,   # NOP
                          0o000241,   # CLC
                          0o000242,   # CLV
                          0o000244,   # CLZ
                          0o000250,   # CLN
                          0o000261,   # SEC
                          0o000262,   # SEV
                          0o000264,   # SEZ
                          0o000270,   # SEN
                          0o000277,   # SCC
                          0o000257    # CCC
            ],

            0o000007: [
                          0o000000,   # HALT
                          0o000001,   # WAIT
                          0o000002,   # RTI
                          0o000003,   # BPT
                          0o000004,   # IOT
                          0o000005,   # RESET
                          0o000006,   # RTT
            ]
        }

        self.singleOp = {
            0o105000: 'clrb',  #
            0o005000: 'clr',   #
            0o105100: 'comb',  #
            0o005100: 'com',   #
            0o105200: 'incb',  #
            0o005200: 'inc',   #
            0o105300: 'decb',  #
            0o005300: 'dec',   #
            0o105400: 'negb',  #
            0o005400: 'neg',   #
            0o105700: 'tstb',  #
            0o005700: 'tst',   #
            0o106200: 'asrb',  #
            0o006200: 'asr',   #
            0o106300: 'aslb',  #
            0o006300: 'asl',   #
            0o106000: 'rorb',  #
            0o006000: 'ror',   #
            0o106100: 'rolb',  #
            0o006100: 'rol',   #
            0o000300: 'swab',  #
            0o105500: 'adcb',  #
            0o005500: 'adc',   #
            0o105600: 'sbcb',  #
            0o005600: 'sbc',   #
            0o006700: 'sxt'    #
        }

        Op.update(self.singleOp)

        self.doubleOp = {
            0o110000: 'movb',  #
            0o010000: 'mov',   #
            0o120000: 'cmpb',  #
            0o020000: 'cmp',   #
            0o060000: 'add',   #
            0o160000: 'sub',   #
            0o130000: 'bitb',  #
            0o030000: 'bit',   #
            0o140000: 'bicb',  #
            0o040000: 'bic',   #
            0o150000: 'bisb',  #
            0o050000: 'bis',   #
            0o070000: 'mul',   #
            0o071000: 'div',   #
            0o072000: 'ash',   #
            0o073000: 'ashc',  #
            0o074000: 'xor'    #
        }
        Op.update(self.doubleOp)

        self.branchOp = {
            0o000400: 'br',    #
            0o001000: 'bne',   #
            0o001400: 'beq',   #
            0o100000: 'bpl',   #
            0o100400: 'bmi',   #
            0o102000: 'bvc',   #
            0o102400: 'bvs',   #
            0o103000: 'bcc',   # bhis
            0o103400: 'bcs',   # blo
            0o002000: 'bge',   #
            0o002400: 'blt',   #
            0o003000: 'bgt',   #
            0o003400: 'ble',   #
            0o101000: 'bhi',   #
            0o101400: 'blos',  #
            0o077000: 'sob',   #
        }
        Op.update(self.branchOp)

        self.sysOp = {
            0o104400: 'sys'    # TRAP
        }
        Op.update(self.sysOp)

        self.prgCntrlOp = {
            0o000100: 'jmp',   #
            0o004000: 'jsr',   #
            0o000200: 'rts',   #
            0o006400: 'mark',  #
            0o000003: 'bpt',   #
            0o000004: 'iot',   #
            0o000002: 'rti',   #
            0o000006: 'rtt',   #
        }
        Op.update(self.prgCntrlOp)

        self.miscOp = {
            0o000000: 'halt',  #
            0o000001: 'wait',  #
            0o000005: 'reset', #
            0o006500: 'mfpi',  #
            0o006600: 'mtpi',  #
            0o000241: 'clc',   #
            0o000242: 'clv',   #
            0o000244: 'clz',   #
            0o000250: 'cln',   #
            0o000261: 'sec',   #
            0o000262: 'sev',   #
            0o000264: 'sez',   #
            0o000270: 'sen',   #
            0o000277: 'scc',   #
            0o000257: 'ccc',   #
            0o000240: 'nop'    #
        }
        Op.update(self.miscOp)
        self.Op = dict(sorted(Op.items()))

        self.syscall = {
            0o0000000: 'indir',
            0o0000001: 'exit',
            0o0000002: 'fork',
            0o0000003: 'read',
            0o0000004: 'write',
            0o0000005: 'open',
            0o0000006: 'close',
            0o0000007: 'wait',
            0o0000010: 'creat',
            0o0000011: 'link',
            0o0000012: 'unlink',
            0o0000013: 'exec',
            0o0000014: 'chdir',
            0o0000015: 'time',
            0o0000016: 'makdir',  # mknod
            0o0000017: 'chmod',
            0o0000020: 'chown',
            0o0000021: 'break',
            0o0000022: 'stat',
            0o0000023: 'seek',
            0o0000024: 'tell',    # getpid
            0o0000025: 'mount',
            0o0000026: 'umount',
            0o0000027: 'setuid',
            0o0000030: 'getuid',
            0o0000031: 'stime',
            0o0000034: 'fstat',
            0o0000036: 'mdate',   # ??, not documented
            0o0000037: 'stty',
            0o0000040: 'gtty',
            0o0000042: 'nice',
            0o0000060: 'signal'
        }

    def isSingle(self, op):
        return op in self.singleOp.values()

    def isDouble(self, op):
        return op in self.doubleOp.values()

    def isBranch(self, op):
        return op in self.branchOp.values()

    def isSys(self, op):
        return op in self.sysOp.values()

    def isPrgCntrl(self, op):
        return op in self.prgCntrlOp.values()

    def isMisc(self, op):
        return op in self.miscOp.values()

    def get(self, word):
        for mask, ops in self.Masks.items():
            bits = word & mask
            if bits in ops:
                return self.Op[bits]

        return None

    def get_syscall(self, word):
        return self.syscall[word]
