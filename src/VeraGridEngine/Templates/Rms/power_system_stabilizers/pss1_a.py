# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES Pss1A model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import InputSignalKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import (
    polynomial_measurement_filter,
)
from VeraGridEngine.Utils.procedural_logic import delay
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Pss1AParameters:
    """Canonical Pss1A scalar settings used by its sourced equation graph."""

    __slots__ = (
        'input_signal_type', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8',
        't1', 't2', 't3', 't4', 't5', 't6', 'ks', 'vrmax', 'vrmin', 'vcu',
        'vcl', 'kd', 'tdelay',
    )

    def __init__(
            self,
            input_signal_type: InputSignalKind | None = None,
            a1: float = 0.0,
            a2: float = 0.0,
            a3: float = 0.0,
            a4: float = 0.0,
            a5: float = 0.0,
            a6: float = 0.0,
            a7: float = 0.0,
            a8: float = 0.0,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.0,
            t4: float = 0.0,
            t5: float = 0.0,
            t6: float = 0.0,
            ks: float = 0.0,
            vrmax: float = 0.0,
            vrmin: float = 0.0,
            vcu: float = 0.0,
            vcl: float = 0.0,
            kd: bool = False,
            tdelay: float = 0.0,
    ) -> None:
        """Store Pss1A's RDF fields without changing their declared meaning.

        :param input_signal_type: CGMES selector for the first stabilizer input.
        :param a1: First low-frequency filter denominator coefficient.
        :param a2: Second low-frequency filter denominator coefficient.
        :param a3: First input filter denominator coefficient.
        :param a4: Second input filter denominator coefficient.
        :param a5: First input filter numerator coefficient.
        :param a6: Second input filter numerator coefficient.
        :param a7: First input filter denominator coefficient after its numerator.
        :param a8: Second input filter denominator coefficient after its numerator.
        :param t1: First phase lead time in seconds.
        :param t2: First phase lag time in seconds.
        :param t3: Second phase lead time in seconds.
        :param t4: Second phase lag time in seconds.
        :param t5: Washout time in seconds.
        :param t6: Input transducer time in seconds.
        :param ks: Stabilizer gain.
        :param vrmax: Upper stabilizer output limit.
        :param vrmin: Lower stabilizer output limit.
        :param vcu: Upper compensating-voltage cutoff.
        :param vcl: Lower compensating-voltage cutoff.
        :param kd: Select whether the transport delay is active.
        :param tdelay: Transport delay in seconds.
        """
        self.input_signal_type: InputSignalKind | None = input_signal_type
        self.a1: float = a1
        self.a2: float = a2
        self.a3: float = a3
        self.a4: float = a4
        self.a5: float = a5
        self.a6: float = a6
        self.a7: float = a7
        self.a8: float = a8
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t5: float = t5
        self.t6: float = t6
        self.ks: float = ks
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.vcu: float = vcu
        self.vcl: float = vcl
        self.kd: bool = kd
        self.tdelay: float = tdelay


def build_pss1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: Pss1AParameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1309 input, filter, delay, and output-gate realization.

    :param vfactory: Factory allocating the equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES scalar fields and input selector.
    :return: Pss1A block with selected-signal and terminal-voltage ports.
    :raises ValueError: Invalid coefficients, times, or output/cutoff limits.
    """
    settings: Pss1AParameters = Pss1AParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.a1, settings.a2, settings.a3, settings.a4, settings.a5,
        settings.a6, settings.a7, settings.a8, settings.t1, settings.t2,
        settings.t3, settings.t4, settings.t5, settings.t6, settings.ks,
        settings.vrmax, settings.vrmin, settings.vcu, settings.vcl, settings.tdelay,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES Pss1A parameters must be finite')
    elif min(settings.a1, settings.a2, settings.a3, settings.a4,
             settings.a7, settings.a8) < 0.0:
        raise ValueError('CGMES Pss1A filter denominator coefficients must be nonnegative')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4,
             settings.t5, settings.t6, settings.tdelay) < 0.0:
        raise ValueError('CGMES Pss1A time constants must be nonnegative')
    elif settings.vrmin > settings.vrmax or settings.vcl > settings.vcu:
        raise ValueError('CGMES Pss1A output or cutoff limits are invalid')
    else:
        pass

    template_name: str = 'Pss1A' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    selected_signal: Var = model.input('SignalPu', Const(0.0))
    terminal_voltage: Var = model.input('VctPu', Const(1.0))
    input_filter: Var = polynomial_measurement_filter(
        model,
        selected_signal,
        (settings.a3, settings.a4, 0.0, 0.0, settings.a5, settings.a6),
        'InputFilter',
    )
    secondary_filter: Var = polynomial_measurement_filter(
        model,
        input_filter,
        (settings.a7, settings.a8, 0.0, 0.0, settings.a5, settings.a6),
        'SecondaryFilter',
    )
    transducer: Var = model.lag(
        'TransducerPu', secondary_filter,
        model.parameter('Pss1A.t6', settings.t6), settings.t6, secondary_filter,
    )
    washout_time: Var = model.parameter('Pss1A.t5', settings.t5)
    if settings.t5 > 0.0:
        washed_signal: Var = model.washout(
            'WashoutPu', transducer, washout_time, settings.t5,
            model.parameter('Pss1A.ks', settings.ks), transducer,
        )
    else:
        washed_signal = model.algebraic('WashoutPu', Const(0.0), Const(0.0))

    final_filter: Var = polynomial_measurement_filter(
        model,
        washed_signal,
        (settings.a1, settings.a2, 0.0, 0.0, 0.0, 0.0),
        'FinalFilter',
    )
    delay_time: Var = model.parameter('Pss1A.tdelay', settings.tdelay)
    if settings.kd and settings.tdelay > 0.0:
        # The source selector enables a true transport delay; runtime history is exact.
        delayed_signal: Var = vfactory.add_var(f'DelayedSignalPu_{template_name}')
        model.block.mode_dict[delayed_signal] = Const(0.0)
        model.block.init_eqs[delayed_signal] = final_filter
        model.block.procedural_logic.append(
            delay(
                final_filter,
                delay_time,
                delayed_signal,
                name=f'Pss1A.Delay_{template_name}',
            )
        )
    else:
        delayed_signal = final_filter

    first_phase: Var = model.lead_lag(
        'FirstPhasePu', delayed_signal,
        model.parameter('Pss1A.t1', settings.t1),
        model.parameter('Pss1A.t2', settings.t2),
        settings.t1, settings.t2, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase,
        model.parameter('Pss1A.t3', settings.t3),
        model.parameter('Pss1A.t4', settings.t4),
        settings.t3, settings.t4, Const(0.0),
    )
    lower_limit: Var = model.parameter('Pss1A.vrmin', settings.vrmin)
    upper_limit: Var = model.parameter('Pss1A.vrmax', settings.vrmax)
    lower_cutoff: Var = model.parameter('Pss1A.vcl', settings.vcl)
    upper_cutoff: Var = model.parameter('Pss1A.vcu', settings.vcu)
    within_voltage_window: Expr = (
        (terminal_voltage > lower_cutoff).to_expression()
        * (terminal_voltage < upper_cutoff).to_expression()
    )
    output: Var = model.algebraic(
        'VsPu',
        within_voltage_window * sym.hard_sat(second_phase, lower_limit, upper_limit),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES Pss1A single-input stabilizer')
    template.comment = 'CGMES Pss1A EA1309 quadratic filters, optional transport delay, and Vct cutoff.'
    # The shared quadratic helper names internal coefficients by stage; these RDF aliases
    # preserve the canonical schema surface on the exported CGMES runtime block.
    rdf_parameters: tuple[tuple[str, float | bool | None], ...] = (
        ('a1', settings.a1), ('a2', settings.a2),
        ('a3', settings.a3), ('a4', settings.a4),
        ('a5', settings.a5), ('a6', settings.a6),
        ('a7', settings.a7), ('a8', settings.a8),
        ('enabled', None), ('inputSignalType', None), ('kd', settings.kd),
    )
    for parameter_name, parameter_value in rdf_parameters:
        parameter: Var = vfactory.add_var(f'Pss1A.{parameter_name}_{template_name}')
        template.block.event_dict[parameter] = vfactory.add_const(value=parameter_value)
    return template
