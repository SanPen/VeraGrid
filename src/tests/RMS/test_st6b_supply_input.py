# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Verify ST6B supply multiplication and filtered derivative equations."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.st6b import (
    build_st6b_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Var


def _equations_by_name(block: Block) -> dict[str, Expr]:
    """Index explicit algebraic right-hand sides by their output variable.

    :param block: ST6B native block.
    :return: Algebraic equations keyed by normalized signal name.
    """
    equations: dict[str, Expr] = dict()
    equation: Expr
    for equation in block.algebraic_eqs:
        if isinstance(equation, BinOp) and isinstance(equation.left, Var):
            equations[equation.left.name] = equation.right
        else:
            pass
    return equations


def test_st6b_vb_input_multiplies_field_regulator_output() -> None:
    """The host-owned available supply scales the limited regulator voltage.

    :return: None.
    """
    block = build_st6b_template(VarFactory()).block
    assert len(block.state_vars) == 4
    supply: Var = block.in_vars[-1]
    assert supply.name == 'avr.VbPu_St6b'
    equations: dict[str, Expr] = _equations_by_name(block)
    assert supply in equations['EfdPu_St6b'].get_vars()
    values: dict[int, float] = dict()
    values[supply.uid] = 0.8
    field_regulator: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name == 'FieldRegulatorPu_St6b'
    )
    values[field_regulator.uid] = 0.75
    assert equations['EfdPu_St6b'].eval_uid(values) == pytest.approx(0.6)


def test_st6b_derivative_channel_matches_filtered_pd_equations() -> None:
    """Evaluate the IEEE ST6B filtered derivative state and output equations.

    :return: None.
    """
    block = build_st6b_template(VarFactory()).block
    values: dict[int, float] = dict()
    parameter: Var
    expression: Expr
    for parameter, expression in block.event_dict.items():
        if parameter.name == 'avr.Kda_St6b':
            values[parameter.uid] = 2.0
        elif parameter.name == 'avr.tDa_St6b':
            values[parameter.uid] = 0.5
        elif isinstance(expression, Const):
            values[parameter.uid] = float(expression.value)
        else:
            pass
    values[block.in_vars[1].uid] = 0.0
    values[block.in_vars[2].uid] = 0.0
    values[block.in_vars[3].uid] = 0.98
    values[block.in_vars[4].uid] = 1.0
    values[block.in_vars[5].uid] = 0.0
    values[block.state_vars[0].uid] = 0.98
    values[block.state_vars[2].uid] = 0.0
    assert block.state_eqs[2].eval_uid(values) == pytest.approx(-0.16)

    equations: dict[str, Expr] = _equations_by_name(block)
    assert equations['DerivativeOutputPu_St6b'].eval_uid(values) == pytest.approx(0.08)
