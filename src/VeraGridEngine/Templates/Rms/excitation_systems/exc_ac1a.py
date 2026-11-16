# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAC1A alternator-supplied rectifier exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC1AParameters:
    """CGMES ExcAC1A regulator, gate, exciter, and rectifier settings."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf', 'kf1', 'kf2',
        'ks', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2',
        'vrmax', 'vrmin', 'hvlvgates',
    )

    def __init__(
            self,
            tb: float = 0.0,
            tc: float = 0.0,
            ka: float = 400.0,
            ta: float = 0.02,
            vamax: float = 14.5,
            vamin: float = -14.5,
            te: float = 0.8,
            kf: float = 0.03,
            kf1: float = 0.0,
            kf2: float = 1.0,
            ks: float = 0.0,
            tf: float = 1.0,
            kc: float = 0.2,
            kd: float = 0.38,
            ke: float = 1.0,
            ve1: float = 4.18,
            seve1: float = 0.1,
            ve2: float = 3.14,
            seve2: float = 0.03,
            vrmax: float = 6.03,
            vrmin: float = -5.43,
            hvlvgates: bool = True,
    ) -> None:
        """Store canonical CGMES fields in their declared units.

        :param tb: Voltage regulator lag time in seconds.
        :param tc: Voltage regulator lead time in seconds.
        :param ka: Voltage regulator gain.
        :param ta: Voltage regulator lag time in seconds.
        :param vamax: Voltage regulator output upper limit.
        :param vamin: Voltage regulator output lower limit.
        :param te: Exciter time constant in seconds.
        :param kf: Exciter stabilizer gain.
        :param kf1: Gain applied to the first feedback source.
        :param kf2: Gain applied to the second feedback source.
        :param ks: Speed deviation gain at the exciter output.
        :param tf: Exciter stabilizer time constant in seconds.
        :param kc: Rectifier commutating reactance factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Exciter field constant.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param hvlvgates: Whether the high and low voltage gates are active.
        """
        self.tb: float = tb
        self.tc: float = tc
        self.ka: float = ka
        self.ta: float = ta
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.te: float = te
        self.kf: float = kf
        self.kf1: float = kf1
        self.kf2: float = kf2
        self.ks: float = ks
        self.tf: float = tf
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.hvlvgates: bool = hvlvgates


def build_exc_a_c1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC1AParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES ExcAC1A control, exciter, and rectifier equations.

    The realization keeps the IEEE AC1A voltage path, selectable high/low
    voltage gates, dual-source field-voltage feedback, and speed multiplier.
    Zero-time controller stages reduce algebraically through ControlRealization.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES values used to select stage topology.
    :return: Executable AC1A excitation model with explicit machine and gate ports.
    :raises ValueError: Invalid times, bounds, or saturation points.
    """
    settings: ExcAC1AParameters = ExcAC1AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC1A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.te, settings.kf, settings.kf1, settings.kf2,
        settings.ks, settings.tf, settings.kc, settings.kd, settings.ke,
        settings.ve1, settings.seve1, settings.ve2, settings.seve2,
        settings.vrmax, settings.vrmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC1A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcAC1A times must be nonnegative and T_E must be positive')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcAC1A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC1A requires zero lead when T_B is zero')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcAC1A nonzero K_F requires positive T_F')
    elif (settings.seve1 == 0.0) != (settings.seve2 == 0.0):
        raise ValueError('ExcAC1A saturation requires both saturation values or neither')
    elif settings.seve1 == 0.0:
        pass
    elif (
            settings.ve1 <= 0.0 or settings.ve2 <= 0.0
            or settings.ve1 == settings.ve2
            or settings.seve1 < 0.0 or settings.seve2 < 0.0
    ):
        raise ValueError('ExcAC1A saturation needs distinct positive voltage points')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    kf1: Var = builder.parameter('KF1', settings.kf1)
    kf2: Var = builder.parameter('KF2', settings.kf2)
    ks: Var = builder.parameter('KS', settings.ks)
    tf: Var = builder.parameter('TF', settings.tf)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    ke: Var = builder.parameter('KE', settings.ke)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    speed: Var = builder.input('OmegaPu', Const(1.0))
    high_voltage_gate: Var = builder.input('VuelPu', Const(0.0))
    low_voltage_gate: Var = builder.input('VoelPu', Const(0.0))

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    saturation: Expr = Const(0.0)
    if settings.seve1 > 0.0 and settings.seve2 > 0.0:
        saturation_b: float = math.log(settings.seve2 / settings.seve1) / (settings.ve2 - settings.ve1)
        saturation_a: float = settings.seve1 * math.exp(-saturation_b * settings.ve1)
        saturation = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_voltage)
    else:
        pass
    exciter_voltage_feedback: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    feedback_source: Expr = kf1 * field_voltage + kf2 * exciter_voltage_feedback
    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', feedback_source, tf, settings.tf,
            Const(settings.kf / settings.tf), Const(0.0),
        )
    else:
        pass
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    lead_lag: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    regulator_output: Var = builder.lag(
        'RegulatorPu', ka * lead_lag, ta, settings.ta, Const(0.0), vamin, vamax,
    )
    gated_signal: Expr = regulator_output
    if settings.hvlvgates:
        gated_signal = sym.min(sym.max(regulator_output, high_voltage_gate), low_voltage_gate)
    else:
        pass
    regulator: Var = builder.algebraic(
        'RegulatorInputPu', sym.hard_sat(gated_signal, vrmin, vrmax), Const(0.0),
    )

    exciter_derivative: Expr = (regulator - exciter_voltage_feedback) / te
    exciter_derivative = (
        exciter_derivative * sym.heaviside(exciter_voltage - Const(1e-9))
        + sym.max(exciter_derivative, Const(0.0))
        * (Const(1.0) - sym.heaviside(exciter_voltage - Const(1e-9)))
    )
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0))
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    speed_correction: Expr = Const(1.0) + ks * (speed - Const(1.0))
    rectifier_output: Expr = exciter_voltage * sym.f_exc(rectifier_loading) * speed_correction
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(
        field_voltage - rectifier_output,
    )
    builder.block.init_eqs[field_voltage] = Const(1.0)
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcAC1A excitation system',
    )

    for parameter_name in (
            'enabled', 'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf',
            'kf1', 'kf2', 'ks', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1',
            've2', 'seve2', 'vrmax', 'vrmin', 'hvlvgates',
    ):
        variable_name: str = f'ExcAC1A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
