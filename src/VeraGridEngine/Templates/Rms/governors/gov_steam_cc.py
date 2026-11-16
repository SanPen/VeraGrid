# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamCC cross-compound steam governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamCCParameters:
    """Construction values using the exact scalar names from the CGMES class."""

    __slots__ = (
        'mwbase', 'pmaxhp', 'rhp', 't1hp', 't3hp', 't4hp', 't5hp', 'fhp', 'dhp',
        'pmaxlp', 'rlp', 't1lp', 't3lp', 't4lp', 't5lp', 'flp', 'dlp',
    )

    def __init__(
            self,
            mwbase: float = 100.0,
            pmaxhp: float = 1.0,
            rhp: float = 0.05,
            t1hp: float = 0.1,
            t3hp: float = 0.3,
            t4hp: float = 0.2,
            t5hp: float = 5.0,
            fhp: float = 0.3,
            dhp: float = 0.0,
            pmaxlp: float = 1.0,
            rlp: float = 0.05,
            t1lp: float = 0.1,
            t3lp: float = 0.3,
            t4lp: float = 0.2,
            t5lp: float = 5.0,
            flp: float = 0.7,
            dlp: float = 0.0,
    ) -> None:
        """Store the mapped GovSteamCC scalar values.

        :param mwbase: Power base in MW used by the importer for shaft-base conversion.
        :param pmaxhp: Maximum high-pressure valve position.
        :param rhp: High-pressure speed droop; must be positive.
        :param t1hp: High-pressure speed-feedback lag in seconds.
        :param t3hp: First high-pressure turbine lag in seconds.
        :param t4hp: Second high-pressure turbine lag in seconds.
        :param t5hp: High-pressure reheat lag in seconds.
        :param fhp: High-pressure reheat numerator fraction.
        :param dhp: High-pressure intermachine damping coefficient.
        :param pmaxlp: Maximum low-pressure valve position.
        :param rlp: Low-pressure speed droop; must be positive.
        :param t1lp: Low-pressure speed-feedback lag in seconds.
        :param t3lp: First low-pressure turbine lag in seconds.
        :param t4lp: Second low-pressure turbine lag in seconds.
        :param t5lp: Low-pressure reheat lag in seconds.
        :param flp: Low-pressure reheat numerator fraction.
        :param dlp: Low-pressure intermachine damping coefficient.
        """
        self.mwbase: float = mwbase
        self.pmaxhp: float = pmaxhp
        self.rhp: float = rhp
        self.t1hp: float = t1hp
        self.t3hp: float = t3hp
        self.t4hp: float = t4hp
        self.t5hp: float = t5hp
        self.fhp: float = fhp
        self.dhp: float = dhp
        self.pmaxlp: float = pmaxlp
        self.rlp: float = rlp
        self.t1lp: float = t1lp
        self.t3lp: float = t3lp
        self.t4lp: float = t4lp
        self.t5lp: float = t5lp
        self.flp: float = flp
        self.dlp: float = dlp


def build_gov_steam_c_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamCCParameters | None = None,
) -> RmsModelTemplate:
    """Build separate HP/LP governor and turbine equations from the EA diagram.

    The diagram has a shared speed reference, one filtered droop path and
    reheat turbine path per shaft, and a shared squared speed-difference
    damping input. All zero-time lags reduce to their exact static connection.

    :param vfactory: Factory that owns all symbolic variables.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical GovSteamCC scalar values.
    :return: Equation-backed template with two speed inputs and four power outputs.
    :raises ValueError: Invalid time constants, droop, or valve limits.
    """
    settings: GovSteamCCParameters = (
        GovSteamCCParameters() if parameters is None else parameters
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.pmaxhp, settings.rhp, settings.t1hp,
        settings.t3hp, settings.t4hp, settings.t5hp, settings.fhp, settings.dhp,
        settings.pmaxlp, settings.rlp, settings.t1lp, settings.t3lp,
        settings.t4lp, settings.t5lp, settings.flp, settings.dlp,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES GovSteamCC parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.rhp <= 0.0 or settings.rlp <= 0.0:
        raise ValueError('CGMES GovSteamCC requires positive mwbase and droops')
    elif min(
            settings.t1hp, settings.t3hp, settings.t4hp, settings.t5hp,
            settings.t1lp, settings.t3lp, settings.t4lp, settings.t5lp,
    ) < 0.0:
        raise ValueError('CGMES GovSteamCC time constants must be nonnegative')
    elif settings.pmaxhp < 0.0 or settings.pmaxlp < 0.0:
        raise ValueError('CGMES GovSteamCC valve maxima must be nonnegative')
    else:
        pass

    template_name: str = 'GovSteamCC' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)

    # Store the exact RDF property surface as runtime events; the shared power
    # base is consumed by the importer when connecting each shaft to its machine.
    mwbase: Var = control.parameter('mwbase', settings.mwbase)
    pmaxhp: Var = control.parameter('pmaxhp', settings.pmaxhp)
    rhp: Var = control.parameter('rhp', settings.rhp)
    t1hp: Var = control.parameter('t1hp', settings.t1hp)
    t3hp: Var = control.parameter('t3hp', settings.t3hp)
    t4hp: Var = control.parameter('t4hp', settings.t4hp)
    t5hp: Var = control.parameter('t5hp', settings.t5hp)
    fhp: Var = control.parameter('fhp', settings.fhp)
    dhp: Var = control.parameter('dhp', settings.dhp)
    pmaxlp: Var = control.parameter('pmaxlp', settings.pmaxlp)
    rlp: Var = control.parameter('rlp', settings.rlp)
    t1lp: Var = control.parameter('t1lp', settings.t1lp)
    t3lp: Var = control.parameter('t3lp', settings.t3lp)
    t4lp: Var = control.parameter('t4lp', settings.t4lp)
    t5lp: Var = control.parameter('t5lp', settings.t5lp)
    flp: Var = control.parameter('flp', settings.flp)
    dlp: Var = control.parameter('dlp', settings.dlp)
    omega_hp: Var = control.input('OmegaHpPu', Const(1.0))
    omega_lp: Var = control.input('OmegaLpPu', Const(1.0))
    omega_reference: Var = control.parameter('OmegaRefPu', 1.0)

    # The branch diagram filters absolute shaft speed, scales it by reciprocal
    # droop, subtracts it from the shared reference, then clips valve position.
    hp_speed: Var = control.lag(
        'GovSteamCCHpSpeedFilter', omega_hp, t1hp, settings.t1hp, omega_hp
    )
    lp_speed: Var = control.lag(
        'GovSteamCCLpSpeedFilter', omega_lp, t1lp, settings.t1lp, omega_lp
    )
    hp_valve: Var = control.algebraic(
        'GovSteamCCHpValvePu',
        sym.hard_sat(omega_reference - hp_speed / rhp, Const(0.0), pmaxhp),
        sym.hard_sat(omega_reference - omega_hp / rhp, Const(0.0), pmaxhp),
    )
    lp_valve: Var = control.algebraic(
        'GovSteamCCLpValvePu',
        sym.hard_sat(omega_reference - lp_speed / rlp, Const(0.0), pmaxlp),
        sym.hard_sat(omega_reference - omega_lp / rlp, Const(0.0), pmaxlp),
    )

    # Each shaft has three denominator stages; the final stage carries its own
    # (1+s*F*T5) numerator. ControlRealization removes zero-time stages exactly.
    hp_stage3: Var = control.lag(
        'GovSteamCCHpT3', hp_valve, t3hp, settings.t3hp, hp_valve
    )
    hp_stage4: Var = control.lag(
        'GovSteamCCHpT4', hp_stage3, t4hp, settings.t4hp, hp_stage3
    )
    hp_turbine: Var = control.lead_lag(
        'GovSteamCCHpTurbine', hp_stage4, fhp * t5hp, t5hp,
        settings.fhp * settings.t5hp, settings.t5hp, hp_stage4,
    )
    lp_stage3: Var = control.lag(
        'GovSteamCCLpT3', lp_valve, t3lp, settings.t3lp, lp_valve
    )
    lp_stage4: Var = control.lag(
        'GovSteamCCLpT4', lp_stage3, t4lp, settings.t4lp, lp_stage3
    )
    lp_turbine: Var = control.lead_lag(
        'GovSteamCCLpTurbine', lp_stage4, flp * t5lp, t5lp,
        settings.flp * settings.t5lp, settings.t5lp, lp_stage4,
    )

    # The EA diagram subtracts a damping block from each shaft's turbine power;
    # the LP block itself is drawn with a negative gain and joins its summer additively.
    speed_difference: Expr = omega_hp - omega_lp
    damping_power_hp: Expr = dhp * speed_difference * speed_difference
    damping_power_lp: Expr = dlp * speed_difference * speed_difference
    mechanical_power_hp: Var = control.algebraic(
        'gov.PmHpPu', hp_turbine - damping_power_hp, hp_turbine
    )
    mechanical_power_lp: Var = control.algebraic(
        'gov.PmLpPu', lp_turbine - damping_power_lp, lp_turbine
    )
    mechanical_power_hp_mw: Var = control.algebraic(
        'gov.PmHpMW', mwbase * mechanical_power_hp,
        Const(settings.mwbase) * hp_turbine,
    )
    mechanical_power_lp_mw: Var = control.algebraic(
        'gov.PmLpMW', mwbase * mechanical_power_lp,
        Const(settings.mwbase) * lp_turbine,
    )
    runtime_template: RmsModelTemplate = control.finish(
        (mechanical_power_hp, mechanical_power_lp,
         mechanical_power_hp_mw, mechanical_power_lp_mw),
        'CGMES GovSteamCC two-shaft governor and reheat turbine',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = runtime_template.tpe
    template.block = runtime_template.block
    template.comment = (
        'CGMES GovSteamCC HP/LP equations from the CGMES EA block diagram; '
        'shaft signals require paired-machine composition.'
    )
    return template
