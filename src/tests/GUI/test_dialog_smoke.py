from __future__ import annotations

import ast
import copy
import gc
import multiprocessing
import queue
import tempfile
import traceback
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

import numpy as np
import pandas as pd
import shiboken6
from PySide6 import QtCore
from PySide6 import QtWidgets

import VeraGridEngine as vge
from VeraGrid.Gui.AboutDialogue.about_dialogue import AboutDialogueGuiGUI
from VeraGrid.Gui.AiAgent.ai_chat_dialogue import AiChatDialogue
from VeraGrid.Gui.Analysis.AnalysisDialogue import GridAnalysisGUI
from VeraGrid.Gui.CatalogueElementsDialogue.catalogue_elements_dialogue import CatalogueElementsSelectionDialogue
from VeraGrid.Gui.ContingencyPlanner.contingency_planner_dialogue import ContingencyPlannerGUI
from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_editor import ControllableShuntEditor
from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_editor import DcLineEditor
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.SolarPowerWizard.solar_power_wizzard import SolarPvWizard
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.WindPowerWizard.wind_power_wizzard import WindFarmWizard
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorQCurveEditor
from VeraGrid.Gui.DeviceEditors.LineEditor.line_editor import LineEditor
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_designer import LoadDesigner
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.DeviceEditors.TowerBuilder.LineBuilderDialogue import TowerBuilderGUI
from VeraGrid.Gui.DeviceEditors.Transformer3wEditor.transformer3w_editor import Transformer3WEditor
from VeraGrid.Gui.DeviceEditors.TransformerEditor.transformer_editor import TransformerEditor
from VeraGrid.Gui.Diagrams.Editors.bus_selector import BusSelectorDialogue
from VeraGrid.Gui.Diagrams.Editors.new_line_dialogue import NewMapLineDialogue
from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import SelectionDialog
from VeraGrid.Gui.Diagrams.SchematicWidget.diagram_bus_selection_dialogue import DiagramBusSelectorDialogue
from VeraGrid.Gui.DynamicEventsDialog.dynamic_events_editor import DynamicEventEditor
from VeraGrid.Gui.DynamicEventsDialog.dynamic_events_editor_support import DynamicEventsGroupsDialog
from VeraGrid.Gui.DynamicEventsDialog.dynamic_events_editor_support import SwitchSequenceDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.jmarti_line_emt_dialog import JMartiLineEmtDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupArrayLinearDialog
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.lookup_table_dialog import LookupMatrixLinearDialog
from VeraGrid.Gui.DynamicModelEditor.detachable_editor_tabs_widget import DynamicEditorPickerDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import DynamicBlockPropertiesDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_validation import ValidationSectionDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_window import DynamicEditorWorkspaceWindow
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_export import CgmesExportDialogue
from VeraGrid.Gui.FileDialogues.CGMESDialogue.cgmes_import import CgmesImportDialogue
from VeraGrid.Gui.FileDialogues.CoordinatesInput.coordinates_dialogue import CoordinatesInputGUI
from VeraGrid.Gui.FileDialogues.DgsDialogue.dgs_export import DgsExportDialogue
from VeraGrid.Gui.FileDialogues.DgsDialogue.dgs_import import DgsImportDialogue
from VeraGrid.Gui.FileDialogues.LoadCatalogue.catalogue_dialogue import CatalogueGUI
from VeraGrid.Gui.FileDialogues.MatpowerDialogue.matpower_export import MatpowerExportDialogue
from VeraGrid.Gui.FileDialogues.ProfilesInput.excel_dialog import ExcelDialog
from VeraGrid.Gui.FileDialogues.ProfilesInput.models_dialogue import ModelsInputGUI
from VeraGrid.Gui.FileDialogues.ProfilesInput.profile_dialogue import GeneratorsProfileOptionsDialogue
from VeraGrid.Gui.FileDialogues.ProfilesInput.profile_dialogue import ProfileInputGUI
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_export import PsseExportDialogue
from VeraGrid.Gui.FileDialogues.PsseDialogue.psse_import import PsseImportDialogue
from VeraGrid.Gui.FileDialogues.RosetaExplorer.RosetaExplorer import RosetaExplorerGUI
from VeraGrid.Gui.FileDialogues.ServerFileDialog.server_file_dialogue_window import ServerFileDialogue
from VeraGrid.Gui.FileDialogues.UcteDialogue.ucte_export import UcteExportDialogue
from VeraGrid.Gui.FmuTemplateEditor.fmu_template_editor import FmuTemplateEditorDialog
from VeraGrid.Gui.GridGenerator.grid_generator_dialogue import GridGeneratorGUI
from VeraGrid.Gui.GridMerge.grid_diff import GridDiffDialogue
from VeraGrid.Gui.GridMerge.grid_merge import GridMergeDialogue
from VeraGrid.Gui.GridReduce.grid_reduce import GridReduceDialogue
from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI
from VeraGrid.Gui.Main.object_select_window import ListSelectWindow
from VeraGrid.Gui.Main.object_select_window import ObjectSelectWindow
from VeraGrid.Gui.ProceduralGrid.map_warning import MapWarningDialog
from VeraGrid.Gui.ProceduralGrid.procedural_grid import ProceduralGridWindow
from VeraGrid.Gui.ProceduralGrid.voltage_warning import VoltageWarningDialog
from VeraGrid.Gui.rms_plot_variables_dialog import RmsPlotDialog
from VeraGrid.Gui.ShortCircuitEditor.short_circuit_selector import ShortCircuitSelector
from VeraGrid.Gui.SigmaAnalysis.sigma_analysis_dialogue import SigmaAnalysisGUI
from VeraGrid.Gui.SubstationDesigner.substation_designer import SubstationDesigner
from VeraGrid.Gui.SubstationDesigner.voltage_level_conversion import VoltageLevelConversionWizard
from VeraGrid.Gui.SyncDialogue.sync_dialogue import SyncDialogueWindow
from VeraGrid.Gui.SystemScaler.system_scaler import SystemScaler
from VeraGrid.Gui.dialog_lifecycle import delete_dialog_safely
from VeraGrid.Gui.dialog_lifecycle import is_dialog_available
from VeraGrid.Gui.general_dialogues import ArrayEditor
from VeraGrid.Gui.general_dialogues import CgmesOptionsSelector
from VeraGrid.Gui.general_dialogues import CheckListDialogue
from VeraGrid.Gui.general_dialogues import CorrectInconsistenciesDialogue
from VeraGrid.Gui.general_dialogues import CustomQuestionDialogue
from VeraGrid.Gui.general_dialogues import DeleteDialogue
from VeraGrid.Gui.general_dialogues import DeviceSelectorDialogue
from VeraGrid.Gui.general_dialogues import ElementsDialogue
from VeraGrid.Gui.general_dialogues import FileTypeSelector
from VeraGrid.Gui.general_dialogues import InputNumberDialogue
from VeraGrid.Gui.general_dialogues import InputSearchDialogue
from VeraGrid.Gui.general_dialogues import LogsDialogue
from VeraGrid.Gui.general_dialogues import NewConnectedDeviceDialogue
from VeraGrid.Gui.general_dialogues import NewProfilesStructureDialogue
from VeraGrid.Gui.general_dialogues import StartEndSelectionDialogue
from VeraGrid.Gui.general_dialogues import TimeReIndexDialogue
from VeraGrid.Gui.gui_functions import LookupMatrixEditorDialog
from VeraGrid.Gui.gui_functions import SequenceEditorDialog
from VeraGrid.Gui.object_column_filter_dialog import ObjectColumnFilterDialog
from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGrid.Session.session import SimulationSession
from VeraGrid.Session.dynamic_editor_workspace_session import DynamicEditorWorkspaceSession
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.enumerations import DynEditorGraphicsModes
from VeraGridEngine.enumerations import WaveformSequenceType


class DialogSmokeTarget(Enum):
    """
    Dialog classes with stable, cheap constructor fixtures.
    """

    ABOUT_DIALOGUE = "AboutDialogueGuiGUI"
    AI_CHAT_DIALOGUE = "AiChatDialogue"
    GRID_ANALYSIS = "GridAnalysisGUI"
    CATALOGUE_ELEMENTS = "CatalogueElementsSelectionDialogue"
    CONTINGENCY_PLANNER = "ContingencyPlannerGUI"
    CONTROLLABLE_SHUNT_EDITOR = "ControllableShuntEditor"
    DC_LINE_EDITOR = "DcLineEditor"
    SOLAR_PV_WIZARD = "SolarPvWizard"
    WIND_FARM_WIZARD = "WindFarmWizard"
    GENERATOR_Q_CURVE_EDITOR = "GeneratorQCurveEditor"
    LINE_EDITOR = "LineEditor"
    LOAD_DESIGNER = "LoadDesigner"
    TEMPLATE_DEVICE_EDITOR = "TemplateDeviceEditor"
    TOWER_BUILDER = "TowerBuilderGUI"
    TRANSFORMER_3W_EDITOR = "Transformer3WEditor"
    TRANSFORMER_EDITOR = "TransformerEditor"
    BUS_SELECTOR = "BusSelectorDialogue"
    NEW_MAP_LINE = "NewMapLineDialogue"
    MAP_SELECTION = "SelectionDialog"
    DIAGRAM_BUS_SELECTOR = "DiagramBusSelectorDialogue"
    DYNAMIC_EVENT_EDITOR = "DynamicEventEditor"
    SWITCH_SEQUENCE = "SwitchSequenceDialog"
    DYNAMIC_EVENTS_GROUPS = "DynamicEventsGroupsDialog"
    JMARTI_LINE_EMT = "JMartiLineEmtDialog"
    LOOKUP_ARRAY_LINEAR = "LookupArrayLinearDialog"
    LOOKUP_MATRIX_LINEAR = "LookupMatrixLinearDialog"
    DYNAMIC_BLOCK_EDITOR = "DynamicBlockEditorGUI"
    DYNAMIC_BLOCK_PROPERTIES = "DynamicBlockPropertiesDialog"
    DYNAMIC_EDITOR_PICKER = "DynamicEditorPickerDialog"
    DYNAMIC_EDITOR_WORKSPACE = "DynamicEditorWorkspaceWindow"
    VALIDATION_SECTION = "ValidationSectionDialog"
    CGMES_EXPORT = "CgmesExportDialogue"
    CGMES_IMPORT = "CgmesImportDialogue"
    COORDINATES_INPUT = "CoordinatesInputGUI"
    CATALOGUE = "CatalogueGUI"
    DGS_EXPORT = "DgsExportDialogue"
    DGS_IMPORT = "DgsImportDialogue"
    MATPOWER_EXPORT = "MatpowerExportDialogue"
    EXCEL_DIALOG = "ExcelDialog"
    MODELS_INPUT = "ModelsInputGUI"
    GENERATORS_PROFILE_OPTIONS = "GeneratorsProfileOptionsDialogue"
    PROFILE_INPUT = "ProfileInputGUI"
    PSSE_EXPORT = "PsseExportDialogue"
    PSSE_IMPORT = "PsseImportDialogue"
    ROSETA_EXPLORER = "RosetaExplorerGUI"
    SERVER_FILE = "ServerFileDialogue"
    UCTE_EXPORT = "UcteExportDialogue"
    FMU_TEMPLATE_EDITOR = "FmuTemplateEditorDialog"
    GRID_GENERATOR = "GridGeneratorGUI"
    GRID_DIFF = "GridDiffDialogue"
    GRID_MERGE = "GridMergeDialogue"
    GRID_REDUCE = "GridReduceDialogue"
    OBJECT_SELECT = "ObjectSelectWindow"
    LIST_SELECT = "ListSelectWindow"
    PROCEDURAL_GRID = "ProceduralGridWindow"
    MAP_WARNING = "MapWarningDialog"
    VOLTAGE_WARNING = "VoltageWarningDialog"
    RMS_PLOT = "RmsPlotDialog"
    SHORT_CIRCUIT_SELECTOR = "ShortCircuitSelector"
    SIGMA_ANALYSIS = "SigmaAnalysisGUI"
    SUBSTATION_DESIGNER = "SubstationDesigner"
    VOLTAGE_LEVEL_CONVERSION = "VoltageLevelConversionWizard"
    SYNC_DIALOGUE = "SyncDialogueWindow"
    SYSTEM_SCALER = "SystemScaler"
    NEW_PROFILES_STRUCTURE = "NewProfilesStructureDialogue"
    LOGS = "LogsDialogue"
    DEVICE_SELECTOR = "DeviceSelectorDialogue"
    NEW_CONNECTED_DEVICE = "NewConnectedDeviceDialogue"
    ELEMENTS = "ElementsDialogue"
    TIME_RE_INDEX = "TimeReIndexDialogue"
    CORRECT_INCONSISTENCIES = "CorrectInconsistenciesDialogue"
    CHECK_LIST = "CheckListDialogue"
    DELETE = "DeleteDialogue"
    INPUT_NUMBER = "InputNumberDialogue"
    INPUT_SEARCH = "InputSearchDialogue"
    START_END_SELECTION = "StartEndSelectionDialogue"
    CUSTOM_QUESTION = "CustomQuestionDialogue"
    ARRAY_EDITOR = "ArrayEditor"
    FILE_TYPE_SELECTOR = "FileTypeSelector"
    CGMES_OPTIONS_SELECTOR = "CgmesOptionsSelector"
    SEQUENCE_EDITOR = "SequenceEditorDialog"
    LOOKUP_MATRIX_EDITOR = "LookupMatrixEditorDialog"
    OBJECT_COLUMN_FILTER = "ObjectColumnFilterDialog"


class NamedObject:
    """
    Minimal object with the ``name`` attribute expected by selector dialogs.
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """
        Store the visible name.

        :param name: Visible object name.
        :return: None.
        """
        self.name: str = name

    def __str__(self) -> str:
        """
        Return the visible name.

        :return: Object name.
        """
        return self.name


class FakeSpinBox:
    """
    Minimal spin-box facade used by diagram dialogue constructors.
    """

    __slots__ = ()

    def value(self) -> float:
        """
        Return a stable default voltage.

        :return: Default voltage in kV.
        """
        return 110.0


class FakeMainUi:
    """
    Minimal GUI namespace required by a few diagram dialogues.
    """

    __slots__ = ("defaultBusVoltageSpinBox",)

    def __init__(self) -> None:
        """
        Build the fake UI object.

        :return: None.
        """
        self.defaultBusVoltageSpinBox: FakeSpinBox = FakeSpinBox()


class FakeServerDriver:
    """
    Deterministic server driver used by ``ServerFileDialogue``.
    """

    __slots__ = ("_files_payload",)

    def __init__(self) -> None:
        """
        Build a fake server tree.

        :return: None.
        """
        model_rows: List[Dict[str, Any]] = list()
        model_rows.append(
            {
                "idtag": "model-a",
                "name": "Model A",
                "parent_model_idtag": None,
                "is_base_model": True,
            }
        )
        self._files_payload: List[Dict[str, Any]] = list()
        self._files_payload.append(
            {
                "idtag": "file-a",
                "name": "File A",
                "user": "tester",
                "created_at": "2026-01-01T00:00:00Z",
                "models": model_rows,
            }
        )

    def list_database_files_tree(self) -> List[Dict[str, Any]]:
        """
        Return a detached file tree.

        :return: File payload rows.
        """
        return copy.deepcopy(self._files_payload)


class FakeIoApp:
    """
    Minimal main-window facade used by import/export and diagram dialogs.
    """

    __slots__ = (
        "circuit",
        "current_boundary_set",
        "file_name",
        "project_directory",
        "server_driver",
        "session",
        "ui",
    )

    def __init__(self, circuit: vge.MultiCircuit) -> None:
        """
        Build the fake application facade.

        :param circuit: Circuit exposed to dialogs.
        :return: None.
        """
        self.circuit: vge.MultiCircuit = circuit
        self.current_boundary_set: Set[object] = set()
        self.file_name: str = ""
        self.project_directory: str = tempfile.gettempdir()
        self.server_driver: FakeServerDriver = FakeServerDriver()
        self.session: SimulationSession = SimulationSession()
        self.ui: FakeMainUi = FakeMainUi()

    def get_selected_buses(self) -> Set[vge.Bus]:
        """
        Return an empty selected-bus set.

        :return: Selected buses.
        """
        return set()

    def get_current_diagram_substations(self) -> list[object]:
        """
        Return no active map substation graphics.

        :return: Empty graphics rows.
        """
        return list()

    def get_diagram_slider_index(self) -> None:
        """
        Return no active time index.

        :return: None.
        """
        return None

    def add_complete_bus_branch_diagram_now(self, name: str = "") -> None:
        """
        Accept diagram creation requests from smoke constructors.

        :param name: Diagram name.
        :return: None.
        """
        del name

    def add_diagram_widget_and_diagram(self, diagram_widget: object, diagram: object) -> None:
        """
        Accept diagram registration requests from smoke constructors.

        :param diagram_widget: Diagram widget.
        :param diagram: Diagram object.
        :return: None.
        """
        del diagram_widget
        del diagram

    def set_diagrams_list_view(self) -> None:
        """
        Accept diagram list refresh requests.

        :return: None.
        """

    def set_diagram_widget(self, widget: object) -> None:
        """
        Accept active diagram widget changes.

        :param widget: Diagram widget.
        :return: None.
        """
        del widget

    def save_file_as(self, *args: object, **kwargs: object) -> None:
        """
        Accept save-as requests without touching disk.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: None.
        """
        del args
        del kwargs

    def save_file_now(self, *args: object, **kwargs: object) -> None:
        """
        Accept save-now requests without touching disk.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: None.
        """
        del args
        del kwargs

    def export_all(self, *args: object, **kwargs: object) -> None:
        """
        Accept export requests without touching disk.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: None.
        """
        del args
        del kwargs


class FakeBranchGraphic:
    """
    Minimal map branch graphic with an ``api_object`` pointer.
    """

    __slots__ = ("api_object",)

    def __init__(self, api_object: object) -> None:
        """
        Store the branch API object.

        :param api_object: Branch object.
        :return: None.
        """
        self.api_object: object = api_object


class FakeSyncThread:
    """
    Minimal sync-thread facade used by ``SyncDialogueWindow``.
    """

    __slots__ = ("issues",)

    def __init__(self) -> None:
        """
        Build an empty issue list.

        :return: None.
        """
        self.issues: list[object] = list()

    def pause(self) -> None:
        """
        Accept pause requests.

        :return: None.
        """

    def resume(self) -> None:
        """
        Accept resume requests.

        :return: None.
        """

    def process_issues(self) -> None:
        """
        Accept issue-processing requests.

        :return: None.
        """


class FakeRmsResults:
    """
    Minimal result object consumed by ``RmsPlotDialog``.
    """

    __slots__ = (
        "devices",
        "devices_vars_info",
        "time_array",
        "uid2idx",
        "units",
        "values",
        "variable_array",
        "vars_glob_name2uid",
    )

    def __init__(self, device: object, variable: Var) -> None:
        """
        Build the result facade.

        :param device: Device owning the variable.
        :param variable: Dynamic variable.
        :return: None.
        """
        variables: List[Var] = list()
        variables.append(variable)
        self.devices: List[object] = list()
        self.devices.append(device)
        self.devices_vars_info: Dict[object, List[Var]] = dict()
        self.devices_vars_info[device] = variables
        self.time_array: np.ndarray = np.array([0.0, 1.0], dtype=float)
        self.uid2idx: Dict[int, int] = dict()
        self.uid2idx[1] = 0
        self.vars_glob_name2uid: Dict[str, int] = dict()
        self.vars_glob_name2uid["speedGenerator"] = 1
        self.variable_array: np.ndarray = np.array(["speedGenerator"], dtype=str)
        self.values: np.ndarray = np.zeros((2, 1), dtype=float)
        self.units: str = ""


class DialogSmokeContext:
    """
    Shared real objects used to construct smoke dialogs.
    """

    __slots__ = ("app", "circuit", "fake_app", "time_array")

    def __init__(self, app: QtWidgets.QApplication) -> None:
        """
        Build one smoke context.

        :param app: Shared Qt application.
        :return: None.
        """
        self.app: QtWidgets.QApplication = app
        self.circuit: vge.MultiCircuit = build_smoke_circuit()
        self.fake_app: FakeIoApp = FakeIoApp(circuit=self.circuit)
        self.time_array: pd.DatetimeIndex = pd.date_range("2026-01-01 00:00:00", periods=2, freq="h")


def build_smoke_circuit() -> vge.MultiCircuit:
    """
    Build the smallest circuit that satisfies editor constructors.

    :return: Smoke-test circuit.
    """
    circuit: vge.MultiCircuit = vge.MultiCircuit()
    bus_from: vge.Bus = vge.Bus(name="Bus 1", Vnom=110.0, is_slack=True, latitude=1.0, longitude=1.0)
    bus_to: vge.Bus = vge.Bus(name="Bus 2", Vnom=110.0, latitude=2.0, longitude=2.0)
    circuit.add_bus(obj=bus_from)
    circuit.add_bus(obj=bus_to)

    line: vge.Line = vge.Line(name="Line", bus_from=bus_from, bus_to=bus_to, r=0.01, x=0.05, rate=100.0)
    circuit.add_line(obj=line)
    dc_line: vge.DcLine = vge.DcLine(name="DC Line", bus_from=bus_from, bus_to=bus_to, r=0.01, rate=100.0)
    circuit.add_dc_line(dc_line)
    transformer_2w: vge.Transformer2W = vge.Transformer2W(
        name="Transformer 2W",
        bus_from=bus_from,
        bus_to=bus_to,
        rate=100.0,
    )
    circuit.add_transformer2w(transformer_2w)
    transformer_3w: vge.Transformer3W = vge.Transformer3W(
        name="Transformer 3W",
        bus1=bus_from,
        bus2=bus_to,
        bus3=bus_to,
        V1=110.0,
        V2=110.0,
        V3=110.0,
        rate12=100.0,
        rate23=100.0,
        rate31=100.0,
    )
    circuit.add_transformer3w(transformer_3w)

    load: vge.Load = vge.Load(name="Load", P=1.0, Q=0.2)
    circuit.add_load(bus=bus_to, api_obj=load)
    generator: vge.Generator = vge.Generator(name="Generator", P=1.0)
    circuit.add_generator(bus=bus_from, api_obj=generator)
    shunt: vge.ControllableShunt = vge.ControllableShunt(name="Controllable Shunt")
    circuit.add_controllable_shunt(bus=bus_to, api_obj=shunt)
    substation: vge.Substation = vge.Substation(name="Substation")
    circuit.add_substation(substation)

    return circuit


def build_object_filter_dialog() -> ObjectColumnFilterDialog:
    """
    Build an object-column filter dialog with a real proxy model.

    :return: Dialog instance.
    """
    table_view: QtWidgets.QTableView = QtWidgets.QTableView()
    bus: vge.Bus = vge.Bus(name="Alpha")
    objects: List[vge.Bus] = list()
    objects.append(bus)
    properties: List[GCProp] = list()
    properties.append(bus.registered_properties["name"])
    source_model: ObjectsModel = ObjectsModel(
        objects=objects,
        property_list=properties,
        time_index=None,
        parent=table_view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    table_view.setModel(proxy_model)
    dialog: ObjectColumnFilterDialog = ObjectColumnFilterDialog(
        proxy_model=proxy_model,
        source_column=0,
        table_view=table_view,
        parent=table_view,
    )
    return dialog


def build_rms_results(circuit: vge.MultiCircuit) -> FakeRmsResults:
    """
    Build minimal RMS results for the plot-variable dialog.

    :param circuit: Circuit supplying one visible device.
    :return: RMS results facade.
    """
    variable: Var = Var(name="speed", uid=1)
    results: FakeRmsResults = FakeRmsResults(device=circuit.generators[0], variable=variable)
    return results


def build_dialog_for_smoke(target: DialogSmokeTarget, context: DialogSmokeContext) -> QtWidgets.QWidget:
    """
    Build one dialog for smoke testing.

    :param target: Dialog target.
    :param context: Shared smoke context.
    :return: Dialog widget.
    """
    circuit: vge.MultiCircuit = context.circuit
    fake_app: FakeIoApp = context.fake_app

    if target == DialogSmokeTarget.ABOUT_DIALOGUE:
        dialog: QtWidgets.QWidget = AboutDialogueGuiGUI()
    elif target == DialogSmokeTarget.AI_CHAT_DIALOGUE:
        dialog = AiChatDialogue()
    elif target == DialogSmokeTarget.GRID_ANALYSIS:
        dialog = GridAnalysisGUI(circuit=circuit)
    elif target == DialogSmokeTarget.CATALOGUE_ELEMENTS:
        dialog = CatalogueElementsSelectionDialogue(parent=None, circuit=circuit)
    elif target == DialogSmokeTarget.CONTINGENCY_PLANNER:
        dialog = ContingencyPlannerGUI(grid=circuit)
    elif target == DialogSmokeTarget.CONTROLLABLE_SHUNT_EDITOR:
        dialog = ControllableShuntEditor(api_object=circuit.controllable_shunts[0])
    elif target == DialogSmokeTarget.DC_LINE_EDITOR:
        dialog = DcLineEditor(branch=circuit.dc_lines[0])
    elif target == DialogSmokeTarget.SOLAR_PV_WIZARD:
        dialog = SolarPvWizard(
            time_array=context.time_array,
            peak_power=1.0,
            latitude=28.0,
            longitude=-16.0,
        )
    elif target == DialogSmokeTarget.WIND_FARM_WIZARD:
        dialog = WindFarmWizard(
            time_array=context.time_array,
            peak_power=1.0,
            latitude=28.0,
            longitude=-16.0,
        )
    elif target == DialogSmokeTarget.GENERATOR_Q_CURVE_EDITOR:
        dialog = GeneratorQCurveEditor(
            q_curve=vge.GeneratorQCurve(),
            Qmin=-1.0,
            Qmax=1.0,
            Pmin=0.0,
            Pmax=1.0,
            Snom=1.0,
        )
    elif target == DialogSmokeTarget.LINE_EDITOR:
        dialog = LineEditor(line=circuit.lines[0], grid=circuit)
    elif target == DialogSmokeTarget.LOAD_DESIGNER:
        dialog = LoadDesigner(
            time_array=context.time_array,
            active_power=1.0,
            reactive_power=0.2,
            latitude=28.0,
            longitude=-16.0,
        )
    elif target == DialogSmokeTarget.TEMPLATE_DEVICE_EDITOR:
        dialog = TemplateDeviceEditor(api_object=circuit.lines[0], circuit=circuit)
    elif target == DialogSmokeTarget.TOWER_BUILDER:
        dialog = TowerBuilderGUI(tower=vge.OverheadLineType(name="Tower", Vnom=110.0), wires_catalogue=list())
    elif target == DialogSmokeTarget.TRANSFORMER_3W_EDITOR:
        dialog = Transformer3WEditor(tr3=circuit.transformers3w[0], Sbase=circuit.Sbase)
    elif target == DialogSmokeTarget.TRANSFORMER_EDITOR:
        dialog = TransformerEditor(branch=circuit.transformers2w[0], grid=circuit)
    elif target == DialogSmokeTarget.BUS_SELECTOR:
        dialog = BusSelectorDialogue(grid=circuit, se=circuit.substations[0])
    elif target == DialogSmokeTarget.NEW_MAP_LINE:
        dialog = NewMapLineDialogue(grid=circuit, se_from=circuit.substations[0], se_to=circuit.substations[0])
    elif target == DialogSmokeTarget.MAP_SELECTION:
        dialog = SelectionDialog(branch=FakeBranchGraphic(api_object=circuit.lines[0]), vnom=110.0)
    elif target == DialogSmokeTarget.DIAGRAM_BUS_SELECTOR:
        dialog = DiagramBusSelectorDialogue(gui=fake_app, grid=circuit, substation=circuit.substations[0])
    elif target == DialogSmokeTarget.DYNAMIC_EVENT_EDITOR:
        dialog = DynamicEventEditor(
            circuit=circuit,
            parameters_list=list(),
            target_device_name="Generator",
            mode=DynamicSimulationMode.RMS,
        )
    elif target == DialogSmokeTarget.SWITCH_SEQUENCE:
        dialog = SwitchSequenceDialog(mode_parameters=list(), events_groups=list())
    elif target == DialogSmokeTarget.DYNAMIC_EVENTS_GROUPS:
        dialog = DynamicEventsGroupsDialog(mode=DynamicSimulationMode.RMS)
    elif target == DialogSmokeTarget.JMARTI_LINE_EMT:
        dialog = JMartiLineEmtDialog()
    elif target == DialogSmokeTarget.LOOKUP_ARRAY_LINEAR:
        dialog = LookupArrayLinearDialog(block_label="Lookup")
    elif target == DialogSmokeTarget.LOOKUP_MATRIX_LINEAR:
        dialog = LookupMatrixLinearDialog(block_label="Lookup")
    elif target == DialogSmokeTarget.DYNAMIC_BLOCK_EDITOR:
        root_block: Block = Block(name="Root")
        dialog = DynamicBlockEditorGUI(
            var_factory=circuit.var_factory,
            api_object=circuit.loads[0],
            circuit=circuit,
            current_theme=DynEditorGraphicsModes.LIGHT,
            mode=DynamicSimulationMode.RMS,
            templates_list=list(),
            is_root_editor=True,
            modal=False,
            workspace_embedded=False,
            root_block=root_block,
            current_block=root_block,
        )
    elif target == DialogSmokeTarget.DYNAMIC_BLOCK_PROPERTIES:
        variable: Var = Var(name="x", uid=100)
        output_variables: List[Var] = list()
        output_variables.append(variable)
        block: Block = Block(name="Gain", out_vars=output_variables)
        dialog = DynamicBlockPropertiesDialog(
            block=block,
            block_type_name=BlockType.GAIN.name,
            var_factory=VarFactory(),
        )
    elif target == DialogSmokeTarget.DYNAMIC_EDITOR_PICKER:
        dialog = DynamicEditorPickerDialog(entries=list())
    elif target == DialogSmokeTarget.DYNAMIC_EDITOR_WORKSPACE:
        dialog = DynamicEditorWorkspaceWindow(session=DynamicEditorWorkspaceSession())
    elif target == DialogSmokeTarget.VALIDATION_SECTION:
        dialog = ValidationSectionDialog(section_results=list())
    elif target == DialogSmokeTarget.CGMES_EXPORT:
        dialog = CgmesExportDialogue(app=fake_app)
    elif target == DialogSmokeTarget.CGMES_IMPORT:
        dialog = CgmesImportDialogue(app=fake_app, options=FileOpenOptions())
    elif target == DialogSmokeTarget.COORDINATES_INPUT:
        dialog = CoordinatesInputGUI(grid=circuit)
    elif target == DialogSmokeTarget.CATALOGUE:
        dialog = CatalogueGUI()
    elif target == DialogSmokeTarget.DGS_EXPORT:
        dialog = DgsExportDialogue(app=fake_app)
    elif target == DialogSmokeTarget.DGS_IMPORT:
        dialog = DgsImportDialogue(options=FileOpenOptions())
    elif target == DialogSmokeTarget.MATPOWER_EXPORT:
        dialog = MatpowerExportDialogue(app=fake_app)
    elif target == DialogSmokeTarget.EXCEL_DIALOG:
        dialog = ExcelDialog()
    elif target == DialogSmokeTarget.MODELS_INPUT:
        dialog = ModelsInputGUI(main_grid=circuit)
    elif target == DialogSmokeTarget.GENERATORS_PROFILE_OPTIONS:
        dialog = GeneratorsProfileOptionsDialogue()
    elif target == DialogSmokeTarget.PROFILE_INPUT:
        dialog = ProfileInputGUI(
            parent=None,
            circuit=circuit,
            dev_type=DeviceType.LoadDevice,
            objects=circuit.loads,
            magnitude="P",
        )
    elif target == DialogSmokeTarget.PSSE_EXPORT:
        dialog = PsseExportDialogue(app=fake_app)
    elif target == DialogSmokeTarget.PSSE_IMPORT:
        dialog = PsseImportDialogue(app=fake_app, options=FileOpenOptions())
    elif target == DialogSmokeTarget.ROSETA_EXPLORER:
        dialog = RosetaExplorerGUI()
    elif target == DialogSmokeTarget.SERVER_FILE:
        dialog = ServerFileDialogue(parent=None, app=fake_app)
    elif target == DialogSmokeTarget.UCTE_EXPORT:
        dialog = UcteExportDialogue(app=fake_app)
    elif target == DialogSmokeTarget.FMU_TEMPLATE_EDITOR:
        dialog = FmuTemplateEditorDialog(
            circuit=circuit,
            template=FmuTemplate(name="FMU"),
            project_directory=tempfile.gettempdir(),
        )
    elif target == DialogSmokeTarget.GRID_GENERATOR:
        dialog = GridGeneratorGUI()
    elif target == DialogSmokeTarget.GRID_DIFF:
        dialog = GridDiffDialogue(grid=circuit)
    elif target == DialogSmokeTarget.GRID_MERGE:
        dialog = GridMergeDialogue(grid=circuit, diff=circuit)
    elif target == DialogSmokeTarget.GRID_REDUCE:
        selected_buses: Set[vge.Bus] = set()
        selected_buses.add(circuit.buses[0])
        dialog = GridReduceDialogue(grid=circuit, session=SimulationSession(), selected_buses_set=selected_buses)
    elif target == DialogSmokeTarget.OBJECT_SELECT:
        named_objects: List[NamedObject] = list()
        named_objects.append(NamedObject(name="Alpha"))
        named_objects.append(NamedObject(name="Beta"))
        dialog = ObjectSelectWindow(title="Select object", object_list=named_objects)
    elif target == DialogSmokeTarget.LIST_SELECT:
        elements: List[str] = list()
        elements.append("Alpha")
        elements.append("Beta")
        dialog = ListSelectWindow(title="Select value", elements=elements)
    elif target == DialogSmokeTarget.PROCEDURAL_GRID:
        dialog = ProceduralGridWindow(app=fake_app)
    elif target == DialogSmokeTarget.MAP_WARNING:
        dialog = MapWarningDialog()
    elif target == DialogSmokeTarget.VOLTAGE_WARNING:
        offenders: List[tuple[str, float]] = list()
        offenders.append(("Bus", 33.0))
        dialog = VoltageWarningDialog(offenders=offenders, valid_voltages=[10.0, 20.0])
    elif target == DialogSmokeTarget.RMS_PLOT:
        dialog = RmsPlotDialog(results=build_rms_results(circuit=circuit))
    elif target == DialogSmokeTarget.SHORT_CIRCUIT_SELECTOR:
        dialog = ShortCircuitSelector()
    elif target == DialogSmokeTarget.SIGMA_ANALYSIS:
        dialog = SigmaAnalysisGUI(grid=circuit)
    elif target == DialogSmokeTarget.SUBSTATION_DESIGNER:
        dialog = SubstationDesigner(grid=circuit)
    elif target == DialogSmokeTarget.VOLTAGE_LEVEL_CONVERSION:
        dialog = VoltageLevelConversionWizard(bus=circuit.buses[0], grid=circuit)
    elif target == DialogSmokeTarget.SYNC_DIALOGUE:
        dialog = SyncDialogueWindow(file_sync_thread=FakeSyncThread())
    elif target == DialogSmokeTarget.SYSTEM_SCALER:
        dialog = SystemScaler(grid=circuit)
    elif target == DialogSmokeTarget.NEW_PROFILES_STRUCTURE:
        dialog = NewProfilesStructureDialogue()
    elif target == DialogSmokeTarget.LOGS:
        dialog = LogsDialogue(name="Log", logger=Logger())
    elif target == DialogSmokeTarget.DEVICE_SELECTOR:
        dialog = DeviceSelectorDialogue(devices_by_type={DeviceType.BusDevice: circuit.buses})
    elif target == DialogSmokeTarget.NEW_CONNECTED_DEVICE:
        dialog = NewConnectedDeviceDialogue(name="New", bus_count=2, buses=circuit.buses)
    elif target == DialogSmokeTarget.ELEMENTS:
        dialog = ElementsDialogue(name="Elements", elements=circuit.buses)
    elif target == DialogSmokeTarget.TIME_RE_INDEX:
        dialog = TimeReIndexDialogue()
    elif target == DialogSmokeTarget.CORRECT_INCONSISTENCIES:
        dialog = CorrectInconsistenciesDialogue()
    elif target == DialogSmokeTarget.CHECK_LIST:
        dialog = CheckListDialogue(objects_list=["Alpha", "Beta"])
    elif target == DialogSmokeTarget.DELETE:
        dialog = DeleteDialogue(names_list=["Alpha", "Beta"])
    elif target == DialogSmokeTarget.INPUT_NUMBER:
        dialog = InputNumberDialogue(min_value=0.0, max_value=10.0, default_value=1.0)
    elif target == DialogSmokeTarget.INPUT_SEARCH:
        dialog = InputSearchDialogue(deafault_value="Alpha")
    elif target == DialogSmokeTarget.START_END_SELECTION:
        dialog = StartEndSelectionDialogue(min_value=0, max_value=1, time_array=context.time_array)
    elif target == DialogSmokeTarget.CUSTOM_QUESTION:
        dialog = CustomQuestionDialogue(title="Question", question="Continue?", answer1="Yes", answer2="No")
    elif target == DialogSmokeTarget.ARRAY_EDITOR:
        dialog = ArrayEditor()
    elif target == DialogSmokeTarget.FILE_TYPE_SELECTOR:
        dialog = FileTypeSelector(file_name="grid.veragrid")
    elif target == DialogSmokeTarget.CGMES_OPTIONS_SELECTOR:
        dialog = CgmesOptionsSelector()
    elif target == DialogSmokeTarget.SEQUENCE_EDITOR:
        dialog = SequenceEditorDialog(parent=None, sequence_type=WaveformSequenceType)
    elif target == DialogSmokeTarget.LOOKUP_MATRIX_EDITOR:
        dialog = LookupMatrixEditorDialog()
    elif target == DialogSmokeTarget.OBJECT_COLUMN_FILTER:
        dialog = build_object_filter_dialog()
    else:
        raise AssertionError(f"Unhandled smoke target {target}")

    return dialog


def close_dialog_for_smoke(dialog: QtWidgets.QWidget,
                           app: QtWidgets.QApplication,
                           close_extra_widgets: bool = True) -> None:
    """
    Close one smoke dialog using its real lifecycle.

    :param dialog: Dialog or window to close.
    :param app: Shared Qt application.
    :param close_extra_widgets: Close helper top-level widgets created by the dialog.
    :return: None.
    """
    if is_dialog_available(dialog=dialog):
        if isinstance(dialog, AiChatDialogue):
            dialog.prepare_for_shutdown()
            dialog.shutdown_turn_thread()
            dialog.close()
        elif isinstance(dialog, QtWidgets.QDialog):
            dialog.reject()
        else:
            dialog.close()

        delete_dialog_safely(dialog=dialog)
    else:
        pass

    if close_extra_widgets:
        close_extra_top_level_widgets(app=app, primary_dialog=dialog)
        collect_qt_deletes(app=app)
    else:
        app.processEvents()


def close_extra_top_level_widgets(app: QtWidgets.QApplication, primary_dialog: QtWidgets.QWidget | None) -> None:
    """
    Close top-level helper widgets created by smoke-dialog constructors.

    :param app: Shared Qt application.
    :param primary_dialog: Dialog already closed by the caller.
    :return: None.
    """
    widgets: List[QtWidgets.QWidget] = list(app.topLevelWidgets())
    widget: QtWidgets.QWidget
    for widget in widgets:
        if widget is primary_dialog:
            pass
        elif is_dialog_available(dialog=widget):
            if isinstance(widget, AiChatDialogue):
                widget.prepare_for_shutdown()
                widget.shutdown_turn_thread()
                widget.close()
            elif isinstance(widget, QtWidgets.QDialog):
                widget.reject()
            else:
                widget.close()
            delete_dialog_safely(dialog=widget)
        else:
            pass


def collect_qt_deletes(app: QtWidgets.QApplication) -> None:
    """
    Flush Qt deferred deletes and Python cycles left by smoke constructors.

    :param app: Shared Qt application.
    :return: None.
    """
    app.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()


def run_dialog_smoke_suite_in_child(message_queue: Any) -> None:
    """
    Run the full dialog smoke inventory in a disposable child process.

    :param message_queue: Parent-visible queue receiving failure details.
    :return: None.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(list(("dialog-smoke",)))
    else:
        pass

    target: DialogSmokeTarget
    for target in DialogSmokeTarget:
        context: DialogSmokeContext = DialogSmokeContext(app=app)
        dialog: QtWidgets.QWidget = build_dialog_for_smoke(target=target, context=context)

        try:
            dialog.show()
            app.processEvents()
            assert shiboken6.isValid(dialog)
        except Exception:
            message_queue.put(f"{target.value}\n{traceback.format_exc()}")
            raise
        finally:
            close_dialog_for_smoke(dialog=dialog, app=app)

        active_modal_widget: QtWidgets.QWidget | None = app.activeModalWidget()
        if active_modal_widget is None:
            pass
        else:
            message_queue.put(f"{target.value}\nleft active modal widget: {active_modal_widget}")
            raise AssertionError(f"{target.value} left active modal widget")


def run_dialog_smoke_suite_subprocess(timeout_s: float) -> None:
    """
    Run dialog smoke coverage outside the parent pytest Qt process.

    :param timeout_s: Maximum child-process runtime in seconds.
    :return: None.
    """
    process_context: multiprocessing.context.BaseContext = multiprocessing.get_context("spawn")
    message_queue: Any = process_context.Queue()
    process: multiprocessing.Process = process_context.Process(
        target=run_dialog_smoke_suite_in_child,
        args=(message_queue,),
    )

    process.start()
    process.join(timeout_s)

    if process.is_alive():
        process.terminate()
        process.join(10.0)
        raise AssertionError(f"Dialog smoke subprocess timed out after {timeout_s} seconds")
    else:
        pass

    message: str = ""
    try:
        queued_message: object = message_queue.get_nowait()
        if isinstance(queued_message, str):
            message = queued_message
        else:
            message = repr(queued_message)
    except queue.Empty:
        pass

    assert process.exitcode == 0, message


def get_smoked_dialog_class_names() -> Set[str]:
    """
    Return class names covered by the smoke test.

    :return: Covered class names.
    """
    names: Set[str] = set()
    target: DialogSmokeTarget
    for target in DialogSmokeTarget:
        names.add(target.value)
    return names


def get_deferred_dialog_class_names() -> Set[str]:
    """
    Return dialog classes that need dedicated runtime-result fixtures.

    :return: Deferred class names.
    """
    names: Set[str] = set()
    names.add("BaseMainGui")
    names.add("CenteredDialog")
    return names


def discover_qt_dialog_class_names() -> Set[str]:
    """
    Discover dialog/window classes declared under ``VeraGrid.Gui``.

    :return: Class names backed by QDialog/QMainWindow/CenteredDialog.
    """
    tests_root: Path = Path(__file__).resolve().parents[1]
    gui_root: Path = tests_root.parent / "VeraGrid" / "Gui"
    class_names: Set[str] = set()
    path: Path
    for path in gui_root.rglob("*.py"):
        tree: ast.Module = ast.parse(path.read_text(encoding="utf-8"))
        node: ast.stmt
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases: List[str] = list()
                base: ast.expr
                for base in node.bases:
                    bases.append(ast.unparse(base))
                if ("QDialog" in bases) or ("QMainWindow" in bases) or ("QtWidgets.QDialog" in bases):
                    class_names.add(node.name)
                elif ("CenteredDialog" in bases) or ("QtWidgets.QMainWindow" in bases):
                    class_names.add(node.name)
                else:
                    pass
            else:
                pass
    return class_names


def test_dialog_opens_and_closes_without_blowing_up() -> None:
    """
    Smoke open and close each stable GUI dialog in an isolated process.

    :return: None.
    """
    run_dialog_smoke_suite_subprocess(timeout_s=120.0)


def test_dialog_smoke_inventory_is_explicit() -> None:
    """
    Keep the smoke target list aligned with real dialog/window classes.

    :return: None.
    """
    known_names: Set[str] = get_smoked_dialog_class_names()
    known_names.update(get_deferred_dialog_class_names())
    missing_names: Set[str] = discover_qt_dialog_class_names() - known_names

    assert sorted(missing_names) == list()


def test_modeless_export_dialogues_reuse_live_windows(qt_app: QtWidgets.QApplication) -> None:
    """
    Check that repeated export actions do not orphan live modeless dialogs.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    app: QtWidgets.QApplication = qt_app
    gui: VeraGridMainGUI = VeraGridMainGUI()

    try:
        gui.export_psse()
        app.processEvents()
        psse_dialog: PsseExportDialogue | None = gui.psse_export_dialogue
        assert is_dialog_available(dialog=psse_dialog)
        gui.export_psse()
        app.processEvents()
        assert gui.psse_export_dialogue is psse_dialog

        gui.export_power_factory()
        app.processEvents()
        dgs_dialog: DgsExportDialogue | None = gui.dgs_export_dialogue
        assert is_dialog_available(dialog=dgs_dialog)
        gui.export_power_factory()
        app.processEvents()
        assert gui.dgs_export_dialogue is dgs_dialog

        gui.export_matpower()
        app.processEvents()
        matpower_dialog: MatpowerExportDialogue | None = gui.matpower_export_dialogue
        assert is_dialog_available(dialog=matpower_dialog)
        gui.export_matpower()
        app.processEvents()
        assert gui.matpower_export_dialogue is matpower_dialog

        gui.export_ucte()
        app.processEvents()
        ucte_dialog: UcteExportDialogue | None = gui.ucte_export_dialogue
        assert is_dialog_available(dialog=ucte_dialog)
        gui.export_ucte()
        app.processEvents()
        assert gui.ucte_export_dialogue is ucte_dialog

        gui.export_cgmes()
        app.processEvents()
        cgmes_dialog: CgmesExportDialogue | None = gui.cgmes_dialogue
        assert is_dialog_available(dialog=cgmes_dialog)
        gui.export_cgmes()
        app.processEvents()
        assert gui.cgmes_dialogue is cgmes_dialog
    finally:
        if is_dialog_available(dialog=gui.psse_export_dialogue):
            close_dialog_for_smoke(dialog=gui.psse_export_dialogue, app=app, close_extra_widgets=False)
        else:
            pass
        if is_dialog_available(dialog=gui.dgs_export_dialogue):
            close_dialog_for_smoke(dialog=gui.dgs_export_dialogue, app=app, close_extra_widgets=False)
        else:
            pass
        if is_dialog_available(dialog=gui.matpower_export_dialogue):
            close_dialog_for_smoke(dialog=gui.matpower_export_dialogue, app=app, close_extra_widgets=False)
        else:
            pass
        if is_dialog_available(dialog=gui.ucte_export_dialogue):
            close_dialog_for_smoke(dialog=gui.ucte_export_dialogue, app=app, close_extra_widgets=False)
        else:
            pass
        if is_dialog_available(dialog=gui.cgmes_dialogue):
            close_dialog_for_smoke(dialog=gui.cgmes_dialogue, app=app, close_extra_widgets=False)
        else:
            pass
        if is_dialog_available(dialog=gui):
            gui.hide()
            gui.stop_all_threads()
            delete_dialog_safely(dialog=gui)
        else:
            pass
        close_extra_top_level_widgets(app=app, primary_dialog=gui)
        collect_qt_deletes(app=app)
