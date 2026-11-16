# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcELIN2 voltage and field-current controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcELIN2Parameters:
    """Settings declared by the canonical CGMES ExcELIN2 class."""

    __slots__ = (
        'k1', 'k1ec', 'kd1', 'tb1', 'pid1max', 'ti1', 'iefmax2', 'k2', 'ketb',
        'upmax', 'upmin', 'te', 'xp', 'te2', 'ke2', 've1', 'seve1', 've2',
        'seve2', 'tr4', 'k3', 'ti3', 'k4', 'ti4', 'iefmax', 'iefmin', 'efdbas',
    )

    def __init__(
            self,
            k1: float = 0.0,
            k1ec: float = 2.0,
            kd1: float = 34.5,
            tb1: float = 12.45,
            pid1max: float = 2.0,
            ti1: float = 0.0,
            iefmax2: float = -5.0,
            k2: float = 5.0,
            ketb: float = 0.06,
            upmax: float = 3.0,
            upmin: float = 0.0,
            te: float = 0.0,
            xp: float = 1.0,
            te2: float = 1.0,
            ke2: float = 0.1,
            ve1: float = 3.0,
            seve1: float = 0.0,
            ve2: float = 0.0,
            seve2: float = 1.0,
            tr4: float = 1.0,
            k3: float = 0.1,
            ti3: float = 3.0,
            k4: float = 0.0,
            ti4: float = 0.0,
            iefmax: float = 1.0,
            iefmin: float = 1.0,
            efdbas: float = 0.1,
    ) -> None:
        """Store the EA typical values without changing source point order.

        :param k1: Voltage regulator proportional gain.
        :param k1ec: Exciter current regulator gain scale.
        :param kd1: Voltage regulator derivative gain.
        :param tb1: Derivative washout time constant in seconds.
        :param pid1max: Symmetric voltage regulator output limit.
        :param ti1: Voltage regulator integral time coefficient.
        :param iefmax2: Voltage regulator integral output bound parameter.
        :param k2: Exciter field-current regulator gain.
        :param ketb: Thyristor converter gain.
        :param upmax: Upper regulator output bound.
        :param upmin: Lower regulator output bound.
        :param te: Thyristor converter time constant in seconds.
        :param xp: Excitation transformer effective reactance.
        :param te2: Brushless exciter integration time in seconds; zero bypasses the state.
        :param ke2: Brushless exciter field constant.
        :param ve1: First exciter saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second exciter saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        :param tr4: Field-current measurement filter time constant in seconds.
        :param k3: Minimum field-current limiter gain.
        :param ti3: Minimum limiter integration time in seconds.
        :param k4: Maximum field-current limiter gain.
        :param ti4: Maximum limiter integration time in seconds.
        :param iefmax: Maximum field-current limit.
        :param iefmin: Minimum field-current limit.
        :param efdbas: Exciter field-voltage base conversion factor.
        """
        self.k1: float = k1
        self.k1ec: float = k1ec
        self.kd1: float = kd1
        self.tb1: float = tb1
        self.pid1max: float = pid1max
        self.ti1: float = ti1
        self.iefmax2: float = iefmax2
        self.k2: float = k2
        self.ketb: float = ketb
        self.upmax: float = upmax
        self.upmin: float = upmin
        self.te: float = te
        self.xp: float = xp
        self.te2: float = te2
        self.ke2: float = ke2
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2
        self.tr4: float = tr4
        self.k3: float = k3
        self.ti3: float = ti3
        self.k4: float = k4
        self.ti4: float = ti4
        self.iefmax: float = iefmax
        self.iefmin: float = iefmin
        self.efdbas: float = efdbas


def build_exc_e_l_i_n2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcELIN2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the ELIN2 voltage regulator, current limiters, and brushless exciter.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Model with terminal voltage, reference, stabilizer, Ifd, and Efd ports.
    :raises ValueError: Invalid time constants, limiter bounds, or saturation points.
    """
    settings: ExcELIN2Parameters = ExcELIN2Parameters() if parameters is None else parameters
    template_name: str = 'ExcELIN2' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.k1, settings.k1ec, settings.kd1, settings.tb1, settings.pid1max,
        settings.ti1, settings.iefmax2, settings.k2, settings.ketb, settings.upmax,
        settings.upmin, settings.te, settings.xp, settings.te2, settings.ke2,
        settings.ve1, settings.seve1, settings.ve2, settings.seve2, settings.tr4,
        settings.k3, settings.ti3, settings.k4, settings.ti4, settings.iefmax,
        settings.iefmin, settings.efdbas,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcELIN2 parameters must be finite')
    elif min(settings.tb1, settings.ti1, settings.te, settings.te2, settings.tr4,
             settings.ti3, settings.ti4) < 0.0:
        raise ValueError('ExcELIN2 time constants must be nonnegative')
    elif settings.pid1max < 0.0 or settings.k1ec < 0.0 or settings.upmin > settings.upmax:
        raise ValueError('ExcELIN2 regulator limits must be ordered and nonnegative')
    elif settings.ve1 == settings.ve2 or settings.efdbas <= 0.0:
        raise ValueError('ExcELIN2 saturation points must differ and EFDBAS must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    k1: Var = builder.parameter('K1', settings.k1)
    k1ec: Var = builder.parameter('K1EC', settings.k1ec)
    kd1: Var = builder.parameter('KD1', settings.kd1)
    tb1: Var = builder.parameter('TB1', settings.tb1)
    pid1max: Var = builder.parameter('PID1MAX', settings.pid1max)
    ti1: Var = builder.parameter('TI1', settings.ti1)
    iefmax2: Var = builder.parameter('IEfMAX2', settings.iefmax2)
    k2: Var = builder.parameter('K2', settings.k2)
    ketb: Var = builder.parameter('KETB', settings.ketb)
    upmax: Var = builder.parameter('UPMAX', settings.upmax)
    upmin: Var = builder.parameter('UPMIN', settings.upmin)
    te: Var = builder.parameter('TE', settings.te)
    xp: Var = builder.parameter('XP', settings.xp)
    te2: Var = builder.parameter('TE2', settings.te2)
    ke2: Var = builder.parameter('KE2', settings.ke2)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    tr4: Var = builder.parameter('TR4', settings.tr4)
    k3: Var = builder.parameter('K3', settings.k3)
    ti3: Var = builder.parameter('TI3', settings.ti3)
    k4: Var = builder.parameter('K4', settings.k4)
    ti4: Var = builder.parameter('TI4', settings.ti4)
    iefmax: Var = builder.parameter('IEfMAX', settings.iefmax)
    iefmin: Var = builder.parameter('IEfMIN', settings.iefmin)
    efdbas: Var = builder.parameter('EFDBAS', settings.efdbas)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    regulator_error: Expr = reference - terminal_voltage + supplementary
    derivative_output: Expr = Const(0.0)
    if settings.kd1 != 0.0 and settings.tb1 > 0.0:
        derivative_output = builder.washout(
            'VoltageDerivativePu', regulator_error, tb1,
            settings.tb1, kd1 / tb1, regulator_error,
        )
        derivative_output = sym.hard_sat(
            derivative_output,
            -Const(2.0) * k1ec,
            Const(2.0) * k1ec,
        )
    else:
        pass
    if settings.ti1 == 0.0:
        integral_output: Expr = Const(0.0)
    else:
        integral_state: Var = vfactory.add_var(f'VoltageIntegralPu_{template_name}')
        integral_limit: Expr = sym.abs(iefmax2)
        integral_output = builder.differential(
            integral_state,
            regulator_error / ti1,
            Const(0.0),
            -integral_limit,
            integral_limit,
        )
    voltage_regulator: Expr = sym.hard_sat(
        k1 * regulator_error + derivative_output + integral_output,
        -pid1max,
        pid1max,
    )

    filtered_field_current: Expr = field_current
    if settings.tr4 > 0.0:
        filtered_field_current = builder.lag(
            'FieldCurrentFilterPu', field_current, tr4,
            settings.tr4, field_current,
        )
    else:
        pass
    limiter_step: Expr = Const(3.56) * k1ec
    minimum_error: Expr = sym.max(
        iefmin - filtered_field_current, Const(0.0),
    )
    if settings.ti3 == 0.0:
        minimum_limiter: Expr = sym.hard_sat(
            k3 * minimum_error, Const(0.0), limiter_step,
        )
    else:
        minimum_state: Var = vfactory.add_var(f'MinimumFieldCurrentLimiterPu_{template_name}')
        minimum_state = builder.differential(
            minimum_state,
            k3 * minimum_error / ti3,
            Const(0.0), Const(0.0), limiter_step,
        )
        minimum_limiter = sym.hard_sat(
            k3 * minimum_error + minimum_state,
            Const(0.0), limiter_step,
        )
    maximum_error: Expr = sym.max(
        filtered_field_current - iefmax, Const(0.0),
    )
    if settings.ti4 == 0.0:
        maximum_limiter: Expr = sym.hard_sat(
            -k4 * maximum_error, -limiter_step, Const(0.0),
        )
    else:
        maximum_state: Var = vfactory.add_var(f'MaximumFieldCurrentLimiterPu_{template_name}')
        maximum_state = builder.differential(
            maximum_state,
            -k4 * maximum_error / ti4,
            Const(0.0), -limiter_step, Const(0.0),
        )
        maximum_limiter = sym.hard_sat(
            -k4 * maximum_error + maximum_state,
            -limiter_step, Const(0.0),
        )
    current_reference: Expr = sym.hard_sat(
        voltage_regulator + minimum_limiter + maximum_limiter,
        iefmin, iefmax,
    )
    current_regulator: Expr = sym.hard_sat(
        k2 * (current_reference - filtered_field_current),
        upmin, upmax,
    )
    converter_command: Expr = ketb * current_regulator
    converter_lower: Expr = terminal_voltage * upmin
    converter_upper: Expr = terminal_voltage * upmax
    if settings.te == 0.0:
        converter_voltage: Expr = sym.hard_sat(
            converter_command, converter_lower, converter_upper,
        )
    else:
        converter_voltage = builder.lag(
            'ConverterVoltagePu', converter_command, te,
            settings.te, Const(0.0), converter_lower, converter_upper,
        )

    field_state: Var = vfactory.add_var(f'BrushlessFieldVoltagePu_{template_name}')
    saturation_slope: float = (
        settings.seve2 - settings.seve1
    ) / (settings.ve2 - settings.ve1)
    saturation: Expr = sym.max(
        seve1 + Const(saturation_slope) * (field_state - ve1),
        Const(0.0),
    )
    brushless_drive: Expr = (
        converter_voltage + xp * filtered_field_current
        - (ke2 + saturation) * field_state
    )
    initial_field: Const = Const(1.0 / settings.efdbas)
    if settings.te2 == 0.0:
        builder.block.algebraic_vars.append(field_state)
        builder.block.algebraic_eqs.append(field_state - brushless_drive)
        builder.block.init_eqs[field_state] = initial_field
    else:
        builder.differential(
            field_state,
            brushless_drive / te2,
            initial_field,
        )
    field_voltage: Var = builder.algebraic(
        'EfdPu', efdbas * field_state, Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcELIN2 thyristor and brushless exciter')
