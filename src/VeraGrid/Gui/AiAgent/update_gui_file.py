# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Script to update correctly the AI agent GUI (.py) file from the Qt design (.ui) file.
"""

from VeraGrid.Gui.update_gui_common import convert_ui_file


if __name__ == "__main__":
    sources: list[str] = list()
    sources.append("ai_chat_gui.ui")

    for source in sources:
        convert_ui_file(source=source)
else:
    pass
