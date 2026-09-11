from __future__ import annotations

import shiboken6
from PySide6 import QtCore
from PySide6 import QtWidgets

from VeraGrid.Gui.toast_widget import ToastManager
from VeraGrid.Gui.toast_widget import ToastWidget


def test_toast_manager_ignores_deleted_toast_wrappers(qt_app: object) -> None:
    """
    Check that stale PySide wrappers do not crash the next toast geometry pass.

    :param qt_app: Shared Qt application.
    :return: None.
    """
    app: QtWidgets.QApplication = qt_app
    parent: QtWidgets.QWidget = QtWidgets.QWidget()
    manager: ToastManager = ToastManager(parent=parent)
    parent.resize(300, 200)
    parent.show()
    app.processEvents()

    manager.show_warning_toast(message="first", duration=1)
    first_toast: ToastWidget = manager.active_toasts[0]
    first_toast.close()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()

    manager.active_toasts.append(first_toast)
    assert not shiboken6.isValid(first_toast)

    manager.show_warning_toast(message="second", duration=1)

    toast: ToastWidget
    for toast in manager.active_toasts:
        assert shiboken6.isValid(toast)

    parent.close()
    parent.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()
