from distutils.core import setup, Extension

setup(name="jpegdev", version="1.0",
      ext_modules=[Extension("jpegdev", ["jpegdev.c", "../common/c_jpegdev.c"], include_dirs=['../common/'])])
