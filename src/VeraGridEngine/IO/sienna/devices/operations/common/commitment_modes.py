# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna CommitmentModes schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaCommitmentModes(Enum):
    """Values declared by the Sienna CommitmentModes schema."""

    UNCOMMITTED = 'UNCOMMITTED'
    COMMITTED = 'COMMITTED'
    SELF_SCHEDULED = 'SELF_SCHEDULED'
    RELIABILITY = 'RELIABILITY'
    MUST_RUN = 'MUST_RUN'


def parse_sienna_commitment_modes(data: str) -> SiennaCommitmentModes:
    """Parse one CommitmentModes enum value.

    :param data: Declared enum wire value.
    :return: Typed enum value.
    """
    return SiennaCommitmentModes(data)


def sienna_commitment_modes_to_json(value: SiennaCommitmentModes) -> str:
    """Write one CommitmentModes enum value to its wire representation.

    :param value: Typed enum value.
    :return: Declared enum wire value.
    """
    return value.value
