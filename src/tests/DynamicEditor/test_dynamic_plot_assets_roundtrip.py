from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6 import QtCore
from PySide6 import QtWidgets

from VeraGrid.Gui.Main.SubClasses.Results.dynamics_results_handler import (
    DynamicsResultsHandler,
    DynamicPlotCandidate,
    DynamicPlotParameter,
    DynamicResultSeries,
    collect_dynamic_model_plot_parameters,
    ensure_dynamic_plot_event_group,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import initialize_connected_bus_models_for_editor_assignment
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.dynamic_plot import DynamicPlot
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.file_save import FileSavingOptions, save_veragrid_circuit
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const
from VeraGridEngine.Utils.Symbolic.templates_common_functions import connect_bus_variables_emt, connect_bus_variables_rms
from VeraGridEngine.enumerations import (DeviceType, FileType, PlotSimulationType, DynamicSimulationMode,
                                         DynamicPlotEntryKind, ParamPowerFlowReferenceType,
                                         DynamicPlotMode, DynamicPlotEntryRole)


def ensure_qt_application() -> QtWidgets.QApplication:
    """
    Ensure a Qt core application exists for Qt model creation.

    :return: Existing or newly created Qt core application.
    """
    application: QtCore.QCoreApplication | None = QtCore.QCoreApplication.instance()
    if application is None:
        return QtWidgets.QApplication(list())
    else:
        if isinstance(application, QtWidgets.QApplication):
            return application
        else:
            return QtWidgets.QApplication(list())


def build_pre_simulation_rms_circuit() -> MultiCircuit:
    """
    Build one minimal circuit with declarative RMS dynamic variables.

    :return: Circuit configured for the pre-simulation dynamic plot editor.
    """
    circuit: MultiCircuit = MultiCircuit(name="pre-sim-rms")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    omega_var: Var = circuit.var_factory.add_var(name="omega_ref", uid=1)
    efd_var: Var = circuit.var_factory.add_var(name="efd", uid=2)
    generator.rms_model = Block(
        state_vars=[omega_var],
        algebraic_vars=[efd_var],
        parameters={omega_var: Const(1.05)},
        api_obj_mapping={ParamPowerFlowReferenceType.omega_ref: omega_var},
        event_dict={efd_var: Const(0.9)},
    )
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_rms_events_group(obj=RmsEventsGroup(idtag="rms-group-a", name="RMS Group A"))
    return circuit


def build_pre_simulation_editor_style_rms_circuit() -> MultiCircuit:
    """
    Build one minimal circuit whose RMS model matches the Dynamic Editor wrapper structure.

    :return: Circuit configured with one root block that stores plottable vars in a child block.
    """
    circuit: MultiCircuit = MultiCircuit(name="pre-sim-editor-rms")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    omega_var: Var = circuit.var_factory.add_var(name="omega", uid=11)
    efd_var: Var = circuit.var_factory.add_var(name="efd", uid=12)
    editor_child_block: Block = Block(
        state_vars=[omega_var],
        algebraic_vars=[efd_var],
        name="editor-child-rms",
    )
    generator.rms_model = Block(children=[editor_child_block], name="editor-root-rms")
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_rms_events_group(obj=RmsEventsGroup(idtag="rms-group-a", name="RMS Group A"))
    return circuit


def build_pre_simulation_editor_style_emt_circuit() -> MultiCircuit:
    """
    Build one minimal circuit whose EMT model matches the Dynamic Editor wrapper structure.

    :return: Circuit configured with one root block that stores plottable vars in a child block.
    """
    circuit: MultiCircuit = MultiCircuit(name="pre-sim-editor-emt")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    omega_var: Var = circuit.var_factory.add_var(name="omega", uid=21)
    domega_var: Var = circuit.var_factory.add_var(name="domega", uid=22)
    editor_child_block: Block = Block(
        state_vars=[omega_var],
        diff_vars=[domega_var],
        name="editor-child-emt",
    )
    generator.emt_model = Block(children=[editor_child_block], name="editor-root-emt")
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_emt_events_group(obj=EmtEventsGroup(idtag="emt-group-a", name="EMT Group A"))
    return circuit


def build_parameter_collection_block() -> Block:
    """
    Build one block with parameters exposed through API mapping and event dict.

    :return: Block configured for parameter collection tests.
    """
    api_parameter: Var = Var(name="api_parameter", uid=801)
    duplicate_parameter: Var = Var(name="duplicate_parameter", uid=802)
    event_only_parameter: Var = Var(name="event_only_parameter", uid=803)
    block: Block = Block(
        parameters={api_parameter: Const(1.0), duplicate_parameter: Const(2.0), event_only_parameter: Const(3.0)},
        api_obj_mapping={ParamPowerFlowReferenceType.K: api_parameter, ParamPowerFlowReferenceType.Kp: duplicate_parameter},
        event_dict={duplicate_parameter: Const(4.0), event_only_parameter: Const(5.0)},
    )
    return block


def build_pre_simulation_rms_circuit_without_event_groups() -> MultiCircuit:
    """
    Build one minimal RMS pre-simulation circuit without any event groups.

    :return: Circuit configured to test on-demand RMS event-group creation.
    """
    circuit: MultiCircuit = MultiCircuit(name="pre-sim-rms-no-groups")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    omega_var: Var = circuit.var_factory.add_var(name="omega", uid=61)
    generator.rms_model = Block(state_vars=[omega_var])
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    return circuit


def build_pre_simulation_emt_circuit_without_event_groups() -> MultiCircuit:
    """
    Build one minimal EMT pre-simulation circuit without any event groups.

    :return: Circuit configured to test on-demand EMT event-group creation.
    """
    circuit: MultiCircuit = MultiCircuit(name="pre-sim-emt-no-groups")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    omega_var: Var = circuit.var_factory.add_var(name="omega", uid=71)
    generator.emt_model = Block(state_vars=[omega_var])
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    return circuit


class FakeEventsGroupsDialog(QtWidgets.QDialog):
    """
    Minimal dialog double used to test event-group creation decisions.
    """

    __slots__ = ("_dialog_code", "_group_name")

    def __init__(self, dialog_code: int, group_name: str) -> None:
        """
        Build the fake dialog.

        :param dialog_code: Dialog result returned by ``exec``.
        :param group_name: Group name returned by ``get_name``.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self)
        self._dialog_code: int = dialog_code
        self._group_name: str = group_name

    def exec(self) -> int:
        """
        Return the configured dialog result.

        :return: Configured Qt dialog code.
        """
        return self._dialog_code

    def get_name(self) -> str:
        """
        Return the configured group name.

        :return: Configured group name.
        """
        return self._group_name




def build_rms_results_from_generator(generator: Generator,
                                     variable_name: str,
                                     variable_uid: int) -> RmsResults:
    """
    Build one minimal RMS results object for the given generator.

    :param generator: Generator that owns the result variable.
    :param variable_name: Result variable name.
    :param variable_uid: Result variable uid.
    :return: Minimal RMS results object.
    """
    variable: Var = Var(name=variable_name, uid=variable_uid)
    results: RmsResults = RmsResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        rms_events_group_names=np.array(["RMS Group A"], dtype=str),
        rms_events_group_idtags=np.array(["rms-group-a"], dtype=str),
        variables=[variable],
        uid2idx={variable_uid: 0},
        vars_glob_name2uid={generator.idtag + ":" + variable_name + ":" + str(variable_uid): variable_uid},
        devices_vars_info={generator: [variable]},
    )
    results.values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)
    results.parameter_value_maps[0][str(generator.idtag) + ":omega_ref"] = 1.05
    return results


def build_rms_results_from_bus(bus: Bus,
                               variable_name: str,
                               variable_uid: int) -> RmsResults:
    """
    Build one minimal RMS results object for one bus voltage variable.

    :param bus: Bus that owns the result variable.
    :param variable_name: Result variable name.
    :param variable_uid: Result variable uid.
    :return: Minimal RMS results object.
    """
    variable: Var = Var(name=variable_name, uid=variable_uid)
    results: RmsResults = RmsResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        rms_events_group_names=np.array(["RMS Group A"], dtype=str),
        rms_events_group_idtags=np.array(["rms-group-a"], dtype=str),
        variables=[variable],
        uid2idx={variable_uid: 0},
        vars_glob_name2uid={bus.idtag + ":" + variable_name + ":" + str(variable_uid): variable_uid},
        devices_vars_info={bus: [variable]},
    )
    results.values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)
    return results


def build_emt_results_from_generator_diff_var(generator: Generator,
                                              variable_name: str,
                                              variable_uid: int) -> EmtResults:
    """
    Build one minimal EMT results object for one differential variable.

    :param generator: Generator that owns the result variable.
    :param variable_name: Result variable name.
    :param variable_uid: Result variable uid.
    :return: Minimal EMT results object.
    """
    diff_variable: Var = Var(name=variable_name, uid=variable_uid)
    results: EmtResults = EmtResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        emt_events_group_names=np.array(["EMT Group A"], dtype=str),
        emt_events_group_idtags=np.array(["emt-group-a"], dtype=str),
        variables=list(),
        diff_variables=[diff_variable],
        uid2idx_vars=dict(),
        uid2idx_diff={variable_uid: 0},
        vars_glob_name2uid={generator.idtag + ":" + variable_name + ":" + str(variable_uid): variable_uid},
        devices_vars_info={generator: [diff_variable]},
    )
    results.diff_values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)
    return results


def build_emt_results_from_bus(bus: Bus,
                               variable_name: str,
                               variable_uid: int) -> EmtResults:
    """
    Build one minimal EMT results object for one bus voltage variable.

    :param bus: Bus that owns the result variable.
    :param variable_name: Result variable name.
    :param variable_uid: Result variable uid.
    :return: Minimal EMT results object.
    """
    variable: Var = Var(name=variable_name, uid=variable_uid)
    results: EmtResults = EmtResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        emt_events_group_names=np.array(["EMT Group A"], dtype=str),
        emt_events_group_idtags=np.array(["emt-group-a"], dtype=str),
        variables=[variable],
        diff_variables=list(),
        uid2idx_vars={variable_uid: 0},
        uid2idx_diff=dict(),
        vars_glob_name2uid={bus.idtag + ":" + variable_name + ":" + str(variable_uid): variable_uid},
        devices_vars_info={bus: [variable]},
    )
    results.values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)
    return results


def test_dynamic_plot_asset_roundtrip_preserves_semantic_fields(tmp_path: Path) -> None:
    """
    Verify that persistent dynamic plot assets survive a ``.veragrid`` roundtrip.

    :param tmp_path: Temporary directory provided by pytest.
    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit(name="dynamic-plot-assets")
    plot_asset: DynamicPlot = DynamicPlot(name="Plot 1", simulation_type=PlotSimulationType.RMS)
    circuit.add_dynamic_plot(obj=plot_asset)

    curve_asset: DynamicPlotEntry = DynamicPlotEntry(
        variable=None,
        plot=plot_asset,
        group=None,
        device=None,
        simulation_type=PlotSimulationType.RMS,
        event_group_idtag="rms-group-a",
        event_group_name="RMS Group A",
        curve_device_type=DeviceType.LoadDevice,
        device_idtag="load-a",
        device_name_hint="Load A",
        variable_name="p_load",
        result_path_kind="values",
        variable_custom_name="Load A - p_load - RMS Group A",
        enabled=True,
        runtime_series_key_payload="payload",
        name="Curve 1",
    )
    circuit.add_dynamic_plot_entry(obj=curve_asset)

    file_name: Path = tmp_path / "dynamic_plot_assets.veragrid"
    options: FileSavingOptions = FileSavingOptions(file_type=FileType.VeraGrid)
    save_veragrid_circuit(circuit=circuit, file_name=str(file_name), options=options)

    loader: FileOpen = FileOpen(file_name=str(file_name))
    loaded_circuit: MultiCircuit | None = loader.open()

    assert loaded_circuit is not None
    assert len(loaded_circuit.dynamic_plots) == 1
    assert len(loaded_circuit.dynamic_plot_entries) == 1

    loaded_plot: DynamicPlot = loaded_circuit.dynamic_plots[0]
    loaded_entry: DynamicPlotEntry = loaded_circuit.dynamic_plot_entries[0]

    assert loaded_plot.name == "Plot 1"
    assert loaded_plot.simulation_type == PlotSimulationType.RMS
    assert loaded_entry.plot is loaded_plot
    assert loaded_entry.variable is None
    assert loaded_entry.group is None
    assert loaded_entry.simulation_type == PlotSimulationType.RMS
    assert loaded_entry.event_group_idtag == "rms-group-a"
    assert loaded_entry.event_group_name == "RMS Group A"
    assert loaded_entry.curve_device_type == DeviceType.LoadDevice
    assert loaded_entry.device_idtag == "load-a"
    assert loaded_entry.device_name_hint == "Load A"
    assert loaded_entry.variable_name == "p_load"
    assert loaded_entry.result_path_kind == "values"
    assert loaded_entry.variable_custom_name == "Load A - p_load - RMS Group A"
    assert loaded_entry.enabled is True
    assert loaded_entry.runtime_series_key_payload == "payload"


def test_pre_simulation_handler_creates_persistent_assets() -> None:
    """
    Verify that the pre-simulation handler writes plot definitions into circuit assets.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")

    created: bool = handler.create_plot_group(name="Plot 1")
    assert created is True

    first_candidate_list = handler.series_by_var_uid[1]
    first_candidate: DynamicPlotCandidate = first_candidate_list[0]
    inserted: bool = handler.add_candidate_to_group(group_name="Plot 1", candidate=first_candidate)

    assert inserted is True
    assert len(circuit.dynamic_plots) == 1
    assert len(circuit.dynamic_plot_entries) == 1
    assert circuit.dynamic_plots[0].simulation_type == PlotSimulationType.RMS
    assert circuit.dynamic_plot_entries[0].event_group_idtag == "rms-group-a"
    assert circuit.dynamic_plot_entries[0].device_idtag == "gen-a"
    assert circuit.dynamic_plot_entries[0].variable_name == "omega_ref"


def test_collect_dynamic_model_plot_parameters_keeps_deterministic_order_without_duplicates() -> None:
    """
    Verify that parameters merge API mapping and event dict without duplicates.

    :return: None.
    """
    block: Block = build_parameter_collection_block()
    parameters: List[DynamicPlotParameter] = collect_dynamic_model_plot_parameters(model=block)
    parameter_names: List[str] = [parameter.get_display_name() for parameter in parameters]

    assert parameter_names == ["api_parameter", "duplicate_parameter", "event_only_parameter"]


def test_ensure_dynamic_plot_event_group_reuses_existing_rms_group() -> None:
    """
    Verify that the helper reuses an existing RMS event group without opening creation flow.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()

    group_asset: RmsEventsGroup | EmtEventsGroup | None = ensure_dynamic_plot_event_group(
        circuit=circuit,
        simulation_type=PlotSimulationType.RMS,
        parent=None,
    )

    assert isinstance(group_asset, RmsEventsGroup)
    assert len(circuit.rms_events_groups) == 1
    assert str(group_asset.idtag) == "rms-group-a"


def test_pre_simulation_tree_exposes_variables_and_parameters_sections() -> None:
    """
    Verify that one device shows explicit Variables and Parameters sections.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    model = handler.tree_model

    assert model is not None
    device_type_item = model.item(0, 0)
    device_item = device_type_item.child(0, 0)
    variables_section_item = device_item.child(0, 0)
    parameters_section_item = device_item.child(1, 0)

    assert variables_section_item.text() == "Variables"
    assert parameters_section_item.text() == "Parameters"
    assert variables_section_item.rowCount() > 0
    assert parameters_section_item.rowCount() > 0


def test_pre_simulation_parameter_candidate_creates_parameter_entry() -> None:
    """
    Verify that dragging a parameter candidate persists a parameter plot entry.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    parameter_candidate_list: List[DynamicPlotCandidate] = handler.candidates_by_parameter_name.get("omega_ref", list())
    assert len(parameter_candidate_list) > 0
    inserted: bool = handler.add_candidate_to_group(group_name="Plot 1", candidate=parameter_candidate_list[0])

    assert inserted is True
    assert len(circuit.dynamic_plot_entries) == 1
    assert circuit.dynamic_plot_entries[0].entry_kind == DynamicPlotEntryKind.PARAMETER
    assert circuit.dynamic_plot_entries[0].variable_name == "omega_ref"


def test_parameter_entry_resolves_to_constant_trace_after_results_exist() -> None:
    """
    Verify that a parameter entry resolves as a constant trace after simulation.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    parameter_candidate_list: List[DynamicPlotCandidate] = handler.candidates_by_parameter_name.get("omega_ref", list())
    assert len(parameter_candidate_list) > 0
    assert handler.add_candidate_to_group(group_name="Plot 1", candidate=parameter_candidate_list[0]) is True

    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: RmsResults = build_rms_results_from_generator(generator=generator, variable_name="omega", variable_uid=101)
    results_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)

    plot_group = results_handler.plot_groups.get_group(name="Plot 1")
    assert plot_group is not None
    stored_entries = plot_group.get_series()
    assert len(stored_entries) == 1
    assert isinstance(stored_entries[0], DynamicPlotEntry)

    parameter_plot_data = results_handler._get_parameter_plot_data(entry=stored_entries[0])
    assert parameter_plot_data is not None
    _, parameter_values = parameter_plot_data
    assert np.array_equal(parameter_values, np.array([1.05, 1.05], dtype=float))


def test_pre_simulation_handler_creates_missing_rms_group_before_adding_candidate() -> None:
    """
    Verify that adding a pre-simulation RMS candidate creates a missing event group first.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit_without_event_groups()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    synthetic_candidate: DynamicPlotCandidate = DynamicPlotCandidate(
        simulation_type=PlotSimulationType.RMS,
        entry_kind=DynamicPlotEntryKind.VARIABLE,
        event_group_idtag="",
        event_group_name="",
        device_type=DeviceType.GeneratorDevice,
        device_idtag="gen-a",
        device_label="Generator A",
        bus_label="",
        variable_name="omega",
        result_path_kind="values",
        variable_custom_name="Generator A - omega",
        var=Var(name="omega", uid=61),
        parameter=None,
    )

    assert synthetic_candidate._event_group_name == ""


def test_pre_simulation_dynamic_plot_assets_survive_roundtrip_without_results(tmp_path: Path) -> None:
    """
    Verify that handler-created pre-simulation plot assets survive save/open.

    :param tmp_path: Temporary directory provided by pytest.
    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    first_candidate_list = handler.series_by_var_uid[1]
    first_candidate: DynamicPlotCandidate = first_candidate_list[0]
    assert handler.add_candidate_to_group(group_name="Plot 1", candidate=first_candidate) is True

    file_name: Path = tmp_path / "pre_simulation_dynamic_plot_assets.veragrid"
    options: FileSavingOptions = FileSavingOptions(file_type=FileType.VeraGrid)
    save_veragrid_circuit(circuit=circuit, file_name=str(file_name), options=options)

    loader: FileOpen = FileOpen(file_name=str(file_name))
    loaded_circuit: MultiCircuit | None = loader.open()

    assert loaded_circuit is not None
    assert len(loaded_circuit.dynamic_plots) == 1
    assert len(loaded_circuit.dynamic_plot_entries) == 1
    assert loaded_circuit.dynamic_plots[0].name == "Plot 1"
    assert loaded_circuit.dynamic_plots[0].simulation_type == PlotSimulationType.RMS
    assert loaded_circuit.dynamic_plot_entries[0].variable_name == "omega_ref"
    assert loaded_circuit.dynamic_plot_entries[0].event_group_idtag == "rms-group-a"


def test_pre_simulation_created_asset_binds_after_results_exist() -> None:
    """
    Verify that a pre-simulation plot definition binds automatically after RMS results exist.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    first_candidate_list = handler.series_by_var_uid[1]
    first_candidate: DynamicPlotCandidate = first_candidate_list[0]
    assert handler.add_candidate_to_group(group_name="Plot 1", candidate=first_candidate) is True

    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: RmsResults = build_rms_results_from_generator(generator=generator, variable_name="omega", variable_uid=101)
    results_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)

    group = results_handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    restored_entries = group.get_series()
    assert len(restored_entries) == 1
    assert results_handler.get_plots_model() is not None
    assert isinstance(restored_entries[0], DynamicPlotEntry)
    assert restored_entries[0].variable_name == "omega_ref"


def test_pre_simulation_xy_plot_rebinds_roles_after_results_exist() -> None:
    """
    Verify that pre-simulation XY plot slots remain populated after RMS results exist.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot XY", mode=DynamicPlotMode.XY) is True

    omega_candidate: DynamicPlotCandidate = handler.series_by_var_uid[1][0]
    efd_candidate: DynamicPlotCandidate = handler.series_by_var_uid[2][0]
    assert handler.add_candidate_to_group_with_role(group_name="Plot XY",
                                                    candidate=omega_candidate,
                                                    role=DynamicPlotEntryRole.X_AXIS) is True
    assert handler.add_candidate_to_group_with_role(group_name="Plot XY",
                                                    candidate=efd_candidate,
                                                    role=DynamicPlotEntryRole.Y_AXIS) is True

    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: RmsResults = build_rms_results_from_generator(generator=generator, variable_name="omega_ref", variable_uid=101)
    extra_variable: Var = Var(name="efd", uid=102)
    results.variables.append(extra_variable)
    results.uid2idx[102] = 1
    results.vars_glob_name2uid[str(generator.idtag) + ":efd:102"] = 102
    results.devices_vars_info[generator] = [results.variables[0], extra_variable]
    expanded_values: np.ndarray = np.zeros((results.nt, 2, results.ng), dtype=float)
    expanded_values[:, 0, :] = results.values[:, 0, :]
    expanded_values[:, 1, :] = np.array([[2.0], [3.0]], dtype=float)
    results.values = expanded_values
    results.nv = 2

    results_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)
    assert len(circuit.dynamic_plot_entries) == 2
    assert circuit.dynamic_plot_entries[0].role == DynamicPlotEntryRole.X_AXIS
    assert circuit.dynamic_plot_entries[1].role == DynamicPlotEntryRole.Y_AXIS
    group = results_handler.plot_groups.get_group(name="Plot XY")
    assert group is not None
    assert group.get_mode() == DynamicPlotMode.XY
    x_entry = group.get_entry_for_role(role=DynamicPlotEntryRole.X_AXIS)
    y_entry = group.get_entry_for_role(role=DynamicPlotEntryRole.Y_AXIS)
    assert isinstance(x_entry, DynamicResultSeries) or isinstance(x_entry, DynamicPlotEntry)
    assert isinstance(y_entry, DynamicResultSeries) or isinstance(y_entry, DynamicPlotEntry)
    assert x_entry is not None
    assert y_entry is not None


def test_post_simulation_xy_plot_accepts_runtime_series_assignment() -> None:
    """
    Verify that a post-simulation XY plot accepts runtime series assignment into X and Y slots.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_rms_circuit()
    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: RmsResults = build_rms_results_from_generator(generator=generator, variable_name="omega_ref", variable_uid=101)
    extra_variable: Var = Var(name="efd", uid=102)
    results.variables.append(extra_variable)
    results.uid2idx[102] = 1
    results.vars_glob_name2uid[str(generator.idtag) + ":efd:102"] = 102
    results.devices_vars_info[generator] = [results.variables[0], extra_variable]
    expanded_values: np.ndarray = np.zeros((results.nt, 2, results.ng), dtype=float)
    expanded_values[:, 0, :] = results.values[:, 0, :]
    expanded_values[:, 1, :] = np.array([[2.0], [3.0]], dtype=float)
    results.values = expanded_values
    results.nv = 2

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)
    assert handler.create_plot_group(name="Plot XY", mode=DynamicPlotMode.XY) is True
    omega_series: DynamicResultSeries = handler.series_by_var_uid[101][0]
    efd_series: DynamicResultSeries = handler.series_by_var_uid[102][0]
    assert handler.add_series_to_group_with_role(group_name="Plot XY",
                                                 series_key=omega_series.get_key(),
                                                 role=DynamicPlotEntryRole.X_AXIS) is True
    assert handler.add_series_to_group_with_role(group_name="Plot XY",
                                                 series_key=efd_series.get_key(),
                                                 role=DynamicPlotEntryRole.Y_AXIS) is True

    group = handler.plot_groups.get_group(name="Plot XY")
    assert group is not None
    assert isinstance(group.get_entry_for_role(role=DynamicPlotEntryRole.X_AXIS), DynamicResultSeries)
    assert isinstance(group.get_entry_for_role(role=DynamicPlotEntryRole.Y_AXIS), DynamicResultSeries)


def test_pre_simulation_handler_discovers_editor_style_rms_variables() -> None:
    """
    Verify that pre-simulation RMS discovery traverses Dynamic Editor child blocks.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_editor_style_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")

    assert 11 in handler.series_by_var_uid
    assert 12 in handler.series_by_var_uid
    assert handler.series_by_var_uid[11][0]._variable_name == "omega"
    assert handler.series_by_var_uid[12][0]._variable_name == "efd"


def test_template_style_pre_simulation_rms_tree_includes_bus_voltage_variables() -> None:
    """
    Verify that the RMS pre-simulation tree includes bus voltage vars when the bus model already exists.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="template-rms-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_rms_events_group(obj=RmsEventsGroup(idtag="rms-group-a", name="RMS Group A"))

    generator_model = Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=13)])
    connect_bus_variables_rms(device=generator, model=generator_model, var_factory=circuit.var_factory)
    generator.rms_model = generator_model

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    bus_variables = handler.tree_data[DeviceType.BusDevice][bus].get_variables()
    bus_variable_names = [variable.name for variable in bus_variables]

    assert "Vm" in bus_variable_names
    assert "Va" in bus_variable_names


def test_uninitialized_rms_bus_does_not_appear_in_pre_simulation_tree() -> None:
    """
    Verify that an uninitialized RMS bus does not appear in the pre-simulation tree.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="editor-rms-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    generator.rms_model = Block(children=[Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=16)])])
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_rms_events_group(obj=RmsEventsGroup(idtag="rms-group-a", name="RMS Group A"))

    assert bus.rms_model.empty() is True

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")

    assert DeviceType.BusDevice not in handler.tree_data


def test_editor_assignment_initializes_rms_bus_before_tree_discovery() -> None:
    """
    Verify that the Dynamic Editor RMS assignment path initializes the connected bus before tree discovery.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="editor-rms-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    generator.rms_model = Block(children=[Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=16)])])
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_rms_events_group(obj=RmsEventsGroup(idtag="rms-group-a", name="RMS Group A"))

    initialize_connected_bus_models_for_editor_assignment(api_object=generator,
                                                          circuit=circuit,
                                                          var_factory=circuit.var_factory,
                                                          mode=DynamicSimulationMode.RMS)

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    bus_variables = handler.tree_data[DeviceType.BusDevice][bus].get_variables()
    bus_variable_names = [variable.name for variable in bus_variables]

    assert "Vm" in bus_variable_names
    assert "Va" in bus_variable_names


def test_post_simulation_rms_results_tree_includes_bus_voltage_variables() -> None:
    """
    Verify that the RMS results tree can expose bus voltage variables for binding.

    :return: None.
    """
    ensure_qt_application()
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    results: RmsResults = build_rms_results_from_bus(bus=bus, variable_name="Vm", variable_uid=17)

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results)

    assert DeviceType.BusDevice in handler.tree_data
    assert bus in handler.tree_data[DeviceType.BusDevice]
    assert handler.tree_data[DeviceType.BusDevice][bus].get_variables()[0].name == "Vm"


def test_pre_simulation_handler_marks_editor_style_emt_diff_variables() -> None:
    """
    Verify that pre-simulation EMT discovery keeps child differential vars on ``diff_values``.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_editor_style_emt_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="EMT")

    assert 21 in handler.series_by_var_uid
    assert 22 in handler.series_by_var_uid
    assert handler.series_by_var_uid[21][0]._result_path_kind == "values"
    assert handler.series_by_var_uid[22][0]._result_path_kind == "diff_values"


def test_editor_style_pre_simulation_asset_binds_after_rms_results_exist() -> None:
    """
    Verify that a Dynamic Editor-style RMS variable binds after runtime results exist.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_editor_style_rms_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="RMS")
    assert handler.create_plot_group(name="Plot 1") is True

    editor_candidate: DynamicPlotCandidate = handler.series_by_var_uid[11][0]
    assert handler.add_candidate_to_group(group_name="Plot 1", candidate=editor_candidate) is True

    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: RmsResults = build_rms_results_from_generator(generator=generator, variable_name="omega", variable_uid=111)
    results_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)

    group = results_handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    restored_entries = group.get_series()
    assert len(restored_entries) == 1
    assert restored_entries[0].get_var().uid == 111


def test_editor_style_pre_simulation_asset_binds_after_emt_diff_results_exist() -> None:
    """
    Verify that a Dynamic Editor-style EMT differential variable binds to ``diff_values``.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = build_pre_simulation_editor_style_emt_circuit()
    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="EMT")
    assert handler.create_plot_group(name="Plot 1") is True

    editor_candidate: DynamicPlotCandidate = handler.series_by_var_uid[22][0]
    assert handler.add_candidate_to_group(group_name="Plot 1", candidate=editor_candidate) is True

    generator: Generator = circuit.get_elements_by_type(device_type=DeviceType.GeneratorDevice)[0]
    results: EmtResults = build_emt_results_from_generator_diff_var(generator=generator,
                                                                    variable_name="domega",
                                                                    variable_uid=222)
    results_handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results, circuit=circuit)

    assert 222 in results_handler.series_by_var_uid
    group = results_handler.plot_groups.get_group(name="Plot 1")
    assert group is not None
    restored_entries = group.get_series()
    assert len(restored_entries) == 1
    assert restored_entries[0].get_var().uid == 222


def test_template_style_pre_simulation_emt_tree_includes_bus_voltage_variables() -> None:
    """
    Verify that the EMT pre-simulation tree includes bus voltage vars when the bus shell already exists.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="template-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_emt_events_group(obj=EmtEventsGroup(idtag="emt-group-a", name="EMT Group A"))

    generator_model = Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=31)])
    connect_bus_variables_emt(device=generator,
                              model=generator_model,
                              var_factory=circuit.var_factory,
                              allow_deferred_connection=True,
                              grid=circuit)
    generator.emt_model = generator_model

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="EMT")
    bus_variables = handler.tree_data[DeviceType.BusDevice][bus].get_variables()
    bus_variable_names = [variable.name for variable in bus_variables]

    assert not any(name.startswith("v_N_") for name in bus_variable_names)
    assert len(bus_variable_names) > 0
    assert any(name.startswith("v_") for name in bus_variable_names)


def test_uninitialized_emt_bus_does_not_appear_in_pre_simulation_tree() -> None:
    """
    Verify that an uninitialized EMT bus does not appear in the pre-simulation tree.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="editor-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    generator.emt_model = Block(children=[Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=41)])])
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_emt_events_group(obj=EmtEventsGroup(idtag="emt-group-a", name="EMT Group A"))

    assert bus.emt_model.empty() is True

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="EMT")

    assert DeviceType.BusDevice not in handler.tree_data


def test_editor_assignment_initializes_emt_bus_before_tree_discovery() -> None:
    """
    Verify that the Dynamic Editor EMT assignment path initializes the connected bus before tree discovery.

    :return: None.
    """
    ensure_qt_application()
    circuit: MultiCircuit = MultiCircuit(name="editor-bus-tree")
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    generator: Generator = Generator(name="Generator A", idtag="gen-a")
    generator.bus = bus
    generator.emt_model = Block(children=[Block(state_vars=[circuit.var_factory.add_var(name="omega", uid=41)])])
    circuit.add_bus(bus)
    circuit.set_elements_list_by_type(device_type=DeviceType.GeneratorDevice, devices=[generator])
    circuit.add_emt_events_group(obj=EmtEventsGroup(idtag="emt-group-a", name="EMT Group A"))

    initialize_connected_bus_models_for_editor_assignment(api_object=generator,
                                                          circuit=circuit,
                                                          var_factory=circuit.var_factory,
                                                          mode=DynamicSimulationMode.EMT)

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=None, circuit=circuit, simulation_type="EMT")
    bus_variables = handler.tree_data[DeviceType.BusDevice][bus].get_variables()
    bus_variable_names = [variable.name for variable in bus_variables]

    assert not any(name.startswith("v_N_") for name in bus_variable_names)
    assert len(bus_variable_names) > 0
    assert any(name.startswith("v_") for name in bus_variable_names)


def test_post_simulation_emt_results_tree_includes_bus_voltage_variables() -> None:
    """
    Verify that the EMT results tree can expose bus voltage variables for binding.

    :return: None.
    """
    ensure_qt_application()
    bus: Bus = Bus(name="Bus A", idtag="bus-a")
    results: EmtResults = build_emt_results_from_bus(bus=bus,
                                                     variable_name="v_A_Bus_A_emt_template",
                                                     variable_uid=51)

    handler: DynamicsResultsHandler = DynamicsResultsHandler(results=results)

    assert DeviceType.BusDevice in handler.tree_data
    assert bus in handler.tree_data[DeviceType.BusDevice]
    assert handler.tree_data[DeviceType.BusDevice][bus].get_variables()[0].name == "v_A_Bus_A_emt_template"
