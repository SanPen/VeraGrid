# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Enumerations used by the supported Sienna v0.4 document subset."""

from enum import Enum

from VeraGridEngine.IO.sienna.devices.format_version import SiennaFormatVersion


class SiennaSchemaVersion(Enum):
    """Supported SiennaSchemas document versions."""

    V0_4_0 = SiennaFormatVersion.V0_4_0.value


class SiennaUnitSystem(Enum):
    """Unit bases declared by Sienna component records."""

    NATURAL_UNITS = "NATURAL_UNITS"
    COMPONENT_BASE = "COMPONENT_BASE"


class SiennaImpedanceUnitBasis(Enum):
    """Unit bases used by Sienna line impedances."""

    NATURAL_UNITS = "NATURAL_UNITS"
    COMPONENT_BASE = "COMPONENT_BASE"
