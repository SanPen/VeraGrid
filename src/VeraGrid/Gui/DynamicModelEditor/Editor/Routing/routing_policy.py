# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from enum import Enum, auto


class AutomaticRoutingPolicy(Enum):
    """
    Define which collision constraints an automatic route may relax.

    Block penetration and core geometric invariants remain hard constraints in
    every policy. Only intersections with other connections are relaxable.

    :return: None.
    """

    STRICT = auto()
    ALLOW_WIRE_CROSSINGS = auto()
