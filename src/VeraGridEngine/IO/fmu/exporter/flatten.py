# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Iterable, List

from .compat import Block, Const, Var
from .snapshot import reconstruct_block


def _extend_unique_vars(target: List[Var], source: Iterable[Var]) -> None:
    seen = {var.uid for var in target}
    for var in source:
        if var.uid not in seen:
            target.append(var)
            seen.add(var.uid)


def _validate_no_duplicate_names(vars_list: List[Var], label: str) -> None:
    names = [var.name for var in vars_list]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {label} names in flattened model: {', '.join(duplicates)}")


def validate_flat_block(block: Block) -> None:
    _validate_no_duplicate_names(block.state_vars, "state")
    _validate_no_duplicate_names(block.algebraic_vars, "algebraic")
    _validate_no_duplicate_names(block.diff_vars, "differential")

    if len(block.state_vars) != len(block.state_eqs):
        raise ValueError(
            f"FMU export requires one state equation per state variable; got {len(block.state_vars)} states and {len(block.state_eqs)} state equations"
        )
    if len(block.algebraic_vars) != len(block.algebraic_eqs):
        raise ValueError(
            f"FMU export requires one algebraic equation per algebraic variable; got {len(block.algebraic_vars)} algebraics and {len(block.algebraic_eqs)} algebraic equations"
        )

    known_uids = {var.uid for var in block.state_vars + block.algebraic_vars + block.diff_vars}
    known_uids.update(var.uid for var in block.parameters.keys())
    known_uids.update(var.uid for var in block.event_dict.keys())
    known_uids.update(var.uid for var in block.mode_dict.keys())

    missing_outputs = sorted(var.name for var in block.out_vars if var.uid not in known_uids)
    if missing_outputs:
        raise ValueError(f"Output vars must exist in the flattened model symbol table: {', '.join(missing_outputs)}")

    missing_params = sorted(var.name for var, value in block.parameters.items() if not isinstance(value, Const) or value.value is None)
    if missing_params:
        raise ValueError(f"Constant parameters without concrete values are not exportable: {', '.join(missing_params)}")


def flatten_block(block: Block) -> Block:
    flat = Block(name=block.name, uid=block.uid)
    flat.diagram = block.diagram.to_dict()

    for current in block.get_all_blocks():
        flat.state_vars.extend(current.state_vars)
        flat.state_eqs.extend(current.state_eqs)
        flat.algebraic_vars.extend(current.algebraic_vars)
        flat.algebraic_eqs.extend(current.algebraic_eqs)
        flat.diff_vars.extend(current.diff_vars)
        flat.reformulated_vars.extend(current.reformulated_vars)
        flat.differential_eqs.extend(current.differential_eqs)
        _extend_unique_vars(flat.in_vars, current.in_vars)
        _extend_unique_vars(flat.out_vars, current.out_vars)
        flat.parameters.update(current.parameters)
        flat.init_values.update(current.init_values)
        flat.init_eqs.update(current.init_eqs)
        flat.diff_init_eqs.update(current.diff_init_eqs)
        flat.discrete_eqs.update(current.discrete_eqs)
        flat.event_dict.update(current.event_dict)
        flat.mode_dict.update(current.mode_dict)
        flat.external_mapping.update(current.external_mapping)
        flat.api_obj_mapping.update(current.api_obj_mapping)
        flat.procedural_logic.extend(current.procedural_logic)

    flat.children = []
    flat.var_mapping = {var.name: var for var in flat.algebraic_vars + flat.state_vars + flat.diff_vars}
    validate_flat_block(flat)
    return flat


def flatten_model(snapshot: dict[str, object]) -> Block:
    block_copy = reconstruct_block(snapshot)
    return flatten_block(block_copy)
