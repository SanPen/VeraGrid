# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES GovSteamBB Brown-Boveri governor and turbine equations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamBBParameters:
    """GovSteamBB parameters in the units defined by its CGMES fields."""

    __slots__ = (
        'fcut', 'ks', 'kls', 'kg', 't1', 'kp', 'tn', 'kd', 'td', 'pmax',
        'pmin', 't4', 'k2', 't5', 'k3', 't6', 'peflag',
    )

    def __init__(
            self,
            fcut: float = 0.002,
            ks: float = 21.0,
            kls: float = 0.1,
            kg: float = 1.0,
            t1: float = 0.05,
            kp: float = 1.0,
            tn: float = 1.0,
            kd: float = 1.0,
            td: float = 1.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            t4: float = 0.15,
            k2: float = 0.75,
            t5: float = 12.0,
            k3: float = 0.5,
            t6: float = 0.75,
            peflag: bool = False,
    ) -> None:
        """Store the exact CGMES parameters without changing their meaning.

        :param fcut: Symmetric speed-deviation deadband in per unit.
        :param ks: Frequency gain.
        :param kls: Step limit for the limiter state.
        :param kg: Gradient limit in per unit per second.
        :param t1: Electrical-power transducer time in seconds.
        :param kp: PI controller proportional gain.
        :param tn: PI controller integral time in seconds.
        :param kd: Valve-section gain.
        :param td: Valve-section time in seconds.
        :param pmax: Maximum valve output.
        :param pmin: Minimum valve output.
        :param t4: Steam-output time in seconds.
        :param k2: Intermediate/low-pressure turbine fraction.
        :param t5: Intermediate-pressure turbine time in seconds.
        :param k3: Low-pressure turbine fraction.
        :param t6: Low-pressure turbine time in seconds.
        :param peflag: Select Pe feedback when true; use steam-output feedback otherwise.
        """
        self.fcut: float = fcut
        self.ks: float = ks
        self.kls: float = kls
        self.kg: float = kg
        self.t1: float = t1
        self.kp: float = kp
        self.tn: float = tn
        self.kd: float = kd
        self.td: float = td
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.t4: float = t4
        self.k2: float = k2
        self.t5: float = t5
        self.k3: float = k3
        self.t6: float = t6
        self.peflag: bool = peflag


def build_gov_steam_b_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamBBParameters | None = None,
) -> RmsModelTemplate:
    """Build the Brown-Boveri governor, valve, and three turbine sections.

    :param vfactory: Factory owning all symbolic variables.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical GovSteamBB coefficients.
    :return: Equation-backed model with speed, reference, and electrical-power ports.
    :raises ValueError: A required gain, time, or limit is invalid.
    """
    settings: GovSteamBBParameters = (
        GovSteamBBParameters() if parameters is None else parameters
    )
    coefficients: tuple[float, ...] = (
        settings.fcut, settings.ks, settings.kls, settings.kg, settings.t1,
        settings.kp, settings.tn, settings.kd, settings.td, settings.pmax,
        settings.pmin, settings.t4, settings.k2, settings.t5, settings.k3,
        settings.t6,
    )
    if not all(math.isfinite(value) for value in coefficients):
        raise ValueError('GovSteamBB parameters must be finite')
    elif settings.fcut < 0.0 or settings.kls <= 0.0 or settings.kg < 0.0:
        raise ValueError('GovSteamBB deadband and limiter settings are invalid')
    elif settings.t1 < 0.0 or settings.tn <= 0.0 or settings.td <= 0.0:
        raise ValueError('GovSteamBB transducer and controller times are invalid')
    elif min(settings.t4, settings.t5, settings.t6) < 0.0:
        raise ValueError('GovSteamBB turbine times must be nonnegative')
    elif settings.pmin >= settings.pmax or settings.kp < 0.0 or settings.kd < 0.0:
        raise ValueError('GovSteamBB valve limits and gains are invalid')
    elif not (0.0 <= settings.k2 <= 1.0 and 0.0 <= settings.k3 <= 1.0):
        raise ValueError('GovSteamBB turbine fractions must be in [0, 1]')
    else:
        pass

    template_name: str = 'GovSteamBB' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = control.input('OmegaPu', Const(1.0))
    reference: Var = control.input('ReferencePu', Const(0.5))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.5))

    # Peflag selects electrical power or the turbine steam-output feedback path.
    steam_output_t4: Var = vfactory.add_var(f'SteamOutputPu_{template_name}')
    if settings.peflag:
        selected_feedback: Expr = electrical_power
    else:
        selected_feedback = steam_output_t4
    measured_feedback: Var = control.lag(
        'FeedbackTransducerPu', selected_feedback,
        control.parameter('T1', settings.t1), settings.t1, Const(0.5),
    )

    # The limiter holds its output within the step bound and its motion within
    # the gradient bound before the signal reaches the PI controller.
    speed_deviation: Expr = Const(1.0) - speed
    deadbanded_speed: Expr = (
        sym.max(speed_deviation - settings.fcut / 2.0, Const(0.0))
        + sym.min(speed_deviation + settings.fcut / 2.0, Const(0.0))
    )
    limiter_demand: Expr = reference + settings.ks * deadbanded_speed - measured_feedback
    limiter_state: Var = vfactory.add_var(f'StepGradientLimiterPu_{template_name}')
    control.differential(
        limiter_state,
        sym.hard_sat(limiter_demand - limiter_state, -settings.kg, settings.kg),
        Const(0.0),
        control.parameter('KLSMIN', -settings.kls),
        control.parameter('KLSMAX', settings.kls),
    )
    limiter_feedback: Var = control.algebraic(
        'StepGradientLimiterFeedbackPu', limiter_state, Const(0.0),
    )

    integral_state: Var = control.differential(
        vfactory.add_var(f'PIControllerIntegralPu_{template_name}'),
        limiter_feedback / control.parameter('TN', settings.tn),
        Const(0.0),
    )
    pi_output: Var = control.algebraic(
        'PIControllerOutputPu', settings.kp * (limiter_feedback + integral_state),
        Const(0.5),
    )
    valve_output: Var = control.lag(
        'ValveOutputPu', settings.kd * pi_output,
        control.parameter('TD', settings.td), settings.td, Const(0.5),
        control.parameter('PMIN', settings.pmin),
        control.parameter('PMAX', settings.pmax),
    )
    control.lag(
        'SteamOutputPu', valve_output,
        control.parameter('T4', settings.t4), settings.t4, Const(0.5),
        output=steam_output_t4,
    )

    turbine_power_t5: Var = control.lag(
        'IntermediateTurbinePowerPu', valve_output,
        control.parameter('T5', settings.t5), settings.t5, Const(0.5),
    )
    turbine_power_t6: Var = control.lag(
        'LowPressureTurbinePowerPu', valve_output,
        control.parameter('T6', settings.t6), settings.t6, Const(0.5),
    )
    mechanical_power: Var = control.algebraic(
        'PmPu', (1.0 - settings.k2) * steam_output_t4
        + settings.k2 * (1.0 - settings.k3) * turbine_power_t5
        + settings.k2 * settings.k3 * turbine_power_t6,
        Const(0.5),
    )
    return control.finish(
        (mechanical_power, valve_output),
        'CGMES GovSteamBB Brown-Boveri governor and three-section steam turbine',
    )
