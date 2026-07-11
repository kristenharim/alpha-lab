"""Build the C++ extension(s). Pure-Python install still works without a compiler —
bands.py falls back to Python if the extension isn't built (see its try/except import).

Build in place:  python setup.py build_ext --inplace
"""
import setuptools  # noqa: F401  — installs the distutils shim (Python 3.12+ removed stdlib distutils)
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "core.backtest._fastbands",
        ["core/backtest/_fastbands.cpp"],
        cxx_std=17,
    ),
]

setup(cmdclass={"build_ext": build_ext}, ext_modules=ext_modules)
