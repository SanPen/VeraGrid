# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamFV2 fast-valving steam governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamFV2Parameters:
    """Values for the exact scalar fields declared by CGMES GovSteamFV2."""

    __slots__ = (
        'mwbase', 't1', 'vmax', 'vmin', 'k', 't3', 'dt', 'tt', 'r', 'ta', 'tb', 'tc', 'ti',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            t1: float = 0.1,
            vmax: float = 1.0,
            vmin: float = 0.0,
            k: float = 0.3,
            t3: float = 0.3,
            dt: float = 0.0,
            tt: float = 0.5,
            r: float = 0.05,
            ta: float = 0.1,
            tb: float = 0.2,
            tc: float = 0.5,
            ti: float = 0.0,
    ) -> None:
        """Store model coefficients in their CGMES units.

        :param mwbase: Governor power base in MW.
        :param t1: Governor valve-command lag time in seconds.
        :param vmax: Maximum valve command in per unit.
        :param vmin: Minimum valve command in per unit.
        :param k: Turbine power fraction from the unvalved sections.
        :param t3: Reheater lag time in seconds.
        :param dt: Mechanical damping coefficient in per unit.
        :param tt: Intercept-valve power-decay time in seconds.
        :param r: Speed droop in per unit.
        :param ta: Time from fast-valving start to valve closure in seconds.
        :param tb: Time from start until valve reopening begins in seconds.
        :param tc: Time from start until the intercept valve is fully open in seconds.
        :param ti: Absolute simulation time when fast valving begins, in seconds.
        """
        self.mwbase: float = mwbase
        self.t1: float = t1
        self.vmax: float = vmax
        self.vmin: float = vmin
        self.k: float = k
        self.t3: float = t3
        self.dt: float = dt
        self.tt: float = tt
        self.r: float = r
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.ti: float = ti


def build_gov_steam_f_v2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamFV2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the governor, reheater, intercept-valve, and shaft-power equations.

    The local CGMES EA diagram supplies the governor and turbine transfer paths;
    its time curve closes the intercept valve, holds it closed, then reopens it.
    Zero-duration curve segments become exact steps, and zero-time lags become
    algebraic paths through :class:`ControlRealization`.

    :param vfactory: Factory that owns all symbolic variables.
    :param name: Optional unique template instance name.
    :param parameters: Canonical GovSteamFV2 scalar values.
    :return: Equation-backed template with speed and reference input ports.
    :raises ValueError: Invalid droop, limits, times, or power base.
    """
    settings: GovSteamFV2Parameters = (
        GovSteamFV2Parameters() if parameters is None else parameters
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.t1, settings.vmax, settings.vmin,
        settings.k, settings.t3, settings.dt, settings.tt, settings.r,
        settings.ta, settings.tb, settings.tc, settings.ti,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES GovSteamFV2 parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.r <= 0.0:
        raise ValueError('CGMES GovSteamFV2 requires positive mwbase and droop')
    elif min(
            settings.t1, settings.t3, settings.tt, settings.ta,
            settings.tb, settings.tc, settings.ti,
    ) < 0.0:
        raise ValueError('CGMES GovSteamFV2 times must be nonnegative')
    elif settings.vmin > settings.vmax or not 0.0 <= settings.k <= 1.0:
        raise ValueError('CGMES GovSteamFV2 valve limits or turbine fraction are invalid')
    elif settings.ta > settings.tb or settings.tb > settings.tc:
        raise ValueError('CGMES GovSteamFV2 requires ta <= tb <= tc')
    else:
        pass

    template_name: str = 'GovSteamFV2' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    mwbase: Var = control.parameter('mwbase', settings.mwbase)
    t1: Var = control.parameter('t1', settings.t1)
    vmax: Var = control.parameter('vmax', settings.vmax)
    vmin: Var = control.parameter('vmin', settings.vmin)
    fraction: Var = control.parameter('k', settings.k)
    t3: Var = control.parameter('t3', settings.t3)
    damping: Var = control.parameter('dt', settings.dt)
    intercept_time: Var = control.parameter('tt', settings.tt)
    droop: Var = control.parameter('r', settings.r)
    close_time: Var = control.parameter('ta', settings.ta)
    reopen_time: Var = control.parameter('tb', settings.tb)
    full_open_time: Var = control.parameter('tc', settings.tc)
    fast_valving_start_time: Var = control.parameter('ti', settings.ti)

    speed: Var = control.input('OmegaPu', Const(1.0))
    speed_reference: Var = control.input('gov.omegaRefPu', Const(1.0))
    initial_power: Expr = (speed_reference - Const(1.0)) / droop
    governor_demand: Expr = sym.hard_sat(initial_power + (Const(1.0) - speed) / droop, vmin, vmax)
    valve_command: Var = control.lag(
        'GovSteamFV2ValveCommandPu', governor_demand, t1, settings.t1,
        sym.hard_sat(initial_power, vmin, vmax), vmin, vmax,
    )
    reheater_power: Var = control.lag(
        'GovSteamFV2ReheaterPowerPu', (Const(1.0) - fraction) * valve_command,
        t3, settings.t3, (Const(1.0) - fraction) * sym.hard_sat(initial_power, vmin, vmax),
    )

    # The simulator recognizes this name as its global time input, so the
    # fast-valving profile adds no artificial state or external device port.
    simulation_time: Var = vfactory.add_var('glob_time')
    elapsed_time: Expr = simulation_time - fast_valving_start_time
    if settings.ta > 0.0:
        close_fraction: Expr = sym.hard_sat(elapsed_time / close_time, Const(0.0), Const(1.0))
    else:
        close_fraction = sym.heaviside(elapsed_time)
    if settings.tc > settings.tb:
        reopen_fraction: Expr = sym.hard_sat(
            (elapsed_time - reopen_time) / (full_open_time - reopen_time),
            Const(0.0),
            Const(1.0),
        )
    else:
        reopen_fraction = sym.heaviside(elapsed_time - reopen_time)
    intercept_position: Expr = Const(1.0) - close_fraction + reopen_fraction
    intercept_power: Var = control.lag(
        'GovSteamFV2InterceptPowerPu', intercept_position * reheater_power,
        intercept_time, settings.tt,
        (Const(1.0) - fraction) * sym.hard_sat(initial_power, vmin, vmax),
    )
    turbine_power: Expr = fraction * valve_command + intercept_power
    mechanical_power_pu: Var = control.algebraic(
        'gov.PmPu', turbine_power + damping * (Const(1.0) - speed),
        initial_power,
    )
    mechanical_power_mw: Var = control.algebraic(
        'gov.PmMW', mwbase * mechanical_power_pu,
        mwbase * initial_power,
    )
    runtime_template: RmsModelTemplate = control.finish(
        (mechanical_power_pu, mechanical_power_mw),
        'CGMES GovSteamFV2 steam turbine fast-valving response',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = runtime_template.tpe
    template.block = runtime_template.block
    template.comment = (
        'CGMES GovSteamFV2 equations from the CGMES EA governor and fast-valving diagram.'
    )
    return template
