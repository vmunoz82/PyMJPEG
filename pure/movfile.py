###############################################################################
# movfile.py
# A pure Python MOV file parser.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import os
import struct
import jpegdec
import misc


class Mov_container:
    """Pure Python MOV file minimal parsing class."""

    def __init__(self, filename):
        self._mf = None
        mf = open(filename, "rb")
        self._mf = mf

        self._mf.seek(0, os.SEEK_END)
        fsz = self._mf.tell()
        self._mf.seek(0)

        self.md = self._traverse_tag(0, fsz, "")

    def _traverse_tag(self, base, size, prefix):
        """Traverses all the MOV file tags, generating a tree representation
           of it."""

        offset = 0

        data = {}

        while (offset + 8) < size:
            self._mf.seek(base + offset)
            (nsize, b) = struct.unpack(">I4s", self._mf.read(8))
            misc.dprint("%s%s\n" % (prefix, str(b)))

            d = None
            if b == b'mdhd':
                a0, a1, a2, a3, f0, f1, timescale, duration, a5, a6 = \
                struct.unpack(">B3BIIIIHH", self._mf.read(32 - 8))

                d = {}
                d[b'timescale'] = timescale
                d[b'duration'] = duration

            if b == b'tkhd':
                a0, a1, a2, a3, a4, a5, trackid, a7, duration, \
                a9, a10, a11, a12, width, eight = \
                struct.unpack(">B3BIIIII8xHHHH36xII", self._mf.read(92 - 8))

                d = {}
                d[b'trackid'] = trackid
                d[b'width'] = (width >> 16)
                d[b'height'] = (eight >> 16)
                d[b'duration'] = duration

            if b == b'hdlr':
                version, a1, a2, a3, ctype, csubtype, \
                cmanufacturer, cflags, cflagsmask = \
                struct.unpack(">B3B4s4s4sII", self._mf.read(32 - 8))

                d = {}
                d[b'ctype'] = ctype
                d[b'csubtype'] = csubtype
                d[b'cmanufacturer'] = cmanufacturer

            if b == b'stsd':
                version, f1, f2, f3, entries = \
                struct.unpack(">B3BI", self._mf.read(16 - 8))

                d = []
                for i in range(entries):
                    stsd_size, stsd_format = \
                    struct.unpack(">I4s", self._mf.read(8))

                    d.append(stsd_format)
                    self._mf.read(stsd_size - 8)

            if b == b'stsc':
                version, a1, a2, a3, entries = \
                struct.unpack(">B3BI", self._mf.read(16 - 8))

                d = []
                for i in range(entries):
                    d.append(struct.unpack(">3I", self._mf.read(12)))

            if b == b'stsz':
                version, a1, a2, a3, samplesize, entries = \
                struct.unpack(">B3BII", self._mf.read(20 - 8))

                if samplesize == 0:
                    d = []
                    for i in range(entries):
                        d.append(struct.unpack(">I", self._mf.read(4))[0])
                else:
                    d = samplesize

            if b == b'stco':
                version, a1, a2, a3, entries = \
                struct.unpack(">B3BI", self._mf.read(16 - 8))

                d = []
                for i in range(entries):
                    d.append(struct.unpack(">I", self._mf.read(4))[0])

            if b == b'moov' or b == b'trak' or b == b'mdia' or \
               b == b'minf' or b == b'stbl':
                d = self._traverse_tag(base + offset + 8, nsize, prefix + " ")

            if b == b'trak':
                if b in data:
                    data[b].append(d)
                else:
                    data[b] = [d]
            else:
                data[b] = d

            offset += nsize

        return data

    def get_frames(self, trak):
        """Generator function that return a blob containing each image frame.
        """

        fc = 0
        stsc_idx = 0

        d = trak[b'mdia'][b'minf'][b'stbl']

        for stco_idx in range(len(d[b'stco'])):
            acc = 0
            for spcc in range(d[b'stsc'][stsc_idx][1]):
                self._mf.seek(d[b'stco'][stco_idx] + acc)

                if isinstance(d[b'stsz'], int):
                    stsz = d[b'stsz']
                else:
                    stsz = d[b'stsz'][fc]

                yield self._mf.read(stsz)
                acc += stsz
                fc += 1

            if stsc_idx < (len(d[b'stsc']) - 1) and \
               d[b'stsc'][stsc_idx + 1][0] == (stco_idx + 2):
                stsc_idx += 1

    def __del__(self):
        if self._mf != None:
            self._mf.close()
