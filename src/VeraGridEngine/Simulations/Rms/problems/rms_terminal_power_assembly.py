# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Assemble declared RMS device powers into topology-owned bus balances.

Signal wiring is intentionally absent from this module. Each declaration says
which symbolic P/Q variable belongs to a physical terminal, and the assigned
VeraGrid device supplies the bus that owns the resulting nodal injection.
"""

from VeraGridEngine.basic_structures import BoolVec, ObjVec
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    RmsTerminalPowerContribution,
    RmsTerminalSide,
    validate_rms_terminal_power_contributions,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _add_terminal_balance_value(
        balance: ObjVec,
        balance_used: BoolVec,
        bus_index: int,
        value: Expr,
) -> None:
    """Add one symbolic contribution to a preallocated nodal balance.

    :param balance: Preallocated symbolic balance array.
    :param balance_used: Flags identifying initialized balance entries.
    :param bus_index: Network bus index selected from device topology.
    :param value: Symbolic contribution to add.
    :return: None.
    """
    if balance_used[bus_index]:
        balance[bus_index] += value
    else:
        balance[bus_index] = value
        balance_used[bus_index] = True


def _resolve_terminal_topology(
        contribution: RmsTerminalPowerContribution,
        bus_from_index: int | None,
        bus_to_index: int | None,
        bus_from_is_dc: bool | None,
        bus_to_is_dc: bool | None,
        bus_index: int | None,
        bus_is_dc: bool | None,
) -> tuple[int, bool]:
    """Resolve one declared side through the physical device topology.

    :param contribution: Typed terminal power declaration.
    :param bus_from_index: Physical from-side bus index.
    :param bus_to_index: Physical to-side bus index.
    :param bus_from_is_dc: Whether the physical from-side bus is DC.
    :param bus_to_is_dc: Whether the physical to-side bus is DC.
    :param bus_index: Physical bus index for a one-terminal device.
    :param bus_is_dc: Whether the one-terminal physical bus is DC.
    :return: Resolved bus index and its AC/DC domain.
    """
    terminal_side: RmsTerminalSide = contribution.get_terminal_side()
    if terminal_side is RmsTerminalSide.BUS:
        if bus_index is not None and bus_is_dc is not None:
            return bus_index, bus_is_dc
        else:
            raise ValueError("RMS bus terminal requires one-terminal device topology")
    else:
        if terminal_side is RmsTerminalSide.FROM:
            if bus_from_index is not None and bus_from_is_dc is not None:
                return bus_from_index, bus_from_is_dc
            else:
                raise ValueError("RMS from terminal requires two-terminal device topology")
        else:
            if terminal_side is RmsTerminalSide.TO:
                if bus_to_index is not None and bus_to_is_dc is not None:
                    return bus_to_index, bus_to_is_dc
                else:
                    raise ValueError("RMS to terminal requires two-terminal device topology")
            else:
                raise ValueError("Unsupported RMS terminal side")


def assemble_rms_terminal_power_contributions(
        model: Block,
        bus_from_index: int | None,
        bus_to_index: int | None,
        bus_from_is_dc: bool | None,
        bus_to_is_dc: bool | None,
        active_power_balance: ObjVec,
        active_power_balance_used: BoolVec,
        reactive_power_balance: ObjVec,
        reactive_power_balance_used: BoolVec,
        bus_index: int | None = None,
        bus_is_dc: bool | None = None,
) -> None:
    """Assemble one device into network balances from topology and its contract.

    Two-terminal powers use the branch convention, positive from the connected
    bus into the device, while a one-terminal ``BUS`` power uses the injection
    convention, positive from the device into the network. Bus indices and
    AC/DC domains come only from physical device topology; no dynamic diagram
    wire participates in network equation ownership.

    :param model: Canonical RMS device block.
    :param bus_from_index: Index of the physical from-side bus.
    :param bus_to_index: Index of the physical to-side bus.
    :param bus_from_is_dc: Whether the physical from-side bus is DC.
    :param bus_to_is_dc: Whether the physical to-side bus is DC.
    :param active_power_balance: Preallocated nodal active-power expressions.
    :param active_power_balance_used: Active-power initialization flags.
    :param reactive_power_balance: Preallocated nodal reactive-power expressions.
    :param reactive_power_balance_used: Reactive-power initialization flags.
    :param bus_index: Physical bus index for a one-terminal device.
    :param bus_is_dc: Whether the one-terminal physical bus is DC.
    :return: None.
    """
    validate_rms_terminal_power_contributions(block=model)
    contributions: list[RmsTerminalPowerContribution] = (
        model.dynamic_model_contract.rms_terminal_power_contributions
    )
    if len(contributions) > 0:
        pass
    else:
        raise ValueError("RMS device has no declared terminal power contributions")

    # Validate the complete topology-domain contract before mutating either
    # balance so one invalid terminal cannot leave a partial device injection.
    contribution: RmsTerminalPowerContribution
    for contribution in contributions:
        bus_index: int
        bus_is_dc: bool
        bus_index, bus_is_dc = _resolve_terminal_topology(
            contribution=contribution,
            bus_from_index=bus_from_index,
            bus_to_index=bus_to_index,
            bus_from_is_dc=bus_from_is_dc,
            bus_to_is_dc=bus_to_is_dc,
            bus_index=bus_index,
            bus_is_dc=bus_is_dc,
        )
        reactive_reference: VarPowerFlowReferenceType | None = (
            contribution.get_reactive_power_reference()
        )
        if reactive_reference is not None and bus_is_dc:
            raise ValueError(
                "RMS terminal declares reactive power on a DC bus"
            )
        else:
            pass

    contribution: RmsTerminalPowerContribution
    for contribution in contributions:
        bus_index, bus_is_dc = _resolve_terminal_topology(
            contribution=contribution,
            bus_from_index=bus_from_index,
            bus_to_index=bus_to_index,
            bus_from_is_dc=bus_from_is_dc,
            bus_to_is_dc=bus_to_is_dc,
            bus_index=bus_index,
            bus_is_dc=bus_is_dc,
        )

        active_power: Var = model.E(
            contribution.get_active_power_reference()
        )
        terminal_side: RmsTerminalSide = contribution.get_terminal_side()
        network_active_power: Expr
        if terminal_side is RmsTerminalSide.BUS:
            network_active_power = active_power
        else:
            network_active_power = -active_power
        _add_terminal_balance_value(
            balance=active_power_balance,
            balance_used=active_power_balance_used,
            bus_index=bus_index,
            value=network_active_power,
        )

        reactive_reference: VarPowerFlowReferenceType | None = (
            contribution.get_reactive_power_reference()
        )
        if reactive_reference is None:
            pass
        else:
            reactive_power: Var = model.E(reactive_reference)
            network_reactive_power: Expr
            if terminal_side is RmsTerminalSide.BUS:
                network_reactive_power = reactive_power
            else:
                network_reactive_power = -reactive_power
            _add_terminal_balance_value(
                balance=reactive_power_balance,
                balance_used=reactive_power_balance_used,
                bus_index=bus_index,
                value=network_reactive_power,
            )


def convert_rms_ac_power_balance_to_current_balance(
        bus_index: int,
        voltage_real: Var,
        voltage_imaginary: Var,
        active_power_balance: ObjVec,
        active_power_balance_used: BoolVec,
        reactive_power_balance: ObjVec,
        reactive_power_balance_used: BoolVec,
        real_current_balance: ObjVec,
        real_current_balance_used: BoolVec,
        imaginary_current_balance: ObjVec,
        imaginary_current_balance_used: BoolVec,
) -> None:
    """Convert one AC nodal power contribution into phasor current balance.

    The phasor solver owns Kirchhoff current equations, while the shared RMS
    device contract declares terminal active and reactive powers. For
    ``S = V * conjugate(I)``, the equivalent balance current is obtained from
    ``I = conjugate(S) / conjugate(V)``. Existing branch and injection current
    terms remain in the same preallocated nodal arrays.

    :param bus_index: AC network bus index to convert.
    :param voltage_real: Real component of the AC bus voltage.
    :param voltage_imaginary: Imaginary component of the AC bus voltage.
    :param active_power_balance: Preallocated nodal active-power expressions.
    :param active_power_balance_used: Active-power initialization flags.
    :param reactive_power_balance: Preallocated nodal reactive-power expressions.
    :param reactive_power_balance_used: Reactive-power initialization flags.
    :param real_current_balance: Preallocated nodal real-current expressions.
    :param real_current_balance_used: Real-current initialization flags.
    :param imaginary_current_balance: Preallocated nodal imaginary-current expressions.
    :param imaginary_current_balance_used: Imaginary-current initialization flags.
    :return: None.
    """
    if active_power_balance_used[bus_index] or reactive_power_balance_used[bus_index]:
        active_power: Expr | Var | Const
        reactive_power: Expr | Var | Const
        if active_power_balance_used[bus_index]:
            active_power = active_power_balance[bus_index]
        else:
            active_power = Const(0.0)
        if reactive_power_balance_used[bus_index]:
            reactive_power = reactive_power_balance[bus_index]
        else:
            reactive_power = Const(0.0)

        # Convert the declared complex-power balance at the physical AC bus
        # into the current coordinates used by the phasor KCL formulation.
        voltage_magnitude_squared: Expr = (
            voltage_real * voltage_real
            + voltage_imaginary * voltage_imaginary
        )
        real_current: Expr = (
            active_power * voltage_real
            + reactive_power * voltage_imaginary
        ) / voltage_magnitude_squared
        imaginary_current: Expr = (
            active_power * voltage_imaginary
            - reactive_power * voltage_real
        ) / voltage_magnitude_squared
        _add_terminal_balance_value(
            balance=real_current_balance,
            balance_used=real_current_balance_used,
            bus_index=bus_index,
            value=real_current,
        )
        _add_terminal_balance_value(
            balance=imaginary_current_balance,
            balance_used=imaginary_current_balance_used,
            bus_index=bus_index,
            value=imaginary_current,
        )
    else:
        pass
