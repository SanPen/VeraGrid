# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native IEEE ST10C static excitation model checks."""
from __future__ import annotations

import cmath
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st10c import (
    St10cParameters, build_st10c_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Var


def test_st10c_default_template_has_expected_open_ports_and_states() -> None:
    """Build the AVR and terminal-fed source with the documented topology.

    :return: None.
    """
    template = build_st10c_template(VarFactory())

    assert len(template.block.in_vars) == 11
    assert len(template.block.out_vars) == 1
    assert len(template.block.state_vars) == 4
    assert template.block.out_vars[0].name == 'EFD_ST10C'


def test_st10c_rejects_invalid_regulator_or_source_limits() -> None:
    """Keep invalid physical limits out of a symbolic template.

    :return: None.
    """
    with pytest.raises(ValueError):
        St10cParameters(vrmin=2.0, vrmax=1.0)
    with pytest.raises(ValueError):
        build_st10c_template(VarFactory(), field_voltage0=2.0, parameters=St10cParameters(vbmax=1.5))


def test_st10c_potential_source_matches_phasor_equation() -> None:
    """Evaluate the terminal-fed source equation with nonzero phase and current.

    :return: None.
    """
    parameters: St10cParameters = St10cParameters(
        kp=1.2, ki=0.15, xl=0.3, thetap_rad=0.2, kc=0.0, vbmax=20.0,
    )
    block: Block = build_st10c_template(
        VarFactory(), 'ST10C_PHASOR', parameters,
        terminal_voltage0=1.0 + 0.2j, terminal_current0=0.3 - 0.1j,
    ).block
    values: dict[int, float] = dict()
    variables: tuple[Var, ...] = tuple(block.in_vars) + tuple(block.event_dict)
    for variable in variables:
        if variable.name.startswith('VTR_'):
            values[variable.uid] = 1.0
        elif variable.name.startswith('VTI_'):
            values[variable.uid] = 0.2
        elif variable.name.startswith('ITR_'):
            values[variable.uid] = 0.3
        elif variable.name.startswith('ITI_'):
            values[variable.uid] = -0.1
        elif variable.name.startswith('IFD_'):
            values[variable.uid] = 0.0
        else:
            default: Expr | None = block.event_dict.get(variable, None)
            if isinstance(default, Const) and default.value is not None:
                values[variable.uid] = float(default.value)
            else:
                pass
    else:
        pass
    supply: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name == 'AvailableFieldSupply_ST10C_PHASOR'
    )
    equation: BinOp = next(
        equation for equation in block.algebraic_eqs
        if isinstance(equation.left, Var) and equation.left.uid == supply.uid
    )
    actual: float = float(equation.right.eval_uid(values))
    rotated_gain: complex = parameters.kp * cmath.exp(1j * parameters.thetap_rad)
    expected: complex = (
        rotated_gain * (1.0 + 0.2j)
        + 1j * (parameters.ki + rotated_gain * parameters.xl) * (0.3 - 0.1j)
    )
    assert actual == pytest.approx(abs(expected))
