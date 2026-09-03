# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, Iterable, Protocol, TypeVar


ExpressionT = TypeVar("ExpressionT")
ProceduralLogicData = Dict[str, object]


class ProceduralLogicEntryContract(Protocol[ExpressionT]):
    """Declare the behavior a symbolic block requires from procedural logic."""

    __slots__ = ()

    def to_data(self) -> ProceduralLogicData:
        """Return the declarative representation of this logic entry.

        :return: Typed declarative logic data.
        """
        ...

    def remap(
            self,
            var_mapping: Dict[ExpressionT | str, ExpressionT],
    ) -> "ProceduralLogicEntryContract[ExpressionT]":
        """Clone this entry against a symbolic-variable mapping.

        :param var_mapping: Source expressions and names mapped to replacements.
        :return: Remapped procedural logic entry.
        """
        ...


class ProceduralLogicCodecContract(Protocol[ExpressionT]):
    """Declare fail-closed reconstruction of declarative procedural entries."""

    __slots__ = ()

    def parse_entries(
            self,
            entries: Iterable[ProceduralLogicData],
    ) -> Iterable[ProceduralLogicEntryContract[ExpressionT]]:
        """Reconstruct typed procedural entries from declarative data.

        :param entries: Declarative procedural entries.
        :return: Reconstructed typed entries.
        """
        ...
