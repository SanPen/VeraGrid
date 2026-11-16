# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""PSS/E CIMTR2 induction-motor template checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import (
    build_international_standard_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.cimtr2 import (
    Cimtr2Parameters,
    build_cimtr2_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def test_cimtr2_uses_motor_signs_and_source_torque_exponent() -> None:
    """Map PSS/E's ``Tnom * speed**D`` law into the shared motor kernel."""
    settings: Cimtr2Parameters = Cimtr2Parameters(
        t_prime=0.7, t_double_prime=0.08, inertia=1.2,
        x=2.4, x_prime=0.55, x_double_prime=0.22,
        x_leakage=0.12, load_torque_exponent=0.35, ra=0.03,
    )
    template: RmsModelTemplate = build_cimtr2_template(
        VarFactory(), 'CIMTR2_MOTOR', settings,
    )
    parameters: dict[str, float] = dict()
    variable: Var
    for variable in template.block.event_dict:
        expression: Expr | Const = template.block.event_dict[variable]
        if isinstance(expression, Const):
            parameters[variable.name] = expression.value
        else:
            pass

    assert len(template.block.state_vars) == 5
    assert template.block.in_vars[2].name == 'TLoad0Pu_CIMTR2_MOTOR'
    assert any(variable.name == 'PLoadPu_CIMTR2_MOTOR'
               for variable in template.block.algebraic_vars)
    assert parameters['D_CIMTR2_MOTOR'] == 1.0
    assert parameters['E_CIMTR2_MOTOR'] == settings.load_torque_exponent
    assert parameters['Damp_CIMTR2_MOTOR'] == 0.0
    assert parameters['RaPu_CIMTR2_MOTOR'] == settings.ra
    assert parameters['H_CIMTR2_MOTOR'] == settings.inertia

    torque_balance: Expr = template.block.algebraic_eqs[3]
    torque_values: dict[str, float] = dict(
        (variable.name, 0.0) for variable in torque_balance.get_vars()
    )
    torque_values.update((name, value) for name, value in parameters.items())
    torque_values['OmegaPu_CIMTR2_MOTOR'] = 1.1
    torque_values['TLoad0Pu_CIMTR2_MOTOR'] = 2.0
    torque_values['TLoadPu_CIMTR2_MOTOR'] = 2.0 * 1.1 ** settings.load_torque_exponent
    assert torque_balance.eval(**torque_values) == pytest.approx(0.0)


def test_cimtr2_factory_builds_its_distinct_motor_template() -> None:
    """Expose CIMTR2 through the international-standard factory."""
    template: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.CIMTR2, VarFactory(), 'CIMTR2_FACTORY',
    )

    assert template.name == 'CIMTR2_FACTORY'
    assert template.block.name == 'CIMTR2_FACTORY'
    assert template.block.in_vars[2].name == 'TLoad0Pu_CIMTR2_FACTORY'


def test_cimtr2_rejects_unrepresented_saturation_and_single_cage() -> None:
    """Keep unsupported source reductions visible instead of discarding fields."""
    with pytest.raises(ValueError, match='saturation'):
        build_cimtr2_template(
            VarFactory(), 'CIMTR2_SATURATION', Cimtr2Parameters(se1=0.1, se2=0.2),
        )
    with pytest.raises(ValueError, match='two-cage'):
        build_cimtr2_template(
            VarFactory(), 'CIMTR2_SINGLE_CAGE', Cimtr2Parameters(t_double_prime=0.0),
        )
