# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC1A alternator-rectifier exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC1AParameters:
    """CGMES AC1A regulator, exciter, saturation, and rectifier settings."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf', 'tf', 'kc',
        'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'vrmax', 'vrmin',
    )

    def __init__(
            self,
            tb: float = 0.0,
            tc: float = 0.0,
            ka: float = 400.0,
            ta: float = 0.02,
            vamax: float = 15.0,
            vamin: float = -15.0,
            te: float = 0.8,
            kf: float = 0.03,
            tf: float = 1.0,
            kc: float = 0.2,
            kd: float = 0.38,
            ke: float = 1.0,
            ve1: float = 4.18,
            seve1: float = 0.1,
            ve2: float = 3.14,
            seve2: float = 0.03,
            vrmax: float = 7.3,
            vrmin: float = -6.6,
    ) -> None:
        """Store CGMES quantities in per-unit and seconds.

        :param tb: Lead-lag denominator time in seconds.
        :param tc: Lead-lag numerator time in seconds.
        :param ka: Regulator gain.
        :param ta: Regulator time in seconds.
        :param vamax: Lead-lag output upper limit.
        :param vamin: Lead-lag output lower limit.
        :param te: Exciter integration time in seconds.
        :param kf: Excitation stabilizer gain.
        :param tf: Excitation stabilizer time in seconds.
        :param kc: Rectifier loading factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Exciter field constant.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        """
        self.tb: float = tb
        self.tc: float = tc
        self.ka: float = ka
        self.ta: float = ta
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.te: float = te
        self.kf: float = kf
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


def build_exc_i_e_e_e_a_c1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC1AParameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE AC1A regulator, exciter, and rectifier equations.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES values used to select exact stage topology.
    :return: Executable AC1A excitation model with four host input ports.
    :raises ValueError: Invalid limits, times, or saturation points.
    """
    settings: ExcIEEEAC1AParameters = (
        ExcIEEEAC1AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC1A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.te, settings.kf, settings.tf, settings.kc,
        settings.kd, settings.ke, settings.ve1, settings.seve1, settings.ve2,
        settings.seve2, settings.vrmax, settings.vrmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEAC1A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcIEEEAC1A times must be nonnegative and T_E must be positive')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEAC1A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEAC1A requires zero lead when T_B is zero')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcIEEEAC1A nonzero K_F requires positive T_F')
    elif settings.seve1 == 0.0 and settings.seve2 == 0.0:
        pass
    elif (
            settings.ve1 > 0.0 and settings.ve2 > 0.0
            and settings.ve1 != settings.ve2
            and settings.seve1 > 0.0 and settings.seve2 > 0.0
    ):
        saturation_b = math.log(settings.seve2 / settings.seve1) / (settings.ve2 - settings.ve1)
        saturation_a = settings.seve1 * math.exp(-saturation_b * settings.ve1)
    else:
        raise ValueError('ExcIEEEAC1A saturation needs two positive, distinct voltage points')

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
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

    # Exciter feedback is the proper transfer Kf*s/(1+s*Tf) from Ve.
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', exciter_voltage, tf, settings.tf,
            Const(settings.kf / settings.tf), exciter_voltage,
        )
    else:
        pass
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    lead_lag: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    amplifier_input: Var = builder.algebraic(
        'AmplifierInputPu', sym.hard_sat(lead_lag, vamin, vamax), Const(0.0),
    )
    regulator: Var = builder.lag(
        'RegulatorPu', ka * amplifier_input, ta, settings.ta, Const(0.0), vrmin, vrmax,
    )

    # The exponential saturation remains tied to editable RDF curve points.
    saturation_active: Expr = sym.heaviside(seve1) * sym.heaviside(seve2)
    safe_seve1: Expr = sym.max(seve1, Const(1e-12))
    safe_seve2: Expr = sym.max(seve2, Const(1e-12))
    voltage_span: Expr = ve2 - ve1
    safe_voltage_span: Expr = (
        voltage_span * sym.heaviside(sym.abs(voltage_span) - Const(1e-12))
        + Const(1e-12) * (Const(1.0) - sym.heaviside(sym.abs(voltage_span) - Const(1e-12)))
    )
    saturation_b_expression: Expr = sym.log(safe_seve2 / safe_seve1) / safe_voltage_span
    saturation_a_expression: Expr = safe_seve1 * sym.exp(-saturation_b_expression * ve1)
    saturation: Expr = (
        saturation_active
        * saturation_a_expression
        * sym.exp(saturation_b_expression * exciter_voltage)
    )
    exciter_derivative: Expr = (
        regulator - (ke + saturation) * exciter_voltage - kd * field_current
    ) / te
    exciter_derivative = (
        exciter_derivative * sym.heaviside(exciter_voltage - Const(1e-9))
        + sym.max(exciter_derivative, Const(0.0))
        * (Const(1.0) - sym.heaviside(exciter_voltage - Const(1e-9)))
    )
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0))
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    field_voltage: Var = builder.algebraic(
        'EfdPu',
        exciter_voltage * sym.f_exc(rectifier_loading),
        Const(1.0),
    )
    template: RmsModelTemplate = builder.finish((field_voltage,), 'CGMES ExcIEEEAC1A excitation system')

    # Keep the exact class property names available for RDF parameter editing.
    for parameter_name in (
            'enabled', 'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'kf',
            'tf', 'kc', 'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'vrmax', 'vrmin',
    ):
        variable_name: str = f'ExcIEEEAC1A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
