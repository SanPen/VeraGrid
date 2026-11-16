# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Shared parsing helpers for Sienna device objects."""

from typing import Any


def get_required_value(data: dict[str, Any], key: str, component_type: str) -> Any:
    """Read one required device value with an explicit diagnostic.

    :param data: Raw JSON device object.
    :param key: Required property name.
    :param component_type: Sienna type used in the diagnostic.
    :return: Raw property value.
    :raises ValueError: When the required property is absent.
    """
    value: Any | None = data.get(key, None)
    if value is None:
        raise ValueError(f"{component_type} is missing required property '{key}'")
    else:
        return value
