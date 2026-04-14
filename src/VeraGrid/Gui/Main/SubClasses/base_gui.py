# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import ctypes
import gc
import json
import os.path
import sys
import threading
import webbrowser
from typing import List, Union

import numpy as np
import pandas as pd

# GUI imports
from PySide6 import QtGui, QtWidgets, QtCore

from VeraGrid.Gui.scenario_tree_model import ScenarioTreeModel
# Engine imports
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse
import VeraGridEngine.Simulations as sim
from VeraGridEngine.enumerations import EngineType, DeviceType, SimulationTypes
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit

from VeraGridEngine.Compilers.circuit_to_bentayga import BENTAYGA_AVAILABLE
from VeraGridEngine.Compilers.circuit_to_newton_pa import NEWTON_PA_AVAILABLE
from VeraGridEngine.Compilers.circuit_to_gslv import GSLV_AVAILABLE
from VeraGridEngine.Compilers.circuit_to_pgm import PGM_AVAILABLE
from VeraGridEngine.Simulations.Clustering.clustering_results import ClusteringResults

import VeraGrid.Gui.gui_functions as gf
import VeraGrid.Session.synchronization_driver as syncdrv
from VeraGrid.Gui.AboutDialogue.about_dialogue import AboutDialogueGuiGUI

from VeraGrid.Gui.Analysis.AnalysisDialogue import GridAnalysisGUI
from VeraGrid.Gui.ContingencyPlanner.contingency_planner_dialogue import ContingencyPlannerGUI
from VeraGrid.Gui.CoordinatesInput.coordinates_dialogue import CoordinatesInputGUI
from VeraGrid.Gui.general_dialogues import CheckListDialogue, StartEndSelectionDialogue, FileTypeSelector, \
    CgmesOptionsSelector
from VeraGrid.Gui.messages import yes_no_question, warning_msg, info_msg, error_msg
from VeraGrid.Gui.GridGenerator.grid_generator_dialogue import GridGeneratorGUI
from VeraGrid.Gui.LoadCatalogue.catalogue_dialogue import CatalogueGUI
from VeraGrid.Gui.Main.MainWindow import Ui_mainWindow, QMainWindow
from VeraGrid.Gui.Main.object_select_window import ObjectSelectWindow
from VeraGrid.Gui.ProfilesInput.models_dialogue import ModelsInputGUI
from VeraGrid.Gui.ProfilesInput.profile_dialogue import ProfileInputGUI
from VeraGrid.Session.session import SimulationSession, GcThread
from VeraGrid.Gui.SigmaAnalysis.sigma_analysis_dialogue import SigmaAnalysisGUI
from VeraGrid.Gui.SyncDialogue.sync_dialogue import SyncDialogueWindow
from VeraGrid.Gui.TowerBuilder.LineBuilderDialogue import TowerBuilderGUI
from VeraGrid.Gui.GridReduce.grid_reduce import GridReduceDialogue
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Gui.Diagrams.SchematicWidget.diagram_bus_selection_dialogue import DiagramBusSelectorDialogue
from VeraGrid.Gui.Diagrams.generic_graphics import IS_DARK
from VeraGrid.Gui.python_console import PythonConsole
from VeraGrid.Gui.python_script_editor import PythonCodeEditor
from VeraGrid.Gui.toast_widget import ToastManager
from VeraGrid.Gui.PsseDialogue.psse_import import PsseImportDialogue
from VeraGrid.Gui.ProceduralGrid.procedural_grid import ProceduralGridWindow
from VeraGrid.Gui.AiAgent.ai_chat_dialogue import AiChatDialogue, AiBackendState
from VeraGrid.Gui.AiAgent.ai_backend import ProviderType
from VeraGridEngine.IO.file_system import get_create_veragrid_folder


def terminate_thread(thread):
    """
    Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if not thread.is_alive():
        return False

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        print("nonexistent thread id")
        return True

    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

    return True


def traverse_objects(name, obj, lst: list, i=0):
    """

    :param name:
    :param obj:
    :param lst:
    :param i:
    """
    lst.append((name, sys.getsizeof(obj)))
    if i < 10:
        if hasattr(obj, '__dict__'):
            for name2, obj2 in obj.__dict__.items():
                if isinstance(obj2, np.ndarray):
                    lst.append((name + "/" + name2, sys.getsizeof(obj2)))
                else:
                    if isinstance(obj2, list):
                        # list or
                        for k, obj3 in enumerate(obj2):
                            traverse_objects(name=name + "/" + name2 + '[' + str(k) + ']',
                                             obj=obj3, lst=lst, i=i + 1)
                    elif isinstance(obj2, dict):
                        # list or
                        for name3, obj3 in obj2.items():
                            traverse_objects(name=name + "/" + name2 + '[' + name3 + ']',
                                             obj=obj3, lst=lst, i=i + 1)
                    else:
                        # normal obj
                        if obj2 != obj:
                            traverse_objects(name=name + "/" + name2, obj=obj2, lst=lst, i=i + 1)


class BaseMainGui(QMainWindow):
    """
    DiagramFunctionsMain
    """

    def __init__(self, parent=None):
        """

        @param parent:
        """
        # create the main window
        QMainWindow.__init__(self, parent)
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        # Declare circuit
        # self.circuit: MultiCircuit = MultiCircuit()
        self._multiverse: MultiVerse = MultiVerse(current_model=MultiCircuit())
        self.scenario_tree_model: ScenarioTreeModel = ScenarioTreeModel(multiverse=self._multiverse)

        self.lock_ui = False
        self.ui.progress_frame.setVisible(self.lock_ui)

        self.stuff_running_now: List[SimulationTypes] = list()

        self.session: SimulationSession = SimulationSession(name='GUI session')

        self._file_name = ''

        self.project_directory = os.path.expanduser("~")

        self.current_boundary_set: str = ""

        # toast manager
        self.toast_manager = ToastManager(parent=self, position_top=False)

        # threads ------------------------------------------------------------------------------------------------------
        self.painter = None
        self.open_file_thread_object = None
        self.save_file_thread_object = None
        self.last_file_driver = None
        self.delete_and_reduce_driver = None
        self.export_all_thread_object = None
        self.topology_reduction = None
        self.find_node_groups_driver: Union[sim.NodeGroupsDriver, None] = None
        self.file_sync_thread = syncdrv.FileSyncThread(self.circuit, None, None)

        self.task_pool = QtCore.QThreadPool()

        # simulation start end
        self.simulation_start_index: int = -1
        self.simulation_end_index: int = -1
        # Menu buttons -------------------------------------------------------------------------------------------------

        self.pf_menu_button = gf.create_menu_button(
            parent=self,
            toolbar=self.ui.toolBar,
            actions=[self.ui.actionPower_flow,
                     self.ui.actionPower_flow_3ph,
                     self.ui.actionLinearAnalysis,
                     self.ui.actionSigma_analysis],
            position=self.ui.actionPower_flow,
            remove_actions=True
        )

        self.rms_menu_button = gf.create_menu_button(
            parent=self,
            toolbar=self.ui.toolBar,
            actions=[self.ui.actionRun_Dynamic_RMS_Simulation,
                     self.ui.actionRun_Dynamic_EMT_Simulation,
                     self.ui.actionRun_Small_Signal_RMS_Simulation,
                     self.ui.actionRun_Small_Signal_EMT_Simulation],
            position=self.ui.actionRun_Dynamic_RMS_Simulation,
            remove_actions=True
        )

        self.opf_menu_button = gf.create_menu_button(
            parent=self,
            toolbar=self.ui.toolBar,
            actions=[self.ui.actionOPF,
                     self.ui.actionNodal_capacity,
                     self.ui.actionOptimal_Net_Transfer_Capacity,
                     self.ui.actionATC],
            position=self.ui.actionNodal_capacity,
            remove_actions=True
        )

        self.stochastic_menu_button = gf.create_menu_button(
            parent=self,
            toolbar=self.ui.toolBar,
            actions=[self.ui.actionPower_flow_Stochastic,
                     self.ui.actionBlackout_cascade,
                     self.ui.actionReliability,
                     self.ui.actionFind_node_groups],
            position=self.ui.actionPower_flow_Stochastic,
            remove_actions=True
        )

        # Add console --------------------------------------------------------------------------------------------------
        self.console = PythonConsole(banner="VeraGrid Python Console!")
        self.ui.consoleLayout.addWidget(self.console)

        self.code_editor = PythonCodeEditor(vars_dict={

            # "app": self,
            # "np": np,
            # "pd": pd,
            # "plt": plt,
        }, )
        self.ui.codeEditorLayout.addWidget(self.code_editor)

        # window pointers ----------------------------------------------------------------------------------------------
        self.file_sync_window: Union[SyncDialogueWindow, None] = None
        self.sigma_dialogue: Union[SigmaAnalysisGUI, None] = None
        self.grid_generator_dialogue: Union[GridGeneratorGUI, None] = None
        self.catalogue_dialogue: Union[CatalogueGUI, None] = None
        self.contingency_planner_dialogue: Union[ContingencyPlannerGUI, None] = None
        self.analysis_dialogue: Union[GridAnalysisGUI, None] = None
        self.profile_input_dialogue: Union[ProfileInputGUI, None] = None
        self.models_input_dialogue: Union[ModelsInputGUI, None] = None
        self.object_select_window: Union[ObjectSelectWindow, None] = None
        self.coordinates_window: Union[CoordinatesInputGUI, None] = None
        self.about_msg_window: Union[AboutDialogueGuiGUI, None] = None
        self.tower_builder_window: Union[TowerBuilderGUI, None] = None
        self.rms_model_Editor_window: Union[DynamicBlockEditorGUI, None] = None
        self.investment_checks_diag: Union[CheckListDialogue, None] = None
        self.new_se_dlg: Union[CheckListDialogue, None] = None
        self.contingency_checks_diag: Union[CheckListDialogue, None] = None
        self.ra_checks_diag: Union[CheckListDialogue, None] = None
        self.start_end_dialogue_window: Union[StartEndSelectionDialogue, None] = None
        self.grid_reduction_dialogue: GridReduceDialogue | None = None
        self.select_bus_dlg: DiagramBusSelectorDialogue | None = None
        self.file_selector: FileTypeSelector | None = None
        self.cgmes_selector: CgmesOptionsSelector | None = None
        self.psse_import_dialogue: PsseImportDialogue | None = None
        self.procedural_grid_window: ProceduralGridWindow | None = None
        self.ai_chat_dialogue: AiChatDialogue | None = None
        self.ai_backend_state: AiBackendState = self.build_default_ai_backend_state()
        self.ai_restore_visible: bool = False

        # available engines --------------------------------------------------------------------------------------------
        engine_lst = [EngineType.VeraGrid]
        if GSLV_AVAILABLE:
            engine_lst.append(EngineType.GSLV)
        if NEWTON_PA_AVAILABLE:
            engine_lst.append(EngineType.NewtonPA)
        if BENTAYGA_AVAILABLE:
            engine_lst.append(EngineType.Bentayga)
        if PGM_AVAILABLE:
            engine_lst.append(EngineType.PGM)

        self.ui.engineComboBox.setModel(gf.get_list_model([x.value for x in engine_lst]))
        self.ui.engineComboBox.setCurrentIndex(0)
        self.engine_dict = {x.value: x for x in engine_lst}

        # available engines --------------------------------------------------------------------------------------------
        exchange_places = [DeviceType.AreaDevice, DeviceType.CountryDevice]
        exchange_places_mdl = gf.get_list_model([x.value for x in exchange_places])
        self.ui.fromComboBox.setModel(exchange_places_mdl)
        self.ui.fromComboBox.setCurrentIndex(0)
        self.ui.toComboBox.setModel(exchange_places_mdl)
        self.ui.toComboBox.setCurrentIndex(0)
        self.exchange_places_dict = {x.value: x for x in exchange_places}

        # dark mode detection ------------------------------------------------------------------------------------------
        self.ui.dark_mode_checkBox.setChecked(IS_DARK)

        self.calculation_inputs_to_display = None

        # --------------------------------------------------------------------------------------------------------------
        self.ui.actionClear_stuff_running_right_now.triggered.connect(self.clear_stuff_running)
        self.ui.actionAbout.triggered.connect(self.about_box)
        self.ui.actionAuto_rate_branches.triggered.connect(self.auto_rate_branches)
        self.ui.actionDetect_transformers.triggered.connect(self.detect_transformers)
        self.ui.actionLaunch_data_analysis_tool.triggered.connect(self.display_grid_analysis)
        self.ui.actionOnline_documentation.triggered.connect(self.show_online_docs)
        self.ui.actionReport_a_bug.triggered.connect(self.report_a_bug)

        self.ui.actionFix_generators_active_based_on_the_power.triggered.connect(
            self.fix_generators_active_based_on_the_power
        )
        self.ui.actionFix_loads_active_based_on_the_power.triggered.connect(self.fix_loads_active_based_on_the_power)
        self.ui.actionInitialize_contingencies.triggered.connect(self.initialize_contingencies)
        self.ui.actionai_chat.triggered.connect(self.open_ai_chat_dialogue)

        # Buttons
        self.ui.cancelButton.clicked.connect(self.set_cancel_state)

        # doubleSpinBox
        self.ui.fbase_doubleSpinBox.valueChanged.connect(self.change_circuit_base)
        self.ui.sbase_doubleSpinBox.valueChanged.connect(self.change_circuit_base)

        self.ui.grid_name_line_edit.textChanged.connect(self.change_circuit_name)
        self.ui.grid_name_line_edit.textChanged.connect(self.refresh_ai_context_if_available)

        # combo-boxes
        self.ui.fromComboBox.currentTextChanged.connect(self.update_from_to_list_views)
        self.ui.toComboBox.currentTextChanged.connect(self.update_from_to_list_views)
        self.ui.engineComboBox.currentTextChanged.connect(self.refresh_ai_context_if_available)
        self.ui.available_results_to_color_comboBox.currentTextChanged.connect(self.refresh_ai_context_if_available)

    def LOCK(self, val: bool = True) -> None:
        """
        Lock the interface to prevent new simulation launches
        :param val:
        :return:
        """
        self.lock_ui = val
        self.ui.progress_frame.setVisible(self.lock_ui)
        QtGui.QGuiApplication.processEvents()

    def UNLOCK(self) -> None:
        """
        Unlock the interface
        """
        if not self.any_thread_running():
            self.LOCK(False)

    @property
    def multiverse(self) -> MultiVerse:
        return self._multiverse

    @multiverse.setter
    def multiverse(self, val: MultiVerse):
        self._multiverse = val
        self.scenario_tree_model = ScenarioTreeModel(multiverse=val)
        self.ui.multiverseTreeView.setModel(self.scenario_tree_model)
        selection_model = self.ui.multiverseTreeView.selectionModel()

        # A loaded multiverse should present the whole scenario tree immediately.
        self.ui.multiverseTreeView.expandAll()

        # Restore the saved active scenario visually so the tree selection matches the
        # multiverse current_node/current_model pair as soon as the model is assigned.
        current_index = self.scenario_tree_model.index_for_node(val.current_node)
        if current_index.isValid():
            self.ui.multiverseTreeView.setCurrentIndex(current_index)
            if selection_model is not None:
                selection_model.select(
                    current_index,
                    QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QtCore.QItemSelectionModel.SelectionFlag.Rows,
                )
            self.ui.multiverseTreeView.scrollTo(current_index)

    @property
    def circuit(self) -> MultiCircuit:
        return self.multiverse.current_model

    @circuit.setter
    def circuit(self, val: MultiCircuit):
        self.multiverse.current_model = val
        self.multiverse.base_model = val

    @property
    def file_name(self) -> str:
        """
        Get the current file name
        :return: str
        """
        return self._file_name

    @file_name.setter
    def file_name(self, val: str):
        """
        Set the current file name
        :param val: file name
        """
        self._file_name = val
        if not isinstance(self._file_name, list):
            self.ui.file_information_label.setText(self._file_name)
        else:
            self.ui.file_information_label.setText("")

    @staticmethod
    def collect_memory() -> None:
        """
        Collect memory
        """
        for i in (0, 1, 2):
            gc.collect(generation=i)

    def get_simulation_threads(self) -> List[GcThread]:
        """
        Get all threads that has to do with simulation
        :return: list of simulation threads
        """

        all_threads = list(self.session.threads.values())

        return all_threads

    def get_process_threads(self) -> List[GcThread]:
        """
        Get all threads that has to do with processing
        :return: list of process threads
        """
        all_threads = [self.open_file_thread_object,
                       self.save_file_thread_object,
                       self.painter,
                       self.delete_and_reduce_driver,
                       self.export_all_thread_object,
                       self.find_node_groups_driver,
                       self.file_sync_thread,
                       ]
        return all_threads

    def get_all_threads(self) -> List[GcThread]:
        """
        Get all threads
        :return: list of all threads
        """
        all_threads = self.get_simulation_threads() + self.get_process_threads()
        return all_threads

    def stop_all_threads(self):
        """
        Stop all running threads
        """
        for thr in self.get_all_threads():
            if thr is not None:
                thr.quit()

        for thread in threading.enumerate():
            print(thread.name, end="")
            if "MainThread" not in thread.name:
                stat = terminate_thread(thread)
                if stat:
                    print(" killed")
                else:
                    print(" not killed")
            else:
                print(" Skipped")

        # second pass, kill main too
        for thread in threading.enumerate():
            print(thread.name, end="")
            stat = terminate_thread(thread)
            if stat:
                print(" killed")
            else:
                print(" not killed")

    def any_thread_running(self) -> bool:
        """
        Checks if any thread is running
        :return: True/False
        """
        val = False

        # this list cannot be created only once, because the None will be copied
        # instead of being a pointer to the future value like it would in a typed language
        all_threads = self.get_all_threads()

        for thr in all_threads:
            if thr is not None:
                if thr.isRunning():
                    return True
        return val

    def clear_stuff_running(self) -> None:
        """
        This clears the list of stuff running right now
        this list blocks new executions of the same threads.
        Cleaning is useful if a particular thread crashes and you want to retry.
        """
        self.stuff_running_now.clear()

    def get_all_objects_in_memory(self):
        """
        Get a list of the objects in memory
        :return:
        """
        objects = []
        # for name, obj in globals().items():
        #     objects.append([name, sys.getsizeof(obj)])

        traverse_objects('MainGUI', self, objects)

        df = pd.DataFrame(data=objects, columns=['Name', 'Size (kb)'])
        df.sort_values(by='Size (kb)', inplace=True, ascending=False)
        return df

    def expand_object_tree_nodes(self) -> None:
        """
        Expand objects' tree nodes
        """
        proxy = self.ui.dataStructuresTreeView.model()

        for row in range(proxy.rowCount()):
            index = proxy.index(row, 0)
            self.ui.dataStructuresTreeView.expand(index)

    def get_simulation_start(self) -> int:
        """
        Get the start simulation index
        """
        return self.simulation_start_index

    def get_simulation_end(self) -> int:
        """
        Get the end simulation index
        """
        return self.simulation_end_index

    def setup_sim_indices(self, st: int, en: int):
        """
        Set the simulation indices
        :param st: start index
        :param en: end index
        """
        self.simulation_start_index = st
        self.simulation_end_index = en

    def get_diagram_slider_index(self) -> Union[int, None]:
        """
        Get the diagram slider value
        :return: [None, int]
        """
        idx = self.ui.diagram_step_slider.value()
        return idx if idx > -1 else None

    def get_db_slider_index(self) -> Union[int, None]:
        """
        Get the db slider value
        :return: [None, int]
        """
        idx = self.ui.db_step_slider.value()
        return idx if idx > -1 else None

    def setup_time_sliders(self):
        """
        Setup the time sliders
        """
        for slider in [self.ui.diagram_step_slider,
                       self.ui.db_step_slider,
                       self.ui.compiled_arrays_step_slider]:
            if self.circuit.has_time_series:
                slider.setRange(-1, self.circuit.get_time_number() - 1)
            else:
                slider.setRange(-1, -1)
            slider.setValue(-1)

    def update_date_dependent_combos(self):
        """
        update the drop down menus that display dates
        """
        if self.circuit.time_profile is not None:
            mdl = gf.get_list_model([str(e) for e in self.circuit.time_profile])
            # setup profile sliders
            t = len(self.circuit.time_profile) - 1
            self.setup_sim_indices(0, t)

        else:
            mdl = QtGui.QStandardItemModel()
            self.setup_sim_indices(-1, -1)
        self.ui.vs_departure_comboBox.setModel(mdl)
        self.ui.vs_target_comboBox.setModel(mdl)
        self.setup_time_sliders()

    def update_from_to_list_views(self):
        """
        Update the exchange area, countries, etc... dependent combos
        """
        same_type = self.ui.fromComboBox.currentText() == self.ui.toComboBox.currentText()

        devs_from = self.circuit.get_elements_by_type(self.exchange_places_dict[self.ui.fromComboBox.currentText()])
        mdl1 = gf.get_list_model([str(elm) for elm in devs_from], checks=True)
        self.ui.fromListView.setModel(mdl1)

        devs_to = self.circuit.get_elements_by_type(self.exchange_places_dict[self.ui.toComboBox.currentText()])
        mdl2 = gf.get_list_model([str(elm) for elm in devs_to], checks=True)
        self.ui.toListView.setModel(mdl2)

        if len(devs_from) > 1 and same_type:
            self.ui.fromListView.model().item(0).setCheckState(QtCore.Qt.CheckState.Checked)
            self.ui.toListView.model().item(1).setCheckState(QtCore.Qt.CheckState.Checked)

    def fix_generators_active_based_on_the_power(self, ask_before=True):
        """
        set the generators active based on the active power values
        :return:
        """

        if ask_before:
            ok = yes_no_question("This action sets the generation active profile based on the active power profile "
                                 "such that ig a generator active power is zero, the active value is false",
                                 "Set generation active profile")
        else:
            ok = True

        if ok:
            self.circuit.set_generators_active_profile_from_their_active_power()
            self.circuit.set_batteries_active_profile_from_their_active_power()

    def fix_loads_active_based_on_the_power(self, ask_before=True):
        """
        set the loads active based on the active power values
        :return:
        """

        if ask_before:
            ok = yes_no_question("This action sets the generation active profile based on the active power profile "
                                 "such that ig a generator active power is zero, the active value is false",
                                 "Set generation active profile")
        else:
            ok = True

        if ok:
            self.circuit.set_loads_active_profile_from_their_active_power()

    def get_preferred_engine(self) -> EngineType:
        """
        Get the currently selected engine
        :return: EngineType
        """
        val = self.ui.engineComboBox.currentText()
        return self.engine_dict[val]

    def about_box(self):
        """
        Display about box
        :return:
        """

        self.about_msg_window = AboutDialogueGuiGUI(self)
        self.about_msg_window.setVisible(True)

    @staticmethod
    def ai_config_file_path() -> str:
        """
        Return the AI configuration file path.

        :returns: AI configuration file path.
        """
        return os.path.join(get_create_veragrid_folder(), "ai_config.json")

    def find_first_gguf_file(self, directory_path: str) -> str:
        """
        Find the first GGUF file in a directory in lexicographic order.

        :param directory_path: Directory to inspect.
        :returns: GGUF file name or an empty string.
        """
        expanded_directory_path: str = os.path.expanduser(directory_path)
        entry_names: list[str]
        sorted_entry_names: list[str]
        index: int = 0

        if os.path.isdir(expanded_directory_path):
            try:
                entry_names = os.listdir(expanded_directory_path)
            except OSError:
                return ""

            sorted_entry_names = sorted(entry_names)

            # Prefer a stable first GGUF file so the local backend opens ready to use.
            while index < len(sorted_entry_names):
                entry_name: str = sorted_entry_names[index]
                if entry_name.lower().endswith(".gguf"):
                    return entry_name
                else:
                    pass
                index += 1

            return ""
        else:
            return ""

    def build_default_ai_backend_state(self) -> AiBackendState:
        """
        Build the default AI backend state for the main window.

        :returns: Default backend state.
        """
        candidate_paths: list[str] = list()
        home_models_path: str = os.path.expanduser("~/models")
        home_downloads_path: str = os.path.expanduser("~/Downloads")
        project_directory_path: str = os.path.expanduser(self.project_directory)
        model_name: str = ""
        model_path: str = ""
        candidate_index: int = 0

        candidate_paths.append(home_models_path)
        candidate_paths.append(home_downloads_path)

        if len(project_directory_path) > 0:
            candidate_paths.append(project_directory_path)
            candidate_paths.append(os.path.join(project_directory_path, "models"))
        else:
            pass

        # Probe a few likely model directories so the floating AI window starts close to a usable local setup.
        while candidate_index < len(candidate_paths):
            candidate_path: str = candidate_paths[candidate_index]
            model_name = self.find_first_gguf_file(candidate_path)
            if len(model_name) > 0:
                model_path = candidate_path
                candidate_index = len(candidate_paths)
            else:
                candidate_index += 1

        if len(model_path) == 0:
            model_path = home_models_path
        else:
            pass

        return AiBackendState(
            provider_tpe=ProviderType.LOCAL_LLAMA_CPP,
            model_name=model_name,
            base_url=model_path,
            api_key=None,
            timeout_s=60.0,
            context_window_tokens=4096,
            completion_tokens=1024,
            gpu_layers=33,
            temperature=0.15,
            top_p=0.90,
            history_message_limit=6,
            history_char_budget=2200,
            grounding_char_budget=1800,
        )

    def build_ai_config_data(self) -> dict[str, str | float | bool]:
        """
        Build the persistable AI configuration dictionary.

        :returns: AI configuration dictionary.
        """
        state_to_save: AiBackendState
        data: dict[str, str | float | bool] = dict()

        if self.ai_chat_dialogue is None:
            state_to_save = self.ai_backend_state
        else:
            state_to_save = self.ai_chat_dialogue.get_backend_state()

        data["provider_tpe"] = state_to_save.provider_tpe.value
        data["model_name"] = state_to_save.model_name
        data["base_url"] = state_to_save.base_url
        data["api_key"] = state_to_save.api_key or ""
        data["timeout_s"] = state_to_save.timeout_s
        data["context_window_tokens"] = state_to_save.context_window_tokens
        data["completion_tokens"] = state_to_save.completion_tokens
        data["gpu_layers"] = state_to_save.gpu_layers
        data["temperature"] = state_to_save.temperature
        data["top_p"] = state_to_save.top_p
        data["history_message_limit"] = state_to_save.history_message_limit
        data["history_char_budget"] = state_to_save.history_char_budget
        data["grounding_char_budget"] = state_to_save.grounding_char_budget
        # The AI window must always stay hidden at startup until the user opens it manually.
        data["visible"] = False

        return data

    def apply_ai_config_data(self, data: dict[str, object]) -> None:
        """
        Apply persisted AI configuration data.

        :param data: Persisted AI configuration dictionary.
        :returns: Nothing.
        """
        provider_value: object = data.get("provider_tpe", ProviderType.LOCAL_LLAMA_CPP.value)
        provider_tpe: ProviderType = ProviderType.LOCAL_LLAMA_CPP
        api_key_obj: object = data.get("api_key", "")
        timeout_obj: object = data.get("timeout_s", 60.0)
        context_window_tokens_obj: object = data.get("context_window_tokens", 4096)
        completion_tokens_obj: object = data.get("completion_tokens", 1024)
        gpu_layers_obj: object = data.get("gpu_layers", 33)
        temperature_obj: object = data.get("temperature", 0.15)
        top_p_obj: object = data.get("top_p", 0.90)
        history_message_limit_obj: object = data.get("history_message_limit", 6)
        history_char_budget_obj: object = data.get("history_char_budget", 2200)
        grounding_char_budget_obj: object = data.get("grounding_char_budget", 1800)
        provider_items: list[ProviderType] = list(ProviderType)
        enum_index: int = 0

        while enum_index < len(provider_items):
            enum_item: ProviderType = provider_items[enum_index]
            if provider_value == enum_item.value:
                provider_tpe = enum_item
                enum_index = len(provider_items)
            else:
                enum_index += 1

        self.ai_backend_state = AiBackendState(
            provider_tpe=provider_tpe,
            model_name=str(data.get("model_name", "")),
            base_url=str(data.get("base_url", self.build_default_ai_backend_state().base_url)),
            api_key=str(api_key_obj) if isinstance(api_key_obj, str) and len(api_key_obj) > 0 else None,
            timeout_s=float(timeout_obj) if isinstance(timeout_obj, (int, float)) else 60.0,
            context_window_tokens=(
                int(context_window_tokens_obj)
                if isinstance(context_window_tokens_obj, int)
                else 4096
            ),
            completion_tokens=(
                int(completion_tokens_obj)
                if isinstance(completion_tokens_obj, int)
                else 1024
            ),
            gpu_layers=int(gpu_layers_obj) if isinstance(gpu_layers_obj, int) else 33,
            temperature=(
                float(temperature_obj)
                if isinstance(temperature_obj, (int, float))
                else 0.15
            ),
            top_p=float(top_p_obj) if isinstance(top_p_obj, (int, float)) else 0.90,
            history_message_limit=(
                int(history_message_limit_obj)
                if isinstance(history_message_limit_obj, int)
                else 6
            ),
            history_char_budget=(
                int(history_char_budget_obj)
                if isinstance(history_char_budget_obj, int)
                else 2200
            ),
            grounding_char_budget=(
                int(grounding_char_budget_obj)
                if isinstance(grounding_char_budget_obj, int)
                else 1800
            ),
        )
        self.ai_restore_visible = False

        if self.ai_chat_dialogue is None:
            pass
        else:
            self.ai_chat_dialogue.apply_backend_state(self.ai_backend_state)

    def save_ai_config(self) -> None:
        """
        Save the AI configuration to disk.

        :returns: Nothing.
        """
        with open(self.ai_config_file_path(), "w") as file_pointer:
            file_pointer.write(json.dumps(self.build_ai_config_data(), indent=4))

    def load_ai_config(self) -> None:
        """
        Load the AI configuration from disk.

        :returns: Nothing.
        """
        config_path: str = self.ai_config_file_path()

        if os.path.exists(config_path):
            with open(config_path, "r") as file_pointer:
                try:
                    self.apply_ai_config_data(json.load(file_pointer))
                except json.decoder.JSONDecodeError:
                    self.ai_backend_state = self.build_default_ai_backend_state()
                    self.ai_restore_visible = False
                    self.save_ai_config()
                    self.show_warning_toast("AI config file was erroneous, wrote a new one")
        else:
            self.ai_backend_state = self.build_default_ai_backend_state()
            self.ai_restore_visible = False

        self.ai_restore_visible = False

    def ensure_ai_dialogue(self) -> None:
        """
        Create the floating AI dialogue lazily and bind it to the live main window.

        :returns: Nothing.
        """
        if self.ai_chat_dialogue is None:
            self.ai_chat_dialogue = AiChatDialogue(parent=self, app=self)
            self.ai_chat_dialogue.set_embedded_mode(False)
            self.ai_chat_dialogue.apply_backend_state(self.ai_backend_state)
            self.ai_chat_dialogue.dialogue_visibility_changed.connect(
                self.handle_ai_dialogue_visibility_changed
            )
        else:
            self.ai_chat_dialogue.apply_backend_state(self.ai_backend_state)

    def sync_ai_dialogue_action_state(self, visible: bool) -> None:
        """
        Synchronize the floating dialogue visibility with the toolbar/menu action state.

        :param visible: Dialogue visibility.
        :returns: Nothing.
        """
        self.ui.actionai_chat.blockSignals(True)
        self.ui.actionai_chat.setChecked(visible)
        self.ui.actionai_chat.blockSignals(False)

        self.ai_restore_visible = visible

        if visible:
            self.refresh_ai_context_if_available()
        else:
            pass

    def refresh_ai_context_if_available(self) -> None:
        """
        Refresh the AI dialogue context when the floating window exists.

        :returns: Nothing.
        """
        if self.ai_chat_dialogue is None:
            pass
        else:
            self.ai_chat_dialogue.refresh_context_from_app()

    def handle_ai_dialogue_visibility_changed(self, visible: bool) -> None:
        """
        Keep the AI action state synchronized with the persistent floating dialogue.

        :param visible: Dialogue visibility state.
        :returns: Nothing.
        """
        self.sync_ai_dialogue_action_state(visible)

    def shutdown_ai_dialogue_if_available(self) -> None:
        """
        Stop the AI worker thread when the dialogue exists.

        :returns: Nothing.
        """
        if self.ai_chat_dialogue is None:
            pass
        else:
            self.ai_chat_dialogue.prepare_for_shutdown()
            self.ai_chat_dialogue.shutdown_turn_thread()

    def set_ai_dialogue_visible(self, visible: bool) -> None:
        """
        Show or hide the floating AI dialogue.

        :param visible: Desired visibility.
        :returns: Nothing.
        """
        self.ensure_ai_dialogue()

        if self.ai_chat_dialogue is None:
            pass
        else:
            if visible:
                self.ai_chat_dialogue.show()
                self.ai_chat_dialogue.raise_()
                self.ai_chat_dialogue.activateWindow()
                self.refresh_ai_context_if_available()
                self.ai_backend_state = self.ai_chat_dialogue.get_backend_state()
                if (
                    self.ai_backend_state.provider_tpe == ProviderType.LOCAL_LLAMA_CPP
                    and len(self.ai_backend_state.base_url.strip()) == 0
                ):
                    default_state: AiBackendState = self.build_default_ai_backend_state()
                    self.ai_backend_state = default_state
                    self.ai_chat_dialogue.apply_backend_state(default_state)
                else:
                    pass

                if self.ai_backend_state.provider_tpe == ProviderType.LOCAL_LLAMA_CPP:
                    self.ai_chat_dialogue.refresh_available_models()
                    self.ai_backend_state = self.ai_chat_dialogue.get_backend_state()
                else:
                    pass

                if len(self.ai_backend_state.model_name.strip()) == 0:
                    self.show_info_toast("Configure a local GGUF model path for the AI window", duration=3500)
                else:
                    pass

                self.sync_ai_dialogue_action_state(True)
            else:
                self.ai_chat_dialogue.hide()
                self.sync_ai_dialogue_action_state(False)

    def open_ai_chat_dialogue(self) -> None:
        """
        Open the AI dialogue connected to the live VeraGrid main window.

        :returns: Nothing.
        """
        self.set_ai_dialogue_visible(True)

    @staticmethod
    def show_online_docs():
        """
        Open the online documentation in a web browser
        """
        webbrowser.open('https://veragrid.readthedocs.io/en/latest/', new=2)

    @staticmethod
    def report_a_bug():
        """
        Open the online github issues in a web browser
        """
        webbrowser.open('https://github.com/SanPen/VeraGrid/issues', new=2)

    def auto_rate_branches(self):
        """
        Rate the Branches that do not have rate
        """

        branches = self.circuit.get_branches()

        if len(branches) > 0:
            _, pf_results = self.session.power_flow

            if pf_results is not None:
                factor = self.ui.branch_rating_doubleSpinBox.value()

                for i, branch in enumerate(branches):

                    S = pf_results.Sf[i]

                    if branch.rate < 1e-3 or self.ui.rating_override_checkBox.isChecked():
                        r = np.round(abs(S) * factor, 1)
                        branch.rate = r if r > 0.0 else 1.0
                    else:
                        pass  # the rate is ok

            else:
                info_msg('Run a power flow simulation first.\nThe results are needed in this function.')

        else:
            warning_msg('There are no Branches!')

    def detect_transformers(self):
        """
        Detect which Branches are transformers
        """
        if len(self.circuit.lines) > 0:

            for elm in self.circuit.lines:

                v1 = elm.bus_from.Vnom
                v2 = elm.bus_to.Vnom

                if abs(v1 - v2) > 1.0:
                    self.circuit.convert_line_to_transformer(elm)
                else:

                    pass  # is a line

        else:
            warning_msg('There are no Branches!')

    def set_cancel_state(self) -> None:
        """
        Cancel what ever's going on that can be cancelled
        @return:
        """

        reply = QtWidgets.QMessageBox.question(self, 'Message',
                                               'Are you sure that you want to cancel the simulation?',
                                               QtWidgets.QMessageBox.StandardButton.Yes,
                                               QtWidgets.QMessageBox.StandardButton.No)

        if reply == QtWidgets.QMessageBox.StandardButton.Yes.value:
            # send the cancel state to whatever it is being executed

            for drv in self.get_all_threads():
                if drv is not None:
                    if hasattr(drv, 'cancel'):
                        drv.cancel()
        else:
            pass

    def display_grid_analysis(self):
        """
        Display the grid analysis GUI
        """

        self.analysis_dialogue = GridAnalysisGUI(circuit=self.circuit)

        self.analysis_dialogue.resize(int(1.61 * 600.0), 600)
        self.analysis_dialogue.show()

    def change_circuit_base(self):
        """
        Update the circuit base values from the UI
        """

        Sbase_new = self.ui.sbase_doubleSpinBox.value()
        self.circuit.change_base(Sbase_new)

        self.circuit.fBase = self.ui.fbase_doubleSpinBox.value()

    def change_circuit_name(self):
        """

        :return:
        """
        self.circuit.name = self.ui.grid_name_line_edit.text().strip()

    def get_snapshot_circuit(self):
        """
        Get a snapshot compilation
        :return: SnapshotData instance
        """
        return compile_numerical_circuit_at(circuit=self.circuit)

    @property
    def numerical_circuit(self) -> NumericalCircuit:
        """
        get the snapshot NumericalCircuit
        :return: NumericalCircuit
        """
        return self.get_snapshot_circuit()

    @property
    def islands(self) -> List[NumericalCircuit]:
        """
        get the snapshot islands
        :return: List[NumericalCircuit]
        """
        numerical_circuit = compile_numerical_circuit_at(circuit=self.circuit)
        calculation_inputs = numerical_circuit.split_into_islands()
        return calculation_inputs

    def initialize_contingencies(self):
        """
        Launch the contingency planner to initialize the contingencies
        :return:
        """
        self.contingency_planner_dialogue = ContingencyPlannerGUI(parent=self, grid=self.circuit)
        self.contingency_planner_dialogue.exec()

        # gather results
        if self.contingency_planner_dialogue.generated_results:
            if len(self.contingency_planner_dialogue.contingency_groups):
                self.circuit.contingency_groups += self.contingency_planner_dialogue.contingency_groups
                self.circuit.contingencies += self.contingency_planner_dialogue.contingencies
            else:
                info_msg(text="No contingencies were generated :/", title="Contingency planner")

    def show_toast(self, message: str, duration: int = 2000):
        """
        Show generic toast
        :param message: Message to display
        :param duration: duration in ms
        """
        self.toast_manager.show_toast(message=message, duration=duration, toast_type="veragrid")

    def show_error_toast(self, message: str, duration: int = 2000):
        """
        Show error toast
        :param message: Message to display
        :param duration: duration in ms
        """
        self.toast_manager.show_error_toast(message=message, duration=duration)

    def show_warning_toast(self, message: str, duration: int = 2000):
        """
        Show warning toast
        :param message: Message to display
        :param duration: duration in ms
        """
        self.toast_manager.show_warning_toast(message=message, duration=duration)

    def show_info_toast(self, message: str, duration: int = 2000):
        """
        Show info toast
        :param message: Message to display
        :param duration: duration in ms
        """
        self.toast_manager.show_info_toast(message=message, duration=duration)

    def get_clustering_results(self) -> Union[ClusteringResults, None]:
        """
        Get the clustering results if available
        :return: ClusteringResults or None
        """
        if self.ui.actionUse_clustering.isChecked():
            _, clustering_results = self.session.clustering

            if clustering_results is not None:
                n = len(clustering_results.time_indices)

                if n != self.ui.cluster_number_spinBox.value():
                    error_msg("The number of clusters in the stored results is different from the specified :(\n"
                              "Run another clustering analysis.")

                    return None
                else:
                    # all ok
                    return clustering_results
            else:
                # no results ...
                self.show_warning_toast("There are no clustering results.")
                self.ui.actionUse_clustering.setChecked(False)
                return None

        else:
            # not marked ...
            return None
