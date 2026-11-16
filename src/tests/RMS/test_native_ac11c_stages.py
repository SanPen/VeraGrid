# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Structural checks for the AC11C filtered-PI building block."""

import pytest

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.excitation_systems.ac11c import (
    Ac11cLimiterLocation,
    Ac11cParameters,
    Ac11cPowerSource,
    Ac11cPssLocation,
    add_ac11c_pi,
    add_ac11c_filtered_pi,
    build_ac11c_template,
)
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def test_ac11c_filtered_pi_has_integrator_and_filter_states() -> None:
    """The source transfer keeps its PI memory and positive-time filter.

    :return: None.
    """
    control: ControlRealization = ControlRealization(VarFactory(), 'AC11C')
    error: Var = control.input('Error', Const(0.0))
    output: Var = add_ac11c_filtered_pi(
        control, 'AVR', error, Const(0.0), Const(0.0),
        20.0, 2.0, 0.4, 0.5, -5.0, 5.0, Const(0.0),
    )
    assert len(control.block.state_vars) == 2
    assert len(control.block.diff_vars) == 2
    assert output in control.block.state_vars
    assert len(control.block.state_eqs) == 2


def test_ac11c_zero_filter_time_reduces_to_pi_integrator() -> None:
    """A disabled derivative filter introduces no artificial state.

    :return: None.
    """
    control: ControlRealization = ControlRealization(VarFactory(), 'AC11CZero')
    error: Var = control.input('Error', Const(0.0))
    output: Var = add_ac11c_filtered_pi(
        control, 'UEL', error, Const(0.0), Const(0.0),
        10.0, 1.0, 0.0, 0.0, -3.0, 3.0, Const(0.0),
    )
    assert len(control.block.state_vars) == 1
    assert len(control.block.diff_vars) == 1
    assert output in control.block.algebraic_vars


def test_ac11c_oel_pi_has_one_limited_integrator_state() -> None:
    """The OEL branch keeps its single PI memory and output clamp.

    :return: None.
    """
    control: ControlRealization = ControlRealization(VarFactory(), 'AC11COel')
    error: Var = control.input('Error', Const(0.0))
    output: Var = add_ac11c_pi(
        control, 'OEL', error, Const(0.0), 30.0, 2.0,
        -5.0, 5.0, Const(0.0),
    )
    assert len(control.block.state_vars) == 1
    assert len(control.block.diff_vars) == 1
    assert output in control.block.algebraic_vars


def test_ac11c_filtered_pi_rejects_invalid_time() -> None:
    """Reject nonpositive integral time at construction.

    :return: None.
    """
    control: ControlRealization = ControlRealization(VarFactory(), 'AC11CInvalid')
    error: Var = control.input('Error', Const(0.0))
    with pytest.raises(ValueError, match='integral time'):
        add_ac11c_filtered_pi(
            control, 'AVR', error, Const(0.0), Const(0.0),
            20.0, 0.0, 0.4, 0.5, -5.0, 5.0, Const(0.0),
        )


def test_ac11c_template_has_nine_states_and_balanced_algebraics() -> None:
    """The composed voltage controller, sources and exciter close all equations.

    :return: None.
    """
    template: RmsModelTemplate = build_ac11c_template(VarFactory(), 'AC11C')
    assert len(template.block.state_vars) == 9
    assert len(template.block.diff_vars) == 9
    assert len(template.block.algebraic_vars) == len(template.block.algebraic_eqs)
    assert len(template.block.in_vars) == 10
    assert len(template.block.out_vars) == 1


def test_ac11c_template_accepts_documented_takeover_and_independent_supply() -> None:
    """Compile each limiter insertion point and independent SW1 source mode.

    :return: None.
    """
    template: RmsModelTemplate = build_ac11c_template(
        VarFactory(),
        'AC11CAlternate',
        Ac11cParameters(
            pss_location=Ac11cPssLocation.SWLIM,
            oel_location=Ac11cLimiterLocation.ALTERNATE,
            uel_location=Ac11cLimiterLocation.REGULATOR_OUTPUT,
            power_source=Ac11cPowerSource.INDEPENDENT,
        ),
    )
    assert len(template.block.state_vars) == 9
    assert len(template.block.algebraic_vars) == len(template.block.algebraic_eqs)


def test_ac11c_is_materialized_by_the_standard_template_factory() -> None:
    """The international-standard registry dispatches AC11C to its native block.

    :return: None.
    """
    template: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.AC11C, VarFactory(), 'AC11CFactory',
    )
    assert len(template.block.state_vars) == 9
    assert template.block.name == 'AC11CFactory'
