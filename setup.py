"""
Build script for neural-rmf.

Compiles neural_rmf/_core/field_engine.pyx to a platform-specific binary
(.pyd on Windows, .so on Linux/macOS) using Cython.

Usage:
    python setup.py build_ext --inplace   # compile in place (dev)
    pip install .                          # full install
    pip install --no-build-isolation .    # if build deps already present
"""

import sys
import os
from pathlib import Path

from setuptools import setup, find_packages, Extension

# ── Cython availability check ─────────────────────────────────────────────────
try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

# ── Extension definition ──────────────────────────────────────────────────────
_EXT_SOURCE = "neural_rmf/_core/field_engine.pyx"
_EXT_NAME   = "neural_rmf._core.field_engine"

if USE_CYTHON and Path(_EXT_SOURCE).exists():
    extensions = cythonize(
        [Extension(_EXT_NAME, [_EXT_SOURCE])],
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
        annotate=False,   # do not emit .html annotation files
    )
else:
    # Fallback: include pre-compiled binary already in the tree.
    # The binary must exist at neural_rmf/_core/field_engine.*.so / .pyd.
    extensions = []

# ── Package data: include compiled binary, exclude source ─────────────────────
_PLATFORM = sys.platform          # "win32" | "linux" | "darwin"
_BIN_GLOB = (
    "*.pyd" if _PLATFORM == "win32" else "*.so"
)

setup(
    name="neural-rmf",
    version="0.1.0",
    description="Resonant Memory Field for real-time EEG pre-ictal detection",
    author="Gustavo",
    author_email="foser0206@gmail.com",
    python_requires=">=3.9",
    packages=find_packages(exclude=["tests*", "notebooks*", "docs*"]),
    package_data={
        # Ship the compiled binary; never ship the .pyx source.
        "neural_rmf._core": [_BIN_GLOB],
    },
    exclude_package_data={
        "neural_rmf._core": ["*.pyx", "*.py"],
    },
    ext_modules=extensions,
    install_requires=[
        "numpy>=1.24",
        "scipy>=1.10",
        "scikit-learn>=1.3",
        "torch>=2.0",
        "pyedflib>=0.1.22",
        "networkx>=3.0",
        "psutil>=5.9",
    ],
    extras_require={
        "live": ["pylsl>=1.16"],
        "dev":  ["cython>=3.0", "pytest>=7.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    zip_safe=False,   # required when shipping binary extensions
)
