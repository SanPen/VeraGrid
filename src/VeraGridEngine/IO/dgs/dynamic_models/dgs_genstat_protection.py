# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native ElmGenstat positive-sequence low-voltage blocking (PF2024 section 8)."""
import math
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.procedural_logic import TimeDelayLogic, FlipFlopLogic
from VeraGridEngine.enumerations import VarPowerFlowReferenceType as Ref


def apply_genstat_voltage_protection(block: Block,
                                     switch_off: float,
                                     switch_on: float | None,
                                     restart_delay: float | None) -> Block:
    """Block terminal injection; keep controller states running during the outage.

    Reconnection requires voltage continuously above the switch-on threshold for
    the restart delay. The timer cancels when voltage falls to/below that threshold.
    All modes and procedural declarations use canonical UIDs for cloning/persistence.
    """
    if not math.isfinite(switch_off) or switch_off < 0:
        raise ValueError('ElmGenstat umin must be finite and nonnegative')
    if switch_off == 0:
        return block
    if (switch_on is None or restart_delay is None or not math.isfinite(switch_on)
            or switch_on < switch_off or not math.isfinite(restart_delay) or restart_delay < 0):
        raise ValueError('ElmGenstat protection requires uonthr >= umin and finite nonnegative Tondelay')
    voltage = block.external_mapping[Ref.Vm]
    blocked, ready = Var('genstat_low_voltage_blocked'), Var('genstat_reconnect_ready')
    block.mode_dict[blocked] = Const(0.)
    block.mode_dict[ready] = Const(0.)
    block.procedural_logic.extend([
        TimeDelayLogic(ready.name, voltage > Const(switch_on), Const(restart_delay),
                       name='Genstat reconnection timer', output_var_uid=ready.uid, continuous=True),
        FlipFlopLogic(blocked.name, voltage < Const(switch_off), ready > Const(.5),
                      name='Genstat low-voltage blocking', output_var_uid=blocked.uid),
    ])
    terminals = {block.external_mapping[Ref.P].uid, block.external_mapping[Ref.Q].uid}
    terminals.update(v.uid for v in block.out_vars if v.name in ('It_r', 'It_i'))
    for index, variable in enumerate(block.algebraic_vars):
        if variable.uid in terminals:
            # Builders declare residuals as variable - RHS. Gate the injected
            # quantity, never the residual itself (which would remove an equation).
            residual = block.algebraic_eqs[index]
            block.algebraic_eqs[index] = variable - (Const(1.) - blocked) * residual.right
    return block
