# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Validate WESGOV sampled PI control and mechanical lag structure."""

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.wesgov import (
    WesgovSettings,
    build_wesgov_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.procedural_logic import (
    SampledPiLimiterLogic,
    build_procedural_logic_entry,
    procedural_logic_entry_to_dict,
)


def _read_error(t: float, x: np.ndarray, params: np.ndarray) -> float:
    """Read the scalar self-check signal used by the sample-driven PI.

    :param t: Current accepted sample time.
    :param x: Accepted states.
    :param params: Mutable runtime event values.
    :return: Current test error.
    """
    return float(x[0])


def test_wesgov_template_has_two_independent_sample_clocks_and_three_states() -> None:
    """Build both sampled measurement paths and continuous physical lags.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    settings: WesgovSettings = WesgovSettings(
        delta_tc=.06, delta_tp=.1, droop=.04, kp=27.0, ti=.13,
        t1=.3, t2=.59, alim=.1, tpe=.1,
    )
    template = build_wesgov_template(vf, settings, 'sampled WESGOV')
    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 3
    assert len(template.block.procedural_logic) == 3
    sample_periods: list[float] = [
        logic.sample_period for logic in template.block.procedural_logic[:2]
    ]
    assert sample_periods == pytest.approx([.06, .1])
    assert isinstance(template.block.procedural_logic[2], SampledPiLimiterLogic)


def test_wesgov_sampled_pi_holds_and_limits_each_control_move() -> None:
    """Integrate the held error and apply ALIM only at fixed controller ticks.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    error: Var = vf.add_var('sampled error')
    logic: SampledPiLimiterLogic = SampledPiLimiterLogic(
        output_var_name='PI output', error_expr=error, sample_period=.25,
        proportional_gain=2.0, integral_time=.5, maximum_change=.2,
    )
    logic.output_idx = 0
    logic.error_eval = _read_error
    params: np.ndarray = np.array((1.0,), dtype=float)

    logic.update(0.0, np.array((0.0,), dtype=float), params)
    assert params[0] == pytest.approx(1.0)
    assert logic.get_next_forced_event_time(0.0, .3) == pytest.approx(.25)
    logic.update(.1, np.array((1.0,), dtype=float), params)
    assert params[0] == pytest.approx(1.0)
    logic.update(.25, np.array((1.0,), dtype=float), params)
    assert params[0] == pytest.approx(1.2)
    logic.update(.5, np.array((1.0,), dtype=float), params)
    assert params[0] == pytest.approx(1.4)

    serialized: dict[str, object] = procedural_logic_entry_to_dict(logic)
    restored: SampledPiLimiterLogic = build_procedural_logic_entry(serialized)
    assert isinstance(restored, SampledPiLimiterLogic)
    assert restored.sample_period == pytest.approx(.25)
    assert restored.proportional_gain == pytest.approx(2.0)
    assert restored.integral_time == pytest.approx(.5)
    assert restored.maximum_change == pytest.approx(.2)


def test_wesgov_zero_physical_lags_reduce_without_dummy_states() -> None:
    """Keep sample behavior while algebraically removing zero source lags.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    settings: WesgovSettings = WesgovSettings(
        delta_tc=.05, delta_tp=.1, droop=.05, kp=10.0, ti=.2,
        t1=0.0, t2=0.0, alim=.1, tpe=0.0,
    )
    template = build_wesgov_template(vf, settings)
    assert len(template.block.state_vars) == 0
    assert len(template.block.procedural_logic) == 3


def test_wesgov_rejects_invalid_sample_and_deadband_domains() -> None:
    """Reject malformed sample periods and the wrong asymmetric deadband signs.

    :return: None.
    """
    with pytest.raises(ValueError, match='sample periods'):
        WesgovSettings(0.0, .1, .05, 2.0, 1.0, .1, .2, .1, .1)
    with pytest.raises(ValueError, match='deadband'):
        WesgovSettings(.1, .1, .05, 2.0, 1.0, .1, .2, .1, .1,
                       deadband_high=-.01)
