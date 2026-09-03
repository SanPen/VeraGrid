# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import math

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.rms_meter_templates import (
    build_rms_current_meter_outputs_from_pq,
    build_rms_physical_signal_meter_block,
    build_rms_power_meter_outputs_from_pq,
    build_rms_voltage_meter_outputs_from_polar,
)
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    RmsPhysicalMeasurementPoint,
    validate_dynamic_model_contract,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.enumerations import RmsPhysicalMeterKind, RmsTerminalSide


def test_veragrid_physical_meter_can_be_created_without_import() -> None:
    """Build the canonical measurement contract without a source parser.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    active_power: Var = var_factory.add_var("native_active_power")
    reactive_power: Var = var_factory.add_var("native_reactive_power")
    signal_expressions: dict[str, Expr] = dict()
    signal_expressions["external_active_alias"] = active_power
    signal_expressions["external_reactive_alias"] = reactive_power
    meter_block: Block
    output_by_alias_name: dict[str, Var]
    meter_block, output_by_alias_name = build_rms_physical_signal_meter_block(
        vf=var_factory,
        signal_expressions=signal_expressions,
        output_signal_names=("active_power", "reactive_power"),
        name="VeraGrid Power meter native",
        source_fid="native-power-meter",
        target_fid="native-device",
        terminal_side=RmsTerminalSide.FROM,
        meter_kind=RmsPhysicalMeterKind.POWER,
        symbol_suffix="VeraGrid Power meter native",
    )
    validate_dynamic_model_contract(block=meter_block)
    measurement_point: RmsPhysicalMeasurementPoint | None = (
        meter_block.dynamic_model_contract.rms_physical_measurement_point
    )
    assert measurement_point is not None
    assert measurement_point.get_meter_kind() is RmsPhysicalMeterKind.POWER
    assert measurement_point.get_output_signal_names() == tuple(
        output_var.name for output_var in meter_block.out_vars
    )
    assert len(meter_block.out_vars) == 2
    assert len(meter_block.algebraic_vars) == 2
    assert len(meter_block.algebraic_eqs) == 2
    assert len(meter_block.init_eqs) == 2
    assert meter_block.name == "VeraGrid Power meter native"
    assert all(output_var.name.isidentifier() for output_var in meter_block.out_vars)
    assert all(" " not in output_var.name for output_var in meter_block.out_vars)
    alias_name: str
    source_expression: Expr
    for alias_name, source_expression in signal_expressions.items():
        output_var: Var = output_by_alias_name[alias_name]
        assert meter_block.init_eqs[output_var] is source_expression
        residuals_with_output: list[Expr] = list(
            residual
            for residual in meter_block.algebraic_eqs
            if output_var.uid in set(
                residual_var.uid for residual_var in residual.get_vars()
            )
        )
        assert len(residuals_with_output) == 1


def test_veragrid_rms_meter_equations_match_phasor_definitions() -> None:
    """Evaluate native voltage, current and power measurement equations.

    :return: None.
    """
    voltage_magnitude: Var = Var("meter_vm")
    voltage_angle: Var = Var("meter_va")
    active_power: Var = Var("meter_p")
    reactive_power: Var = Var("meter_q")
    measured_frequency: Var = Var("meter_frequency")
    nominal_frequency: Var = Var("meter_nominal_frequency")
    voltage_outputs: dict[str, Expr] = build_rms_voltage_meter_outputs_from_polar(
        vm=voltage_magnitude,
        va=voltage_angle,
        measured_frequency_hz=measured_frequency,
        nominal_frequency_hz=nominal_frequency,
    )
    current_outputs: dict[str, Expr] = build_rms_current_meter_outputs_from_pq(
        vm=voltage_magnitude,
        va=voltage_angle,
        p=active_power,
        q=reactive_power,
    )
    power_outputs: dict[str, Expr] = build_rms_power_meter_outputs_from_pq(
        p=active_power,
        q=reactive_power,
    )
    voltage_real: float = 2.0 * math.cos(math.pi / 6.0)
    voltage_imaginary: float = 2.0 * math.sin(math.pi / 6.0)
    current_denominator: float = 4.0 + 1.0e-9
    expected_current_real: float = (
        (3.0 * voltage_real) + (4.0 * voltage_imaginary)
    ) / current_denominator
    expected_current_imaginary: float = (
        (3.0 * voltage_imaginary) - (4.0 * voltage_real)
    ) / current_denominator
    assert math.isclose(
        voltage_outputs["ur"].eval(meter_vm=2.0, meter_va=math.pi / 6.0),
        voltage_real,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        voltage_outputs["ui"].eval(meter_vm=2.0, meter_va=math.pi / 6.0),
        voltage_imaginary,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        current_outputs["ir"].eval(
            meter_vm=2.0,
            meter_va=math.pi / 6.0,
            meter_p=3.0,
            meter_q=4.0,
        ),
        expected_current_real,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )
    assert math.isclose(
        current_outputs["ii"].eval(
            meter_vm=2.0,
            meter_va=math.pi / 6.0,
            meter_p=3.0,
            meter_q=4.0,
        ),
        expected_current_imaginary,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )
    assert power_outputs["p"].eval(meter_p=3.0) == 3.0
    assert power_outputs["q"].eval(meter_q=4.0) == 4.0
