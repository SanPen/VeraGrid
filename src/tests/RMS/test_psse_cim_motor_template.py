# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Structural checks for native PSS/E CIM load-motor equations."""

from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.psse_cim_motor import (
    PsseCimMotorModel,
    PsseCimMotorParameters,
    PsseCimMotorType,
    build_psse_cim_motor_template,
    calculate_cimw_c0,
    solve_psse_cim_motor_operating_point,
)
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType


def _motor_parameters(
        second_cage: bool = True,
        relay_enabled: bool = True,
) -> PsseCimMotorParameters:
    """Return a representative, source-valid PSS/E CIM parameter set.

    :param second_cage: Select the two-cage or single-cage source reduction.
    :param relay_enabled: Enable the voltage timer and breaker delay.
    :return: PSS/E motor parameters on a 40 MVA motor base.
    """
    second_cage_resistance: float = 0.03 if second_cage else 0.0
    second_cage_reactance: float = 0.05 if second_cage else 0.0
    voltage_threshold: float = 0.7 if relay_enabled else 0.0
    return PsseCimMotorParameters(
        ra=0.01,
        xa=0.1,
        xm=3.0,
        r1=0.02,
        x1=0.15,
        r2=second_cage_resistance,
        x2=second_cage_reactance,
        e1=1.0,
        se1=0.06,
        e2=1.2,
        se2=0.6,
        mbase=0.0,
        pmult=0.4,
        load_mw=100.0,
        system_base_mva=100.0,
        inertia=0.5,
        vi=voltage_threshold,
        ti=30.0,
        tb=2.0,
        damping=1.0,
        tnom=1.0,
        a=0.2,
        b=0.3,
        d=0.1,
        exponent=2.0,
        c0=0.4,
        torque_reference=0.8,
    )


@pytest.mark.parametrize(
    'model',
    (PsseCimMotorModel.CIM5, PsseCimMotorModel.CIM6, PsseCimMotorModel.CIMW),
)
@pytest.mark.parametrize(
    'motor_type',
    (PsseCimMotorType.TYPE_A, PsseCimMotorType.TYPE_B),
)
def test_build_psse_cim_motor_templates(
        model: PsseCimMotorModel,
        motor_type: PsseCimMotorType,
) -> None:
    """Build all PSS/E torque-law and circuit-type combinations.

    :param model: Torque-law model under test.
    :param motor_type: Type A or B cage circuit under test.
    :return: None.
    """
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=VarFactory(),
        model=model,
        motor_type=motor_type,
        parameters=_motor_parameters(),
        name=f'{model.value}_{motor_type.name}',
    )

    assert template.tpe == DeviceType.LoadDevice
    assert len(template.block.state_vars) == 5
    assert len(template.block.state_eqs) == 5
    assert len(template.block.algebraic_vars) == len(template.block.algebraic_eqs)
    assert len(template.block.procedural_logic) == 3
    assert VarPowerFlowReferenceType.P in template.block.external_mapping
    assert VarPowerFlowReferenceType.Q in template.block.external_mapping


def test_single_cage_and_disabled_voltage_relay() -> None:
    """Retain the source's single-cage reduction and VI=0 relay disable.

    :return: None.
    """
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=VarFactory(),
        model=PsseCimMotorModel.CIM5,
        motor_type=PsseCimMotorType.TYPE_A,
        parameters=_motor_parameters(second_cage=False, relay_enabled=False),
    )

    assert len(template.block.state_vars) == 5
    assert len(template.block.procedural_logic) == 0


def test_cimw_c0_uses_initialized_speed() -> None:
    """Calculate CIMW C0 from the source torque curve at initial speed.

    :return: None.
    """
    c0: float = calculate_cimw_c0(
        coefficient_a=0.2,
        coefficient_b=0.3,
        coefficient_d=0.1,
        exponent=2.0,
        initialized_speed=0.95,
    )

    assert c0 == pytest.approx(1.0 - 0.2 * 0.95 ** 2 - 0.3 * 0.95 - 0.1 * 0.95 ** 2)


def test_invalid_single_cage_record_rejects_partial_second_cage() -> None:
    """Reject a record that supplies only one of the two cage-two values.

    :return: None.
    """
    parameters: PsseCimMotorParameters = _motor_parameters(second_cage=False)
    parameters.r2 = 0.03

    with pytest.raises(ValueError, match='cage impedances'):
        build_psse_cim_motor_template(
            vf=VarFactory(),
            model=PsseCimMotorModel.CIM5,
            motor_type=PsseCimMotorType.TYPE_A,
            parameters=parameters,
        )


def test_operating_point_seeds_states_torque_and_reactive_correction() -> None:
    """Carry a solved PSS/E motor operating point into template initialization.

    :return: None.
    """
    parameters: PsseCimMotorParameters = _motor_parameters()
    operating_point: tuple[float, float, float, float, float, float, float, float, float] | None = (
        solve_psse_cim_motor_operating_point(
            model=PsseCimMotorModel.CIM6,
            motor_type=PsseCimMotorType.TYPE_A,
            parameters=parameters,
            voltage_magnitude=1.0,
            voltage_angle=0.0,
            active_power_target=0.4,
            reactive_power_target=0.15,
            nominal_frequency_hz=60.0,
        )
    )

    assert operating_point is not None
    parameters.operating_point = operating_point
    template: RmsModelTemplate = build_psse_cim_motor_template(
        vf=VarFactory(),
        model=PsseCimMotorModel.CIM6,
        motor_type=PsseCimMotorType.TYPE_A,
        parameters=parameters,
    )

    assert len(template.block.init_eqs) == 9
    assert len(template.block.event_dict) >= 4
    assert any(variable.name.startswith('ToPu_') for variable in template.block.event_dict)
    assert any(variable.name.startswith('QADJUST_') for variable in template.block.event_dict)
