# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovGAST4 gas turbine governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovGAST4Parameters:
    """Construction settings from the canonical GovGAST4 RDF attributes."""

    __slots__ = (
        'bp', 'tv', 'ta', 'tc', 'tcm', 'ktm', 'tm', 'rymx', 'rymn',
        'mxef', 'mnef',
    )

    def __init__(
            self,
            bp: float = 0.05,
            tv: float = 0.1,
            ta: float = 3.0,
            tc: float = 0.5,
            tcm: float = 0.1,
            ktm: float = 0.0,
            tm: float = 0.2,
            rymx: float = 1.1,
            rymn: float = 0.0,
            mxef: float = 0.05,
            mnef: float = -0.05,
    ) -> None:
        """Store the direct CGMES GovGAST4 scalar values.

        :param bp: Speed droop.
        :param tv: Fuel-valve integrator time in seconds.
        :param ta: Maximum fuel-valve opening rate parameter in seconds.
        :param tc: Maximum fuel-valve closing rate parameter in seconds.
        :param tcm: Fuel-control lag in seconds.
        :param ktm: Compressor direct-path gain.
        :param tm: Compressor discharge-volume lag in seconds.
        :param rymx: Maximum fuel-valve opening.
        :param rymn: Minimum fuel-valve opening.
        :param mxef: Maximum positive speed-error contribution.
        :param mnef: Maximum negative speed-error contribution.
        """
        self.bp: float = bp
        self.tv: float = tv
        self.ta: float = ta
        self.tc: float = tc
        self.tcm: float = tcm
        self.ktm: float = ktm
        self.tm: float = tm
        self.rymx: float = rymx
        self.rymn: float = rymn
        self.mxef: float = mxef
        self.mnef: float = mnef


def build_gov_g_a_s_t4_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovGAST4Parameters | None = None,
) -> RmsModelTemplate:
    """Build the GovGAST4 governor and two-path turbine-power equations.

    :param vfactory: Factory that owns the symbolic equations.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical GovGAST4 settings.
    :return: Equation-backed governor with open speed, reference, and Ey ports.
    :raises ValueError: Invalid droop, limits, rate settings, or zero integrator time.
    """
    settings: GovGAST4Parameters = GovGAST4Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.bp, settings.tv, settings.ta, settings.tc, settings.tcm,
        settings.ktm, settings.tm, settings.rymx, settings.rymn,
        settings.mxef, settings.mnef,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES GovGAST4 parameters must be finite')
    elif settings.bp <= 0.0 or settings.tv <= 0.0:
        raise ValueError('CGMES GovGAST4 requires positive bp and tv')
    elif min(settings.ta, settings.tc, settings.tcm, settings.tm) < 0.0:
        raise ValueError('CGMES GovGAST4 time and rate parameters must be nonnegative')
    elif settings.rymn >= settings.rymx or settings.mnef > settings.mxef:
        raise ValueError('CGMES GovGAST4 fuel-valve or speed-error limits are invalid')
    else:
        pass

    template_name: str = 'GovGAST4' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    omega: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('PRefPu', Const(0.5))
    ey: Var = control.input('EyPu', Const(0.0))
    power_initial: float = 0.5

    speed_error: Expr = sym.hard_sat(
        (Const(1.0) - omega) / settings.bp,
        settings.mnef,
        settings.mxef,
    )
    controller_error: Expr = reference + ey + speed_error
    valve: Var = vfactory.add_var(f'FuelValvePu_{template_name}')
    valve_servo_error: Expr = controller_error - valve
    if settings.ta > 0.0 and settings.tc > 0.0:
        valve_rate_error: Expr = sym.hard_sat(
            valve_servo_error,
            -1.0 / settings.tc,
            1.0 / settings.ta,
        )
    elif settings.ta > 0.0:
        valve_rate_error = sym.min(valve_servo_error, Const(1.0 / settings.ta))
    elif settings.tc > 0.0:
        valve_rate_error = sym.max(valve_servo_error, Const(-1.0 / settings.tc))
    else:
        valve_rate_error = valve_servo_error

    control.differential(
        valve,
        valve_rate_error / settings.tv,
        Const(power_initial),
        Const(settings.rymn),
        Const(settings.rymx),
    )
    fuel_command: Var = control.lag(
        'FuelCommandPu',
        valve,
        control.parameter('Tcm', settings.tcm),
        settings.tcm,
        Const(power_initial),
    )
    compressor_lag: Var = control.lag(
        'CompressorLagPu',
        fuel_command,
        control.parameter('Tm', settings.tm),
        settings.tm,
        Const(power_initial),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu',
        settings.ktm * fuel_command + (1.0 - settings.ktm) * compressor_lag,
        Const(power_initial),
    )
    template: RmsModelTemplate = control.finish(
        (mechanical_power, valve, fuel_command),
        'CGMES GovGAST4 fuel-valve controller and compressor turbine paths',
    )
    template.comment = (
        'CGMES GovGAST4 equations; EyPu is an external auxiliary input and defaults to zero.'
    )
    return template
