# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 inner active/reactive current loops from PSS/E 35.2 §17.1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Dera1InnerCurrentLoopSettings:
    """Store current-loop time, active-current ramp, and initial conditions."""

    __slots__ = ('tg', 'rrpwr', 'initial_active_current', 'initial_reactive_current')

    def __init__(
            self,
            tg: float = 0.02,
            rrpwr: float = 1.0,
            initial_active_current: float = 0.0,
            initial_reactive_current: float = 0.0,
    ) -> None:
        """Store source current-loop parameters.

        :param tg: Current control time constant in seconds.
        :param rrpwr: Symmetric active-current ramp limit in pu/s.
        :param initial_active_current: Solved active current in pu.
        :param initial_reactive_current: Solved reactive current in pu.
        :return: None.
        """
        self.tg: float = tg
        self.rrpwr: float = rrpwr
        self.initial_active_current: float = initial_active_current
        self.initial_reactive_current: float = initial_reactive_current


def build_dera1_inner_current_loop_template(
        vf: VarFactory,
        name: str = 'DERA1 inner current loops',
        settings: Dera1InnerCurrentLoopSettings | None = None,
) -> RmsModelTemplate:
    """Build DERA1's trip-gated Id/Iq inner-loop dynamics.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model-component name.
    :param settings: Source parameters and solved current point.
    :return: Two-input-current controller with active/reactive current outputs.
    :raises ValueError: Invalid source settings or initialization point.
    """
    selected: Dera1InnerCurrentLoopSettings = (
        Dera1InnerCurrentLoopSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.tg, selected.rrpwr, selected.initial_active_current,
        selected.initial_reactive_current,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('DERA1 current-loop settings must be finite')
    elif selected.tg <= 0.0 or selected.rrpwr < 0.0:
        raise ValueError('DERA1 Tg must be positive and Rrpwr nonnegative')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    active_command: Var = control.input(
        'LimitedActiveCurrentCommandPu', Const(selected.initial_active_current),
    )
    reactive_command: Var = control.input(
        'LimitedReactiveCurrentCommandPu', Const(selected.initial_reactive_current),
    )
    trip_multiplier: Var = control.input('TripMultiplier', Const(1.0))
    active_target: Var = vf.add_var(name='TripGatedActiveCurrentTargetPu_' + name)
    control.block.algebraic_vars.append(active_target)
    control.block.algebraic_eqs.append(
        active_target - active_command * trip_multiplier,
    )
    control.block.init_eqs[active_target] = Const(selected.initial_active_current)
    current_time: Var = control.parameter('TG', selected.tg)
    active_current: Var = vf.add_var(name='ActiveCurrentPu_' + name)
    active_derivative: Expr = sym.hard_sat(
        (active_target - active_current) / current_time,
        Const(-selected.rrpwr), Const(selected.rrpwr),
    )
    control.differential(
        active_current, active_derivative, Const(selected.initial_active_current),
    )
    reactive_current: Var = vf.add_var(name='ReactiveCurrentPu_' + name)
    reactive_derivative: Expr = (
        reactive_command * trip_multiplier - reactive_current
    ) / current_time
    control.differential(
        reactive_current, reactive_derivative, Const(selected.initial_reactive_current),
    )
    return control.finish(
        (active_current, reactive_current),
        'DERA1 trip-gated Id/Iq inner current loops',
    )
