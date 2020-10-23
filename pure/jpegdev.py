###############################################################################
# jpegdev.py
# JPEG core decoding functions.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import math
import functools  # reduce (Python 3)

_idct_table = [[0.0] * 8 for i in range(8)]


def _idct_init():
    """Generate an auxiliary IDCT table."""

    for u in range(8):
        for x in range(8):
            if x == 0:
                s = math.sqrt(2) * 0.5 * 0.5
            else:
                s = 0.5
            _idct_table[u][x] = s * math.cos(math.pi * x * (2 * u + 1) / 16)


def idct_1d(msrc, mout, a, b):
    """One dimension IDCT naive implementation."""

    fnc = lambda v, w: v + msrc[w << a | b] * tu[w]
    for u in range(8):
        tu = _idct_table[u]
        mout[u << a | b] = functools.reduce(fnc, range(8), 0)


def idct_2d(mout):
    """Two dimensional IDCT naive implementation."""

    mt = [0] * 64
    msrc = [e for e in mout]
    for i in range(8):
        idct_1d(msrc, mt, 3, i)
    for i in range(8):
        idct_1d(mt, mout, 0, i << 3)

    for i in range(64):
        mout[i] = int(mout[i])

_idct_init()

inv = 1 / 0.587


def ycbcr2rgb(y, cb, cr):
    """YCbCr to RGB color space conversion."""

    r = cr * (2 - 2 * 0.299) + y
    b = cb * (2 - 2 * 0.114) + y
    g = (y - b * 0.114 - r * 0.299) * inv

    rgb = [r, g, b]
    for i in range(3):
        rgb[i] += 128
        if rgb[i] < 0:
            rgb[i] = 0
        if rgb[i] > 255:
            rgb[i] = 255

    return int(rgb[0]), int(rgb[1]), int(rgb[2])
