# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for canonical CGMES PssPTIST1."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_pti_tap_selection import (
    build_pti_tap_selection_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import PeriodicSampleLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class PssPTIST1Parameters:
    """Canonical PssPTIST1 settings from the RDF dynamic profile."""

    __slots__ = ('m', 'tf', 'tp', 't1', 't2', 't3', 't4', 'k', 'dtf', 'dtc', 'dtp')

    def __init__(
            self,
            m: float = 0.0,
            tf: float = 0.0,
            tp: float = 0.0,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.0,
            t4: float = 0.0,
            k: float = 0.0,
            dtf: float = 0.0,
            dtc: float = 0.0,
            dtp: float = 0.0,
    ) -> None:
        """Store all RDF parameters, including discrete implementation steps.

        :param m: Speed washout gain.
        :param tf: Speed washout time constant in seconds.
        :param tp: Electrical-power filter time constant in seconds.
        :param t1: First lead time constant in seconds.
        :param t2: First lag time constant in seconds.
        :param t3: Second lead time constant in seconds.
        :param t4: Second lag time constant in seconds.
        :param k: Stabilizer gain.
        :param dtf: Speed washout discrete time step in seconds.
        :param dtc: Controller discrete time step in seconds.
        :param dtp: Power filter discrete time step in seconds.
        """
        self.m: float = m
        self.tf: float = tf
        self.tp: float = tp
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.k: float = k
        self.dtf: float = dtf
        self.dtc: float = dtc
        self.dtp: float = dtp


def build_pss_p_t_i_s_t1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssPTIST1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the continuous-time EA1319 graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES PssPTIST1 fields.
    :return: Equation-backed graph with an explicit tap-table output input.
    :raises ValueError: Nonfinite values, negative times, or improper lead-lag stages.
    """
    settings: PssPTIST1Parameters = PssPTIST1Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.m, settings.tf, settings.tp, settings.t1, settings.t2,
        settings.t3, settings.t4, settings.k, settings.dtf, settings.dtc, settings.dtp,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES PssPTIST1 parameters must be finite')
    elif min(settings.tf, settings.tp, settings.t1, settings.t2, settings.t3,
             settings.t4, settings.dtf, settings.dtc, settings.dtp) < 0.0:
        raise ValueError('CGMES PssPTIST1 time constants and steps must be nonnegative')
    elif ((settings.t2 == 0.0 and settings.t1 > 0.0)
          or (settings.t4 == 0.0 and settings.t3 > 0.0)):
        raise ValueError('CGMES PssPTIST1 lead time requires a nonzero lag time')
    else:
        pass

    template_name: str = 'PssPTIST1' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    speed_deviation: Var = model.input('OmegaPu', Const(0.0))
    electrical_power: Var = model.input('PePu', Const(0.0))
    terminal_voltage: Var = model.input('VtPu', Const(1.0))
    sampled_speed: Var = speed_deviation
    if settings.dtf > 0.0:
        sampled_speed = vfactory.add_var(f'SampledOmegaPu_{template_name}')
        model.block.mode_dict[sampled_speed] = Const(0.0)
        model.block.init_eqs[sampled_speed] = Const(0.0)
        model.block.procedural_logic.append(PeriodicSampleLogic(
            output_var_name=sampled_speed.name,
            output_var_uid=sampled_speed.uid,
            source_expr=speed_deviation,
            sample_period=settings.dtf,
            name=f'PssPTIST1.SpeedSample_{template_name}',
        ))
    else:
        pass
    sampled_power: Var = electrical_power
    if settings.dtp > 0.0:
        sampled_power = vfactory.add_var(f'SampledPePu_{template_name}')
        model.block.mode_dict[sampled_power] = Const(0.0)
        model.block.init_eqs[sampled_power] = electrical_power
        model.block.procedural_logic.append(PeriodicSampleLogic(
            output_var_name=sampled_power.name,
            output_var_uid=sampled_power.uid,
            source_expr=electrical_power,
            sample_period=settings.dtp,
            name=f'PssPTIST1.PowerSample_{template_name}',
        ))
    else:
        pass
    if settings.tf > 0.0:
        speed_path: Var = model.washout(
            'SpeedWashoutPu', sampled_speed,
            model.parameter('PssPTIST1.tf', settings.tf), settings.tf,
            model.parameter('PssPTIST1.m', settings.m), sampled_speed,
        )
    else:
        speed_path = model.algebraic('SpeedWashoutPu', Const(0.0), Const(0.0))
    measured_power: Var = model.lag(
        'MeasuredPowerPu', sampled_power,
        model.parameter('PssPTIST1.tp', settings.tp), settings.tp, electrical_power,
    )
    first_sum: Var = model.algebraic('SpeedAndPowerPu', speed_path + measured_power, electrical_power)
    power_difference: Var = model.algebraic(
        'PowerDifferencePu', first_sum - electrical_power, Const(0.0),
    )
    first_phase: Var = model.lead_lag(
        'FirstPhasePu', power_difference * model.parameter('PssPTIST1.k', settings.k),
        model.parameter('PssPTIST1.t1', settings.t1),
        model.parameter('PssPTIST1.t2', settings.t2), settings.t1, settings.t2, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase,
        model.parameter('PssPTIST1.t3', settings.t3),
        model.parameter('PssPTIST1.t4', settings.t4), settings.t3, settings.t4, Const(0.0),
    )
    tap_table_signal: Var = model.algebraic(
        'TapTableInputPu', second_phase, Const(0.0),
    )
    tap_table_output: Var = model.algebraic(
        'TapSelectionPu',
        build_pti_tap_selection_expression(tap_table_signal),
        Const(0.0),
    )
    controller_signal: Var = tap_table_output
    if settings.dtc > 0.0:
        controller_signal = vfactory.add_var(f'SampledControllerPu_{template_name}')
        model.block.mode_dict[controller_signal] = Const(0.0)
        model.block.init_eqs[controller_signal] = tap_table_output
        model.block.procedural_logic.append(sampled_value(
            output=controller_signal,
            source=tap_table_output,
            name=f'PssPTIST1.ControllerSample_{template_name}',
            sample_period=settings.dtc,
        ))
    else:
        pass
    tap_sum: Var = model.algebraic(
        'TapAdjustedPu', Const(1.0) + controller_signal, Const(1.0),
    )
    output: Var = model.algebraic('VsPu', terminal_voltage * tap_sum, Const(1.0))
    template: RmsModelTemplate = model.finish(
        (output, tap_table_signal), 'CGMES PssPTIST1 sampled stabilizer',
    )
    template.comment = (
        'CGMES PssPTIST1 continuous filters with the IEC 61970-302 Figure 150 tap-selection table. '
        'Positive dtf samples speed, dtp samples active power, and dtc samples the stabilizer '
        'controller path on exact solver boundaries; zero values retain continuous input.'
    )
    parameter_values: tuple[tuple[str, object], ...] = (
        ('m', settings.m), ('tf', settings.tf), ('tp', settings.tp),
        ('t1', settings.t1), ('t2', settings.t2), ('t3', settings.t3),
        ('t4', settings.t4), ('k', settings.k), ('dtf', settings.dtf),
        ('dtc', settings.dtc), ('dtp', settings.dtp), ('enabled', None),
    )
    for parameter_name, parameter_value in parameter_values:
        parameter_variable_name: str = f'PssPTIST1.{parameter_name}_{template_name}'
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
