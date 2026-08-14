# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, cast

from VeraGridEngine.IO.fmu.exporter_me import compat


@dataclass(frozen=True, slots=True)
class BlockMEProfile:
    kind: str
    supported: bool
    reasons: tuple[str, ...]


def _root_base_var(var: Any) -> Any | None:
    base = getattr(var, "base_var", None)
    if base is None:
        return None
    while getattr(base, "base_var", None) is not None:
        base = base.base_var
    return base


def _unwrap_assignment_target(expr: Any, target_uid: int) -> Any | None:
    if isinstance(expr, compat.BinOp) and expr.op == "-":
        if isinstance(expr.left, compat.Var) and expr.left.uid == target_uid:
            return expr.right
        if isinstance(expr.right, compat.Var) and expr.right.uid == target_uid:
            return expr.left
    return None


def _expr_vars(expr: Any) -> list[Any]:
    getter = getattr(expr, "get_vars", None)
    if callable(getter):
        values = getter()
        return list(cast(Iterable[Any], values))
    return []


def analyze_flat_block_for_me(flat_block: Any) -> BlockMEProfile:
    state_uids = {var.uid for var in flat_block.state_vars}
    algebraic_by_uid = {var.uid: (index, var) for index, var in enumerate(flat_block.algebraic_vars)}
    input_uids = {var.uid for var in getattr(flat_block, "in_vars", []) or []}
    reasons: list[str] = []

    event_names = [getattr(var, "name", "") for var in getattr(flat_block, "event_dict", {}).keys()]
    if (
        event_names
        and len(getattr(flat_block, "state_vars", []) or []) == 0
        and len(getattr(flat_block, "algebraic_vars", []) or []) == 0
        and len(getattr(flat_block, "diff_vars", []) or []) == 0
        and all(name.startswith("Ih_f_") or name.startswith("Ih_t_") for name in event_names)
    ):
        return BlockMEProfile(
            kind="history_runtime",
            supported=False,
            reasons=(
                "The block looks like a Bergeron-style history runtime placeholder. It depends on step-size-driven external delay buffers and runtime-updated history parameters, so it is not exportable as FMI 2.0 Model Exchange with the current ME architecture.",
            ),
        )

    for diff_var in flat_block.diff_vars:
        base = _root_base_var(diff_var)
        if base is None:
            reasons.append(
                f"Differential variable '{diff_var.name}' has no base variable; Model Exchange requires explicit continuous states."
            )
            continue
        if base.uid in state_uids:
            continue
        if base.uid in algebraic_by_uid:
            index, base_var = algebraic_by_uid[base.uid]
            message = (
                f"Differential variable '{diff_var.name}' is based on algebraic variable '{base_var.name}', not on a state variable. "
                f"The current ME exporter supports only semi-explicit profiles xdot=f(x,w,u,p,t), 0=g(x,w,u,p,t)."
            )
            algebraic_eq = flat_block.algebraic_eqs[index]
            rhs = _unwrap_assignment_target(algebraic_eq, base_var.uid)
            if rhs is not None:
                rhs_uids = {var.uid for var in _expr_vars(rhs)}
                if rhs_uids & input_uids:
                    message += (
                        f" '{base_var.name}' is constrained by an algebraic relation that depends on FMU inputs, so exporting its derivative would require host-side input derivatives."
                    )
            message += " This native block should be lowered to explicit states before ME export, e.g. with a state-based transfer-function helper such as `tf_to_block_with_states()`."
            reasons.append(message)
            continue
        if base.uid in input_uids:
            reasons.append(
                f"Differential variable '{diff_var.name}' is based directly on FMU input '{base.name}'. FMI 2.0 Model Exchange does not provide input derivatives through the normal ME calling sequence."
            )
            continue
        reasons.append(
            f"Differential variable '{diff_var.name}' is based on unsupported variable '{base.name}'. Only state-based derivatives are accepted by the current ME exporter."
        )

    if reasons:
        return BlockMEProfile(kind="implicit_dae", supported=False, reasons=tuple(reasons))
    if flat_block.state_vars and flat_block.algebraic_vars:
        return BlockMEProfile(kind="semi_explicit_dae", supported=True, reasons=())
    if flat_block.state_vars:
        return BlockMEProfile(kind="ode", supported=True, reasons=())
    if flat_block.algebraic_vars:
        return BlockMEProfile(kind="algebraic_only", supported=True, reasons=())
    return BlockMEProfile(kind="empty", supported=True, reasons=())


def assert_block_supported_for_me(flat_block: Any) -> BlockMEProfile:
    profile = analyze_flat_block_for_me(flat_block)
    if not profile.supported:
        raise ValueError(" ".join(profile.reasons))
    return profile
