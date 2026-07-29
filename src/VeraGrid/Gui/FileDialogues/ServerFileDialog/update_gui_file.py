# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Script to update correctly the server file dialogue (.py) file from the Qt design (.ui) file.
"""
import os

from VeraGrid.Gui.update_gui_common import convert_ui_file


if __name__ == '__main__':
    uic_cmd: str = 'pyside6-uic'

    if os.name == 'nt':
        uic_cmd += '.exe'
    else:
        pass

    convert_ui_file(source='server_file_dialogue.ui', uic_cmd=uic_cmd)
