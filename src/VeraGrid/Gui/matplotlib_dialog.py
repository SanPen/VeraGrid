# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List

from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6 import QtCore, QtGui, QtWidgets


class MatplotlibFigureDialog(QtWidgets.QDialog):
    """
    Modeless Qt dialog owning one embedded Matplotlib figure.
    """
    __slots__ = ("_open_dialogs", "_canvas", "_toolbar", "_disposed")

    def __init__(self,
                 open_dialogs: List[QtWidgets.QDialog],
                 figure: Figure,
                 parent: QtWidgets.QWidget | None,
                 title: str) -> None:
        """
        Constructor.

        :param open_dialogs: Owner list keeping modeless dialogs alive.
        :param figure: Figure to display.
        :param parent: Parent widget for the modeless dialog.
        :param title: Window title.
        :return: None.
        """
        QtWidgets.QDialog.__init__(self, parent)
        self._open_dialogs: List[QtWidgets.QDialog] = open_dialogs
        self.setWindowTitle(title)
        self.setWindowFlag(QtCore.Qt.WindowType.Window, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self._canvas: FigureCanvas = FigureCanvas(figure)
        self._toolbar: NavigationToolbar = NavigationToolbar(self._canvas, self)
        plt.close(figure)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)
        self.resize(900, 600)
        self._disposed: bool = False

        self.finished.connect(self.on_dialog_finished)

    def dispose(self) -> None:
        """
        Release Matplotlib resources owned by this dialog.

        :return: None.
        """
        if self._disposed:
            pass
        else:
            self._disposed = True
            self._canvas._draw_pending = False
            self._canvas.figure.clear()
            self._toolbar.close()
            self._canvas.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Cancel pending Matplotlib idle draws before Qt deletes the canvas.

        :param event: Qt close event.
        :return: None.
        """
        self.dispose()
        QtWidgets.QDialog.closeEvent(self, event)

    def on_dialog_finished(self, result: int) -> None:
        """
        Drop the owner reference after Qt has closed the dialog.

        :param result: Qt dialog result.
        :return: None.
        """
        if self in self._open_dialogs:
            self._open_dialogs.remove(self)
        else:
            pass


def show_matplotlib_figure(figure: Figure,
                           parent: QtWidgets.QWidget | None,
                           open_dialogs: List[QtWidgets.QDialog],
                           title: str) -> MatplotlibFigureDialog:
    """
    Show a Matplotlib figure through Qt without starting another GUI loop.

    :param figure: Figure to display.
    :param parent: Parent widget for the modeless dialog.
    :param open_dialogs: Owner list retaining modeless dialogs.
    :param title: Window title.
    :return: Created dialog.
    """
    dialog: MatplotlibFigureDialog = MatplotlibFigureDialog(open_dialogs=open_dialogs,
                                                            figure=figure,
                                                            parent=parent,
                                                            title=title)
    open_dialogs.append(dialog)
    dialog.show()
    return dialog
