# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES Pss2B model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import InputSignalKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Pss2BParameters:
    """Canonical CGMES Pss2B parameters and selected input signals."""

    __slots__ = (
        'input_signal1_type', 'input_signal2_type', 'vsi1max', 'vsi1min',
        'tw1', 'tw2', 'vsi2max', 'vsi2min', 'tw3', 'tw4', 't1', 't2',
        't3', 't4', 't6', 't7', 't8', 't9', 't10', 't11', 'ks1', 'ks2',
        'ks3', 'ks4', 'n', 'm', 'vstmax', 'vstmin', 'a', 'ta', 'tb',
    )

    def __init__(
            self,
            input_signal1_type: InputSignalKind | None = InputSignalKind.rotorSpeed,
            input_signal2_type: InputSignalKind | None = InputSignalKind.generatorElectricalPower,
            vsi1max: float = 2.0,
            vsi1min: float = -2.0,
            tw1: float = 2.0,
            tw2: float = 2.0,
            vsi2max: float = 2.0,
            vsi2min: float = -2.0,
            tw3: float = 2.0,
            tw4: float = 0.0,
            t1: float = 0.12,
            t2: float = 0.02,
            t3: float = 0.3,
            t4: float = 0.02,
            t6: float = 0.0,
            t7: float = 2.0,
            t8: float = 0.2,
            t9: float = 0.1,
            t10: float = 0.0,
            t11: float = 0.0,
            ks1: float = 12.0,
            ks2: float = 0.2,
            ks3: float = 1.0,
            ks4: float = 1.0,
            n: int = 1,
            m: int = 5,
            vstmax: float = 0.1,
            vstmin: float = -0.1,
            a: float = 1.0,
            ta: float = 0.0,
            tb: float = 0.0,
    ) -> None:
        """Store CGMES profile values using the canonical property names.

        :param input_signal1_type: RDF selector for the first measurement.
        :param input_signal2_type: RDF selector for the second measurement.
        :param vsi1max: First input upper limit in per unit.
        :param vsi1min: First input lower limit in per unit.
        :param tw1: First signal's first washout time in seconds.
        :param tw2: First signal's second washout time in seconds.
        :param vsi2max: Second input upper limit in per unit.
        :param vsi2min: Second input lower limit in per unit.
        :param tw3: Second signal's first washout time in seconds.
        :param tw4: Second signal's second washout time in seconds.
        :param t1: First phase numerator time in seconds.
        :param t2: First phase denominator time in seconds.
        :param t3: Second phase numerator time in seconds.
        :param t4: Second phase denominator time in seconds.
        :param t6: First signal transducer time in seconds.
        :param t7: Second signal transducer time in seconds.
        :param t8: Ramp tracking numerator time in seconds.
        :param t9: Ramp tracking denominator time in seconds.
        :param t10: Third phase numerator time in seconds.
        :param t11: Third phase denominator time in seconds.
        :param ks1: Stabilizer output gain.
        :param ks2: Second input gain.
        :param ks3: Second input gain before ramp tracking.
        :param ks4: Second input gain after ramp tracking.
        :param n: Number of repeated ramp tracking stages.
        :param m: Denominator order in each ramp tracking stage.
        :param vstmax: Output upper limit in per unit.
        :param vstmin: Output lower limit in per unit.
        :param a: Final numerator constant.
        :param ta: Final numerator time in seconds.
        :param tb: Final denominator time in seconds.
        """
        self.input_signal1_type: InputSignalKind | None = input_signal1_type
        self.input_signal2_type: InputSignalKind | None = input_signal2_type
        self.vsi1max: float = vsi1max
        self.vsi1min: float = vsi1min
        self.tw1: float = tw1
        self.tw2: float = tw2
        self.vsi2max: float = vsi2max
        self.vsi2min: float = vsi2min
        self.tw3: float = tw3
        self.tw4: float = tw4
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t6: float = t6
        self.t7: float = t7
        self.t8: float = t8
        self.t9: float = t9
        self.t10: float = t10
        self.t11: float = t11
        self.ks1: float = ks1
        self.ks2: float = ks2
        self.ks3: float = ks3
        self.ks4: float = ks4
        self.n: int = n
        self.m: int = m
        self.vstmax: float = vstmax
        self.vstmin: float = vstmin
        self.a: float = a
        self.ta: float = ta
        self.tb: float = tb


def build_pss2_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: Pss2BParameters | None = None,
) -> RmsModelTemplate:
    """Build the sourced, selected-signal CGMES Pss2B realization.

    :param vfactory: Factory allocating model and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed scalar fields and input selectors.
    :return: Equation-backed PSS with two selected measurement ports.
    :raises ValueError: Invalid times, orders, or limiter bounds.
    """
    settings: Pss2BParameters = Pss2BParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.vsi1max, settings.vsi1min, settings.tw1, settings.tw2,
        settings.vsi2max, settings.vsi2min, settings.tw3, settings.tw4,
        settings.t1, settings.t2, settings.t3, settings.t4, settings.t6,
        settings.t7, settings.t8, settings.t9, settings.t10, settings.t11,
        settings.ks1, settings.ks2, settings.ks3, settings.ks4, settings.vstmax,
        settings.vstmin, settings.a, settings.ta, settings.tb,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES Pss2B parameters must be finite')
    elif min(settings.tw1, settings.tw2, settings.tw3, settings.tw4, settings.t6,
             settings.t7, settings.t8, settings.t9, settings.t1, settings.t2,
             settings.t3, settings.t4, settings.t10, settings.t11, settings.ta,
             settings.tb) < 0.0:
        raise ValueError('CGMES Pss2B times must be nonnegative')
    elif not isinstance(settings.n, int) or not isinstance(settings.m, int) or min(settings.n, settings.m) < 0:
        raise ValueError('CGMES Pss2B ramp orders must be nonnegative integers')
    elif settings.n * settings.m > 8:
        raise ValueError('CGMES Pss2B ramp tracking order exceeds the supported state count')
    elif settings.t9 == 0.0 and settings.n * settings.m > 0:
        raise ValueError('CGMES Pss2B ramp denominator time must be positive')
    elif settings.tb == 0.0 and settings.ta != 0.0:
        raise ValueError('CGMES Pss2B final rate block requires a nonzero denominator time')
    elif settings.vsi1min >= settings.vsi1max or settings.vsi2min >= settings.vsi2max or settings.vstmin >= settings.vstmax:
        raise ValueError('CGMES Pss2B limiter bounds must be ordered')
    else:
        pass

    template_name: str = 'Pss2B' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    signal1: Var = model.input('Signal1Pu', Const(0.0))
    signal2: Var = model.input('Signal2Pu', Const(0.0))
    clipped1: Var = model.algebraic(
        'ClippedSignal1Pu',
        sym.hard_sat(signal1, model.parameter('Pss2B.vsi1min', settings.vsi1min),
                     model.parameter('Pss2B.vsi1max', settings.vsi1max)),
        Const(0.0),
    )
    clipped2: Var = model.algebraic(
        'ClippedSignal2Pu',
        sym.hard_sat(signal2, model.parameter('Pss2B.vsi2min', settings.vsi2min),
                     model.parameter('Pss2B.vsi2max', settings.vsi2max)),
        Const(0.0),
    )
    if settings.tw1 > 0.0:
        washed1: Var = model.washout(
            'Washout1Pu', clipped1, model.parameter('Pss2B.tw1', settings.tw1),
            settings.tw1, Const(1.0), clipped1,
        )
    else:
        washed1 = model.algebraic('Washout1Pu', Const(0.0), Const(0.0))
    if settings.tw1 > 0.0 and settings.tw2 > 0.0:
        washed1 = model.washout(
            'Washout2Pu', washed1, model.parameter('Pss2B.tw2', settings.tw2),
            settings.tw2, Const(1.0), Const(0.0),
        )
    else:
        pass
    if settings.tw3 > 0.0:
        washed2: Var = model.washout(
            'Washout3Pu', clipped2, model.parameter('Pss2B.tw3', settings.tw3),
            settings.tw3, Const(1.0), clipped2,
        )
    else:
        washed2 = model.algebraic('Washout3Pu', Const(0.0), Const(0.0))
    if settings.tw3 > 0.0 and settings.tw4 > 0.0:
        washed2 = model.washout(
            'Washout4Pu', washed2, model.parameter('Pss2B.tw4', settings.tw4),
            settings.tw4, Const(1.0), Const(0.0),
        )
    else:
        pass
    measured1: Var = model.lag(
        'Transducer1Pu', washed1, model.parameter('Pss2B.t6', settings.t6),
        settings.t6, Const(0.0),
    )
    measured2: Var = model.lag(
        'Transducer2Pu', model.parameter('Pss2B.ks2', settings.ks2) * washed2,
        model.parameter('Pss2B.t7', settings.t7), settings.t7, Const(0.0),
    )
    tracked: Var = model.algebraic(
        'RampInputPu', measured1 + model.parameter('Pss2B.ks3', settings.ks3) * measured2,
        Const(0.0),
    )
    t8_parameter: Var = model.parameter('Pss2B.t8', settings.t8)
    t9_parameter: Var = model.parameter('Pss2B.t9', settings.t9)
    ramp_index: int
    pole_index: int
    for ramp_index in range(0 if settings.m == 0 else settings.n):
        tracked = model.lead_lag(
            f'Ramp{ramp_index + 1}LeadPu', tracked,
            t8_parameter,
            t9_parameter, settings.t8,
            settings.t9, Const(0.0),
        )
        for pole_index in range(settings.m - 1):
            tracked = model.lag(
                f'Ramp{ramp_index + 1}Lag{pole_index + 1}Pu', tracked,
                t9_parameter, settings.t9, Const(0.0),
            )
    post_ramp: Expr = model.parameter('Pss2B.ks1', settings.ks1) * (
        tracked - model.parameter('Pss2B.ks4', settings.ks4) * measured2
    )
    phase1: Var = model.lead_lag(
        'Phase1Pu', post_ramp, model.parameter('Pss2B.t1', settings.t1),
        model.parameter('Pss2B.t2', settings.t2), settings.t1, settings.t2, Const(0.0),
    )
    phase2: Var = model.lead_lag(
        'Phase2Pu', phase1, model.parameter('Pss2B.t3', settings.t3),
        model.parameter('Pss2B.t4', settings.t4), settings.t3, settings.t4, Const(0.0),
    )
    phase3: Var = model.lead_lag(
        'Phase3Pu', phase2, model.parameter('Pss2B.t10', settings.t10),
        model.parameter('Pss2B.t11', settings.t11), settings.t10, settings.t11, Const(0.0),
    )
    if settings.tb > 0.0:
        final_memory: Var = model.lag(
            'FinalFilterMemoryPu', phase3,
            model.parameter('Pss2B.tb', settings.tb), settings.tb, Const(0.0),
        )
        final_output: Expr = (
            model.parameter('Pss2B.a', settings.a) * final_memory
            + model.parameter('Pss2B.ta', settings.ta) / model.parameter('Pss2B.tb', settings.tb)
            * (phase3 - final_memory)
        )
    else:
        final_output = model.parameter('Pss2B.a', settings.a) * phase3
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(
            final_output,
            model.parameter('Pss2B.vstmin', settings.vstmin),
            model.parameter('Pss2B.vstmax', settings.vstmax),
        ),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES Pss2B modified dual-input stabilizer')
    template.comment = 'CGMES Pss2B EA1311 selected inputs, KS4 path, four final phase/rate blocks, and output limits.'
    parameter_values: tuple[tuple[str, object], ...] = (
        ('inputSignal1Type', settings.input_signal1_type),
        ('inputSignal2Type', settings.input_signal2_type),
        ('vsi1max', settings.vsi1max), ('vsi1min', settings.vsi1min),
        ('tw1', settings.tw1), ('tw2', settings.tw2),
        ('vsi2max', settings.vsi2max), ('vsi2min', settings.vsi2min),
        ('tw3', settings.tw3), ('tw4', settings.tw4),
        ('t1', settings.t1), ('t2', settings.t2), ('t3', settings.t3),
        ('t4', settings.t4), ('t6', settings.t6), ('t7', settings.t7),
        ('t8', settings.t8), ('t9', settings.t9), ('t10', settings.t10),
        ('t11', settings.t11), ('ks1', settings.ks1), ('ks2', settings.ks2),
        ('ks3', settings.ks3), ('ks4', settings.ks4),
        ('n', settings.n), ('m', settings.m),
        ('vstmax', settings.vstmax), ('vstmin', settings.vstmin),
        ('a', settings.a), ('ta', settings.ta), ('tb', settings.tb),
        ('enabled', None),
    )
    for parameter_name, parameter_value in parameter_values:
        parameter_variable_name: str = f'Pss2B.{parameter_name}_{template_name}'
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
