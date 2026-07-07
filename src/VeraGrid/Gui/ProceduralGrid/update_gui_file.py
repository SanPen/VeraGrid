# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""
Script to update correctly the main GUI (.py) file from the Qt design (.ui) file
"""
from VeraGrid.Gui.update_gui_common import convert_ui_file

if __name__ == '__main__':

    for f in ['procedural_grid_ui.ui', 'map_warning_ui.ui']:
        convert_ui_file(source=f)