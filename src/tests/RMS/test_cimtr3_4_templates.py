# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""PSS/E CIMTR3/CIMTR4 induction-machine template checks."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import (
    build_international_standard_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr3 import (
    Cimtr3Parameters,
    build_cimtr3_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr4 import (
    Cimtr4Parameters,
    build_cimtr4_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def test_cimtr3_has_generator_signs_and_angle_deviation_state() -> None:
    """Build the six-state generator and verify its rotor-angle kinematics."""
    template: RmsModelTemplate = build_cimtr3_template(
        VarFactory(), 'CIMTR3_GEN',
        Cimtr3Parameters(synchronous_power=1.3, switch=1),
    )
    angle_equation: Expr = template.block.state_eqs[5]
    values: dict[str, float] = dict(
        (variable.name, 0.0) for variable in angle_equation.get_vars()
    )
    values['FNomHz_CIMTR3_GEN'] = 50.0
    values['OmegaPu_CIMTR3_GEN'] = 0.98

    assert len(template.block.state_vars) == 6
    assert template.block.state_vars[5].name == 'AngleDeviationRad_CIMTR3_GEN'
    assert angle_equation.eval(**values) == pytest.approx(2.0 * math.pi * 50.0 * -0.02)
    assert any(variable.name == 'PGenPu_CIMTR3_GEN'
               for variable in template.block.algebraic_vars)


def test_cimtr4_has_motor_signs_torque_exponent_and_angle_state() -> None:
    """Build the six-state motor and map its speed-dependent torque law."""
    template: RmsModelTemplate = build_cimtr4_template(
        VarFactory(), 'CIMTR4_MOTOR',
        Cimtr4Parameters(load_torque_exponent=0.4, synchronous_torque=-1.2),
    )
    parameters: dict[str, float] = dict()
    variable: Var
    for variable in template.block.event_dict:
        expression: Expr | Const = template.block.event_dict[variable]
        if isinstance(expression, Const):
            parameters[variable.name] = expression.value
        else:
            pass

    assert len(template.block.state_vars) == 6
    assert template.block.in_vars[2].name == 'TLoad0Pu_CIMTR4_MOTOR'
    assert 'PLoadPu_CIMTR4_MOTOR' in tuple(
        variable.name for variable in template.block.algebraic_vars
    )
    assert parameters['D_CIMTR4_MOTOR'] == pytest.approx(1.0)
    assert parameters['E_CIMTR4_MOTOR'] == pytest.approx(0.4)
    assert parameters['Damp_CIMTR4_MOTOR'] == 0.0

    torque_balance: Expr = template.block.algebraic_eqs[3]
    torque_values: dict[str, float] = dict(
        (variable.name, 0.0) for variable in torque_balance.get_vars()
    )
    torque_values.update((name, value) for name, value in parameters.items())
    torque_values['OmegaPu_CIMTR4_MOTOR'] = 1.1
    torque_values['TLoad0Pu_CIMTR4_MOTOR'] = 2.0
    torque_values['TLoadPu_CIMTR4_MOTOR'] = 2.0 * 1.1 ** 0.4
    assert torque_balance.eval(**torque_values) == pytest.approx(0.0)


def test_cimtr3_and_cimtr4_are_available_from_the_factory() -> None:
    """Expose both source identities as distinct factory models."""
    cimtr3: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.CIMTR3, VarFactory(), 'CIMTR3_FACTORY',
    )
    cimtr4: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.CIMTR4, VarFactory(), 'CIMTR4_FACTORY',
    )

    assert cimtr3.name == 'CIMTR3_FACTORY'
    assert cimtr4.name == 'CIMTR4_FACTORY'
    assert len(cimtr3.block.state_vars) == 6
    assert len(cimtr4.block.state_vars) == 6


def test_cimtr3_rejects_saturation_and_invalid_switch_value() -> None:
    """Gate unsupported saturation and malformed switch flags."""
    with pytest.raises(ValueError, match='saturation'):
        build_cimtr3_template(
            VarFactory(), 'CIMTR3_SAT', Cimtr3Parameters(se1=0.1, se2=0.2),
        )
    with pytest.raises(ValueError, match='switch must be 0 or 1'):
        build_cimtr3_template(
            VarFactory(), 'CIMTR3_SWITCH', Cimtr3Parameters(switch=2),
        )


def test_cimtr4_rejects_saturation_and_invalid_starting_torque() -> None:
    """Gate unsupported saturation and invalid negative SYN-TOR data."""
    with pytest.raises(ValueError, match='saturation'):
        build_cimtr4_template(
            VarFactory(), 'CIMTR4_SAT', Cimtr4Parameters(se1=0.1, se2=0.2),
        )
    with pytest.raises(ValueError, match='negative SYNTOR'):
        build_cimtr4_template(
            VarFactory(), 'CIMTR4_TORQUE', Cimtr4Parameters(synchronous_torque=0.0),
        )
