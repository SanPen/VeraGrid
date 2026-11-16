# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the two memories and MW limits of the auxiliary frequency response."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.auxiliary_signals.cpaaut import (
    build_cpaaut_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def test_auxiliary_frequency_washout_lag_and_output_limit() -> None:
    """A frequency step moves both memories before the bounded MW output.

    :return: None.
    """
    block: Block = build_cpaaut_template(
        VarFactory(), gain_mw_per_pu=100., washout_time=2., lag_time=.5,
        minimum_mw=-.5, maximum_mw=.5,
    ).block
    assert len(block.state_vars) == 2
    assert len(block.in_vars) == 1
    values: dict[int, float] = dict()
    parameter: Var
    expression: Const
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        values[parameter.uid] = float(expression.value)
    values[block.in_vars[0].uid] = .02
    for state in block.state_vars:
        values[state.uid] = 0.
    signal: Var
    equation: object
    for signal, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        values[signal.uid] = 0.
        values[signal.uid] = -equation.eval_uid(values)
    assert block.state_eqs[0].eval_uid(values) == pytest.approx(.01)
    assert block.state_eqs[1].eval_uid(values) == pytest.approx(.04)
    assert values[block.out_vars[0].uid] == pytest.approx(0.)
    values[block.state_vars[1].uid] = .01
    output_equation: object = block.algebraic_eqs[-1]
    values[block.out_vars[0].uid] = 0.
    values[block.out_vars[0].uid] = -output_equation.eval_uid(values)
    assert values[block.out_vars[0].uid] == pytest.approx(.5)
    values[block.state_vars[0].uid] = .02
    transient_equation: object = block.algebraic_eqs[0]
    values[block.algebraic_vars[0].uid] = 0.
    values[block.algebraic_vars[0].uid] = -transient_equation.eval_uid(values)
    assert values[block.algebraic_vars[0].uid] == pytest.approx(0.)


def test_auxiliary_frequency_catalogue_and_invalid_times() -> None:
    """Expose the controller through the native catalogue with physical times.

    :return: None.
    """
    block: Block = build_international_standard_template(
        InternationalStandardModel.CPAAUT, VarFactory(), 'auxiliary',
    ).block
    assert len(block.state_vars) == 2
    assert len(block.out_vars) == 1
    with pytest.raises(ValueError):
        build_cpaaut_template(VarFactory(), washout_time=0.)
    with pytest.raises(ValueError):
        build_cpaaut_template(VarFactory(), lag_time=0.)
    with pytest.raises(ValueError):
        build_cpaaut_template(VarFactory(), minimum_mw=1.)
