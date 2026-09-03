# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Assemble declared EMT device currents into topology-owned KCL balances.

The assembler resolves typed device terminals and conductors through the
assigned VeraGrid topology. Visible symbolic ports remain signal interfaces
and never determine electrical ownership.
"""

from typing import Dict, List, Tuple

from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    EmtTerminalConductor,
    EmtTerminalCurrentContribution,
    EmtTerminalSide,
    validate_emt_terminal_current_contributions,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _resolve_emt_terminal_topology(
        terminal_side: EmtTerminalSide,
        bus_from_index: int | None,
        bus_to_index: int | None,
        bus_from_is_dc: bool | None,
        bus_to_is_dc: bool | None,
        bus_index: int | None,
        bus_is_dc: bool | None,
) -> Tuple[int, bool, float]:
    """Resolve one declared EMT terminal against physical network topology.

    :param terminal_side: Declared device terminal.
    :param bus_from_index: From-side bus index for a two-terminal device.
    :param bus_to_index: To-side bus index for a two-terminal device.
    :param bus_from_is_dc: Whether the from-side bus is DC.
    :param bus_to_is_dc: Whether the to-side bus is DC.
    :param bus_index: Bus index for a one-terminal device.
    :param bus_is_dc: Whether the one-terminal bus is DC.
    :return: Bus index, DC-domain flag, and nodal sign.
    """
    if terminal_side is EmtTerminalSide.BUS:
        if bus_index is not None and bus_is_dc is not None:
            result: Tuple[int, bool, float] = (bus_index, bus_is_dc, 1.0)
        else:
            raise ValueError("EMT bus terminal lacks one-terminal topology")
    else:
        if terminal_side is EmtTerminalSide.FROM:
            if bus_from_index is not None and bus_from_is_dc is not None:
                result = (bus_from_index, bus_from_is_dc, -1.0)
            else:
                raise ValueError("EMT from terminal lacks branch topology")
        else:
            if terminal_side is EmtTerminalSide.TO:
                if bus_to_index is not None and bus_to_is_dc is not None:
                    result = (bus_to_index, bus_to_is_dc, -1.0)
                else:
                    raise ValueError("EMT to terminal lacks branch topology")
            else:
                raise TypeError("EMT terminal side must be an EmtTerminalSide")
    return result


def _get_emt_conductor_phase_index(conductor: EmtTerminalConductor) -> int:
    """Return the KCL vector index of one EMT conductor.

    :param conductor: Declared EMT terminal conductor.
    :return: DC or NABC KCL vector index.
    """
    if conductor is EmtTerminalConductor.DC:
        phase_index: int = 0
    else:
        if conductor is EmtTerminalConductor.NEUTRAL:
            phase_index = 0
        else:
            if conductor is EmtTerminalConductor.PHASE_A:
                phase_index = 1
            else:
                if conductor is EmtTerminalConductor.PHASE_B:
                    phase_index = 2
                else:
                    if conductor is EmtTerminalConductor.PHASE_C:
                        phase_index = 3
                    else:
                        raise ValueError("Unsupported EMT terminal conductor")
    return phase_index


def assemble_emt_terminal_current_contributions(
        model: Block,
        current_balance: Dict[int, List[Expr | Var | Const]],
        bus_from_index: int | None = None,
        bus_to_index: int | None = None,
        bus_from_is_dc: bool | None = None,
        bus_to_is_dc: bool | None = None,
        bus_index: int | None = None,
        bus_is_dc: bool | None = None,
) -> None:
    """Assemble one EMT device into topology-owned instantaneous KCL.

    The contract is hidden electrical metadata. Visible block ports and diagram
    connections do not participate in nodal ownership. Validation completes for
    every declaration before the first KCL entry is mutated.

    :param model: Canonical EMT block owning current variables and declarations.
    :param current_balance: Per-bus DC or NABC current accumulators.
    :param bus_from_index: From-side bus index for a two-terminal device.
    :param bus_to_index: To-side bus index for a two-terminal device.
    :param bus_from_is_dc: Whether the from-side bus is DC.
    :param bus_to_is_dc: Whether the to-side bus is DC.
    :param bus_index: Bus index for a one-terminal device.
    :param bus_is_dc: Whether the one-terminal bus is DC.
    :return: None.
    """
    validate_emt_terminal_current_contributions(block=model)
    contributions: List[EmtTerminalCurrentContribution] = (
        model.dynamic_model_contract.emt_terminal_current_contributions
    )
    if len(contributions) > 0:
        pass
    else:
        raise ValueError("EMT model has no declared terminal current contributions")

    resolved_contributions: List[Tuple[int, int, float, Var]] = list()
    contribution: EmtTerminalCurrentContribution
    for contribution in contributions:
        terminal_side: EmtTerminalSide = contribution.get_terminal_side()
        conductor: EmtTerminalConductor = contribution.get_conductor()
        resolved_bus_index: int
        resolved_bus_is_dc: bool
        sign: float
        resolved_bus_index, resolved_bus_is_dc, sign = _resolve_emt_terminal_topology(
            terminal_side=terminal_side,
            bus_from_index=bus_from_index,
            bus_to_index=bus_to_index,
            bus_from_is_dc=bus_from_is_dc,
            bus_to_is_dc=bus_to_is_dc,
            bus_index=bus_index,
            bus_is_dc=bus_is_dc,
        )
        if conductor is EmtTerminalConductor.DC:
            conductor_is_dc: bool = True
        else:
            conductor_is_dc = False
        if conductor_is_dc == resolved_bus_is_dc:
            pass
        else:
            raise ValueError(
                "EMT terminal conductor does not match the connected bus domain"
            )
        phase_index: int = _get_emt_conductor_phase_index(conductor=conductor)
        if phase_index < len(current_balance[resolved_bus_index]):
            pass
        else:
            raise ValueError("EMT terminal conductor is absent from the bus shell")
        current_var: Var = model.E(contribution.get_current_reference())
        resolved_contributions.append((
            resolved_bus_index,
            phase_index,
            sign,
            current_var,
        ))
    else:
        pass

    resolved_contribution: Tuple[int, int, float, Var]
    for resolved_contribution in resolved_contributions:
        target_bus_index: int = resolved_contribution[0]
        target_phase_index: int = resolved_contribution[1]
        target_sign: float = resolved_contribution[2]
        target_current: Var = resolved_contribution[3]
        current_balance[target_bus_index][target_phase_index] = (
            current_balance[target_bus_index][target_phase_index]
            + target_sign * target_current
        )
    else:
        pass
