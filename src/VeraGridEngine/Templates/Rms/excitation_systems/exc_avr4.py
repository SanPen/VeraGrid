# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR4 excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAVR4Parameters:
    """Numeric and boolean settings declared by the CGMES ExcAVR4 class."""

    __slots__ = (
        'ka', 'vrmn', 'vrmx', 't1', 't2', 't3', 't4', 'ke', 'vfmx', 'vfmn',
        'kif', 'tif', 't1if', 'imul',
    )

    def __init__(
            self,
            ka: float = 300.0,
            vrmn: float = 0.0,
            vrmx: float = 5.0,
            t1: float = 4.8,
            t2: float = 1.5,
            t3: float = 0.0,
            t4: float = 0.0,
            ke: float = 1.0,
            vfmx: float = 5.0,
            vfmn: float = 0.0,
            kif: float = 0.0,
            tif: float = 0.0,
            t1if: float = 60.0,
            imul: bool = True,
    ) -> None:
        """Store canonical values and local EA typical defaults.

        :param ka: AVR gain.
        :param vrmn: Lower AVR output limit.
        :param vrmx: Upper AVR output limit.
        :param t1: First regulator denominator time.
        :param t2: First regulator filter time.
        :param t3: Second regulator ratio numerator time.
        :param t4: Second regulator filter time.
        :param ke: Exciter gain.
        :param vfmx: Upper exciter output limit.
        :param vfmn: Lower exciter output limit.
        :param kif: Exciter field-current feedback gain.
        :param tif: Lower-path current filter time.
        :param t1if: Upper-path current filter time.
        :param imul: Multiply the exciter output by terminal voltage.
        """
        self.ka: float = ka
        self.vrmn: float = vrmn
        self.vrmx: float = vrmx
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.ke: float = ke
        self.vfmx: float = vfmx
        self.vfmn: float = vfmn
        self.kif: float = kif
        self.tif: float = tif
        self.t1if: float = t1if
        self.imul: bool = imul


def build_exc_a_v_r4_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR4Parameters | None = None,
) -> RmsModelTemplate:
    """Build AVR4 regulator filters, current feedback, exciter clamp, and multiplier.

    :param vfactory: Factory that owns the symbolic equations.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES AVR4 settings.
    :return: Equation-backed regulator with terminal voltage, Ifd, and Efd ports.
    :raises ValueError: Invalid selector, time, or bound values.
    """
    settings: ExcAVR4Parameters = ExcAVR4Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR4' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.vrmn, settings.vrmx, settings.t1, settings.t2,
        settings.t3, settings.t4, settings.ke, settings.vfmx, settings.vfmn,
        settings.kif, settings.tif, settings.t1if,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR4 numeric parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.tif, settings.t1if) < 0.0:
        raise ValueError('ExcAVR4 time constants must be nonnegative')
    elif settings.t1 <= 0.0 or settings.t2 <= 0.0 or settings.t1if <= 0.0:
        raise ValueError('ExcAVR4 T1, T2, and T1IF must be positive')
    elif (settings.t4 == 0.0 and settings.t3 != 0.0) or settings.vrmn >= settings.vrmx:
        raise ValueError('ExcAVR4 second stage or AVR limits are invalid')
    elif settings.vfmn >= settings.vfmx:
        raise ValueError('ExcAVR4 exciter limits must be ordered')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    vrmn: Var = builder.parameter('VRMN', settings.vrmn)
    vrmx: Var = builder.parameter('VRMX', settings.vrmx)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    ke: Var = builder.parameter('KE', settings.ke)
    vfmx: Var = builder.parameter('VFMX', settings.vfmx)
    vfmn: Var = builder.parameter('VFMN', settings.vfmn)
    kif: Var = builder.parameter('KIF', settings.kif)
    tif: Var = builder.parameter('TIF', settings.tif)
    t1if: Var = builder.parameter('T1IF', settings.t1if)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    voltage_error: Expr = reference - terminal_voltage + stabilizer
    avr_demand: Expr = ka * voltage_error
    first_ratio: Var = t2 / t1
    first_state: Var = vfactory.add_var(f'FirstStageMemoryPu_{template_name}')
    first_lower: Expr = vrmn - avr_demand * first_ratio
    first_upper: Expr = vrmx - avr_demand * first_ratio
    builder.differential(
        first_state, (avr_demand - first_state) / t2, Const(0.0), first_lower, first_upper,
    )
    first_output: Expr = first_ratio * avr_demand + (Const(1.0) - first_ratio) * first_state
    second_output: Expr = first_output
    if settings.t4 > 0.0:
        second_ratio: Var = t3 / t4
        second_state: Var = vfactory.add_var(f'SecondStageMemoryPu_{template_name}')
        second_lower: Expr = vrmn - avr_demand * second_ratio
        second_upper: Expr = vrmx - avr_demand * second_ratio
        builder.differential(
            second_state, (first_output - second_state) / t4, Const(0.0), second_lower, second_upper,
        )
        second_output = second_ratio * first_output + (Const(1.0) - second_ratio) * second_state
    else:
        pass
    upper_current_filter: Var = builder.lag(
        'UpperCurrentMemoryPu', field_current, t1if, settings.t1if, Const(0.0),
    )
    lower_current_filter: Var = builder.lag(
        'LowerCurrentMemoryPu', field_current, tif, settings.tif, Const(0.0),
    )
    current_limiter_feedback: Expr = kif * (upper_current_filter - lower_current_filter)
    exciter_input: Expr = second_output + current_limiter_feedback
    exciter_output: Var = builder.algebraic(
        'ExciterOutputPu', sym.hard_sat(ke * exciter_input, vfmn, vfmx), Const(1.0),
    )
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    multiplier: Expr = terminal_voltage if settings.imul else Const(1.0)
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - exciter_output * multiplier)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    return builder.finish((field_voltage,), 'CGMES ExcAVR4 excitation system')
