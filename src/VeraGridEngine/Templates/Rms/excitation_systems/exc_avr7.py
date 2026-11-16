# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR7 three-stage lead-lag excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAVR7Parameters:
    """The 21 numeric properties declared by the canonical CGMES ExcAVR7 class."""

    __slots__ = (
        'k1', 'a1', 'a2', 't1', 't2', 'vmax1', 'vmin1', 'k3', 'a3', 'a4',
        't3', 't4', 'vmax3', 'vmin3', 'k5', 'a5', 'a6', 't5', 't6', 'vmax5', 'vmin5',
    )

    def __init__(
            self,
            k1: float = 1.0,
            a1: float = 0.5,
            a2: float = 0.5,
            t1: float = 0.05,
            t2: float = 0.1,
            vmax1: float = 5.0,
            vmin1: float = -5.0,
            k3: float = 3.0,
            a3: float = 0.5,
            a4: float = 0.5,
            t3: float = 0.1,
            t4: float = 0.1,
            vmax3: float = 5.0,
            vmin3: float = -5.0,
            k5: float = 1.0,
            a5: float = 0.5,
            a6: float = 0.5,
            t5: float = 0.1,
            t6: float = 0.1,
            vmax5: float = 5.0,
            vmin5: float = -2.0,
    ) -> None:
        """Store settings with local EA typical values as defaults.

        :param k1: First stage gain.
        :param a1: First stage numerator constant.
        :param a2: First stage denominator constant.
        :param t1: First stage numerator time.
        :param t2: First stage denominator time.
        :param vmax1: First stage upper limit.
        :param vmin1: First stage lower limit.
        :param k3: Second stage gain.
        :param a3: Second stage numerator constant.
        :param a4: Second stage denominator constant.
        :param t3: Second stage numerator time.
        :param t4: Second stage denominator time.
        :param vmax3: Second stage upper limit.
        :param vmin3: Second stage lower limit.
        :param k5: Third stage gain.
        :param a5: Third stage numerator constant.
        :param a6: Third stage denominator constant.
        :param t5: Third stage numerator time.
        :param t6: Third stage denominator time.
        :param vmax5: Final output upper limit.
        :param vmin5: Final output lower limit.
        """
        self.k1: float = k1
        self.a1: float = a1
        self.a2: float = a2
        self.t1: float = t1
        self.t2: float = t2
        self.vmax1: float = vmax1
        self.vmin1: float = vmin1
        self.k3: float = k3
        self.a3: float = a3
        self.a4: float = a4
        self.t3: float = t3
        self.t4: float = t4
        self.vmax3: float = vmax3
        self.vmin3: float = vmin3
        self.k5: float = k5
        self.a5: float = a5
        self.a6: float = a6
        self.t5: float = t5
        self.t6: float = t6
        self.vmax5: float = vmax5
        self.vmin5: float = vmin5


def build_limited_rational_stage(
        builder: ControlRealization,
        vfactory: VarFactory,
        name: str,
        signal: Expr,
        gain: Var,
        numerator_a: Var,
        denominator_a: Var,
        numerator_t: Var,
        denominator_t: Var,
        denominator_a_value: float,
        numerator_t_value: float,
        denominator_t_value: float,
        lower: Var,
        upper: Var,
) -> Var:
    """Realize and limit ``gain*(A1+sT1)/(A2+sT2)``.

    :param builder: Owner for stage states and algebraic outputs.
    :param vfactory: Factory creating the denominator memory state.
    :param name: Runtime stage identifier.
    :param signal: Input expression.
    :param gain: Stage gain symbol.
    :param numerator_a: Numerator constant symbol.
    :param denominator_a: Denominator constant symbol.
    :param numerator_t: Numerator time symbol.
    :param denominator_t: Denominator time symbol.
    :param denominator_a_value: Construction-time denominator constant.
    :param numerator_t_value: Construction-time numerator time.
    :param denominator_t_value: Construction-time denominator time.
    :param lower: Output lower limit.
    :param upper: Output upper limit.
    :return: Limited stage output.
    :raises ValueError: The selected transfer would be improper or singular.
    """
    if denominator_t_value > 0.0:
        memory: Var = vfactory.add_var(f'{name}MemoryPu_{builder.name}')
        memory_initial: Expr = signal / denominator_a if denominator_a_value != 0.0 else Const(0.0)
        builder.differential(
            memory,
            (signal - denominator_a * memory) / denominator_t,
            memory_initial,
        )
        direct_gain: Expr = gain * numerator_t / denominator_t
        memory_gain: Expr = gain * (numerator_a - numerator_t * denominator_a / denominator_t)
        raw_output: Expr = direct_gain * signal + memory_gain * memory
        steady_output: Expr = gain * numerator_a / denominator_a * signal
        return builder.algebraic(
            name + 'OutputPu',
            sym.hard_sat(raw_output, lower, upper),
            sym.hard_sat(steady_output, lower, upper),
        )
    elif numerator_t_value == 0.0 and denominator_a_value != 0.0:
        static_gain: Expr = gain * numerator_a / denominator_a
        return builder.algebraic(
            name + 'OutputPu', sym.hard_sat(static_gain * signal, lower, upper), Const(0.0),
        )
    else:
        raise ValueError('ExcAVR7 stage denominator is singular or transfer is improper: ' + name)


def build_exc_a_v_r7_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR7Parameters | None = None,
) -> RmsModelTemplate:
    """Build three bounded AVR7 rational stages from the EA block diagram.

    :param vfactory: Factory owning the model graph.
    :param name: Optional runtime instance name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed AVR7 with voltage/reference/stabilizer inputs.
    :raises ValueError: Nonfinite parameters, invalid bounds, or improper transfer stages.
    """
    settings: ExcAVR7Parameters = ExcAVR7Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR7' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.k1, settings.a1, settings.a2, settings.t1, settings.t2,
        settings.vmax1, settings.vmin1, settings.k3, settings.a3, settings.a4,
        settings.t3, settings.t4, settings.vmax3, settings.vmin3, settings.k5,
        settings.a5, settings.a6, settings.t5, settings.t6, settings.vmax5, settings.vmin5,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR7 parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.t5, settings.t6) < 0.0:
        raise ValueError('ExcAVR7 time constants must be nonnegative')
    elif settings.vmin1 >= settings.vmax1 or settings.vmin3 >= settings.vmax3 or settings.vmin5 >= settings.vmax5:
        raise ValueError('ExcAVR7 stage limits must be ordered')
    elif settings.a2 == 0.0 and settings.t2 == 0.0:
        raise ValueError('ExcAVR7 first stage denominator cannot be zero')
    elif settings.a4 == 0.0 and settings.t4 == 0.0:
        raise ValueError('ExcAVR7 second stage denominator cannot be zero')
    elif settings.a6 == 0.0 and settings.t6 == 0.0:
        raise ValueError('ExcAVR7 third stage denominator cannot be zero')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    k1: Var = builder.parameter('K1', settings.k1)
    a1: Var = builder.parameter('A1', settings.a1)
    a2: Var = builder.parameter('A2', settings.a2)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    vmax1: Var = builder.parameter('VMAX1', settings.vmax1)
    vmin1: Var = builder.parameter('VMIN1', settings.vmin1)
    k3: Var = builder.parameter('K3', settings.k3)
    a3: Var = builder.parameter('A3', settings.a3)
    a4: Var = builder.parameter('A4', settings.a4)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    vmax3: Var = builder.parameter('VMAX3', settings.vmax3)
    vmin3: Var = builder.parameter('VMIN3', settings.vmin3)
    k5: Var = builder.parameter('K5', settings.k5)
    a5: Var = builder.parameter('A5', settings.a5)
    a6: Var = builder.parameter('A6', settings.a6)
    t5: Var = builder.parameter('T5', settings.t5)
    t6: Var = builder.parameter('T6', settings.t6)
    vmax5: Var = builder.parameter('VMAX5', settings.vmax5)
    vmin5: Var = builder.parameter('VMIN5', settings.vmin5)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))

    input_signal: Expr = reference - terminal_voltage + stabilizer
    first_output: Var = build_limited_rational_stage(
        builder, vfactory, 'FirstStage', input_signal, k1, a1, a2, t1, t2, settings.a2,
        settings.t1, settings.t2, vmin1, vmax1,
    )
    second_output: Var = build_limited_rational_stage(
        builder, vfactory, 'SecondStage', first_output, k3, a3, a4, t3, t4, settings.a4,
        settings.t3, settings.t4, vmin3, vmax3,
    )
    final_output: Var = build_limited_rational_stage(
        builder, vfactory, 'FinalStage', second_output, k5, a5, a6, t5, t6, settings.a6,
        settings.t5, settings.t6, vmin5, vmax5,
    )
    field_voltage: Var = builder.algebraic('EfdPu', final_output, Const(1.0))
    return builder.finish((field_voltage,), 'CGMES ExcAVR7 three-stage excitation system')
