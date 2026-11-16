# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Numerical contracts of native equipment blocks before parser integration."""

import math

import pytest

from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import (
    DgsElmSymMachineParameters,
    build_dgs_elmgenstat_block,
    build_dgs_elmsvs_block,
    build_dgs_elmsym_block,
    build_dgs_elmvsc_block,
    build_dgs_elmvscmono_block,
    build_dgs_regc_current_pll_block,
    build_dgs_regc_voltage_source_block,
)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import build_explicit_init_graph
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver
from VeraGridEngine.enumerations import SynchronousMachineSpeedVariationMode


def _initial_bindings(block: Block, supplied: dict[str, float]) -> dict[int, float]:
    """Evaluate native startup assignments with supplied terminal operating data.

    :param block: Equipment-only block with no imported controller children.
    :param supplied: Test operating point keyed by the documented port names.
    :return: Numeric UID bindings after explicit initialization.
    """
    bindings: dict[int, float] = dict()
    collection: list[Var]
    variable: Var
    for collection in (block.in_vars, block.out_vars, block.state_vars, block.algebraic_vars, block.diff_vars):
        for variable in collection:
            bindings[variable.uid] = supplied.get(variable.name, 0.0)
    expression: Expr
    for variable, expression in block.parameters.items():
        assert isinstance(expression, Const)
        bindings[variable.uid] = float(expression.value)
    equations, dependencies, ordered, events = build_explicit_init_graph(block)
    for variable in ordered:
        assert variable not in dependencies[variable], "Native startup must not depend on a scalar root guess"
        bindings[variable.uid] = float(equations[variable].eval_uid(bindings))
    return bindings


def _assert_equilibrium(block: Block, bindings: dict[int, float], tolerance: float = 1e-8) -> None:
    """Check complete native DAE balance rather than just its port counts.

    :param block: Physical equipment under test.
    :param bindings: Initialized numeric operating point.
    :param tolerance: Absolute residual tolerance.
    :return: None.
    """
    assert len(block.state_vars) == len(block.state_eqs)
    assert len(block.algebraic_vars) == len(block.algebraic_eqs)
    expression: Expr
    for expression in block.state_eqs:
        assert expression.eval_uid(bindings) == pytest.approx(0.0, abs=tolerance)
    for expression in block.algebraic_eqs:
        assert expression.eval_uid(bindings) == pytest.approx(0.0, abs=tolerance)
    assert len(block.children) == 0


@pytest.mark.parametrize("delay", (0.0, 0.1))
def test_regc_voltage_source_equilibrium_and_blocking(delay: float) -> None:
    """Keep the complex impedance drop and bypass it when the bridge blocks.

    :param delay: Te selects algebraic or first-order voltage realization.
    :return: None.
    """
    block: Block = build_dgs_regc_voltage_source_block(delay, 0.1, 0.2)
    bindings: dict[int, float] = _initial_bindings(
        block, dict(ur=1.0, ui=0.0, id_ref=0.2, iq_ref=-0.1, is_blocked=0.0))
    _assert_equilibrium(block, bindings)
    assert bindings[block.out_vars[0].uid] == pytest.approx(1.04)
    assert bindings[block.out_vars[1].uid] == pytest.approx(0.03)
    assert len(block.state_vars) == (2 if delay > 0.0 else 0)
    blocked: dict[int, float] = _initial_bindings(
        block, dict(ur=1.0, ui=0.0, id_ref=0.2, iq_ref=-0.1, is_blocked=1.0))
    _assert_equilibrium(block, blocked)
    assert blocked[block.out_vars[0].uid] == pytest.approx(1.0)
    assert blocked[block.out_vars[1].uid] == pytest.approx(0.0)


def test_regc_voltage_lag_follows_voltage_step() -> None:
    """A dynamic Te retains memory and responds with its expected derivative.

    :return: None.
    """
    block: Block = build_dgs_regc_voltage_source_block(0.1, 0.0, 0.0)
    bindings: dict[int, float] = _initial_bindings(
        block, dict(ur=1.0, ui=0.0, id_ref=0.0, iq_ref=0.0, is_blocked=0.0))
    bindings[block.in_vars[0].uid] = 1.2
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(2.0)


@pytest.mark.parametrize("angle", (0.0, math.pi / 2.0, -math.pi / 2.0, 2.7))
def test_regc_pll_locks_in_every_quadrant(angle: float) -> None:
    """Lock to the voltage angle and rotate stationary current consistently.

    :param angle: Terminal phasor angle in radians.
    :return: None.
    """
    block: Block = build_dgs_regc_current_pll_block(2.0, 3.0, 0.2, -0.5, 0.5)
    bindings: dict[int, float] = _initial_bindings(block, dict(
        ur=math.cos(angle), ui=math.sin(angle), u=1.0,
        ir=0.4 * math.cos(angle), ii=0.4 * math.sin(angle)))
    _assert_equilibrium(block, bindings)
    assert bindings[block.out_vars[0].uid] == pytest.approx(0.4)
    assert bindings[block.out_vars[1].uid] == pytest.approx(0.0, abs=1e-12)
    assert bindings[block.state_vars[1].uid] == pytest.approx(angle)


def test_regc_pll_limits_speed_and_freezes_both_memories() -> None:
    """Limit the angle rate above threshold and freeze it during voltage dips.

    :return: None.
    """
    block: Block = build_dgs_regc_current_pll_block(2.0, 3.0, 0.2, -0.5, 0.5)
    bindings: dict[int, float] = _initial_bindings(block, dict(ur=1.0, ui=0.0, u=1.0))
    bindings[block.in_vars[3].uid] = 1.0
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(3.0)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.5)
    bindings[block.in_vars[4].uid] = 0.1
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.0)


@pytest.mark.parametrize("delay", (0.0, 0.05))
def test_elmgenstat_converts_equipment_currents_to_system_power(delay: float) -> None:
    """Preserve injected P/Q across distinct power bases and frame rotation.

    :param delay: Optional lag on the dq reference frame.
    :return: None.
    """
    block: Block = build_dgs_elmgenstat_block(100.0, 50.0, delay)
    bindings: dict[int, float] = _initial_bindings(block, dict(Vm=1.0, Va=0.6, Pg=0.2, Qg=0.1))
    _assert_equilibrium(block, bindings)
    assert bindings[block.in_vars[2].uid] == pytest.approx(0.4)
    assert bindings[block.in_vars[3].uid] == pytest.approx(-0.2)
    assert bindings[block.out_vars[2].uid] == pytest.approx(0.4)
    assert bindings[block.out_vars[3].uid] == pytest.approx(0.2)
    assert len(block.state_vars) == (2 if delay > 0.0 else 0)


def test_svc_uses_voltage_squared_and_preserves_native_metadata() -> None:
    """A 25 MVAr susceptance delivers 20.25 MVAr at 0.9 p.u. voltage.

    :return: None.
    """
    block: Block = build_dgs_elmsvs_block(100.0, 40.0, -20.0, 5.0, 2.0, 1.0)
    bindings: dict[int, float] = _initial_bindings(block, dict(Vm=0.9, Va=0.0, Qsvs=0.2025))
    _assert_equilibrium(block, bindings)
    assert bindings[block.in_vars[2].uid] == pytest.approx(25.0, abs=1e-9)
    assert bindings[block.out_vars[0].uid] == pytest.approx(0.0)
    assert bindings[block.out_vars[4].uid] == pytest.approx(-20.0)


@pytest.mark.parametrize("capacitance", (0.0, 500.0))
def test_monopolar_vsc_closes_power_balance_with_copper_losses(capacitance: float) -> None:
    """Start from terminal P/Q and derive modulation and converter losses.

    :param capacitance: Optional DC terminal capacitor in microfarads.
    :return: None.
    """
    block: Block = build_dgs_elmvscmono_block(100.0, 90.0, 230.0, 400.0, 400.0, 0.01, 0.1, capacitance)
    bindings: dict[int, float] = _initial_bindings(block, dict(
        Vdc=1.0, Vm=1.0, Va=0.0, cosref=1.0, sinref=0.0, Pac=-0.18, Qac=-0.09))
    variable: Var
    for variable in block.diff_vars:
        bindings[variable.uid] = 0.0
    _assert_equilibrium(block, bindings)
    assert bindings[block.out_vars[0].uid] == pytest.approx(0.2, abs=1e-10)
    assert bindings[block.out_vars[1].uid] == pytest.approx(-0.1, abs=1e-10)
    assert bindings[block.out_vars[3].uid] == pytest.approx(0.18045)
    assert len(block.diff_vars) == (1 if capacitance > 0.0 else 0)


def test_bipolar_mmc_stores_power_imbalance_in_its_capacitor() -> None:
    """Seed a balanced MMC, then charge its capacitance with a power surplus.

    :return: None.
    """
    block: Block = build_dgs_elmvsc_block(
        100.0, 200.0, 230.0, 320.0, 320.0, 640.0, 1000.0, 0.01, 0.1)
    bindings: dict[int, float] = _initial_bindings(block, dict(
        Vdc_positive=1.0, Vdc_negative=-1.0, Vm=1.0, Va=0.0, Pac=0.2, Qac=0.1))
    _assert_equilibrium(block, bindings)
    assert bindings[block.out_vars[1].uid] == pytest.approx(640.0)
    assert bindings[block.in_vars[6].uid] == pytest.approx(1.0)
    # 1 MW of surplus = 0.01 p.u.; Ceq=0.006 F and U=640 kV.
    bindings[block.out_vars[2].uid] += 0.01
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1e6 / (6000.0 * 640.0))


def _machine_parameters(round_rotor: bool) -> DgsElmSymMachineParameters:
    """Build a finite physical machine without any DGS circuit dependency.

    :param round_rotor: Enable the q-axis transient rotor winding.
    :return: Complete physical machine parameter object.
    """
    return DgsElmSymMachineParameters(
        Snom=100.0, rated_power_factor=0.9, Rs=0.002,
        Xd=1.8, Xq=1.7, Xd_prime=0.3, Xq_prime=0.55,
        Xd_2prime=0.2, Xq_2prime=0.2, Xl=0.1,
        Td0_prime=8.0, Tq0_prime=0.4 if round_rotor else 0.0,
        Td0_2prime=0.03, Tq0_2prime=0.05,
        rms_acceleration_time_constant=7.0, rms_dpu=0.0, rms_dkd=0.0, rms_dpe=0.0,
        rms_rotor_coupling_reactance_d=0.0, rms_rotor_coupling_reactance_q=0.0,
        rms_td_prime_short_circuit=0.0, rms_tq_prime_short_circuit=0.0,
        rms_td_2prime_short_circuit=0.0, rms_tq_2prime_short_circuit=0.0,
        rms_excitation_current_base=1.0, rms_excitation_voltage_base_ratio=1.0,
        rms_excitation_gain=1.0, rms_rated_field_voltage=1.0,
        rms_saturation_curve_type=-1, rms_saturation_axis_mode=0,
        rms_saturation_smoothing_factor=0.0,
        rms_speed_variation_mode=SynchronousMachineSpeedVariationMode.Considered,
        rms_saturation_sg10=0.0, rms_saturation_sg12=0.0,
        rms_saturation_sg10q=0.0, rms_saturation_sg12q=0.0,
        rms_saturation_voltage_points=tuple(), rms_saturation_excitation_points=tuple(),
        rms_saturation_q_voltage_points=tuple(), rms_saturation_q_excitation_points=tuple(),
    )


@pytest.mark.parametrize("round_rotor", (False, True))
@pytest.mark.parametrize("active_power", (0.0, 0.3))
def test_synchronous_machine_flux_equilibrium(round_rotor: bool, active_power: float) -> None:
    """Reconstruct distinct rotor circuits and initialize their flux equilibrium.

    :param round_rotor: Cylindrical or salient rotor topology.
    :param active_power: Solved system-base active injection.
    :return: None.
    """
    block: Block = build_dgs_elmsym_block(_machine_parameters(round_rotor), 200.0, 60.0)
    bindings: dict[int, float] = _initial_bindings(block, dict(Vm=1.0, Va=0.2, Pg=active_power, Qg=0.05))
    _assert_equilibrium(block, bindings, tolerance=1e-6)
    assert len(block.state_vars) == (6 if round_rotor else 5)
    assert bindings[block.out_vars[2].uid] == pytest.approx(1.0)
    assert bindings[block.out_vars[4].uid] == pytest.approx(active_power * 2.0 / 0.9)


def test_native_blocks_reject_undefined_physical_parameters() -> None:
    """Refuse invalid bases, delays, limits and required capacitor storage.

    :return: None.
    """
    with pytest.raises(ValueError):
        build_dgs_elmgenstat_block(0.0, 100.0)
    with pytest.raises(ValueError):
        build_dgs_regc_voltage_source_block(-0.1, 0.0, 0.1)
    with pytest.raises(ValueError):
        build_dgs_regc_current_pll_block(1.0, 1.0, 0.2, 2.0, 1.0)
    with pytest.raises(ValueError):
        build_dgs_elmvsc_block(100.0, 100.0, 230.0, 320.0, 320.0, 640.0, 0.0, 0.01, 0.1)


def test_native_equipment_instances_own_independent_symbolic_graphs() -> None:
    """Keep repeated instances independent and preserve the block through IO.

    :return: None.
    """
    first: Block = build_dgs_elmgenstat_block(100.0, 50.0)
    second: Block = build_dgs_elmgenstat_block(100.0, 50.0)
    assert first.in_vars[0].uid != second.in_vars[0].uid
    assert first.out_vars[0].uid != second.out_vars[0].uid
    saver: BlockSaver = BlockSaver(VarFactory())
    saver.save_block(first)
    parser: BlockParser = BlockParser(VarFactory())
    restored_roots: list[Block] = parser.parse(dict(
        consts=saver.get_const_to_save(), vars=saver.get_vars_to_save(),
        diff_vars=saver.get_diff_vars_to_save(), blocks=saver.get_blocks()))
    assert len(restored_roots) == 1
    restored: Block = restored_roots[0]
    bindings: dict[int, float] = _initial_bindings(restored, dict(Vm=1.0, Va=0.2, Pg=0.2, Qg=0.1))
    _assert_equilibrium(restored, bindings)


def test_all_native_blocks_roundtrip_preserves_physical_interfaces() -> None:
    """Persist every supported topology without losing states, ports or bases.

    :return: None.
    """
    blocks: tuple[Block, ...] = (
        build_dgs_regc_voltage_source_block(0.0, 0.01, 0.1),
        build_dgs_regc_voltage_source_block(0.1, 0.01, 0.1),
        build_dgs_regc_current_pll_block(2.0, 3.0, 0.2, -0.5, 0.5),
        build_dgs_elmgenstat_block(100.0, 50.0, 0.05),
        build_dgs_elmsvs_block(100.0, 40.0, -20.0, 5.0, 2.0, 1.0),
        build_dgs_elmvscmono_block(100.0, 90.0, 230.0, 400.0, 400.0, 0.01, 0.1, 500.0),
        build_dgs_elmvsc_block(100.0, 200.0, 230.0, 320.0, 320.0, 640.0, 1000.0, 0.01, 0.1),
        build_dgs_elmsym_block(_machine_parameters(False), 200.0, 60.0),
        build_dgs_elmsym_block(_machine_parameters(True), 200.0, 60.0),
    )
    block: Block
    for block in blocks:
        saver: BlockSaver = BlockSaver(VarFactory())
        saver.save_block(block)
        parser: BlockParser = BlockParser(VarFactory())
        restored_roots: list[Block] = parser.parse(dict(
            consts=saver.get_const_to_save(), vars=saver.get_vars_to_save(),
            diff_vars=saver.get_diff_vars_to_save(), blocks=saver.get_blocks()))
        assert len(restored_roots) == 1
        restored: Block = restored_roots[0]
        assert list(var.name for var in restored.in_vars) == list(var.name for var in block.in_vars)
        assert list(var.name for var in restored.out_vars) == list(var.name for var in block.out_vars)
        assert list(var.name for var in restored.state_vars) == list(var.name for var in block.state_vars)
        assert len(restored.diff_vars) == len(block.diff_vars)
        assert set(restored.external_mapping.keys()) == set(block.external_mapping.keys())
        assert len(restored.algebraic_eqs) == len(block.algebraic_eqs)
