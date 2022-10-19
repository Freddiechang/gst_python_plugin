from distutils.core import setup, Extension
import numpy
from Cython.Distutils import build_ext

setup(
    cmdclass={'build_ext': build_ext},
    ext_modules=[Extension("tsnnls", ["py_tsnnls.pyx"], include_dirs=[numpy.get_include()], libraries=["tsnnls"],
    extra_link_args=["-L/usr/local/lib/"])]
)