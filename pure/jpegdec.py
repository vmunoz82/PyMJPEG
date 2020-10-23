###############################################################################
# jpegdec.py
# A pure Python JPEG decoding class.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import struct

import huffman
import jpegdev
import misc

# for Python 2.6 - 3 compatibility
pord = misc.def_pord()


class Jpeg_decoder:
    """Pure Python JPEG decoding class."""

    log2 = {1 << i: i for i in range(8)}

    izz_table = (0,  1,  8, 16,  9,  2,  3, 10,
                17, 24, 32, 25, 18, 11,  4,  5,
                12, 19, 26, 33, 40, 48, 41, 34,
                27, 20, 13,  6,  7, 14, 21, 28,
                35, 42, 49, 56, 57, 50, 43, 36,
                29, 22, 15, 23, 30, 37, 44, 51,
                58, 59, 52, 45, 38, 31, 39, 46,
                53, 60, 61, 54, 47, 55, 62, 63)

    zz_table = (0,  1,  5,  6, 14, 15, 27, 28,
                2,  4,  7, 13, 16, 26, 29, 42,
                3,  8, 12, 17, 25, 30, 41, 43,
                9, 11, 18, 24, 31, 40, 44, 53,
               10, 19, 23, 32, 39, 45, 52, 54,
               20, 22, 33, 38, 46, 51, 55, 60,
               21, 34, 37, 47, 50, 56, 59, 61,
               35, 36, 48, 49, 57, 58, 62, 63)

    def __init__(self):
        self._qtables = [[0] * 64 for i in range(8)]
        self._htables = [0] * 8
        self._planes_count = 0
        self._planes = [{'fh':-1, 'fv':-1, 'q':-1}] * 256
        self._width = 0
        self._height = 0
        self._pwidth = 0
        self._pheight = 0

        self._psum = 3
        self._lsum = 0

        self._sos_table = [(0, 0)]

        self._use_ri = False
        self._ri = 0

        self._bmpdata = None
        self._huf = huffman.Huffman()

        self._inverse_dir = False

    def _block_blt(self, dest, src, a, b, c):
        """Put an 8x8 block inside a JPEG MCU."""

        for i in range(len(src)):
            dest[((i & 0xFFF8) << a) + ((i & 7) << b) + c] = src[i]

    def _mcu_blt(self, src, sw, x, y):
        """Put an MCU in the image frame buffer."""

        j = 0

        bitmap = self._bmpdata
        if self._inverse_dir:
            rev = (self._pwidth * (self._pheight - y - 1) + (x)) * 3
        else:
            rev = (self._pwidth * y + x) * 3

        for i in range(len(src[0])):
            bitmap[rev + 2], bitmap[rev + 1], bitmap[rev + 0] = \
            jpegdev.ycbcr2rgb(src[0][i], src[1][i], src[2][i])

            rev += self._psum
            j += 1
            if j == sw:
                j = 0
                rev += self._lsum

    def _decode_block(self, table_idx):
        """Fill an 8x8 block: apply Huffman decoding and retrieve a variable
           length signed value, skips positions according to RLZ and insert
           according the zigzag table."""

        is_ac = 0

        m = [0] * 64
        midx = 0

        ht = [self._htables[self._sos_table[table_idx][0]],
              self._htables[4 | self._sos_table[table_idx][1]]]

        while True:
            tmp = self._huf.get_symbol(ht[is_ac])
            hbits, rlz = tmp & 0xF, tmp >> 4
            midx += rlz
            tidx = Jpeg_decoder.izz_table[midx]
            m[tidx] = self._huf.get_jpeg_value(hbits)
            #print("RLZ: %d VAL: %d" % (rlz,m[izz_table[midx]]))
            midx += 1

            if (is_ac == 1 and rlz == 0 and hbits == 0) or midx == 64:  # EOB
                return m
            if is_ac == 0:
                is_ac = 1

    def _decode_image(self):
        """Calculate multiple values (and a table) to decode this image and
           call the decoding process."""

        q = [self._qtables[self._planes[i]['q']] \
             for i in range(self._planes_count)]
        unitspp = [self._planes[i]['fh'] * self._planes[i]['fv']
                   for i in range(self._planes_count)]

        fhmax = max(self._planes, key = lambda a: a['fh'])['fh']  # PEP8??!!
        fvmax = max(self._planes, key = lambda a: a['fv'])['fv']

        mcu_width = fhmax << 3
        mcu_height = fvmax << 3
        mcu_pixels = mcu_width * mcu_height

        idxs = [[0] * mcu_pixels for i in range(self._planes_count)]

        self._pwidth = int(((self._width + mcu_width - 1) / mcu_width)) \
                       * mcu_width
        self._pheight = int(((self._height + mcu_height - 1) / mcu_height)) \
                       * mcu_height

        if self._inverse_dir:
            self._lsum = -(self._pwidth + mcu_width) * 3
        else:
            self._lsum = (self._pwidth - mcu_width) * 3

        for i in range(self._planes_count):
            plane = self._planes[i]
            mxc = 0
            for j in range(fvmax << 3):
                for k in range(fhmax << 3):
                    ta = (j >> Jpeg_decoder.log2[fvmax / plane['fv']])
                    tb = (Jpeg_decoder.log2[plane['fh']] + 3)
                    tc = (k >> Jpeg_decoder.log2[fhmax / plane['fh']])
                    idxs[i][mxc] = (ta << tb) | tc
                    mxc += 1

        self._decode_image_process(q, unitspp, fhmax, fvmax, mcu_width, \
                                   mcu_height, mcu_pixels, idxs)

    def _decode_image_process(self, q, unitspp, fhmax, fvmax, mcu_width, \
                              mcu_height, mcu_pixels, idxs):
        """Main JPEG decoding process: decode basic 8x8 blocks, craft the MCU
           and put it inside the image bitmap."""

        dc = [0] * self._planes_count
        trans = [[0] * 64 for i in range(fhmax * fvmax)]
        mcu = [0] * mcu_pixels
        dest = [[0] * mcu_pixels for i in range(self._planes_count)]

        self._bmpdata = bytearray(self._pwidth * self._pheight * 3)

        x, y = 0, 0
        for i in range(int(self._pwidth * self._pheight / mcu_pixels)):
            if self._use_ri and self._ri != 0 and i % self._ri == 0:
                self._huf.sync()
                for j in range(self._planes_count):
                    dc[j] = 0

            for j in range(self._planes_count):
                plane = self._planes[j]
                for k in range(unitspp[j]):
                    unit = self._decode_block(j)

                    dc[j] += unit[0]
                    unit[0] = dc[j]
                    for l in range(64):
                        trans[k][l] = unit[l] * q[j][l]

                    jpegdev.idct_2d(trans[k])

                ic = 0
                for k in range(plane['fv']):
                    ta = Jpeg_decoder.log2[plane['fh']]
                    tb = ((plane['fh'] * k) << 6)
                    for l in range(plane['fh']):
                        self._block_blt(mcu, trans[ic], ta, 0, (l << 3) + tb)
                        ic += 1

                ta, tb = dest[j], idxs[j]
                for k in range(len(tb)):
                    ta[k] = mcu[tb[k]]

            self._mcu_blt(dest, mcu_width, x, y)
            x += mcu_width
            if x == self._pwidth:
                x = 0
                y += mcu_height

    def _m_sof0(self, code, data, offset, size):
        """JPEG Start Of Frame marker (Baseline)."""

        (a, b, c, d) = struct.unpack(">BHHB", data[offset:offset + 6])
        precision, self._height, self._width, \
        self._planes_count = (a, b, c, d)

        offset += 6
        for i in range(self._planes_count):
            pid, fact, quant = struct.unpack(">BBB", data[offset:offset + 3])
            self._planes[pid - 1] = {'fh': fact >> 4, 'fv': fact & 15, \
                                     'q': quant}
            offset += 3

    def _m_dht(self, code, data, offset, size):
        """JPEG Define Huffman Table marker."""

        o = offset
        while o < (offset + size):
            htid = pord(data[o])  # class<<4 | destination_id
            o += 1

            spb = map(pord, data[o:o + 16])  # Python 2.6+ compat.
            acc = sum(spb)
            o += 16

            ht = self._huf.table_init(data[o:o + acc], data[o - 16:o])
            self._htables[((htid >> 2) & 4) | (htid & 3)] = ht
            o += acc

    def _m_eoi(self, code, data, offset, size):
        """JPEG End Of Image marker."""

        self._decode_image()

    def _m_sos(self, code, data, offset, size):
        """JPEG Start Of Scan marker."""

        count = pord(data[offset])
        offset += 1
        self._sos_table = [(0, 0)] * count
        for i in range(count):
            pid, tidx = struct.unpack(">BB", data[offset:offset + 2])
            self._sos_table[pid - 1] = (tidx >> 4, tidx & 15)  # dc - ac
            offset += 2

        offset += 3
        off = offset
        size = 0
        while True:
            off2 = off
            off = data.find(b"\xFF", off)
            size += (off - off2)
            if pord(data[off + 1]) == 0x00:
                size += 1
            elif pord(data[off + 1]) & 0xD8 != 0xD0:
                break
            off += 2

        hdata = bytearray(size + 2)  # +2 because the Huffman implementation

        off = offset
        size = 0
        while True:
            off2 = off
            off = data.find(b"\xFF", off)
            hdata[size:size + (off - off2)] = data[off2:off]
            size += (off - off2)

            if pord(data[off + 1]) == 0x00:
                hdata[size] = 0xFF
                size += 1
            elif pord(data[off + 1]) & 0xD8 != 0xD0:
                break
            off += 2

        self._huf.stream_init(hdata, 0)

    def _m_dqt(self, code, data, offset, size):
        """JPEG Define Quantization Table marker."""

        for i in range(int(size / 65)):
            q = list(map(pord, data[offset + 1:offset + 65]))
            self._qtables[pord(data[offset])] = \
            list(map(lambda x: q[x], Jpeg_decoder.zz_table))
            offset += 65

    def _m_dri(self, code, data, offset, size):
        """JPEG Define Restart Interval marker."""

        self._use_ri = True
        self._ri = pord(data[offset]) << 8 | pord(data[offset + 1])

    def parse(self, jblob, inverse=False):
        """Main JPEG stream parsing. Returns bitmap image, width and height.
        """

        bi = 0
        s = len(jblob)

        self._inverse_dir = inverse

        while bi < s:
            bi = jblob.find(b"\xFF", bi)
            bi += 1
            marker = pord(jblob[bi])
            misc.dprint("marker %x\n" % (marker))
            if pord(jblob[bi]) != 0x00:
                if marker in self._m_table:
                    e = self._m_table[marker]

                    skip = 0
                    if e[1] & 1 == 1:
                        skip = (pord(jblob[bi + 1]) << 8 | pord(jblob[bi + 2]))
                    if e[2] != None:
                        e[2](self, pord(jblob[bi]), jblob, bi + 3, skip - 2)
                    bi += skip
                    bi += 1
                else:
                    misc.dprint("The marker %x is not in table.\n" % \
                                pord(jblob[bi]))
                if marker == 0xD9:
                    return self._bmpdata, self._pwidth, self._pheight

    _m_table = {
        0xC0: ("SOF0", 1, _m_sof0),
        0xC4: ("DHT",  1, _m_dht),
        0xD0: ("RST0", 0, None), 0xD1: ("RST1", 0, None),
        0xD2: ("RST2", 0, None), 0xD3: ("RST3", 0, None),
        0xD4: ("RST4", 0, None), 0xD5: ("RST5", 0, None),
        0xD6: ("RST6", 0, None), 0xD7: ("RST7", 0, None),
        0xD8: ("SOI",  0, None),
        0xD9: ("EOI",  0, _m_eoi),
        0xDA: ("SOS",  3, _m_sos),
        0xDB: ("DQT",  1, _m_dqt),
        0xDD: ("DRI",  1, _m_dri),
        0xE0: ("APP0", 1, None), 0xE1: ("APP1", 1, None),
        0xE2: ("APP2", 1, None), 0xE3: ("APP3", 1, None),
        0xE4: ("APP4", 1, None), 0xE5: ("APP5", 1, None),
        0xE6: ("APP6", 1, None), 0xE7: ("APP7", 1, None),
        0xE8: ("APP8", 1, None), 0xE9: ("APP9", 1, None),
        0xEA: ("APPA", 1, None), 0xEB: ("APPB", 1, None),
        0xEC: ("APPC", 1, None), 0xED: ("APPD", 1, None),
        0xEE: ("APPE", 1, None), 0xEF: ("APPF", 1, None)
    }
