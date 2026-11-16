# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C controlled-rectifier bridge gain and bounded lag."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class Ac9cRectifierBridgeSettings:
    """Store controlled-bridge gain, time, voltage bounds and initial state."""

    __slots__ = ('ka', 'ta', 'vrmax', 'vrmin', 'vavr0', 'va0')

    def __init__(self, ka: float = 1.0, ta: float = 0.0,
                 vrmax: float = 5.0, vrmin: float = -5.0,
                 vavr0: float = 0.0, va0: float = 0.0) -> None:
        """Store bridge settings in per-unit and seconds.

        :param ka: Controlled rectifier bridge gain.
        :param ta: Bridge lag time in seconds.
        :param vrmax: Upper bridge output limit.
        :param vrmin: Lower bridge output limit.
        :param vavr0: Initial field-current regulator output.
        :param va0: Initial bridge output.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.vavr0: float = vavr0
        self.va0: float = va0


def build_ac9c_rectifier_bridge_template(
        vf: VarFactory,
        name: str = 'AC9C controlled rectifier bridge',
        settings: Ac9cRectifierBridgeSettings | None = None,
) -> RmsModelTemplate:
    """Build the source bounded ``KA/(1+s*TA)`` bridge block.

    :param vf: Symbol factory owning bridge symbols.
    :param name: Unique component label.
    :param settings: Bridge gain, lag, limits and solved initial values.
    :return: Native component exposing bridge voltage ``VAPu``.
    :raises ValueError: Nonfinite values, nonpositive gain or invalid bounds.
    """
    selected: Ac9cRectifierBridgeSettings = (
        Ac9cRectifierBridgeSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.ka, selected.ta, selected.vrmax, selected.vrmin,
        selected.vavr0, selected.va0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C bridge settings must be finite')
    elif selected.ka <= 0.0 or selected.ta < 0.0:
        raise ValueError('AC9C bridge requires positive KA and nonnegative TA')
    elif selected.vrmin >= selected.vrmax:
        raise ValueError('AC9C bridge output limits must be ordered')
    elif not selected.vrmin <= selected.va0 <= selected.vrmax:
        raise ValueError('AC9C initial bridge output must lie within its limits')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    gain: Var = control.parameter('KA', selected.ka)
    time: Var = control.parameter('TA', selected.ta)
    maximum: Var = control.parameter('VRMAX', selected.vrmax)
    minimum: Var = control.parameter('VRMIN', selected.vrmin)
    regulator_output: Var = control.input('VAVRPu', Const(selected.vavr0))
    bridge_voltage: Var = control.lag(
        'VAPu', gain * regulator_output, time, selected.ta, Const(selected.va0),
        minimum, maximum,
    )
    return control.finish((bridge_voltage,), 'AC9C bounded controlled-rectifier bridge')
