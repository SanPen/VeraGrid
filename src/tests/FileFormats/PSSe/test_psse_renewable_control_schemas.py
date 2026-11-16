# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Direct PSS/E 35.2 renewable electrical and plant record layouts."""

import pytest

from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33
from VeraGridEngine.IO.raw.versioned.v34.dyr import RawDyrV34


def test_reeca1_direct_schema_preserves_six_icons_and_45_constants() -> None:
    """Retain the full electrical-control data sheet in its documented order.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 46))
    source: str = "1 'REECA1' '01' 0 0 0 1 0 1 " + values + ' /'
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == (0, 0, 0, 1, 0, 1)
    assert len(record.parameters) == 45
    assert record.parameters[0].name == 'VDIP'
    assert record.parameters[24].name == 'DPMIN'
    assert record.parameters[44].name == 'IP4'
    assert RawDyrV33().get_model_schema('REECA1') is None
    assert RawDyrV34().get_model_schema('REECA1') is None


def test_wtdta1_direct_schema_preserves_five_shaft_constants() -> None:
    """Retain the 35.2 drive-train record without promoting its binding.

    :return: None.
    """
    record: DyrRecord = parse_dyr("1 'WTDTA1' '01' 4.0 0.1 0.25 2.0 1.0 /", version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'H', 'DAMP', 'HTFRAC', 'FREQ1', 'DSHAFT',
    )
    assert RawDyrV33().get_model_schema('WTDTA1') is None
    assert RawDyrV34().get_model_schema('WTDTA1') is None
    short_record: DyrRecord = parse_dyr("1 'WTDTA1' '01' 4.0 0.1 0.25 2.0 /", version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt12t1_direct_schema_preserves_type_1_2_shaft_constants() -> None:
    """Keep the 35.2 Type 1/2 shaft separate from the Type 3/4 sheet.

    :return: None.
    """
    record: DyrRecord = parse_dyr("1 'WT12T1' '01' 4.0 0.1 0.25 2.0 1.0 /", version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'H', 'DAMP', 'HTFRAC', 'FREQ1', 'DSHAFT',
    )
    assert RawDyrV33().get_model_schema('WT12T1') is None
    assert RawDyrV34().get_model_schema('WT12T1') is None
    short_record: DyrRecord = parse_dyr("1 'WT12T1' '01' 4.0 0.1 0.25 2.0 /", version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt1g1_direct_schema_preserves_type_1_machine_constants() -> None:
    """Retain the ten 35.2 induction-machine fields before source binding.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 11))
    record: DyrRecord = parse_dyr("1 'WT1G1' '01' " + values + ' /', version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'TPO', 'TPPO', 'X', 'XP', 'XPP', 'XL', 'E1', 'SE1', 'E2', 'SE2',
    )
    assert RawDyrV33().get_model_schema('WT1G1') is None
    assert RawDyrV34().get_model_schema('WT1G1') is None
    short_record: DyrRecord = parse_dyr("1 'WT1G1' '01' " +
                                        ' '.join(str(index) for index in range(1, 10)) + ' /', version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt2g1_direct_schema_preserves_type_2_machine_curve() -> None:
    """Retain all 19 Type 2 machine and power-slip curve fields.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 20))
    record: DyrRecord = parse_dyr("1 'WT2G1' '01' " + values + ' /', version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'XA', 'XM', 'X1', 'R_ROT_MACH', 'R_ROT_MAX', 'E1', 'SE1', 'E2', 'SE2',
        'POWER_REF_1', 'POWER_REF_2', 'POWER_REF_3', 'POWER_REF_4', 'POWER_REF_5',
        'SLIP_1', 'SLIP_2', 'SLIP_3', 'SLIP_4', 'SLIP_5',
    )
    assert RawDyrV33().get_model_schema('WT2G1') is None
    assert RawDyrV34().get_model_schema('WT2G1') is None
    short_record: DyrRecord = parse_dyr("1 'WT2G1' '01' " +
                                        ' '.join(str(index) for index in range(1, 19)) + ' /', version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt2e1_direct_schema_preserves_rotor_resistance_controls() -> None:
    """Retain the six 35.2 controller CONs in documented order.

    :return: None.
    """
    record: DyrRecord = parse_dyr("1 'WT2E1' '01' .05 .05 1.0 1.0 .2 0.0 /", version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'TSP', 'TPE', 'TI', 'KP', 'ROTRV_MAX', 'ROTRV_MIN',
    )
    assert RawDyrV33().get_model_schema('WT2E1') is None
    assert RawDyrV34().get_model_schema('WT2E1') is None
    short_record: DyrRecord = parse_dyr("1 'WT2E1' '01' .05 .05 1.0 1.0 .2 /", version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wtara1_direct_schema_preserves_pitch_constants() -> None:
    """Keep the 35.2 aerodynamic record inspectable without conversion.

    :return: None.
    """
    record: DyrRecord = parse_dyr("1 'WTARA1' '01' 0.007 2.0 /", version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == ('KA', 'THETA0')
    assert RawDyrV33().get_model_schema('WTARA1') is None
    assert RawDyrV34().get_model_schema('WTARA1') is None
    short_record: DyrRecord = parse_dyr("1 'WTARA1' '01' 0.007 /", version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt12a1_direct_schema_preserves_pseudo_governor_constants() -> None:
    """Keep the 35.2 Type 1/2 controller record in source order.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 9))
    record: DyrRecord = parse_dyr("1 'WT12A1' '01' " + values + ' /', version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'DROOP', 'KP', 'TI', 'T1', 'T2', 'TP', 'LIMMAX', 'LIMMIN',
    )
    assert RawDyrV33().get_model_schema('WT12A1') is None
    assert RawDyrV34().get_model_schema('WT12A1') is None
    short_record: DyrRecord = parse_dyr("1 'WT12A1' '01' " +
                                        ' '.join(str(index) for index in range(1, 8)) + ' /', version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wt12a1u_b_user_wrapper_preserves_active_stall_allocation() -> None:
    """Keep the 35.2 active-stall wrapper distinct from direct WT12A1.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 15))
    source: str = "1 'USRMDL' '01' 'WT12A1U_B' 105 0 1 14 3 2 0 " + values + ' /'
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.user_schema is not None
    assert record.icons == (0,)
    assert tuple(parameter.name for parameter in record.parameters) == (
        'TR', 'RMAX', 'RMIN', 'T0', 'PMIN', 'PSET', 'VT1', 'T1',
        'VT2', 'T2', 'VT3', 'T3', 'VT4', 'T4',
    )
    assert parse_dyr(source.replace('105 0 1 14 3 2', '105 0 1 14 3 3'),
                     version=35).records[0].status is RecordStatus.INVALID
    assert parse_dyr(source.replace(' 14 3 2 0 ', ' 14 3 2 '),
                     version=35).records[0].status is RecordStatus.INVALID
    assert parse_dyr(source, version=33).records[0].user_schema is None
    assert parse_dyr(source, version=34).records[0].user_schema is None


def test_wtpta1_direct_schema_preserves_pitch_limits() -> None:
    """Retain the ten 35.2 Type 3 pitch constants in source order.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 11))
    record: DyrRecord = parse_dyr("1 'WTPTA1' '01' " + values + ' /', version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert tuple(parameter.name for parameter in record.parameters) == (
        'KIW', 'KPW', 'KIC', 'KPC', 'KCC', 'TP', 'TETAMAX', 'TETAMIN', 'RTETAMAX', 'RTETAMIN',
    )
    assert RawDyrV33().get_model_schema('WTPTA1') is None
    assert RawDyrV34().get_model_schema('WTPTA1') is None
    short_record: DyrRecord = parse_dyr("1 'WTPTA1' '01' " +
                                        ' '.join(str(index) for index in range(1, 10)) + ' /', version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


def test_wttqa1_direct_schema_preserves_tflag_and_turbine_rating() -> None:
    """Retain all fifteen torque constants and the source mode selector.

    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 16))
    record: DyrRecord = parse_dyr("1 'WTTQA1' '01' 0 " + values + ' /', version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == (0,)
    assert len(record.parameters) == 15
    assert record.parameters[0].name == 'KPP'
    assert record.parameters[-1].name == 'TRATE'
    assert RawDyrV33().get_model_schema('WTTQA1') is None
    assert RawDyrV34().get_model_schema('WTTQA1') is None
    short_record: DyrRecord = parse_dyr("1 'WTTQA1' '01' 0 " +
                                        ' '.join(str(index) for index in range(1, 15)) + ' /', version=35).records[0]
    assert short_record.status is RecordStatus.INVALID


@pytest.mark.parametrize('model', ('REPCA1', 'REPCTA1'))
def test_plant_control_schema_retains_quoted_branch_id(model: str) -> None:
    """Keep type-3 and type-4 plant records distinct with the same layout.

    :param model: Source model name for the plant-control command path.
    :return: None.
    """
    values: str = ' '.join(str(index) for index in range(1, 28))
    source: str = "1 '" + model + "' '01' 2 3 4 '02' 1 1 0 " + values + ' /'
    record: DyrRecord = parse_dyr(source, version=35).records[0]
    assert record.status is RecordStatus.VALID
    assert record.icons == (2, 3, 4, '02', 1, 1, 0)
    assert len(record.parameters) == 27
    assert record.parameters[0].name == 'TFLTR'
    assert record.parameters[26].name == 'DUP'
    assert RawDyrV33().get_model_schema(model) is None
    assert RawDyrV34().get_model_schema(model) is None


def test_renewable_control_records_reject_missing_tail_constants() -> None:
    """Reject short records before any control assembly can use them.

    :return: None.
    """
    short_reeca: str = "1 'REECA1' '01' 0 0 0 1 0 1 " + ' '.join(str(index) for index in range(1, 45)) + ' /'
    short_repca: str = "1 'REPCA1' '01' 2 3 4 '02' 1 1 0 " + ' '.join(str(index) for index in range(1, 27)) + ' /'
    assert parse_dyr(short_reeca, version=35).records[0].status is RecordStatus.INVALID
    assert parse_dyr(short_repca, version=35).records[0].status is RecordStatus.INVALID
