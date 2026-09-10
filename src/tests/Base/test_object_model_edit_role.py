import sys

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.object_model import ObjectsModel
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import GeneratorControlMode


def _get_app():
    app = QtWidgets.QApplication.instance()
    if app is not None:
        return app

    return QtWidgets.QApplication(sys.argv)


def test_object_model_returns_typed_enum_for_edit_role():
    _get_app()
    view = QtWidgets.QTableView()
    generator = Generator()
    prop = generator.registered_properties["control_mode"]
    model = ObjectsModel(objects=[generator],
                         property_list=[prop],
                         time_index=None,
                         parent=view,
                         editable=True)

    index = model.index(0, 0)

    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == str(GeneratorControlMode.V)
    assert model.data(index, QtCore.Qt.ItemDataRole.EditRole) is GeneratorControlMode.V


def test_object_model_returns_hosted_device_for_raw_bus_cell() -> None:
    """
    Check that device-reference cells expose the raw hosted device.

    :return: None.
    """
    _get_app()
    view: QtWidgets.QTableView = QtWidgets.QTableView()
    bus: Bus = Bus(name="Bus A")
    generator: Generator = Generator()
    generator.bus = bus
    prop: GCProp = generator.registered_properties["bus"]
    model: ObjectsModel = ObjectsModel(objects=[generator],
                                       property_list=[prop],
                                       time_index=None,
                                       parent=view,
                                       editable=True)

    index: QtCore.QModelIndex = model.index(0, 0)

    assert model.data(index, QtCore.Qt.ItemDataRole.DisplayRole) == "Bus A"
    assert model.get_value_at_index(index=index) is bus
    assert model.get_hosted_device_at_index(index=index) is bus
