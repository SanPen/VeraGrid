# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES Pss2ST model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import InputSignalKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Pss2STParameters:
    """Canonical CGMES Pss2ST scalar settings and signal selectors."""

    __slots__ = (
        'input_signal1_type', 'input_signal2_type', 'k1', 'k2', 't1', 't2',
        't3', 't4', 't5', 't6', 't7', 't8', 't9', 't10', 'lsmax', 'lsmin',
        'vcu', 'vcl',
    )

    def __init__(
            self,
            input_signal1_type: InputSignalKind | None = InputSignalKind.rotorAngularFrequencyDeviation,
            input_signal2_type: InputSignalKind | None = InputSignalKind.generatorElectricalPower,
            k1: float = 0.0,
            k2: float = 0.0,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.0,
            t4: float = 0.0,
            t5: float = 0.0,
            t6: float = 0.0,
            t7: float = 0.0,
            t8: float = 0.0,
            t9: float = 0.0,
            t10: float = 0.0,
            lsmax: float = 0.0,
            lsmin: float = 0.0,
            vcu: float = 0.0,
            vcl: float = 0.0,
    ) -> None:
        """Store parsed Pss2ST values in their RDF units.

        :param input_signal1_type: Selector for the first input channel.
        :param input_signal2_type: Selector for the second input channel.
        :param k1: Gain on the first RDF selected input.
        :param k2: Gain on the second RDF selected input.
        :param t1: First input lag time in seconds.
        :param t2: Second input lag time in seconds.
        :param t3: Washout numerator time in seconds.
        :param t4: Washout denominator time in seconds.
        :param t5: First phase numerator time in seconds.
        :param t6: First phase denominator time in seconds.
        :param t7: Second phase numerator time in seconds.
        :param t8: Second phase denominator time in seconds.
        :param t9: Output path numerator time in seconds.
        :param t10: Output path denominator time in seconds.
        :param lsmax: Upper stabilizer output limit in per unit.
        :param lsmin: Lower stabilizer output limit in per unit.
        :param vcu: Upper terminal-voltage cutoff in per unit.
        :param vcl: Lower terminal-voltage cutoff in per unit.
        """
        self.input_signal1_type: InputSignalKind | None = input_signal1_type
        self.input_signal2_type: InputSignalKind | None = input_signal2_type
        self.k1: float = k1
        self.k2: float = k2
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t5: float = t5
        self.t6: float = t6
        self.t7: float = t7
        self.t8: float = t8
        self.t9: float = t9
        self.t10: float = t10
        self.lsmax: float = lsmax
        self.lsmin: float = lsmin
        self.vcu: float = vcu
        self.vcl: float = vcl


def build_pss2_s_t_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: Pss2STParameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1313 dual-input Pss2ST graph and voltage cutoff.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES Pss2ST settings.
    :return: Equation-backed stabilizer with two selected inputs and Vct.
    :raises ValueError: Invalid time constants, limits, or improper rate stages.
    """
    settings: Pss2STParameters = Pss2STParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.k1, settings.k2, settings.t1, settings.t2, settings.t3,
        settings.t4, settings.t5, settings.t6, settings.t7, settings.t8,
        settings.t9, settings.t10, settings.lsmax, settings.lsmin,
        settings.vcu, settings.vcl,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES Pss2ST parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.t5,
             settings.t6, settings.t7, settings.t8, settings.t9, settings.t10) < 0.0:
        raise ValueError('CGMES Pss2ST times must be nonnegative')
    elif settings.t4 == 0.0 and settings.t3 > 0.0:
        raise ValueError('CGMES Pss2ST washout denominator time must be positive when T3 is nonzero')
    elif ((settings.t2 == 0.0 and settings.t1 > 0.0)
          or (settings.t6 == 0.0 and settings.t5 > 0.0)
          or (settings.t8 == 0.0 and settings.t7 > 0.0)
          or (settings.t10 == 0.0 and settings.t9 > 0.0)):
        raise ValueError('CGMES Pss2ST lead time requires a nonzero lag time')
    elif settings.lsmin > settings.lsmax or settings.vcl > settings.vcu:
        raise ValueError('CGMES Pss2ST output or voltage limits must be ordered')
    else:
        pass

    template_name: str = 'Pss2ST' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    signal1: Var = model.input('Signal1Pu', Const(0.0))
    signal2: Var = model.input('Signal2Pu', Const(0.0))
    terminal_voltage: Var = model.input('VctPu', Const(1.0))
    input1: Var = model.lag(
        'Input1Pu', model.parameter('Pss2ST.k1', settings.k1) * signal1,
        model.parameter('Pss2ST.t1', settings.t1), settings.t1, Const(0.0),
    )
    input2: Var = model.lag(
        'Input2Pu', model.parameter('Pss2ST.k2', settings.k2) * signal2,
        model.parameter('Pss2ST.t2', settings.t2), settings.t2, Const(0.0),
    )
    summed_input: Var = model.algebraic('SummedInputPu', input1 + input2, Const(0.0))
    if settings.t3 > 0.0 and settings.t4 > 0.0:
        washed_signal: Var = model.washout(
            'WashoutPu', summed_input, model.parameter('Pss2ST.t4', settings.t4),
            settings.t4,
            model.parameter('Pss2ST.t3', settings.t3) / model.parameter('Pss2ST.t4', settings.t4),
            Const(0.0),
        )
    else:
        washed_signal = model.algebraic('WashoutPu', Const(0.0), Const(0.0))
    first_phase: Var = model.lead_lag(
        'FirstPhasePu', washed_signal, model.parameter('Pss2ST.t5', settings.t5),
        model.parameter('Pss2ST.t6', settings.t6), settings.t5, settings.t6, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase, model.parameter('Pss2ST.t7', settings.t7),
        model.parameter('Pss2ST.t8', settings.t8), settings.t7, settings.t8, Const(0.0),
    )
    output_filter: Var = model.lead_lag(
        'OutputFilterPu', second_phase, model.parameter('Pss2ST.t9', settings.t9),
        model.parameter('Pss2ST.t10', settings.t10), settings.t9, settings.t10, Const(0.0),
    )
    limited_output: Expr = sym.hard_sat(
        output_filter,
        model.parameter('Pss2ST.lsmin', settings.lsmin),
        model.parameter('Pss2ST.lsmax', settings.lsmax),
    )
    within_voltage_window: Expr = (
        (terminal_voltage > model.parameter('Pss2ST.vcl', settings.vcl)).to_expression()
        * (terminal_voltage < model.parameter('Pss2ST.vcu', settings.vcu)).to_expression()
    )
    output: Var = model.algebraic('VsPu', within_voltage_window * limited_output, Const(0.0))
    template: RmsModelTemplate = model.finish((output,), 'CGMES Pss2ST dual-input stabilizer')
    template.comment = 'CGMES Pss2ST EA1313 dual input, washout, three lead-lags, output limiter and Vct gate.'
    parameter_values: tuple[tuple[str, object], ...] = (
        ('inputSignal1Type', settings.input_signal1_type),
        ('inputSignal2Type', settings.input_signal2_type),
        ('k1', settings.k1), ('k2', settings.k2), ('t1', settings.t1),
        ('t2', settings.t2), ('t3', settings.t3), ('t4', settings.t4),
        ('t5', settings.t5), ('t6', settings.t6), ('t7', settings.t7),
        ('t8', settings.t8), ('t9', settings.t9), ('t10', settings.t10),
        ('lsmax', settings.lsmax), ('lsmin', settings.lsmin),
        ('vcu', settings.vcu), ('vcl', settings.vcl), ('enabled', None),
    )
    for parameter_name, parameter_value in parameter_values:
        parameter_variable_name: str = f'Pss2ST.{parameter_name}_{template_name}'
        parameter_exists: bool = any(
            event_variable.name == parameter_variable_name
            for event_variable in template.block.event_dict
        )
        if not parameter_exists:
            parameter_variable: Var = vfactory.add_var(parameter_variable_name)
            template.block.event_dict[parameter_variable] = vfactory.add_const(value=parameter_value)
        else:
            pass
    return template
