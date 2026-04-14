# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

__all__: list[str] = list()
__all__.append("AiChatDialogue")


def __getattr__(name: str):
    """
    Lazily expose the AI dialogue without importing the GUI stack at package import time.

    :param name: Requested attribute name.
    :returns: Exported object.
    """
    if name == "AiChatDialogue":
        from VeraGrid.Gui.AiAgent.ai_chat_dialogue import AiChatDialogue

        return AiChatDialogue
    else:
        raise AttributeError(name)
