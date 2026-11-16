# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Unsaturated WT2G1 induction-generator electrical core without shaft inertia."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wt2g1ElectricalSettings:
    """Hold WT2G1 machine data and the attached network operating point."""

    __slots__ = ('xa', 'xm', 'x1', 'r_rot_mach', 'r_rot_max', 'e1', 'se1',
                 'e2', 'se2', 'ra', 'nominal_frequency_hz', 'initial_speed',
                 'initial_resistance_fraction', 'initial_vd', 'initial_vq')

    def __init__(self, xa: float = .126, xm: float = 6.84, x1: float = .18,
                 r_rot_mach: float = .0044, r_rot_max: float = .1099,
                 e1: float = 1., se1: float = 0., e2: float = 1.2, se2: float = 0.,
                 ra: float = 0., nominal_frequency_hz: float = 50.,
                 initial_speed: float = 1.02, initial_resistance_fraction: float = .2,
                 initial_vd: float = 0., initial_vq: float = 1.) -> None:
        """Store the source machine values and host-owned initial conditions.

        :param xa: Stator leakage reactance on machine MVA base.
        :param xm: Magnetizing reactance.
        :param x1: Rotor leakage reactance.
        :param r_rot_mach: Internal rotor resistance.
        :param r_rot_max: Total available rotor resistance.
        :param e1: First saturation coordinate.
        :param se1: First saturation factor; currently zero only.
        :param e2: Second saturation coordinate.
        :param se2: Second saturation factor; currently zero only.
        :param ra: Stator resistance from the power-flow source impedance.
        :param nominal_frequency_hz: Electrical base frequency.
        :param initial_speed: Initial generator speed in per unit.
        :param initial_resistance_fraction: Initial share of available external resistance.
        :param initial_vd: Initial d-axis terminal voltage.
        :param initial_vq: Initial q-axis terminal voltage.
        :return: None.
        """
        self.xa: float = xa
        self.xm: float = xm
        self.x1: float = x1
        self.r_rot_mach: float = r_rot_mach
        self.r_rot_max: float = r_rot_max
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.ra: float = ra
        self.nominal_frequency_hz: float = nominal_frequency_hz
        self.initial_speed: float = initial_speed
        self.initial_resistance_fraction: float = initial_resistance_fraction
        self.initial_vd: float = initial_vd
        self.initial_vq: float = initial_vq


def _wt2g1_steady_current(
        settings: Wt2g1ElectricalSettings, speed: float,
        resistance_fraction: float, voltage: complex,
) -> complex:
    """Solve the unsaturated steady rotor and stator circuit at one slip.

    :param settings: Physical machine parameters.
    :param speed: Generator speed in per unit.
    :param resistance_fraction: Share of available external rotor resistance.
    :param voltage: Terminal d/q voltage phasor.
    :return: Stator current flowing into the machine.
    """
    wb: float = 2. * math.pi * settings.nominal_frequency_hz
    xs: float = settings.xa + settings.xm
    xp: float = settings.xa + settings.xm * settings.x1 / (settings.xm + settings.x1)
    rotor_resistance: float = (settings.r_rot_mach + resistance_fraction
                               * (settings.r_rot_max - settings.r_rot_mach))
    tp: float = (settings.xm + settings.x1) / (wb * rotor_resistance)
    rotor_factor: complex = 1. + 1j * wb * (1. - speed) * tp
    impedance: complex = complex(settings.ra, xp) + 1j * (xs - xp) / rotor_factor
    return voltage / impedance


def derive_wt2g1_operating_point(
        source: Wt2g1ElectricalSettings, target_power: float,
        voltage_d: float, voltage_q: float,
        curve: tuple[tuple[float, float], ...],
) -> Wt2g1ElectricalSettings:
    """Fit initial slip and resistance fraction to solved machine-base P.

    This restricted initializer uses an increasing WT2G1 power-slip curve.
    It does not resolve nonmonotonic source curves or nonzero saturation.

    :param source: WT2G1 physical source data.
    :param target_power: Solved generator P on its own MVA base.
    :param voltage_d: Solved d-axis terminal voltage.
    :param voltage_q: Solved q-axis terminal voltage.
    :param curve: Five ordered (generator slip, power) points.
    :return: New settings with matched speed, fraction and terminal voltage.
    :raises ValueError: Invalid or unreachable operating point.
    """
    if (not math.isfinite(target_power) or target_power < 0
            or not math.isfinite(voltage_d) or not math.isfinite(voltage_q)
            or voltage_d == 0 and voltage_q == 0):
        raise ValueError('WT2G1 target power and voltage must be finite and physical')
    elif (not all(math.isfinite(value) for value in (
            source.xa, source.xm, source.x1, source.r_rot_mach, source.r_rot_max,
            source.e1, source.se1, source.e2, source.se2,
            source.ra, source.nominal_frequency_hz,
    )) or source.xa < 0 or source.xm <= 0 or source.x1 < 0
          or source.r_rot_mach <= 0 or source.r_rot_max < source.r_rot_mach
          or source.ra < 0 or source.nominal_frequency_hz <= 0
          or source.se1 != 0 or source.se2 != 0):
        raise ValueError('WT2G1 source machine data are invalid or saturated')
    elif len(curve) != 5 or curve[0] != (0., 0.):
        raise ValueError('WT2G1 initial power-slip curve needs five points from the origin')
    else:
        pass
    previous_slip: float = -math.inf
    previous_power: float = -math.inf
    point_slip: float
    point_power: float
    for point_slip, point_power in curve:
        if (not math.isfinite(point_slip) or not math.isfinite(point_power)
                or point_slip <= previous_slip or point_power <= previous_power):
            raise ValueError('WT2G1 initial curve must increase in slip and power')
        else:
            previous_slip = point_slip
            previous_power = point_power
    if target_power > curve[-1][1]:
        raise ValueError('WT2G1 target power exceeds the source power-slip curve')
    else:
        pass
    slip: float = 0.
    index: int
    for index in range(1, 5):
        if curve[index - 1][1] <= target_power <= curve[index][1]:
            span_power: float = curve[index][1] - curve[index - 1][1]
            slip = (curve[index - 1][0] + (target_power - curve[index - 1][1])
                    * (curve[index][0] - curve[index - 1][0]) / span_power)
            break
        else:
            pass
    speed: float = 1. + slip
    voltage: complex = complex(voltage_d, voltage_q)
    lower: float = 0.
    upper: float = 1.
    current_lower: complex = _wt2g1_steady_current(source, speed, lower, voltage)
    current_upper: complex = _wt2g1_steady_current(source, speed, upper, voltage)
    power_lower: float = -(voltage_d * current_lower.real + voltage_q * current_lower.imag)
    power_upper: float = -(voltage_d * current_upper.real + voltage_q * current_upper.imag)
    if not min(power_lower, power_upper) <= target_power <= max(power_lower, power_upper):
        raise ValueError('WT2G1 target power is unreachable within rotor-resistance limits')
    else:
        pass
    midpoint: float = 0.
    midpoint_power: float = 0.
    iteration: int
    for iteration in range(60):
        midpoint = (lower + upper) / 2.
        current_mid: complex = _wt2g1_steady_current(source, speed, midpoint, voltage)
        midpoint_power = -(voltage_d * current_mid.real + voltage_q * current_mid.imag)
        if (midpoint_power - target_power) * (power_lower - target_power) > 0:
            lower = midpoint
            power_lower = midpoint_power
        else:
            upper = midpoint
    if abs(midpoint_power - target_power) > 1e-9:
        raise ValueError('WT2G1 rotor-resistance fit did not converge')
    else:
        pass
    return Wt2g1ElectricalSettings(
        xa=source.xa, xm=source.xm, x1=source.x1,
        r_rot_mach=source.r_rot_mach, r_rot_max=source.r_rot_max,
        e1=source.e1, se1=source.se1, e2=source.e2, se2=source.se2,
        ra=source.ra, nominal_frequency_hz=source.nominal_frequency_hz,
        initial_speed=speed, initial_resistance_fraction=midpoint,
        initial_vd=voltage_d, initial_vq=voltage_q,
    )


def build_wt2g1_electrical_core(
        vf: VarFactory, name: str = 'WT2G1 electrical core',
        settings: Wt2g1ElectricalSettings | None = None,
) -> RmsModelTemplate:
    """Build the unsaturated rotor-flux and terminal-current Type 2 equations.

    This core has no inertia or hidden Q-matching shunt. Its machine-base
    P/Q/current outputs are open to the network host and Type 2 controls.

    :param vf: Shared symbolic variable factory.
    :param name: Unique machine name.
    :param settings: WT2G1 source data and initial network conditions.
    :return: Native two-flux-state induction-generator electrical core.
    :raises ValueError: Unsupported saturation or invalid source/host values.
    """
    selected: Wt2g1ElectricalSettings = Wt2g1ElectricalSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.xa, selected.xm, selected.x1,
                                 selected.r_rot_mach, selected.r_rot_max,
                                 selected.e1, selected.se1, selected.e2, selected.se2,
                                 selected.ra, selected.nominal_frequency_hz,
                                 selected.initial_speed, selected.initial_resistance_fraction,
                                 selected.initial_vd, selected.initial_vq)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WT2G1 electrical data must be finite')
    elif selected.xa < 0 or selected.xm <= 0 or selected.x1 < 0:
        raise ValueError('WT2G1 reactances are invalid')
    elif (selected.r_rot_mach <= 0 or selected.r_rot_max < selected.r_rot_mach
          or not 0 <= selected.initial_resistance_fraction <= 1):
        raise ValueError('WT2G1 rotor-resistance range is invalid')
    elif selected.ra < 0 or selected.nominal_frequency_hz <= 0 or selected.initial_speed <= 0:
        raise ValueError('WT2G1 stator resistance, frequency or speed is invalid')
    elif selected.e1 <= 0 or selected.e2 <= selected.e1 or selected.se1 != 0 or selected.se2 != 0:
        raise ValueError('WT2G1 electrical core currently requires zero saturation')
    elif selected.initial_vd == 0 and selected.initial_vq == 0:
        raise ValueError('WT2G1 initial terminal voltage must be nonzero')
    else:
        pass

    # The controller selects a fraction of R_ROT_MAX minus R_ROT_MACH; the
    # source's example limits near one distinguish this from physical ohms.
    # Solve the steady rotor equation and stator Thevenin circuit together,
    # so the two flux states and both terminal-current equations start in balance.
    xp0: float = selected.xa + selected.xm * selected.x1 / (selected.xm + selected.x1)
    voltage0: complex = complex(selected.initial_vd, selected.initial_vq)
    current0: complex = _wt2g1_steady_current(
        selected, selected.initial_speed, selected.initial_resistance_fraction, voltage0,
    )
    emf0: complex = voltage0 - complex(selected.ra, xp0) * current0
    power0: float = -(selected.initial_vd * current0.real + selected.initial_vq * current0.imag)
    reactive0: float = -(selected.initial_vq * current0.real - selected.initial_vd * current0.imag)
    torque0: float = -(emf0.real * current0.real + emf0.imag * current0.imag) / selected.initial_speed

    vd: Var = vf.add_var('VdPu_' + name)
    vq: Var = vf.add_var('VqPu_' + name)
    speed: Var = vf.add_var('GeneratorSpeedPu_' + name)
    resistance_fraction: Var = vf.add_var('RotorResistanceFraction_' + name)
    ed: Var = vf.add_var('EdPrimePu_' + name)
    eq: Var = vf.add_var('EqPrimePu_' + name)
    id_current: Var = vf.add_var('IdPu_' + name)
    iq_current: Var = vf.add_var('IqPu_' + name)
    electrical_power: Var = vf.add_var('ElectricalPowerPu_' + name)
    reactive_power: Var = vf.add_var('ReactivePowerPu_' + name)
    electrical_torque: Var = vf.add_var('ElectricalTorquePu_' + name)
    xa: Var = vf.add_var('XA_' + name)
    xm: Var = vf.add_var('XM_' + name)
    x1: Var = vf.add_var('X1_' + name)
    r_rot_mach: Var = vf.add_var('R_ROT_MACH_' + name)
    r_rot_max: Var = vf.add_var('R_ROT_MAX_' + name)
    ra: Var = vf.add_var('RA_' + name)
    f_nominal: Var = vf.add_var('FNomHz_' + name)
    wb: Expr = Const(2. * math.pi) * f_nominal
    xs: Expr = xa + xm
    xp: Expr = xa + xm * x1 / (xm + x1)
    delta: Expr = xs - xp
    rotor_resistance: Expr = (r_rot_mach + sym.hard_sat(
        resistance_fraction, Const(0.), Const(1.),
    ) * (r_rot_max - r_rot_mach))
    tp: Expr = (xm + x1) / (wb * rotor_resistance)
    slip: Expr = Const(1.) - speed
    ded: Expr = wb * slip * eq - (ed + delta * iq_current) / tp
    deq: Expr = -wb * slip * ed - (eq - delta * id_current) / tp

    block: Block = Block(
        name=name,
        state_vars=list((ed, eq)),
        diff_vars=list((vf.add_diff_var('d_' + ed.name, base_var=ed),
                        vf.add_diff_var('d_' + eq.name, base_var=eq))),
        state_eqs=list((ded, deq)),
        algebraic_vars=list((id_current, iq_current, electrical_power,
                             reactive_power, electrical_torque)),
        algebraic_eqs=list((
            vd - ed - ra * id_current + xp * iq_current,
            vq - eq - ra * iq_current - xp * id_current,
            electrical_power + vd * id_current + vq * iq_current,
            reactive_power + vq * id_current - vd * iq_current,
            electrical_torque + (ed * id_current + eq * iq_current) / speed,
        )),
        init_eqs=dict(((vd, Const(selected.initial_vd)),
                       (vq, Const(selected.initial_vq)),
                       (speed, Const(selected.initial_speed)),
                       (resistance_fraction, Const(selected.initial_resistance_fraction)),
                       (ed, Const(emf0.real)), (eq, Const(emf0.imag)),
                       (id_current, Const(current0.real)), (iq_current, Const(current0.imag)),
                       (electrical_power, Const(power0)), (reactive_power, Const(reactive0)),
                       (electrical_torque, Const(torque0)))),
        event_dict=dict(((xa, Const(selected.xa)), (xm, Const(selected.xm)),
                         (x1, Const(selected.x1)), (r_rot_mach, Const(selected.r_rot_mach)),
                         (r_rot_max, Const(selected.r_rot_max)), (ra, Const(selected.ra)),
                         (f_nominal, Const(selected.nominal_frequency_hz)))),
        in_vars=list((vd, vq, speed, resistance_fraction)),
        out_vars=list((electrical_power, reactive_power, electrical_torque,
                       id_current, iq_current)),
    )
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.NoDevice
    template.block = block
    template.comment = 'Unsaturated WT2G1 electrical core with explicit machine and network ports'
    return template
