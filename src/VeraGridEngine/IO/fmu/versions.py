# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import re

from VeraGridEngine.enumerations import FmiVersion


def parse_declared_fmi_version(value: str) -> FmiVersion:
    """Resolve an FMU ``fmiVersion`` declaration to a supported family.

    FMI 1.0.1 and every FMI 2.0.x maintenance specification retain the
    canonical declarations ``1.0`` and ``2.0`` respectively. FMI 3 stable
    patch declarations such as ``3.0.2`` use the FMI 3.0 runtime family.
    Future minor versions and development prereleases remain rejected until
    their compatibility has been explicitly validated.

    :param value: Exact ``fmiVersion`` text read from ``modelDescription.xml``.
    :return: FMI family used to select compatible parsing and runtime logic.
    :raises TypeError: If the declaration is not text.
    :raises ValueError: If the declaration is malformed or unsupported.
    """

    # The parser is a trust boundary, so reject incorrect runtime types with a
    # stable public error instead of leaking an attribute-access failure.
    if isinstance(value, str):
        declared_value: str = value
    else:
        raise TypeError("The FMI version declaration must be text")

    # FMI 1 and FMI 2 define fixed model-description declarations. FMI 3 has
    # a version grammar that permits stable patch identifiers without leading
    # zeros, while this implementation deliberately limits the minor to 0.
    # Whitespace is not removed because it is not part of the XML grammar.
    if declared_value == FmiVersion.FMI_1_0.value:
        version: FmiVersion = FmiVersion.FMI_1_0
    elif declared_value == FmiVersion.FMI_2_0.value:
        version = FmiVersion.FMI_2_0
    else:
        fmi_three_match: re.Match[str] | None = re.fullmatch(
            r"3\.0(?:\.(?:0|[1-9][0-9]*))?",
            declared_value,
            flags=re.ASCII,
        )
        if fmi_three_match is not None:
            version = FmiVersion.FMI_3_0
        else:
            raise ValueError(
                f"Invalid or unsupported FMI version declaration: {declared_value!r}"
            )

    return version


def normalize_fmi_export_version(value: FmiVersion | str) -> FmiVersion:
    """Normalize a public export-version selection to the canonical FMI type.

    Textual API values must use the complete canonical family so a future
    minor version cannot make a short major alias ambiguous. Patch releases
    are declarations of imported FMUs, not export targets, and therefore are
    not silently reduced here.

    :param value: Canonical FMI version or its complete textual value.
    :return: Canonical FMI version selected by the caller.
    :raises TypeError: If the selection is neither text nor ``FmiVersion``.
    :raises ValueError: If the selection is not a supported canonical value.
    """

    # Preserve type identity when an internal caller already supplies the
    # canonical enum; only external textual input needs normalization.
    if isinstance(value, FmiVersion):
        version: FmiVersion = value
    elif isinstance(value, str):
        normalized_value: str = value.strip()
        if normalized_value == FmiVersion.FMI_1_0.value:
            version = FmiVersion.FMI_1_0
        elif normalized_value == FmiVersion.FMI_2_0.value:
            version = FmiVersion.FMI_2_0
        elif normalized_value == FmiVersion.FMI_3_0.value:
            version = FmiVersion.FMI_3_0
        else:
            raise ValueError(f"Unsupported FMI version selection: {normalized_value!r}")
    else:
        raise TypeError("The FMI export-version selection must be text or FmiVersion")

    return version
