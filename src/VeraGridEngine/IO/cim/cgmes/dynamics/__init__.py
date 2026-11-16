# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES Dynamics schema and importer assets."""

from VeraGridEngine.IO.cim.cgmes.dynamics.assets import CgmesDynamicsAssets
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    DY_ASSOCIATION_INVERSES,
    DY_CLASS_DICT,
    DY_CLASS_NAMES,
)


def get_cgmes_dynamics_classes() -> dict[str, type]:
    """Return the generated CGMES Dynamics class registry.

    :return: Class constructors keyed by their CIM class name.
    """
    return dict(DY_CLASS_DICT)
