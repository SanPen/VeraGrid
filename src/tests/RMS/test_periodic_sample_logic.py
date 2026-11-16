# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check fixed-period procedural sample-and-hold behavior."""

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.procedural_logic import (
    PeriodicSampleLogic,
    build_procedural_logic_entry,
    procedural_logic_entry_to_dict,
)


def _read_first_state(t: float, x: np.ndarray, params: np.ndarray) -> float:
    """Return a simple state signal for the sample-and-hold self-check.

    :param t: Current sample time.
    :param x: Current state values.
    :param params: Runtime parameter values.
    :return: First state value.
    """
    return float(x[0])


def test_periodic_sample_holds_between_clock_ticks_and_round_trips() -> None:
    """Sample initially and at clock ticks while retaining intervening values.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    source: Var = vf.add_var('sample source')
    logic: PeriodicSampleLogic = PeriodicSampleLogic(
        output_var_name='held signal',
        source_expr=source,
        sample_period=.25,
        name='sample clock',
    )
    logic.output_idx = 0
    logic.source_eval = _read_first_state
    params: np.ndarray = np.array((0.,), dtype=float)

    logic.update(0., np.array((1.,), dtype=float), params)
    assert params[0] == pytest.approx(1.)
    assert logic.get_next_forced_event_time(0., .24) is None
    assert logic.get_next_forced_event_time(0., .30) == pytest.approx(.25)
    logic.update(.1, np.array((2.,), dtype=float), params)
    assert params[0] == pytest.approx(1.)
    logic.update(.25, np.array((3.,), dtype=float), params)
    assert params[0] == pytest.approx(3.)
    assert logic.get_next_forced_event_time(.25, .5) == pytest.approx(.5)

    serialized: dict[str, object] = procedural_logic_entry_to_dict(logic)
    restored: PeriodicSampleLogic = build_procedural_logic_entry(serialized)
    assert isinstance(restored, PeriodicSampleLogic)
    assert restored.output_var_name == 'held signal'
    assert restored.sample_period == pytest.approx(.25)
    assert restored.name == 'sample clock'
    replacement: Var = vf.add_var('replacement source')
    remapped: PeriodicSampleLogic = logic.remap({source: replacement})
    assert remapped.source_expr is replacement


def test_periodic_sample_rejects_nonpositive_intervals() -> None:
    """Reject invalid sample clocks before runtime binding.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    source: Var = vf.add_var('sample source')
    with pytest.raises(ValueError, match='interval'):
        PeriodicSampleLogic('held signal', source, 0.)
