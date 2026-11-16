# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Direct modern brushless layouts and complete generator assembly checks."""
from __future__ import annotations

import pytest

from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33
from VeraGridEngine.IO.raw.versioned.v34.dyr import RawDyrV34
from tests.FileFormats.PSSe.test_psse_auxiliary_conversion import test_adapter_initializes_at_a_real_power_flow_equilibrium as check_equilibrium


def ac6c_record(modified: bool, maximum: int = 1, minimum: int = 1,
                dependent: int = 1) -> str:
    """Create the documented modern 25-CON assignment.

    :param modified: Select the three-ICON limit-dependency variant.
    :param maximum: Maximum-excitation insertion flag.
    :param minimum: Minimum-excitation insertion flag.
    :param dependent: Terminal-dependent forcing-limit flag.
    :return: Complete direct assignment.
    """
    name: str = 'AC6C2' if modified else 'AC6C'
    selection: str = f'{maximum} {minimum} {dependent}' if modified else f'{maximum} {minimum}'
    return f"1 '{name}' '01' {selection} .02 20 .05 .02 .05 .02 5 -5 5 -5 .5 2 .2 2 .1 .05 .1 .1 1 3 .1 4 .3 5 0 /"


@pytest.mark.parametrize('modified',(False,True))
def test_ac6c_release_layout(modified: bool) -> None:
    """The supplied direct schemas parse only under the modern source profile.

    :param modified: Select the third limit-dependency ICON.
    """
    source: str = ac6c_record(modified)
    record: DyrRecord = parse_dyr(source,version=35).records[0]
    assert record.status == RecordStatus.VALID
    assert len(record.parameters) == 25 and len(record.icons) == (3 if modified else 2)
    assert RawDyrV33().get_model_schema(record.model) is None
    assert RawDyrV34().get_model_schema(record.model) is None


@pytest.mark.parametrize('modified',(False,True))
@pytest.mark.parametrize('maximum,minimum',((1,1),(2,1),(1,2),(2,2)))
def test_ac6c_complete_machine(modified: bool, maximum: int, minimum: int) -> None:
    """Each high/low limiter location starts from the actual generator field equilibrium.

    :param modified: Select the optional limit-dependency variant.
    :param maximum: Maximum-excitation insertion flag.
    :param minimum: Minimum-excitation insertion flag.
    """
    source: str = ac6c_record(modified,maximum,minimum,0 if modified else 1)
    check_equilibrium('GENROU','8 .03 .4 .05 4 2 1.8 1.7 .3 .55 .25 .2 .09 .38',source,False,version=35)


@pytest.mark.parametrize('minimum',(1,2))
def test_ac6c_connected_auxiliary_initialization(minimum: int) -> None:
    """An actual stabilizer and minimum limiter keep the stored generator at equilibrium.

    :param minimum: Additive or high-gate minimum-excitation insertion.
    """
    source: str = ac6c_record(True,2,minimum,1)
    source += "\n1 'PSS3B' '01' 1 0 3 0 1 0 0 -.5 0 0 0 0 0 0 0 0 0 0 0 .1 -.1 /"
    source += "\n1 'MNLEX1' '01' .001 1 2 .2 .1 1 /"
    check_equilibrium('GENROU','8 .03 .4 .05 4 2 1.8 1.7 .3 .55 .25 .2 .09 .38',source,True,version=35)
