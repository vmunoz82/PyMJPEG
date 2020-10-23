from distutils.core import setup, Extension

setup(name="huffman", version="1.0",
      ext_modules=[Extension("huffman", ["huffman.c", "../common/c_huffman.c"], include_dirs=['../common/'])])
