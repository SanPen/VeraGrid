# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Check that native slot filters retain their DGS class restrictions."""

import pytest

from VeraGridEngine.IO.dgs.dgs_objects import BlkSlot
from VeraGridEngine.IO.dgs.dgs_to_blocks import ElmCompInstanceEntry


@pytest.mark.parametrize("filter_text", ("*", "ElmVsc*", "ElmVsc", ""))
def test_slot_filter_survives_read_and_write(filter_text: str) -> None:
    """Preserve wildcard and explicit filters without changing missing references.

    :param filter_text: Raw filter exported in the slot row.
    :return: None.
    """
    header: dict[str, int] = dict(FID=0, OP=1, loc_name=2, element=3, filtmod=4)
    slot: BlkSlot = BlkSlot.parse_line(f'1;C;Converter;*;{filter_text}', header)
    assert slot.filtmod == filter_text
    # The exception applies only to the filter, not to the reference column.
    assert slot.element is None
    columns: dict[str, int] = dict((prop.name, index) for index, prop in enumerate(BlkSlot.properties_list))
    reloaded: BlkSlot = BlkSlot.parse_line(slot.to_dgs_line(), columns)
    assert reloaded.filtmod == filter_text


@pytest.mark.parametrize(("filter_text", "element_kind", "expected"), (
    ("*", "ElmVsc", True),
    ("*", "ElmDsl", True),
    ("*", "StaVmea", True),
    ("*", "StaImea", True),
    ("*", "ElmPhi", True),
    ("ElmVsc*", "ElmVscmono", True),
    ("ElmVsc*", "StaVmea", False),
    ("ElmVsc", "ElmVsc", True),
    ("ElmVsc", "ElmVscmono", False),
    ("", "ElmVsc", False),
))
def test_slot_filter_validates_the_referenced_class(
        filter_text: str, element_kind: str, expected: bool,
) -> None:
    """Permit unrestricted slots while preserving exact and prefix restrictions.

    :param filter_text: Source filter rather than an inferred class list.
    :param element_kind: Actual class of the referenced object.
    :param expected: Whether the declared filter permits the class.
    :return: None.
    """
    entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="slot", slot_name="Converter", element_id="equipment",
        element_name="Equipment", element_kind=element_kind, element_outserv=0,
        type_id=None, type_name=None, slot_filter=filter_text,
        slot_reference_is_resolved=True, element_reference_is_resolved=True,
    )
    assert entry.accepts_element_kind(element_kind) == expected
