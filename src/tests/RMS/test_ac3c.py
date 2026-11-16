# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check AC3C's native PID controller and limiter insertion points."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.dc_exciter import RotatingLimiterLocation
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac3c import (
    Ac3cParameters, build_ac3c_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def test_ac3c_builds_pid_memories_and_catalogue_entry() -> None:
    """Build the 28-CON native controller and retain the plotted PID memories."""
    vf: VarFactory = VarFactory()
    template = build_international_standard_template(
        InternationalStandardModel.AC3C, vf, 'AC3C_catalogue',
    )
    block: Block = template.block

    assert len(block.in_vars) == 6
    assert len(block.out_vars) == 3
    assert len(block.state_vars) == 7
    assert block.out_vars[1].name == 'PidOutputPu_AC3C_catalogue'
    assert block.out_vars[2].name == 'avr_leadLag_y_AC3C_catalogue'
    assert len(block.event_dict) >= 6


def test_ac3c_limiters_select_error_sum_or_post_pid_gates() -> None:
    """Route both limiter signals to their selected source locations."""
    summed: Block = build_ac3c_template(VarFactory(), 'AC3C_SUM').block
    gated: Block = build_ac3c_template(
        VarFactory(), 'AC3C_GATE',
        oel_location=RotatingLimiterLocation.TAKEOVER_GATE,
        uel_location=RotatingLimiterLocation.TAKEOVER_GATE,
    ).block
    summed_equations: dict[Var, Expr] = dict(zip(
        summed.algebraic_vars, summed.algebraic_eqs, strict=True,
    ))
    gated_equations: dict[Var, Expr] = dict(zip(
        gated.algebraic_vars, gated.algebraic_eqs, strict=True,
    ))
    summed_error_vars: set[str] = set(
        variable.name for variable in summed_equations[
            next(variable for variable in summed.algebraic_vars
                 if variable.name.startswith('avr.sum1.y_'))
        ].right.get_vars()
    )
    gated_error_vars: set[str] = set(
        variable.name for variable in gated_equations[
            next(variable for variable in gated.algebraic_vars
                 if variable.name.startswith('avr.sum1.y_'))
        ].right.get_vars()
    )
    gated_drive_vars: set[str] = set(
        variable.name for variable in gated_equations[
            next(variable for variable in gated.algebraic_vars
                 if variable.name.startswith('avr.limitedFirstOrder.Gk.y_'))
        ].right.get_vars()
    )

    assert 'avr.UOelPu_AC3C_SUM' in summed_error_vars
    assert 'avr.UUelPu_AC3C_SUM' in summed_error_vars
    assert 'avr.UOelPu_AC3C_GATE' not in gated_error_vars
    assert 'avr.UUelPu_AC3C_GATE' not in gated_error_vars
    assert 'avr.UOelPu_AC3C_GATE' in gated_drive_vars
    assert 'avr.UUelPu_AC3C_GATE' in gated_drive_vars


@pytest.mark.parametrize('settings', (
    Ac3cParameters(kia=0.0),
    Ac3cParameters(kda=0.1, tda=0.0),
    Ac3cParameters(vpidmax=-5.0, vpidmin=5.0),
))
def test_ac3c_rejects_invalid_pid_settings(settings: Ac3cParameters) -> None:
    """Decline PID coefficients that do not define the documented transfer."""
    with pytest.raises(ValueError):
        build_ac3c_template(VarFactory(), 'AC3C_INVALID', settings)
