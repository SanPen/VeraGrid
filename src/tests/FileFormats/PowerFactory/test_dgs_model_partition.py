# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check deterministic DGS ownership and cross-device symbolic connections."""
from __future__ import annotations

from pathlib import Path

import pytest
import numpy as np
import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Templates.Rms.common.voltage_source_template import build_thevenin_voltage_source
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model

from VeraGridEngine.Devices.Dynamic.model_interconnections import get_interconnection_variables
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_to_veragrid import dgs_to_circuit
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import build_dgs_elmgenstat_voltage_block
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkSlot, BlkSig, ElmComp, ElmDsl, ElmGenstat
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import DynamicModelImport, DgsDynamicTemplateConversionResult
from VeraGridEngine.IO.dgs.dynamic_models.dgs_model_partition import DgsModelPartition
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from scipy.sparse import csc_matrix
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import BlockType, DynamicSimulationMode, ParamPowerFlowReferenceType


def make_partition_fixture() -> tuple[DgsCircuit, MultiCircuit, DynamicModelImport]:
    """Build two current-controlled natives with one shared state controller.

    :return: Source DGS, destination circuit and importer.
    """
    dgs: DgsCircuit = DgsCircuit()
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Bus", idtag="bus", Vnom=110.0, is_slack=True)
    grid.add_bus(bus)
    initialize_bus_rms(bus, grid.var_factory)
    frame: BlkDef = BlkDef()
    frame.ID = "frame"
    frame.loc_name = "Composite"
    dgs.blkdefs.append(frame)
    root: ElmComp = ElmComp()
    root.ID = "root"
    root.loc_name = "Composite"
    root.typ_id = frame.ID
    dgs.elmcomps.append(root)
    definitions: tuple = (
        ("shared", list(), list(("s",)), list(("x",)), list(("inc(x)=0", "x.=1", "s=x"))),
        ("first", list(("a",)), list(("d1", "q1")), list(), list(("d1=0.01*a", "q1=0"))),
        ("second", list(("b",)), list(("d2", "q2")), list(), list(("d2=0.02*b", "q2=0"))),
    )
    name: str
    inputs: list[str]
    outputs: list[str]
    states: list[str]
    equations: list[str]
    for name, inputs, outputs, states, equations in definitions:
        definition: BlkDef = BlkDef()
        definition.ID = f"type_{name}"
        definition.loc_name = name
        definition.inputs = inputs
        definition.outputs = outputs
        definition.states = states
        definition.equations_raw = equations
        dgs.blkdefs.append(definition)
        instance: ElmDsl = ElmDsl()
        instance.ID = f"instance_{name}"
        instance.loc_name = name
        instance.typ_id = definition.ID
        instance.fold_id = root.ID
        dgs.elmdsls.append(instance)
        slot: BlkSlot = BlkSlot()
        slot.ID = name
        slot.loc_name = name
        slot.filtmod = "ElmDsl*"
        slot.inputs = inputs
        slot.outputs = outputs
        dgs.blkslots.append(slot)
        root.pblk.append(slot.ID)
        root.pelm.append(instance.ID)
    host_id: str
    for host_id in ("100", "200"):
        source: ElmGenstat = ElmGenstat()
        source.ID = host_id
        source.loc_name = f"Host {host_id}"
        source.c_pmod = root.ID
        source.sgn = 100.0
        dgs.elmgenstats.append(source)
        host: Generator = Generator(name=source.loc_name, idtag=host_id, P=0.0, Snom=100.0)
        grid.add_generator(bus, host)
        slot = BlkSlot()
        slot.ID = f"native_{host_id}"
        slot.loc_name = slot.ID
        slot.filtmod = "ElmGenstat*"
        slot.inputs = list(("idref", "iqref"))
        dgs.blkslots.append(slot)
        root.pblk.append(slot.ID)
        root.pelm.append(host_id)
    edges: tuple = (("shared", 0, "first", 0), ("shared", 0, "second", 0),
                    ("first", 0, "native_100", 0), ("first", 1, "native_100", 1),
                    ("second", 0, "native_200", 0), ("second", 1, "native_200", 1))
    index: int
    source_slot: str
    source_port: int
    target_slot: str
    target_port: int
    for index, (source_slot, source_port, target_slot, target_port) in enumerate(edges):
        cable: BlkSig = BlkSig()
        cable.ID = str(index)
        cable.pnodfrom = source_slot
        cable.pnodto = target_slot
        cable.inodfrom = source_port
        cable.inodto = target_port
        cable.iconfrom = 2
        cable.iconto = 1
        cable.loc_name = f"signal_{index}"
        dgs.blksigs.append(cable)
    importer: DynamicModelImport = DynamicModelImport(dgs, grid, DynamicSimulationMode.RMS, Logger())
    return dgs, grid, importer


def test_partition_assigns_shared_state_once_and_connects_final_instances() -> None:
    """Keep local controls at their native hosts and share one state by UID.

    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    assert "root" in result.partitions_by_root_dgs_id, str(importer._logger)
    parts: list[DgsModelPartition] = result.partitions_by_root_dgs_id["root"]
    assert len(parts) == 2
    assert "shared" in parts[0].slots and "first" in parts[0].slots
    assert "second" in parts[1].slots
    assert sum(len(block.state_vars) for part in parts for block in part.template.block.get_all_blocks()) == 1
    importer.apply_templates_to_devices()
    importer.finalize_partitioned_roots()
    states: list[Var] = list(variable for host in grid.generators for block in host.rms_model.get_all_blocks()
                             for variable in block.state_vars)
    assert len(states) == 1
    receiver: Generator = grid.generators[1]
    links: list[Block] = list(block for block in receiver.rms_model.children
                              if receiver.rms_model.diagram.node_data[block.uid].tpe == BlockType.INTERCONNECTION.name)
    assert len(links) == 1
    # s is algebraic, produced once from x in the first host.
    shared_output: Var = next(variable for variable in get_interconnection_variables(grid.generators[0])
                               if variable.name.endswith("s") and variable.uid == links[0].out_vars[0].uid)
    assert links[0].out_vars[0].uid == shared_output.uid
    assert receiver.rms_template.block.diagram.to_dict() == receiver.rms_model.diagram.to_dict()


def test_partition_is_independent_of_export_row_order() -> None:
    """Use stable source FIDs rather than the order of slots or cables.

    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    dgs.blksigs.reverse()
    dgs.elmgenstats.reverse()
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    parts: list[DgsModelPartition] = result.partitions_by_root_dgs_id["root"]
    assert parts[0].device.idtag == "100"
    assert "shared" in parts[0].slots


def test_partitioned_current_sources_run_with_one_shared_state() -> None:
    """Match the analytical shared ramp through both physical injections.

    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    importer.convert_and_add_templates()
    importer.apply_templates_to_devices()
    importer.finalize_partitioned_roots()
    slack: Generator = Generator(name="Slack source", P=0.0, r1=0.01, x1=0.1)
    grid.add_generator(grid.buses[0], slack)
    slack.rms_model = build_thevenin_voltage_source(grid.var_factory, 0.01, 0.1).block
    set_rms_model(slack, slack.rms_model, grid.var_factory)
    pf: gce.PowerFlowResults = gce.power_flow(grid)
    assert pf.converged
    problem: RmsProblemDae = RmsProblemDae(grid, RmsOptions(time_step=0.05, simulation_time=0.15), pf, logger=Logger())
    problem.set_events_group(None)
    problem.reset_boundary_update_state(0.0)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=0.15, h=0.05, max_iter=100)
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged
    states: list[Var] = list(variable for host in grid.generators for owner in host.rms_model.get_all_blocks()
                             for variable in owner.state_vars)
    assert len(states) == 1
    np.testing.assert_allclose(values[:, problem.uid2idx_vars[states[0].uid]], times, atol=1e-8)
    host: Generator
    factor: float
    for host, factor in zip(grid.generators[:2], (0.01, 0.02)):
        native: Block = host.rms_model.children[0]
        command: Var = native.in_vars[2]
        np.testing.assert_allclose(values[:, problem.uid2idx_vars[command.uid]], factor * times, atol=1e-8)


def test_partitioned_models_survive_native_archive(tmp_path: Path) -> None:
    """Retain one state owner and the interconnection diagram after save/load.

    :param tmp_path: Temporary archive directory.
    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    importer.convert_and_add_templates()
    importer.apply_templates_to_devices()
    importer.finalize_partitioned_roots()
    path: Path = tmp_path / "partitioned.veragrid"
    gce.save_file(grid, str(path))
    restored: MultiCircuit = gce.open_file(str(path))
    first: Generator = next(host for host in restored.generators if host.idtag == "100")
    second: Generator = next(host for host in restored.generators if host.idtag == "200")
    assert sum(len(block.state_vars) for host in restored.generators for block in host.rms_model.get_all_blocks()) == 1
    link: Block = next(block for block in second.rms_model.children
                       if second.rms_model.diagram.node_data[block.uid].tpe == BlockType.INTERCONNECTION.name)
    source_uids: set[int] = set(variable.uid for variable in get_interconnection_variables(first))
    assert all(variable.uid in source_uids for variable in link.out_vars)
    assert len(second.rms_model.diagram.con_data) > 0


def test_dfig_import_activates_both_devices_and_preserves_measurement_locations(tmp_path: Path) -> None:
    """Exercise file-open wiring with explicit native reactor test parameters.

    :param tmp_path: Temporary completed fixture; the original export stays intact.
    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[4] / "trunk/dynamics/DFIG_RMS_v5_Export.dgs"
    if not path.is_file():
        pytest.skip("Local PowerFactory DFIG export is unavailable")
    else:
        pass
    # This wiring/initialization fixture supplies the reactor data now required
    # by the native voltage-source contract. These are explicit test values,
    # not defaults inferred for the original user export.
    rows: list[str] = list()
    in_genstat: bool = False
    row: str
    for row in path.read_text().splitlines():
        if row.startswith("$$"):
            in_genstat = row.startswith("$$ElmGenstat;")
            if in_genstat:
                row += ";uk(r);Pcu(r)"
            else:
                pass
        elif in_genstat and row.lstrip()[:1].isdigit():
            row += ";10;0"
        else:
            pass
        rows.append(row)
    complete_path: Path = tmp_path / "dfig_with_explicit_reactors.dgs"
    complete_path.write_text("\n".join(rows) + "\n")
    logger: Logger = Logger()
    grid: MultiCircuit = dgs_to_circuit(str(complete_path), use_dynamic_information=True,
                                       dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    devices: list[StaticGenerator] = list(device for device in grid.static_generators if device.idtag in ("965", "966"))
    assert len(devices) == 2
    assert all(device.rms_template is not None and device.rms_template.name.startswith("RMS / ") for device in devices)
    assert devices[0].bus is not devices[1].bus
    links: list[Block] = list(block for device in devices for block in device.rms_model.children
        if device.rms_model.diagram.node_data[block.uid].tpe == BlockType.INTERCONNECTION.name)
    assert len(links) > 0
    # Voltage meter 1193 measures the SeriesReactor bus, not the owner's terminal.
    measured_bus: Bus = next(bus for bus in grid.buses if bus.idtag == "993")
    physical_uids: set[int] = set(variable.uid for variable in measured_bus.rms_model.get_all_vars())
    meter: Block = next(block for device in devices for block in device.rms_model.get_all_blocks()
                         if "1193" in block.name)
    used_uids: set[int] = set(variable.uid for equation in meter.algebraic_eqs for variable in equation.get_vars())
    assert len(used_uids & physical_uids) > 0
    device: StaticGenerator
    owner: Block
    mapping: dict
    for device in devices:
        for owner in device.rms_model.get_all_blocks():
            for mapping in (owner.init_eqs, owner.post_init_seed_eqs):
                assert all(variable in mapping for variable in mapping)
    assert not any("could not" in entry.msg.lower() for entry in logger.entries), str(logger)
    # Template materialization must preserve the state identity established by
    # sStates, including when initialization lives on the graphical parent.
    dc_link: Block = next(block for device in devices for block in device.rms_model.get_all_blocks()
                          if block.name == "Vdc_Calc")
    integrator: Block = next(block for block in dc_link.get_all_blocks() if block.name == "1/s")
    state: Var = integrator.state_vars[0]
    assert dc_link.init_eqs[state].eval_uid(dict()) == pytest.approx(1150.0)
    # ElmVac 998 must supply a genuine solved operating point; an empty PF
    # convergence report with zero voltages used to masquerade as success.
    assert any(source.idtag == "998" for source in grid.external_grids)
    assert any(branch.idtag == "998:impedance" for branch in grid.series_reactances)
    pf: gce.PowerFlowResults = gce.power_flow(grid)
    assert len(pf.convergence_reports) > 0 and pf.converged
    assert np.all(np.abs(pf.voltage) > 0.5)
    problem: RmsProblemDae = RmsProblemDae(
        grid, RmsOptions(time_step=0.001, simulation_time=0.01), pf, logger=logger)
    problem.set_events_group(None)
    initial: np.ndarray = problem.get_x0()
    assert initial[problem.uid2idx_vars[state.uid]] == pytest.approx(1150.0)
    # Equal local labels never merge independent physical meters. All six
    # former duplicate columns and the FRT collision must remain independent.
    meter_uids: set[int] = set()
    physical_meter: Block
    for physical_meter in (block for device in devices for block in device.rms_model.get_all_blocks()
                           if block.name.startswith(("Current meter", "Voltage meter"))):
        local_uids: set[int] = set(variable.uid for variable in physical_meter.out_vars)
        assert meter_uids.isdisjoint(local_uids)
        meter_uids.update(local_uids)
    jacobian: csc_matrix = problem.get_j22(initial, np.zeros(problem.get_diff_var_number()), 1.0)
    assert jacobian.shape[0] == jacobian.shape[1]
    # The static reactor impedance must replace the generic line-shell defaults.
    parameter_values: dict[int, float] = dict((variable.uid, float(problem._constant_params[index]))
                                             for index, variable in enumerate(problem._constant_parameters))
    reactor: SeriesReactance
    for reactor in grid.series_reactances:
        physical: Block = next(block for block in reactor.rms_model.get_all_blocks()
                               if ParamPowerFlowReferenceType.g in block.api_obj_mapping)
        admittance: complex = 1.0 / complex(reactor.R, reactor.X)
        assert parameter_values[physical.api_obj_mapping[ParamPowerFlowReferenceType.g].uid] == pytest.approx(admittance.real)
        assert parameter_values[physical.api_obj_mapping[ParamPowerFlowReferenceType.b].uid] == pytest.approx(admittance.imag)
    assert all(variable.uid in problem.init_guess for variable in problem.sys_vars.values())
    # The imported symbolic initial conditions avoid the former atan2(0, 0)
    # Jacobian singularity without modifying the numerical initializer.
    assert np.all(np.isfinite(problem.get_j22(initial, np.zeros(problem.get_diff_var_number()), 1.0).data))
    # The supplied reactor values make this a structural import fixture;
    # they are not a validated transient operating point for the DFIG.


def test_native_voltage_source_obeys_voltage_commands_and_power_base() -> None:
    """Check the physical realization required by the DFIG's iSimModel=2.

    :return: None.
    """
    block: Block = build_dgs_elmgenstat_voltage_block(100.0, 150.0)
    voltage: float = 1.05
    angle: float = 0.2
    pg: float = 0.3
    qg: float = 0.1
    gain: float = 1.5
    real: float = voltage * np.cos(angle)
    imag: float = voltage * np.sin(angle)
    values: dict[str, float] = dict(Vm=voltage, Va=angle, u1r_in=real, u1i_in=imag,
        Pg=pg, Qg=qg, Pe=pg / gain, Qgen=qg / gain, Vt_r=real, Vt_i=imag,
        It_r=(pg * np.cos(angle) + qg * np.sin(angle)) / (gain * voltage),
        It_i=(pg * np.sin(angle) - qg * np.cos(angle)) / (gain * voltage))
    bindings: dict[int, float] = dict((variable.uid, values[variable.name])
                                      for collection in (block.in_vars, block.algebraic_vars) for variable in collection)
    np.testing.assert_allclose(list(equation.eval_uid(bindings) for equation in block.algebraic_eqs), 0.0, atol=1e-12)
    bindings[block.in_vars[2].uid] += 0.01
    assert block.algebraic_eqs[-2].eval_uid(bindings) == pytest.approx(-0.01)


@pytest.mark.parametrize("blocked", ("service", "selection"))
def test_partition_respects_native_service_and_selected_root(blocked: str) -> None:
    """Reject a composite whose native hosts do not all select the active root.

    :param blocked: Native selection condition to invalidate.
    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    if blocked == "service":
        dgs.elmgenstats[1].outserv = 1
    else:
        dgs.elmgenstats[1].c_pmod = "another-root"
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    importer.apply_templates_to_devices()
    assert result.partitions_by_root_dgs_id == dict()
    assert all(host.rms_template is None for host in grid.generators)


def test_partition_accepts_unambiguous_legacy_root_without_pmod() -> None:
    """Resolve ownership from explicit slots when older exports omit c_pmod.

    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    source: ElmGenstat
    for source in dgs.elmgenstats:
        source.c_pmod = ""
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    assert len(result.partitions_by_root_dgs_id["root"]) == 2


def test_partition_owns_procedural_logic_once_and_finalization_is_idempotent() -> None:
    """Move a state event together with its controller and create links once.

    :return: None.
    """
    dgs: DgsCircuit
    grid: MultiCircuit
    importer: DynamicModelImport
    dgs, grid, importer = make_partition_fixture()
    definition: BlkDef = next(block for block in dgs.blkdefs if block.ID == "type_shared")
    definition.internals = list(("held",))
    definition.equations_raw.extend(("inc(held)=0", "event(1,time()>=1.0, 'name=this value=x variable=held')"))
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    assert "root" in result.partitions_by_root_dgs_id, str(importer._logger)
    importer.apply_templates_to_devices()
    assert importer.finalize_partitioned_roots()
    assert sum(len(block.procedural_logic) for device in grid.generators
               for block in device.rms_model.get_all_blocks()) == 1
    before: list[int] = list(len(device.rms_model.children) for device in grid.generators)
    assert importer.finalize_partitioned_roots()
    assert list(len(device.rms_model.children) for device in grid.generators) == before


def test_legacy_dfig_missing_reactor_parameters_is_reported_without_wrong_equipment() -> None:
    """Keep an incomplete voltage-source export inspectable without guessing Z.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[4] / "trunk/dynamics/DFIG_RMS_v5_Export.dgs"
    if not path.is_file():
        pytest.skip("Local PowerFactory DFIG export is unavailable")
    else:
        pass
    logger: Logger = Logger()
    grid: MultiCircuit = dgs_to_circuit(str(path), use_dynamic_information=True,
        dynamic_simulation_mode=DynamicSimulationMode.RMS, logger_=logger)
    assert any("requires exported uk and Pcu" in str(entry.value) for entry in logger.entries)
    devices: list[StaticGenerator] = list(device for device in grid.static_generators if device.idtag in ("965", "966"))
    assert len(devices) == 2
    assert all(not device.active for device in devices)
