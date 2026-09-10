# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from enum import Enum, auto


class RoutingEditValidationResult(Enum):
    """
    Classify whether an edited route can commit or requires recovery.

    Internal conflicts are direct consequences of manual geometry editing and
    must stop at the previous valid snapshot. Environmental conflicts may use
    automatic reconstruction because blocks or foreign wires changed around
    an otherwise meaningful user operation.

    :return: None.
    """

    VALID = auto()
    INTERNAL_CONFLICT = auto()
    ENVIRONMENT_CONFLICT = auto()
