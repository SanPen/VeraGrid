# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Shared tap-selection table from IEC 61970-302 Figures 150 and 151."""

from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, heaviside


def build_pti_tap_selection_expression(table_input: Expr) -> Expr:
    """Map the PTI stabilizer output signal to the IEC tap-ratio correction.

    The IEC table publishes tap ratios from 1.100 to 0.900. The block diagram
    adds the selected output to unity before multiplying terminal voltage, so
    this function returns the table ratio minus one.

    :param table_input: Stabilizer signal driving the tap-selection table.
    :return: Selected tap-ratio correction around nominal unity.
    """
    boundaries: tuple[float, ...] = (
        -0.100, -0.040, -0.020, -0.010, -0.005, -0.002,
        0.002, 0.005, 0.010, 0.020, 0.040, 0.100,
    )
    tap_ratios: tuple[float, ...] = (
        1.100, 1.040, 1.020, 1.010, 1.005, 1.002, 1.000,
        0.998, 0.995, 0.990, 0.980, 0.960, 0.900,
    )
    tap_adjustment: Expr = Const(tap_ratios[0] - 1.0)
    boundary_index: int
    for boundary_index in range(len(boundaries)):
        # A boundary belongs to the next interval, which is left-inclusive.
        boundary_step: Expr = Const(1.0) - heaviside(
            Const(boundaries[boundary_index]) - table_input,
        )
        ratio_change: float = (
            tap_ratios[boundary_index + 1] - tap_ratios[boundary_index]
        )
        tap_adjustment += Const(ratio_change) * boundary_step
    else:
        pass
    return tap_adjustment
