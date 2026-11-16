# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Release-specific source layouts for multi-machine voltage compensators."""

from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33
from VeraGridEngine.IO.raw.versioned.v34.dyr import RawDyrV34
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33


def test_compcc_preserves_second_machine_id_and_four_system_base_impedances() -> None:
    """Read the second machine identifier before the four source constants.

    :return: None.
    """
    source: str = "1 'COMPCC' '01' '02' .01 .02 .03 .04 /"
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == ('02',)
    assert tuple(parameter.name for parameter in record.parameters) == ('R1', 'X1', 'R2', 'X2')
    record_33: DyrRecord = parse_dyr(source, version=33).records[0]
    assert record_33.status is RecordStatus.VALID
    assert record_33.icons == ('02',)
    assert tuple(parameter.name for parameter in record_33.parameters) == ('R1', 'X1', 'R2', 'X2')
    assert RawDyrV33().get_model_schema('COMPCC') is not None
    assert RawDyrV34().get_model_schema('COMPCC') is None
    assert parse_dyr(source.replace("'02'", "'003'"), version=35).records[0].status is RecordStatus.INVALID
    assert parse_dyr(source.replace(' .03 .04', ' .03'), version=35).records[0].status is RecordStatus.INVALID


def test_ccomp4a_preserves_linked_bus_and_machine_ids() -> None:
    """Keep three quoted machine identifiers distinct from numeric buses.

    :return: None.
    """
    source: str = "1 'CCOMP4A' '01' 2 '02' 3 'A' 4 'B' 1 -1 .5 -.5 2 .1 -.1 /"
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == (2, '02', 3, 'A', 4, 'B')
    assert tuple(parameter.name for parameter in record.parameters) == (
        'K1', 'K2', 'K3', 'K4', 'KC', 'VMAX', 'VMIN',
    )
    assert RawDyrV33().get_model_schema('CCOMP4A') is None
    assert RawDyrV34().get_model_schema('CCOMP4A') is None
    assert parse_dyr(source.replace("'02'", "'003'"), version=35).records[0].status is RecordStatus.INVALID
    assert parse_dyr(source.replace(' 2 .1 -.1', ' 2 .1'), version=35).records[0].status is RecordStatus.INVALID


def test_ccomp4u1_preserves_33_wrapper_allocation_and_linked_ids() -> None:
    """Retain the exact 33.10 CCOMP4U1 wrapper contract and character IDs.

    :return: None.
    """
    source: str = (
        "1 'USRMDL' '01' 'CCOMP4U1' 2 0 6 7 0 5 "
        "2 '02' 3 '03' 4 '04' 1 -1 0 0 2 .1 -.1 /"
    )
    record: DyrRecord = parse_dyr(source, version=33).records[0]
    assert record.status is RecordStatus.VALID
    assert record.model == 'USRMDL'
    assert record.user_header is not None
    assert record.user_header.model_type_code == 2
    assert record.user_header.call_type == 0
    assert record.user_header.icon_count == 6
    assert record.user_header.constant_count == 7
    assert record.user_header.state_count == 0
    assert record.user_header.variable_count == 5
    assert record.icons == (2, '02', 3, '03', 4, '04')
    assert tuple(parameter.name for parameter in record.parameters) == (
        'K1','K2','K3','K4','KC','VMAX','VMIN',
    )
    assert RawDyrV33().get_user_model_schema('CCOMP4U1') is not None
    assert RawDyrV34().get_user_model_schema('CCOMP4U1') is None
    assert parse_dyr(source.replace(' 2 0 6 7 0 5 ', ' 2 0 5 7 0 5 '), version=33).records[0].status is RecordStatus.INVALID
