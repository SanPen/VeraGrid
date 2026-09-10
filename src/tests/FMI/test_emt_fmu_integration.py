from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.fmu.exporter.build import host_build_capable
from VeraGridEngine.IO.fmu.exporter.compat import Block, Var
from VeraGridEngine.IO.fmu.importer.bindings import FmuRefBinding
from VeraGridEngine.IO.fmu.importer.model_description import FmuInterfaceMode
from VeraGridEngine.IO.fmu.importer.user_api import (
    FmuDeviceAttachmentRequest,
    FmuDeviceDomain,
    FmuReferenceValue,
    attach_fmu_to_device,
)
from VeraGridEngine.Simulations.EMT.emt_driver import EmtSimulationDriver
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.enumerations import (
    DynamicIntegrationMethod,
    EmtInitializationMethod,
    EmtSolverTypes,
    VarPowerFlowReferenceType,
)
from tests.FMI.fmi_test_support import (
    build_test_emt_grid,
    build_test_power_flow_options,
    execute_test_emt_fmu_case,
    export_test_emt_cs_fmu,
)


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_emt_fmu_co_simulation_runs_end_to_end(tmp_path: Path) -> None:
    """Exercise EMT Co-Simulation through the complete product integration path.

    :param tmp_path: Isolated FMU and native staging directory supplied by pytest.
    :return: None.
    """

    pytest.importorskip("fmpy")
    driver: EmtSimulationDriver
    load: Load
    fmu_path: Path
    driver, load, fmu_path = execute_test_emt_fmu_case(
        tmp_path,
        FmuInterfaceMode.CO_SIMULATION,
    )

    if driver.results is None:
        raise AssertionError("The EMT Co-Simulation case did not publish results")
    else:
        results: EmtResults = driver.results
    available_group_indices: np.ndarray = np.flatnonzero(
        results.has_event_group_results
    )
    assert available_group_indices.size == 1
    group_index: int = int(available_group_indices[0])
    assert bool(results.well_initialized[group_index])
    assert bool(results.converged[group_index])
    assert float(results.time_array[-1].value) * 1.0e-9 == pytest.approx(1.0e-3)

    i_a_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_A]
    i_b_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_B]
    i_c_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_C]
    final_currents: np.ndarray = np.array(
        [
            results.values[-1, results.uid2idx[i_a_var.uid], group_index],
            results.values[-1, results.uid2idx[i_b_var.uid], group_index],
            results.values[-1, results.uid2idx[i_c_var.uid], group_index],
        ],
        dtype=float,
    )
    assert bool(np.all(np.isfinite(final_currents)))
    assert float(np.max(np.abs(final_currents))) >= 1.0e-8
    assert abs(float(np.sum(final_currents))) <= 1.0e-6
    assert fmu_path.exists()
    assert tuple(tmp_path.glob("veragrid_fmu_stage_*")) == tuple()


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
@pytest.mark.parametrize("solver_tpe", tuple(EmtSolverTypes))
def test_emt_fmu_model_exchange_runs_end_to_end(
    tmp_path: Path,
    solver_tpe: EmtSolverTypes,
) -> None:
    """Exercise EMT Model Exchange through the complete product integration path.

    :param tmp_path: Isolated FMU and native staging directory supplied by pytest.
    :param solver_tpe: EMT Jacobian backend under test.
    :return: None.
    """

    pytest.importorskip("fmpy")
    driver: EmtSimulationDriver
    load: Load
    fmu_path: Path
    driver, load, fmu_path = execute_test_emt_fmu_case(
        tmp_path,
        FmuInterfaceMode.MODEL_EXCHANGE,
        solver_tpe,
    )

    if driver.results is None:
        raise AssertionError("The EMT Model Exchange case did not publish results")
    else:
        results: EmtResults = driver.results
    available_group_indices: np.ndarray = np.flatnonzero(
        results.has_event_group_results
    )
    assert available_group_indices.size == 1
    group_index: int = int(available_group_indices[0])
    assert bool(results.well_initialized[group_index])
    assert bool(results.converged[group_index])
    assert float(results.time_array[-1].value) * 1.0e-9 == pytest.approx(1.0e-3)

    i_a_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_A]
    i_b_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_B]
    i_c_var: Var = load.emt_model.external_mapping[VarPowerFlowReferenceType.i_C]
    final_currents: np.ndarray = np.array(
        [
            results.values[-1, results.uid2idx[i_a_var.uid], group_index],
            results.values[-1, results.uid2idx[i_b_var.uid], group_index],
            results.values[-1, results.uid2idx[i_c_var.uid], group_index],
        ],
        dtype=float,
    )
    assert bool(np.all(np.isfinite(final_currents)))
    assert float(np.max(np.abs(final_currents))) >= 1.0e-8
    assert abs(float(np.sum(final_currents))) <= 1.0e-6

    attached_block: Block = load.emt_model
    copied_block: Block = attached_block.copy()
    candidate_blocks: tuple[Block, Block] = (attached_block, copied_block)
    candidate_block: Block
    reference: VarPowerFlowReferenceType
    for candidate_block in candidate_blocks:
        for reference in (
            VarPowerFlowReferenceType.v_A,
            VarPowerFlowReferenceType.v_B,
            VarPowerFlowReferenceType.v_C,
        ):
            input_var: Var | None = candidate_block.external_mapping.get(
                reference,
                None,
            )
            matching_input_vars: list[Var] = list(
                candidate_var
                for candidate_var in candidate_block.in_vars
                if candidate_var.ref == reference
            )
            assert input_var is not None
            assert len(matching_input_vars) == 1
            assert input_var is matching_input_vars[0]
            assert input_var.ref == reference

    assert fmu_path.exists()
    assert tuple(tmp_path.glob("veragrid_fmu_stage_*")) == tuple()


@pytest.mark.skipif(not host_build_capable(), reason="No usable host build toolchain available")
def test_emt_driver_releases_native_runtime_after_failed_solve(tmp_path: Path) -> None:
    """Prove driver-owned native runtimes close after a failed EMT solve.

    :param tmp_path: Isolated FMU and staging directory supplied by pytest.
    :return: None.
    """

    pytest.importorskip("fmpy")
    fmu_path: Path = export_test_emt_cs_fmu(tmp_path)
    grid: MultiCircuit
    load: Load
    grid, load = build_test_emt_grid()
    grid.add_emt_events_group(
        EmtEventsGroup(name="failed_native_cleanup_group")
    )

    power_flow_driver: PowerFlowDriver = PowerFlowDriver(
        grid=grid,
        options=build_test_power_flow_options(),
    )
    power_flow_driver.run()
    request: FmuDeviceAttachmentRequest = FmuDeviceAttachmentRequest(
        fmu_path=fmu_path,
        domain=FmuDeviceDomain.EMT,
        mode=FmuInterfaceMode.CO_SIMULATION,
        input_bindings=(
            FmuRefBinding(VarPowerFlowReferenceType.v_A, "v_a_in"),
            FmuRefBinding(VarPowerFlowReferenceType.v_B, "v_b_in"),
            FmuRefBinding(VarPowerFlowReferenceType.v_C, "v_c_in"),
        ),
        output_bindings=(
            FmuRefBinding(VarPowerFlowReferenceType.i_A, "i_a_out"),
            FmuRefBinding(VarPowerFlowReferenceType.i_B, "i_b_out"),
            FmuRefBinding(VarPowerFlowReferenceType.i_C, "i_c_out"),
        ),
        output_defaults=(
            FmuReferenceValue(VarPowerFlowReferenceType.i_A, 0.0),
            FmuReferenceValue(VarPowerFlowReferenceType.i_B, 0.0),
            FmuReferenceValue(VarPowerFlowReferenceType.i_C, 0.0),
        ),
        extraction_root=tmp_path,
    )
    attached_block: Block = attach_fmu_to_device(load, grid, request)
    assert attached_block is load.emt_model

    # Zero initialization iterations deliberately fails only after the real
    # boundary runtime has opened, exercising driver-owned cleanup.
    emt_driver: EmtSimulationDriver = EmtSimulationDriver(
        grid=grid,
        options=EmtOptions(
            time_step=5.0e-6,
            simulation_time=1.0e-3,
            tolerance=1.0e-6,
            solver_type=EmtSolverTypes.Symbolic,
            integration_method=DynamicIntegrationMethod.DaeTrapezoidal,
            initialization_method=EmtInitializationMethod.ConsistentNewton,
            init_newton_max_iter=0,
            verbose=0,
        ),
        pf_results=power_flow_driver.results,
        pf_results_3ph=None,
    )
    emt_driver.run()

    if emt_driver.results is None:
        raise AssertionError("The failed EMT solve did not publish its status")
    else:
        assert not bool(emt_driver.results.well_initialized[0])
        assert not bool(emt_driver.results.converged[0])
    assert fmu_path.exists()
    assert tuple(tmp_path.glob("veragrid_fmu_stage_*")) == tuple()
