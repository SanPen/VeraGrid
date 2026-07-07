# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import importlib.util
import sys
import types
import uuid

import numpy as np


repo_root = Path(__file__).resolve().parents[6]
src_root = repo_root / "src"
engine_root = src_root / "VeraGridEngine"

if str(src_root) in sys.path:
    pass
else:
    sys.path.insert(0, str(src_root))


networkx_module = sys.modules.get("networkx", None)
if networkx_module is None:
    sys.modules["networkx"] = types.ModuleType("networkx")
else:
    pass

matplotlib_module = sys.modules.get("matplotlib", None)
if matplotlib_module is None:
    matplotlib_module = types.ModuleType("matplotlib")
    sys.modules["matplotlib"] = matplotlib_module
else:
    pass

for submodule_name in ("pyplot", "colors", "cm"):
    full_name = f"matplotlib.{submodule_name}"
    submodule = sys.modules.get(full_name, None)
    if submodule is None:
        submodule = types.ModuleType(full_name)
        sys.modules[full_name] = submodule
    else:
        pass
    setattr(matplotlib_module, submodule_name, submodule)

pyplot_module = sys.modules["matplotlib.pyplot"]
if hasattr(pyplot_module, "axis"):
    pass
else:
    setattr(pyplot_module, "axis", object)

chardet_module = sys.modules.get("chardet", None)
if chardet_module is None:
    sys.modules["chardet"] = types.ModuleType("chardet")
else:
    pass

sklearn_module = sys.modules.get("sklearn", None)
if sklearn_module is None:
    sklearn_module = types.ModuleType("sklearn")
    sys.modules["sklearn"] = sklearn_module
else:
    pass

sklearn_ensemble_module = sys.modules.get("sklearn.ensemble", None)
if sklearn_ensemble_module is None:
    sklearn_ensemble_module = types.ModuleType("sklearn.ensemble")
    sys.modules["sklearn.ensemble"] = sklearn_ensemble_module
else:
    pass
setattr(sklearn_module, "ensemble", sklearn_ensemble_module)
if hasattr(sklearn_ensemble_module, "RandomForestRegressor"):
    pass
else:
    setattr(sklearn_ensemble_module, "RandomForestRegressor", object)


def _ensure_package(name: str, path: Path) -> None:
    module = sys.modules.get(name, None)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    else:
        pass


# _ensure_package("VeraGridEngine.Simulations", engine_root / "Simulations")
# _ensure_package("VeraGridEngine.Simulations.Rms", engine_root / "Simulations" / "Rms")
# _ensure_package("VeraGridEngine.Simulations.Rms.numerical", engine_root / "Simulations" / "Rms" / "numerical")
# _ensure_package("VeraGridEngine.Simulations.Rms.problems", engine_root / "Simulations" / "Rms" / "problems")
# _ensure_package("VeraGridEngine.Simulations.PowerFlow", engine_root / "Simulations" / "PowerFlow")
# _ensure_package("VeraGridEngine.Simulations.PowerFlow.NumericalMethods", engine_root / "Simulations" / "PowerFlow" / "NumericalMethods")
# _ensure_package("VeraGridEngine.Simulations.EMT", engine_root / "Simulations" / "EMT")
# _ensure_package("VeraGridEngine.Simulations.EMT.problems", engine_root / "Simulations" / "EMT" / "problems")
# _ensure_package("VeraGridEngine.Simulations.EMT.solvers", engine_root / "Simulations" / "EMT" / "solvers")
# _ensure_package("VeraGridEngine.Simulations.Clustering", engine_root / "Simulations" / "Clustering")
# _ensure_package("VeraGridEngine.Simulations.Stochastic", engine_root / "Simulations" / "Stochastic")
# _ensure_package("VeraGridEngine.IO", engine_root / "IO")
# _ensure_package("VeraGridEngine.IO.others", engine_root / "IO" / "others")

from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.emt_driver import EmtSimulationDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Rms.rms_driver import RmsSimulationDriver
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Templates.Emt.bus_emt_template import BusEmtTemplate
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Templates.Rms.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.enumerations import (
    BranchImpedanceMode,
    DynamicIntegrationMethod,
    SolverType,
    VarPowerFlowRefferenceType,
)

from VeraGridEngine.IO.fmu.exporter.api import export_fmu
from VeraGridEngine.IO.fmu.exporter.config import ExportConfig as CsExportConfig, detect_target_platform as detect_cs_target_platform
from VeraGridEngine.IO.fmu.exporter.compat import Block, Const, Var
from VeraGridEngine.IO.fmu.importer import (
    FmuDeviceAttachmentRequest,
    FmuDeviceDomain,
    FmuInterfaceMode,
    FmuMeIntegrationMethod,
    FmuReferenceValue,
    FmuRefBinding,
    attach_fmu_to_device,
    build_emt_boundary_updater,
    register_emt_fmu_cs_device,
    register_emt_fmu_me_device,
)
from VeraGridEngine.IO.fmu.exporter_me.api import export_fmu_me
from VeraGridEngine.IO.fmu.exporter_me.config import ExportConfig as MeExportConfig, detect_target_platform as detect_me_target_platform


def get_example_output_dir() -> Path:
    """Return the directory used by the FMU import example scripts.

    :return: Example output directory.
    """

    output_dir: Path = Path(__file__).resolve().parents[1] / "reports" / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir.resolve()


def _has_fmpy() -> bool:
    """Return whether the current Python environment provides `fmpy`.

    :return: `True` when `fmpy` can be imported.
    """

    return importlib.util.find_spec("fmpy") is not None


def write_example_report(report_path: Path, lines: tuple[str, ...]) -> Path:
    """Write a plain-text report for one FMU import example run.

    :param report_path: Report output path.
    :param lines: Lines written to the report.
    :return: Final report path.
    """

    text: str = "\n".join(lines) + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8")
    return report_path


def _build_rms_cs_source_block() -> Block:
    """Build the self-contained source block used to export an example RMS CS FMU.

    :return: Example RMS CS FMU block.
    """

    x: Var = Var("x")
    dx: Var = Var("dx", base_var=x)
    p_out: Var = Var("p_out")
    q_out: Var = Var("q_out")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0)],
        algebraic_vars=[p_out, q_out],
        algebraic_eqs=[p_out - (Const(-0.1) - Const(0.02) * x), q_out - Const(-0.01)],
        diff_vars=[dx],
        init_values={x: Const(0.0), p_out: Const(-0.1), q_out: Const(-0.01)},
        init_eqs={p_out: Const(-0.1), q_out: Const(-0.01)},
        out_vars=[p_out, q_out],
    )


def _build_rms_me_source_block() -> Block:
    """Build the self-contained source block used to export an example RMS ME FMU.

    :return: Example RMS ME FMU block.
    """

    x: Var = Var("x")
    dx: Var = Var("dx", base_var=x)
    p_out: Var = Var("p_out")
    q_out: Var = Var("q_out")
    u: Var = Var("u")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0) + u],
        algebraic_vars=[p_out, q_out],
        algebraic_eqs=[p_out - x, q_out - Const(-0.01)],
        diff_vars=[dx],
        init_values={x: Const(0.0), p_out: Const(0.0), q_out: Const(-0.01)},
        init_eqs={p_out: Const(0.0), q_out: Const(-0.01)},
        in_vars=[u],
        out_vars=[p_out, q_out],
    )


def _build_emt_cs_source_block() -> Block:
    """Build the self-contained source block used to export an example EMT CS FMU.

    :return: Example EMT CS FMU block.
    """

    x: Var = Var("x")
    dx: Var = Var("dx", base_var=x)
    i_a: Var = Var("i_a_out")
    i_b: Var = Var("i_b_out")
    i_c: Var = Var("i_c_out")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0)],
        algebraic_vars=[i_a, i_b, i_c],
        algebraic_eqs=[i_a - (Const(-0.01) * x), i_b - (Const(0.005) * x), i_c - (Const(0.005) * x)],
        diff_vars=[dx],
        init_values={x: Const(0.0), i_a: Const(0.0), i_b: Const(0.0), i_c: Const(0.0)},
        init_eqs={i_a: Const(0.0), i_b: Const(0.0), i_c: Const(0.0)},
        out_vars=[i_a, i_b, i_c],
    )


def _build_emt_me_source_block() -> Block:
    """Build the self-contained source block used to export an example EMT ME FMU.

    :return: Example EMT ME FMU block.
    """

    x: Var = Var("x")
    dx: Var = Var("dx", base_var=x)
    i_a: Var = Var("i_a_out")
    i_b: Var = Var("i_b_out")
    i_c: Var = Var("i_c_out")
    u: Var = Var("u")
    return Block(
        state_vars=[x],
        state_eqs=[Const(1.0) + u],
        algebraic_vars=[i_a, i_b, i_c],
        algebraic_eqs=[i_a - x, i_b - (Const(-0.5) * x), i_c - (Const(-0.5) * x)],
        diff_vars=[dx],
        init_values={x: Const(0.0), i_a: Const(0.0), i_b: Const(0.0), i_c: Const(0.0)},
        init_eqs={i_a: Const(0.0), i_b: Const(0.0), i_c: Const(0.0)},
        in_vars=[u],
        out_vars=[i_a, i_b, i_c],
    )


def export_example_rms_cs_fmu(output_dir: Path) -> Path:
    """Export the self-contained RMS CS device FMU used by the example scripts.

    :param output_dir: Output directory for the generated FMU.
    :return: Generated FMU path.
    """

    unique_name: str = f"ExampleRmsCsDevice_{uuid.uuid4().hex[:8]}"
    return export_fmu(
        _build_rms_cs_source_block(),
        CsExportConfig(
            model_name=unique_name,
            output_path=output_dir / f"{unique_name}.fmu",
            target_platform=detect_cs_target_platform(),
            compile_binary=True,
            keep_build_dir=False,
        ),
    )


def export_example_rms_me_fmu(output_dir: Path) -> Path:
    """Export the self-contained RMS ME device FMU used by the example scripts.

    :param output_dir: Output directory for the generated FMU.
    :return: Generated FMU path.
    """

    unique_name: str = f"ExampleRmsMeDevice_{uuid.uuid4().hex[:8]}"
    return export_fmu_me(
        _build_rms_me_source_block(),
        MeExportConfig(
            model_name=unique_name,
            output_path=output_dir / f"{unique_name}.fmu",
            target_platform=detect_me_target_platform(),
            compile_binary=True,
            keep_build_dir=False,
        ),
    )


def export_example_emt_cs_fmu(output_dir: Path) -> Path:
    """Export the self-contained EMT CS device FMU used by the example scripts.

    :param output_dir: Output directory for the generated FMU.
    :return: Generated FMU path.
    """

    unique_name: str = f"ExampleEmtCsDevice_{uuid.uuid4().hex[:8]}"
    return export_fmu(
        _build_emt_cs_source_block(),
        CsExportConfig(
            model_name=unique_name,
            output_path=output_dir / f"{unique_name}.fmu",
            target_platform=detect_cs_target_platform(),
            compile_binary=True,
            keep_build_dir=False,
        ),
    )


def export_example_emt_me_fmu(output_dir: Path) -> Path:
    """Export the self-contained EMT ME device FMU used by the example scripts.

    :param output_dir: Output directory for the generated FMU.
    :return: Generated FMU path.
    """

    unique_name: str = f"ExampleEmtMeDevice_{uuid.uuid4().hex[:8]}"
    return export_fmu_me(
        _build_emt_me_source_block(),
        MeExportConfig(
            model_name=unique_name,
            output_path=output_dir / f"{unique_name}.fmu",
            target_platform=detect_me_target_platform(),
            compile_binary=True,
            keep_build_dir=False,
        ),
    )


def _build_power_flow_options() -> PowerFlowOptions:
    """Build the power-flow options reused by the FMU import examples.

    :return: Power-flow options.
    """

    return PowerFlowOptions(
        solver_type=SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=False,
        control_taps_phase=False,
        control_remote_voltage=False,
        orthogonalize_controls=True,
        apply_temperature_correction=False,
        branch_impedance_tolerance_mode=BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )


def _get_bus_power_default(grid: MultiCircuit, pf_results: Any, bus: Bus) -> tuple[float, float]:
    """
    Return the exact active and reactive power injection solved at one bus.

    The FMU examples use these values as output defaults so the imported FMU shell
    starts from the same operating point that the static network used during the
    power-flow initialization.

    :param grid: Solved grid.
    :param pf_results: Finished power-flow results.
    :param bus: Bus where the imported FMU device is connected.
    :return: Active and reactive bus injections.
    """

    bus_index: int = grid.buses.index(bus)
    bus_power: complex = complex(pf_results.Sbus[bus_index] / grid.Sbase)
    return float(bus_power.real), float(bus_power.imag)


def _build_rms_demo_grid() -> tuple[MultiCircuit, Load]:
    """Build the minimal RMS demo grid used by the RMS FMU import examples.

    :return: Grid and imported device.
    """

    grid: MultiCircuit = MultiCircuit(Sbase=100.0, fbase=50.0)
    bus_slack: Bus = Bus(name="Bus0", Vnom=10.0, is_slack=True)
    bus_load: Bus = Bus(name="Bus1", Vnom=10.0)
    grid.add_bus(bus_slack)
    grid.add_bus(bus_load)

    # RMS buses need their symbolic shell before attaching dynamic devices.
    initialize_bus_rms(bus_slack, vf=grid.var_factory)
    initialize_bus_rms(bus_load, vf=grid.var_factory)

    line: Line = Line(name="line_0_1", bus_from=bus_slack, bus_to=bus_load, r=0.03, x=0.07, b=0.03, rate=900.0)
    generator: Generator = Generator(name="Gen0", P=10.0, vset=1.0, Snom=900.0, x1=0.86138701, r1=0.3, freq=50.0)
    load: Load = Load(name="ImportedLoad", P=10.0, Q=1.0)

    line.rms_model = get_line_rms_template(grid.var_factory).block
    generator.rms_model = get_complete_generator_template_rms(grid.var_factory).block
    grid.add_rms_events_group(RmsEventsGroup(name="default_rms_example_group"))

    grid.add_line(line)
    grid.add_generator(bus=bus_slack, api_obj=generator)
    grid.add_load(bus=bus_load, api_obj=load)
    return grid, load


def _build_emt_demo_grid() -> tuple[MultiCircuit, Load]:
    """Build the minimal EMT demo grid used by the EMT FMU import examples.

    :return: Grid and imported device.
    """

    grid: MultiCircuit = MultiCircuit(Sbase=100.0, fbase=50.0)
    bus: Bus = Bus(name="Bus0", Vnom=10.0, is_slack=True)
    grid.add_bus(bus)

    # The example forces a simple ABC bus shell because the demo grid has no EMT branches yet.
    bus_template = BusEmtTemplate(vf=grid.var_factory, mask=[False, True, True, True], is_dc=bus.is_dc, name=f"{bus.name}_emt_template")

    # The public setter copies the block through symbolic serialization and that path still rejects `None`
    # entries present in EMT bus external mappings. For this controlled example we attach the template directly.
    bus._emt_template = bus_template
    bus._emt_model = bus_template.block

    generator: Generator = Generator(name="Gen0", P=0.0, vset=1.0, Snom=900.0, x1=0.2, r1=0.01)
    generator_template = get_generator_thevenin_rl_emt_template(grid=grid, gen=generator, name="emt_thevenin_source")

    # The public setter still serializes through external mappings with `None` placeholders, so we attach directly.
    generator._emt_template = generator_template
    generator._emt_model = generator_template.block
    load: Load = Load(name="ImportedLoad", P=0.0, Q=0.0)

    grid.add_generator(bus=bus, api_obj=generator)
    grid.add_load(bus=bus, api_obj=load)
    return grid, load


class _ExampleEmtProblem:
    """Minimal EMT harness used by the example scripts.

    :param block: Imported FMU shell block.
    :param bus_voltage_var: Optional EMT bus voltage variable used as FMU input.
    """

    __slots__ = ("uid2idx_event_params", "uid2idx_vars", "_fmu_cs_adapters", "_fmu_me_adapters", "calls")

    def __init__(self, block: Block, bus_voltage_var: Var | None = None) -> None:
        """Store the synthetic EMT harness state.

        :return: None.
        """

        self.uid2idx_event_params: dict[int, int] = dict()
        self.uid2idx_vars: dict[int, int] = dict()
        event_index: int = 0
        event_parameter: Var
        for event_parameter in block.event_dict.keys():
            self.uid2idx_event_params[event_parameter.uid] = event_index
            event_index += 1
        if bus_voltage_var is None:
            pass
        else:
            self.uid2idx_vars[bus_voltage_var.uid] = 0
        self._fmu_cs_adapters = list()
        self._fmu_me_adapters = list()
        self.calls: int = 0

    def emt_boundary_update(self, t_curr: float, x_prev: np.ndarray, full_params: np.ndarray) -> None:
        """Record one synthetic EMT boundary update call.

        :param t_curr: Current simulation time.
        :param x_prev: Accepted state vector.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        self.calls += 1

    def get_next_forced_event_time(self, t_prev: float, t_target: float):
        """Return that the synthetic harness has no forced events.

        :param t_prev: Previous time.
        :param t_target: Candidate target time.
        :return: None.
        """

        return None

    def close(self) -> None:
        """Provide the same close interface as the real EMT problem.

        :return: None.
        """

        return


def _build_emt_results_report_lines(params: np.ndarray, prefixes: tuple[str, ...]) -> tuple[str, ...]:
    """Build a simple textual report from the synthetic EMT boundary harness.

    :param params: Runtime-parameter vector.
    :param prefixes: Label prefixes for the report.
    :return: Summary lines.
    """

    lines: list[str] = list()
    index: int
    for index, prefix in enumerate(prefixes):
        lines.append(f"{prefix} = {float(params[index]):.8f}")
    return tuple(lines)


def _build_rms_results_summary(driver: RmsSimulationDriver, load: Load) -> tuple[str, ...]:
    """Build a human-readable summary for one RMS FMU import example.

    :param driver: Finished RMS simulation driver.
    :param load: Imported FMU load device.
    :return: Summary lines.
    """

    if driver.results is None:
        raise RuntimeError("The RMS simulation did not produce results")
    else:
        p_var: Var = load.rms_model.external_mapping[VarPowerFlowRefferenceType.P]
        q_var: Var = load.rms_model.external_mapping[VarPowerFlowRefferenceType.Q]
        p_final = _try_get_result_value(driver.results.values, driver.results.uid2idx.get(p_var.uid, None))
        q_final = _try_get_result_value(driver.results.values, driver.results.uid2idx.get(q_var.uid, None))
        p_text: str
        q_text: str
        if p_final is None:
            p_text = "not recorded"
        else:
            p_text = f"{p_final:.8f}"
        if q_final is None:
            q_text = "not recorded"
        else:
            q_text = f"{q_final:.8f}"
        return (
            f"final_time = {driver.results.time_array[-1]}",
            f"P_final = {p_text}",
            f"Q_final = {q_text}",
        )


def _read_rms_fmu_output(problem: Any, device: Load, reference: VarPowerFlowRefferenceType) -> float | None:
    """
    Read one FMU-backed RMS output directly from the registered runtime adapters.

    The helper prefers adapter indices over symbolic-name reconstruction because the
    runtime adapters already own the authoritative mapping from VeraGrid references
    to the parameter vector updated during the simulation.

    :param problem: Finished RMS problem instance.
    :param device: Device hosting the imported FMU.
    :param reference: VeraGrid output reference to recover.
    :return: Runtime output value when available.
    """

    adapter = None
    for adapter in problem._fmu_cs_adapters:
        if adapter.device == device:
            if reference in adapter.last_outputs:
                return adapter.last_outputs[reference]
            else:
                if problem._last_variable_parameters_values is None:
                    return None
                else:
                    if reference in adapter.output_param_indices:
                        output_index: int = adapter.output_param_indices[reference]
                        return float(problem._last_variable_parameters_values[output_index])
                    else:
                        return None
        else:
            pass

    for adapter in problem._fmu_me_adapters:
        if adapter.device == device:
            if reference in adapter.last_outputs:
                return adapter.last_outputs[reference]
            else:
                if problem._last_variable_parameters_values is None:
                    return None
                else:
                    if reference in adapter.output_param_indices:
                        output_index = adapter.output_param_indices[reference]
                        return float(problem._last_variable_parameters_values[output_index])
                    else:
                        return None
        else:
            pass

    return None


def _build_final_rms_snapshot(driver: RmsSimulationDriver) -> np.ndarray:
    """
    Build the final RMS state snapshot from the finished results matrix.

    :param driver: Finished RMS simulation driver.
    :return: Final RMS state/algebraic snapshot.
    """

    final_values: np.ndarray = np.asarray(driver.results.values[-1, :, 0], dtype=float)
    return np.ravel(final_values)


def _refresh_rms_fmu_outputs_from_final_snapshot(problem: Any,
                                                 device: Load,
                                                 final_snapshot: np.ndarray,
                                                 final_time: float) -> None:
    """
    Re-evaluate FMU outputs from the final RMS network snapshot when the runtime cache is empty.

    The fallback is used only by the example report helpers. It keeps the example
    informative even when the solver lifecycle closes the FMU before the report is
    assembled.

    :param problem: Finished RMS problem instance.
    :param device: Device hosting the imported FMU.
    :param final_snapshot: Final RMS state/algebraic snapshot.
    :param final_time: Final simulation time.
    :return: None.
    """

    adapter = None
    for adapter in problem._fmu_cs_adapters:
        if adapter.device == device:
            if len(adapter.last_outputs) == 0:
                outputs = adapter.initialize_outputs(final_time, final_snapshot)
                adapter.last_outputs = dict(outputs)
                adapter.close()
            else:
                pass
        else:
            pass

    for adapter in problem._fmu_me_adapters:
        if adapter.device == device:
            if len(adapter.last_outputs) == 0:
                outputs = adapter.initialize_outputs(final_time, final_snapshot)
                adapter.last_outputs = dict(outputs)
                adapter.close()
            else:
                pass
        else:
            pass


def _build_emt_results_summary(driver: EmtSimulationDriver, load: Load) -> tuple[str, ...]:
    """Build a human-readable summary for one EMT FMU import example.

    :param driver: Finished EMT simulation driver.
    :param load: Imported FMU load device.
    :return: Summary lines.
    """

    if driver.results is None:
        raise RuntimeError("The EMT simulation did not produce results")
    else:
        i_a_var: Var = load.emt_model.external_mapping[VarPowerFlowRefferenceType.i_A]
        i_b_var: Var = load.emt_model.external_mapping[VarPowerFlowRefferenceType.i_B]
        i_c_var: Var = load.emt_model.external_mapping[VarPowerFlowRefferenceType.i_C]
        i_a_final = _try_get_result_value(driver.results.values, driver.results.uid2idx.get(i_a_var.uid, None))
        i_b_final = _try_get_result_value(driver.results.values, driver.results.uid2idx.get(i_b_var.uid, None))
        i_c_final = _try_get_result_value(driver.results.values, driver.results.uid2idx.get(i_c_var.uid, None))
        i_a_text: str
        i_b_text: str
        i_c_text: str
        if i_a_final is None:
            i_a_text = "not recorded"
        else:
            i_a_text = f"{i_a_final:.8f}"
        if i_b_final is None:
            i_b_text = "not recorded"
        else:
            i_b_text = f"{i_b_final:.8f}"
        if i_c_final is None:
            i_c_text = "not recorded"
        else:
            i_c_text = f"{i_c_final:.8f}"
        return (
            f"final_time = {driver.results.time_array[-1]}",
            f"iA_final = {i_a_text}",
            f"iB_final = {i_b_text}",
            f"iC_final = {i_c_text}",
        )


def _try_get_result_value(values: np.ndarray, column_index: int | None) -> float | None:
    """Try to recover one scalar value from a VeraGrid results matrix.

    :param values: Results matrix.
    :param column_index: Candidate variable column index.
    :return: Final scalar value when available.
    """

    if column_index is None:
        return None
    else:
        flat_values: np.ndarray = np.ravel(values[-1, column_index])
        if flat_values.size > 0:
            return float(flat_values[0])
        else:
            return None


def run_rms_cs_example(output_dir: Path) -> Path:
    """Run the full RMS Co-Simulation FMU device example.

    :param output_dir: Output directory used for the FMU and the report.
    :return: Generated report path.
    """

    fmu_path: Path = export_example_rms_cs_fmu(output_dir)
    report_path: Path = output_dir / "rms_cs_example_report.txt"
    if _has_fmpy():
        pass
    else:
        lines: tuple[str, ...] = (
            f"fmu_path = {fmu_path}",
            "mode = CoSimulation",
            "status = skipped",
            "reason = fmpy not installed in this Python environment",
        )
        return write_example_report(report_path, lines)

    grid: MultiCircuit
    load: Load
    grid, load = _build_rms_demo_grid()
    pf_driver: PowerFlowDriver = PowerFlowDriver(grid=grid, options=_build_power_flow_options())
    pf_driver.run()
    p_default: float
    q_default: float
    p_default, q_default = _get_bus_power_default(grid, pf_driver.results, load.bus)

    request = FmuDeviceAttachmentRequest(
        fmu_path=fmu_path,
        domain=FmuDeviceDomain.RMS,
        mode=FmuInterfaceMode.CO_SIMULATION,
        input_bindings=tuple(),
        output_bindings=(
            FmuRefBinding(VarPowerFlowRefferenceType.P, "p_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.Q, "q_out"),
        ),
        output_defaults=(
            FmuReferenceValue(VarPowerFlowRefferenceType.P, p_default),
            FmuReferenceValue(VarPowerFlowRefferenceType.Q, q_default),
        ),
        extraction_root=output_dir,
    )

    # The imported FMU is attached as a normal load device shell before running the RMS driver.
    attach_fmu_to_device(load, grid, request)

    rms_driver: RmsSimulationDriver = RmsSimulationDriver(
        grid=grid,
        options=RmsOptions(time_step=1e-3, simulation_time=5e-3, tolerance=1e-6, integration_method=DynamicIntegrationMethod.DaeBackEuler, max_iter=50),
        pf_results=pf_driver.results,
    )
    rms_driver.run()

    if rms_driver.problem is None:
        raise RuntimeError("The RMS example did not keep a reference to the simulation problem")
    else:
        final_snapshot: np.ndarray = _build_final_rms_snapshot(rms_driver)
        final_time_seconds: float = float(rms_driver.results.time_array[-1].value) * 1e-9
        _refresh_rms_fmu_outputs_from_final_snapshot(rms_driver.problem, load, final_snapshot, final_time_seconds)
        p_value = _read_rms_fmu_output(rms_driver.problem, load, VarPowerFlowRefferenceType.P)
        q_value = _read_rms_fmu_output(rms_driver.problem, load, VarPowerFlowRefferenceType.Q)
        p_text: str = "not available" if p_value is None else f"{p_value:.8f}"
        q_text: str = "not available" if q_value is None else f"{q_value:.8f}"

    lines: tuple[str, ...] = (
        f"fmu_path = {fmu_path}",
        f"mode = {request.mode.value}",
        f"final_time = {rms_driver.results.time_array[-1]}",
        f"P_final = {p_text}",
        f"Q_final = {q_text}",
    )
    return write_example_report(report_path, lines)


def run_rms_me_example(output_dir: Path) -> Path:
    """Run the full RMS Model Exchange FMU device example.

    :param output_dir: Output directory used for the FMU and the report.
    :return: Generated report path.
    """

    fmu_path: Path = export_example_rms_me_fmu(output_dir)
    report_path: Path = output_dir / "rms_me_example_report.txt"
    if _has_fmpy():
        pass
    else:
        lines: tuple[str, ...] = (
            f"fmu_path = {fmu_path}",
            "mode = ModelExchange",
            "status = skipped",
            "reason = fmpy not installed in this Python environment",
        )
        return write_example_report(report_path, lines)

    grid: MultiCircuit
    load: Load
    grid, load = _build_rms_demo_grid()
    pf_driver: PowerFlowDriver = PowerFlowDriver(grid=grid, options=_build_power_flow_options())
    pf_driver.run()
    p_default, q_default = _get_bus_power_default(grid, pf_driver.results, load.bus)

    request = FmuDeviceAttachmentRequest(
        fmu_path=fmu_path,
        domain=FmuDeviceDomain.RMS,
        mode=FmuInterfaceMode.MODEL_EXCHANGE,
        input_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.Vm, "u"),),
        output_bindings=(
            FmuRefBinding(VarPowerFlowRefferenceType.P, "p_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.Q, "q_out"),
        ),
        output_defaults=(
            FmuReferenceValue(VarPowerFlowRefferenceType.P, p_default),
            FmuReferenceValue(VarPowerFlowRefferenceType.Q, q_default),
        ),
        extraction_root=output_dir,
        integration_method=FmuMeIntegrationMethod.EXPLICIT_EULER,
    )

    attach_fmu_to_device(load, grid, request)

    rms_driver: RmsSimulationDriver = RmsSimulationDriver(
        grid=grid,
        options=RmsOptions(time_step=1e-3, simulation_time=5e-3, tolerance=1e-6, integration_method=DynamicIntegrationMethod.DaeBackEuler, max_iter=50),
        pf_results=pf_driver.results,
    )
    rms_driver.run()

    if rms_driver.problem is None:
        raise RuntimeError("The RMS example did not keep a reference to the simulation problem")
    else:
        final_snapshot = _build_final_rms_snapshot(rms_driver)
        final_time_seconds = float(rms_driver.results.time_array[-1].value) * 1e-9
        _refresh_rms_fmu_outputs_from_final_snapshot(rms_driver.problem, load, final_snapshot, final_time_seconds)
        p_value = _read_rms_fmu_output(rms_driver.problem, load, VarPowerFlowRefferenceType.P)
        q_value = _read_rms_fmu_output(rms_driver.problem, load, VarPowerFlowRefferenceType.Q)
        p_text = "not available" if p_value is None else f"{p_value:.8f}"
        q_text = "not available" if q_value is None else f"{q_value:.8f}"

    lines: tuple[str, ...] = (
        f"fmu_path = {fmu_path}",
        f"mode = {request.mode.value}",
        f"final_time = {rms_driver.results.time_array[-1]}",
        f"P_final = {p_text}",
        f"Q_final = {q_text}",
    )
    return write_example_report(report_path, lines)


def run_emt_cs_example(output_dir: Path) -> Path:
    """Run the full EMT Co-Simulation FMU device example.

    :param output_dir: Output directory used for the FMU and the report.
    :return: Generated report path.
    """

    fmu_path: Path = export_example_emt_cs_fmu(output_dir)
    report_path: Path = output_dir / "emt_cs_example_report.txt"
    if _has_fmpy():
        pass
    else:
        lines: tuple[str, ...] = (
            f"fmu_path = {fmu_path}",
            "mode = CoSimulation",
            "status = skipped",
            "reason = fmpy not installed in this Python environment",
        )
        return write_example_report(report_path, lines)

    from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
    from VeraGridEngine.Devices.Substation.bus import Bus
    from VeraGridEngine.Devices.Injections.load import Load
    from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType

    grid = SimpleNamespace(var_factory=VarFactory(name="ExampleEmtCsVarFactory"))
    load = Load(name="ImportedLoad", P=0.0, Q=0.0)
    load.device_type = DeviceType.LoadDevice
    bus = Bus(name="ExampleBus", Vnom=10.0)
    bus._emt_model = Block()
    load._bus = bus

    request = FmuDeviceAttachmentRequest(
        fmu_path=fmu_path,
        domain=FmuDeviceDomain.EMT,
        mode=FmuInterfaceMode.CO_SIMULATION,
        input_bindings=tuple(),
        output_bindings=(
            FmuRefBinding(VarPowerFlowRefferenceType.i_A, "i_a_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.i_B, "i_b_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.i_C, "i_c_out"),
        ),
        output_defaults=(
            FmuReferenceValue(VarPowerFlowRefferenceType.i_A, 0.0),
            FmuReferenceValue(VarPowerFlowRefferenceType.i_B, 0.0),
            FmuReferenceValue(VarPowerFlowRefferenceType.i_C, 0.0),
        ),
        extraction_root=output_dir,
    )

    attached_block: Block = attach_fmu_to_device(load, grid, request)
    load.idtag = "example-emt-cs-device"
    problem = _ExampleEmtProblem(attached_block)
    register_emt_fmu_cs_device(problem, load, attached_block)
    boundary_updater = build_emt_boundary_updater(problem)

    params = np.zeros(3, dtype=float)
    try:
        boundary_updater.update(0.0, np.zeros(1, dtype=float), params)
        boundary_updater.update(1e-3, np.zeros(1, dtype=float), params)
    finally:
        boundary_updater.close()

    lines: tuple[str, ...] = (
        f"fmu_path = {fmu_path}",
        f"mode = {request.mode.value}",
        f"boundary_calls = {problem.calls}",
    ) + _build_emt_results_report_lines(params, ("iA_final", "iB_final", "iC_final"))
    return write_example_report(report_path, lines)


def run_emt_me_example(output_dir: Path) -> Path:
    """Run the full EMT Model Exchange FMU device example.

    :param output_dir: Output directory used for the FMU and the report.
    :return: Generated report path.
    """

    fmu_path: Path = export_example_emt_me_fmu(output_dir)
    report_path: Path = output_dir / "emt_me_example_report.txt"
    if _has_fmpy():
        pass
    else:
        lines: tuple[str, ...] = (
            f"fmu_path = {fmu_path}",
            "mode = ModelExchange",
            "status = skipped",
            "reason = fmpy not installed in this Python environment",
        )
        return write_example_report(report_path, lines)

    from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
    from VeraGridEngine.Devices.Substation.bus import Bus
    from VeraGridEngine.Devices.Injections.load import Load
    from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType

    grid = SimpleNamespace(var_factory=VarFactory(name="ExampleEmtMeVarFactory"))
    load = Load(name="ImportedLoad", P=0.0, Q=0.0)
    load.device_type = DeviceType.LoadDevice
    bus = Bus(name="ExampleBus", Vnom=10.0)
    load._bus = bus

    request = FmuDeviceAttachmentRequest(
        fmu_path=fmu_path,
        domain=FmuDeviceDomain.EMT,
        mode=FmuInterfaceMode.MODEL_EXCHANGE,
        input_bindings=(FmuRefBinding(VarPowerFlowRefferenceType.v_A, "u"),),
        output_bindings=(
            FmuRefBinding(VarPowerFlowRefferenceType.i_A, "i_a_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.i_B, "i_b_out"),
            FmuRefBinding(VarPowerFlowRefferenceType.i_C, "i_c_out"),
        ),
        output_defaults=(
            FmuReferenceValue(VarPowerFlowRefferenceType.i_A, 0.0),
            FmuReferenceValue(VarPowerFlowRefferenceType.i_B, 0.0),
            FmuReferenceValue(VarPowerFlowRefferenceType.i_C, 0.0),
        ),
        extraction_root=output_dir,
        integration_method=FmuMeIntegrationMethod.EXPLICIT_EULER,
    )

    attached_block: Block = attach_fmu_to_device(load, grid, request)
    load.idtag = "example-emt-me-device"
    bus_voltage_var = Var("example_bus_v_a")
    bus._emt_model = Block(external_mapping={VarPowerFlowRefferenceType.v_A: bus_voltage_var})
    problem = _ExampleEmtProblem(attached_block, bus_voltage_var)
    register_emt_fmu_me_device(problem, load, attached_block)
    boundary_updater = build_emt_boundary_updater(problem)

    x_snapshot = np.array([1.0], dtype=float)
    params = np.zeros(3, dtype=float)
    try:
        boundary_updater.update(0.0, x_snapshot, params)
        boundary_updater.update(1e-3, x_snapshot, params)
    finally:
        boundary_updater.close()

    lines: tuple[str, ...] = (
        f"fmu_path = {fmu_path}",
        f"mode = {request.mode.value}",
        f"boundary_calls = {problem.calls}",
    ) + _build_emt_results_report_lines(params, ("iA_final", "iB_final", "iC_final"))
    return write_example_report(report_path, lines)
