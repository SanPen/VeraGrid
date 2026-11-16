# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C freewheel-voltage gain and output limits."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cFreewheelVoltageSettings:
    """Store AC9C freewheel gain, bounds and operating point."""

    __slots__ = ('kfw', 'vfwmax', 'vfwmin', 'feedback0', 'vfw0')

    def __init__(self, kfw: float = 1.0, vfwmax: float = 1.0,
                 vfwmin: float = 0.0, feedback0: float = 0.0,
                 vfw0: float = 0.0) -> None:
        """Store freewheel settings in per-unit.

        :param kfw: Gain applied to filtered field-feedback signal.
        :param vfwmax: Maximum freewheel voltage feedback.
        :param vfwmin: Minimum freewheel voltage feedback.
        :param feedback0: Initial filtered field-feedback input.
        :param vfw0: Initial bounded freewheel voltage.
        """
        self.kfw: float = kfw
        self.vfwmax: float = vfwmax
        self.vfwmin: float = vfwmin
        self.feedback0: float = feedback0
        self.vfw0: float = vfw0


def build_ac9c_freewheel_voltage_template(
        vf: VarFactory,
        name: str = 'AC9C freewheel voltage',
        settings: Ac9cFreewheelVoltageSettings | None = None,
) -> RmsModelTemplate:
    """Build the AC9C ``KFW`` freewheel-voltage limiter.

    The source feedback-filter output is multiplied by KFW and clipped to the
    configured VFWMIN/VFWMAX interval. The filtered signal stays an open input
    for composition with the field-feedback stage.

    :param vf: Symbol factory owning controller symbols.
    :param name: Unique component label.
    :param settings: Gain, bounds and solved initial values.
    :return: Native component exposing ``VFWPu``.
    :raises ValueError: Nonfinite settings, unordered limits or infeasible init.
    """
    selected: Ac9cFreewheelVoltageSettings = (
        Ac9cFreewheelVoltageSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kfw, selected.vfwmax, selected.vfwmin,
        selected.feedback0, selected.vfw0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C freewheel settings must be finite')
    elif selected.vfwmin >= selected.vfwmax:
        raise ValueError('AC9C freewheel limits must be ordered')
    elif not selected.vfwmin <= selected.vfw0 <= selected.vfwmax:
        raise ValueError('AC9C initial freewheel voltage must lie within its limits')
    elif selected.vfw0 != min(max(selected.kfw * selected.feedback0, selected.vfwmin), selected.vfwmax):
        raise ValueError('AC9C initial freewheel voltage must match its bounded gain')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    gain: Var = control.parameter('KFW', selected.kfw)
    maximum: Var = control.parameter('VFWMAX', selected.vfwmax)
    minimum: Var = control.parameter('VFWMIN', selected.vfwmin)
    feedback: Var = control.input('FilteredFieldFeedbackPu', Const(selected.feedback0))
    freewheel_voltage: Var = control.algebraic(
        'VFWPu', sym.hard_sat(gain * feedback, minimum, maximum), Const(selected.vfw0),
    )
    return control.finish((freewheel_voltage,), 'AC9C bounded freewheel-voltage feedback')
