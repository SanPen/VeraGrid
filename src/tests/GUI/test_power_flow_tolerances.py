# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGrid.Gui.Main.SubClasses.simulations import get_valid_controls_start_tolerance_index


def test_controls_start_tolerance_is_adjusted_when_it_is_below_solver_tolerance() -> None:
    """
    The GUI should relax the controls activation threshold to ``tol * 100`` when it is too strict.
    """
    adjusted_idx: int = get_valid_controls_start_tolerance_index(
        tolerance_idx=4,
        controls_start_tolerance_idx=6,
        controls_start_tolerance_min_idx=1,
    )

    assert adjusted_idx == 2


def test_controls_start_tolerance_adjustment_respects_spin_box_minimum() -> None:
    """
    The GUI should clamp the relaxed threshold to the smallest exponent the spin box can represent.
    """
    adjusted_idx: int = get_valid_controls_start_tolerance_index(
        tolerance_idx=2,
        controls_start_tolerance_idx=4,
        controls_start_tolerance_min_idx=1,
    )

    assert adjusted_idx == 1
