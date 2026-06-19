from __future__ import annotations

from collections import deque
from typing import List, Tuple, Dict, Optional, Any, Set
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import BlockType

try:
    from VeraGridEngine.Utils.Symbolic.hierarchical_layout_v2 import compute_layout as _compute_layout_v2
    _HAVE_LAYOUT_V2 = True
except ImportError as e:
    _HAVE_LAYOUT_V2 = False
    _layout_import_error = str(e)

def build_diagram_regular_blocks(children: List[Block],
                                 connection_tpe: Dict[int, str] | None = None) -> Tuple[BlockDiagram, List[Block]]:
    diagram = BlockDiagram()

    if not children:
        return diagram, children

    original_count = len(children)

    # ---- PASS 1: Build producer map from out_vars ----
    var_to_producer_block: Dict[int, int] = {}
    for i, blk in enumerate(children):
        for v in blk.out_vars:
            var_to_producer_block[v.non_mutable_uid] = i

    # ---- PASS 2: Detect consumers from in_vars (works regardless of order) ----
    var_consumers: Dict[int, List[int]] = {}
    block_input_ports: List[Dict[int, int]] = [{} for _ in range(original_count)]
    for i, blk in enumerate(children):
        ports = block_input_ports[i]
        for idx, v in enumerate(blk.in_vars):
            ports[v.non_mutable_uid] = idx
            producer = var_to_producer_block.get(v.non_mutable_uid)
            if producer is not None and producer != i:
                var_consumers.setdefault(v.non_mutable_uid, []).append(i)

    # ---- Pre-build output port index lookup ----
    block_output_ports: List[Dict[int, int]] = [{} for _ in range(original_count)]
    for i, blk in enumerate(children):
        ports = block_output_ports[i]
        for idx, v in enumerate(blk.out_vars):
            ports[v.non_mutable_uid] = idx

    original_var_to_producer = dict(var_to_producer_block)

    # ---- Map (producer_idx, consumer_idx) -> list of (var_uid, src_port, dst_port) ----
    pair_to_vars: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
    for i in range(original_count):
        blk = children[i]
        for port_idx, in_var in enumerate(blk.in_vars):
            producer = original_var_to_producer.get(in_var.non_mutable_uid)
            if producer is not None and producer != i:
                src_port = block_output_ports[producer].get(in_var.non_mutable_uid)
                if src_port is not None:
                    pair_to_vars.setdefault((producer, i), []).append(
                        (in_var.non_mutable_uid, src_port, port_idx)
                    )

    # --- Create From/To pairs for fan-out variables ---
    new_children: List[Block] = list(children)
    fan_out_pairs: List[Tuple[int, int, int, int]] = []
    pair_counter = 0
    from_to_tpe: Dict[int, str] = {}

    for var_uid, consumer_indices in var_consumers.items():
        if len(consumer_indices) < 2:
            continue
        v = None
        for ci in consumer_indices:
            for iv in children[ci].in_vars:
                if iv.non_mutable_uid == var_uid:
                    v = iv
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

    # ---- Build dependency graph (producer -> consumer direction) ----
    dep_graph: Dict[int, set] = {i: set() for i in range(len(children))}

    for (producer, consumer) in pair_to_vars:
        dep_graph[producer].add(consumer)

    for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
        producer_idx = original_var_to_producer.get(var_uid)
        if producer_idx is not None:
            dep_graph[producer_idx].add(from_idx)
        dep_graph[from_idx].add(to_idx)
        dep_graph[to_idx].add(consumer_idx)

    # ---- Debug: print dependency graph ----
    for node, deps in dep_graph.items():
        print(
            children[node].name,
            "->",
            [children[c].name for c in sorted(deps)]
        )

    # ---- layout: v2 (Sugiyama-inspired) or fallback ----
    # _compute_layout_v2 expects dep_graph[consumer] = {producers}
    # so invert producer->consumer to consumer->producer
    positions_by_uid: Dict[int, Tuple[float, float]] = {}
    if _HAVE_LAYOUT_V2:
        layout_graph: Dict[int, Set[int]] = {i: set() for i in range(len(children))}
        for p, consumers in dep_graph.items():
            for c in consumers:
                layout_graph[c].add(p)
        pos_by_idx = _compute_layout_v2(
            len(children), layout_graph, from_to_tpe,
        )
        for i, pos in pos_by_idx.items():
            positions_by_uid[children[i].uid] = pos

    for i, blk in enumerate(children):
        x, y = positions_by_uid.get(blk.uid, (80.0, 60.0))
        tpe = from_to_tpe.get(i, "")
        if not tpe and connection_tpe:
            tpe = connection_tpe.get(blk.uid, tpe)
        diagram.add_node(
            name=blk.name if blk.name else f"block_{i}",
            x=x,
            y=y,
            tpe=tpe,
            device_uid=blk.uid,
            color="#C0C0C0",
        )

    # ---- Build connections from dep_graph (original blocks only) ----
    con_uid_counter = 0
    for p_idx, consumers in dep_graph.items():
        for c_idx in consumers:
            var_infos = pair_to_vars.get((p_idx, c_idx))
            if var_infos is None:
                continue
            for var_uid, src_port, dst_port in var_infos:
                con_uid_counter += 1
                diagram.add_branch(
                    connectionitem_uid=con_uid_counter,
                    device_uid_from=children[p_idx].uid,
                    device_uid_to=children[c_idx].uid,
                    port_number_from=src_port,
                    port_number_to=dst_port,
                    color="#587291",
                )

    # ---- Fan-out connections: Producer -> From, To -> Consumer ----
    for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
        producer_idx = original_var_to_producer.get(var_uid)
        if producer_idx is None:
            continue
        src_port = block_output_ports[producer_idx].get(var_uid)
        if src_port is not None:
            con_uid_counter += 1
            diagram.add_branch(
                connectionitem_uid=con_uid_counter,
                device_uid_from=children[producer_idx].uid,
                device_uid_to=children[from_idx].uid,
                port_number_from=src_port,
                port_number_to=0,
                color="#587291",
            )
        dst_port = block_input_ports[consumer_idx].get(var_uid)
        if dst_port is not None:
            con_uid_counter += 1
            diagram.add_branch(
                connectionitem_uid=con_uid_counter,
                device_uid_from=children[to_idx].uid,
                device_uid_to=children[consumer_idx].uid,
                port_number_from=0,
                port_number_to=dst_port,
                color="#587291",
            )

    return diagram, children


def build_diagram(children: List[Block],
                  connection_tpe: Dict[int, str] | None = None) -> Tuple[BlockDiagram, List[Block]]:
    diagram = BlockDiagram()

    if not children:
        return diagram, children

    original_count = len(children)

    # Single combined pass: producer map + consumer detection + port caches + eq vars cache
    var_to_producer_block: Dict[int, int] = {}
    var_consumers: Dict[int, List[int]] = {}
    block_output_ports: List[Dict[int, int]] = [{} for _ in range(original_count)]
    eq_vars_cache: Dict[int, List[Any]] = {}

    for i, blk in enumerate(children):
        for v in blk.algebraic_vars:
            var_to_producer_block[v.non_mutable_uid] = i
        for v in blk.state_vars:
            var_to_producer_block[v.non_mutable_uid] = i
        for v in blk.out_vars:
            var_to_producer_block[v.non_mutable_uid] = i

        for in_var in blk.in_vars:
            producer = var_to_producer_block.get(in_var.non_mutable_uid)
            if producer is not None and producer != i:
                var_consumers.setdefault(in_var.non_mutable_uid, []).append(i)

        for eq in (blk.state_eqs or []) + (blk.algebraic_eqs or []):
            eq_vars = eq.get_vars()
            eq_vars_cache[eq.uid] = eq_vars
            for v in eq_vars:
                producer = var_to_producer_block.get(v.non_mutable_uid)
                if producer is not None and producer != i:
                    consumers = var_consumers.setdefault(v.non_mutable_uid, [])
                    if i not in consumers:
                        consumers.append(i)

    # Pre-build output port index lookup per block
    for i, blk in enumerate(children):
        ports = block_output_ports[i]
        for idx, v in enumerate(blk.out_vars):
            ports[v.non_mutable_uid] = idx
        for idx, v in enumerate(blk.algebraic_vars):
            if v.non_mutable_uid not in ports:
                ports[v.non_mutable_uid] = idx
        for idx, v in enumerate(blk.state_vars):
            if v.non_mutable_uid not in ports:
                ports[v.non_mutable_uid] = idx

    original_var_to_producer = dict(var_to_producer_block)

    # --- Create From/To pairs for fan-out variables ---
    new_children: List[Block] = list(children)
    fan_out_pairs: List[Tuple[int, int, int, int]] = []
    fan_out_vars: Set[int] = set()
    pair_counter = 0
    from_to_tpe: Dict[int, str] = {}

    for var_uid, consumer_indices in var_consumers.items():
        if len(consumer_indices) < 2:
            continue
        fan_out_vars.add(var_uid)
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
                    for ev in eq_vars_cache.get(eq.uid, eq.get_vars()):
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

    # --- Rebuild var_to_producer_block with all children ---
    var_to_producer_block = {}
    for i, blk in enumerate(children):
        for v in blk.algebraic_vars:
            var_to_producer_block[v.non_mutable_uid] = i
        for v in blk.state_vars:
            var_to_producer_block[v.non_mutable_uid] = i
        for v in blk.out_vars:
            var_to_producer_block[v.non_mutable_uid] = i

    # --- Build dependency graph using cached eq vars ---
    dep_graph: Dict[int, set] = {i: set() for i in range(len(children))}
    for i in range(original_count):
        blk = children[i]
        for in_var in blk.in_vars:
            producer = original_var_to_producer.get(in_var.non_mutable_uid)
            if producer is not None and producer != i:
                dep_graph[i].add(producer)
        for eq in (blk.state_eqs or []) + (blk.algebraic_eqs or []):
            for v in eq_vars_cache.get(eq.uid, ()):
                producer = original_var_to_producer.get(v.non_mutable_uid)
                if producer is not None and producer != i:
                    dep_graph[i].add(producer)

    for var_uid, from_idx, to_idx, consumer_idx in fan_out_pairs:
        producer_idx = original_var_to_producer.get(var_uid)
        if producer_idx is not None:
            dep_graph[from_idx].add(producer_idx)
        dep_graph[to_idx].add(from_idx)
        dep_graph[consumer_idx].discard(producer_idx)
        dep_graph[consumer_idx].add(to_idx)

    # ---- layout: v2 (Sugiyama-inspired) or fallback to legacy ----
    positions = {}
    if _HAVE_LAYOUT_V2:
        positions = _compute_layout_v2(
            len(children), dep_graph, from_to_tpe,
        )

    for i, blk in enumerate(children):
        x, y = positions.get(i, (80.0, 60.0))
        tpe = from_to_tpe.get(i, "")
        if not tpe and connection_tpe:
            tpe = connection_tpe.get(blk.uid, tpe)
        diagram.add_node(
            name=blk.name if blk.name else f"block_{i}",
            x=x,
            y=y,
            tpe=tpe,
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
        ports_in: Dict[int, int] = {}
        for idx, v in enumerate(blk.in_vars):
            ports_in[v.non_mutable_uid] = idx

        for port_idx, in_var in enumerate(blk.in_vars):
            producer = original_var_to_producer.get(in_var.non_mutable_uid)
            if producer is not None and producer != i:
                if (in_var.non_mutable_uid in fan_out_var_consumers and
                        i in fan_out_var_consumers[in_var.non_mutable_uid]):
                    continue
                src_port_idx = block_output_ports[producer].get(in_var.non_mutable_uid)
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

        for eq in blk.state_eqs or []:
            for v in eq_vars_cache.get(eq.uid, ()):
                producer = original_var_to_producer.get(v.non_mutable_uid)
                if producer is not None and producer != i:
                    if (v.non_mutable_uid in fan_out_var_consumers and
                            i in fan_out_var_consumers[v.non_mutable_uid]):
                        continue
                    src_port_idx = block_output_ports[producer].get(v.non_mutable_uid)
                    if src_port_idx is not None:
                        needed_input_port = ports_in.get(v.non_mutable_uid)
                        if needed_input_port is None:
                            needed_input_port = len(blk.in_vars)
                            blk.in_vars.append(v)
                            ports_in[v.non_mutable_uid] = needed_input_port
                        con_uid_counter += 1
                        diagram.add_branch(
                            connectionitem_uid=con_uid_counter,
                            device_uid_from=children[producer].uid,
                            device_uid_to=blk.uid,
                            port_number_from=src_port_idx,
                            port_number_to=needed_input_port,
                            color="#587291",
                        )

        for eq in blk.algebraic_eqs or []:
            for v in eq_vars_cache.get(eq.uid, ()):
                producer = original_var_to_producer.get(v.non_mutable_uid)
                if producer is not None and producer != i:
                    if (v.non_mutable_uid in fan_out_var_consumers and
                            i in fan_out_var_consumers[v.non_mutable_uid]):
                        continue
                    src_port_idx = block_output_ports[producer].get(v.non_mutable_uid)
                    if src_port_idx is not None:
                        needed_input_port = ports_in.get(v.non_mutable_uid)
                        if needed_input_port is None:
                            needed_input_port = len(blk.in_vars)
                            blk.in_vars.append(v)
                            ports_in[v.non_mutable_uid] = needed_input_port
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
        producer_idx = original_var_to_producer.get(var_uid)
        if producer_idx is None:
            continue
        src_port_idx = block_output_ports[producer_idx].get(var_uid)
        if src_port_idx is not None:
            con_uid_counter += 1
            diagram.add_branch(
                connectionitem_uid=con_uid_counter,
                device_uid_from=children[producer_idx].uid,
                device_uid_to=children[from_idx].uid,
                port_number_from=src_port_idx,
                port_number_to=0,
                color="#587291",
            )

        consumer_blk = children[consumer_idx]
        v = children[from_idx].in_vars[0]
        ports_in = {}
        for idx, iv in enumerate(consumer_blk.in_vars):
            ports_in[iv.non_mutable_uid] = idx
        needed_input_port = ports_in.get(var_uid)
        if needed_input_port is None:
            needed_input_port = len(consumer_blk.in_vars)
            consumer_blk.in_vars.append(v)
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

        # --- create connection blocks for input/output boundary ---
        # Input blocks first so their outputs are in the producer map
        # when equation blocks are processed.
        connection_tpe: Dict[int, str] = {}
        for in_var in block.in_vars:
            in_blk = Block(
                out_vars=[in_var],
                name=f"input_{in_var.name}",
                is_decomposable=False
            )
            child_blocks.append(in_blk)
            connection_tpe[in_blk.uid] = BlockType.INPUT_CONN.name

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
                                is_decomposable=False
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
                        is_decomposable=False
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
                        is_decomposable=False
                    )
                    block_eq_map[int_blk.uid] = eq_key
                    child_blocks.append(int_blk)
                var_to_block_output[var.non_mutable_uid] = var

        # Output blocks after equation blocks so their input vars' producers
        # (equation blocks) are already in the producer map.
        for out_var in block.out_vars:
            out_blk = Block(
                in_vars=[out_var],
                name=f"output_{out_var.name}",
                is_decomposable=False
            )
            child_blocks.append(out_blk)
            connection_tpe[out_blk.uid] = BlockType.OUTPUT_CONN.name

        # --- build diagram ---
        diagram, all_children = build_diagram(child_blocks, connection_tpe)

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
        queue = deque(k for k, v in in_degree.items() if v == 0)
        sorted_keys: List[str] = []

        while queue:
            node = queue.popleft()
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
                is_decomposable=False
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
            is_decomposable=False
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
                is_decomposable=False
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
            "floor": sym.floor, "ceil": sym.ceil, "heaviside": sym.heaviside,
        }

        if expr.op in func_map:
            f = func_map[expr.op]
            blk = Block(
                algebraic_vars=[y],
                algebraic_eqs=[y - f(inner_var)],
                in_vars=[inner_var],
                out_vars=[y],
                name=expr.op,
                is_decomposable=False
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
                is_decomposable=False
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

