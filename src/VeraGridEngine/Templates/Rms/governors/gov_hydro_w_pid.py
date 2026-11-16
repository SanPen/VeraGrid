# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovHydroWPID equations for the Woodward PID hydro governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroWPIDParameters:
    """CGMES GovHydroWPID parameters, retaining their RDF names and units."""

    __slots__ = (
        'mwbase', 'treg', 'reg', 'kp', 'ki', 'kd', 'ta', 'tb', 'velmax',
        'velmin', 'gatmax', 'gatmin', 'tw', 'pmax', 'pmin', 'd', 'gv1',
        'pgv1', 'gv2', 'pgv2', 'gv3', 'pgv3',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            treg: float = 0.1,
            reg: float = 0.05,
            kp: float = 0.1,
            ki: float = 0.36,
            kd: float = 1.11,
            ta: float = 0.1,
            tb: float = 0.1,
            velmax: float = 0.2,
            velmin: float = -0.15,
            gatmax: float = 1.0,
            gatmin: float = 0.0,
            tw: float = 1.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            d: float = 0.5,
            gv1: float = 0.3,
            pgv1: float = 0.3,
            gv2: float = 0.7,
            pgv2: float = 0.65,
            gv3: float = 1.0,
            pgv3: float = 1.0,
    ) -> None:
        """Store the canonical fields in MW, seconds, and per unit.

        :param mwbase: Active-power base in MW.
        :param treg: Electrical-power measurement lag in seconds.
        :param reg: Permanent droop gain.
        :param kp: Proportional gain.
        :param ki: Integral gain.
        :param kd: Derivative gain.
        :param ta: Controller filter time in seconds.
        :param tb: Gate-rate filter time in seconds.
        :param velmax: Maximum gate opening rate in pu/s.
        :param velmin: Maximum gate closing rate in pu/s.
        :param gatmax: Maximum gate position.
        :param gatmin: Minimum gate position.
        :param tw: Water-column time in seconds.
        :param pmax: Maximum turbine power.
        :param pmin: Minimum turbine power.
        :param d: Turbine speed damping.
        :param gv1: First gate-curve coordinate.
        :param pgv1: Power at ``gv1``.
        :param gv2: Second gate-curve coordinate.
        :param pgv2: Power at ``gv2``.
        :param gv3: Final gate-curve coordinate, normally one.
        :param pgv3: Power at ``gv3``.
        """
        self.mwbase: float = mwbase
        self.treg: float = treg
        self.reg: float = reg
        self.kp: float = kp
        self.ki: float = ki
        self.kd: float = kd
        self.ta: float = ta
        self.tb: float = tb
        self.velmax: float = velmax
        self.velmin: float = velmin
        self.gatmax: float = gatmax
        self.gatmin: float = gatmin
        self.tw: float = tw
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.d: float = d
        self.gv1: float = gv1
        self.pgv1: float = pgv1
        self.gv2: float = gv2
        self.pgv2: float = pgv2
        self.gv3: float = gv3
        self.pgv3: float = pgv3


def get_gov_hydro_wpid_curve_power(
        parameters: GovHydroWPIDParameters,
        gate: float,
) -> float:
    """Evaluate the default or three-point gate-to-power characteristic.

    :param parameters: Imported curve coordinates and powers.
    :param gate: Gate position in per unit.
    :return: Turbine power in per unit on ``mwbase``.
    """
    if parameters.gv1 <= 0.0:
        return gate
    elif gate <= parameters.gv1:
        return parameters.pgv1 * gate / parameters.gv1
    elif gate <= parameters.gv2:
        return parameters.pgv1 + (gate - parameters.gv1) * (
            (parameters.pgv2 - parameters.pgv1) / (parameters.gv2 - parameters.gv1)
        )
    else:
        return parameters.pgv2 + (gate - parameters.gv2) * (
            (parameters.pgv3 - parameters.pgv2) / (parameters.gv3 - parameters.gv2)
        )


def get_gov_hydro_wpid_gate_for_power(
        parameters: GovHydroWPIDParameters,
        power: float,
) -> float | None:
    """Invert the monotone turbine characteristic for operating-point setup.

    :param parameters: Imported curve coordinates and powers.
    :param power: Initial turbine power in per unit on ``mwbase``.
    :return: Gate position, or ``None`` when the curve is invalid or unbounded.
    """
    if parameters.gv1 <= 0.0:
        gate: float = power
    elif not (
            0.0 < parameters.gv1 < parameters.gv2 < parameters.gv3
            and parameters.pgv1 <= parameters.pgv2 <= parameters.pgv3
    ):
        return None
    elif power <= parameters.pgv1:
        gate = power * parameters.gv1 / parameters.pgv1 if parameters.pgv1 != 0.0 else parameters.gv1
    elif power <= parameters.pgv2:
        gate = parameters.gv1 + (power - parameters.pgv1) * (
            (parameters.gv2 - parameters.gv1) / (parameters.pgv2 - parameters.pgv1)
        ) if parameters.pgv2 != parameters.pgv1 else parameters.gv2
    elif parameters.pgv3 != parameters.pgv2:
        gate = parameters.gv2 + (power - parameters.pgv2) * (
            (parameters.gv3 - parameters.gv2) / (parameters.pgv3 - parameters.pgv2)
        )
    else:
        gate = parameters.gv3
    if parameters.gatmin <= gate <= parameters.gatmax:
        return gate
    else:
        return None


def build_gov_hydro_w_p_i_d_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroWPIDParameters | None = None,
) -> RmsModelTemplate:
    """Build the Woodward PID governor and hydro-turbine realization.

    :param vfactory: Factory owning the runtime symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical GovHydroWPID coefficients.
    :return: Equation-backed template with ``OmegaPu``, ``ReferencePu``,
        ``ElectricalPowerPu`` inputs and ``PmPu``/gate/rate outputs.
    """
    settings: GovHydroWPIDParameters = (
        GovHydroWPIDParameters() if parameters is None else parameters
    )
    coefficients: tuple[float, ...] = (
        settings.mwbase, settings.treg, settings.reg, settings.kp, settings.ki,
        settings.kd, settings.ta, settings.tb, settings.velmax, settings.velmin,
        settings.gatmax, settings.gatmin, settings.tw, settings.pmax,
        settings.pmin, settings.d, settings.gv1, settings.pgv1, settings.gv2,
        settings.pgv2, settings.gv3, settings.pgv3,
    )
    if not all(math.isfinite(value) for value in coefficients):
        raise ValueError('GovHydroWPID coefficients must be finite')
    elif settings.mwbase <= 0.0 or min(settings.treg, settings.ta, settings.tb, settings.tw) < 0.0:
        raise ValueError('GovHydroWPID power base and times are invalid')
    elif settings.velmin >= settings.velmax or settings.gatmin >= settings.gatmax:
        raise ValueError('GovHydroWPID gate rates and position stops must be ordered')
    elif settings.pmin >= settings.pmax or settings.pgv3 < settings.pgv1:
        raise ValueError('GovHydroWPID power limits and curve must be ordered')
    elif settings.gv1 > 0.0 and not (
            settings.gv1 < settings.gv2 < settings.gv3
            and settings.pgv1 <= settings.pgv2 <= settings.pgv3
    ):
        raise ValueError('GovHydroWPID three-point curve must be monotone')
    else:
        pass

    control: ControlRealization = ControlRealization(
        vfactory,
        'GovHydroWPID' if name is None else name,
    )
    reference: Var = control.input('ReferencePu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))
    speed: Var = control.input('OmegaPu', Const(1.0))
    initial_gate: Var = control.parameter('Gate0Pu', settings.gatmin)
    power_error: Var = control.lag(
        'PowerDroopPu',
        settings.reg * (electrical_power - reference),
        control.parameter('TREG', settings.treg),
        settings.treg,
        Const(0.0),
    )
    speed_error: Var = control.algebraic(
        'SpeedDeviationPu',
        speed - Const(1.0),
        Const(0.0),
    )
    controller_error: Expr = speed_error + power_error
    integral: Var = control.differential(
        vfactory.add_var('IntegralPu_' + control.name),
        settings.ki * controller_error,
        Const(0.0),
    )
    pi_output: Expr = settings.kp * controller_error + integral
    filtered_pi: Var = control.lag(
        'FilteredPiPu',
        pi_output,
        control.parameter('TA', settings.ta),
        settings.ta,
        Const(0.0),
    ) if settings.ta > 0.0 else control.algebraic(
        'FilteredPiPu',
        pi_output,
        Const(0.0),
    )
    derivative_output: Var = control.washout(
        'DerivativePu',
        controller_error,
        control.parameter('DerivativeTime', settings.ta),
        settings.ta,
        settings.kd / settings.ta if settings.ta > 0.0 else 0.0,
        Const(0.0),
    ) if settings.ta > 0.0 else control.algebraic(
        'DerivativePu',
        Const(0.0),
        Const(0.0),
    )
    filtered_controller: Var = control.algebraic(
        'FilteredControllerPu',
        filtered_pi + derivative_output,
        Const(0.0),
    )
    if settings.tb > 0.0:
        rate_memory: Var = control.lag(
            'GateRateMemoryPu',
            filtered_controller,
            control.parameter('GateRateTime', settings.tb),
            settings.tb,
            Const(0.0),
        )
        gate_rate_demand: Expr = (filtered_controller - rate_memory) / settings.tb
    else:
        gate_rate_demand = control.differential(
            vfactory.add_var('GateRateDerivative_' + control.name),
            filtered_controller,
            Const(0.0),
        )
    gate_rate: Var = control.algebraic(
        'GateRatePu',
        sym.hard_sat(gate_rate_demand, settings.velmin, settings.velmax),
        Const(0.0),
    )
    gate: Var = control.differential(
        vfactory.add_var('GatePu_' + control.name),
        gate_rate,
        initial_gate,
        control.parameter('GATMIN', settings.gatmin),
        control.parameter('GATMAX', settings.gatmax),
    )
    gate_curve: Var = control.algebraic(
        'GateCurvePowerPu',
        settings.pgv1 * sym.min(gate, Const(settings.gv1)) / settings.gv1
        + (settings.pgv2 - settings.pgv1)
        * sym.max(sym.min(gate, Const(settings.gv2)) - settings.gv1, Const(0.0))
        / (settings.gv2 - settings.gv1)
        + (settings.pgv3 - settings.pgv2)
        * sym.max(gate - settings.gv2, Const(0.0)) / (settings.gv3 - settings.gv2),
        Const(0.5),
    ) if settings.gv1 > 0.0 else control.algebraic(
        'GateCurvePowerPu',
        gate,
        Const(0.5),
    )
    turbine_power: Var = control.algebraic(
        'LimitedTurbinePowerPu',
        sym.hard_sat(gate_curve, settings.pmin, settings.pmax),
        Const(0.5),
    )
    water_power: Var = control.lead_lag(
        'WaterPowerPu',
        turbine_power,
        -control.parameter('TW', settings.tw),
        control.parameter('TWHalf', settings.tw / 2.0),
        -settings.tw,
        settings.tw / 2.0,
        Const(0.5),
    ) if settings.tw > 0.0 else control.algebraic(
        'WaterPowerPu',
        turbine_power,
        Const(0.5),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu',
        water_power - settings.d * (speed - Const(1.0)),
        Const(0.5),
    )
    return control.finish(
        (mechanical_power, gate, gate_rate),
        'Woodward PID hydro governor with three-point turbine curve and water inertia',
    )
