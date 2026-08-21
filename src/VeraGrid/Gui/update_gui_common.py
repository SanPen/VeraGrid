# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Script to update correctly the main GUI (.py) file from the Qt design (.ui) file
"""
import os
import sys
import xml.etree.ElementTree as ET
from subprocess import call
from typing import List, Tuple


def get_ui_declared_shortcuts(source: str) -> List[Tuple[str, str]]:
    """
    Read the shortcut declarations stored in one Qt Designer ``.ui`` file.

    The build-time validation works on the source XML because the Windows
    AltGr collision is already encoded once the shortcut text is declared in
    the file. There is no need to construct a Qt widget tree to detect it.

    :param source: UI file path.
    :return: List of ``(action_name, shortcut_text)`` tuples.
    """
    ui_root: ET.Element = ET.parse(source).getroot()
    shortcut_entries: List[Tuple[str, str]] = list()
    action_element: ET.Element

    for action_element in ui_root.findall(".//action"):
        action_name: str = str(action_element.get("name", "")).strip()
        shortcut_text: str = ""
        property_element: ET.Element

        # The ``shortcut`` property is the declarative source of truth for Qt
        # action accelerators exported by Designer.
        for property_element in action_element.findall("property"):
            if property_element.get("name") == "shortcut":
                shortcut_text = "".join(property_element.itertext()).strip()
                break
            else:
                pass

        if len(action_name) > 0 and len(shortcut_text) > 0:
            shortcut_entries.append((action_name, shortcut_text))
        else:
            pass

    return shortcut_entries


def validate_ui_shortcuts_do_not_use_ctrl_alt_prefix(source: str) -> None:
    """
    Reject ``.ui`` files that declare shortcuts starting with ``Ctrl+Alt+``.

    On Windows many keyboard layouts report AltGr as Ctrl+Alt. A GUI shortcut
    beginning with that prefix can therefore steal text entry from child input
    widgets such as ``QLineEdit`` and make layout-specific characters like
    ``]`` impossible to type. The fix is not in the widget code: remove the
    ``Ctrl+Alt`` shortcut from the UI and replace it with a non-conflicting
    sequence.

    :param source: UI file path.
    :return: None.
    :raises ValueError: If the UI declares one or more conflicting shortcuts.
    """
    conflicting_shortcuts: List[str] = list()
    action_name: str
    shortcut_text: str

    for action_name, shortcut_text in get_ui_declared_shortcuts(source=source):
        if shortcut_text.startswith("Ctrl+Alt+"):
            conflicting_shortcuts.append(f"{action_name}: {shortcut_text}")
        else:
            pass

    if len(conflicting_shortcuts) == 0:
        return
    else:
        pass

    raise ValueError(
        "Refusing to convert UI file because it declares shortcut sequences starting with 'Ctrl+Alt+'. "
        "On Windows many keyboard layouts report AltGr as Ctrl+Alt, so these shortcuts collide with text "
        "entry in child widgets such as QLineEdit and can make characters like ']' impossible to type. "
        "The matter is the shortcut declaration itself, not the editor widget. "
        "The fix is to remove the Ctrl+Alt shortcut and replace it with a non-conflicting sequence. "
        f"File: {source}. Conflicting shortcuts: {', '.join(conflicting_shortcuts)}"
    )


def correct_file_imports(filename):
    """
    Correct file with qtpy agnostic imports
    :param filename: file name
    :return: Nothing
    """
    with open(filename, 'r') as file:
        file_data = file.read()

    # Replace the target string
    file_data = file_data.replace('import icons_rc', 'from VeraGrid.Gui.Icons.icons_rc import *')
    file_data = file_data.replace('from .matplotlibwidget import MatplotlibWidget', 'from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget')
    file_data = file_data.replace('from matplotlibwidget import MatplotlibWidget', 'from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget')
    file_data = file_data.replace('from qrangeslider3 import QRangeSlider3', 'from VeraGrid.Gui.Widgets.custom_qrangeslider import QRangeSlider3')
    # file_data = file_data.replace('PySide6', 'qtpy')
    # file_data = file_data.replace('PyQt5', 'qtpy')
    # file_data = file_data.replace('PyQt6', 'qtpy')

    # Write the file out again
    with open(filename, 'w') as file:
        file.write(file_data)


def convert_resource_file(source, rcc_cmd='pyside6-rcc'):

    folder = os.path.dirname(sys.executable)
    f1 = folder.split(os.sep)[-1]

    if f1 == 'bin':
        fbase = folder
    else:
        if 'script' in folder.lower():
            fbase = folder
        else:
            fbase = os.path.join(folder, 'Script')

    # get the target fil name
    target = source.replace('.qrc', '_rc.py')

    # define the possible commands
    possible_cmds = [os.path.join(fbase, rcc_cmd),
                     os.path.join(fbase, rcc_cmd + '.exe'),
                     rcc_cmd]

    for cmd in possible_cmds:

        try:
            call([sys.executable, os.path.join(fbase, cmd), source, '-o', target])
            correct_file_imports(target)
            print(rcc_cmd, ' (py) ok')
            return True
        except:
            print('Failed with', rcc_cmd)


def convert_ui_file(source, uic_cmd='pyside6-uic'):
    """
    Convert UI file to .py with qtpy agnostic imports
    :param source:
    :param uic_cmd:
    :return:
    """
    print(f"Converting {source}...")
    validate_ui_shortcuts_do_not_use_ctrl_alt_prefix(source=source)
    folder = os.path.dirname(sys.executable)
    f1 = folder.split(os.sep)[-1]

    if f1 == 'bin':
        fbase = folder
    else:
        if 'script' in folder.lower():
            fbase = folder
        else:
            fbase = os.path.join(folder, 'Script')

    # get the target fil name
    target = source.replace('.ui', '.py')

    # define the possible commands
    possible_cmds = [os.path.join(fbase, uic_cmd),
                     os.path.join(fbase, uic_cmd + '.exe'),
                     uic_cmd]

    for cmd in possible_cmds:

        try:
            call([cmd, source, '-o', target])
            correct_file_imports(filename=target)
            print(uic_cmd, ' (py) ok')
            return True

        except:
            pass

    print('Could not find the right command to convert', source)
    return False
