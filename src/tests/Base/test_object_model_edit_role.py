import sys

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.object_model import ObjectsModel
from VeraGridEngine.Devices.Injections.generator import Generator
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
