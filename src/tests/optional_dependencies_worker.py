# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Probe Engine startup while one optional PyPSA integration is deliberately broken."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import sys
from types import ModuleType


class _BrokenPypsaFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Supply one controlled PyPSA import result to an isolated interpreter."""

    __slots__ = ("_failure",)

    def __init__(self, failure: str) -> None:
        """Store the requested optional-dependency failure.

        :param failure: Failure condition selected by the parent test.
        :return: None.
        """
        self._failure = failure

    def find_spec(
            self, fullname: str, path: object, target: object,
    ) -> importlib.machinery.ModuleSpec | None:
        """Claim only the PyPSA import boundary.

        :param fullname: Absolute module name requested by the importer.
        :param path: Parent package search path, when applicable.
        :param target: Existing module used by reloads, when applicable.
        :return: Loader specification for PyPSA or no opinion for other modules.
        """
        if fullname == "pypsa":
            return importlib.machinery.ModuleSpec(fullname, self)
        else:
            return None

    def create_module(
            self, spec: importlib.machinery.ModuleSpec,
    ) -> None:
        """Use Python's standard module allocation.

        :param spec: Specification for the fake PyPSA module.
        :return: None.
        """
        return None

    def exec_module(self, module: ModuleType) -> None:
        """Raise the selected failure or leave the requested API absent.

        :param module: Fresh module object supplied by Python's importer.
        :return: None.
        """
        if self._failure == "absent":
            raise ModuleNotFoundError("No module named 'pypsa'", name="pypsa")
        elif self._failure == "ImportError":
            raise ImportError("simulated PyPSA import failure")
        elif self._failure == "AttributeError":
            raise AttributeError("simulated PyPSA API failure")
        elif self._failure == "OSError":
            raise OSError("simulated PyPSA native failure")
        elif self._failure == "RuntimeError":
            raise RuntimeError("simulated PyPSA runtime failure")
        elif self._failure == "ValueError":
            raise ValueError("simulated PyPSA configuration failure")
        elif self._failure == "TypeError":
            raise TypeError("simulated PyPSA type failure")
        elif self._failure == "missing_dependency":
            raise ModuleNotFoundError(
                "No module named 'pypsa_dependency'", name="pypsa_dependency",
            )
        elif self._failure in ("missing_api", "missing_format_api"):
            pass
        else:
            raise ValueError(f"Unknown optional dependency failure: {self._failure}")


def main() -> None:
    """Install the fake optional boundary and import the complete Engine.

    :return: None.
    """
    failure: str = sys.argv[1]
    sys.modules.pop("pypsa", None)
    sys.meta_path.insert(0, _BrokenPypsaFinder(failure))
    engine_module: ModuleType = importlib.import_module("VeraGridEngine")
    properly_loaded: bool = engine_module.PROPERLY_LOADED_API
    if properly_loaded:
        print("optional dependency startup passed")
    else:
        raise RuntimeError("VeraGrid Engine startup failed with a broken optional dependency")


if __name__ == "__main__":
    main()
