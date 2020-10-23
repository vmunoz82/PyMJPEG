###############################################################################
# huffman.py
# A pure Python Huffman decoding class.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import misc

# for Python 2.6 - 3 compatibility
pord = misc.def_pord()


class Huffman:
    """Pure Python Huffman decoding class."""

    bits_table_unos = [0] * 128 + [1] * 64 + [2] * 32 + [3] * 16 + \
                      [4] * 8 + [5] * 4 + [6] * 2 + [7] + [8]

    def __init__(self):
        self._tables = [{} for i in range(256)]
        self._tables_count = 0

        self._data = None
        self._di = 0

    def _primer_cero(self, bits, bitcount):
        """Returns the number of zeros at the left of a given 'bits' number of
           length 'bitcount' bits."""

        pc = 0
        val = 0
        for i in range(bitcount):
            val |= (bits & 1) << i
            if (bits & 1) == 1:
                pc += 1
            else:
                pc = 0
                vr = val
            bits >>= 1
        return pc, vr

    def stream_init(self, streamdata, streamindex):
        """Set a Huffman coded stream."""

        self._data = streamdata
        self._di = streamindex

    #{posicion_del_cero:
    # {bitstream_recortado_a_8_bits: (rlz << 4 | bits, bits_despues_de_cero)
    def table_init(self, stable, symcounts):
        """Generate a Huffman table, 'stable' is the actual symbol table and
           'symcount' is the number of symbols for each bitcounts of Huffman
           codes."""

        symbol = 0
        idx = 0
        tree = self._tables[self._tables_count]

        for symbits in range(len(symcounts)):
            symcount = pord(symcounts[symbits])
            for i in range(symcount):
                pc, tail = self._primer_cero(symbol, symbits + 1)
                dpc = symbits - pc

                if not pc in tree:
                    tree[pc] = {}
                for k in range(1 << (8 - dpc)):
                    tree[pc][(tail << (8 - dpc)) | k] = \
                    (pord(stable[idx]), dpc)

                symbol += 1
                idx += 1
            symbol <<= 1

        ridx = self._tables_count
        self._tables_count += 1
        return ridx

    def _bits_get_bits(self, bits):
        """Retrieve 'bits' bits of the working stream."""

        val = self._data[self._di >> 3] & ((2 << (7 - (self._di & 7))) - 1)
        bits -= 8 - (self._di & 7)
        self._di += 8 - (self._di & 7)

        if bits < 0:
            val = val >> (-bits)
            self._di += bits
            return val

        while bits >= 8:
            val = (val << 8) | self._data[(self._di >> 3)]
            bits -= 8
            self._di += 8

        if bits > 0:
            val = (val << bits) | (self._data[(self._di >> 3)] >> (8 - bits))
            self._di += bits

        return val

    def _bits_cuantos_unos(self):
        """Count the number of consecutive ones (bits) in current position of
           the stream."""

        unos = Huffman.bits_table_unos[(self._data[self._di >> 3] << \
                                        (self._di & 7)) & 0xFF]
        if unos & 7 == 8 - self._di & 7:
            di2 = self._di + unos
            unos2 = Huffman.bits_table_unos[(self._data[di2 >> 3] <<
                                          (di2 & 7)) & 0xFF]
            unos += unos2
            if unos2 & 7 == (8 - di2) & 7:
                idx = (self._data[(self._di + unos) >> 3] << \
                   ((self._di + unos) & 7)) & 0xFF
                unos += Huffman.bits_table_unos[idx]
        return unos

    def get_symbol(self, table):
        """Return a decoded symbol from the Huffman stream according with the
           given table."""

        hcount = self._bits_cuantos_unos()
        self._di += hcount + 1

        symbol, c = self._tables[table][hcount][self._bits_get_bits(8)]
        self._di -= 8 - c
        return symbol

    def _signed_value(self, n, bits):
        """Calculate the value of an 'bits' bits signed number (as per JPEG
           specs)."""

        if bits == 0:
            return 0
        if (n >> (bits - 1)) == 0:
            return n - ((1 << (bits)) - 1)
        return n

    def get_jpeg_value(self, hbits):
        """Retrieve a JPEG variable length int from the Huffman stream."""

        return self._signed_value(self._bits_get_bits(hbits), hbits)

    def sync(self):
        """Sync the Huffman stream to a byte boundary."""

        self._di = ((self._di + 7) >> 3) << 3
