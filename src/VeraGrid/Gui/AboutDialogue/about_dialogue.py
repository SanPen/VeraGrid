# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import sys
import chardet
import subprocess
import time
import pkg_resources
from importlib.metadata import version, distributions
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard
from typing import List
import packaging.version as pkg
from VeraGrid.Gui.AboutDialogue.about_gui import Ui_AboutDialog
from VeraGrid.__version__ import __VeraGrid_VERSION__
from VeraGrid.update import find_latest_version, get_upgrade_command
from VeraGridEngine.__version__ import __VeraGridEngine_VERSION__, copyright_msg, contributors_msg
from VeraGridEngine.Compilers.Gslv.activation import (GSLV_AVAILABLE,
                                                      GSLV_RECOMMENDED_VERSION,
                                                      GSLV_VERSION)
from VeraGridEngine.Compilers.circuit_to_pgm import (PGM_AVAILABLE,
                                                     PGM_RECOMMENDED_VERSION,
                                                     PGM_VERSION)

try:

    def get_packages():
        """
        Get system libraries info
        :return:
        """
        for d in distributions():
            name = d.metadata.get("Name", "")
            versn = d.version
            license_ = d.metadata.get("License", "")

            # Installation directory
            try:
                install_path = str(d.locate_file(""))
            except Exception:
                install_path = ""

            # Dependencies
            deps = d.metadata.get_all("Requires-Dist") or []
            deps_text = ", ".join(deps)

            yield name, versn, license_, install_path, deps_text

except ImportError:

    def get_packages():
        """
        Get system libraries info
        :return:
        """
        for d in pkg_resources.working_set:
            name = d.project_name
            versn = d.version
            license_ = getattr(d, "license", "")

            install_path = d.location

            # Dependencies (requires)
            deps = d.requires()
            deps_text = ", ".join(str(dep) for dep in deps)

            yield name, versn, license_, install_path, deps_text


def make_item(text):
    """Create a read-only table item."""
    item = QtWidgets.QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


class OptionalLibraryStatus:
    """
    Optional library status displayed in the About dialog.
    """

    __slots__ = ("name", "package_name", "installed", "installed_version", "latest_version", "supported_version",
                 "licensed")

    def __init__(self,
                 name: str,
                 package_name: str,
                 installed: bool,
                 installed_version: str,
                 latest_version: str,
                 supported_version: str,
                 licensed: bool) -> None:
        """
        Build one optional library status row.

        :param name: User-facing library name.
        :param package_name: PyPI package name.
        :param installed: Whether the package is installed.
        :param installed_version: Installed package version.
        :param latest_version: Latest PyPI version.
        :param supported_version: VeraGrid recommended or bundled compatible version.
        :param licensed: Whether the library is licensed or usable.
        :return: None.
        """
        self.name: str = name
        self.package_name: str = package_name
        self.installed: bool = installed
        self.installed_version: str = installed_version
        self.latest_version: str = latest_version
        self.supported_version: str = supported_version
        self.licensed: bool = licensed


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


def get_installed_package_version(package_name: str) -> str:
    """
    Return one installed package version from Python package metadata.

    :param package_name: Distribution package name.
    :return: Installed version or an empty string when unavailable.
    """
    package_version: str = ""

    try:

        package_version = version(package_name)
    except Exception:
        package_version = ""

    return package_version


def get_package_install_command(package_name: str, latest_version: str) -> List[str]:
    """
    Build a pip install or upgrade command for one package.

    :param package_name: Distribution package name.
    :param latest_version: Version to install, or empty for the newest resolvable package.
    :return: Split command suitable for subprocess execution.
    """
    package_spec: str

    if len(latest_version) > 0:
        package_spec = f"{package_name}=={latest_version}"
    else:
        package_spec = package_name

    command: List[str] = [
        sys.executable,
        "-m",
        "pip",
        "install",
        package_spec,
        "--upgrade",
        "--break-system-packages",
    ]
    return command


def can_update_package(installed: bool, installed_version: str, latest_version: str) -> bool:
    """
    Determine whether one installed package can be updated from PyPI data.

    :param installed: Whether the package is installed.
    :param installed_version: Installed package version.
    :param latest_version: Latest PyPI package version.
    :return: True when the latest version is newer than the installed version.
    """
    if installed and len(installed_version) > 0 and len(latest_version) > 0:
        can_update: bool = pkg.parse(latest_version) > pkg.parse(installed_version)
    else:
        can_update = False

    return can_update


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
    process: subprocess.Popen[str]
    output_chunks: List[str] = list()
    attempt_chunks: List[str]
    output_line: str
    return_code: int = 1

    while attempt_number < max_attempts:
        attempt_number = attempt_number + 1
        attempt_chunks = list()
        output_chunks.append(f"Attempt {attempt_number}")
        print(f"Attempt {attempt_number}: {' '.join(command)}", flush=True)

        # Stream stdout and stderr together so the console shows the live pip
        # progress while the final dialog can still include the same details.
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if process.stdout is not None:
            for output_line in process.stdout:
                print(output_line, end="", flush=True)
                attempt_chunks.append(output_line)
        else:
            pass

        return_code = process.wait()
        output_chunks.append("".join(attempt_chunks))

        if return_code == 0:
            return return_code, "\n\n".join(output_chunks), attempt_number
        else:
            if attempt_number < max_attempts:
                time.sleep(1.0)
            else:
                pass

    return return_code, "\n\n".join(output_chunks), attempt_number


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
        self.ui.updateLabel.setText(sys.executable)

        # self.ui.mainLabel.setText(about_msg)
        self.ui.copyrightLabel.setText(copyright_msg)
        self.ui.contributorsTextEdit.setPlainText(contributors_msg)
        self.ui.contributorsTextEdit.setReadOnly(True)

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

    def fill_optional_libs(self) -> None:
        """
        Fill the optional libraries table with installed and available package data.

        :return: None.
        """
        rows: List[OptionalLibraryStatus] = list()
        veragrid_latest_version: str | None = find_latest_version(package_name="VeraGrid")
        gslv_installed_version: str = get_installed_package_version(package_name="pygslv")
        pgm_installed_version: str = get_installed_package_version(package_name="power-grid-model")
        pandapower_installed_version: str = get_installed_package_version(package_name="pandapower")
        pypsa_installed_version: str = get_installed_package_version(package_name="pypsa")
        pypowsybl_installed_version: str = get_installed_package_version(package_name="pypowsybl")

        rows.append(OptionalLibraryStatus(
            name="VeraGrid",
            package_name="VeraGrid",
            installed=True,
            installed_version=__VeraGrid_VERSION__,
            latest_version=veragrid_latest_version if veragrid_latest_version is not None else "",
            supported_version=__VeraGridEngine_VERSION__,
            licensed=True,
        ))
        rows.append(OptionalLibraryStatus(
            name="GSLV",
            package_name="pygslv",
            installed=len(gslv_installed_version) > 0,
            installed_version=gslv_installed_version if len(gslv_installed_version) > 0 else GSLV_VERSION,
            latest_version=find_latest_version(package_name="pygslv") or "",
            supported_version=GSLV_RECOMMENDED_VERSION,
            licensed=GSLV_AVAILABLE,
        ))
        rows.append(OptionalLibraryStatus(
            name="power-grid-model",
            package_name="power-grid-model",
            installed=len(pgm_installed_version) > 0 or PGM_AVAILABLE,
            installed_version=pgm_installed_version if len(pgm_installed_version) > 0 else PGM_VERSION,
            latest_version=find_latest_version(package_name="power-grid-model") or "",
            supported_version=PGM_RECOMMENDED_VERSION,
            licensed=PGM_AVAILABLE,
        ))
        rows.append(OptionalLibraryStatus(
            name="pandapower",
            package_name="pandapower",
            installed=len(pandapower_installed_version) > 0,
            installed_version=pandapower_installed_version,
            latest_version=find_latest_version(package_name="pandapower") or "",
            supported_version="",
            licensed=len(pandapower_installed_version) > 0,
        ))
        rows.append(OptionalLibraryStatus(
            name="PyPSA",
            package_name="pypsa",
            installed=len(pypsa_installed_version) > 0,
            installed_version=pypsa_installed_version,
            latest_version=find_latest_version(package_name="pypsa") or "",
            supported_version="",
            licensed=len(pypsa_installed_version) > 0,
        ))
        rows.append(OptionalLibraryStatus(
            name="pypowsybl",
            package_name="pypowsybl",
            installed=len(pypowsybl_installed_version) > 0,
            installed_version=pypowsybl_installed_version,
            latest_version=find_latest_version(package_name="pypowsybl") or "",
            supported_version="",
            licensed=len(pypowsybl_installed_version) > 0,
        ))

        self.ui.librariesTableWidget.setColumnCount(7)
        self.ui.librariesTableWidget.setRowCount(len(rows))
        self.ui.librariesTableWidget.setHorizontalHeaderLabels([
            self.tr("Name"),
            self.tr("Action"),
            self.tr("Installed version"),
            self.tr("Newest version"),
            self.tr("Supported version"),
            self.tr("Licensed"),
        ])

        row_idx: int
        library_status: OptionalLibraryStatus
        installed_text: str
        installed_version: str
        latest_version: str
        licensed_text: str

        for row_idx, library_status in enumerate(rows):
            installed_text = self.tr("True") if library_status.installed else self.tr("False")

            if library_status.installed:
                installed_version = library_status.installed_version
            else:
                installed_version = ""

            if len(library_status.latest_version) > 0:
                latest_version = library_status.latest_version
            else:
                latest_version = self.tr("Unknown")

            licensed_text = self.tr("True") if library_status.licensed else self.tr("False")

            self.ui.librariesTableWidget.setItem(row_idx, 0, make_item(library_status.name))
            self.ui.librariesTableWidget.setCellWidget(
                row_idx,
                1,
                self.create_optional_library_action_button(library_status=library_status),
            )
            self.ui.librariesTableWidget.setItem(row_idx, 2, make_item(installed_version))
            self.ui.librariesTableWidget.setItem(row_idx, 3, make_item(latest_version))
            self.ui.librariesTableWidget.setItem(row_idx, 4, make_item(library_status.supported_version))
            self.ui.librariesTableWidget.setItem(row_idx, 5, make_item(licensed_text))

        self.ui.librariesTableWidget.resizeColumnsToContents()

    def create_optional_library_action_button(self, library_status: OptionalLibraryStatus) -> QtWidgets.QPushButton:
        """
        Create the install or update button for one optional library row.

        :param library_status: Optional library status.
        :return: Configured action button.
        """
        if library_status.installed:
            if can_update_package(
                    installed=library_status.installed,
                    installed_version=library_status.installed_version,
                    latest_version=library_status.latest_version):
                text: str = self.tr("Update")
                enabled: bool = True
            else:
                text = self.tr("Installed")
                enabled = False
        else:
            text = self.tr("Install")
            enabled = True

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(text)
        button.setProperty("package_name", library_status.package_name)
        button.setProperty("latest_version", library_status.latest_version)
        button.setEnabled(enabled)
        button.clicked.connect(self.install_or_update_optional_library)
        return button

    def install_or_update_optional_library(self, checked: bool = False) -> None:
        """
        Install or update the package associated with the clicked optional library row.

        :param checked: Qt button checked state.
        :return: None.
        """
        del checked

        button: QtCore.QObject | None = self.sender()

        if isinstance(button, QtWidgets.QPushButton):
            package_name: str = str(button.property("package_name"))
            latest_version: str = str(button.property("latest_version"))

            if package_name == "VeraGrid":
                command: List[str] = get_upgrade_command(latest_version=latest_version)
            else:
                command = get_package_install_command(package_name=package_name, latest_version=latest_version)

            return_code, command_output, attempts_used = run_upgrade_command(
                command=command,
                max_attempts=3,
            )
            output_excerpt: str = command_output[-4000:] if len(command_output) > 4000 else command_output

            if return_code == 0:
                self.msg(
                    text=self.tr("{name} updated successfully after {attempts} attempt(s)").format(
                        name=package_name,
                        attempts=attempts_used,
                    ),
                    title=self.tr("Information"),
                )
                self.fill_optional_libs()
            else:
                self.msg(
                    text=(
                            self.tr("{name} update failed after {attempts} attempt(s).").format(
                                name=package_name,
                                attempts=attempts_used,
                            )
                            + "\n"
                            + self.tr("Exit code: {code}").format(code=return_code)
                            + "\n\n"
                            + self.tr("Command output:")
                            + "\n"
                            + output_excerpt
                    ),
                    title=self.tr("Warning"),
                )
        else:
            pass

    def fill_libs(self):
        """

        :return:
        """
        self.ui.allLibsTableWidget.setColumnCount(5)
        self.ui.allLibsTableWidget.setHorizontalHeaderLabels([
            self.tr("Package"),
            self.tr("Version"),
            self.tr("License"),
            self.tr("Installation Path"),
            self.tr("Dependencies")
        ])

        pkgs = sorted(get_packages(), key=lambda x: x[0].lower())
        self.ui.allLibsTableWidget.setRowCount(len(pkgs))

        for row, (name, versn, license_, path, deps) in enumerate(pkgs):
            self.ui.allLibsTableWidget.setItem(row, 0, make_item(name))
            self.ui.allLibsTableWidget.setItem(row, 1, make_item(versn))
            self.ui.allLibsTableWidget.setItem(row, 2, make_item(license_))
            self.ui.allLibsTableWidget.setItem(row, 3, make_item(path))
            self.ui.allLibsTableWidget.setItem(row, 4, make_item(deps))

        self.ui.allLibsTableWidget.resizeColumnsToContents()

    def msg(self, text: str, title: str = "Warning"):
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
