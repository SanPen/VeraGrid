from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.Main.SubClasses.Model.data_base import DataBaseTableMain
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def _find_device_type_index(model: QtCore.QAbstractItemModel,
                            parent: QtCore.QModelIndex,
                            device_type: DeviceType) -> QtCore.QModelIndex:
    """
    Locate one device leaf in the database tree.

    :param model: Tree model to inspect.
    :param parent: Parent index whose children are searched.
    :param device_type: Stable enum payload to find.
    :return: Matching model index or an invalid index when absent.
    """
    row: int
    for row in range(model.rowCount(parent)):
        index: QtCore.QModelIndex = model.index(row, 0, parent)
        payload: object = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if payload == device_type:
            return index
        else:
            child_index: QtCore.QModelIndex = _find_device_type_index(
                model=model,
                parent=index,
                device_type=device_type,
            )
            if child_index.isValid():
                return child_index
            else:
                pass
    return QtCore.QModelIndex()


def test_database_add_action_creates_dc_cable_type(qt_app: object) -> None:
    """
    Exercise the real GUI add action for the DC cable catalogue.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    _application: object = qt_app
    gui: DataBaseTableMain = DataBaseTableMain()
    gui.hide()

    try:
        gui.circuit = MultiCircuit()
        gui.setup_objects_tree()
        tree_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructuresTreeView.model()
        assert tree_model is not None
        cable_index: QtCore.QModelIndex = _find_device_type_index(
            model=tree_model,
            parent=QtCore.QModelIndex(),
            device_type=DeviceType.DcCableTypeDevice,
        )
        assert cable_index.isValid()

        selection_model: QtCore.QItemSelectionModel | None = gui.ui.dataStructuresTreeView.selectionModel()
        assert selection_model is not None
        selection_model.select(
            cable_index,
            QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QtCore.QItemSelectionModel.SelectionFlag.Rows,
        )
        gui.ui.dataStructuresTreeView.setCurrentIndex(cable_index)
        gui.view_objects_data()
        gui.add_objects()
        QtWidgets.QApplication.processEvents()

        table_model: QtCore.QAbstractItemModel | None = gui.ui.dataStructureTableView.model()
        assert len(gui.circuit.dc_cable_types) == 1
        assert gui.circuit.dc_cable_types[0].name == 'DC cable 1'
        assert table_model is not None
        assert table_model.rowCount() == 1
    finally:
        gui.close()
        gui.deleteLater()
        QtWidgets.QApplication.processEvents()
