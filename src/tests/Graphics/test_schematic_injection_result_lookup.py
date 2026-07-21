# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import (
    SchematicWidget,
    _get_injection_result_index,
)


def test_injection_name_lookup_skips_blank_and_duplicate_names() -> None:
    lookup = SchematicWidget._build_injection_name_lookup(None, ["", "  ", "G1", "G1", "G2"])

    assert lookup == {"G2": 4}


def test_injection_result_index_falls_back_for_blank_or_duplicate_names() -> None:
    lookup = SchematicWidget._build_injection_name_lookup(None, ["", "", "G3"])

    assert lookup == {"G3": 2}
    assert lookup.get("", None) is None
    assert _get_injection_result_index(device_name="", fallback_index=1, lookup=lookup) == 1
    assert _get_injection_result_index(device_name="G3", fallback_index=0, lookup=lookup) == 2
