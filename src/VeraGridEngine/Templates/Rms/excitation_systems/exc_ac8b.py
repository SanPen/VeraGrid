# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAC8B alternator rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC8BParameters:
    """Numeric and selector settings declared by the CGMES ExcAC8B RDF class."""

    __slots__ = (
        'inlim', 'ka', 'kc', 'kd', 'kdr', 'ke', 'kir', 'kpr', 'ks', 'pidlim',
        'seve1', 'seve2', 'ta', 'tdr', 'te', 'telim', 've1', 've2', 'vemin',
        'vfemax', 'vimax', 'vimin', 'vpidmax', 'vpidmin', 'vrmax', 'vrmin', 'vtmult',
    )

    def __init__(
            self,
            inlim: bool = True,
            ka: float = 1.0,
            kc: float = 0.55,
            kd: float = 1.1,
            kdr: float = 10.0,
            ke: float = 1.0,
            kir: float = 5.0,
            kpr: float = 80.0,
            ks: float = 0.0,
            pidlim: bool = True,
            seve1: float = 0.3,
            seve2: float = 3.0,
            ta: float = 0.0,
            tdr: float = 0.1,
            te: float = 1.2,
            telim: bool = False,
            ve1: float = 6.5,
            ve2: float = 9.0,
            vemin: float = 0.0,
            vfemax: float = 6.0,
            vimax: float = 35.0,
            vimin: float = -10.0,
            vpidmax: float = 35.0,
            vpidmin: float = -10.0,
            vrmax: float = 35.0,
            vrmin: float = 0.0,
            vtmult: bool = False,
    ) -> None:
        """Store canonical settings and local EA typical defaults.

        :param inlim: Enable the input voltage-error limiter.
        :param ka: Amplifier gain.
        :param kc: Rectifier commutating-reactance factor.
        :param kd: Demagnetizing factor.
        :param kdr: Derivative gain.
        :param ke: Exciter field constant.
        :param kir: Integral gain.
        :param kpr: Proportional gain.
        :param ks: Speed correction gain.
        :param pidlim: Enable PID output limits.
        :param seve1: Saturation at ``ve1``.
        :param seve2: Saturation at ``ve2``.
        :param ta: Amplifier time constant.
        :param tdr: Derivative branch lag.
        :param te: Exciter time constant.
        :param telim: Enable the upper field-current limit.
        :param ve1: First saturation voltage.
        :param ve2: Second saturation voltage.
        :param vemin: Exciter voltage lower limit.
        :param vfemax: Exciter field-current limit reference.
        :param vimax: Input limiter upper limit.
        :param vimin: Input limiter lower limit.
        :param vpidmax: PID output upper limit.
        :param vpidmin: PID output lower limit.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param vtmult: Multiply regulator bounds by terminal voltage.
        """
        self.inlim: bool = inlim
        self.ka: float = ka
        self.kc: float = kc
        self.kd: float = kd
        self.kdr: float = kdr
        self.ke: float = ke
        self.kir: float = kir
        self.kpr: float = kpr
        self.ks: float = ks
        self.pidlim: bool = pidlim
        self.seve1: float = seve1
        self.seve2: float = seve2
        self.ta: float = ta
        self.tdr: float = tdr
        self.te: float = te
        self.telim: bool = telim
        self.ve1: float = ve1
        self.ve2: float = ve2
        self.vemin: float = vemin
        self.vfemax: float = vfemax
        self.vimax: float = vimax
        self.vimin: float = vimin
        self.vpidmax: float = vpidmax
        self.vpidmin: float = vpidmin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.vtmult: bool = vtmult


def build_exc_a_c8_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC8BParameters | None = None,
) -> RmsModelTemplate:
    """Build AC8B voltage PID, excitation, field-current limit, and rectifier equations.

    :param vfactory: Factory that owns the symbolic equations.
    :param name: Optional model instance name.
    :param parameters: Parsed CGMES parameters.
    :return: Equation-backed AC8B with machine voltage, current, speed, and Efd ports.
    :raises ValueError: If parameter domains make one of the block equations invalid.
    """
    settings: ExcAC8BParameters = ExcAC8BParameters() if parameters is None else parameters
    template_name: str = 'ExcAC8B' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.kc, settings.kd, settings.kdr, settings.ke, settings.kir,
        settings.kpr, settings.ks, settings.seve1, settings.seve2, settings.ta,
        settings.tdr, settings.te, settings.ve1, settings.ve2, settings.vemin,
        settings.vfemax, settings.vimax, settings.vimin, settings.vpidmax,
        settings.vpidmin, settings.vrmax, settings.vrmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC8B numeric parameters must be finite')
    elif min(settings.ta, settings.tdr, settings.te) < 0.0:
        raise ValueError('ExcAC8B time constants must be nonnegative')
    elif settings.te <= 0.0 or settings.tdr <= 0.0:
        raise ValueError('ExcAC8B T_E and T_DR must be positive')
    elif settings.vimin >= settings.vimax or settings.vpidmin >= settings.vpidmax:
        raise ValueError('ExcAC8B input and PID limits must be ordered')
    elif settings.vrmin >= settings.vrmax or settings.vemin < 0.0:
        raise ValueError('ExcAC8B regulator and exciter limits are invalid')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcAC8B saturation voltage points must be distinct and positive')
    elif settings.seve1 <= 0.0 or settings.seve2 <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcAC8B saturation values and K_E must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    kdr: Var = builder.parameter('KDR', settings.kdr)
    ke: Var = builder.parameter('KE', settings.ke)
    kir: Var = builder.parameter('KIR', settings.kir)
    kpr: Var = builder.parameter('KPR', settings.kpr)
    ks: Var = builder.parameter('KS', settings.ks)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    ta: Var = builder.parameter('TA', settings.ta)
    tdr: Var = builder.parameter('TDR', settings.tdr)
    te: Var = builder.parameter('TE', settings.te)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    vemin: Var = builder.parameter('VEMIN', settings.vemin)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    vimax: Var = builder.parameter('VIMAX', settings.vimax)
    vimin: Var = builder.parameter('VIMIN', settings.vimin)
    vpidmax: Var = builder.parameter('VPIDMAX', settings.vpidmax)
    vpidmin: Var = builder.parameter('VPIDMIN', settings.vpidmin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    underexcitation: Var = builder.input('VuelPu', Const(0.0))
    overexcitation: Var = builder.input('VoelPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    speed: Var = builder.input('OmegaPu', Const(1.0))

    raw_error: Expr = reference - terminal_voltage + stabilizer + underexcitation + overexcitation
    input_signal: Expr = raw_error
    if settings.inlim:
        input_signal = sym.hard_sat(raw_error, vimin, vimax)
    else:
        pass
    derivative_memory: Var = builder.lag('DerivativeMemoryPu', input_signal, tdr, settings.tdr, Const(0.0))
    derivative_signal: Expr = kdr * (input_signal - derivative_memory) / tdr
    integral: Var = vfactory.add_var(f'IntegralPu_{template_name}')
    integral_derivative: Expr = kir * input_signal
    if settings.pidlim:
        pid_unbounded: Expr = kpr * input_signal + integral + derivative_signal
        pid_signal: Var = builder.algebraic(
            'PidPu', sym.hard_sat(pid_unbounded, vpidmin, vpidmax), Const(0.0),
        )
        builder.differential(integral, integral_derivative, Const(0.0), vpidmin, vpidmax)
    else:
        pid_signal = builder.algebraic(
            'PidPu', kpr * input_signal + integral + derivative_signal, Const(0.0),
        )
        builder.differential(integral, integral_derivative, Const(0.0))
    regulator_state: Var = vfactory.add_var(f'RegulatorPu_{template_name}')
    amplifier_output: Var = builder.lag(
        'RegulatorPu', ka * pid_signal, ta, settings.ta, Const(0.0),
        vrmin * terminal_voltage if settings.vtmult else vrmin,
        vrmax * terminal_voltage if settings.vtmult else vrmax,
        output=regulator_state,
    )
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    saturation_b: float = math.log(settings.seve2 / settings.seve1) / (settings.ve2 - settings.ve1)
    saturation_a: float = settings.seve1 * math.exp(-saturation_b * settings.ve1)
    saturation: Expr = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_voltage)
    exciter_gain: Expr = ke + saturation
    exciter_feedback: Expr = exciter_gain * exciter_voltage + kd * field_current
    field_derivative: Expr = (amplifier_output - exciter_feedback) / te
    field_upper: Expr = sym.max((vfemax - kd * field_current) / exciter_gain, vemin)
    if settings.telim:
        builder.differential(exciter_voltage, field_derivative, Const(1.0), vemin, field_upper)
    else:
        builder.differential(exciter_voltage, field_derivative, Const(1.0), vemin, Const(1e12))
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    speed_factor: Expr = Const(1.0) + ks * (speed - Const(1.0))
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - exciter_voltage * sym.f_exc(rectifier_loading) * speed_factor)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    return builder.finish((field_voltage,), 'CGMES ExcAC8B alternator rectifier excitation system')
