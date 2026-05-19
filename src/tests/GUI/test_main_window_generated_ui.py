from typing import Tuple

from PySide6 import QtWidgets

from VeraGrid.Gui.Main.MainWindow import Ui_mainWindow


def build_main_window() -> Tuple[QtWidgets.QMainWindow, Ui_mainWindow]:
    """
    Build the generated main-window UI on a plain Qt main window.

    :return: Main window and configured generated UI object.
    """
    window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    ui: Ui_mainWindow = Ui_mainWindow()
    ui.setupUi(window)
    return window, ui


def test_generated_main_window_builds_core_tab_widgets(qt_app: object) -> None:
    """
    Check that generated MainWindow UI exposes the tab widgets used by VeraGridMainGUI.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    window: QtWidgets.QMainWindow
    ui: Ui_mainWindow
    window, ui = build_main_window()

    assert ui.mainTabWidget.count() > 0
    assert ui.modelTabWidget.count() > 0
    assert ui.settingsTabWidget.count() > 0
    assert ui.resultsTabWidget.count() > 0
    assert ui.mainTabWidget.currentIndex() >= 0
    assert ui.modelTabWidget.currentIndex() >= 0

    window.close()
    window.deleteLater()


def test_generated_main_window_exposes_splitters_used_by_main_gui(qt_app: object) -> None:
    """
    Check that generated MainWindow UI exposes the splitters configured by VeraGridMainGUI.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    window: QtWidgets.QMainWindow
    ui: Ui_mainWindow
    window, ui = build_main_window()

    assert ui.dataStructuresSplitter.count() >= 2
    assert ui.simulationDataSplitter.count() >= 2
    assert ui.results_splitter.count() >= 2
    assert ui.diagram_selection_splitter.count() >= 2

    window.close()
    window.deleteLater()


def test_generated_main_window_exposes_main_actions(qt_app: object) -> None:
    """
    Check that generated MainWindow UI exposes actions connected by Main subclasses.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    window: QtWidgets.QMainWindow
    ui: Ui_mainWindow
    window, ui = build_main_window()

    assert ui.actionPower_flow.text() != ""
    assert ui.actionPower_flow_3ph.text() != ""
    assert ui.actionLinearAnalysis.text() != ""
    assert ui.actionRun_Dynamic_RMS_Simulation.text() != ""
    assert ui.actionRun_Dynamic_EMT_Simulation.text() != ""
    assert ui.actionRun_Small_Signal_RMS_Simulation.text() != ""
    assert ui.actionRun_Small_Signal_EMT_Simulation.text() != ""
    assert ui.actionDelete_selected.text() != ""
    assert ui.actionSync.text() != ""

    window.close()
    window.deleteLater()
