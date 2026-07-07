# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
VariableAlignmentEngine - Exact 1-to-1 Variable Mapping for Equivalent Systems.

Computes a deterministic bijection between variables of two mathematically
equivalent systems of equations using structural hashing and backtracking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Const, Var, BinOp, UnOp, Func, Func2
from VeraGridEngine.Utils.Symbolic.compare_expressions_structure import (
    canonical,
    structural_hash,
    expand_and_canonicalize,
)


PLACEHOLDER_NAME = "_"


class VariableSignature:
    """Immutable signature for a variable occurrence in an equation context."""
    __slots__ = ("var_uid", "occurrence_idx", "context_hash", "depth", "path_signature")

    def __init__(
        self,
        var_uid: int,
        occurrence_idx: int,
        context_hash: str,
        depth: int,
        path_signature: Tuple[str, ...],
    ):
        self.var_uid = var_uid
        self.occurrence_idx = occurrence_idx
        self.context_hash = context_hash
        self.depth = depth
        self.path_signature = path_signature

    def __hash__(self) -> int:
        return hash((
            self.var_uid,
            self.occurrence_idx,
            self.context_hash,
            self.depth,
            self.path_signature,
        ))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VariableSignature):
            return False
        return (
            self.occurrence_idx == other.occurrence_idx
            and self.context_hash == other.context_hash
            and self.depth == other.depth
            and self.path_signature == other.path_signature
        )

    def __repr__(self) -> str:
        return f"VarSig(uid={self.var_uid}, occ={self.occurrence_idx}, ctx={self.context_hash[:6]}, depth={self.depth})"


def _replace_var_at_position(
    expr: Expr,
    target_uid: int,
    placeholder: Var,
    occurrence_counter: List[int],
) -> Tuple[Expr, int]:
    """Replace a variable occurrence with a placeholder and return the occurrence index."""
    if isinstance(expr, Var):
        if expr.uid == target_uid:
            occurrence_counter[0] += 1
            return placeholder, occurrence_counter[0] - 1
        return expr, -1

    if isinstance(expr, BinOp):
        new_left, idx = _replace_var_at_position(expr.left, target_uid, placeholder, occurrence_counter)
        new_right, idx2 = _replace_var_at_position(expr.right, target_uid, placeholder, occurrence_counter)
        if idx == -1 and idx2 != -1:
            idx = idx2
        return BinOp(new_left, expr.op, new_right), idx

    if isinstance(expr, UnOp):
        new_operand, idx = _replace_var_at_position(expr.operand, target_uid, placeholder, occurrence_counter)
        return UnOp(expr.op, new_operand), idx

    if isinstance(expr, Func):
        new_arg, idx = _replace_var_at_position(expr.arg, target_uid, placeholder, occurrence_counter)
        return Func(new_arg, expr.op), idx

    if isinstance(expr, Func2):
        new_arg1, idx1 = _replace_var_at_position(expr.arg1, target_uid, placeholder, occurrence_counter)
        new_arg2, idx2 = _replace_var_at_position(expr.arg2, target_uid, placeholder, occurrence_counter)
        idx = idx1 if idx1 != -1 else idx2
        return Func2(expr.name, new_arg1, new_arg2), idx

    return expr, -1


def _get_var_occurrences(expr: Expr, var_uid: int) -> List[int]:
    """Get list of occurrence indices where var_uid appears in expr."""
    occurrences: List[int] = []
    _collect_occurrences(expr, var_uid, occurrences)
    return occurrences


def _get_all_var_occurrences(expr: Expr) -> Dict[int, List[int]]:
    """Get occurrences for all variables in expr in a single pass. Returns dict mapping var_uid to list of occurrence indices."""
    result: Dict[int, List[int]] = {}
    global_counter = [0]
    _collect_all_occurrences(expr, result, global_counter)
    return result


def _collect_all_occurrences(expr: Expr, result: Dict[int, List[int]], counter: List[int]) -> None:
    """Collect occurrence indices for all variables in a single pass."""
    _collect_occurrences_rec(expr, result, counter)


def _collect_occurrences_rec(expr: Expr, result: Dict[int, List[int]], counter: List[int]) -> None:
    """Recursive helper to collect all variable occurrences."""
    if isinstance(expr, Var):
        if expr.uid not in result:
            result[expr.uid] = []
        result[expr.uid].append(counter[0])
        counter[0] += 1
        return
    
    if isinstance(expr, BinOp):
        _collect_occurrences_rec(expr.left, result, counter)
        _collect_occurrences_rec(expr.right, result, counter)
        return
    
    if isinstance(expr, UnOp):
        _collect_occurrences_rec(expr.operand, result, counter)
        return
    
    if isinstance(expr, Func):
        _collect_occurrences_rec(expr.arg, result, counter)
        return
    
    if isinstance(expr, Func2):
        _collect_occurrences_rec(expr.arg1, result, counter)
        _collect_occurrences_rec(expr.arg2, result, counter)
        return


def _collect_occurrences(expr: Expr, var_uid: int, result: List[int]) -> None:
    """Recursively collect occurrence indices."""
    if isinstance(expr, Var):
        if expr.uid == var_uid:
            result.append(len(result))
        return

    if isinstance(expr, BinOp):
        _collect_occurrences(expr.left, var_uid, result)
        _collect_occurrences(expr.right, var_uid, result)
        return

    if isinstance(expr, UnOp):
        _collect_occurrences(expr.operand, var_uid, result)
        return

    if isinstance(expr, Func):
        _collect_occurrences(expr.arg, var_uid, result)
        return

    if isinstance(expr, Func2):
        _collect_occurrences(expr.arg1, var_uid, result)
        _collect_occurrences(expr.arg2, var_uid, result)
        return


def _compute_all_path_signatures(
    expr: Expr,
    var_occurrences: Dict[int, List[int]],
) -> Dict[Tuple[int, int], Tuple[str, ...]]:
    """Compute path signatures for all variable occurrences in a single traversal.
    Returns dict mapping (var_uid, occurrence_idx) -> path_signature.
    """
    result: Dict[Tuple[int, int], Tuple[str, ...]] = {}
    target_occurrences: Dict[int, int] = {uid: 0 for uid in var_occurrences}
    _compute_paths_rec(expr, (), 0, var_occurrences, target_occurrences, result)
    return result


def _compute_paths_rec(
    expr: Expr,
    current_path: Tuple[str, ...],
    current_depth: int,
    var_occurrences: Dict[int, List[int]],
    target_occurrences: Dict[int, int],
    result: Dict[Tuple[int, int], Tuple[str, ...]],
) -> None:
    """Recursive helper to compute all path signatures in one pass."""
    if isinstance(expr, Var):
        uid = expr.uid
        if uid in var_occurrences:
            occ_list = var_occurrences[uid]
            target_idx = target_occurrences[uid]
            if target_idx < len(occ_list):
                result[(uid, occ_list[target_idx])] = current_path + ("Var:placeholder",)
            target_occurrences[uid] += 1
        return
    
    if isinstance(expr, BinOp):
        op_path = current_path + (f"BinOp:{expr.op}:left",)
        _compute_paths_rec(expr.left, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        op_path = current_path + (f"BinOp:{expr.op}:right",)
        _compute_paths_rec(expr.right, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        return
    
    if isinstance(expr, UnOp):
        op_path = current_path + (f"UnOp:{expr.op}",)
        _compute_paths_rec(expr.operand, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        return
    
    if isinstance(expr, Func):
        op_path = current_path + (f"Func:{expr.op}",)
        _compute_paths_rec(expr.arg, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        return
    
    if isinstance(expr, Func2):
        op_path = current_path + (f"Func2:{expr.name}:left",)
        _compute_paths_rec(expr.arg1, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        op_path = current_path + (f"Func2:{expr.name}:right",)
        _compute_paths_rec(expr.arg2, op_path, current_depth + 1, var_occurrences, target_occurrences, result)
        return


def _replace_all_vars_with_placeholder(expr: Expr, target_uid: int, placeholder: Var) -> Expr:
    """Replace all occurrences of a variable with a placeholder."""
    if isinstance(expr, Var):
        if expr.uid == target_uid:
            return placeholder
        return expr

    if isinstance(expr, BinOp):
        return BinOp(
            _replace_all_vars_with_placeholder(expr.left, target_uid, placeholder),
            expr.op,
            _replace_all_vars_with_placeholder(expr.right, target_uid, placeholder),
        )

    if isinstance(expr, UnOp):
        return UnOp(expr.op, _replace_all_vars_with_placeholder(expr.operand, target_uid, placeholder))

    if isinstance(expr, Func):
        return Func(_replace_all_vars_with_placeholder(expr.arg, target_uid, placeholder), expr.op)

    if isinstance(expr, Func2):
        return Func2(
            expr.name,
            _replace_all_vars_with_placeholder(expr.arg1, target_uid, placeholder),
            _replace_all_vars_with_placeholder(expr.arg2, target_uid, placeholder),
        )

    return expr


def _replace_all_vars_same_placeholder(expr: Expr, placeholder: Var) -> Expr:
    """Replace ALL variables in expr with the same placeholder."""
    if isinstance(expr, Var):
        return placeholder

    if isinstance(expr, BinOp):
        return BinOp(
            _replace_all_vars_same_placeholder(expr.left, placeholder),
            expr.op,
            _replace_all_vars_same_placeholder(expr.right, placeholder),
        )

    if isinstance(expr, UnOp):
        return UnOp(expr.op, _replace_all_vars_same_placeholder(expr.operand, placeholder))

    if isinstance(expr, Func):
        return Func(_replace_all_vars_same_placeholder(expr.arg, placeholder), expr.op)

    if isinstance(expr, Func2):
        return Func2(
            expr.name,
            _replace_all_vars_same_placeholder(expr.arg1, placeholder),
            _replace_all_vars_same_placeholder(expr.arg2, placeholder),
        )

    return expr


def _replace_all_vars_with_name_placeholder(expr: Expr) -> Expr:
    """Replace each variable with a placeholder named after the variable's name.
    This allows distinguishing structurally identical equations that contain
    differently-named variables (e.g. Pf vs Pt equations).
    """
    if isinstance(expr, Var):
        return Var(name=f"PH_{expr.name}")

    if isinstance(expr, BinOp):
        return BinOp(
            _replace_all_vars_with_name_placeholder(expr.left),
            expr.op,
            _replace_all_vars_with_name_placeholder(expr.right),
        )

    if isinstance(expr, UnOp):
        return UnOp(expr.op, _replace_all_vars_with_name_placeholder(expr.operand))

    if isinstance(expr, Func):
        return Func(_replace_all_vars_with_name_placeholder(expr.arg), expr.op)

    if isinstance(expr, Func2):
        return Func2(
            expr.name,
            _replace_all_vars_with_name_placeholder(expr.arg1),
            _replace_all_vars_with_name_placeholder(expr.arg2),
        )

    return expr


class VariableAlignmentEngine:
    """Computes exact 1-to-1 mapping between variables of equivalent systems."""

    def __init__(self, sys1: List[Expr], sys2: List[Expr]):
        self.sys1 = sys1
        self.sys2 = sys2
        self.sys1_hashes: Set[str] = set()
        self.sys2_hashes: Set[str] = set()
        self._var_signatures_sys1: Dict[int, List[VariableSignature]] = {}
        self._var_signatures_sys2: Dict[int, List[VariableSignature]] = {}
        self._candidate_map: Dict[int, Set[int]] = {}
        self._mapping: Dict[int, int] = {}
        self._norm_sys1: List[Expr] = []
        self._norm_sys2: List[Expr] = []

    def compute_mapping(self) -> Dict[int, int]:
        """Main entry point. Computes the variable mapping."""
        self._var_signatures_sys1.clear()
        self._var_signatures_sys2.clear()
        self._candidate_map.clear()
        self._mapping.clear()

        self._normalize_and_check_equivalence()
        self._extract_signatures()
        self._build_candidate_map()

        if not self._backtrack_match():
            return {}

        if self._validate_mapping():
            return dict(self._mapping)
        return {}

    def _normalize_and_check_equivalence(self) -> bool:
        """Normalize systems."""
        self._norm_sys1 = [expand_and_canonicalize(eq) for eq in self.sys1]
        self._norm_sys2 = [expand_and_canonicalize(eq) for eq in self.sys2]
        self.sys1_hashes = {structural_hash(eq) for eq in self._norm_sys1}
        self.sys2_hashes = {structural_hash(eq) for eq in self._norm_sys2}
        return True

    def _extract_signatures(self) -> None:
        """Extract signatures for all variables in both systems."""
        for eq in self.sys1:
            self._extract_signatures_from_equation(eq, self._var_signatures_sys1)

        for eq in self.sys2:
            self._extract_signatures_from_equation(eq, self._var_signatures_sys2)

    def _extract_signatures_from_equation(
        self,
        eq: Expr,
        signature_dict: Dict[int, List[VariableSignature]],
    ) -> None:
        """Extract signatures for all Var nodes in an equation."""
        all_occurrences = _get_all_var_occurrences(eq)
        if not all_occurrences:
            return

        # Use name-based placeholders so equations with differently-named variables
        # (e.g. Pf vs Pt) produce different context hashes, even if they are
        # structurally identical after blanket placeholder replacement.
        placeholder = Var(name=PLACEHOLDER_NAME)
        all_name_placeholder_expr = _replace_all_vars_with_name_placeholder(eq)
        all_placeholder_hash = structural_hash(canonical(all_name_placeholder_expr))
        
        all_paths = _compute_all_path_signatures(eq, all_occurrences)
        
        for var_uid, occurrences in all_occurrences.items():
            for occ_idx in occurrences:
                path_sig = all_paths.get((var_uid, occ_idx))
                if path_sig is None:
                    continue

                depth = len(path_sig)
                sig = VariableSignature(
                    var_uid=var_uid,
                    occurrence_idx=occ_idx,
                    context_hash=all_placeholder_hash,
                    depth=depth,
                    path_signature=path_sig,
                )

                if var_uid not in signature_dict:
                    signature_dict[var_uid] = []
                signature_dict[var_uid].append(sig)

    def _compute_context_hash(
        self,
        eq: Expr,
        var_uid: int,
        occurrence_idx: int,
        placeholder: Var,
    ) -> str:
        """Compute context hash by replacing var with placeholder and hashing."""
        modified_expr = _replace_all_vars_same_placeholder(eq, placeholder)
        return structural_hash(canonical(modified_expr))

    def _collect_vars_in_expr(self, expr: Expr) -> Set[int]:
        """Collect all variable uids in an expression."""
        vars_set: Set[int] = set()
        self._collect_vars_recursive(expr, vars_set)
        return vars_set

    def _collect_vars_recursive(self, expr: Expr, result: Set[int]) -> None:
        """Recursively collect variable uids."""
        if isinstance(expr, Var):
            result.add(expr.uid)
            return

        if isinstance(expr, BinOp):
            self._collect_vars_recursive(expr.left, result)
            self._collect_vars_recursive(expr.right, result)
            return

        if isinstance(expr, UnOp):
            self._collect_vars_recursive(expr.operand, result)
            return

        if isinstance(expr, Func):
            self._collect_vars_recursive(expr.arg, result)
            return

        if isinstance(expr, Func2):
            self._collect_vars_recursive(expr.arg1, result)
            self._collect_vars_recursive(expr.arg2, result)
            return

    def _build_candidate_map(self) -> None:
        """Build bipartite matching candidates based on signature equality."""
        for uid1, sigs1 in self._var_signatures_sys1.items():
            candidates: Set[int] = set()
            for uid2, sigs2 in self._var_signatures_sys2.items():
                if self._signatures_match(sigs1, sigs2):
                    candidates.add(uid2)
            if candidates:
                self._candidate_map[uid1] = candidates

    def _signatures_match(
        self,
        sigs1: List[VariableSignature],
        sigs2: List[VariableSignature],
    ) -> bool:
        """Check if two sets of signatures represent the same variable positions."""
        if len(sigs1) != len(sigs2):
            return False

        sigs1_norm = sorted(sigs1, key=lambda s: (s.occurrence_idx, s.context_hash))
        sigs2_norm = sorted(sigs2, key=lambda s: (s.occurrence_idx, s.context_hash))

        for s1, s2 in zip(sigs1_norm, sigs2_norm):
            if s1 != s2:
                return False

        return True

    def _backtrack_match(self) -> bool:
        """Perform backtracking to find valid 1-to-1 mapping."""
        if not self._candidate_map:
            return True

        sorted_vars = sorted(
            self._candidate_map.keys(),
            key=lambda u: (len(self._candidate_map[u]), u),
        )

        assigned: Dict[int, int] = {}
        used_sys2: Set[int] = set()

        return self._recursive_match(sorted_vars, 0, assigned, used_sys2)

    def _recursive_match(
        self,
        sorted_vars: List[int],
        index: int,
        assigned: Dict[int, int],
        used_sys2: Set[int],
    ) -> bool:
        """Recursive backtracking with MRV heuristic."""
        if index == len(sorted_vars):
            self._mapping = dict(assigned)
            return True

        var_uid = sorted_vars[index]
        candidates = self._candidate_map[var_uid]

        sorted_candidates = sorted(candidates - used_sys2)

        for candidate_uid in sorted_candidates:
            assigned[var_uid] = candidate_uid
            used_sys2.add(candidate_uid)

            if self._partial_validate(assigned):
                if self._recursive_match(sorted_vars, index + 1, assigned, used_sys2):
                    return True

            del assigned[var_uid]
            used_sys2.remove(candidate_uid)

        return False

    def _partial_validate(self, partial_mapping: Dict[int, int]) -> bool:
        """Validate partial mapping for injectivity."""
        return len(partial_mapping) == len(set(partial_mapping.values()))

    def _validate_mapping(self) -> bool:
        """Full validation of the computed mapping."""
        return len(self._mapping) == len(set(self._mapping.values()))


def align_variables(sys1: List[Expr], sys2: List[Expr]) -> Dict[int, int]:
    """
    Compute exact 1-to-1 variable mapping between two equivalent systems.

    Args:
        sys1: First system of equations
        sys2: Second system of equations

    Returns:
        Dict[int, int]: Mapping from sys1 variable uids to sys2 variable uids.
                        Empty dict if mapping fails.
    """
    engine = VariableAlignmentEngine(sys1, sys2)
    return engine.compute_mapping()


__all__ = [
    "VariableAlignmentEngine",
    "VariableSignature",
    "align_variables",
]
