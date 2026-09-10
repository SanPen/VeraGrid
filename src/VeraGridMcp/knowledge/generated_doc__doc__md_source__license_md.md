# Official VeraGrid Doc: License

- Original source path: `doc/md_source/license.md`
- Knowledge kind: official documentation

## Document Content

# 📜 License


VeraGrid is licensed under the [Mozilla Public License 2.0 (MPLv2)](https://mozilla.org/MPL/2.0/)

In practical terms this means that:

- You can use VeraGrid for commercial work.
- You can sell commercial services based on VeraGrid.
- If you distribute VeraGrid, you must distribute VeraGrid's source code as well.
  That is always achieved in practice with python code.
- VeraGrid license does not propagate, even if you use VeraGrid or pieces of it in your code.
  However, you must retain the individual files licensing.

Nonetheless, read the license carefully.

## License of the dependencies


| Package       | License                                  |
|---------------|------------------------------------------|
| setuptools    | MIT                                      |
| wheel         | MIT                                      |
| PySide6       | LGPL                                     |
| numpy         | BSD                                      |
| scipy         | BSD                                      |
| networkx      | BSD                                      |
| pandas        | Apache                                   |
| pulp          | MIT-like (permissive)                    |
| xlwt          | BSD                                      |
| xlrd          | BSD                                      |
| matplotlib    | Python Software Foundation License (PSF) |
| openpyxl      | MIT                                      |
| smopy         | BSD                                      |
| chardet       | LGPL                                     |
| scikit-learn  | OSI approved (new BSD)                   |
| geopy         | MIT                                      |
| pytest        | MIT                                      |
| h5py          | BSD                                      |
| numba         | BSD                                      |
| pyproj        | MIT                                      |
| brotli        | MIT                                      |
| chardet       | LGPL                                     |
| highspy       | MIT                                      |
| opencv-python | MIT & Apache                             |
| pvlib         | BSD 2-Clause                             |
| pyarrow       | Apache                                   |
| pymoo         | Apache                                   |
| rdflib        | BSD-2                                    |
| websockets    | BSD-3                                    |
| windpowerlib  | MIT                                      |

## Dependency map

```
veragrid                                  VeraGrid is a Power Systems simulation program intended for professional use and research
├── VeraGridEngine==5.3.53                VeraGrid is a Power Systems simulation program intended for professional use and research
│   ├── autograd>=1.7.0                   Efficiently computes derivatives of NumPy code.
│   │   └── numpy<3                       Fundamental package for array computing in Python
│   ├── brotli                            Python bindings for the Brotli compression library
│   ├── chardet>=3.0.4                    Universal encoding detector for Python 3
│   ├── geopy>=1.16                       Python Geocoding Toolbox
│   │   └── geographiclib<3,>=1.52        The geodesic routines from GeographicLib
│   ├── h5py>=3.12.0                      Read and write HDF5 files from Python
│   │   └── numpy>=1.19.3                 Fundamental package for array computing in Python
│   ├── highspy>=1.8.0                    A thin set of pybind11 wrappers to HiGHS
│   │   └── numpy                         Fundamental package for array computing in Python
│   ├── matplotlib>=2.1.1                 Python plotting package
│   │   ├── contourpy>=1.0.1              Python library for calculating contours of 2D quadrilateral grids
│   │   │   └── numpy>=1.23               Fundamental package for array computing in Python
│   │   ├── cycler>=0.10                  Composable style cycles
│   │   ├── fonttools>=4.22.0             Tools to manipulate font files
│   │   ├── kiwisolver>=1.3.1             A fast implementation of the Cassowary constraint solver
│   │   ├── numpy>=1.23                   Fundamental package for array computing in Python
│   │   ├── packaging>=20.0               Core utilities for Python packages
│   │   ├── pillow>=8                     Python Imaging Library (Fork)
│   │   ├── pyparsing>=2.3.1              pyparsing module - Classes and methods to define and execute parsing grammars
│   │   └── python-dateutil>=2.7          Extensions to the standard Python datetime module
│   │       └── six>=1.5                  Python 2 and 3 compatibility utilities
│   ├── networkx>=2.1                     Python package for creating and manipulating graphs and networks
│   ├── numba>=0.61                       compiling Python code using LLVM
│   │   ├── llvmlite<0.45,>=0.44.0dev0    lightweight wrapper around basic LLVM functionality
│   │   └── numpy<2.3,>=1.24              Fundamental package for array computing in Python
│   ├── numpy>=2.2.0                      Fundamental package for array computing in Python
│   ├── opencv-python>=4.10.0.84          Wrapper package for OpenCV python bindings.
│   │   └── numpy<2.3.0,>=2               Fundamental package for array computing in Python
│   ├── openpyxl>=2.4.9                   A Python library to read/write Excel 2010 xlsx/xlsm files
│   │   └── et-xmlfile                    An implementation of lxml.xmlfile for the standard library
│   ├── pandas>=2.2.3                     Powerful data structures for data analysis, time series, and statistics
│   │   ├── numpy>=1.26.0                 Fundamental package for array computing in Python
│   │   ├── python-dateutil>=2.8.2        Extensions to the standard Python datetime module
│   │   │   └── six>=1.5                  Python 2 and 3 compatibility utilities
│   │   ├── pytz>=2020.1                  World timezone definitions, modern and historical
│   │   └── tzdata>=2022.7                Provider of IANA time zone data
│   ├── pvlib>=0.11                       A set of functions and classes for simulating the performance of photovoltaic energy systems.
│   │   ├── h5py                          Read and write HDF5 files from Python
│   │   │   └── numpy>=1.19.3             Fundamental package for array computing in Python
│   │   ├── numpy>=1.19.3                 Fundamental package for array computing in Python
│   │   ├── pandas>=1.3.0                 Powerful data structures for data analysis, time series, and statistics
│   │   │   ├── numpy>=1.26.0             Fundamental package for array computing in Python
│   │   │   ├── python-dateutil>=2.8.2    Extensions to the standard Python datetime module
│   │   │   │   └── six>=1.5              Python 2 and 3 compatibility utilities
│   │   │   ├── pytz>=2020.1              World timezone definitions, modern and historical
│   │   │   └── tzdata>=2022.7            Provider of IANA time zone data
│   │   ├── pytz                          World timezone definitions, modern and historical
│   │   ├── requests                      Python HTTP for Humans.
│   │   │   ├── certifi>=2017.4.17        Python package for providing Mozilla's CA Bundle.
│   │   │   ├── charset_normalizer<4,>=2  The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.
│   │   │   ├── idna<4,>=2.5              Internationalized Domain Names in Applications (IDNA)
│   │   │   └── urllib3<3,>=1.21.1        HTTP library with thread-safe connection pooling, file post, and more.
│   │   └── scipy>=1.6.0                  Fundamental algorithms for scientific computing in Python
│   │       └── numpy<2.6,>=1.25.2        Fundamental package for array computing in Python
│   ├── pyarrow>=15                       Python library for Apache Arrow
│   ├── pymoo>=0.6                        Multi-Objective Optimization in Python
│   │   ├── Deprecated                    Python @deprecated decorator to deprecate old python classes, functions or methods.
│   │   │   └── wrapt<2,>=1.10            Module for decorators, wrappers and monkey patching.
│   │   ├── alive-progress                A new kind of Progress Bar, with real-time throughput, ETA, and very cool animations!
│   │   │   ├── about-time==4.2.1         Easily measure timing and throughput of code blocks, with beautiful human friendly representations.
│   │   │   └── graphemeu==0.7.2          Unicode grapheme helpers
│   │   ├── autograd>=1.4                 Efficiently computes derivatives of NumPy code.
│   │   │   └── numpy<3                   Fundamental package for array computing in Python
│   │   ├── cma>=3.2.2                    CMA-ES, Covariance Matrix Adaptation Evolution Strategy for non-linear numerical optimization in Python
│   │   │   └── numpy                     Fundamental package for array computing in Python
│   │   ├── dill                          serialize all of Python
│   │   ├── matplotlib>=3                 Python plotting package
│   │   │   ├── contourpy>=1.0.1          Python library for calculating contours of 2D quadrilateral grids
│   │   │   │   └── numpy>=1.23           Fundamental package for array computing in Python
│   │   │   ├── cycler>=0.10              Composable style cycles
│   │   │   ├── fonttools>=4.22.0         Tools to manipulate font files
│   │   │   ├── kiwisolver>=1.3.1         A fast implementation of the Cassowary constraint solver
│   │   │   ├── numpy>=1.23               Fundamental package for array computing in Python
│   │   │   ├── packaging>=20.0           Core utilities for Python packages
│   │   │   ├── pillow>=8                 Python Imaging Library (Fork)
│   │   │   ├── pyparsing>=2.3.1          pyparsing module - Classes and methods to define and execute parsing grammars
│   │   │   └── python-dateutil>=2.7      Extensions to the standard Python datetime module
│   │   │       └── six>=1.5              Python 2 and 3 compatibility utilities
│   │   ├── numpy>=1.19.3                 Fundamental package for array computing in Python
│   │   └── scipy>=1.1                    Fundamental algorithms for scientific computing in Python
│   │       └── numpy<2.6,>=1.25.2        Fundamental package for array computing in Python
│   ├── pyproj                            Python interface to PROJ (cartographic projections and coordinate transformations library)
│   │   └── certifi                       Python package for providing Mozilla's CA Bundle.
│   ├── pytest>=7.2                       pytest: simple powerful testing with Python
│   │   ├── iniconfig>=1                  brain-dead simple config-ini parsing
│   │   ├── packaging>=20                 Core utilities for Python packages
│   │   ├── pluggy<2,>=1.5                plugin and hook calling mechanisms for python
│   │   └── pygments>=2.7.2               Pygments is a syntax highlighting package written in Python.
│   ├── rdflib                            RDFLib is a Python library for working with RDF, a simple yet powerful language for representing information.
│   │   └── pyparsing<4,>=2.1.0           pyparsing module - Classes and methods to define and execute parsing grammars
│   ├── scikit-learn>=1.5.0               A set of python modules for machine learning and data mining
│   │   ├── joblib>=1.2.0                 Lightweight pipelining with Python functions
│   │   ├── numpy>=1.22.0                 Fundamental package for array computing in Python
│   │   ├── scipy>=1.8.0                  Fundamental algorithms for scientific computing in Python
│   │   │   └── numpy<2.6,>=1.25.2        Fundamental package for array computing in Python
│   │   └── threadpoolctl>=3.1.0          threadpoolctl
│   ├── scipy>=1.0.0                      Fundamental algorithms for scientific computing in Python
│   │   └── numpy<2.6,>=1.25.2            Fundamental package for array computing in Python
│   ├── setuptools>=41.0.1                Easily download, build, install, upgrade, and uninstall Python packages
│   ├── websockets                        An implementation of the WebSocket Protocol (RFC 6455 & 7692)
│   ├── wheel>=0.37.2                     A built-package format for Python
│   ├── windpowerlib>=0.2.2               Creating time series of wind power plants.
│   │   ├── pandas                        Powerful data structures for data analysis, time series, and statistics
│   │   │   ├── numpy>=1.26.0             Fundamental package for array computing in Python
│   │   │   ├── python-dateutil>=2.8.2    Extensions to the standard Python datetime module
│   │   │   │   └── six>=1.5              Python 2 and 3 compatibility utilities
│   │   │   ├── pytz>=2020.1              World timezone definitions, modern and historical
│   │   │   └── tzdata>=2022.7            Provider of IANA time zone data
│   │   └── requests                      Python HTTP for Humans.
│   │       ├── certifi>=2017.4.17        Python package for providing Mozilla's CA Bundle.
│   │       ├── charset_normalizer<4,>=2  The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.
│   │       ├── idna<4,>=2.5              Internationalized Domain Names in Applications (IDNA)
│   │       └── urllib3<3,>=1.21.1        HTTP library with thread-safe connection pooling, file post, and more.
│   ├── xlrd>=1.1.0                       Library for developers to extract data from Microsoft Excel (tm) .xls spreadsheet files
│   └── xlwt>=1.3.0                       Library to create spreadsheet files compatible with MS Excel 97/2000/XP/2003 XLS files, on any platform, with Python 2.6, 2.7, 3.3+
├── PySide6>=6.8.0                        Python bindings for the Qt cross-platform application and UI framework
│   ├── PySide6-Addons==6.9.1             Python bindings for the Qt cross-platform application and UI framework (Addons)
│   │   ├── PySide6-Essentials==6.9.1     Python bindings for the Qt cross-platform application and UI framework (Essentials)
│   │   │   └── shiboken6==6.9.1          Python/C++ bindings helper module
│   │   └── shiboken6==6.9.1              Python/C++ bindings helper module
│   ├── PySide6-Essentials==6.9.1         Python bindings for the Qt cross-platform application and UI framework (Essentials)
│   │   └── shiboken6==6.9.1              Python/C++ bindings helper module
│   └── shiboken6==6.9.1                  Python/C++ bindings helper module
├── opencv-python>=4.10.0.84              Wrapper package for OpenCV python bindings.
│   └── numpy<2.3.0,>=2                   Fundamental package for array computing in Python
├── packaging                             Core utilities for Python packages
├── pytest>=7.2                           pytest: simple powerful testing with Python
│   ├── iniconfig>=1                      brain-dead simple config-ini parsing
│   ├── packaging>=20                     Core utilities for Python packages
│   ├── pluggy<2,>=1.5                    plugin and hook calling mechanisms for python
│   └── pygments>=2.7.2                   Pygments is a syntax highlighting package written in Python.
├── setuptools>=41.0.1                    Easily download, build, install, upgrade, and uninstall Python packages
├── websockets                            An implementation of the WebSocket Protocol (RFC 6455 & 7692)
└── wheel>=0.37.2                         A built-package format for Python
```
