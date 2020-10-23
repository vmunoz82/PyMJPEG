from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("jpegdec", ["jpegdec.pyx", "../common/c_jpegdev.c", "../common/c_huffman.c"], include_dirs=['../common/'])]
)