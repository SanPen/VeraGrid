# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import sys
import chardet
import subprocess
import time
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from typing import List
from VeraGrid.Gui.AboutDialogue.about_gui import Ui_AboutDialog
from VeraGrid.__version__ import __VeraGrid_VERSION__
from VeraGrid.update import check_version, get_upgrade_command
from VeraGridEngine.__version__ import __VeraGridEngine_VERSION__, copyright_msg, contributors_msg
from VeraGridEngine.Compilers.Gslv import (GSLV_AVAILABLE,
                                                      GSLV_RECOMMENDED_VERSION,
                                                      GSLV_VERSION)
from VeraGridEngine.Compilers.circuit_to_pgm import (PGM_AVAILABLE,
                                                     PGM_RECOMMENDED_VERSION,
                                                     PGM_VERSION)

try:
    from importlib.metadata import distributions


    def get_packages():
        """
        Get system libraries info
        :return:
        """
        for d in distributions():
            name = d.metadata.get("Name", "")
            version = d.version
            license_ = d.metadata.get("License", "")

            # Installation directory
            try:
                install_path = str(d.locate_file(""))
            except Exception:
                install_path = ""

            # Dependencies
            deps = d.metadata.get_all("Requires-Dist") or []
            deps_text = ", ".join(deps)

            yield name, version, license_, install_path, deps_text

except ImportError:
    import pkg_resources


    def get_packages():
        """
        Get system libraries info
        :return:
        """
        for d in pkg_resources.working_set:
            name = d.project_name
            version = d.version
            license_ = getattr(d, "license", "")

            install_path = d.location

            # Dependencies (requires)
            deps = d.requires()
            deps_text = ", ".join(str(dep) for dep in deps)

            yield name, version, license_, install_path, deps_text


def make_item(text):
    """Create a read-only table item."""
    item = QtWidgets.QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def sanitize_tsv_field(text: str) -> str:
    """

    :param text:
    :return:
    """
    if text is None:
        return ""
    # Replace tabs and newlines with safe placeholders
    text = text.replace("\t", " ")  # remove tabs
    text = text.replace("\r\n", " ")  # Windows newlines
    text = text.replace("\n", " ")  # Unix newlines
    text = text.replace("\r", " ")  # Old mac newlines
    return text.strip()


def run_upgrade_command(command: List[str], max_attempts: int) -> tuple[int, str, int]:
    """
    Run the package upgrade command with a bounded retry loop.

    Some user environments fail during the first ``pip install --upgrade`` run
    but succeed when the exact same command is executed again. Retrying a small
    number of times is cheaper than asking the user to repeat the action
    manually.

    :param command: Upgrade command already split for ``subprocess.run``.
    :param max_attempts: Maximum number of attempts.
    :return: Final exit code, collected command output and number of attempts used.
    """
    attempt_number: int = 0
    process_result: subprocess.CompletedProcess[str]
    output_chunks: List[str] = list()
    output_text: str

    while attempt_number < max_attempts:
        attempt_number = attempt_number + 1

        # Capture stdout and stderr together because pip error details are
        # useful both for retries and for the final message shown to the user.
        process_result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_text = process_result.stdout if process_result.stdout is not None else ""
        output_chunks.append(f"Attempt {attempt_number}\n{output_text}")

        if process_result.returncode == 0:
            return process_result.returncode, "\n\n".join(output_chunks), attempt_number
        else:
            if attempt_number < max_attempts:
                time.sleep(1.0)
            else:
                pass

    return process_result.returncode, "\n\n".join(output_chunks), attempt_number


def translate_about_dialog(source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
    """
    Translate one runtime About dialog string through the generated UI context.

    :param source_text: Source string to translate.
    :param disambiguation: Optional Qt disambiguation text.
    :param n: Optional plural parameter.
    :return: Translated text.
    """
    return QtCore.QCoreApplication.translate("AboutDialog", source_text, disambiguation, n)


class AboutDialogueGuiGUI(QtWidgets.QDialog):
    """
    AboutDialogueGuiGUI
    """

    def __init__(self, parent=None):
        """

        :param parent:
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('About VeraGrid'))
        self.setAcceptDrops(True)

        self.fill_optional_libs()
        self.fill_libs()

        # check the version in pypi
        version_code, latest_version = check_version()

        self.upgrade_cmd: List[str] = ['']

        if version_code == 1:
            addendum = '\nThere is a newer version: ' + latest_version

            self.upgrade_cmd = get_upgrade_command(latest_version)
            command = ' '.join(self.upgrade_cmd)
            self.ui.updateLabel.setText('\n\nTerminal command to update:\n\n' + command)
            self.ui.updateButton.setVisible(True)

        elif version_code == -1:
            addendum = '\nThis version is newer than the version available in the repositories (' + latest_version + ')'
            self.ui.updateLabel.setText(addendum)
            self.ui.updateButton.setVisible(False)

        elif version_code == 0:
            addendum = '\nVeraGrid is up to date.'
            self.ui.updateLabel.setText(addendum)
            self.ui.updateButton.setVisible(False)

        elif version_code == -2:
            addendum = '\nIt was impossible to check for a newer version'
            self.ui.updateLabel.setText(addendum)
            self.ui.updateButton.setVisible(False)

        else:
            addendum = ''
            self.ui.updateLabel.setText(addendum)
            self.ui.updateButton.setVisible(False)

        # self.ui.mainLabel.setText(about_msg)
        self.ui.versionLabel.setText('VeraGrid version: ' + __VeraGrid_VERSION__ + ', ' + addendum)
        self.ui.copyrightLabel.setText(copyright_msg)
        self.ui.contributorsLabel.setText(contributors_msg)

        # click
        self.ui.updateButton.clicked.connect(self.update)

        self.ui.copyLibsButton.clicked.connect(self.copy_libs)

        self.show_license()

    def tr(self, source_text: str, disambiguation: str | None = None, n: int = -1) -> str:
        """
        Translate runtime strings through the ``AboutDialog`` catalog context.

        :param source_text: Source string to translate.
        :param disambiguation: Optional Qt disambiguation text.
        :param n: Optional plural parameter.
        :return: Translated text.
        """
        return translate_about_dialog(source_text, disambiguation, n)

    def fill_optional_libs(self):
        """

        :return:
        """
        self.ui.librariesTableWidget.setColumnCount(4)
        self.ui.librariesTableWidget.setRowCount(3)
        self.ui.librariesTableWidget.setHorizontalHeaderLabels([
            self.tr("Name"),
            self.tr("version"),
            self.tr("supported version"),
            self.tr("licensed"),
        ])

        self.ui.librariesTableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem("VeraGrid"))
        self.ui.librariesTableWidget.setItem(0, 1, QtWidgets.QTableWidgetItem(__VeraGrid_VERSION__))
        self.ui.librariesTableWidget.setItem(0, 2, QtWidgets.QTableWidgetItem(__VeraGridEngine_VERSION__))
        self.ui.librariesTableWidget.setItem(0, 3, QtWidgets.QTableWidgetItem(self.tr("True")))

        # GSLV
        self.ui.librariesTableWidget.setItem(1, 0, QtWidgets.QTableWidgetItem("GSLV"))
        self.ui.librariesTableWidget.setItem(1, 1, QtWidgets.QTableWidgetItem(GSLV_VERSION
                                                                              if GSLV_AVAILABLE else
                                                                              self.tr("Not installed")))

        self.ui.librariesTableWidget.setItem(1, 2, QtWidgets.QTableWidgetItem(GSLV_RECOMMENDED_VERSION))
        self.ui.librariesTableWidget.setItem(1, 3, QtWidgets.QTableWidgetItem(str(GSLV_AVAILABLE)))

        # PGM
        self.ui.librariesTableWidget.setItem(2, 0, QtWidgets.QTableWidgetItem("power-grid-model"))
        self.ui.librariesTableWidget.setItem(2, 1, QtWidgets.QTableWidgetItem(PGM_VERSION
                                                                              if PGM_AVAILABLE else
                                                                              self.tr("Not installed")))
        self.ui.librariesTableWidget.setItem(2, 2, QtWidgets.QTableWidgetItem(PGM_RECOMMENDED_VERSION))
        self.ui.librariesTableWidget.setItem(2, 3, QtWidgets.QTableWidgetItem(str(PGM_AVAILABLE)))

    def fill_libs(self):

        self.ui.allLibsTableWidget.setColumnCount(5)
        self.ui.allLibsTableWidget.setHorizontalHeaderLabels([
            self.tr("Package"), self.tr("Version"), self.tr("License"),
            self.tr("Installation Path"), self.tr("Dependencies")
        ])

        pkgs = sorted(get_packages(), key=lambda x: x[0].lower())
        self.ui.allLibsTableWidget.setRowCount(len(pkgs))

        for row, (name, version, license_, path, deps) in enumerate(pkgs):
            self.ui.allLibsTableWidget.setItem(row, 0, make_item(name))
            self.ui.allLibsTableWidget.setItem(row, 1, make_item(version))
            self.ui.allLibsTableWidget.setItem(row, 2, make_item(license_))
            self.ui.allLibsTableWidget.setItem(row, 3, make_item(path))
            self.ui.allLibsTableWidget.setItem(row, 4, make_item(deps))

        self.ui.allLibsTableWidget.resizeColumnsToContents()

    def msg(self, text, title="Warning"):
        """
        Message box
        :param text: Text to display
        :param title: Name of the window
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText(text)
        # msg.setInformativeText("This is additional information")
        msg.setWindowTitle(title)
        # msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        retval = msg.exec()

    def update(self):
        """
        Upgrade VeraGrid
        :return:
        """
        max_attempts: int = 3
        return_code: int
        command_output: str
        attempts_used: int
        message_text: str
        output_excerpt: str

        return_code, command_output, attempts_used = run_upgrade_command(
            command=self.upgrade_cmd,
            max_attempts=max_attempts
        )

        output_excerpt = command_output[-4000:] if len(command_output) > 4000 else command_output

        if return_code != 0:
            message_text = (
                f"VeraGrid update failed after {attempts_used} attempt(s).\n"
                f"Exit code: {return_code}\n\n"
                f"Command output:\n{output_excerpt}"
            )
            self.msg(message_text)
        else:
            if attempts_used == 1:
                message_text = 'VeraGrid updated successfully'
            else:
                message_text = f'VeraGrid updated successfully after {attempts_used} attempts'

            self.msg(message_text)

    def copy_libs(self):
        """

        :return:
        """
        rows = self.ui.allLibsTableWidget.rowCount()
        cols = self.ui.allLibsTableWidget.columnCount()

        lines = []
        # Header
        header = "\t".join(
            self.ui.allLibsTableWidget.horizontalHeaderItem(c).text()
            for c in range(cols)
        )
        lines.append(header)

        # Data
        for r in range(rows):
            row_vals = []
            for c in range(cols):
                item = self.ui.allLibsTableWidget.item(r, c)
                txt = sanitize_tsv_field(item.text().replace("\t", "    ") if item else "")

                row_vals.append(txt)
            lines.append("\t".join(row_vals))

        tsv_text = "\n".join(lines)

        QtWidgets.QApplication.clipboard().setText(tsv_text, QClipboard.Mode.Clipboard)

    def show_license(self):
        """
        Show the license
        """
        here = os.path.abspath(os.path.dirname(__file__))
        license_file = os.path.join(here, '..', '..', 'LICENSE.txt')

        # make a guess of the file encoding
        detection = chardet.detect(open(license_file, "rb").read())

        with open(license_file, 'r', encoding=detection['encoding']) as file:
            license_txt = file.read()

        self.ui.licenseTextEdit.setPlainText(license_txt)


# if __name__ == "__main__":
#     app = QtWidgets.QApplication(sys.argv)
#     window = AboutDialogueGuiGUI()
#     # window.resize(1.61 * 700.0, 600.0)  # golden ratio
#     window.show()
#     sys.exit(app.exec())
