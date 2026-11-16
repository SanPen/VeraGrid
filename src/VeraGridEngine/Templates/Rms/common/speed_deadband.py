# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Stateful speed deadband used by CGMES turbine governor blocks."""

from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import flipflop


def build_intentional_speed_deadband(
        control: ControlRealization,
        speed_deviation: Expr,
        deadband_threshold: Expr,
        hysteresis_width: Expr,
) -> Expr:
    """Build the source-defined positive and negative hysteresis branches.

    The signal remains zero until its magnitude exceeds threshold plus
    hysteresis. Once active, it follows the unit-slope branch until it returns
    inside the deadband threshold.

    :param control: Governor realization that owns modes and procedural logic.
    :param speed_deviation: Signed per-unit speed deviation from nominal.
    :param deadband_threshold: Per-unit intentional deadband threshold.
    :param hysteresis_width: Per-unit pickup/dropout separation.
    :return: Signed deadband output with retained positive and negative modes.
    """
    positive_mode: Var = control.vf.add_var(
        f'PositiveSpeedDeadbandMode_{control.name}',
    )
    negative_mode: Var = control.vf.add_var(
        f'NegativeSpeedDeadbandMode_{control.name}',
    )
    control.block.mode_dict[positive_mode] = Const(0.0)
    control.block.mode_dict[negative_mode] = Const(0.0)

    control.block.procedural_logic.append(
        flipflop(
            boolset=sym.heaviside(
                speed_deviation - deadband_threshold - hysteresis_width,
            ),
            boolreset=Const(1.0) - sym.heaviside(
                speed_deviation - deadband_threshold,
            ),
            output=positive_mode,
            name=f'PositiveSpeedDeadband_{control.name}',
        )
    )
    control.block.procedural_logic.append(
        flipflop(
            boolset=sym.heaviside(
                -deadband_threshold - hysteresis_width - speed_deviation,
            ),
            boolreset=Const(1.0) - sym.heaviside(
                -deadband_threshold - speed_deviation,
            ),
            output=negative_mode,
            name=f'NegativeSpeedDeadband_{control.name}',
        )
    )
    positive_output: Expr = positive_mode * (speed_deviation - deadband_threshold)
    negative_output: Expr = negative_mode * (speed_deviation + deadband_threshold)
    return positive_output + negative_output
