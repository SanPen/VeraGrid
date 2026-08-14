import sys

import pytest
from PySide6 import QtCore
from PySide6 import QtWidgets


@pytest.fixture(scope="session")
def qt_app() -> object:
    """
    Get or create the Qt application used by GUI tests.

    :return: Qt application instance.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        pass

    yield app

    app.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    app.processEvents()


@pytest.fixture(autouse=True)
def cleanup_qt_widgets(qt_app: object) -> object:
    """
    Ensure GUI tests do not leak top-level widgets or deferred deletions across test boundaries.

    :param qt_app: Shared Qt application instance.
    :return: Nothing.
    """
    app: QtWidgets.QApplication = qt_app

    yield

    app.processEvents()

    for widget in list(app.topLevelWidgets()):
        widget.close()
        widget.deleteLater()

    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    app.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    app.processEvents()
