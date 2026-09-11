from datetime import datetime

import pandas as pd
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.FileDialogues.ProfilesInput.models_dialogue import GridsModel, GridsModelTimeDelegate
from VeraGrid.Gui.FileDialogues.ProfilesInput.profiles_from_models_gui import Ui_Dialog
from VeraGridEngine.basic_structures import Logger


def test_generated_models_import_ui_exposes_re_index_button(qt_app: object) -> None:
    """
    Check that the generated models-import UI exposes the re-index button.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    window: QtWidgets.QDialog = QtWidgets.QDialog()
    ui: Ui_Dialog = Ui_Dialog()
    ui.setupUi(window)

    assert ui.reIndexTimeButton.text() == "Re-index time"

    window.close()
    window.deleteLater()


def test_grids_model_manual_time_edit_and_re_index(qt_app: object) -> None:
    """
    Check that manual time edits and automatic time re-indexing update the model values.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    model: GridsModel = GridsModel(logger=Logger())
    model.add_path(path="/tmp/model_a.raw")
    model.add_path(path="/tmp/model_b.raw")

    edited: bool = model.setData(index=model.index(0, 0), value="2026-02-03 04:05:00")
    assert edited
    assert model.items()[0].time == pd.Timestamp("2026-02-03 04:05:00")

    path_edited: bool = model.setData(index=model.index(0, 2), value="/tmp/renamed_model.raw")
    assert path_edited
    assert model.items()[0].path == "/tmp/renamed_model.raw"
    assert model.items()[0].name == "renamed_model.raw"
    assert not model.flags(model.index(0, 2)) & QtCore.Qt.ItemFlag.ItemIsEditable

    model.re_index_time(t0=datetime(2026, 1, 1, 0, 0, 45), step_size=30.0, step_unit="m")
    assert model.items()[0].time == pd.Timestamp("2026-01-01 00:00:00")
    assert model.items()[1].time == pd.Timestamp("2026-01-01 00:30:00")


def test_grids_model_time_delegate_loads_existing_timestamp(qt_app: object) -> None:
    """
    Check that the time-column delegate opens with the already stored row timestamp.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    model: GridsModel = GridsModel(logger=Logger())
    model.add_path(path="/tmp/model_a.raw")
    model.setData(index=model.index(0, 0), value="2026-02-03 04:05:06")

    table: QtWidgets.QTableView = QtWidgets.QTableView()
    delegate: GridsModelTimeDelegate = GridsModelTimeDelegate(table)
    editor: QtWidgets.QDateTimeEdit = delegate.createEditor(parent=table,
                                                            option=QtWidgets.QStyleOptionViewItem(),
                                                            index=model.index(0, 0))
    delegate.setEditorData(editor=editor, index=model.index(0, 0))

    assert editor.dateTime().toPython() == datetime(2026, 2, 3, 4, 5, 6)

    table.close()
    table.deleteLater()
