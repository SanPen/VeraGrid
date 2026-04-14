# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations


class FmuImportError(RuntimeError):
    """Base exception for the experimental FMU import package.

    :return: None.
    """


class FmuDependencyError(FmuImportError):
    """Raised when an external FMU runtime dependency is missing.

    :return: None.
    """


class FmuArchiveError(FmuImportError):
    """Raised when the FMU archive cannot be inspected safely.

    :return: None.
    """


class FmuModeError(FmuImportError):
    """Raised when the requested FMI mode cannot be executed.

    :return: None.
    """


class FmuBindingError(FmuImportError):
    """Raised when VeraGrid and FMU signal bindings are inconsistent.

    :return: None.
    """
