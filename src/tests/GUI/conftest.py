import os
import sys

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure Qt before GUI test modules import PySide.

    :param config: Pytest configuration object.
    :return: Nothing.
    """
    del config

    if "QT_QPA_PLATFORM" in os.environ:
        pass
    else:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session")
def qt_app() -> object:
    """
    Get or create the Qt application used by GUI tests.

    :return: Qt application instance.
    """
    from PySide6 import QtWidgets

    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app
