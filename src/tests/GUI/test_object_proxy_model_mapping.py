import sys
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.object_model import ObjectsModel
from VeraGrid.Gui.object_column_filter_dialog import ObjectColumnFilterDialog, set_line_edit_clear_action
from VeraGrid.Gui.object_proxy_model import ObjectModelFilterProxy
from VeraGrid.Gui.table_view_header_wrap import HeaderViewWithWordWrap
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Parents.editable_device import GCProp


def get_qt_app() -> QtWidgets.QApplication:
    """
    Return the current Qt application or create one for the test process.

    :return: Qt application instance.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def test_proxy_helpers_map_sorted_rows_to_source_objects() -> None:
    """
    Check that sorted proxy rows expose and edit the matching source object.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    zulu: Bus = Bus(name="Zulu")
    alpha: Bus = Bus(name="Alpha")
    objects: List[Bus] = [zulu, alpha]
    properties: List[GCProp] = [zulu.registered_properties["name"]]

    source_model: ObjectsModel = ObjectsModel(
        objects=objects,
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)

    proxy_model.sort(0, QtCore.Qt.SortOrder.AscendingOrder)

    assert proxy_model.has_column_sort(source_column=0) is True
    assert proxy_model.get_column_sort_order(source_column=0) == QtCore.Qt.SortOrder.AscendingOrder
    assert proxy_model.get_objects_in_db_order() == [zulu, alpha]
    assert proxy_model.get_objects_in_display_order() == [alpha, zulu]
    assert proxy_model.get_source_row_from_proxy_row(proxy_row=0) == 1
    assert proxy_model.get_object_at_proxy_row(proxy_row=0) is alpha
    assert proxy_model.get_objects_at_proxy_rows(proxy_rows=[0]) == [alpha]

    changed: bool = proxy_model.setData(
        proxy_model.index(0, 0),
        "Beta",
        QtCore.Qt.ItemDataRole.EditRole,
    )

    assert changed is True
    assert zulu.name == "Zulu"
    assert alpha.name == "Beta"


def test_proxy_exact_column_filter_preserves_edit_mapping() -> None:
    """
    Check that exact column filters expose and edit the matching source object.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    zulu: Bus = Bus(name="Zulu")
    alpha: Bus = Bus(name="Alpha")
    omega: Bus = Bus(name="Omega")
    objects: List[Bus] = [zulu, alpha, omega]
    properties: List[GCProp] = [zulu.registered_properties["name"]]

    source_model: ObjectsModel = ObjectsModel(
        objects=objects,
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)

    assert proxy_model.get_column_filter_values(source_column=0) == ["Alpha", "Omega", "Zulu"]

    proxy_model.set_column_filter(source_column=0, accepted_values={"Alpha", "Omega"})
    proxy_model.sort(0, QtCore.Qt.SortOrder.DescendingOrder)

    assert proxy_model.has_column_sort(source_column=0) is True
    assert proxy_model.rowCount() == 2
    assert proxy_model.get_objects_in_display_order() == [omega, alpha]
    assert proxy_model.get_object_at_proxy_row(proxy_row=0) is omega

    changed: bool = proxy_model.setData(
        proxy_model.index(0, 0),
        "Gamma",
        QtCore.Qt.ItemDataRole.EditRole,
    )

    assert changed is True
    assert zulu.name == "Zulu"
    assert alpha.name == "Alpha"
    assert omega.name == "Gamma"

    proxy_model.clear_column_filter(source_column=0)

    assert proxy_model.rowCount() == 3
    assert proxy_model.has_column_filter(source_column=0) is False
    assert proxy_model.has_column_sort(source_column=0) is False
    assert proxy_model.get_objects_in_display_order() == [zulu, alpha, omega]

    proxy_model.set_column_filter(source_column=0, accepted_values={"Alpha", "Gamma", "Zulu"})

    assert proxy_model.rowCount() == 3
    assert proxy_model.has_column_filter(source_column=0) is False


def test_column_filter_dialog_uses_icon_only_buttons() -> None:
    """
    Check that the filter popup builds with icon-only action buttons.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    bus: Bus = Bus(name="Alpha")
    properties: List[GCProp] = [bus.registered_properties["name"]]
    source_model: ObjectsModel = ObjectsModel(
        objects=[bus],
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)

    dialog: ObjectColumnFilterDialog = ObjectColumnFilterDialog(
        proxy_model=proxy_model,
        source_column=0,
        table_view=view,
        parent=view,
    )
    buttons: List[QtWidgets.QToolButton] = dialog.findChildren(QtWidgets.QToolButton)

    assert dialog.values_list_widget.count() == 1
    assert len(buttons) > 0
    for button in buttons:
        assert button.text() == ""
        assert button.icon().isNull() is False


def test_line_edit_clear_action_uses_filter_popup_icon() -> None:
    """
    Check that line edits use the same clear icon as the filter popup.
    """
    get_qt_app()

    line_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
    action: QtGui.QAction = set_line_edit_clear_action(line_edit=line_edit)
    same_action: QtGui.QAction = set_line_edit_clear_action(line_edit=line_edit)

    assert action.isVisible() is False

    line_edit.setText("abc")

    assert action.isVisible() is True

    action.trigger()

    assert action is same_action
    assert action.objectName() == "veragrid_clear_line_edit_action"
    assert action.data() == ":/Icons/icons/line_edit_clear_gray.png"
    assert action.icon().isNull() is False
    assert action.isVisible() is False
    assert line_edit.text() == ""


def test_column_filter_dialog_cancel_clears_filter() -> None:
    """
    Check that the cancel/X action removes the active column filter.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    zulu: Bus = Bus(name="Zulu")
    alpha: Bus = Bus(name="Alpha")
    properties: List[GCProp] = [zulu.registered_properties["name"]]
    source_model: ObjectsModel = ObjectsModel(
        objects=[zulu, alpha],
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)
    proxy_model.set_column_filter(source_column=0, accepted_values={"Alpha"})
    proxy_model.sort(0, QtCore.Qt.SortOrder.AscendingOrder)

    dialog: ObjectColumnFilterDialog = ObjectColumnFilterDialog(
        proxy_model=proxy_model,
        source_column=0,
        table_view=view,
        parent=view,
    )
    buttons: List[QtWidgets.QToolButton] = dialog.findChildren(QtWidgets.QToolButton)
    cancel_button: QtWidgets.QToolButton | None = None
    button: QtWidgets.QToolButton
    for button in buttons:
        if button.toolTip() == dialog.tr("Cancel filter"):
            cancel_button = button
        else:
            pass

    assert proxy_model.has_column_filter(source_column=0) is True
    assert proxy_model.has_column_sort(source_column=0) is True
    assert cancel_button is not None

    cancel_button.click()

    assert proxy_model.has_column_filter(source_column=0) is False
    assert proxy_model.has_column_sort(source_column=0) is False
    assert proxy_model.rowCount() == 2


def test_filtered_column_header_paints_filter_indicator() -> None:
    """
    Check that filtered object columns paint the active filter icon.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    view.setHorizontalHeader(HeaderViewWithWordWrap(view))
    zulu: Bus = Bus(name="Zulu")
    alpha: Bus = Bus(name="Alpha")
    properties: List[GCProp] = [zulu.registered_properties["name"]]
    source_model: ObjectsModel = ObjectsModel(
        objects=[zulu, alpha],
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)
    view.resize(240, 120)
    view.show()
    QtWidgets.QApplication.processEvents()

    proxy_model.set_column_filter(source_column=0, accepted_values={"Alpha"})
    view.horizontalHeader().viewport().update()
    QtWidgets.QApplication.processEvents()

    header_image: QtGui.QImage = view.horizontalHeader().grab().toImage()
    found_indicator_pixel: bool = False
    x_index: int
    y_index: int
    for y_index in range(header_image.height()):
        for x_index in range(header_image.width()):
            color: QtGui.QColor = QtGui.QColor(header_image.pixel(x_index, y_index))
            if color.blue() > 160 and color.red() < 120:
                found_indicator_pixel = True
            else:
                pass

    assert found_indicator_pixel is True


def test_sorted_column_header_has_sort_indicator() -> None:
    """
    Check that sorted object columns expose a header indicator like filters.
    """
    get_qt_app()

    view: QtWidgets.QTableView = QtWidgets.QTableView()
    header: HeaderViewWithWordWrap = HeaderViewWithWordWrap(view)
    view.setHorizontalHeader(header)
    zulu: Bus = Bus(name="Zulu")
    alpha: Bus = Bus(name="Alpha")
    properties: List[GCProp] = [zulu.registered_properties["name"]]
    source_model: ObjectsModel = ObjectsModel(
        objects=[zulu, alpha],
        property_list=properties,
        time_index=None,
        parent=view,
        editable=True,
    )
    proxy_model: ObjectModelFilterProxy = ObjectModelFilterProxy(mdl=source_model)
    view.setModel(proxy_model)

    proxy_model.sort(0, QtCore.Qt.SortOrder.AscendingOrder)

    assert header._header_state_icon_path(logicalIndex=0) == ":/Icons/icons/up.png"

    proxy_model.sort(0, QtCore.Qt.SortOrder.DescendingOrder)

    assert header._header_state_icon_path(logicalIndex=0) == ":/Icons/icons/down.png"
