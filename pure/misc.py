###############################################################################
# misc.py
# Miscellaneous functions.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import struct
import sys


def def_pord():
    """Defines the ord builtin function according the Python version."""

    if sys.version_info >= (2, 6):
        if sys.version_info < (3, 0):
            def xpord(v):
                return ord(v)
        else:
            def xpord(v):
                return v
        return xpord
    else:
        raise "sorry, Python 2.6+ is needed."


def save_bmp(filename, data, width, height):
    """Minimal code to save a BMP bitmap file."""

    hdr = struct.pack("<BBLHHLLLLHHLLLLLL",
                  0x42, 0x4D,
                  width * height * 3 + 54,
                  0, 0,
                  54,                  # offset
                  40,                  # header length
                  width, height,
                  0,                   # colorplanes
                  24,                  # colordepth
                  0,                   # compression
                  width * height * 3,  # imagesize: calcular
                  0, 0,                # resolution hor,vert
                  0,                   # palette
                  0)                   # importantcolors

    bmpfile = open(filename, "wb")
    bmpfile.write(hdr)
    bmpfile.write(data)
    bmpfile.close()


def dprint(pstr):
    """Development informative print."""

    #sys.stdout.write(pstr)
    pass


def uprint(pstr):
    """User level informative print."""

    sys.stdout.write(pstr)
