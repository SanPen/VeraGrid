# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Frequency-sensitive auxiliary power signal with washout and lag memories."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_cpaaut_template(
        vf: VarFactory, name: str | None = None, gain_mw_per_pu: float = 100.,
        washout_time: float = 2., lag_time: float = .5,
        minimum_mw: float = -50., maximum_mw: float = 50.,
) -> RmsModelTemplate:
    """Build a bounded auxiliary power response to bus-frequency deviation.

    The input is frequency deviation from nominal in per unit. A washout
    rejects steady offsets, a first-order lag smooths the transient, and a
    gain converts the result to MW. The output limits apply after that gain.
    Both memories initialize at zero deviation, making the initial output zero.
    The frequency input and MW output remain open for a network/device host.

    :param vf: Shared variable factory.
    :param name: Optional instance name.
    :param gain_mw_per_pu: Transient power gain in MW per unit frequency.
    :param washout_time: Positive washout time in seconds.
    :param lag_time: Positive smoothing time in seconds.
    :param minimum_mw: Lower auxiliary-power limit in MW.
    :param maximum_mw: Upper auxiliary-power limit in MW.
    :return: Two-state auxiliary power controller.
    :raises ValueError: Nonfinite values, nonpositive times or reversed limits.
    """
    values: tuple[float, ...] = (
        gain_mw_per_pu, washout_time, lag_time, minimum_mw, maximum_mw,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Auxiliary power settings must be finite')
    elif washout_time <= 0 or lag_time <= 0 or maximum_mw <= minimum_mw:
        raise ValueError('Auxiliary power times and limits must be ordered')
    elif not minimum_mw <= 0 <= maximum_mw:
        raise ValueError('Auxiliary power limits must contain zero equilibrium')
    else:
        pass

    control: ControlRealization = ControlRealization(
        vf, 'CPAAUT' if name is None else name,
    )
    frequency: Var = control.input('FrequencyDeviationPu', Const(0.))
    washout: Var = control.parameter('TB', washout_time)
    lag_time_parameter: Var = control.parameter('TA', lag_time)
    gain: Var = control.parameter('CM', gain_mw_per_pu)
    minimum: Var = control.parameter('PMIN', minimum_mw)
    maximum: Var = control.parameter('PMAX', maximum_mw)
    transient: Var = control.washout(
        'TransientFrequencyPu', frequency, washout, washout_time,
        Const(1.), Const(0.),
    )
    smoothed: Var = control.lag(
        'SmoothedFrequencyPu', transient, lag_time_parameter, lag_time,
        Const(0.),
    )
    power: Var = control.algebraic(
        'AuxiliaryPowerMw', sym.hard_sat(gain * smoothed, minimum, maximum),
        Const(0.),
    )
    return control.finish((power,), 'Frequency-sensitive bounded auxiliary power')
