# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 active-power reference, order lag and current conversion."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1ActivePowerMode(Enum):
    """Select the source PFLAG branch before the power-order lag."""

    POWER = 0
    TORQUE_TIMES_SPEED = 1


class Reeca1ActivePowerSettings:
    """Store the reviewed active-power lag and Pord output limits."""

    __slots__ = ('tpord', 'pmin', 'pmax', 'mode', 'dpmax', 'dpmin', 'bidirectional')

    def __init__(self, tpord: float = .02, pmin: float = 0., pmax: float = 999.,
                 mode: Reeca1ActivePowerMode = Reeca1ActivePowerMode.POWER,
                 dpmax: float | None = None, dpmin: float | None = None,
                 bidirectional: bool = False) -> None:
        """Store power-order parameters on the generator MVA base.

        :param tpord: Pord lag time in seconds.
        :param pmin: Minimum generation power order in per unit.
        :param pmax: Maximum generation power order in per unit.
        :param mode: Direct-power or turbine-torque-times-speed source branch.
        :param dpmax: Optional positive Pref rise rate in per unit per second.
        :param dpmin: Optional negative Pref fall rate in per unit per second.
        :param bidirectional: Allow storage charging with a negative Pmin.
        :return: None.
        """
        self.tpord: float = tpord
        self.pmin: float = pmin
        self.pmax: float = pmax
        self.mode: Reeca1ActivePowerMode = mode
        self.dpmax: float | None = dpmax
        self.dpmin: float | None = dpmin
        self.bidirectional: bool = bidirectional


def build_reeca1_active_power_template(
        vf: VarFactory,
        name: str = 'REECA1 active power',
        settings: Reeca1ActivePowerSettings | None = None,
) -> RmsModelTemplate:
    """Build the source Pord lag and its filtered-voltage current conversion.

    When both rate limits are provided, a Pref state precedes the PFLAG
    branch. The speed-dependent branch exposes a turbine-speed input.
    This component cannot activate a complete REECA1 source record.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Lag time and power-order limits.
    :return: Controller with Pref and filtered-voltage inputs, and Ipcmd output.
    :raises ValueError: Invalid time or power-order bounds.
    """
    selected: Reeca1ActivePowerSettings = Reeca1ActivePowerSettings() if settings is None else settings
    if not all(math.isfinite(value) for value in (selected.tpord, selected.pmin, selected.pmax)):
        raise ValueError('REECA1 active-power settings must be finite')
    elif (selected.tpord < 0 or selected.pmax <= selected.pmin
          or (selected.pmin < 0 and not selected.bidirectional)):
        raise ValueError('REECA1 active-power time or limits are invalid')
    elif not isinstance(selected.bidirectional, bool):
        raise ValueError('REECA1 bidirectional active-power selector is invalid')
    elif not isinstance(selected.mode, Reeca1ActivePowerMode):
        raise ValueError('REECA1 active-power mode is invalid')
    elif (selected.dpmax is None) != (selected.dpmin is None):
        raise ValueError('REECA1 Pref slew limits must be supplied together')
    elif (selected.dpmax is not None and selected.dpmin is not None
          and (not math.isfinite(selected.dpmax) or not math.isfinite(selected.dpmin)
               or selected.dpmax <= 0 or selected.dpmin >= 0)):
        raise ValueError('REECA1 Pref slew limits must straddle zero')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    pref: Var = control.input('PrefPu', Const(0.))
    measured_voltage: Var = control.input('FilteredVoltagePu', Const(1.))
    power_request: Expr = pref
    if selected.dpmax is not None and selected.dpmin is not None:
        dpmax: Var = control.parameter('DPMAX', selected.dpmax)
        dpmin: Var = control.parameter('DPMIN', selected.dpmin)
        slew: Var = vf.add_var('PrefSlewPu_' + name)
        # shortcut: the source rate-limiter macro has no time constant; the
        # established native REEC uses 1 ms tracking. Replace when a discrete
        # event-aware rate limiter is available for the implicit DAE.
        control.differential(slew, sym.hard_sat((pref - slew) / Const(.001), dpmin, dpmax), pref)
        power_request = slew
    else:
        pass
    if selected.mode is Reeca1ActivePowerMode.TORQUE_TIMES_SPEED:
        speed: Var = control.input('TurbineSpeedPu', Const(1.))
        power_request = power_request * speed
    else:
        pass
    tpord: Var = control.parameter('TPORD', selected.tpord)
    pmin: Var = control.parameter('PMIN', selected.pmin)
    pmax: Var = control.parameter('PMAX', selected.pmax)
    # The source limits Pord before dividing by the measured voltage. The
    # 0.01 floor is the zero-voltage guard shown in the REEC_A block diagram.
    pord: Var = control.lag('PordPu', power_request, tpord, selected.tpord,
                            Const(0.), pmin, pmax)
    ip_command: Var = control.algebraic(
        'ActiveCurrentCommandPu', pord / sym.max(measured_voltage, Const(.01)), Const(0.),
    )
    return control.finish((ip_command,), 'REECA1 active-power lag and filtered-voltage current conversion')
