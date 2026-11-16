# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC8B PID alternator excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC8BParameters:
    """Settings declared by the canonical ExcIEEEAC8B RDF class."""

    __slots__ = (
        'kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'ka', 'ta', 'te',
        'vfemax', 'vemin', 'ke', 'kc', 'kd', 've1', 'seve1', 've2', 'seve2',
    )

    def __init__(
            self,
            kpr: float = 80.0,
            kir: float = 5.0,
            kdr: float = 10.0,
            tdr: float = 0.1,
            vrmax: float = 35.0,
            vrmin: float = 0.0,
            ka: float = 1.0,
            ta: float = 0.0,
            te: float = 1.2,
            vfemax: float = 6.0,
            vemin: float = 0.0,
            ke: float = 1.0,
            kc: float = 0.55,
            kd: float = 1.1,
            ve1: float = 6.5,
            seve1: float = 0.3,
            ve2: float = 9.0,
            seve2: float = 3.0,
    ) -> None:
        """Store CGMES values with the local EA typicals as missing-value fallbacks.

        :param kpr: Voltage-regulator proportional gain.
        :param kir: Voltage-regulator integral gain.
        :param kdr: Voltage-regulator derivative gain.
        :param tdr: Derivative-branch lag time constant.
        :param vrmax: Regulator-output upper limit.
        :param vrmin: Regulator-output lower limit.
        :param ka: Amplifier gain.
        :param ta: Amplifier time constant.
        :param te: Exciter winding integration time constant.
        :param vfemax: Exciter field-current limit reference.
        :param vemin: Minimum exciter winding voltage.
        :param ke: Exciter field constant.
        :param kc: Rectifier commutating-reactance coefficient.
        :param kd: Exciter demagnetizing factor.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        """
        self.kpr: float = kpr
        self.kir: float = kir
        self.kdr: float = kdr
        self.tdr: float = tdr
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ka: float = ka
        self.ta: float = ta
        self.te: float = te
        self.vfemax: float = vfemax
        self.vemin: float = vemin
        self.ke: float = ke
        self.kc: float = kc
        self.kd: float = kd
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2


def build_exc_i_e_e_e_a_c8_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC8BParameters | None = None,
) -> RmsModelTemplate:
    """Build the AC8B PID, amplifier, rotating field, and rectifier graph.

    :param vfactory: Factory owning variables and differential states.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values or EA typical defaults.
    :return: Equation-backed excitation system with machine-facing ports.
    :raises ValueError: If the supplied limits, gains, or time constants are invalid.
    """
    settings: ExcIEEEAC8BParameters = (
        ExcIEEEAC8BParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC8B' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.kpr, settings.kir, settings.kdr, settings.tdr,
        settings.vrmax, settings.vrmin, settings.ka, settings.ta, settings.te,
        settings.vfemax, settings.vemin, settings.ke, settings.kc, settings.kd,
        settings.ve1, settings.seve1, settings.ve2, settings.seve2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEAC8B parameters must be finite')
    elif min(settings.tdr, settings.ta, settings.te) < 0.0:
        raise ValueError('ExcIEEEAC8B time constants must be nonnegative')
    elif settings.te <= 0.0 or settings.ke <= 0.0 or settings.ka <= 0.0:
        raise ValueError('ExcIEEEAC8B TE, KE, and KA must be positive')
    elif settings.kdr != 0.0 and settings.tdr <= 0.0:
        raise ValueError('ExcIEEEAC8B nonzero KDR requires positive TDR')
    elif settings.vrmin >= settings.vrmax or settings.vemin < 0.0:
        raise ValueError('ExcIEEEAC8B regulator and exciter limits are invalid')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcIEEEAC8B saturation points must be distinct and positive')
    elif settings.seve1 < 0.0 or settings.seve2 < 0.0 or settings.vfemax <= 0.0:
        raise ValueError('ExcIEEEAC8B saturation and field-current limits are invalid')
    elif (settings.seve1 == 0.0) != (settings.seve2 == 0.0):
        raise ValueError('ExcIEEEAC8B saturation samples must both be zero or positive')
    elif settings.kpr == 0.0 and settings.kir == 0.0:
        raise ValueError('ExcIEEEAC8B requires proportional or integral voltage action')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    kpr: Var = builder.parameter('KPR', settings.kpr)
    kir: Var = builder.parameter('KIR', settings.kir)
    kdr: Var = builder.parameter('KDR', settings.kdr)
    tdr: Var = builder.parameter('TDR', settings.tdr)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    te: Var = builder.parameter('TE', settings.te)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    vemin: Var = builder.parameter('VEMIN', settings.vemin)
    ke: Var = builder.parameter('KE', settings.ke)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer, Const(0.0),
    )
    derivative_term: Expr = Const(0.0)
    if settings.kdr != 0.0:
        derivative_memory: Var = builder.lag(
            'DerivativeMemoryPu', voltage_error, tdr, settings.tdr, Const(0.0),
        )
        derivative_term = kdr * (voltage_error - derivative_memory) / tdr
    else:
        pass

    integral: Var = vfactory.add_var(f'IntegralPu_{template_name}')
    builder.differential(integral, kir * voltage_error, Const(0.0))
    pid_output: Expr = kpr * voltage_error + integral + derivative_term
    regulator: Var = builder.lag(
        'RegulatorPu', ka * pid_output, ta, settings.ta, Const(0.0), vrmin, vrmax,
    )

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    saturation: Expr = Const(0.0)
    if settings.seve1 > 0.0 and settings.seve2 > 0.0:
        saturation_slope: Expr = sym.log(seve2 / seve1) / (ve2 - ve1)
        saturation_base: Expr = seve1 * sym.exp(-saturation_slope * ve1)
        saturation = saturation_base * sym.exp(saturation_slope * exciter_voltage)
    else:
        pass
    equivalent_field_expression: Expr = (
        ke * exciter_voltage + saturation * exciter_voltage + kd * field_current
    )
    exciter_derivative: Expr = (regulator - equivalent_field_expression) / te
    field_upper: Expr = sym.max((vfemax - kd * field_current) / (ke + saturation), vemin)
    builder.differential(
        exciter_voltage,
        exciter_derivative,
        Const(1.0),
        vemin,
        field_upper,
    )

    equivalent_field: Var = builder.algebraic(
        'VfePu', equivalent_field_expression, Const(1.0),
    )
    delivered_field: Var = builder.algebraic(
        'EfdPu', exciter_voltage * sym.f_exc(
            sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0)),
        ), Const(1.0),
    )
    template: RmsModelTemplate = builder.finish(
        (delivered_field,), 'CGMES ExcIEEEAC8B PID alternator excitation system',
    )
    for parameter_name in (
            'enabled', 'kpr', 'kir', 'kdr', 'tdr', 'vrmax', 'vrmin', 'ka',
            'ta', 'te', 'vfemax', 'vemin', 'ke', 'kc', 'kd', 've1', 'seve1',
            've2', 'seve2',
    ):
        variable_name: str = f'ExcIEEEAC8B.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template
