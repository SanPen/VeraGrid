# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

import os.path
import sys

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from VeraGrid.Gui.Main.MainWindow import QApplication
from PySide6.QtCore import QDirIterator, QResource
from PySide6.QtSvg import QSvgRenderer
from VeraGrid.Gui.i18n import ApplicationTranslator, read_saved_language
from VeraGrid.Gui.update_gui_all import update_all_icons
from VeraGrid.Gui.Main.SubClasses.Scripting.scripting import ScriptingMain
import VeraGrid.ThirdParty.qdarktheme as qdarktheme
from VeraGrid.__version__ import __VeraGrid_VERSION__

__author__ = 'Santiago Peñate Vera'

"""
This class is the handler of the main gui of VeraGrid.
"""


########################################################################################################################
# Main Window
########################################################################################################################

class VeraGridMainGUI(ScriptingMain):
    """
    MainGUI
    """

    def __init__(self, translation_controller: ApplicationTranslator | None = None) -> None:
        """
        Main constructor
        """

        # create main window
        ScriptingMain.__init__(self, parent=None)
        if translation_controller is not None:
            self.set_translation_controller(translation_controller)
        else:
            pass
        self.setWindowTitle(self.tr("VeraGrid {version}").format(version=__VeraGrid_VERSION__))
        self.setAcceptDrops(True)

        self.ui.mainTabWidget.setCurrentIndex(0)
        self.ui.modelTabWidget.setCurrentIndex(0)
        self.ui.settingsTabWidget.setCurrentIndex(0)
        self.ui.resultsTabWidget.setCurrentIndex(0)

        ################################################################################################################
        # Set splitters
        ################################################################################################################

        # 1:4
        self.ui.dataStructuresSplitter.setStretchFactor(0, 3)
        self.ui.dataStructuresSplitter.setStretchFactor(1, 4)

        self.ui.simulationDataSplitter.setStretchFactor(1, 15)

        self.ui.results_splitter.setStretchFactor(0, 2)
        self.ui.results_splitter.setStretchFactor(1, 4)

        self.ui.diagram_selection_splitter.setStretchFactor(0, 10)
        self.ui.diagram_selection_splitter.setStretchFactor(1, 2)

        ################################################################################################################
        # Other actions
        ################################################################################################################

        self.ui.grid_colouring_frame.setVisible(True)

        self.ui.actionSync.setVisible(False)

        self.modify_ui_options_according_to_the_engine()

        # this is the contingency planner tab, invisible until done
        self.ui.modelTabWidget.setTabVisible(4, True)

        self.clear_results()

        self.load_all_config()

        self.add_complete_bus_branch_diagram()
        # self.add_map_diagram(ask=False)
        self.set_diagram_widget(self.diagram_widgets_list[0])
        self.update_available_results()

        self.ui.actionRun_Dynamic_RMS_Simulation.setVisible(True)
        self.ui.actionRun_Small_Signal_RMS_Simulation.setVisible(True)

        # global delete function
        self.ui.actionDelete_selected.triggered.connect(self.global_delete)

    def refresh_runtime_translations(self) -> None:
        """
        Refresh runtime-owned main-window strings after a language change.

        :returns: None.
        """
        super().refresh_runtime_translations()
        self.setWindowTitle(self.tr("VeraGrid {version}").format(version=__VeraGrid_VERSION__))

    def global_delete(self):
        """
        Function to dispatch what to do when [supr] is pressed
        :return:
        """
        if self.ui.mainTabWidget.currentIndex() == 0:  # Model
            if self.ui.modelTabWidget.currentIndex() == 0:  # Diagrams
                self.delete_selected_diagram_widgets()

            elif self.ui.modelTabWidget.currentIndex() == 1:  # Database
                self.delete_selected_db_table_objects()

            else:
                self.show_warning_toast(self.tr("No effect, select diagrams or database"))
        else:
            self.show_warning_toast(self.tr("No effect, select diagrams or database"))

    def save_all_config(self) -> None:
        """
        Save all configuration files needed
        """
        self.save_gui_config()
        self.save_server_config()
        self.save_ai_config()

    def load_all_config(self) -> None:
        """
        Load all configuration files needed
        """
        self.load_gui_config()
        self.load_server_config()
        self.load_ai_config()
        self.add_plugins()

        # apply the theme selected by the settings
        self.change_theme_mode()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Close event
        :param event:
        :return:
        """
        if self.circuit.get_bus_number() > 0:
            quit_msg = self.tr("Are you sure that you want to exit VeraGrid?")
            reply = QtWidgets.QMessageBox.question(self, self.tr("Close"), quit_msg,
                                                   QtWidgets.QMessageBox.StandardButton.Yes,
                                                   QtWidgets.QMessageBox.StandardButton.No)

            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                # save config regardless
                self.save_all_config()
                self.shutdown_ai_dialogue_if_available()
                self.stop_all_threads()
                event.accept()
            else:
                # save config regardless
                self.save_all_config()
                event.ignore()
        else:
            # no buses so exit
            # save config regardless
            self.save_all_config()
            self.shutdown_ai_dialogue_if_available()
            self.stop_all_threads()
            event.accept()


def create_linux_desktop_entry(app_name: str, qrc_icon_path: str):
    """
    Create a .desktop entry for a PySide app using a resource icon (":/path/to/icon.svg").

    Parameters
    ----------
    app_name : str
        Name of the application (also used for StartupWMClass).
    qrc_icon_path : str
        Path to the icon inside the .qrc (e.g. ':/icons/app_icon.svg')
    """
    if not sys.platform.startswith("linux"):
        # print("[INFO] Not running on Linux, skipping .desktop creation.")
        return None

    # Extract icon from Qt resource to a real file
    icon = QIcon(qrc_icon_path)
    if icon.isNull():
        print(f"[WARNING] Could not find icon in resource: {qrc_icon_path}")
        return None

    # Temporary export path (user local cache)
    cache_dir = os.path.expanduser(f"~/.cache/{app_name}")
    os.makedirs(cache_dir, exist_ok=True)
    icon_path = os.path.join(cache_dir, f"{app_name}.png")

    # Save first available icon size
    pixmap = icon.pixmap(256, 256)
    pixmap.save(icon_path, "PNG")

    # Create .desktop entry
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file = os.path.join(desktop_dir, f"{app_name}.desktop")

    if not os.path.exists(desktop_file):
        exec_path = f"{sys.executable} {os.path.abspath(sys.argv[0])}"
        content = f"""[Desktop Entry]
Version={__VeraGrid_VERSION__}
Type=Application
Name={app_name}
Exec={exec_path}
Icon={icon_path}
Terminal=false
StartupWMClass={app_name}
Categories=Utility;
"""
        with open(desktop_file, "w") as f:
            f.write(content)
        os.chmod(desktop_file, 0o755)
        print(f"[OK] Created .desktop entry: {desktop_file}")
    else:
        pass
        # print(f"[INFO] .desktop entry already exists: {desktop_file}")

    return desktop_file


def check_all_svgs():
    """
    Iterate through all resources registered by icons_rc and check SVG validity.
    :returns: if any icon has errors
    """
    it = QDirIterator(":/Icons", QDirIterator.IteratorFlag.Subdirectories)
    bad_files = []

    while it.hasNext():
        path = it.next()
        if path.lower().endswith(".svg"):
            res = QResource(path)
            if not res.isValid():
                print(f"[MISSING] {path}")
                bad_files.append((path, "missing"))
                continue

            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                print(f"[INVALID] {path}")
                bad_files.append((path, "invalid"))
            else:
                pass

    if len(bad_files) > 0:
        print("\nSVG compatibility summary:")
        for path, status in bad_files:
            print(f"  {status.upper():<8} {path}")

        update_all_icons()
    else:
        print("SVG compatibility summary: all ok")


def runVeraGrid() -> None:
    """
    Main function to run the GUI
    :return:
    """

    # if hasattr(qdarktheme, 'enable_hi_dpi'):
    qdarktheme.enable_hi_dpi()

    app = QApplication(sys.argv)
    translation_controller = ApplicationTranslator(app)
    translation_controller.set_language(read_saved_language())

    # MacOS: display icons in menus
    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)

    icon_name = ':/Program icon/icons/VeraGrid_icon.png'
    icon = QtGui.QIcon(icon_name)

    # will check os internally
    create_linux_desktop_entry("veragrid", qrc_icon_path=icon_name)

    # macOS: Fix to show the icon on the task bar
    app.setWindowIcon(icon)

    window_ = VeraGridMainGUI(translation_controller=translation_controller)
    window_.setWindowIcon(icon)  # also apply directly

    # process the argument if provided
    if len(sys.argv) > 1:
        f_name = sys.argv[1]
        if os.path.exists(f_name):
            window_.open_file_now(filenames=[f_name])

    # launch
    h_ = 780
    window_.resize(int(1.7 * h_), h_)  # almost the golden ratio :)
    window_.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    runVeraGrid()
