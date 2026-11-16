# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Tests for EMT system topology validation in EmtProblemDae.

These tests exercise current interface checks, canonical electrical connections
and mapped-current assembly without relying on the retired connection counter.
"""


import pytest
import numpy as np
import warnings

from scipy.sparse.linalg import MatrixRankWarning

from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.problems.emt_problem_dae import (
    EmtDeviceDisposition,
    EmtInterfaceValidationError,
    EmtProblemDae,
    EmtTopologyError,
    _build_emt_device_type_disposition_table,
    validate_line_phase_layout,
)
from VeraGridEngine.Simulations.EMT.problems.emt_terminal_current_assembly import assemble_emt_mapped_current_references
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_driver_3ph import PowerFlowDriver3Ph
from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtSolverTypes, ShuntConnectionType, EmtInitializationMethod, \
    ConverterControlType, DeviceType, SolverType, VarPowerFlowReferenceType
from VeraGridEngine.Templates.Emt.line.pi_line_emt_template import get_pi_line_emt_template
from VeraGridEngine.Templates.Emt.line.bergeron_line_emt_template import get_bergeron_line_emt_template
from VeraGridEngine.Templates.Emt.load_characteristics.load_RLC_emt_template import (
    get_grounding_link_emt_template,
    get_shunt_r_emt_template,
    get_shunt_rlc_combo_emt_template,
)
from VeraGridEngine.Templates.Emt.synchronous_machines.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template_with_ref
from VeraGridEngine.Templates.Emt.buses.bus_emt_template import get_bus_emt_template
from VeraGridEngine.Templates.Emt.transformers.transformer_emt_template import get_transformer_emt_template
from VeraGridEngine.Templates.Emt.converters.converter_emt_template import get_emt_ideal_converter
from VeraGridEngine.Templates.Emt.converters.converter_switched_emt_template import get_switched_emt_converter
from VeraGridEngine.Templates.Emt.dc_line.dc_load_emt_template import get_dc_load_emt_template
from VeraGridEngine.Templates.Emt.dc_line.dc_line_emt_template import get_dc_line_emt_template
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_emt_model
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockSaver
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, get_expression_vars
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.api as gce

from tests.symbolic_block_roundtrip import parse_saved_block, save_block_fixture


def get_default_emt_options() -> EmtOptions:
    """Return default EMT options for testing."""
    return EmtOptions(
        time_step=5e-6,
        simulation_time=0.01,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Auto,
        integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=0
    )


def get_switched_converter_emt_options() -> EmtOptions:
    """Return lightweight EMT options for the switched-converter validation test."""
    return EmtOptions(
        time_step=1e-5,
        simulation_time=1.2e-3,
        tolerance=1e-6,
        solver_type=EmtSolverTypes.Symbolic,
        initialization_method=EmtInitializationMethod.Explicit,
        integration_method=DynamicIntegrationMethod.DaeBackEuler,
        verbose=0,
    )


def run_power_flow(grid: gce.MultiCircuit) -> tuple:
    """Run power flow and return results."""
    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        retry_with_other_methods=True,
        max_iter=100,
        tolerance=1e-6,
        control_q=True,
        control_taps_modules=False,
        control_taps_phase=False,
        orthogonalize_controls=False,
    )
    with warnings.catch_warnings():
        # The retry battery intentionally explores several numerical methods.
        # Some rejected candidates emit transient numeric warnings before the
        # driver falls back to a converged solution, which is the behavior this
        # validation helper cares about.
        warnings.filterwarnings(
            "ignore",
            message="overflow encountered in scalar multiply",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in multiply",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in scalar divide",
            category=RuntimeWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Matrix is exactly singular",
            category=MatrixRankWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Unable to factorize HELM coefficients matrix :/",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in divide",
            category=RuntimeWarning,
        )
        pf_results = gce.power_flow(grid=grid, options=pf_options)

    pf_options_3ph = PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=True,
        control_taps_phase=True,
        control_remote_voltage=True,
        orthogonalize_controls=True,
        apply_temperature_correction=True,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )
    power_flow_3ph = PowerFlowDriver3Ph(grid, pf_options_3ph)
    power_flow_3ph.run()
    pf_res_3ph = power_flow_3ph.results

    return pf_results, pf_res_3ph


def _build_interface_validation_problem(grid: gce.MultiCircuit) -> EmtProblemDae:
    """Build one minimal problem instance used only for EMT interface validation."""
    problem: EmtProblemDae = EmtProblemDae.__new__(EmtProblemDae)
    problem.grid = grid
    problem.logger = Logger()
    problem._device_type_disposition = _build_emt_device_type_disposition_table()
    problem._local_external_mapping_by_block_uid = dict()
    return problem


def _build_terminal_mapping_test_problem(logger: Logger | None) -> EmtProblemDae:
    """Build the minimal problem state required to register one EMT model.

    :param logger: Optional driver-owned logger used by mapping diagnostics.
    :return: Lightweight EMT problem prepared for ``_process_device_model``.
    """
    problem: EmtProblemDae = EmtProblemDae.__new__(EmtProblemDae)
    problem.logger = logger
    problem._device_type_disposition = _build_emt_device_type_disposition_table()
    problem._local_external_mapping_by_block_uid = dict()
    problem._runtime_parameter_owner_blocks = dict()
    problem._runtime_parameter_devices = dict()
    problem._event_parameter_device_idtags = dict()
    problem._event_parameter_name_lookup = dict()
    problem._continuous_event_parameter_uids = set()
    problem._discrete_event_parameter_uids = set()
    problem._vars2device = dict()
    problem._vars_info = dict()
    problem._vars_glob_name2uid = dict()
    problem._pending_fmu_cs_devices = list()
    problem._pending_fmu_me_devices = list()
    problem._device_models_with_init_eqs = list()
    problem._device_models_with_init_eqs_seen = set()
    problem._device_models_for_ptc = list()
    return problem


def _build_line_for_phase_layout(
        phase_mask: tuple[bool, bool, bool, bool],
) -> gce.Line:
    """Build one line whose physical phase mask is explicitly controlled.

    :param phase_mask: Active physical conductors in NABC order.
    :return: Line prepared for terminal-layout validation.
    """
    bus_from: gce.Bus = gce.Bus(name="Terminal from", Vnom=20.0)
    bus_to: gce.Bus = gce.Bus(name="Terminal to", Vnom=20.0)
    line: gce.Line = gce.Line(name="Terminal line", bus_from=bus_from, bus_to=bus_to)
    line.ys.phN = phase_mask[0]
    line.ys.phA = phase_mask[1]
    line.ys.phB = phase_mask[2]
    line.ys.phC = phase_mask[3]
    return line


def _register_terminal_mapping(
        problem: EmtProblemDae,
        line: gce.Line,
        block: Block,
) -> dict[object, Var]:
    """Register one line block and return its problem-local external mapping.

    :param problem: Lightweight EMT problem receiving the local mapping.
    :param line: Static line owning the symbolic model.
    :param block: Symbolic line model to register.
    :return: Effective mapping stored by the EMT problem.
    """
    system_block: Block = Block()
    problem._process_device_model(
        dev=line,
        mdl=block,
        sys_block=system_block,
        static_parameter_values_mapping=dict(),
    )
    return problem._local_external_mapping_by_block_uid[block.uid]


def test_terminal_mapping_keeps_modern_connected_targets_authoritative() -> None:
    """Keep modern semantic keys after their targets are rebound to bus variables.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    from_target: Var = Var(name="connected_from_a", reference=VarPowerFlowReferenceType.v_A)
    to_target: Var = Var(name="connected_to_a", reference=VarPowerFlowReferenceType.v_A)
    block: Block = Block(
        in_vars=list((from_target, to_target)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.vf_A, from_target),
            (VarPowerFlowReferenceType.vt_A, to_target),
        )),
    )
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=None)
    effective_mapping: dict[object, Var] = _register_terminal_mapping(
        problem=problem,
        line=line,
        block=block,
    )

    assert list(effective_mapping.keys()) == list((
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vt_A,
    ))
    assert validate_line_phase_layout(
        branch=line,
        mdl=block,
        effective_external_mapping=effective_mapping,
        logger=None,
    )


def test_terminal_mapping_completes_partial_modern_contract_from_legacy_inputs() -> None:
    """Complete one missing modern terminal from a compatible legacy input.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    from_target: Var = Var(name="modern_from_a", reference=VarPowerFlowReferenceType.vf_A)
    to_target: Var = Var(name="legacy_to_a", reference=VarPowerFlowReferenceType.vt_A)
    block: Block = Block(
        in_vars=list((from_target, to_target)),
        external_mapping=dict(((VarPowerFlowReferenceType.vf_A, from_target),)),
    )
    original_mapping: dict[object, Var] = dict(block.external_mapping)
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=None)
    effective_mapping: dict[object, Var] = _register_terminal_mapping(
        problem=problem,
        line=line,
        block=block,
    )

    assert effective_mapping[VarPowerFlowReferenceType.vf_A] is from_target
    assert effective_mapping[VarPowerFlowReferenceType.vt_A] is to_target
    assert block.external_mapping == original_mapping
    assert VarPowerFlowReferenceType.vt_A not in block.external_mapping


def test_terminal_mapping_restores_complete_legacy_line_contract_locally() -> None:
    """Restore an in-vars-only line interface without mutating its source block.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, True, False))
    legacy_vars: list[Var] = list((
        Var(name="legacy_from_a", reference=VarPowerFlowReferenceType.vf_A),
        Var(name="legacy_from_b", reference=VarPowerFlowReferenceType.vf_B),
        Var(name="legacy_to_a", reference=VarPowerFlowReferenceType.vt_A),
        Var(name="legacy_to_b", reference=VarPowerFlowReferenceType.vt_B),
    ))
    block: Block = Block(in_vars=legacy_vars, external_mapping=dict())
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=None)
    effective_mapping: dict[object, Var] = _register_terminal_mapping(
        problem=problem,
        line=line,
        block=block,
    )

    assert list(effective_mapping.keys()) == list((
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
    ))
    assert len(block.external_mapping) == 0
    assert validate_line_phase_layout(
        branch=line,
        mdl=block,
        effective_external_mapping=effective_mapping,
        logger=None,
    )


def test_terminal_mapping_rejects_modern_legacy_target_conflict() -> None:
    """Reject one terminal whose modern and legacy targets are incompatible.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    modern_target: Var = Var(name="modern_from_a", reference=VarPowerFlowReferenceType.v_A)
    legacy_target: Var = Var(name="legacy_from_a", reference=VarPowerFlowReferenceType.vf_A)
    block: Block = Block(
        in_vars=list((legacy_target,)),
        external_mapping=dict(((VarPowerFlowReferenceType.vf_A, modern_target),)),
    )
    logger: Logger = Logger()
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=logger)

    with pytest.raises(EmtTopologyError, match="Conflicting EMT terminal mappings"):
        _register_terminal_mapping(problem=problem, line=line, block=block)

    assert logger.has_errors()
    assert logger.entries[-1].device_property == "emt_terminal_mapping"


def test_terminal_mapping_ignores_internal_legacy_reference_when_modern_owner_exists() -> None:
    """Do not treat a child-internal input as a second public terminal.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    public_vdc: Var = Var(name="public_vdc", reference=VarPowerFlowReferenceType.Vdc)
    internal_vdc: Var = Var(name="internal_vdc", reference=VarPowerFlowReferenceType.Vdc)
    child_block: Block = Block(in_vars=list((internal_vdc,)))
    root_block: Block = Block(
        children=list((child_block,)),
        in_vars=list((public_vdc,)),
        external_mapping=dict(((VarPowerFlowReferenceType.Vdc, public_vdc),)),
    )
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=None)
    effective_mapping: dict[object, Var] = _register_terminal_mapping(
        problem=problem,
        line=line,
        block=root_block,
    )

    assert effective_mapping[VarPowerFlowReferenceType.Vdc] is public_vdc


def test_terminal_mapping_rejects_conflicting_hierarchy_declarations() -> None:
    """Reject two hierarchy blocks that map one terminal to different variables.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    root_target: Var = Var(name="root_from_a", reference=VarPowerFlowReferenceType.vf_A)
    child_target: Var = Var(name="child_from_a", reference=VarPowerFlowReferenceType.vf_A)
    child_block: Block = Block(
        external_mapping=dict(((VarPowerFlowReferenceType.vf_A, child_target),)),
    )
    root_block: Block = Block(
        children=list((child_block,)),
        external_mapping=dict(((VarPowerFlowReferenceType.vf_A, root_target),)),
    )
    problem: EmtProblemDae = _build_terminal_mapping_test_problem(logger=None)

    with pytest.raises(EmtTopologyError, match="targets both"):
        _register_terminal_mapping(problem=problem, line=line, block=root_block)


@pytest.mark.parametrize(
    "phase_mask, terminal_refs",
    list((
        (
            (False, True, True, True),
            (
                VarPowerFlowReferenceType.vf_A,
                VarPowerFlowReferenceType.vf_B,
                VarPowerFlowReferenceType.vf_C,
                VarPowerFlowReferenceType.vt_A,
                VarPowerFlowReferenceType.vt_B,
                VarPowerFlowReferenceType.vt_C,
            ),
        ),
        (
            (True, True, True, True),
            (
                VarPowerFlowReferenceType.vf_N,
                VarPowerFlowReferenceType.vf_A,
                VarPowerFlowReferenceType.vf_B,
                VarPowerFlowReferenceType.vf_C,
                VarPowerFlowReferenceType.vt_N,
                VarPowerFlowReferenceType.vt_A,
                VarPowerFlowReferenceType.vt_B,
                VarPowerFlowReferenceType.vt_C,
            ),
        ),
        (
            (False, False, True, False),
            (
                VarPowerFlowReferenceType.vf_B,
                VarPowerFlowReferenceType.vt_B,
            ),
        ),
        (
            (False, True, False, True),
            (
                VarPowerFlowReferenceType.vf_A,
                VarPowerFlowReferenceType.vf_C,
                VarPowerFlowReferenceType.vt_A,
                VarPowerFlowReferenceType.vt_C,
            ),
        ),
    )),
)
def test_line_phase_layout_accepts_canonical_phase_variants(
        phase_mask: tuple[bool, bool, bool, bool],
        terminal_refs: tuple[VarPowerFlowReferenceType, ...],
) -> None:
    """Accept ABC, NABC, single-phase and non-contiguous two-phase layouts.

    :param phase_mask: Active physical conductors in NABC order.
    :param terminal_refs: Expected canonical terminal sequence.
    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout(phase_mask)
    effective_mapping: dict[object, Var] = dict()
    terminal_ref: VarPowerFlowReferenceType
    for terminal_ref in terminal_refs:
        effective_mapping[terminal_ref] = Var(
            name=f"mapped_{terminal_ref.value}",
            reference=terminal_ref,
        )
    block: Block = Block(external_mapping=dict(effective_mapping))

    assert validate_line_phase_layout(
        branch=line,
        mdl=block,
        effective_external_mapping=effective_mapping,
        logger=None,
    )


def test_line_phase_layout_rejects_missing_terminal_without_logger() -> None:
    """Reject an incomplete phase layout even when diagnostics are disabled.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    from_target: Var = Var(name="only_from_a", reference=VarPowerFlowReferenceType.vf_A)
    effective_mapping: dict[object, Var] = dict(((VarPowerFlowReferenceType.vf_A, from_target),))
    block: Block = Block(external_mapping=dict(effective_mapping))

    assert not validate_line_phase_layout(
        branch=line,
        mdl=block,
        effective_external_mapping=effective_mapping,
        logger=None,
    )


def test_line_phase_layout_reports_unexpected_terminal_to_driver_logger() -> None:
    """Report source, resolved, missing and unexpected terminal sets.

    :return: None.
    """
    line: gce.Line = _build_line_for_phase_layout((False, True, False, False))
    refs: tuple[VarPowerFlowReferenceType, ...] = (
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vt_A,
    )
    effective_mapping: dict[object, Var] = dict()
    terminal_ref: VarPowerFlowReferenceType
    for terminal_ref in refs:
        effective_mapping[terminal_ref] = Var(
            name=f"mapped_{terminal_ref.value}",
            reference=terminal_ref,
        )
    block: Block = Block(external_mapping=dict(effective_mapping))
    driver_logger: Logger = Logger()

    assert not validate_line_phase_layout(
        branch=line,
        mdl=block,
        effective_external_mapping=effective_mapping,
        logger=driver_logger,
    )
    assert driver_logger.has_errors()
    assert "resolved=" in driver_logger.entries[-1].value
    assert "missing=" in driver_logger.entries[-1].value
    assert "unexpected=" in driver_logger.entries[-1].value


def test_bus_readiness_validation_rejects_missing_bus_emt_model() -> None:
    """EMT problem preconditions must reject buses without one EMT shell."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusMissingShell", Vnom=20.0)
    grid.add_bus(bus)

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="BusMissingShell"):
        problem._validate_bus_emt_models_ready()


def test_bus_readiness_validation_rejects_pending_emt_devices() -> None:
    """EMT problem preconditions must reject unresolved deferred bus connections."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusPending", Vnom=20.0)
    load = gce.Load(name="PendingLoad", P=10.0, Q=1.0)
    grid.add_bus(bus)
    bus.emt_model = _make_external_mapping_block([VarPowerFlowReferenceType.v_A], "bus_pending")
    bus.add_pending_emt_device(load)

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="PendingLoad"):
        problem._validate_bus_emt_models_ready()


def test_bus_readiness_validation_accepts_valid_ac_bus_shell() -> None:
    """One valid AC bus EMT shell must pass the new readiness validation."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusReadyAC", Vnom=20.0)
    grid.add_bus(bus)
    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_ready_ac")

    problem = _build_interface_validation_problem(grid)
    problem._validate_bus_emt_models_ready()


def test_bus_readiness_validation_accepts_valid_dc_bus_shell() -> None:
    """One valid DC bus EMT shell must pass the new readiness validation."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusReadyDC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus)
    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.Vdc,
    ], "bus_ready_dc")

    problem = _build_interface_validation_problem(grid)
    problem._validate_bus_emt_models_ready()


def test_emt_device_type_disposition_table_covers_full_enum() -> None:
    """Every ``DeviceType`` must have one explicit EMT disposition entry."""
    disposition_table: dict[DeviceType, str] = _build_emt_device_type_disposition_table()
    device_tpe: DeviceType

    for device_tpe in DeviceType:
        assert device_tpe in disposition_table


def test_emt_device_type_disposition_table_marks_structural_network_types() -> None:
    """EMT network devices must map to explicit structural dispositions."""
    disposition_table: dict[DeviceType, str] = _build_emt_device_type_disposition_table()

    assert disposition_table[DeviceType.BusDevice] == EmtDeviceDisposition.BUS_STRUCTURAL
    assert disposition_table[DeviceType.LineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.Transformer2WDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.SeriesReactanceDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.SwitchDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.DCLineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.HVDCLineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.VscDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.GeneratorDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.BatteryDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.LoadDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ExternalGridDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.StaticGeneratorDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ShuntDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ControllableShuntDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.CurrentInjectionDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL


def test_emt_device_type_disposition_table_marks_non_network_types_as_noop() -> None:
    """Non-electrical metadata device types must resolve to explicit EMT no-op."""
    disposition_table: dict[DeviceType, str] = _build_emt_device_type_disposition_table()

    assert disposition_table[DeviceType.CountryDevice] == EmtDeviceDisposition.NON_EMT_NOOP
    assert disposition_table[DeviceType.AreaDevice] == EmtDeviceDisposition.NON_EMT_NOOP
    assert disposition_table[DeviceType.FuelDevice] == EmtDeviceDisposition.NON_EMT_NOOP
    assert disposition_table[DeviceType.EmtEventDevice] == EmtDeviceDisposition.NON_EMT_NOOP
    assert disposition_table[DeviceType.EmtModelTemplateDevice] == EmtDeviceDisposition.NON_EMT_NOOP


def test_emt_device_type_disposition_table_marks_explicit_branch_paths() -> None:
    """Representative branch device types must resolve to explicit structural EMT paths."""
    disposition_table: dict[DeviceType, str] = _build_emt_device_type_disposition_table()

    assert disposition_table[DeviceType.LineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.Transformer2WDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.SeriesReactanceDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.SwitchDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.DCLineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.HVDCLineDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL
    assert disposition_table[DeviceType.VscDevice] == EmtDeviceDisposition.BRANCH_STRUCTURAL


def test_emt_device_type_disposition_table_marks_explicit_injection_paths() -> None:
    """Representative injection device types must resolve to explicit structural EMT paths."""
    disposition_table: dict[DeviceType, str] = _build_emt_device_type_disposition_table()

    assert disposition_table[DeviceType.GeneratorDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.BatteryDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.LoadDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ExternalGridDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.StaticGeneratorDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ShuntDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.ControllableShuntDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL
    assert disposition_table[DeviceType.CurrentInjectionDevice] == EmtDeviceDisposition.INJECTION_STRUCTURAL


def _make_ref_var(reference: VarPowerFlowReferenceType, name_suffix: str) -> Var:
    """Create one symbolic variable for a test EMT external reference."""
    return Var(name=f"{reference.value}_{name_suffix}", reference=reference)


def _make_external_mapping_block(refs: list[VarPowerFlowReferenceType], name_suffix: str) -> Block:
    """Create one minimal EMT block exposing the requested external references."""
    external_mapping: dict[VarPowerFlowReferenceType, Var] = dict()
    out_vars: list[Var] = list()
    reference: VarPowerFlowReferenceType

    for reference in refs:
        var = _make_ref_var(reference, name_suffix)
        external_mapping[reference] = var
        out_vars.append(var)

    return Block(external_mapping=external_mapping, out_vars=out_vars)


def _restore_version_three_grounding_block(
        block: Block,
        disconnect_internal_voltage: bool,
) -> Block:
    """Restore one legacy grounding fixture through the production migration.

    :param block: Canonical grounding block to downgrade.
    :param disconnect_internal_voltage: Break the child-to-parent voltage link.
    :return: Parsed version-three block after declarative migration.
    """
    if disconnect_internal_voltage:
        isolated_voltage: Var = Var(name="isolated_ground_voltage")
        ideal_ground_block: Block = block.children[0]
        ideal_ground_block.in_vars[0] = isolated_voltage
        ideal_ground_block.algebraic_eqs[0] = isolated_voltage
    else:
        pass

    legacy_records: dict[int, dict[str, object]]
    legacy_data: dict[str, object]
    legacy_saver: BlockSaver
    legacy_records, legacy_saver = save_block_fixture(block)
    legacy_data = legacy_records[block.uid]
    legacy_contract: object = legacy_data["dynamic_model_contract"]
    assert isinstance(legacy_contract, dict)
    legacy_contract["version"] = 3
    legacy_contract["rms_terminal_power_contributions"] = []
    legacy_contract.pop("emt_internal_grounding_link", None)
    legacy_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    legacy_contract.pop("modal_template_kind")
    legacy_contract.pop("modal_template_config")
    legacy_children_data: object = legacy_data["children"]
    assert isinstance(legacy_children_data, list)
    legacy_child_uid: object
    for legacy_child_uid in legacy_children_data:
        assert isinstance(legacy_child_uid, int)
        legacy_child_data: dict[str, object] = legacy_records[legacy_child_uid]
        legacy_child_contract: object = legacy_child_data["dynamic_model_contract"]
        assert isinstance(legacy_child_contract, dict)
        legacy_child_contract["version"] = 3
        legacy_child_contract["rms_terminal_power_contributions"] = []
        legacy_child_contract.pop("emt_internal_grounding_link", None)
        legacy_child_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
        legacy_child_contract.pop("modal_template_kind")
        legacy_child_contract.pop("modal_template_config")
    else:
        pass
    return parse_saved_block(legacy_records, legacy_saver)


@pytest.mark.parametrize("disconnect_internal_voltage", (False, True))
def test_legacy_grounding_assembly_preserves_electrical_connections_without_diagram(
        disconnect_internal_voltage: bool,
) -> None:
    """Assemble a public grounding terminal without inventing internal voltage links.

    :param disconnect_internal_voltage: Whether the ideal-ground child is disconnected.
    :return: None.
    """
    grid: gce.MultiCircuit = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus: gce.Bus = gce.Bus(name="NeutralBus", Vnom=20.0)
    load: gce.Load = gce.Load(name="Grounding", P=0.0, Q=0.0)
    grid.add_bus(bus)
    grid.add_load(bus=bus, api_obj=load)
    bus.emt_model = _make_external_mapping_block(
        refs=list((VarPowerFlowReferenceType.v_N,)), name_suffix="neutral_bus",
    )
    # A standalone grounding device must expose its public neutral terminal.
    original: Block = get_grounding_link_emt_template(
        vf=grid.var_factory, include_r=True, include_l=False, include_c=False,
        nested=False, direct_r_value=1.0, name="grounding_without_magic_name",
    ).block
    load.emt_model = _restore_version_three_grounding_block(
        block=original, disconnect_internal_voltage=disconnect_internal_voltage,
    )
    problem: EmtProblemDae = _build_interface_validation_problem(grid=grid)
    model: Block = load.emt_model
    public_voltage: Var | None = model.external_mapping.get(VarPowerFlowReferenceType.v_N, None)
    public_current: Var | None = model.external_mapping.get(VarPowerFlowReferenceType.i_N, None)
    bus_voltage: Var | None = bus.emt_model.external_mapping.get(VarPowerFlowReferenceType.v_N, None)
    assert public_voltage is not None
    assert public_current is not None
    assert bus_voltage is not None
    internal_voltage: Var = model.algebraic_vars[1]
    ground_child: Block = model.children[0]
    ground_voltage: Var = ground_child.in_vars[0]
    if disconnect_internal_voltage:
        assert ground_voltage.uid != internal_voltage.uid
    else:
        assert ground_voltage.uid == internal_voltage.uid
    # Diagram removal must leave both the bus substitution and neutral KCL unchanged.
    expected_ground_voltage_uid: int = ground_voltage.uid
    clear_diagram: bool
    for clear_diagram in (False, True):
        if clear_diagram:
            model.diagram.node_data.clear()
            model.diagram.con_data.clear()
        else:
            pass
        substitutions: dict[Var, Var] = dict()
        problem._connect_injection_bus_voltages(
            injection=load, mdl=model, bus_working_models=dict(((bus, bus.emt_model),)),
            voltage_connection_substitution=substitutions,
            ph_v_keys=list((VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.v_A,
                           VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.v_C)),
        )
        assert substitutions[public_voltage].uid == bus_voltage.uid
        assert internal_voltage not in substitutions
        assert ground_voltage not in substitutions
        assert set(variable.uid for variable in get_expression_vars(ground_child.algebraic_eqs[0])) == set((expected_ground_voltage_uid,))
        balances: dict[int, list[Expr]] = dict(((0, list(Const(0.0) for phase in range(4))),))
        assert assemble_emt_mapped_current_references(
            model=model, current_balance=balances, bus_index=0, bus_is_dc=False,
        )
        assert balances[0][0].eval_uid(dict(((public_current.uid, 2.0),))) == 2.0
        assert all(balance.eval_uid(dict()) == 0.0 for balance in balances[0][1:])


def test_grounded_star_assembly_leaves_unmapped_bus_neutral_unconnected() -> None:
    """Keep internal star-point grounds out of the external bus-neutral KCL.

    :return: None.
    """
    grid: gce.MultiCircuit = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus: gce.Bus = gce.Bus(name="StarBus", Vnom=20.0)
    grid.add_bus(bus)
    bus.emt_model = _make_external_mapping_block(
        refs=list((VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.v_N)), name_suffix="star_bus",
    )
    problem: EmtProblemDae = _build_interface_validation_problem(grid=grid)
    balances: dict[int, list[Expr]] = dict(((0, list(Const(0.0) for phase in range(4))),))
    bindings: dict[int, float] = dict()
    load_name: str
    for load_name in ("GroundedStarLoad1", "GroundedStarLoad2"):
        load: gce.Load = gce.Load(name=load_name, P=1.0, Q=0.0)
        grid.add_load(bus=bus, api_obj=load)
        model: Block = get_shunt_rlc_combo_emt_template(
            vf=grid.var_factory, include_r=True, include_l=False, include_c=False,
            phA=True, phB=False, phC=False, connection_type=ShuntConnectionType.GroundedStar,
            name=load_name,
        ).block
        load.emt_model = model
        assert model.external_mapping.get(VarPowerFlowReferenceType.v_N, None) is None
        assert model.external_mapping.get(VarPowerFlowReferenceType.i_N, None) is None
        phase_voltage: Var | None = model.external_mapping.get(VarPowerFlowReferenceType.v_A, None)
        phase_current: Var | None = model.external_mapping.get(VarPowerFlowReferenceType.i_A, None)
        assert phase_voltage is not None
        assert phase_current is not None
        substitutions: dict[Var, Var] = dict()
        problem._connect_injection_bus_voltages(
            injection=load, mdl=model, bus_working_models=dict(((bus, bus.emt_model),)),
            voltage_connection_substitution=substitutions,
            ph_v_keys=list((VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.v_A,
                           VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.v_C)),
        )
        assert set(substitutions) == set((phase_voltage,))
        assert substitutions[phase_voltage] is bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_A]
        assert assemble_emt_mapped_current_references(
            model=model, current_balance=balances, bus_index=0, bus_is_dc=False,
        )
        bindings[phase_current.uid] = 1.0
    assert balances[0][0].eval_uid(bindings) == 0.0
    assert balances[0][1].eval_uid(bindings) == 2.0
    assert all(balance.eval_uid(bindings) == 0.0 for balance in balances[0][2:])


def test_emt_template_assignment_materializes_missing_bus_shell() -> None:
    """GUI EMT template assignment may materialize one missing bus shell immediately."""
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    bus = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    generator = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50.0, r1=0.001, x1=1.7)

    grid.add_bus(bus)
    grid.add_generator(bus=bus, api_obj=generator)

    assert bus.emt_model.empty() is True

    generator.emt_template = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory)

    assert bus.emt_model.empty() is False
    assert bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_N] is None
    assert VarPowerFlowReferenceType.v_A in bus.emt_model.external_mapping


# =============================================================================
# TEST 1: scripting_example_thevequiv_piline_Rload_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================

def test_pi_line_rload_emt_passes_validation():
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    line_mdl = get_pi_line_emt_template(vf = grid.var_factory, phN = False, phA = True, phB = True, phC = True).block
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


# =============================================================================
# TEST 2: scripting_example_thevequiv_bergeronline_Rload_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================

def test_bergeron_line_rload_emt_passes_validation():
    """
    Validate the Bergeron EMT line workflow with the current history-var naming.

    The Bergeron runtime now resolves history event parameters using the compact
    root names ``Ih_f_<phase>`` and ``Ih_t_<phase>`` instead of the older
    line-name-qualified form. This test asserts that the template exposes those
    runtime parameters before building the EMT problem.

    :return: None.
    :rtype: None
    """
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    line_mdl = get_bergeron_line_emt_template(vf=grid.var_factory).block
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block

    history_var_names: set[str] = set()
    history_block = None
    history_var = None
    for history_block in line_mdl.get_all_blocks():
        for history_var in history_block.event_dict.keys():
            history_var_names.add(str(history_var.name))

    assert "Ih_f_A" in history_var_names
    assert "Ih_f_B" in history_var_names
    assert "Ih_f_C" in history_var_names
    assert "Ih_t_A" in history_var_names
    assert "Ih_t_B" in history_var_names
    assert "Ih_t_C" in history_var_names


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


# =============================================================================
# TEST 3: scripting_vsc_emt
# Positive case - should pass validation without raising EmtTopologyError
# =============================================================================


def test_vsc_emt_passes_validation():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus1_ac = gce.Bus(name="Bus1_AC", Vnom=230.0, is_slack=True)
    bus2_ac = gce.Bus(name="Bus2_AC", Vnom=230.0)
    bus3_dc = gce.Bus(name="Bus3_DC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus1_ac)
    grid.add_bus(bus2_ac)
    grid.add_bus(bus3_dc)

    gen1 = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    transformer = gce.Transformer2W(name="Transformer", bus_from=bus1_ac, bus_to=bus2_ac, rate=100.0, r=0.01, x=0.1, tap_module=1.0, tap_phase=0.0)

    p_transfer_mw = 30.0
    q_transfer_mvar = 0.0
    vsc = gce.VSC(name="VSC", bus_from=bus3_dc, bus_to=bus2_ac, rate=100.0, control1=ConverterControlType.Qac, control2=ConverterControlType.Vm_dc, control1_val=q_transfer_mvar, control2_val=1.0)

    dc_load = gce.Load(name="DC_Load", P=p_transfer_mw, Q=0.0)

    grid.add_generator(bus1_ac, gen1)
    grid.add_transformer2w(transformer)
    grid.add_vsc(vsc)
    grid.add_load(bus3_dc, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    trafo_templ = get_transformer_emt_template(vf=grid.var_factory, name=transformer.name)
    trafo_mdl = trafo_templ.block.children[0]
    vsc_mdl = get_emt_ideal_converter(
        vf=grid.var_factory,
        name=vsc.name,
    ).block
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt").block

    set_emt_model(device=gen1, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=transformer, model=trafo_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    # Should NOT raise EmtTopologyError - this is a valid topology
    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None


def _find_name_in_block(name: str, block: Block) -> Var | None:
    """
    Return one symbolic variable from a block hierarchy by name.

    :param name: Requested symbolic-variable name.
    :param block: Root symbolic block.
    :return: Matching variable or ``None``.
    """
    variable: Var
    child_block: Block
    nested_result: Var | None

    for variable_list in [block.in_vars, block.out_vars, block.algebraic_vars, block.state_vars, block.diff_vars]:
        for variable in variable_list:
            if variable.name == name:
                return variable
            else:
                pass

    for variable in list(block.event_dict.keys()):
        if variable.name == name:
            return variable
        else:
            pass

    for child_block in block.children:
        nested_result = _find_name_in_block(name, child_block)
        if nested_result is not None:
            return nested_result
        else:
            pass

    return None


def _build_switched_vsc_validation_problem(options=None, configure_template=None) -> EmtProblemDae:
    """Build the same PF operating point for averaged and direct-PWM checks."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus1_ac = gce.Bus(name="Bus1_AC", Vnom=230.0, is_slack=True)
    bus2_ac = gce.Bus(name="Bus2_AC", Vnom=230.0)
    bus3_dc = gce.Bus(name="Bus3_DC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus1_ac)
    grid.add_bus(bus2_ac)
    grid.add_bus(bus3_dc)

    gen1 = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    transformer = gce.Transformer2W(name="Transformer", bus_from=bus1_ac, bus_to=bus2_ac, rate=100.0, r=0.01, x=0.1, tap_module=1.0, tap_phase=0.0)
    vsc = gce.VSC(name="VSC", bus_from=bus3_dc, bus_to=bus2_ac, rate=100.0, control1=ConverterControlType.Qac, control2=ConverterControlType.Vm_dc, control1_val=0.0, control2_val=1.0)
    dc_load = gce.Load(name="DC_Load", P=30.0, Q=0.0)

    grid.add_generator(bus1_ac, gen1)
    grid.add_transformer2w(transformer)
    grid.add_vsc(vsc)
    grid.add_load(bus3_dc, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        retry_with_other_methods=False,
        max_iter=25,
        tolerance=1e-10,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        orthogonalize_controls=False,
    )
    pf_results = gce.power_flow(grid=grid, options=pf_options)
    pf_res_3ph = None

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    trafo_templ = get_transformer_emt_template(vf=grid.var_factory, name=transformer.name)
    trafo_mdl = trafo_templ.block.children[0]
    vsc_mdl = get_switched_emt_converter(vf=grid.var_factory, name=vsc.name).block
    if configure_template is not None:
        configure_template(vsc_mdl)
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt_switched").block

    set_emt_model(device=gen1, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=transformer, model=trafo_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    switched_options = get_switched_converter_emt_options() if options is None else options
    problem = EmtProblemDae(grid=grid, options=switched_options, pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    return problem


def test_switched_vsc_emt_passes_validation_and_switches_gates() -> None:
    """Verify the VSC network initialization and averaged-to-PWM handover."""
    problem = _build_switched_vsc_validation_problem()
    switched_options = problem.options
    vsc = problem.grid.vsc_devices[0]
    assert problem is not None

    gate_a_var = _find_name_in_block("gate_a", vsc.emt_model)
    gate_b_var = _find_name_in_block("gate_b", vsc.emt_model)
    gate_c_var = _find_name_in_block("gate_c", vsc.emt_model)
    i_A_var = _find_name_in_block("i_A", vsc.emt_model)
    i_B_var = _find_name_in_block("i_B", vsc.emt_model)
    i_C_var = _find_name_in_block("i_C", vsc.emt_model)
    v_dc_var = _find_name_in_block("v_dc", vsc.emt_model)
    p_var = _find_name_in_block("P", vsc.emt_model)
    p_f_var = _find_name_in_block("P_f", vsc.emt_model)
    i_d_var = _find_name_in_block("i_d", vsc.emt_model)
    i_d_ref_var = _find_name_in_block("i_d_ref", vsc.emt_model)

    assert gate_a_var is not None
    assert gate_b_var is not None
    assert gate_c_var is not None
    assert i_A_var is not None
    assert i_B_var is not None
    assert i_C_var is not None
    assert v_dc_var is not None
    assert p_var is not None
    assert p_f_var is not None
    assert i_d_var is not None
    assert i_d_ref_var is not None
    assert problem.initialization_report is not None
    assert problem.initialization_report.method_requested == EmtInitializationMethod.Explicit
    assert problem.initialization_report.method_used == EmtInitializationMethod.Explicit
    assert str(problem.initialization_report.status.name) == "RESOLVED"
    assert problem.initialization_report.final_residual_inf < 1e-7

    problem.reset_boundary_update_state(0.0)
    x0 = problem.get_x0()
    assert x0[problem.get_var_idx(p_var)] > 0.0
    assert np.isclose(
        x0[problem.get_var_idx(p_var)],
        x0[problem.get_var_idx(p_f_var)],
        atol=1e-9,
    )
    assert np.isclose(
        x0[problem.get_var_idx(i_d_var)],
        x0[problem.get_var_idx(i_d_ref_var)],
        atol=1e-6,
    )
    initial_derivatives = {
        variable.name: problem.get_dx0()[problem.get_diff_var_idx(variable)]
        for variable in problem.get_diff_vars()
    }
    assert abs(initial_derivatives["d_v_dc"]) < 1e-8
    assert abs(initial_derivatives["d_xi_vdc"]) < 1e-8
    runtime_values = problem.event_params_values.copy()
    constant_values = np.asarray([const.value for const in problem.get_parameters_values()], dtype=float)
    full_params = np.concatenate((runtime_values, constant_values))
    runtime_mode_map = {var.name: var for var in problem.get_runtime_mode_parameters()}
    gate_a_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_a_mode"].uid]
    gate_b_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_b_mode"].uid]
    gate_c_mode_idx = problem.uid2idx_event_params[runtime_mode_map["gate_c_mode"].uid]
    switching_enabled_idx = problem.uid2idx_event_params[runtime_mode_map["switching_enabled_mode"].uid]
    gate_a_trace = list()
    gate_b_trace = list()
    gate_c_trace = list()

    for time_s in np.linspace(0.0, switched_options.simulation_time, 1201):
        problem.emt_boundary_update(float(time_s), x0.copy(), full_params)
        gate_a_trace.append(float(full_params[gate_a_mode_idx]))
        gate_b_trace.append(float(full_params[gate_b_mode_idx]))
        gate_c_trace.append(float(full_params[gate_c_mode_idx]))

    assert float(full_params[switching_enabled_idx]) > 0.5
    assert float(np.max(np.asarray(gate_a_trace)) - np.min(np.asarray(gate_a_trace))) > 0.5
    assert float(np.max(np.asarray(gate_b_trace)) - np.min(np.asarray(gate_b_trace))) > 0.5
    assert float(np.max(np.asarray(gate_c_trace)) - np.min(np.asarray(gate_c_trace))) > 0.5
    assert np.isfinite(float(x0[problem.get_var_idx(v_dc_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_A_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_B_var)]))
    assert np.isfinite(float(x0[problem.get_var_idx(i_C_var)]))

    solver = JitSymbolicSolver(
        problem=problem,
        t0=0.0,
        t_end=switched_options.simulation_time,
        h=switched_options.time_step,
        method=switched_options.integration_method,
        pred_method=DynamicIntegrationMethod.OdeEuler,
        dense_threshold=0,
        verbose=False,
    )
    time, trajectory, derivatives, well_initialized, converged = solver.simulate(
        boundary_updater=problem
    )
    assert well_initialized
    assert converged
    pre_handover = time <= 9.0e-5
    v_dc_idx = problem.get_var_idx(v_dc_var)
    assert np.max(np.abs(trajectory[pre_handover, v_dc_idx] - x0[v_dc_idx])) < 1e-6
    i_d_idx = problem.get_var_idx(i_d_var)
    assert np.max(np.abs(trajectory[pre_handover, i_d_idx] - x0[i_d_idx])) < 1e-3
    switching_blend_var = _find_name_in_block("switching_blend", vsc.emt_model)
    assert switching_blend_var is not None
    i_ki_effective_var = _find_name_in_block("i_ki_effective", vsc.emt_model)
    assert i_ki_effective_var is not None
    assert np.isclose(x0[problem.get_var_idx(i_ki_effective_var)], 4.0)
    # The handover reaches a majority switched contribution within the
    # configured carrier period, rather than using a fixed 5 ms ramp.
    assert trajectory[-1, problem.get_var_idx(switching_blend_var)] > 0.5
    assert trajectory[-1, problem.get_var_idx(i_ki_effective_var)] > 20.0
    for variable in (v_dc_var, i_A_var, i_B_var, i_C_var):
        assert np.all(np.isfinite(trajectory[:, problem.get_var_idx(variable)]))
    assert np.all(np.isfinite(derivatives))


@pytest.mark.parametrize("method", [DynamicIntegrationMethod.DaeBackEuler,
                                    DynamicIntegrationMethod.DaeTrapezoidal])
def test_switched_vsc_direct_pwm_has_no_initial_current_offset(method) -> None:
    """A PF current seed must start a symmetric PWM interval without a DC offset."""
    from VeraGridEngine.Utils.Symbolic.symbolic import Const

    def direct_pwm(block):
        for item in block.get_all_blocks():
            for variable in item.event_dict:
                if variable.name == "omega_sw":
                    item.event_dict[variable] = Const(2.0 * np.pi * 10000.0)
            for variable in item.mode_dict:
                if variable.name == "switching_enabled_mode":
                    item.mode_dict[variable] = Const(1.0)
                elif variable.name == "omega_sw_eff":
                    item.mode_dict[variable] = Const(2.0 * np.pi * 10000.0)
            for variable in item.init_eqs:
                if variable.name == "switching_blend":
                    item.init_eqs[variable] = Const(1.0)
            item.procedural_logic = [entry for entry in item.procedural_logic
                                     if entry.name not in ("startup_handover", "startup_carrier_handover")]

    options = get_switched_converter_emt_options()
    options.integration_method = method
    options.simulation_time = 0.5e-3
    options.time_step = 1e-6
    problem = _build_switched_vsc_validation_problem(options, direct_pwm)
    solver = JitSymbolicSolver(
        problem=problem, t0=0.0, t_end=options.simulation_time, h=options.time_step,
        method=options.integration_method, pred_method=DynamicIntegrationMethod.OdeEuler,
        dense_threshold=0, verbose=False,
    )
    t, y, _, initialized, converged = solver.simulate(boundary_updater=problem)
    assert initialized and converged
    assert solver.get_last_runtime_stats()["failed_substeps"] == 0
    model = problem.grid.vsc_devices[0].emt_model
    iq = problem.get_var_idx(_find_name_in_block("i_q", model))
    id_ = problem.get_var_idx(_find_name_in_block("i_d", model))
    for cycle in range(5):
        mask = (t >= cycle * 1e-4 - 1e-12) & (t < (cycle + 1) * 1e-4 - 1e-12)
        assert abs(np.mean(y[mask, iq])) < 3e-4
        assert abs(np.mean(y[mask, id_]) - y[0, id_]) < 3e-4


def test_set_emt_model_connects_dc_line_terminal_voltages():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus_from_dc = gce.Bus(name="BusFromDC", Vnom=320.0, is_dc=True)
    bus_to_dc = gce.Bus(name="BusToDC", Vnom=320.0, is_dc=True)
    grid.add_bus(bus_from_dc)
    grid.add_bus(bus_to_dc)

    get_bus_emt_template(grid, bus_from_dc)
    get_bus_emt_template(grid, bus_to_dc)

    dc_line = gce.DcLine(name="DC_Line", bus_from=bus_from_dc, bus_to=bus_to_dc, r=0.02, rate=100.0)
    line_mdl = get_dc_line_emt_template(vf=grid.var_factory, name=dc_line.name).block

    set_emt_model(device=dc_line, model=line_mdl, var_factory=grid.var_factory)

    assert dc_line.emt_model.E(VarPowerFlowReferenceType.Vf_dc).uid == bus_from_dc.emt_model.E(VarPowerFlowReferenceType.Vdc).uid
    assert dc_line.emt_model.E(VarPowerFlowReferenceType.Vt_dc).uid == bus_to_dc.emt_model.E(VarPowerFlowReferenceType.Vdc).uid


def test_dc_line_emt_passes_validation_and_initializes_branch_currents():
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)

    bus_ac = gce.Bus(name="Bus_AC", Vnom=230.0, is_slack=True)
    bus_dc_from = gce.Bus(name="Bus_DC_From", Vnom=320.0, is_dc=True)
    bus_dc_to = gce.Bus(name="Bus_DC_To", Vnom=320.0, is_dc=True)
    grid.add_bus(bus_ac)
    grid.add_bus(bus_dc_from)
    grid.add_bus(bus_dc_to)

    gen = gce.Generator(name="Generator", vset=1.0, Snom=100.0, freq=50.0, r1=0.001, x1=0.4)
    vsc = gce.VSC(
        name="VSC",
        bus_from=bus_dc_from,
        bus_to=bus_ac,
        rate=100.0,
        control1=ConverterControlType.Qac,
        control2=ConverterControlType.Vm_dc,
        control1_val=0.0,
        control2_val=1.0,
    )
    dc_line = gce.DcLine(name="DC_Line", bus_from=bus_dc_from, bus_to=bus_dc_to, r=0.02, rate=100.0)
    dc_load = gce.Load(name="DC_Load", P=30.0, Q=0.0)

    grid.add_generator(bus_ac, gen)
    grid.add_vsc(vsc)
    grid.add_dc_line(dc_line)
    grid.add_load(bus_dc_to, dc_load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    vsc_mdl = get_emt_ideal_converter(vf=grid.var_factory, name=vsc.name).block
    dc_line_mdl = get_dc_line_emt_template(vf=grid.var_factory, name=dc_line.name).block
    dc_load_mdl = get_dc_load_emt_template(vf=grid.var_factory, name="dc_load_emt").block

    set_emt_model(device=gen, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_line, model=dc_line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=dc_load, model=dc_load_mdl, var_factory=grid.var_factory)

    problem = EmtProblemDae(grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph)
    assert problem is not None

    if_dc_var = dc_line.emt_model.E(VarPowerFlowReferenceType.If_dc)
    it_dc_var = dc_line.emt_model.E(VarPowerFlowReferenceType.It_dc)

    assert if_dc_var is not None
    assert it_dc_var is not None
    assert if_dc_var.uid in problem.init_guess
    assert it_dc_var.uid in problem.init_guess
    assert abs(problem.init_guess[if_dc_var.uid] + problem.init_guess[it_dc_var.uid]) < 1e-9


# =============================================================================
# TEST 4: scripting_example_validate_connections_phases
# A single-phase load does not disconnect the other source-fed line phases
# =============================================================================

def test_single_phase_load_on_three_phase_line_preserves_unloaded_phase_kcl() -> None:
    """Accept source-fed unloaded phases and retain their line-terminal KCL.

    :return: None.
    """
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    vnom = 10

    bus0 = gce.Bus(name="Bus0", Vnom=vnom, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=vnom)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10, rate=900.0)

    tower = gce.OverheadLineType(name="Tower", Vnom=vnom)
    wire = gce.Wire(name="Panther 30/7 ACSR", diameter=21.0, diameter_internal=9.0, is_tube=True, r=0.1363, max_current=1)
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    v_ph = vnom / (3**0.5)
    R_ph = 100
    P_ph = (v_ph**2) / R_ph
    Q_ph = 0.0
    load = gce.Load(name="load", P=3.0*P_ph, Q=3.0*Q_ph, P1=P_ph, P2=P_ph, P3=P_ph, Q1=Q_ph, Q2=Q_ph, Q3=Q_ph)
    load.conn = ShuntConnectionType.GroundedStar

    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50, r1=0.001, x1=1.7)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    for bus in grid.buses:
        get_bus_emt_template(grid, bus)

    pf_results, pf_res_3ph = run_power_flow(grid)

    gen_mdl = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory).block
    line_mdl = get_pi_line_emt_template(vf = grid.var_factory, phN = False, phA = True, phB = True, phC = True).block
    # The other two phases remain connected to the source through the line.
    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=False, phC=False).block


    set_emt_model(device=gen0, model=gen_mdl, var_factory=grid.var_factory)
    set_emt_model(device=line0, model=line_mdl, var_factory=grid.var_factory)
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    # Exercise normal production construction, then inspect its nodal equations.
    problem: EmtProblemDae = EmtProblemDae(
        grid=grid, options=get_default_emt_options(), pf_results=pf_results, pf_results_3ph=pf_res_3ph,
    )
    assert np.all(np.isfinite(problem.get_x0()))
    phase_reference: VarPowerFlowReferenceType
    for phase_reference in (VarPowerFlowReferenceType.it_B, VarPowerFlowReferenceType.it_C):
        line_current: Var | None = line0.emt_model.external_mapping.get(phase_reference, None)
        assert line_current is not None
        terminal_kcl: list[Expr] = list(
            equation for equation in problem.get_algebraic_eqs()
            if set(variable.uid for variable in get_expression_vars(equation)) == set((line_current.uid,))
        )
        assert len(terminal_kcl) == 1
        assert terminal_kcl[0].eval_uid(dict(((line_current.uid, 1.0),))) == -1.0


def test_interface_validation_accepts_compatible_ac_abc_injection() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABC", Vnom=20.0)
    load = gce.Load(name="LoadABC", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_abc")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ], "load_abc")

    problem = _build_interface_validation_problem(grid)
    problem._validate_dynamic_emt_interfaces()


def test_interface_validation_ignores_dormant_neutral_mapping_outside_root_contract() -> None:
    """
    Dormant neutral mappings must not make one active ABC model expose neutral.

    :return: None.
    """
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABC", Vnom=20.0)
    load = gce.Load(name="LoadWithDormantNeutral", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_abc_dormant")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ], "load_abc_dormant")
    load.emt_model.external_mapping[VarPowerFlowReferenceType.v_N] = _make_ref_var(
        VarPowerFlowReferenceType.v_N,
        "load_dormant_neutral",
    )
    load.emt_model.external_mapping[VarPowerFlowReferenceType.i_N] = _make_ref_var(
        VarPowerFlowReferenceType.i_N,
        "load_dormant_neutral",
    )

    problem = _build_interface_validation_problem(grid)
    problem._validate_dynamic_emt_interfaces()


def test_interface_validation_accepts_compatible_ac_abcn_injection() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABCN", Vnom=20.0)
    load = gce.Load(name="LoadABCN", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_abcn")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ], "load_abcn")

    problem = _build_interface_validation_problem(grid)
    problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_neutral_without_bus_support() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusNoNeutral", Vnom=20.0)
    load = gce.Load(name="LoadNeutral", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_noneutral")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
    ], "load_noneutral")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="BusNoNeutral"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_dc_refs_on_ac_bus() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="AcBus", Vnom=20.0)
    load = gce.Load(name="DcStyledLoad", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "ac_bus")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Idc,
    ], "dc_load_on_ac")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="DC"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_ac_refs_on_dc_bus() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="DcBus", Vnom=320.0, is_dc=True)
    load = gce.Load(name="AcStyledLoad", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.Vdc,
    ], "dc_bus")
    load.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.i_A,
    ], "ac_load_on_dc")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="AC phase"):
        problem._validate_dynamic_emt_interfaces()


def test_interface_validation_rejects_shared_dc_branch_collision() -> None:
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_from = gce.Bus(name="DcFrom", Vnom=320.0, is_dc=True)
    bus_to = gce.Bus(name="DcTo", Vnom=320.0, is_dc=True)
    dc_line = gce.DcLine(name="SharedDcBranch", bus_from=bus_from, bus_to=bus_to, r=0.01, rate=100.0)
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    grid.add_dc_line(dc_line)

    bus_from.emt_model = _make_external_mapping_block([VarPowerFlowReferenceType.Vdc], "dc_from")
    bus_to.emt_model = _make_external_mapping_block([VarPowerFlowReferenceType.Vdc], "dc_to")
    dc_line.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Idc,
    ], "shared_dc_branch")

    problem = _build_interface_validation_problem(grid)

    with pytest.raises(EmtInterfaceValidationError, match="Use If_dc and It_dc instead"):
        problem._validate_dynamic_emt_interfaces()


def test_set_emt_model_connects_single_bus_ac_injection_refs() -> None:
    """Single-bus AC EMT injections must bind their voltage inputs to the bus shell."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusABC", Vnom=20.0)
    load = gce.Load(name="LoadABC", P=10.0, Q=1.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
    ], "bus_connect_abc")

    load_mdl = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True).block
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid == bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid == bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid == bus.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid


def test_set_emt_model_connects_single_bus_dc_injection_refs() -> None:
    """Single-bus DC EMT injections must bind their DC input to the bus shell."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus = gce.Bus(name="BusDC", Vnom=320.0, is_dc=True)
    load = gce.Load(name="LoadDC", P=10.0, Q=0.0)
    grid.add_bus(bus)
    grid.add_load(bus, load)

    bus.emt_model = _make_external_mapping_block([
        VarPowerFlowReferenceType.Vdc,
    ], "bus_connect_dc")

    load_mdl = get_dc_load_emt_template(vf=grid.var_factory).block
    set_emt_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.Vdc].uid == bus.emt_model.external_mapping[VarPowerFlowReferenceType.Vdc].uid


def test_set_emt_model_connects_ac_branch_terminal_voltages() -> None:
    """AC branch EMT models must bind their terminal voltages to both bus shells."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_from = gce.Bus(name="BusFrom", Vnom=20.0)
    bus_to = gce.Bus(name="BusTo", Vnom=20.0)
    line = gce.Line(name="LineABC", bus_from=bus_from, bus_to=bus_to, r=0.01, x=0.1, b=0.0, rate=100.0)
    grid.add_bus(bus_from)
    grid.add_bus(bus_to)
    grid.add_line(line)

    get_bus_emt_template(grid=grid, bus=bus_from)
    get_bus_emt_template(grid=grid, bus=bus_to)

    line_mdl = get_pi_line_emt_template(vf=grid.var_factory, phN=False, phA=True, phB=True, phC=True).block
    set_emt_model(device=line, model=line_mdl, var_factory=grid.var_factory)

    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vf_A].uid == bus_from.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vf_B].uid == bus_from.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vf_C].uid == bus_from.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid
    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vt_A].uid == bus_to.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vt_B].uid == bus_to.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert line.emt_model.external_mapping[VarPowerFlowReferenceType.vt_C].uid == bus_to.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid


def test_set_emt_model_connects_vsc_terminal_voltages() -> None:
    """VSC EMT models must bind DC and AC terminal voltages to their bus shells."""
    grid = gce.MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_dc = gce.Bus(name="BusDC", Vnom=320.0, is_dc=True)
    bus_ac = gce.Bus(name="BusAC", Vnom=20.0)
    vsc = gce.VSC(name="VSCConnect", bus_from=bus_dc, bus_to=bus_ac, rate=100.0,
                  control1=ConverterControlType.Vm_ac, control2=ConverterControlType.Va_ac,
                  control1_val=1.0, control2_val=0.0)
    grid.add_bus(bus_dc)
    grid.add_bus(bus_ac)
    grid.add_vsc(vsc)

    get_bus_emt_template(grid=grid, bus=bus_dc)
    get_bus_emt_template(grid=grid, bus=bus_ac)

    vsc_mdl = get_emt_ideal_converter(vf=grid.var_factory, name=vsc.name).block
    set_emt_model(device=vsc, model=vsc_mdl, var_factory=grid.var_factory)

    assert vsc.emt_model.external_mapping[VarPowerFlowReferenceType.Vdc].uid == bus_dc.emt_model.external_mapping[VarPowerFlowReferenceType.Vdc].uid
    assert vsc.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid == bus_ac.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert vsc.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid == bus_ac.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert vsc.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid == bus_ac.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid


def test_emt_template_setter_requires_bus_shells_before_gui_order_assignment() -> None:
    """The GUI EMT template setter must require bus shells before EMT assignment order."""
    grid = gce.MultiCircuit(Sbase=2.0, fbase=50.0)
    bus0 = gce.Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10.0)
    grid.add_bus(bus0)
    grid.add_bus(bus1)

    line0 = gce.Line(name="line0", bus_from=bus0, bus_to=bus1, length=10.0, rate=900.0)
    load = gce.Load(name="load", P=10.0, Q=1.0)
    gen0 = gce.Generator(name="Gen0", vset=1.0, Snom=grid.Sbase, freq=50.0, r1=0.001, x1=1.7)

    tower = gce.OverheadLineType(name="Tower", Vnom=10.0)
    wire = gce.Wire(
        name="Panther 30/7 ACSR",
        diameter=21.0,
        diameter_internal=9.0,
        is_tube=True,
        r=0.1363,
        max_current=1,
    )
    tower.add_wire_relationship(wire=wire, xpos=-12.65, ypos=27.5, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0.0, ypos=27.5, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=12.65, ypos=27.5, phase=3)
    tower.compute()
    line0.apply_template(tower, grid.Sbase, grid.fBase)

    grid.add_line(line0)
    grid.add_generator(bus=bus0, api_obj=gen0)
    grid.add_load(bus=bus1, api_obj=load)

    get_bus_emt_template(grid=grid, bus=bus0)
    get_bus_emt_template(grid=grid, bus=bus1)

    gen0.emt_template = get_generator_thevenin_rl_emt_template_with_ref(vf=grid.var_factory)
    assert not gen0.emt_model.empty()
    assert len(bus0.get_pending_emt_devices()) == 0
    assert not bus0.emt_model.empty()

    line0.emt_template = get_pi_line_emt_template(vf=grid.var_factory, phN=False, phA=True, phB=True, phC=True)
    load.emt_template = get_shunt_r_emt_template(vf=grid.var_factory, phA=True, phB=True, phC=True)

    assert len(bus0.get_pending_emt_devices()) == 0
    assert len(bus1.get_pending_emt_devices()) == 0
    assert not line0.emt_model.empty()
    assert not load.emt_model.empty()

    assert gen0.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid == bus0.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert gen0.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid == bus0.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert gen0.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid == bus0.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid
    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid == bus1.emt_model.external_mapping[VarPowerFlowReferenceType.v_A].uid
    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid == bus1.emt_model.external_mapping[VarPowerFlowReferenceType.v_B].uid
    assert load.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid == bus1.emt_model.external_mapping[VarPowerFlowReferenceType.v_C].uid
