# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native IEEE ST6B static potential-source excitation system."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_st6b_template(vf: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the four-state ST6B regulator and field-current limiting path.

    The derivative channel is the IEEE filtered PD realization. ``VB`` remains
    a host input so the PSS/E adapter can select its reviewed terminal-supply
    path; independent-source attachment is not inferred from the DYR record.

    :param vf: Shared symbolic variable factory.
    :param name: Optional instance name.
    :return: Native ST6B controller with seven inputs and one field output.
    """
    label: str = 'St6b' if name is None else name
    control: ControlRealization = ControlRealization(vf, label)

    # Declare source parameters before using them in the physical equations.
    transducer_time: Var = control.parameter('avr.tR', 0.02)
    proportional_gain: Var = control.parameter('avr.Kpa', 1.0)
    integral_gain: Var = control.parameter('avr.Kia', 10.0)
    derivative_gain: Var = control.parameter('avr.Kda', 0.0)
    derivative_time: Var = control.parameter('avr.tDa', 1.0)
    regulator_maximum: Var = control.parameter('avr.VaMaxPu', 5.0)
    regulator_minimum: Var = control.parameter('avr.VaMinPu', -5.0)
    feedforward_gain: Var = control.parameter('avr.Kff', 0.0)
    forward_gain: Var = control.parameter('avr.Km', 1.0)
    current_adjustment: Var = control.parameter('avr.Kcl', 1.0)
    current_limit_gain: Var = control.parameter('avr.Klr', 17.0)
    current_limit_reference: Var = control.parameter('avr.IlrPu', 1.1)
    field_maximum: Var = control.parameter('avr.VrMaxPu', 5.0)
    field_minimum: Var = control.parameter('avr.VrMinPu', -5.0)
    feedback_gain: Var = control.parameter('avr.Kg', 1.0)
    feedback_time: Var = control.parameter('avr.tG', 0.02)
    initial_field: Var = control.parameter('avr.Efd0Pu', 1.0)
    initial_current: Var = control.parameter('avr.Ir0Pu', 1.0)
    initial_voltage: Var = control.parameter('avr.Us0Pu', 1.0)

    # Inputs follow the stable source-model interface used by the DYR adapter.
    field_current: Var = control.input('avr.IrPu', initial_current)
    overexcitation: Var = control.input('avr.UOelPu', Const(0.0))
    stabilizer: Var = control.input('avr.UPssPu', Const(0.0))
    terminal_voltage: Var = control.input('avr.UsPu', initial_voltage)
    reference_voltage: Var = control.input('avr.UsRefPu', initial_voltage)
    underexcitation: Var = control.input('avr.UUelPu', Const(0.0))
    available_supply: Var = control.input('avr.VbPu', initial_voltage)

    # Terminal voltage transduction and the reference summing point set the loop error.
    measured_voltage: Var = control.lag(
        'MeasuredVoltagePu', terminal_voltage, transducer_time, 0.02, initial_voltage,
    )
    error: Expr = reference_voltage + overexcitation + stabilizer + underexcitation - measured_voltage

    # Seed the field-voltage feedforward at the power-flow operating point.
    voltage_regulator_initial: Expr = sym.safe_divide(
        sym.safe_divide(initial_field, available_supply, 1.0)
        + forward_gain * feedback_gain * initial_field,
        forward_gain + feedforward_gain,
        1.0,
    )
    integral_initial: Expr = sym.safe_divide(
        voltage_regulator_initial - proportional_gain * error,
        integral_gain,
        1.0,
    )
    integral_state: Var = vf.add_var('avr.IntegralChannel_' + label)
    pi_unbounded: Expr = proportional_gain * error + integral_gain * integral_state
    integral_rate: Expr = error * sym.heaviside(pi_unbounded - regulator_minimum - Const(1e-6)) * sym.heaviside(regulator_maximum - pi_unbounded - Const(1e-6))
    control.differential(integral_state, integral_rate, integral_initial)
    pi_output: Var = control.algebraic(
        'PiOutputPu', sym.hard_sat(pi_unbounded, regulator_minimum, regulator_maximum),
        voltage_regulator_initial,
    )

    # The IEEE derivative block is a high-pass memory, not a numerical derivative.
    derivative_state: Var = vf.add_var('avr.DerivativeChannel_' + label)
    derivative_state_initial: Expr = -sym.safe_divide(derivative_gain * error, derivative_time, 1.0)
    control.differential(
        derivative_state,
        (-sym.safe_divide(derivative_gain * error, derivative_time, 1.0) - derivative_state) / derivative_time,
        derivative_state_initial,
    )
    derivative_output: Var = control.algebraic(
        'DerivativeOutputPu', derivative_state + sym.safe_divide(derivative_gain * error, derivative_time, 1.0),
        Const(0.0),
    )
    regulator_output: Var = control.algebraic(
        'RegulatorOutputPu', pi_output + derivative_output, voltage_regulator_initial,
    )

    # The KG/TG lag feeds back field voltage into the inner forward regulator.
    feedback_initial: Expr = feedback_gain * initial_field
    feedback: Var = vf.add_var('FieldFeedbackPu_' + label)
    feedforward: Expr = (
        forward_gain * (regulator_output - feedback)
        + feedforward_gain * regulator_output
    )
    voltage_limited: Expr = sym.hard_sat(feedforward, field_minimum, field_maximum)
    current_limited: Expr = sym.max(
        (current_limit_reference * current_adjustment - field_current) * current_limit_gain,
        field_minimum,
    )
    field_regulator: Var = control.algebraic(
        'FieldRegulatorPu', sym.min(voltage_limited, current_limited),
        sym.safe_divide(initial_field, available_supply, 1.0),
    )
    field_voltage: Var = control.algebraic(
        'EfdPu', available_supply * field_regulator, initial_field,
    )
    control.differential(
        feedback,
        (feedback_gain * field_voltage - feedback) / feedback_time,
        feedback_initial,
    )
    control.block.init_eqs[reference_voltage] = initial_voltage
    control.block.init_eqs[feedback] = feedback_initial
    return control.finish((field_voltage,), 'IEEE ST6B four-state static potential-source exciter')
