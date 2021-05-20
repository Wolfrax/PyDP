

class aout_file:
    def __init__(self, fname):
        self.fname = fname
        with open(self.fname, 'rb') as f:
            self.data = f.read()

        self.start_header = 0
        self.header_size = 16
        self.header = {'magic': self._word(0), 'text size': self._word(2), 'data size': self._word(4),
                       'bss size': self._word(6), 'sym table size': self._word(8), 'entry loc': self._word(10),
                       'unused': self._word(12), 'relocation flag': self._word(14)}

        self.start_text_segment = self.start_header + self.header_size
        self.start_data_segment = self.start_text_segment + self.header['text size']
        if self.header['relocation flag'] == 0:
            self.start_relocation_info = 0
            self.start_symbol_table = self.start_text_segment + 2 * (self.header['text size'] + self.header['data size'])
        else:
            self.start_relocation_info = self.start_data_segment + self.header['data size']
            self.start_symbol_table = self.header_size + self.header['text size'] + self.header['data size']

    def _word(self, ind):
        return (self.data[ind + 1] << 8) | self.data[ind]

    def dump_header(self):
        print("magic: {}".format(self.header['magic']))
        print("text size: {}".format(self.header['text size']))
        print("data size: {}".format(self.header['data size']))
        print("bss size: {}".format(self.header['bss size']))
        print("symbol table size: {}".format(self.header['sym table size']))
        print("entry location: {}".format(self.header['entry loc']))
        print("unused: {}".format(self.header['unused']))
        print("relocation flag: {}".format(self.header['relocation flag']))

    def dump_sym_table(self):
        sym_tab = self.start_symbol_table
        while sym_tab < (self.start_symbol_table + (self.header['sym table size'])):
            sym = ''
            for i in range(8):
                ch = self.data[sym_tab + i]
                if ch != 0:
                    sym += chr(ch)
            print('{}: type: {}, val: {}'.format(sym, self._word(sym_tab + 8), self._word(sym_tab + 10)))
            sym_tab += 12

    def dump_text(self):
        print("instr: {}".format(self._word(self.header_size)))


if __name__ == '__main__':
    aout = aout_file('a1.out')
    aout.dump_header()
    aout.dump_text()
    aout.dump_sym_table()