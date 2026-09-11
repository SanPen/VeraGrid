import numpy as np
import pandas as pd
from PySide6 import QtWidgets

from VeraGrid.Gui.profiles_model import ProfilesModel
from VeraGridEngine.enumerations import DeviceType


class FakeRegisteredProperty:
    """
    Minimal registered-property object for profile clipboard tests.
    """

    __slots__ = ("tpe",)

    def __init__(self, tpe: type) -> None:
        """
        Store the value parser type.

        :param tpe: Python type used by paste parsing.
        :return: None.
        """
        self.tpe: type = tpe


class FakeProfile:
    """
    Minimal profile object exposing the profile API used by ``ProfilesModel``.
    """

    __slots__ = ("_values",)

    def __init__(self, values: list[float]) -> None:
        """
        Store one profile array.

        :param values: Initial profile values.
        :return: None.
        """
        self._values: np.ndarray = np.array(values, dtype=float)

    def toarray(self) -> np.ndarray:
        """
        Return the profile values as an array.

        :return: Profile array copy.
        """
        return self._values.copy()

    def set(self, arr: np.ndarray) -> bool:
        """
        Replace the profile values.

        :param arr: New profile values.
        :return: ``True``.
        """
        self._values = np.array(arr, dtype=float)
        return True


class FakeElement:
    """
    Minimal editable element exposing profile lookup.
    """

    __slots__ = ("name", "registered_properties", "_profile")

    def __init__(self, name: str, values: list[float]) -> None:
        """
        Store the element name and profile.

        :param name: Element name.
        :param values: Profile values.
        :return: None.
        """
        self.name: str = name
        self.registered_properties: dict[str, FakeRegisteredProperty] = {
            "P": FakeRegisteredProperty(float)
        }
        self._profile: FakeProfile = FakeProfile(values=values)

    def get_profile(self, magnitude: str) -> FakeProfile:
        """
        Return the profile for the requested magnitude.

        :param magnitude: Profile magnitude.
        :return: Stored fake profile.
        """
        del magnitude
        return self._profile


def build_profiles_model(table: QtWidgets.QTableView) -> ProfilesModel:
    """
    Build a small profiles model for clipboard tests.

    :param table: Parent table view.
    :return: Configured profiles model.
    """
    time_array: pd.DatetimeIndex = pd.date_range("2026-01-01 00:00:00", periods=3, freq="h")
    elements: list[FakeElement] = [
        FakeElement(name="A", values=[1.0, 2.0, 3.0]),
        FakeElement(name="B", values=[4.0, 5.0, 6.0]),
    ]

    return ProfilesModel(time_array=time_array,
                         elements=elements,
                         device_type=DeviceType.LoadDevice,
                         magnitude="P",
                         data_format=float,
                         dictionary_of_lists=None,
                         parent=table)


def test_profiles_copy_full_table_includes_headers_and_index(qt_app: object) -> None:
    """
    Check full-table profile copy includes headers and time index.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    table: QtWidgets.QTableView = QtWidgets.QTableView()
    model: ProfilesModel = build_profiles_model(table=table)

    assert model.copy_to_clipboard()

    text: str = QtWidgets.QApplication.clipboard().text()
    assert text.startswith("\tA\tB\n")
    assert "2026-01-01 00:00:00\t1.0\t4.0\n" in text

    table.close()
    table.deleteLater()


def test_profiles_copy_selection_excludes_headers_and_index(qt_app: object) -> None:
    """
    Check selected profile copy emits only selected data cells.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    table: QtWidgets.QTableView = QtWidgets.QTableView()
    model: ProfilesModel = build_profiles_model(table=table)

    assert model.copy_to_clipboard(cols=[1], rows=[1, 2], include_headers=False)

    text: str = QtWidgets.QApplication.clipboard().text()
    assert text == "5.0\n6.0\n"

    table.close()
    table.deleteLater()


def test_profiles_paste_single_value_fills_selection(qt_app: object) -> None:
    """
    Check a one-cell clipboard value is repeated into a larger selected range.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    table: QtWidgets.QTableView = QtWidgets.QTableView()
    model: ProfilesModel = build_profiles_model(table=table)

    QtWidgets.QApplication.clipboard().setText("9.5")
    model.paste_from_clipboard(row_idx=0,
                               col_idx=0,
                               selected_rows=[0, 1],
                               selected_cols=[0, 1])

    assert np.array_equal(model.elements[0].get_profile("P").toarray(), np.array([9.5, 9.5, 3.0]))
    assert np.array_equal(model.elements[1].get_profile("P").toarray(), np.array([9.5, 9.5, 6.0]))

    table.close()
    table.deleteLater()
