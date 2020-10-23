###############################################################################
# decode.py
# A pure Python JPEG decoder, convert JPEG and frames inside a MOV or MP4 file
# (when coded with JPEG) to BMP files.
#
# Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>
#
# for demonstration purpose only, not for redistribution.
#

import sys
import time

import jpegdec
import misc
import movfile


def decode_jpeg_file(filename, baseout):
    jd = jpegdec.Jpeg_decoder()
    fp = open(filename, "rb")

    jpegtext = fp.read()
    fp.close()
    data, w, h = jd.parse(jpegtext, True)

    misc.save_bmp("%s.bmp" % baseout, data, w, h)

    misc.uprint("Width: %d\n" % w)
    misc.uprint("Height: %d\n" % h)


def decode_mov_file(filename, baseout):
    b = 0
    found = False

    mv = movfile.Mov_container(filename)

    for trak in mv.md[b'moov'][b'trak']:
        csubtype = trak[b'mdia'][b'hdlr'][b'csubtype']
        sdesc = trak[b'mdia'][b'minf'][b'stbl'][b'stsd']

        if csubtype == b'vide' and sdesc[0] == b'jpeg':

            found = True

            duration = trak[b'tkhd'][b'duration'] / \
                       float(trak[b'mdia'][b'mdhd'][b'timescale'])
            frames = len(trak[b'mdia'][b'minf'][b'stbl'][b'stsz'])
            trackid = trak[b'tkhd'][b'trackid']
            width = trak[b'tkhd'][b'width']
            height = trak[b'tkhd'][b'height']

            misc.uprint("Video track with JPEG stream found.\n")
            misc.uprint("Track id: %d\n" % trackid)
            misc.uprint("Width: %d\n" % width)
            misc.uprint("Height: %d\n" % height)
            misc.uprint("Frames: %d\n" % frames)
            misc.uprint("Duration: %0.1f seconds (%d FPS)\n" % \
                        (duration, (frames / duration) + 0.5))

            for bu in mv.get_frames(trak):
                misc.uprint("Decoding frame %d/%d...\n" % (b + 1, frames))
                jd = jpegdec.Jpeg_decoder()
                data, w, h = jd.parse(bu, True)

                misc.save_bmp("%s_%d.bmp" % (baseout, b), data, w, h)

                b += 1

    if not found:
        misc.uprint("No JPEG stream found.\n")


def extract_bitmaps(filename):
    dot = filename.rfind('.')
    slash = max([filename.rfind('/'), filename.rfind('\\')])

    base, ext = filename[slash + 1:dot], filename[dot + 1:]

    if ext.lower() == 'jpg':
        decode_jpeg_file(filename, base)
    elif ext.lower() == 'mov' or ext.lower() == 'mp4':
        decode_mov_file(filename, base)
    else:
        misc.uprint("filename %s has not a supported extension.\n" % filename)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        misc.uprint("usage:\n%s <image.jpg|video.mov>\n" % sys.argv[0])
    else:
        t0 = time.clock()
        extract_bitmaps(sys.argv[1])
        misc.uprint("Time elapsed %0.4f\n" % (time.clock() - t0))
