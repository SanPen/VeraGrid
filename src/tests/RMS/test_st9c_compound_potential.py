# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Live phasor compound-source equations in the ST9C native template."""
from __future__ import annotations

import cmath

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st9c import (
    St9cParameters, build_st9c_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


def equation_value(block: Block, name: str, values: dict[int, float]) -> float:
    """Evaluate one ordered algebraic equation using caller-supplied values.

    :param block: ST9C symbolic block.
    :param name: Left-hand algebraic variable name.
    :param values: Numeric values indexed by symbolic variable UID.
    :return: Evaluated right-hand side.
    """
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var) and equation.left.name == name:
            return float(equation.right.eval_uid(values))
        else:
            pass
    raise AssertionError('Missing ST9C algebraic equation: ' + name)


def test_st9c_compound_potential_uses_live_terminal_phasors() -> None:
    """Check ``VE=|KP∠THETAP·VT+j(KI+KP∠THETAP·XL)·IT|``.

    :return: None.
    """
    block: Block = build_st9c_template(VarFactory()).block
    by_name: dict[str, Var] = dict()
    for variable in block.in_vars:
        by_name[variable.name] = variable
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var):
            by_name[equation.left.name] = equation.left
        else:
            pass
    for variable in block.event_dict:
        by_name[variable.name] = variable
    terminal_voltage: complex = 1.0 + 0.3j
    terminal_current: complex = 0.2 - 0.1j
    kp: float = 1.1
    ki: float = 0.2
    theta: float = 0.25
    reactance: float = 0.4
    values: dict[int, float] = {
        by_name['avr.utPu.re_St9c'].uid: terminal_voltage.real,
        by_name['avr.utPu.im_St9c'].uid: terminal_voltage.imag,
        by_name['avr.itPu.re_St9c'].uid: terminal_current.real,
        by_name['avr.itPu.im_St9c'].uid: terminal_current.imag,
        by_name['avr.potentialCircuit.Kp_St9c'].uid: kp,
        by_name['avr.potentialCircuit.Ki_St9c'].uid: ki,
        by_name['avr.potentialCircuit.Theta_St9c'].uid: theta,
        by_name['avr.potentialCircuit.X_St9c'].uid: reactance,
    }
    for variable_name in (
        'avr.potentialCircuit.v1.re_St9c',
        'avr.potentialCircuit.v1.im_St9c',
        'avr.potentialCircuit.v2.re_St9c',
        'avr.potentialCircuit.v2.im_St9c',
        'avr.potentialCircuit.vE_St9c',
    ):
        variable: Var = by_name[variable_name]
        values[variable.uid] = equation_value(block, variable_name, values)
    rotated_transformer: complex = kp * cmath.exp(1j * theta)
    expected_source: complex = (
        rotated_transformer * terminal_voltage
        + 1j * (ki + rotated_transformer * reactance) * terminal_current
    )
    assert values[by_name['avr.potentialCircuit.vE_St9c'].uid] == pytest.approx(
        abs(expected_source)
    )
    assert tuple(variable.name for variable in block.in_vars[:4]) == (
        'avr.utPu.re_St9c', 'avr.utPu.im_St9c',
        'avr.itPu.re_St9c', 'avr.itPu.im_St9c',
    )


def test_st9c_source_coefficients_parameterize_native_template() -> None:
    """Place every independent PSS/E physical coefficient on the native graph.

    :return: None.
    """
    parameters: St9cParameters = St9cParameters(
        tr=0.1, tcd=0.2, tbd=0.3, za=0.04, ka=11.0, ku=12.0,
        ta=0.5, tauel=0.6, vrmax=4.0, vrmin=-3.0, kas=2.0,
        tas=0.7, kp=1.3, thetap_rad=0.8, ki=1.4, xl=0.9,
        kc=0.15, vbmax=3.0,
    )
    block: Block = build_st9c_template(VarFactory(), 'ST9C_PARAMETERS', parameters).block
    expected: dict[str, float] = {
        'avr.tR_ST9C_PARAMETERS': 0.1,
        'avr.tCd_ST9C_PARAMETERS': 0.2,
        'avr.tBd_ST9C_PARAMETERS': 0.3,
        'avr.ZaPu_ST9C_PARAMETERS': 0.04,
        'avr.Ka_ST9C_PARAMETERS': 11.0,
        'avr.Ku_ST9C_PARAMETERS': 12.0,
        'avr.tA_ST9C_PARAMETERS': 0.5,
        'avr.tAUel_ST9C_PARAMETERS': 0.6,
        'avr.VrMaxPu_ST9C_PARAMETERS': 4.0,
        'avr.VrMinPu_ST9C_PARAMETERS': -3.0,
        'avr.Kas_ST9C_PARAMETERS': 2.0,
        'avr.tAs_ST9C_PARAMETERS': 0.7,
        'avr.Kp_ST9C_PARAMETERS': 1.3,
        'avr.Thetap_ST9C_PARAMETERS': 0.8,
        'avr.Ki_ST9C_PARAMETERS': 1.4,
        'avr.XlPu_ST9C_PARAMETERS': 0.9,
        'avr.Kc_ST9C_PARAMETERS': 0.15,
        'avr.VbMaxPu_ST9C_PARAMETERS': 3.0,
    }
    actual: dict[str, float] = dict()
    for variable, expression in block.event_dict.items():
        if variable.name in expected and isinstance(expression, Const):
            actual[variable.name] = expression.value
        else:
            pass
    assert actual == expected


def test_st9c_rejects_unrealizable_physical_coefficients() -> None:
    """Reject zero denominator times and unordered regulator limits.

    :return: None.
    """
    with pytest.raises(ValueError):
        St9cParameters(tbd=0.0)
    with pytest.raises(ValueError):
        St9cParameters(ta=0.0)
    with pytest.raises(ValueError):
        St9cParameters(vrmin=5.0)
