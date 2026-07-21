# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np

from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import _get_branch_result_index


def test_branch_result_index_uses_branch_index_for_non_expanded_three_phase_arrays() -> None:
    values = np.ones(12, dtype=float)

    assert _get_branch_result_index(branch_index=6, phase_index=0, values=values, is_three_phase=True) == 6
    assert _get_branch_result_index(branch_index=6, phase_index=2, values=values, is_three_phase=True) == 6


def test_branch_result_index_uses_phase_offset_for_expanded_three_phase_arrays() -> None:
    values = np.ones(36, dtype=float)

    assert _get_branch_result_index(branch_index=6, phase_index=0, values=values, is_three_phase=True) == 18
    assert _get_branch_result_index(branch_index=6, phase_index=2, values=values, is_three_phase=True) == 20
