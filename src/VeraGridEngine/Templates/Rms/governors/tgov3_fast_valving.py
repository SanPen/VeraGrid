# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""TGOV3 scheduled intercept-valve position."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Tgov3FastValvingSettings:
    """Store the source fast-valving start time and interval boundaries."""

    __slots__ = ('start_time', 'close_time', 'reopen_time', 'open_time')

    def __init__(self, start_time: float = 0.0, close_time: float = 0.0,
                 reopen_time: float = 0.0, open_time: float = 0.0) -> None:
        """Store the time schedule in seconds relative to the simulation clock.

        :param start_time: Source ``TI`` event time.
        :param close_time: ``TA``, time to reach fully closed position.
        :param reopen_time: ``TB``, time reopening begins.
        :param open_time: ``TC``, time to reach fully open position.
        """
        self.start_time: float = start_time
        self.close_time: float = close_time
        self.reopen_time: float = reopen_time
        self.open_time: float = open_time


def build_tgov3_fast_valving_template(
        vf: VarFactory,
        name: str = 'TGOV3 fast valving',
        settings: Tgov3FastValvingSettings | None = None,
) -> RmsModelTemplate:
    """Build the TI-relative intercept-valve schedule from PSS/E 33.10 §7.36.

    The valve is at 1 before ``TI``, closes linearly over ``TA``, remains closed
    until ``TB``, reopens linearly until ``TC``, then stays at 1. The model's
    ``TI`` input is a native event parameter because it is not in the DYR record.

    :param vf: Symbol factory owning the schedule symbols.
    :param name: Unique model label.
    :param settings: Fast-valving event and interval times.
    :return: Stateless native template exposing intercept-valve position.
    :raises ValueError: Time values are nonfinite or the source intervals overlap.
    """
    selected: Tgov3FastValvingSettings = (
        Tgov3FastValvingSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.start_time, selected.close_time,
        selected.reopen_time, selected.open_time,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('TGOV3 fast-valving times must be finite')
    elif selected.start_time < 0.0 or selected.close_time < 0.0:
        raise ValueError('TGOV3 fast-valving start and close times must be nonnegative')
    elif selected.reopen_time < selected.close_time or selected.open_time <= selected.reopen_time:
        raise ValueError('TGOV3 fast-valving times must satisfy 0 <= TA <= TB < TC')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    start_time: Var = control.parameter('FastValvingStartTimeSec', selected.start_time)
    close_time: Var = control.parameter('TA', selected.close_time)
    reopen_time: Var = control.parameter('TB', selected.reopen_time)
    open_time: Var = control.parameter('TC', selected.open_time)
    simulation_time: Var = vf.add_var(name='glob_time')
    elapsed: Expr = simulation_time - start_time
    close_fraction: Expr
    if selected.close_time == 0.0:
        close_fraction = sym.heaviside(elapsed)
    else:
        close_fraction = sym.max(
            Const(0.0), sym.min(elapsed / close_time, Const(1.0)),
        )
    open_duration: Expr = open_time - reopen_time
    reopen_fraction: Expr = sym.max(
        Const(0.0), sym.min((elapsed - reopen_time) / open_duration, Const(1.0)),
    )
    position: Var = control.algebraic(
        'InterceptValvePositionPu', Const(1.0) - close_fraction + reopen_fraction,
        Const(1.0),
    )
    return control.finish((position,), 'TGOV3 TI-relative intercept-valve schedule')
