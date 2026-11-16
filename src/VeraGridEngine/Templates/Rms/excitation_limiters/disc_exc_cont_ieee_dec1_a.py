# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for CGMES IEEE DEC1A."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import bool_and, flipflop, pickup_dropoff
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class DiscExcContIEEEDEC1AParameters:
    """Canonical IEEE DEC1A parameters from the CGMES RDF class."""

    __slots__ = (
        'vtlmt', 'vomax', 'vomin', 'ketl', 'vtc', 'val', 'esc', 'kan', 'tan',
        'tw5', 'vsmax', 'vsmin', 'td', 'tl1', 'tl2', 'vtm', 'vtn', 'vanmax',
    )

    def __init__(
            self,
            vtlmt: float = 1.1,
            vomax: float = 0.3,
            vomin: float = 0.1,
            ketl: float = 47.0,
            vtc: float = 0.95,
            val: float = 5.5,
            esc: float = 0.0015,
            kan: float = 400.0,
            tan: float = 0.08,
            tw5: float = 5.0,
            vsmax: float = 0.2,
            vsmin: float = -0.066,
            td: float = 0.03,
            tl1: float = 0.025,
            tl2: float = 1.25,
            vtm: float = 1.13,
            vtn: float = 1.12,
            vanmax: float = 1.0,
    ) -> None:
        """Store the standard DEC1A parameter values.

        :param vtlmt: Terminal-voltage limit reference.
        :param vomax: Upper terminal-limiter signal bound and hysteresis level.
        :param vomin: Lower terminal-limiter signal bound.
        :param ketl: Continuous terminal-voltage limiter gain.
        :param vtc: Terminal-voltage threshold for DEC pickup.
        :param val: Regulator-voltage threshold for DEC pickup.
        :param esc: Rotor-speed deviation threshold for DEC pickup.
        :param kan: DEC integrator gain.
        :param tan: DEC integrator reset time constant.
        :param tw5: Rotor-speed washout time constant.
        :param vsmax: Combined PSS/DEC upper output limit.
        :param vsmin: Combined PSS/DEC lower output limit.
        :param td: DEC relay drop-off delay.
        :param tl1: Continuous limiter lead time constant.
        :param tl2: Continuous limiter lag time constant.
        :param vtm: Bang-bang limiter upper voltage threshold.
        :param vtn: Bang-bang limiter lower voltage threshold.
        :param vanmax: DEC integrator upper bound.
        """
        self.vtlmt: float = vtlmt
        self.vomax: float = vomax
        self.vomin: float = vomin
        self.ketl: float = ketl
        self.vtc: float = vtc
        self.val: float = val
        self.esc: float = esc
        self.kan: float = kan
        self.tan: float = tan
        self.tw5: float = tw5
        self.vsmax: float = vsmax
        self.vsmin: float = vsmin
        self.td: float = td
        self.tl1: float = tl1
        self.tl2: float = tl2
        self.vtm: float = vtm
        self.vtn: float = vtn
        self.vanmax: float = vanmax


def build_disc_exc_cont_i_e_e_e_d_e_c1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: DiscExcContIEEEDEC1AParameters | None = None,
) -> RmsModelTemplate:
    """Build DEC1A voltage limiting, relay, washout, and integrator equations.

    :param vfactory: Factory allocating graph symbols and procedural state.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical CGMES DEC1A parameters.
    :return: DEC1A graph exposing terminal voltage, regulator voltage, speed,
        and PSS input ports.
    :raises ValueError: Parameters are nonfinite or violate stage bounds.
    """
    settings: DiscExcContIEEEDEC1AParameters = (
        DiscExcContIEEEDEC1AParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.vtlmt, settings.vomax, settings.vomin, settings.ketl,
        settings.vtc, settings.val, settings.esc, settings.kan, settings.tan,
        settings.tw5, settings.vsmax, settings.vsmin, settings.td, settings.tl1,
        settings.tl2, settings.vtm, settings.vtn, settings.vanmax,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES DEC1A parameters must be finite')
    elif min(settings.tan, settings.tw5, settings.td, settings.tl1, settings.tl2) < 0.0:
        raise ValueError('CGMES DEC1A time constants must be nonnegative')
    elif settings.vomin > settings.vomax or settings.vsmin >= settings.vsmax:
        raise ValueError('CGMES DEC1A limiter bounds are reversed')
    elif settings.vanmax < 0.0:
        raise ValueError('CGMES DEC1A VANMAX must be nonnegative')
    elif settings.tl2 == 0.0 and settings.tl1 != 0.0:
        raise ValueError('CGMES DEC1A TL2=0 requires TL1=0')
    else:
        pass

    template_name: str = 'DiscExcContIEEEDEC1A' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    terminal_voltage: Var = model.input('VtPu', Const(1.0))
    regulator_voltage: Var = model.input('VaPu', Const(5.5))
    speed_deviation: Var = model.input('SpeedDeviationPu', Const(0.0))
    stabilizer: Var = model.input('VstPu', Const(0.0))

    # The slow voltage path clips a lead-lag of the voltage-reference error.
    vtlmt: Var = model.parameter('DiscExcContIEEEDEC1A.vtlmt', settings.vtlmt)
    vomax: Var = model.parameter('DiscExcContIEEEDEC1A.vomax', settings.vomax)
    vomin: Var = model.parameter('DiscExcContIEEEDEC1A.vomin', settings.vomin)
    ketl: Var = model.parameter('DiscExcContIEEEDEC1A.ketl', settings.ketl)
    tl1: Var = model.parameter('DiscExcContIEEEDEC1A.tl1', settings.tl1)
    tl2: Var = model.parameter('DiscExcContIEEEDEC1A.tl2', settings.tl2)
    limiter_initial: float = min(
        settings.vomax,
        max(settings.vomin, settings.ketl * (settings.vtlmt - 1.0)),
    )
    limiter_error: Var = model.algebraic('LimiterErrorPu', vtlmt - terminal_voltage, Const(0.1))
    limiter_demand: Var = model.algebraic(
        'LimiterDemandPu', ketl * limiter_error, Const(settings.ketl * 0.1),
    )
    limiter_output: Var = model.bounded_lead_lag(
        'VoPu', limiter_demand, tl1, tl2, settings.tl1, settings.tl2,
        Const(limiter_initial), vomin, vomax,
    )

    # IEEE's Vp branch retains its prior value between the two voltage thresholds.
    vp: Var = vfactory.add_var(f'VpPu_{template_name}')
    vp_initial: float = 1.0 if 1.0 > settings.vtm else 0.0
    model.block.event_dict[vp] = vfactory.add_const(value=vp_initial)
    model.block.procedural_logic.append(
        flipflop(
            output=vp,
            boolset=terminal_voltage > Const(settings.vtm),
            boolreset=terminal_voltage < Const(settings.vtn),
            name=f'DEC1A.VoltageHysteresis_{template_name}',
        )
    )
    vp_limit: Var = model.algebraic(
        'BangBangVoltageLimitPu', vomax * vp, Const(settings.vomax * vp_initial),
    )
    high_gate_initial: float = max(limiter_initial, settings.vomax * vp_initial)
    high_voltage_gate: Var = model.algebraic(
        'TerminalVoltageLimitPu', sym.max(limiter_output, vp_limit), Const(high_gate_initial),
    )

    # Relay pickup requires a voltage drop, positive regulator ceiling, and speed rise;
    # TD holds the switch after pickup conditions clear, as specified by IEEE 421.5.
    vtc: Var = model.parameter('DiscExcContIEEEDEC1A.vtc', settings.vtc)
    val: Var = model.parameter('DiscExcContIEEEDEC1A.val', settings.val)
    esc: Var = model.parameter('DiscExcContIEEEDEC1A.esc', settings.esc)
    td: Var = model.parameter('DiscExcContIEEEDEC1A.td', settings.td)
    relay_closed: Var = vfactory.add_var(f'DEC1A_RelayClosed_{template_name}')
    model.block.event_dict[relay_closed] = vfactory.add_const(value=0.0)
    relay_condition: Expr = bool_and(
        terminal_voltage < vtc,
        regulator_voltage > val,
        speed_deviation > esc,
    )
    model.block.procedural_logic.append(
        pickup_dropoff(
            output=relay_closed,
            boolexpr=relay_condition,
            Tpick=Const(0.0),
            Tdrop=td,
            name=f'DEC1A.RelayDropDelay_{template_name}',
        )
    )

    # Rotor-angle change is the switched speed washout integrated with exponential reset.
    tw5: Var = model.parameter('DiscExcContIEEEDEC1A.tw5', settings.tw5)
    kan: Var = model.parameter('DiscExcContIEEEDEC1A.kan', settings.kan)
    tan: Var = model.parameter('DiscExcContIEEEDEC1A.tan', settings.tan)
    vanmax: Var = model.parameter('DiscExcContIEEEDEC1A.vanmax', settings.vanmax)
    if settings.tw5 > 0.0:
        speed_washout: Var = model.washout(
            'SpeedWashoutPu', speed_deviation, tw5, settings.tw5, Const(1.0), Const(0.0),
        )
    else:
        speed_washout = model.algebraic('SpeedWashoutPu', speed_deviation, Const(0.0))
    gated_speed: Var = model.algebraic(
        'GatedSpeedWashoutPu', relay_closed * speed_washout, Const(0.0),
    )
    integrator_demand: Var = model.algebraic('IntegratorDemandPu', kan * gated_speed, Const(0.0))
    angle_boost: Var = model.lag(
        'VanPu', integrator_demand, tan, settings.tan, Const(0.0), Const(0.0), vanmax,
    )

    # The terminal limiter opposes excess voltage; DEC angle boost adds to the PSS path.
    vsmax: Var = model.parameter('DiscExcContIEEEDEC1A.vsmax', settings.vsmax)
    vsmin: Var = model.parameter('DiscExcContIEEEDEC1A.vsmin', settings.vsmin)
    combined_initial: float = -high_gate_initial
    output_initial: float = min(settings.vsmax, max(settings.vsmin, combined_initial))
    combined_demand: Var = model.algebraic(
        'CombinedDemandPu', stabilizer + angle_boost - high_voltage_gate, Const(combined_initial),
    )
    output: Var = model.algebraic(
        'VsPu', sym.hard_sat(combined_demand, vsmin, vsmax), Const(output_initial),
    )
    template: RmsModelTemplate = model.finish((output,), 'IEEE DEC1A discontinuous excitation control')

    enabled_name: str = f'DiscExcContIEEEDEC1A.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    template.comment = (
        'IEEE 421.5-2016 DEC1A continuous terminal-voltage limiter, Vp hysteresis, '
        'TD relay drop delay, speed washout, bounded TAN reset, and summed output. '
        'The composer connects VaPu to the associated exciter RegulatorOutputPu when '
        'that sourced output exists; otherwise VaPu remains an explicit open input and '
        'the importer reports it. Canonical RDF requires vanmax; imports with a missing '
        'or nonnumeric value retain the RDF object but do not create this equation template.'
    )
    return template
