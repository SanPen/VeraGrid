from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PySide6 import QtWidgets

from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI


def collect_config_combo_boxes(prefix: str,
                               struct: Dict[str, Any],
                               combo_boxes: List[Tuple[str, QtWidgets.QComboBox]]) -> None:
    """
    Collect the combo boxes present in the GUI configuration structure.

    :param prefix: Current configuration path prefix.
    :param struct: Configuration structure returned by the main window.
    :param combo_boxes: Output list receiving path and combo-box pairs.
    :return: Nothing.
    """
    for key, value in struct.items():
        path: str
        if len(prefix) == 0:
            path = key
        else:
            path = prefix + "/" + key

        if isinstance(value, dict):
            collect_config_combo_boxes(prefix=path, struct=value, combo_boxes=combo_boxes)
        elif isinstance(value, QtWidgets.QComboBox):
            combo_boxes.append((path, value))
        else:
            pass


def select_last_config_combo_items(combo_boxes: List[Tuple[str, QtWidgets.QComboBox]]) -> Dict[str, Any]:
    """
    Select the last available item in each non-empty combo and remember the runtime value.

    :param combo_boxes: Configuration combo boxes to exercise.
    :return: Mapping of configuration paths to expected runtime values.
    """
    expected_values: Dict[str, Any] = dict()
    for path, combo_box in combo_boxes:
        if combo_box.count() > 0:
            combo_box.setCurrentIndex(combo_box.count() - 1)
            expected_values[path] = combo_box.currentData()
        else:
            pass

    return expected_values


def reset_config_combo_items(combo_boxes: List[Tuple[str, QtWidgets.QComboBox]]) -> None:
    """
    Reset non-empty combo boxes to their first item before applying saved configuration.

    :param combo_boxes: Configuration combo boxes to reset.
    :return: Nothing.
    """
    for _path, combo_box in combo_boxes:
        if combo_box.count() > 0:
            combo_box.setCurrentIndex(0)
        else:
            pass


def assert_config_combo_values(combo_boxes: List[Tuple[str, QtWidgets.QComboBox]],
                               expected_values: Dict[str, Any]) -> None:
    """
    Assert that combo-box runtime values match the values selected before persistence.

    :param combo_boxes: Configuration combo boxes to inspect.
    :param expected_values: Expected runtime values by configuration path.
    :return: Nothing.
    """
    for path, combo_box in combo_boxes:
        expected_value: Any | None = expected_values.get(path, None)
        if expected_value is None:
            pass
        else:
            actual_value: Any = combo_box.currentData()
            assert actual_value == expected_value, f"{path}: {actual_value!r} != {expected_value!r}"


def run_config_combo_round_trip(config_file: Path) -> None:
    """
    Save and restore every combo-box setting exposed by the real main window.

    :param config_file: Temporary JSON file used for the round trip.
    :return: Nothing.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        pass

    window = VeraGridMainGUI()
    window.hide()

    combo_boxes: List[Tuple[str, QtWidgets.QComboBox]] = list()
    collect_config_combo_boxes(prefix="", struct=window.get_config_structure(), combo_boxes=combo_boxes)

    expected_values: Dict[str, Any] = select_last_config_combo_items(combo_boxes=combo_boxes)
    assert len(expected_values) > 0, "No non-empty configuration combo boxes were found"

    with config_file.open("w", encoding="utf-8") as file_pointer:
        json.dump(window.get_gui_config_data(), file_pointer)

    reset_config_combo_items(combo_boxes=combo_boxes)

    with config_file.open("r", encoding="utf-8") as file_pointer:
        saved_data: Dict[str, Any] = json.load(file_pointer)

    window.apply_gui_config(data=saved_data)
    assert_config_combo_values(combo_boxes=combo_boxes, expected_values=expected_values)

    skipped_empty: List[str] = list()
    for path, combo_box in combo_boxes:
        if combo_box.count() == 0:
            skipped_empty.append(path)
        else:
            pass

    print("all config combo round trip: ok")
    print(f"covered: {len(expected_values)}")
    print(f"skipped_empty: {len(skipped_empty)} {skipped_empty}")


def main() -> None:
    """
    Dispatch the combo configuration regression runner.

    :return: Nothing.
    """
    if len(sys.argv) != 2:
        raise ValueError("Usage: combo_model_config_runner.py <config_file>")
    else:
        pass

    run_config_combo_round_trip(config_file=Path(sys.argv[1]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    else:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
