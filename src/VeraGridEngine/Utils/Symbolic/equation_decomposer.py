from __future__ import annotations

from typing import List, Tuple, Dict, Optional, Any, Set
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram


class EquationDecomposer:
    """
    Decomposes a Block containing algebraic_eqs and state_eqs
    into a hierarchical Block with children representing basic operations
    (gain, sum, product, divide, etc.) connected as a block diagram.

    This is the inverse of Block.unify_blocks(). Instead of flattening
    child blocks into a single equation set, it takes a monolithic block
    of equations and produces a tree of simple operation blocks that can
    be visually rendered in the DynamicBlockEditorGUI.
    """

    def __init__(self, var_factory: VarFactory):
        self.vf = var_factory
        self._counter: int = 0
        self._expr_cache: Dict[int, Tuple[sym.Var, List[Block]]] = {}
        self._param_uids: set = set()
        self._orig_block: Block | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(self, block: Block) -> Block:
        """
        Decompose a block's equations into child operation blocks.

        Returns a new Block with ``children`` and a populated
        ``BlockDiagram`` suitable for the graphical editor.
        """
        self._counter = 0
        self._expr_cache.clear()
        self._orig_block = block

        self._collect_parameter_uids(block)

        child_blocks: List[Block] = []
        processed_vars: Dict[int, sym.Var] = {}
        block_eq_map: Dict[int, str] = {}

        for v in block.in_vars:
            processed_vars[v.non_mutable_uid] = v

        for v in block.out_vars:
            processed_vars[v.non_mutable_uid] = v

        eq_order = self._topological_sort_block(block)
        var_to_block_output: Dict[int, sym.Var] = {}

        for eq_key, var, eq in eq_order:
            if eq_key.startswith("alg_"):
                rhs = self._extract_rhs(eq, var)
                if rhs is None:
                    rhs = self._extract_rhs_fallback(eq, var)
                if rhs is not None:
                    result_var, blocks = self._decompose_expr(rhs)
                    if not blocks:
                        if result_var is not var:
                            blk = self._make_pass_through(var, result_var)
                            block_eq_map[blk.uid] = eq_key
                            child_blocks.append(blk)
                        else:
                            blk = Block(
                                algebraic_vars=[var],
                                algebraic_eqs=[var - rhs],
                                out_vars=[var],
                                name="passthrough",
                            )
                            block_eq_map[blk.uid] = eq_key
                            child_blocks.append(blk)
                        var_to_block_output[var.non_mutable_uid] = var
                    else:
                        self._remap_last_output(blocks, result_var, var)
                        for b in blocks:
                            block_eq_map[b.uid] = eq_key
                        var_to_block_output[var.non_mutable_uid] = var
                        child_blocks.extend(blocks)

            elif eq_key.startswith("state_"):
                rhs = eq
                result_var, blocks = self._decompose_expr(rhs)
                if not blocks:
                    int_blk = Block(
                        state_vars=[var],
                        state_eqs=[result_var],
                        out_vars=[var],
                        name="integrator",
                    )
                    block_eq_map[int_blk.uid] = eq_key
                    child_blocks.append(int_blk)
                else:
                    for b in blocks:
                        block_eq_map[b.uid] = eq_key
                    child_blocks.extend(blocks)
                    int_blk = Block(
                        state_vars=[var],
                        state_eqs=[result_var],
                        out_vars=[var],
                        name="integrator",
                    )
                    block_eq_map[int_blk.uid] = eq_key
                    child_blocks.append(int_blk)
                var_to_block_output[var.non_mutable_uid] = var

        # --- build diagram ---
        diagram, all_children = self._build_diagram(child_blocks, block)

        new_event_dict = dict(block.event_dict) if block.event_dict else {}
        new_mode_dict = dict(block.mode_dict) if block.mode_dict else {}
        new_parameters = dict(block.parameters) if block.parameters else {}
        new_init_eqs = dict(block.init_eqs) if block.init_eqs else {}
        new_init_values = dict(block.init_values) if block.init_values else {}
        new_diff_init_eqs = dict(block.diff_init_eqs) if block.diff_init_eqs else {}

        result = Block(
            name=block.name,
            children=all_children,
            in_vars=list(block.in_vars),
            out_vars=list(block.out_vars),
            event_dict=new_event_dict,
            mode_dict=new_mode_dict,
            parameters=new_parameters,
            init_eqs=new_init_eqs,
            init_values=new_init_values,
            diff_init_eqs=new_diff_init_eqs,
            external_mapping=dict(block.external_mapping) if block.external_mapping else None,
            api_obj_mapping=dict(block.api_obj_mapping) if block.api_obj_mapping else None,
        )
        result.uid = block.uid
        result.diagram = diagram

        return result

    # ------------------------------------------------------------------
    # Parameter collection
    # ------------------------------------------------------------------

    def _collect_parameter_uids(self, block: Block) -> None:
        self._param_uids.clear()
        for p in block.event_dict or {}:
            self._param_uids.add(p.non_mutable_uid)
        for p in block.mode_dict or {}:
            self._param_uids.add(p.non_mutable_uid)
        for p in block.parameters or {}:
            self._param_uids.add(p.non_mutable_uid)

    def _is_parameter(self, expr: sym.Expr) -> bool:
        if isinstance(expr, sym.Var):
            return expr.non_mutable_uid in self._param_uids
        return False

    def _is_in_var(self, var: sym.Var) -> bool:
        if self._orig_block is None:
            return False
        for v in self._orig_block.in_vars:
            if v.non_mutable_uid == var.non_mutable_uid:
                return True
        return False

    @staticmethod
    def _contains_var(expr: sym.Expr, target: sym.Var) -> bool:
        for v in expr.get_vars():
            if v.non_mutable_uid == target.non_mutable_uid:
                return True
        return False

    # ------------------------------------------------------------------
    # Naming helpers
    # ------------------------------------------------------------------

    def _new_name(self, prefix: str = "x") -> str:
        self._counter += 1
        return f"_{prefix}_{self._counter}"

    def _new_var(self, prefix: str = "x") -> sym.Var:
        return self.vf.add_var(self._new_name(prefix))

    # ------------------------------------------------------------------
    # Variable-to-equation mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _find_defined_var(eq: sym.Expr,
                          candidates: List[sym.Var]) -> Optional[sym.Var]:
        """
        Return the candidate variable that *eq* defines, or ``None``.

        The canonical pattern is  ``var - expr`` where *var* is directly a
        :class:`sym.Var`.  When that is not found the entire equation is
        searched for any of the candidates and the first match is returned.
        """
        if isinstance(eq, sym.BinOp) and eq.op == "-":
            for v in candidates:
                if isinstance(eq.left, sym.Var) and eq.left.non_mutable_uid == v.non_mutable_uid:
                    return v
                if isinstance(eq.right, sym.Var) and eq.right.non_mutable_uid == v.non_mutable_uid:
                    return v
        for v in candidates:
            for inner in eq.get_vars():
                if inner.non_mutable_uid == v.non_mutable_uid:
                    return v
        return None

    # ------------------------------------------------------------------
    # Topological sort of equations
    # ------------------------------------------------------------------

    def _topological_sort_block(self, block: Block) -> List[Tuple[str, sym.Var, sym.Expr]]:
        entries: List[Tuple[str, sym.Var, sym.Expr]] = []

        for eq_idx, eq in enumerate(block.algebraic_eqs):
            var = self._find_defined_var(eq, block.algebraic_vars)
            if var is not None:
                entries.append((f"alg_{eq_idx}", var, eq))

        for i, var in enumerate(block.state_vars):
            #Todo: state vars and equations might no be in the same order
            eq = block.state_eqs[i]
            entries.append((f"state_{i}", var, eq))

        eq_deps: Dict[str, List[int]] = dict()
        var_defined_by: Dict[int, str] = dict()

        for eq_key, var, eq in entries:
            rhs = eq
            if eq_key.startswith("alg_"):
                extracted = self._extract_rhs(eq, var)
                if extracted is not None:
                    rhs = extracted
            all_vars = rhs.get_vars()
            deps = [
                v.non_mutable_uid for v in all_vars
                if v.non_mutable_uid != var.non_mutable_uid
            ]
            eq_deps[eq_key] = deps
            var_defined_by[var.non_mutable_uid] = eq_key

        adj: Dict[str, set] = {}
        for eq_key, dep_uids in eq_deps.items():
            deps: set = set()
            for uid in dep_uids:
                if uid in var_defined_by:
                    deps.add(var_defined_by[uid])
            adj[eq_key] = deps

        in_degree = {k: len(v) for k, v in adj.items()}
        queue = [k for k, v in in_degree.items() if v == 0]
        sorted_keys: List[str] = []

        while queue:
            node = queue.pop(0)
            sorted_keys.append(node)
            for other_key, other_deps in adj.items():
                if node in other_deps:
                    in_degree[other_key] -= 1
                    if in_degree[other_key] == 0:
                        queue.append(other_key)

        remaining = set(eq_deps.keys()) - set(sorted_keys)
        sorted_keys.extend(remaining)

        key_to_entry = {e[0]: e for e in entries}
        return [key_to_entry[k] for k in sorted_keys if k in key_to_entry]

    # ------------------------------------------------------------------
    # RHS extraction
    # ------------------------------------------------------------------

    def _extract_rhs(self, eq: sym.Expr, defined_var: sym.Var) -> sym.Expr | None:
        if isinstance(eq, sym.BinOp) and eq.op == "-":
            if isinstance(eq.left, sym.Var) and eq.left.non_mutable_uid == defined_var.non_mutable_uid:
                return eq.right
            if isinstance(eq.right, sym.Var) and eq.right.non_mutable_uid == defined_var.non_mutable_uid:
                return eq.left
        return None

    def _extract_factor_for_var(self, expr: sym.Expr, var: sym.Var) -> sym.Expr | None:
        """
        If *expr* has the form ``factor * var`` or ``var * factor`` return
        the *factor* sub-expression, otherwise return ``None``.
        """
        if isinstance(expr, sym.Var):
            if expr.non_mutable_uid == var.non_mutable_uid:
                return sym.Const(1.0)
            return None
        if isinstance(expr, sym.BinOp) and expr.op == "*":
            if isinstance(expr.left, sym.Var) and expr.left.non_mutable_uid == var.non_mutable_uid:
                return expr.right
            if isinstance(expr.right, sym.Var) and expr.right.non_mutable_uid == var.non_mutable_uid:
                return expr.left
        return None

    def _extract_rhs_fallback(self, eq: sym.Expr, defined_var: sym.Var) -> sym.Expr | None:
        if isinstance(eq, sym.BinOp):
            left_has = self._contains_var(eq.left, defined_var)
            right_has = self._contains_var(eq.right, defined_var)

            if eq.op == "-":
                if left_has and not right_has:
                    factor = self._extract_factor_for_var(eq.left, defined_var)
                    if factor is not None and not (isinstance(factor, sym.Const) and factor.value == 1.0):
                        return eq.right / factor
                    return eq.right
                if right_has and not left_has:
                    factor = self._extract_factor_for_var(eq.right, defined_var)
                    if factor is not None and not (isinstance(factor, sym.Const) and factor.value == 1.0):
                        return eq.left / factor
                    return eq.left

            elif eq.op == "+":
                if left_has and not right_has:
                    return -eq.right
                if right_has and not left_has:
                    return -eq.left

        if self._contains_var(eq, defined_var):
            return eq

        return None

    # ------------------------------------------------------------------
    # Expression decomposition (core)
    # ------------------------------------------------------------------

    def _decompose_expr(self, expr: sym.Expr) -> Tuple[sym.Var, List[Block]]:
        cache_key = expr.uid
        if cache_key in self._expr_cache:
            return self._expr_cache[cache_key]

        result: Tuple[sym.Var, List[Block]]

        if isinstance(expr, sym.Var):
            result = (expr, [])

        elif isinstance(expr, sym.Const):
            y = self._new_var("const")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - expr],
                out_vars=[y],
                name="const",
            )
            result = (y, [blk])

        elif isinstance(expr, sym.BinOp):
            result = self._decompose_binop(expr)

        elif isinstance(expr, sym.UnOp):
            result = self._decompose_unop(expr)

        elif isinstance(expr, sym.Func):
            result = self._decompose_func(expr)

        elif isinstance(expr, sym.Func2):
            result = self._decompose_func2(expr)

        else:
            raise TypeError(f"Unsupported expression type: {type(expr)}")

        self._expr_cache[cache_key] = result
        return result

    def _decompose_binop(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        if expr.op == "*":
            return self._decompose_mul(expr)

        left_is_const = isinstance(expr.left, sym.Const)
        right_is_const = isinstance(expr.right, sym.Const)

        if left_is_const:
            left_val: sym.Expr = expr.left
            left_blocks = []
        else:
            left_v, left_blocks = self._decompose_expr(expr.left)
            left_val = left_v

        if right_is_const:
            right_val: sym.Expr = expr.right
            right_blocks = []
        else:
            right_v, right_blocks = self._decompose_expr(expr.right)
            right_val = right_v

        all_blocks = left_blocks + right_blocks

        in_vars: List[sym.Var] = []
        if not left_is_const:
            in_vars.append(left_v)
        if not right_is_const:
            in_vars.append(right_v)

        if expr.op == "+":
            y = self._new_var("sum")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - (left_val + right_val)],
                in_vars=in_vars,
                out_vars=[y],
                name="sum",
            )
            all_blocks.append(blk)
            return (y, all_blocks)

        elif expr.op == "-":
            y = self._new_var("sub")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - (left_val - right_val)],
                in_vars=in_vars,
                out_vars=[y],
                name="substraction",
            )
            all_blocks.append(blk)
            return (y, all_blocks)

        elif expr.op == "/":
            y = self._new_var("div")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - (left_val / right_val)],
                in_vars=in_vars,
                out_vars=[y],
                name="divide",
            )
            all_blocks.append(blk)
            return (y, all_blocks)

        elif expr.op == "**":
            y = self._new_var("pow")
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - (left_val ** right_val)],
                in_vars=in_vars,
                out_vars=[y],
                name="power",
            )
            all_blocks.append(blk)
            return (y, all_blocks)

        else:
            raise ValueError(f"Unsupported binary operator: {expr.op}")

    def _decompose_mul(self, expr: sym.BinOp) -> Tuple[sym.Var, List[Block]]:
        if isinstance(expr.right, sym.Const):
            inner_var, inner_blocks = self._decompose_expr(expr.left)
            gain_var = self._new_var("gain")
            gain_param = self.vf.add_var(self._new_name("gain_p"))
            blk = Block(
                algebraic_vars=[gain_var],
                algebraic_eqs=[gain_var - (inner_var * gain_param)],
                in_vars=[inner_var],
                out_vars=[gain_var],
                event_dict={gain_param: sym.Const(expr.right.value)},
                name="gain",
            )
            return (gain_var, inner_blocks + [blk])

        if isinstance(expr.left, sym.Const):
            inner_var, inner_blocks = self._decompose_expr(expr.right)
            gain_var = self._new_var("gain")
            gain_param = self.vf.add_var(self._new_name("gain_p"))
            blk = Block(
                algebraic_vars=[gain_var],
                algebraic_eqs=[gain_var - (gain_param * inner_var)],
                in_vars=[inner_var],
                out_vars=[gain_var],
                event_dict={gain_param: sym.Const(expr.left.value)},
                name="gain",
            )
            return (gain_var, inner_blocks + [blk])

        if isinstance(expr.right, sym.Var) and self._is_parameter(expr.right):
            inner_var, inner_blocks = self._decompose_expr(expr.left)
            gain_var = self._new_var("gain")
            blk = Block(
                algebraic_vars=[gain_var],
                algebraic_eqs=[gain_var - (inner_var * expr.right)],
                in_vars=[inner_var],
                out_vars=[gain_var],
                event_dict={expr.right: sym.Const(0.0)},
                name="gain",
            )
            return (gain_var, inner_blocks + [blk])

        if isinstance(expr.left, sym.Var) and self._is_parameter(expr.left):
            inner_var, inner_blocks = self._decompose_expr(expr.right)
            gain_var = self._new_var("gain")
            blk = Block(
                algebraic_vars=[gain_var],
                algebraic_eqs=[gain_var - (expr.left * inner_var)],
                in_vars=[inner_var],
                out_vars=[gain_var],
                event_dict={expr.left: sym.Const(0.0)},
                name="gain",
            )
            return (gain_var, inner_blocks + [blk])

        left_var, left_blocks = self._decompose_expr(expr.left)
        right_var, right_blocks = self._decompose_expr(expr.right)
        prod_var = self._new_var("prod")
        blk = Block(
            algebraic_vars=[prod_var],
            algebraic_eqs=[prod_var - (left_var * right_var)],
            in_vars=[left_var, right_var],
            out_vars=[prod_var],
            name="product",
        )
        return (prod_var, left_blocks + right_blocks + [blk])

    def _decompose_unop(self, expr: sym.UnOp) -> Tuple[sym.Var, List[Block]]:
        inner_var, inner_blocks = self._decompose_expr(expr.operand)
        if expr.op == "-":
            y = self._new_var("neg")
            neg_param = self.vf.add_var(self._new_name("neg_gain"))
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - (neg_param * inner_var)],
                in_vars=[inner_var],
                out_vars=[y],
                event_dict={neg_param: sym.Const(-1.0)},
                name="gain",
            )
            return (y, inner_blocks + [blk])
        else:
            raise ValueError(f"Unsupported unary operator: {expr.op}")

    def _decompose_func(self, expr: sym.Func) -> Tuple[sym.Var, List[Block]]:
        inner_var, inner_blocks = self._decompose_expr(expr.arg)
        y = self._new_var(expr.op)

        func_map = {
            "sin": sym.sin, "cos": sym.cos, "tan": sym.tan,
            "exp": sym.exp, "log": sym.log, "sqrt": sym.sqrt,
            "abs": sym.abs, "asin": sym.asin, "acos": sym.acos,
            "atan": sym.atan, "sinh": sym.sinh, "cosh": sym.cosh,
            "floor": sym.floor, "ceil": sym.ceil,
        }

        if expr.op in func_map:
            f = func_map[expr.op]
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - f(inner_var)],
                in_vars=[inner_var],
                out_vars=[y],
                name=expr.op,
            )
            return (y, inner_blocks + [blk])
        else:
            raise ValueError(f"Unsupported function: {expr.op}")

    def _decompose_func2(self, expr: sym.Func2) -> Tuple[sym.Var, List[Block]]:
        left_var, left_blocks = self._decompose_expr(expr.arg1)
        right_var, right_blocks = self._decompose_expr(expr.arg2)
        y = self._new_var(expr.name)

        func2_map = {"atan2": sym.atan2, "min": sym.min, "max": sym.max}

        if expr.name in func2_map:
            f = func2_map[expr.name]
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - f(left_var, right_var)],
                in_vars=[left_var, right_var],
                out_vars=[y],
                name=expr.name,
            )
            return (y, left_blocks + right_blocks + [blk])
        else:
            raise ValueError(f"Unsupported function: {expr.name}")

    # ------------------------------------------------------------------
    # Output remapping
    # ------------------------------------------------------------------

    def _remap_last_output(self, blocks: List[Block], current_output: sym.Var, target_output: sym.Var) -> sym.Var:
        if not blocks:
            return current_output
        last = blocks[-1]
        if current_output is not target_output:
            last.update_equations(current_output, target_output)
            last.update_variables(current_output, target_output)
            for i, v in enumerate(last.algebraic_vars):
                if v.non_mutable_uid == current_output.non_mutable_uid:
                    last.algebraic_vars[i] = target_output
            for i, v in enumerate(last.out_vars):
                if v.non_mutable_uid == current_output.non_mutable_uid:
                    last.out_vars[i] = target_output
        return target_output

    def _make_pass_through(self, target_var: sym.Var, source_var: sym.Var) -> Block:
        return Block(
            algebraic_vars=[target_var],
            algebraic_eqs=[target_var - source_var],
            in_vars=[source_var],
            out_vars=[target_var],
            name="passthrough",
        )

    # ------------------------------------------------------------------
    # BlockDiagram construction
    # ------------------------------------------------------------------

    def _build_diagram(self, children: List[Block], parent: Block) -> Tuple[BlockDiagram, List[Block]]:
        diagram = BlockDiagram()

        if not children:
            return diagram, children

        block_uid_to_idx: Dict[int, int] = {}
        for i, blk in enumerate(children):
            block_uid_to_idx[blk.uid] = i

        # --- Build producer map from original children only ---
        var_to_producer_block: Dict[int, int] = {}
        for i, blk in enumerate(children):
            for v in blk.algebraic_vars:
                var_to_producer_block[v.non_mutable_uid] = i
            for v in blk.state_vars:
                var_to_producer_block[v.non_mutable_uid] = i
            for v in blk.out_vars:
                var_to_producer_block[v.non_mutable_uid] = i

        # --- Detect fan-out: variables consumed by >= 2 blocks ---
        var_consumers: Dict[int, List[int]] = {}
        for i, blk in enumerate(children):
            for in_var in blk.in_vars:
                producer = var_to_producer_block.get(in_var.non_mutable_uid)
                if producer is not None and producer != i:
                    var_consumers.setdefault(in_var.non_mutable_uid, []).append(i)
            for eq in (blk.state_eqs or []) + (blk.algebraic_eqs or []):
                for v in eq.get_vars():
                    producer = var_to_producer_block.get(v.non_mutable_uid)
                    if producer is not None and producer != i:
                        consumers = var_consumers.setdefault(v.non_mutable_uid, [])
                        if i not in consumers:
                            consumers.append(i)

        # Save original producer map before adding From/To blocks
        original_var_to_producer = dict(var_to_producer_block)
        original_count = len(children)

        # --- Create From/To pairs for fan-out variables ---
        new_children: List[Block] = list(children)
        fan_out_pairs: List[Tuple[int, int, int, int]] = []  # (var_uid, from_idx, to_idx, consumer_idx)
        fan_out_vars: Set[int] = set()
        pair_counter = 0
        from_to_tpe: Dict[int, str] = {}  # block index -> "signal_in" or "signal_out"

        for var_uid, consumer_indices in var_consumers.items():
            if len(consumer_indices) < 2:
                continue
            fan_out_vars.add(var_uid)
            # Find the variable object from any consumer
            v = None
            for ci in consumer_indices:
                for iv in children[ci].in_vars:
                    if iv.non_mutable_uid == var_uid:
                        v = iv
                        break
                if v:
                    break
            if v is None:
                for ci in consumer_indices:
                    for eq in (children[ci].state_eqs or []) + (children[ci].algebraic_eqs or []):
                        for ev in eq.get_vars():
                            if ev.non_mutable_uid == var_uid:
                                v = ev
                                break
                        if v:
                            break
                    if v:
                        break
            if v is None:
                continue
            for consumer_idx in consumer_indices:
                pair_counter += 1
                from_blk = Block(in_vars=[v], name=f"From_{pair_counter}")
                to_blk = Block(out_vars=[v], name=f"To_{pair_counter}")
                from_idx = len(new_children)
                new_children.append(from_blk)
                from_to_tpe[from_idx] = "signal_in"
                to_idx = len(new_children)
                new_children.append(to_blk)
                from_to_tpe[to_idx] = "signal_out"
                fan_out_pairs.append((var_uid, from_idx, to_idx, consumer_idx))

        children = new_children

        # --- Rebuild indices with all children ---
        block_uid_to_idx = {}
        for i, blk in enumerate(children):
            block_uid_to_idx[blk.uid] = i

        var_to_producer_block = {}
        for i, blk in enumerate(children):
            for v in blk.algebraic_vars:
                var_to_producer_block[v.non_mutable_uid] = i
            for v in blk.state_vars:
                var_to_producer_block[v.non_mutable_uid] = i
            for v in blk.out_vars:
                var_to_producer_block[v.non_mutable_uid] = i

        # --- Build dependency graph for layering ---
        dep_graph: Dict[int, set] = {i: set() for i in range(len(children))}
        for i in range(original_count):
            blk = children[i]
            for in_var in blk.in_vars:
                producer = original_var_to_producer.get(in_var.non_mutable_uid)
                if producer is not None and producer != i:
                    dep_graph[i].add(producer)
            for state_eq in blk.state_eqs or []:
                for v in state_eq.get_vars():
                    producer = original_var_to_producer.get(v.non_mutable_uid)
                    if producer is not None and producer != i:
                        dep_graph[i].add(producer)
            for alg_eq in blk.algebraic_eqs or []:
                for v in alg_eq.get_vars():
                    producer = original_var_to_producer.get(v.non_mutable_uid)
                    if producer is not None and producer != i:
                        dep_graph[i].add(producer)
        # From depends on producer, To depends on From,
        # Consumer depends on To (replaces dep on original producer)
        from_to_idx_set: Set[int] = set()
        for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
            from_to_idx_set.add(from_idx)
            from_to_idx_set.add(to_idx)
            producer_idx = original_var_to_producer.get(var_uid)
            if producer_idx is not None:
                dep_graph[from_idx].add(producer_idx)
            dep_graph[to_idx].add(from_idx)
            dep_graph[consumer_idx].discard(producer_idx)
            dep_graph[consumer_idx].add(to_idx)

        # ---- Build routing pairs for From/To post-processing ----
        routing_pairs: List[Tuple[int, int, int, int]] = []
        for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
            producer_idx = original_var_to_producer.get(var_uid)
            if producer_idx is not None:
                routing_pairs.append((from_idx, to_idx, producer_idx, consumer_idx))

        # ---- hierarchical layout (Sugiyama-based) ----
        positions = self._layout_hierarchical(children, dep_graph, from_to_tpe, routing_pairs)

        for i, blk in enumerate(children):
            x, y = positions.get(i, (80.0, 60.0))
            diagram.add_node(
                name=blk.name if blk.name else f"block_{i}",
                x=x,
                y=y,
                tpe=from_to_tpe.get(i, ""),
                device_uid=blk.uid,
                color="#C0C0C0",
            )

        # ---- Build fan-out consumer lookup for skip logic ----
        fan_out_var_consumers: Dict[int, Set[int]] = {}
        for var_uid, indices in var_consumers.items():
            if var_uid in fan_out_vars:
                fan_out_var_consumers[var_uid] = set(indices)

        # ---- auto-connections (original children only, skip fan-out) ----
        con_uid_counter = 0
        for i in range(original_count):
            blk = children[i]
            for port_idx, in_var in enumerate(blk.in_vars):
                producer = original_var_to_producer.get(in_var.non_mutable_uid)
                if producer is not None and producer != i:
                    if (in_var.non_mutable_uid in fan_out_var_consumers and
                            i in fan_out_var_consumers[in_var.non_mutable_uid]):
                        continue
                    src_port_idx = self._find_output_port(children[producer], in_var)
                    if src_port_idx is not None:
                        con_uid_counter += 1
                        diagram.add_branch(
                            connectionitem_uid=con_uid_counter,
                            device_uid_from=children[producer].uid,
                            device_uid_to=blk.uid,
                            port_number_from=src_port_idx,
                            port_number_to=port_idx,
                            color="#587291",
                        )

            for port_idx, state_eq in enumerate(blk.state_eqs or []):
                for v in state_eq.get_vars():
                    producer = original_var_to_producer.get(v.non_mutable_uid)
                    if producer is not None and producer != i:
                        if (v.non_mutable_uid in fan_out_var_consumers and
                                i in fan_out_var_consumers[v.non_mutable_uid]):
                            continue
                        src_port_idx = self._find_output_port(children[producer], v)
                        if src_port_idx is not None:
                            needed_input_port = self._find_or_create_input_port(blk, v)
                            if needed_input_port is not None:
                                con_uid_counter += 1
                                diagram.add_branch(
                                    connectionitem_uid=con_uid_counter,
                                    device_uid_from=children[producer].uid,
                                    device_uid_to=blk.uid,
                                    port_number_from=src_port_idx,
                                    port_number_to=needed_input_port,
                                    color="#587291",
                                )

            for port_idx, alg_eq in enumerate(blk.algebraic_eqs or []):
                for v in alg_eq.get_vars():
                    producer = original_var_to_producer.get(v.non_mutable_uid)
                    if producer is not None and producer != i:
                        if (v.non_mutable_uid in fan_out_var_consumers and
                                i in fan_out_var_consumers[v.non_mutable_uid]):
                            continue
                        src_port_idx = self._find_output_port(children[producer], v)
                        if src_port_idx is not None:
                            needed_input_port = self._find_or_create_input_port(blk, v)
                            if needed_input_port is not None:
                                con_uid_counter += 1
                                diagram.add_branch(
                                    connectionitem_uid=con_uid_counter,
                                    device_uid_from=children[producer].uid,
                                    device_uid_to=blk.uid,
                                    port_number_from=src_port_idx,
                                    port_number_to=needed_input_port,
                                    color="#587291",
                                )

        # ---- manual fan-out connections: Producer -> From, To -> Consumer ----
        for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
            # Find the variable object from the producer
            producer_idx = original_var_to_producer.get(var_uid)
            if producer_idx is None:
                continue
            producer_blk = children[producer_idx]
            v = None
            for ov in producer_blk.out_vars:
                if ov.non_mutable_uid == var_uid:
                    v = ov
                    break
            if v is None:
                for av in producer_blk.algebraic_vars:
                    if av.non_mutable_uid == var_uid:
                        v = av
                        break
            if v is None:
                for sv in producer_blk.state_vars:
                    if sv.non_mutable_uid == var_uid:
                        v = sv
                        break
            if v is None:
                continue

            # Producer -> From (port 0)
            src_port_idx = self._find_output_port(producer_blk, v)
            if src_port_idx is not None:
                con_uid_counter += 1
                diagram.add_branch(
                    connectionitem_uid=con_uid_counter,
                    device_uid_from=producer_blk.uid,
                    device_uid_to=children[from_idx].uid,
                    port_number_from=src_port_idx,
                    port_number_to=0,
                    color="#587291",
                )

            # To (port 0) -> Consumer
            consumer_blk = children[consumer_idx]
            needed_input_port = self._find_or_create_input_port(consumer_blk, v)
            if needed_input_port is not None:
                con_uid_counter += 1
                diagram.add_branch(
                    connectionitem_uid=con_uid_counter,
                    device_uid_from=children[to_idx].uid,
                    device_uid_to=consumer_blk.uid,
                    port_number_from=0,
                    port_number_to=needed_input_port,
                    color="#587291",
                )

        return diagram, children

    def _assign_layers(self, dep_graph: Dict[int, set]) -> List[List[int]]:
        remaining = set(dep_graph.keys())
        in_degree = {k: len(v) for k, v in dep_graph.items()}
        layers: List[List[int]] = []

        while remaining:
            current_layer = [n for n in remaining if in_degree.get(n, 0) == 0]
            if not current_layer:
                current_layer = [min(remaining)]
            layers.append(sorted(current_layer))
            for n in current_layer:
                remaining.remove(n)
                for other in remaining:
                    if n in dep_graph.get(other, set()):
                        in_degree[other] = max(0, in_degree[other] - 1)

        return layers

    def _layout_hierarchical(
        self,
        children: List[Block],
        dep_graph: Dict[int, Set[int]],
        from_to_tpe: Dict[int, str],
        routing_pairs: List[Tuple[int, int, int, int]] = None,
    ) -> Dict[int, Tuple[float, float]]:
        n = len(children)
        if n == 0:
            return {}

        LAYER_SPACING_X = 300.0
        BLOCK_SPACING_Y = 200.0
        BLOCK_H = 70.0
        MARGIN_X = 100.0
        MARGIN_Y = 80.0

        # --- Build forward graph (successors) ---
        successors: Dict[int, Set[int]] = {i: set() for i in range(n)}
        for i in range(n):
            for p in dep_graph.get(i, set()):
                successors[p].add(i)

        # --- Topological sort ---
        in_degree = {i: len(dep_graph.get(i, set())) for i in range(n)}
        queue = [i for i in range(n) if in_degree.get(i, 0) == 0]
        topo_order: List[int] = []
        temp_in_degree = dict(in_degree)
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for succ in successors.get(node, set()):
                temp_in_degree[succ] -= 1
                if temp_in_degree[succ] == 0:
                    queue.append(succ)

        remaining = set(range(n)) - set(topo_order)
        topo_order.extend(remaining)

        # --- Longest-path layering ---
        layer: Dict[int, int] = {i: 0 for i in range(n)}
        for node in topo_order:
            max_parent_layer = -1
            for parent in dep_graph.get(node, set()):
                pl = layer.get(parent, 0)
                if pl > max_parent_layer:
                    max_parent_layer = pl
            layer[node] = max_parent_layer + 1

        max_layer = max(layer.values()) if layer else 0
        layers_list: List[List[int]] = [[] for _ in range(max_layer + 1)]
        for i in range(n):
            layers_list[layer[i]].append(i)

        for l in layers_list:
            l.sort(key=lambda x: (x in from_to_tpe, x))

        # --- Crossing minimization (barycenter + local optimization) ---
        # Routing blocks are kept at the end of each layer so they don't
        # interfere with functional-block ordering.
        def _parent_barycenter(layers, target_layer):
            if target_layer == 0:
                return
            items = layers[target_layer]
            func_items = [n for n in items if n not in from_to_tpe]
            if not func_items:
                return
            prev_layer = layers[target_layer - 1]
            scores = []
            for node in func_items:
                parents = [p for p in dep_graph.get(node, set())
                           if p in prev_layer and p not in from_to_tpe]
                if parents:
                    avg = sum(prev_layer.index(p) for p in parents) / len(parents)
                    scores.append((avg, node))
                else:
                    scores.append((func_items.index(node), node))
            scores.sort(key=lambda x: x[0])
            routing_items = [n for n in items if n in from_to_tpe]
            layers[target_layer] = [node for _, node in scores] + routing_items

        def _child_barycenter(layers, target_layer):
            if target_layer >= len(layers) - 1:
                return
            items = layers[target_layer]
            func_items = [n for n in items if n not in from_to_tpe]
            if not func_items:
                return
            next_layer = layers[target_layer + 1]
            scores = []
            for node in func_items:
                children = [c for c in successors.get(node, set())
                            if c in next_layer and c not in from_to_tpe]
                if children:
                    avg = sum(next_layer.index(c) for c in children) / len(children)
                    scores.append((avg, node))
                else:
                    scores.append((func_items.index(node), node))
            scores.sort(key=lambda x: x[0])
            routing_items = [n for n in items if n in from_to_tpe]
            layers[target_layer] = [node for _, node in scores] + routing_items

        def _crossings_between(upper, lower):
            # Only count crossings for functional blocks — routing blocks
            # (signal_in / signal_out) get repositioned later, so optimising
            # crossings that involve them is wasted effort.
            lower_pos = {n: i for i, n in enumerate(lower) if n not in from_to_tpe}
            cnt = 0
            for i, u in enumerate(upper):
                if u in from_to_tpe:
                    continue
                u_conn = successors.get(u, set()) & set(lower)
                if not u_conn:
                    continue
                for v in upper[i + 1:]:
                    if v in from_to_tpe:
                        continue
                    v_conn = successors.get(v, set()) & set(lower)
                    if not v_conn:
                        continue
                    for a in u_conn:
                        pa = lower_pos.get(a)
                        if pa is None:
                            continue
                        for b in v_conn:
                            pb = lower_pos.get(b)
                            if pb is None:
                                continue
                            if pb < pa:
                                cnt += 1
            return cnt

        def _total_crossings():
            total = 0
            for l in range(len(layers_list) - 1):
                total += _crossings_between(layers_list[l], layers_list[l + 1])
            return total

        # Barycenter sweeps
        for sweep in range(15):
            if sweep % 2 == 0:
                for l in range(1, len(layers_list)):
                    _parent_barycenter(layers_list, l)
            else:
                for l in range(len(layers_list) - 2, -1, -1):
                    _child_barycenter(layers_list, l)

        # Local optimization: try adjacent swaps that reduce crossings.
        # Only swap functional blocks; routing blocks stay at the end.
        for iteration in range(12):
            improved = False
            for l in range(len(layers_list)):
                items = layers_list[l]
                func_idx = [idx for idx, n in enumerate(items) if n not in from_to_tpe]
                for pos in range(len(func_idx) - 1):
                    i, j = func_idx[pos], func_idx[pos + 1]
                    cnt_before = _total_crossings()
                    items[i], items[j] = items[j], items[i]
                    cnt_after = _total_crossings()
                    if cnt_after < cnt_before:
                        improved = True
                    else:
                        items[i], items[j] = items[j], items[i]
            if not improved:
                break

        # --- Initial positions ---
        pos: Dict[int, List[float]] = {}
        for l, items in enumerate(layers_list):
            for i, node in enumerate(items):
                pos[node] = [
                    MARGIN_X + l * LAYER_SPACING_X,
                    MARGIN_Y + i * BLOCK_SPACING_Y,
                ]

        # --- Vertical alignment: align connected nodes across layers ---
        # Connected blocks should share similar Y to minimize long vertical
        # connection lines.  This replaces a generic force-directed relaxation.
        ALIGN_MIN_GAP = BLOCK_H + 12.0
        ALIGN_BLEND = 0.6

        for iteration in range(3):
            # Left-to-right: align each node with its predecessors
            for l in range(1, len(layers_list)):
                items = layers_list[l]
                # store current Y snapshot for this sweep
                cur = [pos[node][1] for node in items]
                for idx, node in enumerate(items):
                    preds = [p for p in dep_graph.get(node, set())
                             if p in layers_list[l - 1]]
                    if not preds:
                        continue
                    avg_pred = sum(pos[p][1] for p in preds) / len(preds)
                    lower = cur[idx - 1] + ALIGN_MIN_GAP if idx > 0 else float("-inf")
                    target = max(lower, avg_pred)
                    pos[node][1] += (target - pos[node][1]) * ALIGN_BLEND

                # Reverse pass: enforce upper bound from successor in layer
                for idx in range(len(items) - 2, -1, -1):
                    node = items[idx]
                    nxt = items[idx + 1]
                    upper = pos[nxt][1] - ALIGN_MIN_GAP
                    if pos[node][1] > upper:
                        pos[node][1] = upper

            # Right-to-left: align each node with its successors
            for l in range(len(layers_list) - 2, -1, -1):
                items = layers_list[l]
                cur = [pos[node][1] for node in items]
                for idx, node in enumerate(items):
                    succs = [s for s in successors.get(node, set())
                             if s in layers_list[l + 1]]
                    if not succs:
                        continue
                    avg_succ = sum(pos[s][1] for s in succs) / len(succs)
                    lower = cur[idx - 1] + ALIGN_MIN_GAP if idx > 0 else float("-inf")
                    target = max(lower, avg_succ)
                    pos[node][1] += (target - pos[node][1]) * ALIGN_BLEND

                # Reverse pass: enforce upper bound
                for idx in range(len(items) - 2, -1, -1):
                    node = items[idx]
                    nxt = items[idx + 1]
                    upper = pos[nxt][1] - ALIGN_MIN_GAP
                    if pos[node][1] > upper:
                        pos[node][1] = upper

        # --- Compact vertically ---
        for l in layers_list:
            if len(l) <= 1:
                continue
            items = sorted(l, key=lambda x: pos[x][1])
            for idx in range(1, len(items)):
                curr = items[idx]
                prev = items[idx - 1]
                gap = pos[curr][1] - pos[prev][1]
                min_dist = BLOCK_H + 10.0
                if gap > min_dist + 25.0:
                    pos[curr][1] = pos[prev][1] + min_dist

        # --- Post-process: reposition signal_in/signal_out blocks ---
        # These must stay visually close to their producer/consumer blocks,
        # overriding the Sugiyama layer assignment for these routing elements.
        # Includes collision avoidance: search vertically for free space if
        # the ideal position is already occupied by another block.
        if routing_pairs:
            FUNC_BLOCK_W = 160.0
            FUNC_BLOCK_H = 70.0
            SIGNAL_BLOCK_W = 140.0
            SIGNAL_BLOCK_H = 70.0
            ROUTING_GAP = 80.0
            SIGNAL_GAP_Y = 30.0
            SEARCH_STEP_Y = 25.0
            MAX_VERTICAL_STEPS = 30
            SECONDARY_OFFSET_X = 60.0

            # Identify which indices are routing blocks
            is_signal: Set[int] = {i for i, t in from_to_tpe.items()
                                   if t in ("signal_in", "signal_out")}

            # Build occupied rects for all non-routing blocks
            occupied: List[Tuple[float, float, float, float]] = []

            # Build connection corridors between functional blocks.
            # These represent the area where an orthogonal connection line
            # between two functional blocks travels. Routing blocks must
            # avoid sitting on top of these lines.
            corridors: List[Tuple[float, float, float, float]] = []
            CORRIDOR_PAD = 15.0

            def _add_rect(idx: int, w: float, h: float) -> None:
                occupied.append((
                    pos[idx][0],
                    pos[idx][1],
                    pos[idx][0] + w,
                    pos[idx][1] + h,
                ))

            for i in range(n):
                if i not in is_signal:
                    _add_rect(i, FUNC_BLOCK_W, FUNC_BLOCK_H)

            for i in range(n):
                if i in is_signal:
                    continue
                for p in dep_graph.get(i, set()):
                    if p in is_signal:
                        continue
                    p_right = pos[p][0] + FUNC_BLOCK_W
                    i_left = pos[i][0]
                    if p_right >= i_left:
                        continue
                    p_cy = pos[p][1] + FUNC_BLOCK_H / 2.0
                    i_cy = pos[i][1] + FUNC_BLOCK_H / 2.0
                    corridors.append((
                        p_right - CORRIDOR_PAD,
                        min(p_cy, i_cy) - CORRIDOR_PAD,
                        i_left + CORRIDOR_PAD,
                        max(p_cy, i_cy) + CORRIDOR_PAD,
                    ))

            def _rects_overlap(
                l1: float, t1: float, r1: float, b1: float,
                l2: float, t2: float, r2: float, b2: float,
            ) -> bool:
                return not (r1 <= l2 or l1 >= r2 or b1 <= t2 or t1 >= b2)

            def _is_free(l: float, t: float, r: float, b: float) -> bool:
                for o in occupied:
                    if _rects_overlap(l, t, r, b, o[0], o[1], o[2], o[3]):
                        return False
                for c in corridors:
                    if _rects_overlap(l, t, r, b, c[0], c[1], c[2], c[3]):
                        return False
                return True

            def _place_near_anchor(
                target_idx: int,
                ideal_x: float,
               ideal_y: float,
                block_w: float,
                block_h: float,
            ) -> None:
                for step in range(MAX_VERTICAL_STEPS + 1):
                    for direction in ([0] if step == 0 else [step, -step]):
                        cy = ideal_y + direction * SEARCH_STEP_Y
                        cr = ideal_x + block_w
                        cb = cy + block_h
                        if _is_free(ideal_x, cy, cr, cb):
                            pos[target_idx] = [ideal_x, cy]
                            _add_rect(target_idx, block_w, block_h)
                            return
                for step in range(1, 10):
                    for h_dir in (1, -1):
                        cx = ideal_x + h_dir * step * SECONDARY_OFFSET_X
                        cr = cx + block_w
                        cb = ideal_y + block_h
                        if _is_free(cx, ideal_y, cr, cb):
                            pos[target_idx] = [cx, ideal_y]
                            _add_rect(target_idx, block_w, block_h)
                            return
                pos[target_idx] = [ideal_x, ideal_y]
                _add_rect(target_idx, block_w, block_h)

            # --- Place signal_in (From) blocks ---
            producer_to_froms: Dict[int, List[int]] = {}
            for from_idx, to_idx, producer_idx, consumer_idx in routing_pairs:
                producer_to_froms.setdefault(producer_idx, []).append(from_idx)
            for producer_idx, from_indices in producer_to_froms.items():
                base_x = pos[producer_idx][0] + FUNC_BLOCK_W + ROUTING_GAP
                base_y = pos[producer_idx][1]
                count = len(from_indices)
                for i, from_idx in enumerate(from_indices):
                    ideal_x = base_x
                    if count == 1:
                        ideal_y = base_y
                    else:
                        ideal_y = base_y + (i - (count - 1) / 2.0) * SIGNAL_GAP_Y
                    _place_near_anchor(from_idx, ideal_x, ideal_y,
                                       SIGNAL_BLOCK_W, SIGNAL_BLOCK_H)

            # --- Place signal_out (To) blocks ---
            consumer_to_tos: Dict[int, List[int]] = {}
            for from_idx, to_idx, producer_idx, consumer_idx in routing_pairs:
                consumer_to_tos.setdefault(consumer_idx, []).append(to_idx)
            for consumer_idx, to_indices in consumer_to_tos.items():
                for i, to_idx in enumerate(to_indices):
                    ideal_x = pos[consumer_idx][0] - SIGNAL_BLOCK_W - ROUTING_GAP
                    ideal_y = pos[consumer_idx][1]
                    _place_near_anchor(to_idx, ideal_x, ideal_y,
                                       SIGNAL_BLOCK_W, SIGNAL_BLOCK_H)

        # --- Global overlap resolution ---
        # After all blocks are placed, resolve any remaining overlaps
        # between ANY two blocks (functional vs functional, routing vs any, etc.)
        GLOBAL_FUNC_W = 160.0
        GLOBAL_FUNC_H = 70.0
        GLOBAL_SIG_W = 140.0
        GLOBAL_SIG_H = 70.0
        GLOBAL_GAP = 15.0
        is_sig = {i for i, t in from_to_tpe.items() if t in ("signal_in", "signal_out")}

        # Rebuild connection corridors for the overlap check
        global_corridors: List[Tuple[float, float, float, float]] = []
        for i in range(n):
            if i in is_sig:
                continue
            for p in dep_graph.get(i, set()):
                if p in is_sig:
                    continue
                pr = pos[p][0] + GLOBAL_FUNC_W
                il = pos[i][0]
                if pr >= il:
                    continue
                pc = pos[p][1] + GLOBAL_FUNC_H / 2.0
                ic = pos[i][1] + GLOBAL_FUNC_H / 2.0
                global_corridors.append((pr, min(pc, ic), il, max(pc, ic)))

        def _global_rects_overlap(a, b):
            return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

        for iteration in range(40):
            any_sep = False
            # Build rects for current positions
            rects = []
            for idx in range(n):
                w = GLOBAL_SIG_W if idx in is_sig else GLOBAL_FUNC_W
                h = GLOBAL_SIG_H if idx in is_sig else GLOBAL_FUNC_H
                rects.append((pos[idx][0], pos[idx][1], pos[idx][0] + w, pos[idx][1] + h))

            for i in range(n):
                for j in range(i + 1, n):
                    if not _global_rects_overlap(rects[i], rects[j]):
                        continue
                    any_sep = True
                    ri = rects[i]
                    rj = rects[j]
                    overlap_x = min(ri[2], rj[2]) - max(ri[0], rj[0])
                    overlap_y = min(ri[3], rj[3]) - max(ri[1], rj[1])
                    if overlap_y < overlap_x:
                        dir_y = 1.0 if pos[i][1] < pos[j][1] else -1.0
                        push = overlap_y + GLOBAL_GAP
                        pos[i][1] -= dir_y * push * 0.5
                        pos[j][1] += dir_y * push * 0.5
                    else:
                        dir_x = 1.0 if pos[i][0] < pos[j][0] else -1.0
                        push = overlap_x + GLOBAL_GAP
                        pos[i][0] -= dir_x * push * 0.5
                        pos[j][0] += dir_x * push * 0.5

            # Also check routing blocks against connection corridors
            for idx in range(n):
                if idx not in is_sig:
                    continue
                w = GLOBAL_SIG_W
                h = GLOBAL_SIG_H
                br = (pos[idx][0], pos[idx][1], pos[idx][0] + w, pos[idx][1] + h)
                for c in global_corridors:
                    if _global_rects_overlap(br, c):
                        any_sep = True
                        overlap_y = min(br[3], c[3]) - max(br[1], c[1])
                        dir_y = 1.0 if pos[idx][1] + h / 2 < (c[1] + c[3]) / 2 else -1.0
                        pos[idx][1] += dir_y * (overlap_y + GLOBAL_GAP)
                        break

            if not any_sep:
                break

        # --- Normalize to positive coordinates ---
        min_x = min(p[0] for p in pos.values())
        min_y = min(p[1] for p in pos.values())
        return {
            i: (pos[i][0] - min_x + MARGIN_X, pos[i][1] - min_y + MARGIN_Y)
            for i in range(n)
        }

    def _find_output_port(self, blk: Block, var: sym.Var) -> int | None:
        for i, v in enumerate(blk.out_vars):
            if v.non_mutable_uid == var.non_mutable_uid:
                return i
        for i, v in enumerate(blk.algebraic_vars):
            if v.non_mutable_uid == var.non_mutable_uid:
                if i < len(blk.out_vars if blk.out_vars else []):
                    return i
                return i
        for i, v in enumerate(blk.state_vars):
            if v.non_mutable_uid == var.non_mutable_uid:
                return i
        return None

    def _find_or_create_input_port(self, blk: Block, var: sym.Var) -> int | None:
        for i, v in enumerate(blk.in_vars):
            if v.non_mutable_uid == var.non_mutable_uid:
                return i
        blk.in_vars.append(var)
        return len(blk.in_vars) - 1
