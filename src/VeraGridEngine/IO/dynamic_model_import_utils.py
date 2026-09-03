# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


def sanitize_dynamic_model_file_stem(text: str) -> str:
    """Convert one dynamic-model display name into a filesystem-safe stem.

    :param text: Source display name.
    :return: Filesystem-safe stem.
    """
    safe_characters: list[str] = list()
    character: str

    for character in text:
        if character.isalnum() or character in {"_", "-"}:
            safe_characters.append(character)
        else:
            safe_characters.append("_")

    return "".join(safe_characters).strip("_")
