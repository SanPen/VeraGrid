# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone tests for VariableAlignmentEngine.
This test file imports ONLY the minimal classes needed.
"""

import sys
import os
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, '/home/marina/PycharmProjects/VeraGrid/src')


class Const:
    __slots__ = ("value", "name", "uid")
    def __init__(self, value=None, uid=None, name=""):
        self.uid = uid if uid is not None else id(self)
        self.value = value
        self.name = name
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return self.__str__()


class Var:
    __slots__ = ("name", "uid")
    def __init__(self, name, uid=None):
        self.name = name
        self.uid = uid if uid is not None else id(self)
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name


class BinOp:
    __slots__ = ("op", "left", "right", "uid")
    def __init__(self, left, op, right, uid=None):
        self.op = op
        self.left = left
        self.right = right
        self.uid = uid if uid is not None else id(self)
    def __str__(self):
        return f"({self.left} {self.op} {self.right})"
    def __repr__(self):
        return self.__str__()


class UnOp:
    __slots__ = ("op", "operand", "uid")
    def __init__(self, op, operand, uid=None):
        self.op = op
        self.operand = operand
        self.uid = uid if uid is not None else id(self)
    def __str__(self):
        return f"{self.op}({self.operand})"
    def __repr__(self):
        return self.__str__()


class Func:
    __slots__ = ("op", "arg", "uid")
    def __init__(self, arg, op="", uid=None):
        self.op = op
        self.arg = arg
        self.uid = uid if uid is not None else id(self)
    def __str__(self):
        return f"{self.op}({self.arg})"
    def __repr__(self):
        return self.__str__()


class Func2:
    __slots__ = ("name", "arg1", "arg2", "uid")
    def __init__(self, name, arg1, arg2, uid=None):
        self.name = name
        self.arg1 = arg1
        self.arg2 = arg2
        self.uid = uid if uid is not None else id(self)
    def __str__(self):
        return f"{self.name}({self.arg1}, {self.arg2})"
    def __repr__(self):
        return self.__str__()


def _to_expr(val):
    if isinstance(val, (int, float)):
        return Const(val)
    return val


def _add(self, other):
    return BinOp(self, "+", _to_expr(other))

def _radd(self, other):
    return BinOp(_to_expr(other), "+", self)

def _sub(self, other):
    return BinOp(self, "-", _to_expr(other))

def _rsub(self, other):
    return BinOp(_to_expr(other), "-", self)

def _mul(self, other):
    return BinOp(self, "*", _to_expr(other))

def _rmul(self, other):
    return BinOp(_to_expr(other), "*", self)

def _truediv(self, other):
    return BinOp(self, "/", _to_expr(other))

def _rtruediv(self, other):
    return BinOp(_to_expr(other), "/", self)

def _pow(self, other):
    return BinOp(self, "**", _to_expr(other))

def _rpow(self, other):
    return BinOp(_to_expr(other), "**", self)

def _neg(self):
    return UnOp("-", self)

Const.__add__ = _add
Const.__radd__ = _radd
Const.__sub__ = _sub
Const.__rsub__ = _rsub
Const.__mul__ = _mul
Const.__rmul__ = _rmul
Const.__truediv__ = _truediv
Const.__rtruediv__ = _rtruediv
Const.__pow__ = _pow
Const.__rpow__ = _rpow
Const.__neg__ = _neg

Var.__add__ = _add
Var.__radd__ = _radd
Var.__sub__ = _sub
Var.__rsub__ = _rsub
Var.__mul__ = _mul
Var.__rmul__ = _rmul
Var.__truediv__ = _truediv
Var.__rtruediv__ = _rtruediv
Var.__pow__ = _pow
Var.__rpow__ = _rpow
Var.__neg__ = _neg

BinOp.__add__ = _add
BinOp.__radd__ = _radd
BinOp.__sub__ = _sub
BinOp.__rsub__ = _rsub
BinOp.__mul__ = _mul
BinOp.__rmul__ = _rmul
BinOp.__truediv__ = _truediv
BinOp.__rtruediv__ = _rtruediv
BinOp.__pow__ = _pow
BinOp.__rpow__ = _rpow
BinOp.__neg__ = _neg

UnOp.__add__ = _add
UnOp.__radd__ = _radd
UnOp.__sub__ = _sub
UnOp.__rsub__ = _rsub
UnOp.__mul__ = _mul
UnOp.__rmul__ = _rmul
UnOp.__truediv__ = _truediv
UnOp.__rtruediv__ = _rtruediv
UnOp.__pow__ = _pow
UnOp.__rpow__ = _rpow
UnOp.__neg__ = _neg


CommutativeOps = {"+", "*"}

def _canonical_const(value):
    if value is None:
        return ("none", None)
    if isinstance(value, complex):
        return ("complex", (float(value.real), float(value.imag)))
    if isinstance(value, float):
        if value == int(value):
            return ("int", int(value))
        return ("float", value)
    return (type(value).__name__, value)


def _flatten_assoc(expr, op):
    if isinstance(expr, BinOp) and expr.op == op:
        return _flatten_assoc(expr.left, op) + _flatten_assoc(expr.right, op)
    return [expr]


def _sort_exprs(exprs, key_func):
    return sorted(exprs, key=key_func)


def _hash_expr(expr):
    if isinstance(expr, Const):
        type_key, norm_val = _canonical_const(expr.value)
        h = hashlib.sha256()
        h.update(f"Const:{type_key}:{norm_val}".encode())
        return h.hexdigest()

    if isinstance(expr, Var):
        h = hashlib.sha256()
        h.update(f"Var:{expr.name}".encode())
        return h.hexdigest()

    if isinstance(expr, UnOp):
        h = hashlib.sha256()
        h.update(f"UnOp:{expr.op}:{_hash_expr(expr.operand)}".encode())
        return h.hexdigest()

    if isinstance(expr, BinOp):
        h = hashlib.sha256()
        child_hash = _hash_expr(expr.left) + _hash_expr(expr.right)
        if expr.op in CommutativeOps:
            child_hash = "".join(sorted(child_hash))
        h.update(f"BinOp:{expr.op}:{child_hash}".encode())
        return h.hexdigest()

    if isinstance(expr, Func):
        h = hashlib.sha256()
        h.update(f"Func:{expr.op}:{_hash_expr(expr.arg)}".encode())
        return h.hexdigest()

    if isinstance(expr, Func2):
        h = hashlib.sha256()
        arg_hash = _hash_expr(expr.arg1) + _hash_expr(expr.arg2)
        if expr.name in {"min", "max", "atan2"}:
            arg_hash = "".join(sorted([_hash_expr(expr.arg1), _hash_expr(expr.arg2)]))
        h.update(f"Func2:{expr.name}:{arg_hash}".encode())
        return h.hexdigest()

    raise TypeError(f"Unknown expression type: {type(expr)}")


def _build_sum(terms):
    sorted_terms = _sort_exprs(terms, _hash_expr)
    result = sorted_terms[0]
    for t in sorted_terms[1:]:
        result = BinOp(result, "+", t)
    return result


def _build_product(factors):
    sorted_factors = _sort_exprs(factors, _hash_expr)
    result = sorted_factors[0]
    for f in sorted_factors[1:]:
        result = BinOp(result, "*", f)
    return result


def _eval_func(op, value):
    import math
    if op == "sin":
        return math.sin(value)
    if op == "cos":
        return math.cos(value)
    if op == "tan":
        return math.tan(value)
    if op == "exp":
        return math.exp(value)
    if op == "log":
        return math.log(value)
    if op == "sqrt":
        return math.sqrt(value)
    if op == "abs":
        return abs(value)
    if op == "floor":
        return math.floor(value)
    if op == "ceil":
        return math.ceil(value)
    if op == "heaviside":
        return 0.0 if value <= 0 else 1.0
    raise ValueError(f"Cannot evaluate function {op}")


def canonical(expr):
    if isinstance(expr, Const):
        return Const(expr.value)

    if isinstance(expr, Var):
        return Var(expr.name)

    if isinstance(expr, UnOp):
        canonical_operand = canonical(expr.operand)
        if expr.op == "-":
            if isinstance(canonical_operand, Const):
                return Const(-canonical_operand.value)
            if isinstance(canonical_operand, UnOp) and canonical_operand.op == "-":
                return canonical_operand.operand
            return UnOp("-", canonical_operand)
        return UnOp(expr.op, canonical_operand)

    if isinstance(expr, BinOp):
        left = canonical(expr.left)
        right = canonical(expr.right)

        if expr.op == "+":
            terms = _flatten_assoc(BinOp(left, "+", right), "+")
            const_sum = 0.0
            non_const_terms = []
            for t in terms:
                if isinstance(t, Const) and t.value is not None:
                    const_sum += t.value
                else:
                    non_const_terms.append(t)
            if const_sum != 0.0 or not non_const_terms:
                non_const_terms.append(Const(const_sum))
            if len(non_const_terms) == 1:
                return non_const_terms[0]
            return _build_sum(non_const_terms)

        if expr.op == "*":
            factors = _flatten_assoc(BinOp(left, "*", right), "*")
            zero_found = False
            const_product = 1.0
            non_const_factors = []
            for f in factors:
                if isinstance(f, Const) and f.value is not None:
                    if f.value == 0:
                        zero_found = True
                        break
                    const_product *= f.value
                else:
                    non_const_factors.append(f)
            if zero_found:
                return Const(0)
            if const_product != 1.0:
                non_const_factors.append(Const(const_product))
            if not non_const_factors:
                return Const(1)
            if len(non_const_factors) == 1:
                return non_const_factors[0]
            return _build_product(non_const_factors)

        if expr.op == "-":
            if isinstance(right, Const) and isinstance(left, Const):
                return Const(left.value - right.value)
            if isinstance(right, Const) and right.value == 0:
                return left
            if isinstance(left, Const) and left.value == 0:
                return UnOp("-", right)
            return BinOp(left, "-", right)

        if expr.op == "/":
            if isinstance(left, Const) and isinstance(right, Const):
                if right.value != 0:
                    return Const(left.value / right.value)
            if isinstance(right, Const) and right.value == 1:
                return left
            if isinstance(left, Const) and left.value == 0:
                return Const(0)
            return BinOp(left, "/", right)

        if expr.op == "**":
            if isinstance(right, Const) and right.value == 0:
                return Const(1)
            if isinstance(right, Const) and right.value == 1:
                return left
            if isinstance(left, Const) and isinstance(right, Const):
                return Const(left.value ** right.value)
            return BinOp(left, "**", right)

        return BinOp(left, expr.op, right)

    if isinstance(expr, Func):
        arg_canon = canonical(expr.arg)
        if isinstance(arg_canon, Const) and arg_canon.value is not None:
            try:
                result = _eval_func(expr.op, arg_canon.value)
                return Const(result)
            except (ValueError, TypeError):
                pass
        return Func(arg_canon, expr.op)

    return expr


def structural_hash(expr):
    canon = canonical(expr)
    return _hash_expr(canon)


def _get_product_vars(expr):
    if isinstance(expr, Var):
        return [expr.name]
    if isinstance(expr, BinOp) and expr.op == "*":
        return _get_product_vars(expr.left) + _get_product_vars(expr.right)
    return []


def _get_sorted_vars_key(expr):
    return tuple(sorted(_get_product_vars(expr)))


def _get_const_from_term(expr):
    if isinstance(expr, Const):
        return expr.value if expr.value is not None else 0.0
    if isinstance(expr, BinOp) and expr.op == "*":
        consts = []
        if isinstance(expr.left, Const) and expr.left.value is not None:
            consts.append(expr.left.value)
        if isinstance(expr.right, Const) and expr.right.value is not None:
            consts.append(expr.right.value)
        if consts:
            result = 1.0
            for c in consts:
                result *= c
            return result
    return 1.0


def _get_non_const_part(expr):
    if isinstance(expr, Const):
        return Const(1)
    if isinstance(expr, Var):
        return expr
    if isinstance(expr, BinOp) and expr.op == "*":
        parts = []
        if isinstance(expr.left, Const):
            pass
        else:
            parts.append(_get_non_const_part(expr.left))
        if isinstance(expr.right, Const):
            pass
        else:
            parts.append(_get_non_const_part(expr.right))
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return BinOp(parts[0], "*", parts[1])
        return Const(1)
    return expr


def _expand_power(expr):
    if not isinstance(expr, BinOp) or expr.op != "**":
        return expr
    
    base = expr.left
    exponent = expr.right
    
    if isinstance(exponent, Const) and isinstance(exponent.value, (int, float)):
        n = int(exponent.value)
        if n == 2:
            return canonical(BinOp(base, "*", base))
        if n >= 2 and n <= 10:
            result = base
            for _ in range(n - 1):
                result = canonical(BinOp(result, "*", base))
            return result
    
    return expr


def _collect_all_terms(expr):
    if isinstance(expr, BinOp) and expr.op == "+":
        return _collect_all_terms(expr.left) + _collect_all_terms(expr.right)
    return [expr]


def _merge_terms_list(terms):
    term_map = {}
    
    for term in terms:
        key = _get_sorted_vars_key(term)
        const = _get_const_from_term(term) or 0.0
        
        if key in term_map:
            existing_const, _ = term_map[key]
            term_map[key] = (existing_const + const, term)
        else:
            term_map[key] = (const, term)
    
    if not term_map:
        return Const(0)
    
    merged = []
    for const, term in term_map.values():
        if const == 0:
            continue
        non_const = _get_non_const_part(term)
        if isinstance(non_const, Const):
            merged.append(Const(const))
        elif const == 1.0:
            merged.append(non_const)
        else:
            merged.append(BinOp(Const(const), "*", non_const))
    
    merged.sort(key=_hash_expr)
    result = merged[0]
    for t in merged[1:]:
        result = BinOp(result, "+", t)
    return result


def _combine_like_terms(expr):
    if not isinstance(expr, BinOp) or expr.op != "+":
        return expr
    
    all_terms = _collect_all_terms(expr)
    return _merge_terms_list(all_terms)


def _expand_product_sum(expr):
    if not isinstance(expr, BinOp):
        return expr
    
    left = expr.left
    right = expr.right
    op = expr.op
    
    if op == "**":
        if isinstance(right, Const) and isinstance(right.value, (int, float)):
            n = int(right.value)
            if n == 2 and isinstance(left, BinOp) and left.op == "+":
                a = left.left
                b = left.right
                a_sq = _expand_power(BinOp(a, "**", Const(2)))
                b_sq = _expand_power(BinOp(b, "**", Const(2)))
                ab = BinOp(a, "*", b)
                ba = BinOp(b, "*", a)
                two_ab = BinOp(Const(2), "*", ab)
                result = BinOp(BinOp(a_sq, "+", two_ab), "+", b_sq)
                return _combine_like_terms(result)
            if n >= 2 and n <= 10 and isinstance(left, BinOp) and left.op == "+":
                result = left
                for _ in range(n - 1):
                    result = BinOp(result, "*", left)
                return _combine_like_terms(expand(result))
    
    if op == "*":
        left_exp = _expand_product_sum(left)
        right_exp = _expand_product_sum(right)
        
        if isinstance(left_exp, BinOp) and left_exp.op == "+":
            term1 = BinOp(left_exp.left, "*", right_exp)
            term2 = BinOp(left_exp.right, "*", right_exp)
            result = BinOp(term1, "+", term2)
            return _combine_like_terms(result)
        
        if isinstance(right_exp, BinOp) and right_exp.op == "+":
            term1 = BinOp(left_exp, "*", right_exp.left)
            term2 = BinOp(left_exp, "*", right_exp.right)
            result = BinOp(term1, "+", term2)
            return _combine_like_terms(result)
        
        if isinstance(left_exp, BinOp) and left_exp.op == "-":
            term1 = BinOp(left_exp.left, "*", right_exp)
            term2 = BinOp(left_exp.right, "*", right_exp)
            return canonical(BinOp(term1, "-", term2))
        
        if isinstance(right_exp, BinOp) and right_exp.op == "-":
            term1 = BinOp(left_exp, "*", right_exp.left)
            term2 = BinOp(left_exp, "*", right_exp.right)
            return canonical(BinOp(term1, "-", term2))
    
    return expr


def _try_expand(expr):
    if isinstance(expr, BinOp):
        left_expanded = _try_expand(expr.left)
        right_expanded = _try_expand(expr.right)
        
        new_expr = BinOp(left_expanded, expr.op, right_expanded)
        
        expanded = _expand_product_sum(new_expr)
        if expanded is not new_expr:
            return _combine_like_terms(expanded)
        
        if new_expr.op == "**":
            pow_expanded = _expand_power(new_expr)
            if pow_expanded is not new_expr:
                return _combine_like_terms(pow_expanded)
        
        return _combine_like_terms(new_expr)
    
    if isinstance(expr, UnOp):
        operand_expanded = _try_expand(expr.operand)
        if operand_expanded is not expr.operand:
            return UnOp(expr.op, operand_expanded)
        return expr
    
    if isinstance(expr, Func):
        arg_expanded = _try_expand(expr.arg)
        if arg_expanded is not expr.arg:
            return Func(arg_expanded, expr.op)
        return expr
    
    return expr


def expand(expr):
    result = expr
    for _ in range(20):
        expanded = _try_expand(result)
        if str(expanded) == str(result):
            break
        result = expanded
    return result


def expand_and_canonicalize(expr):
    expanded = expand(expr)
    result = expanded
    for _ in range(20):
        canonicalized = canonical(result)
        if str(canonicalized) == str(result):
            break
        result = canonicalized
        
        expanded2 = expand(result)
        if str(expanded2) == str(result):
            break
        result = expanded2
    
    return result


class DAGNode:
    __slots__ = ("op", "children", "structural_hash", "_expr")

    def __init__(self, op, children, structural_hash, expr=None):
        self.op = op
        self.children = children
        self.structural_hash = structural_hash
        self._expr = expr


def to_dag(expr, memo=None):
    if memo is None:
        memo = {}
    canon = canonical(expr)
    return _to_dag_recursive(canon, memo)


def _to_dag_recursive(expr, memo):
    h = _hash_expr(expr)
    if h in memo:
        return memo[h]
    if isinstance(expr, Const):
        node = DAGNode(op="Const", children=[], structural_hash=h, expr=expr)
        memo[h] = node
        return node
    if isinstance(expr, Var):
        node = DAGNode(op=f"Var:{expr.name}", children=[], structural_hash=h, expr=expr)
        memo[h] = node
        return node
    if isinstance(expr, UnOp):
        child = _to_dag_recursive(expr.operand, memo)
        node = DAGNode(op=f"UnOp:{expr.op}", children=[child], structural_hash=h, expr=expr)
        memo[h] = node
        return node
    if isinstance(expr, BinOp):
        left = _to_dag_recursive(expr.left, memo)
        right = _to_dag_recursive(expr.right, memo)
        children = [left, right]
        if expr.op in CommutativeOps:
            children = sorted(children, key=lambda n: n.structural_hash)
        node = DAGNode(op=f"BinOp:{expr.op}", children=children, structural_hash=h, expr=expr)
        memo[h] = node
        return node
    if isinstance(expr, Func):
        arg = _to_dag_recursive(expr.arg, memo)
        node = DAGNode(op=f"Func:{expr.op}", children=[arg], structural_hash=h, expr=expr)
        memo[h] = node
        return node
    if isinstance(expr, Func2):
        arg1 = _to_dag_recursive(expr.arg1, memo)
        arg2 = _to_dag_recursive(expr.arg2, memo)
        children = [arg1, arg2]
        if expr.name in {"min", "max", "atan2"}:
            children = sorted(children, key=lambda n: n.structural_hash)
        node = DAGNode(op=f"Func2:{expr.name}", children=children, structural_hash=h, expr=expr)
        memo[h] = node
        return node
    raise TypeError(f"Unknown expression type: {type(expr)}")


PLACEHOLDER_NAME = "_"


class VariableSignature:
    __slots__ = ("var_uid", "occurrence_idx", "context_hash", "depth", "path_signature")

    def __init__(self, var_uid, occurrence_idx, context_hash, depth, path_signature):
        self.var_uid = var_uid
        self.occurrence_idx = occurrence_idx
        self.context_hash = context_hash
        self.depth = depth
        self.path_signature = path_signature

    def __hash__(self):
        return hash((self.var_uid, self.occurrence_idx, self.context_hash, self.depth, self.path_signature))

    def __eq__(self, other):
        if not isinstance(other, VariableSignature):
            return False
        return (self.occurrence_idx == other.occurrence_idx
                and self.context_hash == other.context_hash
                and self.depth == other.depth
                and self.path_signature == other.path_signature)

    def __repr__(self):
        return f"VarSig(uid={self.var_uid}, occ={self.occurrence_idx}, ctx={self.context_hash[:6]}, depth={self.depth})"


def _replace_var_at_position(expr, target_uid, placeholder, occurrence_counter):
    counter = occurrence_counter[0]
    if isinstance(expr, Var):
        if expr.uid == target_uid:
            occurrence_counter[0] += 1
            return placeholder, counter
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


def _get_var_occurrences(expr, var_uid):
    occurrences = []
    _collect_occurrences(expr, var_uid, occurrences)
    return occurrences


def _collect_occurrences(expr, var_uid, result):
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


def _compute_path_signature(expr, var_uid, target_occurrence, current_path, current_depth):
    if isinstance(expr, Var):
        if expr.uid == var_uid:
            return current_path + ("Var:placeholder",)
        return None
    if isinstance(expr, BinOp):
        op_path = current_path + (f"BinOp:{expr.op}:left",)
        left_result = _compute_path_signature(expr.left, var_uid, target_occurrence, op_path, current_depth + 1)
        if left_result is not None:
            return left_result
        op_path = current_path + (f"BinOp:{expr.op}:right",)
        right_result = _compute_path_signature(expr.right, var_uid, target_occurrence, op_path, current_depth + 1)
        return right_result
    if isinstance(expr, UnOp):
        op_path = current_path + (f"UnOp:{expr.op}",)
        return _compute_path_signature(expr.operand, var_uid, target_occurrence, op_path, current_depth + 1)
    if isinstance(expr, Func):
        op_path = current_path + (f"Func:{expr.op}",)
        return _compute_path_signature(expr.arg, var_uid, target_occurrence, op_path, current_depth + 1)
    if isinstance(expr, Func2):
        op_path = current_path + (f"Func2:{expr.name}:left",)
        left_result = _compute_path_signature(expr.arg1, var_uid, target_occurrence, op_path, current_depth + 1)
        if left_result is not None:
            return left_result
        op_path = current_path + (f"Func2:{expr.name}:right",)
        return _compute_path_signature(expr.arg2, var_uid, target_occurrence, op_path, current_depth + 1)
    return None


class VariableAlignmentEngine:
    def __init__(self, sys1, sys2):
        self.sys1 = sys1
        self.sys2 = sys2
        self.sys1_hashes = set()
        self.sys2_hashes = set()
        self._var_signatures_sys1 = {}
        self._var_signatures_sys2 = {}
        self._candidate_map = {}
        self._mapping = {}
        self._norm_sys1 = []
        self._norm_sys2 = []

    def compute_mapping(self):
        self._var_signatures_sys1.clear()
        self._var_signatures_sys2.clear()
        self._candidate_map.clear()
        self._mapping.clear()

        if not self._normalize_and_check_equivalence():
            return {}

        self._extract_signatures()
        self._build_candidate_map()

        if not self._backtrack_match():
            return {}

        if self._validate_mapping():
            return dict(self._mapping)
        return {}

    def _normalize_and_check_equivalence(self):
        self._norm_sys1 = [expand_and_canonicalize(eq) for eq in self.sys1]
        self._norm_sys2 = [expand_and_canonicalize(eq) for eq in self.sys2]
        self.sys1_hashes = {structural_hash(eq) for eq in self._norm_sys1}
        self.sys2_hashes = {structural_hash(eq) for eq in self._norm_sys2}
        return True

    def _extract_signatures(self):
        for eq in self.sys1:
            self._extract_signatures_from_equation(eq, self._var_signatures_sys1)
        for eq in self.sys2:
            self._extract_signatures_from_equation(eq, self._var_signatures_sys2)

    def _extract_signatures_from_equation(self, eq, signature_dict):
        all_vars = self._collect_vars_in_expr(eq)
        placeholder = Var(name=PLACEHOLDER_NAME)

        for var_uid in all_vars:
            occurrences = _get_var_occurrences(eq, var_uid)
            for occ_idx in occurrences:
                context_hash = self._compute_context_hash(eq, var_uid, occ_idx, placeholder)
                path_sig = _compute_path_signature(eq, var_uid, occ_idx, (), 0)
                if path_sig is None:
                    continue
                depth = len(path_sig)
                sig = VariableSignature(
                    var_uid=var_uid,
                    occurrence_idx=occ_idx,
                    context_hash=context_hash,
                    depth=depth,
                    path_signature=path_sig,
                )
                if var_uid not in signature_dict:
                    signature_dict[var_uid] = []
                signature_dict[var_uid].append(sig)

    def _compute_context_hash(self, eq, var_uid, occurrence_idx, placeholder):
        modified_expr = _replace_all_vars_same_placeholder(eq, placeholder)
        return structural_hash(canonical(modified_expr))

    def _collect_vars_in_expr(self, expr):
        vars_set = set()
        self._collect_vars_recursive(expr, vars_set)
        return vars_set

    def _collect_vars_recursive(self, expr, result):
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

    def _build_candidate_map(self):
        for uid1, sigs1 in self._var_signatures_sys1.items():
            candidates = set()
            for uid2, sigs2 in self._var_signatures_sys2.items():
                if self._signatures_match(sigs1, sigs2):
                    candidates.add(uid2)
            if candidates:
                self._candidate_map[uid1] = candidates

    def _signatures_match(self, sigs1, sigs2):
        if len(sigs1) != len(sigs2):
            return False
        sigs1_norm = sorted(sigs1, key=lambda s: (s.occurrence_idx, s.context_hash))
        sigs2_norm = sorted(sigs2, key=lambda s: (s.occurrence_idx, s.context_hash))
        for s1, s2 in zip(sigs1_norm, sigs2_norm):
            if s1 != s2:
                return False
        return True

    def _backtrack_match(self):
        if not self._candidate_map:
            return True
        sorted_vars = sorted(self._candidate_map.keys(), key=lambda u: (len(self._candidate_map[u]), u))
        assigned = {}
        used_sys2 = set()
        return self._recursive_match(sorted_vars, 0, assigned, used_sys2)

    def _recursive_match(self, sorted_vars, index, assigned, used_sys2):
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

    def _partial_validate(self, partial_mapping):
        return len(partial_mapping) == len(set(partial_mapping.values()))

    def _validate_mapping(self):
        if len(self._mapping) != len(set(self._mapping.values())):
            return False
        return True

    def _verify_substitution(self):
        for eq1 in self._norm_sys1:
            substituted = self._substitute_variables(eq1, self._mapping)
            sub_hash = structural_hash(substituted)
            if sub_hash not in self.sys2_hashes:
                return False
        return True

    def _substitute_variables(self, expr, mapping):
        if isinstance(expr, Var):
            if expr.uid in mapping:
                return Var(name=expr.name, uid=mapping[expr.uid])
            return Var(name=expr.name, uid=expr.uid)
        if isinstance(expr, BinOp):
            return BinOp(
                self._substitute_variables(expr.left, mapping),
                expr.op,
                self._substitute_variables(expr.right, mapping),
            )
        if isinstance(expr, UnOp):
            return UnOp(expr.op, self._substitute_variables(expr.operand, mapping))
        if isinstance(expr, Func):
            return Func(self._substitute_variables(expr.arg, mapping), expr.op)
        if isinstance(expr, Func2):
            return Func2(
                expr.name,
                self._substitute_variables(expr.arg1, mapping),
                self._substitute_variables(expr.arg2, mapping),
            )
        return expr


def _replace_all_vars_with_placeholder(expr, target_uid, placeholder):
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


def _replace_all_vars_same_placeholder(expr, placeholder):
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


def align_variables(sys1, sys2):
    engine = VariableAlignmentEngine(sys1, sys2)
    return engine.compute_mapping()


def test_simple_linear_system():
    """Test simple linear system with different variable names."""
    x1 = Var("x", uid=1)
    y1 = Var("y", uid=2)
    x2 = Var("a", uid=10)
    y2 = Var("b", uid=20)

    eq1_sys1 = x1 + y1
    eq2_sys1 = x1 - y1
    eq1_sys2 = x2 + y2
    eq2_sys2 = x2 - y2

    sys1 = [eq1_sys1, eq2_sys1]
    sys2 = [eq1_sys2, eq2_sys2]

    mapping = align_variables(sys1, sys2)
    print(f"Test simple linear system:")
    print(f"  mapping: {mapping}")
    
    assert len(mapping) == 2, f"Expected 2 mappings, got {len(mapping)}"
    assert mapping[1] == 10, f"x should map to a"
    assert mapping[2] == 20, f"y should map to b"
    print("  PASSED\n")


def test_polynomial_system():
    """Test polynomial system equivalence."""
    x1 = Var("x", uid=1)
    y1 = Var("y", uid=2)
    x2 = Var("u", uid=10)
    y2 = Var("v", uid=20)

    eq1_sys1 = (x1 + y1) ** Const(2)
    eq2_sys1 = x1 ** Const(2) + Const(2) * x1 * y1 + y1 ** Const(2)
    eq1_sys2 = (x2 + y2) ** Const(2)
    eq2_sys2 = x2 ** Const(2) + Const(2) * x2 * y2 + y2 ** Const(2)

    sys1 = [eq1_sys1, eq2_sys1]
    sys2 = [eq1_sys2, eq2_sys2]

    mapping = align_variables(sys1, sys2)
    print(f"Test polynomial system:")
    print(f"  mapping: {mapping}")
    
    assert len(mapping) == 2, f"Expected 2 mappings, got {len(mapping)}"
    print("  PASSED\n")


def test_constants_ignored():
    """Test that constants are properly ignored."""
    a1 = Var("a", uid=1)
    b1 = Var("b", uid=2)
    a2 = Var("x", uid=10)
    b2 = Var("y", uid=20)

    eq1_sys1 = a1 + Const(5)
    eq2_sys1 = b1 * Const(3)
    eq1_sys2 = a2 + Const(5)
    eq2_sys2 = b2 * Const(3)

    sys1 = [eq1_sys1, eq2_sys1]
    sys2 = [eq1_sys2, eq2_sys2]

    mapping = align_variables(sys1, sys2)
    print(f"Test constants ignored:")
    print(f"  mapping: {mapping}")
    
    assert len(mapping) == 2, f"Expected 2 mappings, got {len(mapping)}"
    print("  PASSED\n")


def run_all_tests():
    print("=" * 60)
    print("RUNNING VARIABLE ALIGNMENT TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_simple_linear_system,
        test_polynomial_system,
        test_constants_ignored,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}\n")
            failed += 1
        except Exception as e:
            import traceback
            print(f"  ERROR: {e}")
            traceback.print_exc()
            print()
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
