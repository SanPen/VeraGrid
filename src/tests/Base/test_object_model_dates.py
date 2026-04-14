import sys

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.object_model import ObjectsModel
from VeraGridEngine.Devices.Parents.editable_device import GCProp


class DummyDevice:
    def __init__(self, values):
        self.values = values

    def get_value(self, prop, t_idx=None):
        return self.values[prop.name]


def _get_app():
    if QtWidgets.QApplication.instance():
        return QtWidgets.QApplication.instance()

    return QtWidgets.QApplication(sys.argv)


def _build_model(value):
    _get_app()
    view = QtWidgets.QTableView()
    prop = GCProp(key="timestamp", tpe=int, is_date=True)
    device = DummyDevice({"timestamp": value})

    return ObjectsModel(objects=[device],
                        property_list=[prop],
                        time_index=None,
                        parent=view,
                        editable=False)


def test_object_model_formats_integer_epoch_dates():
    model = _build_model(1_700_000_000)
    index = model.index(0, 0)

    expected = QtCore.QDateTime.fromSecsSinceEpoch(1_700_000_000).toString("yyyy/MM/dd")

    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == expected


def test_object_model_rejects_non_integral_float_dates():
    model = _build_model(123.5)
    index = model.index(0, 0)

    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == "123.5"


def test_object_model_accepts_integral_float_dates():
    model = _build_model(86_400.0)
    index = model.index(0, 0)

    expected = QtCore.QDateTime.fromSecsSinceEpoch(86_400).toString("yyyy/MM/dd")

    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == expected
