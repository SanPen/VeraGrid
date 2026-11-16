# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression coverage for shared variable UIDs in distinct vectorized groups."""

from VeraGridEngine.Utils.Symbolic import block as block_module


class _StructuralBlock:
    def __init__(self, uid: int, kind: str) -> None:
        self.uid = uid
        self.kind = kind

    def copy(self):
        return self

    def unify_blocks(self) -> None:
        pass

    def get_all_equations_list(self):
        return self.kind, self.uid


def _same_kind(first, second) -> bool:
    return first[0] == second[0]


def _align_shared_input(first, second):
    return {10: second[1] + 100}


def _matching_attributes(blocks, alignments) -> bool:
    return True


def test_variable_alignments_remain_in_their_model_group(monkeypatch) -> None:
    monkeypatch.setattr(block_module, "equivalent_systems", _same_kind)
    monkeypatch.setattr(block_module, "align_variables", _align_shared_input)
    monkeypatch.setattr(block_module, "variables_in_corresponding_attributes", _matching_attributes)

    blocks = [_StructuralBlock(1, "A"), _StructuralBlock(2, "A"),
              _StructuralBlock(3, "B"), _StructuralBlock(4, "B"),
              _StructuralBlock(5, "B")]
    groups, alignments = block_module.compare_n_blocks_structurally(blocks, by_class=True)

    assert groups == {1: [2], 3: [4, 5]}
    assert alignments == {1: {10: [102]}, 3: {10: [104, 105]}}
