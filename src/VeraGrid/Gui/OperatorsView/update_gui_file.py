# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Regenerate the Operator View UI module from its Qt Designer source."""

from VeraGrid.Gui.update_gui_common import convert_ui_file


if __name__ == '__main__':
    # Keep the generated view separate from the future window controller.
    convert_ui_file(source='operator_view.ui', target_file_name='operator_view_ui.py')
