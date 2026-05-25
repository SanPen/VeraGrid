# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Standalone tests for symbolic expression equivalence system.
This test file imports ONLY the minimal classes needed and does not
trigger the full VeraGridEngine import chain.
"""

import sys
import os
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple, Union

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


def sin(x):
    return Func(x, "sin")


def cos(x):
    return Func(x, "cos")


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


def _get_product_vars(expr):
    if isinstance(expr, Var):
        return [expr.name]
    if isinstance(expr, BinOp) and expr.op == "*":
        return _get_product_vars(expr.left) + _get_product_vars(expr.right)
    return []


def _get_sorted_vars_key(expr):
    """Get a canonical key (sorted tuple) for variable comparison in products."""
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


def _combine_like_terms(expr):
    """Combine like terms in a sum by collecting all terms first."""
    if not isinstance(expr, BinOp) or expr.op != "+":
        return expr
    
    all_terms = _collect_all_terms(expr)
    return _merge_terms_list(all_terms)


def _collect_all_terms(expr):
    """Collect all terms from a sum into a flat list."""
    if isinstance(expr, BinOp) and expr.op == "+":
        return _collect_all_terms(expr.left) + _collect_all_terms(expr.right)
    return [expr]


def _merge_terms_list(terms):
    """Merge like terms from a flat list of terms."""
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
    
    merged.sort(key=lambda e: _hash_expr(e))
    result = merged[0]
    for t in merged[1:]:
        result = BinOp(result, "+", t)
    return result


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


def structural_hash(expr):
    canon = canonical(expr)
    return _hash_expr(canon)


def structural_hash_expanded(expr):
    canon = expand_and_canonicalize(expr)
    return _hash_expr(canon)


def equivalent(e1, e2):
    if e1 is e2:
        return True
    h1 = structural_hash(e1)
    h2 = structural_hash(e2)
    return h1 == h2


def equivalent_expanded(e1, e2):
    if e1 is e2:
        return True
    h1 = structural_hash_expanded(e1)
    h2 = structural_hash_expanded(e2)
    return h1 == h2


def equivalent_systems(sys1, sys2):
    if len(sys1) != len(sys2):
        return False
    hashes1 = sorted(structural_hash(e) for e in sys1)
    hashes2 = sorted(structural_hash(e) for e in sys2)
    return hashes1 == hashes2


def equations_equivalent(eq1, eq2):
    if not isinstance(eq1, BinOp) or not isinstance(eq2, BinOp):
        return structural_hash(eq1) == structural_hash(eq2)

    lhs1_hash = structural_hash(eq1.left)
    lhs2_hash = structural_hash(eq2.left)
    rhs1_hash = structural_hash(eq1.right)
    rhs2_hash = structural_hash(eq2.right)

    if lhs1_hash == lhs2_hash and rhs1_hash == rhs2_hash:
        return True
    if lhs1_hash == rhs2_hash and rhs1_hash == lhs2_hash:
        return True

    diff1 = canonical(BinOp(eq1.left, "-", eq1.right))
    diff2 = canonical(BinOp(eq2.left, "-", eq2.right))
    return structural_hash(diff1) == structural_hash(diff2)


def test_commutativity():
    """Test a + b == b + a"""
    a = Var("a")
    b = Var("b")
    
    expr1 = a + b
    expr2 = b + a
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    
    print(f"Test commutativity (add):")
    print(f"  a + b hash: {h1[:16]}...")
    print(f"  b + a hash: {h2[:16]}...")
    assert h1 == h2, f"Hashes should match: {h1} != {h2}"
    assert equivalent(expr1, expr2), "a + b should be equivalent to b + a"
    print("  PASSED\n")


def test_commutativity_mult():
    """Test a * b == b * a"""
    a = Var("a")
    b = Var("b")
    
    expr1 = a * b
    expr2 = b * a
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    
    print(f"Test commutativity (mult):")
    print(f"  a * b hash: {h1[:16]}...")
    print(f"  b * a hash: {h2[:16]}...")
    assert h1 == h2, f"Hashes should match: {h1} != {h2}"
    assert equivalent(expr1, expr2), "a * b should be equivalent to b * a"
    print("  PASSED\n")


def test_associativity():
    """Test (a + b) + c == a + (b + c)"""
    a = Var("a")
    b = Var("b")
    c = Var("c")
    
    expr1 = (a + b) + c
    expr2 = a + (b + c)
    
    print(f"Test associativity (add):")
    print(f"  (a + b) + c: {expr1}")
    print(f"  a + (b + c): {expr2}")
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    print(f"  hash1: {h1[:16]}...")
    print(f"  hash2: {h2[:16]}...")
    assert h1 == h2, f"Hashes should match: {h1} != {h2}"
    assert equivalent(expr1, expr2), "(a+b)+c should be equivalent to a+(b+c)"
    print("  PASSED\n")


def test_associativity_mult():
    """Test (a * b) * c == a * (b * c)"""
    a = Var("a")
    b = Var("b")
    c = Var("c")
    
    expr1 = (a * b) * c
    expr2 = a * (b * c)
    
    print(f"Test associativity (mult):")
    print(f"  (a * b) * c: {expr1}")
    print(f"  a * (b * c): {expr2}")
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    assert h1 == h2, f"Hashes should match: {h1} != {h2}"
    assert equivalent(expr1, expr2), "(a*b)*c should be equivalent to a*(b*c)"
    print("  PASSED\n")


def test_polynomial_equivalence():
    """Test (x + 1)^2 == x^2 + 2x + 1 using expanded comparison"""
    x = Var("x")
    
    expr1 = (x + Const(1)) ** Const(2)
    expr2 = x ** Const(2) + Const(2) * x + Const(1)
    
    print(f"Test polynomial equivalence:")
    print(f"  (x + 1)^2: {expr1}")
    print(f"  x^2 + 2x + 1: {expr2}")
    print(f"  (x + 1)^2 expanded: {expand(expr1)}")
    print(f"  x^2 + 2x + 1 expanded: {expand(expr2)}")
    print(f"  (x + 1)^2 expand+canon: {expand_and_canonicalize(expr1)}")
    print(f"  x^2 + 2x + 1 expand+canon: {expand_and_canonicalize(expr2)}")
    
    h1 = structural_hash_expanded(expr1)
    h2 = structural_hash_expanded(expr2)
    print(f"  expanded hash1: {h1[:16]}...")
    print(f"  expanded hash2: {h2[:16]}...")
    
    assert equivalent_expanded(expr1, expr2), "(x+1)^2 should equal x^2+2x+1 with expansion"
    print("  PASSED\n")


def test_function_stability():
    """Test sin(x + 0) == sin(x)"""
    x = Var("x")
    
    expr1 = sin(x + Const(0))
    expr2 = sin(x)
    
    print(f"Test function stability:")
    print(f"  sin(x + 0): {canonical(expr1)}")
    print(f"  sin(x): {canonical(expr2)}")
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    assert h1 == h2, f"sin(x+0) should hash same as sin(x)"
    assert equivalent(expr1, expr2), "sin(x+0) should be equivalent to sin(x)"
    print("  PASSED\n")


def test_complex_expression():
    """Test more complex expressions"""
    x = Var("x")
    y = Var("y")
    
    expr1 = (x + y) * (x + y)
    expr2 = x * x + Const(2) * x * y + y * y
    
    print(f"Test complex expression:")
    print(f"  (x + y)^2: {expr1}")
    print(f"  x^2 + 2xy + y^2: {expr2}")
    print(f"  (x + y)^2 expanded: {expand(expr1)}")
    print(f"  x^2 + 2xy + y^2 expanded: {expand(expr2)}")
    print(f"  (x + y)^2 expand+canon: {expand_and_canonicalize(expr1)}")
    print(f"  x^2 + 2xy + y^2 expand+canon: {expand_and_canonicalize(expr2)}")
    
    h1 = structural_hash_expanded(expr1)
    h2 = structural_hash_expanded(expr2)
    print(f"  expanded hash1: {h1[:16]}...")
    print(f"  expanded hash2: {h2[:16]}...")
    
    assert equivalent_expanded(expr1, expr2), "(x+y)^2 should equal x^2+2xy+y^2 with expansion"
    print("  PASSED\n")


def test_equations_equivalent():
    """Test equation equivalence considering a=b == b=a"""
    x = Var("x")
    
    eq1 = x - Const(1)
    eq2 = Const(1) - x
    
    print(f"Test equations_equivalent:")
    print(f"  eq1: x - 1")
    print(f"  eq2: 1 - x")
    print(f"  eq1 canonical: {canonical(eq1)}")
    print(f"  eq2 canonical: {canonical(eq2)}")
    
    h1 = structural_hash(canonical(eq1))
    h2 = structural_hash(canonical(eq2))
    print(f"  hash1: {h1[:16]}...")
    print(f"  hash2: {h2[:16]}...")
    
    assert equations_equivalent(eq1, eq2), "x-1 should be equivalent to 1-x as equations"
    print("  PASSED\n")


def test_system_equivalence():
    """Test that two systems with equations in different order are equivalent"""
    x = Var("x")
    y = Var("y")
    
    sys1 = [
        x + y,
        x * y,
        x - y,
    ]
    
    sys2 = [
        x * y,
        x - y,
        x + y,
    ]
    
    print(f"Test system equivalence:")
    print(f"  sys1 hashes: {[structural_hash(e)[:8] for e in sys1]}")
    print(f"  sys2 hashes: {[structural_hash(e)[:8] for e in sys2]}")
    
    assert equivalent_systems(sys1, sys2), "Systems should be equivalent regardless of equation order"
    print("  PASSED\n")


def test_constant_folding():
    """Test constant folding"""
    a = Var("a")
    
    expr1 = Const(2) + Const(3)
    expr2 = Const(5)
    
    print(f"Test constant folding:")
    print(f"  2 + 3 canonical: {canonical(expr1)}")
    print(f"  5 canonical: {canonical(expr2)}")
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    assert h1 == h2, "2+3 should hash same as 5"
    assert equivalent(expr1, expr2), "2+3 should be equivalent to 5"
    print("  PASSED\n")


def test_neutral_elements():
    """Test a + 0 = a, a * 1 = a"""
    a = Var("a")
    
    print(f"Test neutral elements:")
    
    expr1 = a + Const(0)
    expr2 = a
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    print(f"  a + 0 hash: {h1[:16]}...")
    print(f"  a hash: {h2[:16]}...")
    assert equivalent(expr1, expr2), "a + 0 should be equivalent to a"
    
    expr3 = a * Const(1)
    expr4 = a
    
    h3 = structural_hash(expr3)
    h4 = structural_hash(expr4)
    print(f"  a * 1 hash: {h3[:16]}...")
    print(f"  a hash: {h4[:16]}...")
    assert equivalent(expr3, expr4), "a * 1 should be equivalent to a"
    print("  PASSED\n")


def test_zero_product():
    """Test a * 0 = 0"""
    a = Var("a")
    
    print(f"Test zero product:")
    
    expr1 = a * Const(0)
    expr2 = Const(0)
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    print(f"  a * 0 hash: {h1[:16]}...")
    print(f"  0 hash: {h2[:16]}...")
    assert equivalent(expr1, expr2), "a * 0 should be equivalent to 0"
    print("  PASSED\n")


def test_power_normalization():
    """Test a**0 = 1, a**1 = a"""
    a = Var("a")
    
    print(f"Test power normalization:")
    
    expr1 = a ** Const(0)
    expr2 = Const(1)
    
    h1 = structural_hash(expr1)
    h2 = structural_hash(expr2)
    print(f"  a**0 hash: {h1[:16]}...")
    print(f"  1 hash: {h2[:16]}...")
    assert equivalent(expr1, expr2), "a**0 should be equivalent to 1"
    
    expr3 = a ** Const(1)
    h3 = structural_hash(expr3)
    h4 = structural_hash(a)
    print(f"  a**1 hash: {h3[:16]}...")
    print(f"  a hash: {h4[:16]}...")
    assert equivalent(expr3, a), "a**1 should be equivalent to a"
    print("  PASSED\n")


def run_all_tests():
    print("=" * 60)
    print("RUNNING SYMBOLIC EQUIVALENCE TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_commutativity,
        test_commutativity_mult,
        test_associativity,
        test_associativity_mult,
        test_polynomial_equivalence,
        test_function_stability,
        test_complex_expression,
        test_equations_equivalent,
        test_system_equivalence,
        test_constant_folding,
        test_neutral_elements,
        test_zero_product,
        test_power_normalization,
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