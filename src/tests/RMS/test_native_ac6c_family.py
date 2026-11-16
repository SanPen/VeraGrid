# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Independent equilibrium, transfer and voltage-limit checks for two-stage brushless excitation."""
from __future__ import annotations

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c import Ac6cParameters, FieldLimitVoltage, build_ac6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c2 import build_ac6c2_template
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.RMS.test_native_turbine_governors import evaluate_controller, initialized_values, linearized_response


@pytest.mark.parametrize('dependent',(False,True))
def test_ac6c_equilibrium_and_limit_choice(dependent: bool) -> None:
    """Both forcing-limit modes start at the same physical field equilibrium.

    :param dependent: Select terminal-following forcing capability.
    """
    parameters: Ac6cParameters = Ac6cParameters(limit_voltage=FieldLimitVoltage.TERMINAL if dependent else FieldLimitVoltage.FIXED)
    block: Block = build_ac6c2_template(VarFactory(),'ac6',parameters).block
    values: dict[int,float] = initialized_values(block)
    assert len(block.state_vars) == 5
    np.testing.assert_allclose([equation.eval_uid(values) for equation in block.state_eqs],0.,atol=1e-11)
    np.testing.assert_allclose([equation.eval_uid(values) for equation in block.algebraic_eqs],0.,atol=1e-11)
    block.out_vars[0] = next(variable for variable in block.algebraic_vars if variable.name == 'FieldForcingPu_ac6')
    states: np.ndarray = np.asarray([values[variable.uid] for variable in block.state_vars])
    initial_derivative: np.ndarray
    initial_forcing: float
    initial_derivative,initial_forcing = evaluate_controller(block,values,states,1.)
    values[block.in_vars[4].uid] = 0.
    derivative: np.ndarray
    forcing: float
    derivative,forcing = evaluate_controller(block,values,states,1.)
    assert forcing == pytest.approx(0. if dependent else initial_forcing)


def test_ac6c_unclipped_transfer() -> None:
    """Both lead-lag numerators and the winding time enter the voltage-to-field transfer."""
    parameters: Ac6cParameters = Ac6cParameters(kc=0.,kd=0.,kh=0.,se1=0.,se2=0.,
        ka=2.,ke=1.4,te=.7,tr=.02,ta=.11,tk=.04,tb=.13,tc=.05)
    block: Block = build_ac6c_template(VarFactory(),'ac6',parameters).block
    values: dict[int,float] = initialized_values(block)
    for frequency in (.01,.1,1.,10.):
        s: complex = 2j*np.pi*frequency
        expected: complex = -2.*(1.+.04*s)*(1.+.05*s)/((1.+.02*s)*(1.+.11*s)*(1.+.13*s)*(1.4+.7*s))
        assert linearized_response(block,values,0,frequency) == pytest.approx(expected,rel=5e-7,abs=1e-8)


def test_ac6c_zero_time_reduction() -> None:
    """Disabled sensing and feedback and zero lead-lags produce only winding memory."""
    block: Block = build_ac6c_template(VarFactory(),'ac6',Ac6cParameters(
        tr=0.,ta=0.,tk=0.,tb=0.,tc=0.,kh=0.,th=0.,tj=0.)).block
    values: dict[int,float] = initialized_values(block)
    assert len(block.state_vars) == 1
    np.testing.assert_allclose([equation.eval_uid(values) for equation in block.state_eqs],0.,atol=1e-11)


def test_ac6c_feedback_clips_before_lead_lag() -> None:
    """The feedback lead can temporarily exceed its clipped input ceiling."""
    block: Block = build_ac6c_template(VarFactory(),'ac6',Ac6cParameters(
        kh=1.,vfelim=1.15,vhmax=.2,th=.1,tj=.2)).block
    values: dict[int,float] = initialized_values(block)
    states: np.ndarray = np.asarray([values[variable.uid] for variable in block.state_vars])
    block.out_vars[0] = next(variable for variable in block.algebraic_vars if variable.name == 'FeedbackPu_ac6')
    values[block.in_vars[3].uid] = 5.
    derivative: np.ndarray
    feedback: float
    derivative,feedback = evaluate_controller(block,values,states,1.)
    assert feedback > .2
