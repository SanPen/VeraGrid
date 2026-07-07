from typing import List

from VeraGrid.Gui.Main.object_select_window import ListSelectWindow, ObjectSelectWindow


class NamedObject:
    """
    Minimal named object used by object-selection dialog tests.
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """
        Build the named object.

        :param name: Name exposed to the GUI list.
        :return: Nothing.
        """
        self.name: str = name

    def __str__(self) -> str:
        """
        Get the user-facing object name.

        :return: Object name.
        """
        return self.name


def build_named_objects() -> List[NamedObject]:
    """
    Build a deterministic object list for selection-window tests.

    :return: Named objects.
    """
    objects: List[NamedObject] = list()
    objects.append(NamedObject(name="Alpha"))
    objects.append(NamedObject(name="Beta"))
    objects.append(NamedObject(name="Gamma"))
    return objects


def test_object_select_window_populates_rows_from_object_names(qt_app: object) -> None:
    """
    Check that object-selection dialogs expose object names in list order.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    objects: List[NamedObject] = build_named_objects()
    window: ObjectSelectWindow = ObjectSelectWindow(title="Select object", object_list=objects)

    assert window.windowTitle() == "Select object"
    assert window.list_widget.count() == len(objects)
    assert window.list_widget.item(0).text() == "Alpha"
    assert window.list_widget.item(1).text() == "Beta"
    assert window.list_widget.item(2).text() == "Gamma"
    assert window.selected_object is None

    window.close()
    window.deleteLater()


def test_object_select_window_double_click_selects_current_object(qt_app: object) -> None:
    """
    Check that double-click handling stores the selected object pointer.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    objects: List[NamedObject] = build_named_objects()
    window: ObjectSelectWindow = ObjectSelectWindow(title="Select object", object_list=objects)

    window.list_widget.setCurrentRow(1)
    window.dbl_clicked(qmodelindex=window.list_widget.currentIndex())

    assert window.selected_object is objects[1]

    window.close()
    window.deleteLater()


def test_list_select_window_double_click_selects_current_element(qt_app: object) -> None:
    """
    Check that list-selection dialogs store the selected list element.

    :param qt_app: Shared Qt application fixture.
    :return: Nothing.
    """
    del qt_app

    elements: List[str] = list()
    elements.append("Voltage")
    elements.append("Current")
    elements.append("Power")
    window: ListSelectWindow = ListSelectWindow(title="Select value", elements=elements)

    window.list_widget.setCurrentRow(2)
    window.dbl_clicked(qmodelindex=window.list_widget.currentIndex())

    assert window.windowTitle() == "Select value"
    assert window.list_widget.count() == len(elements)
    assert window.selected_object == "Power"

    window.close()
    window.deleteLater()
