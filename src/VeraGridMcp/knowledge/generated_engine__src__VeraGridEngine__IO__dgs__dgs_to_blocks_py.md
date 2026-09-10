# VeraGridEngine Module: src/VeraGridEngine/IO/dgs/dgs_to_blocks.py

- Original source path: `src/VeraGridEngine/IO/dgs/dgs_to_blocks.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 10
- Top-level function count: 82
- Representative imports: __future__, ast, math, pprint, re, dataclasses, pathlib, typing, VeraGridEngine.IO.dgs.dgs_circuit, VeraGridEngine.IO.dgs.dgs_objects, VeraGridEngine.Utils.procedural_logic, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.enumerations

## Function: _safe_name(name)

No docstring provided.

## Function: _split_symbol_blob(raw)

No docstring provided.

## Function: _split_equation_statements(raw_equations)

No docstring provided.

## Function: classify_dgs_statement(statement)

Classify a single DGS equation statement.

## Function: build_blkdef_statement_support_report(blkdef)

Build a line-by-line support report for one DGS block definition.

## Function: summarize_blkdef_support_report(entries)

Count statuses and statement kinds from a support report.

## Function: _comparison_to_expr(obj)

No docstring provided.

## Class: ElmCompInstanceEntry

- Bases: none
- Summary: One direct instance declared inside an ElmComp through pblk/pelm.

### Methods

- No methods detected.

## Class: DgsBlockInstanceSelection

- Bases: none
- Summary: Selection result for a block resolved from the root ElmComp slots.

### Methods

- No methods detected.

## Class: UnsupportedDgsExpression

- Bases: Exception
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: _split_top_level_dsl_operator(expr, token)

No docstring provided.

## Function: _predeclare_statement_lhs_symbols(blkdef, symbol_table)

No docstring provided.

## Class: DgsExpressionParser

- Bases: ast.NodeVisitor
- Summary: No docstring provided.

### Methods

- `procedural_mode_defaults(self)`
  Summary: No docstring provided.
- `procedural_logic_entries(self)`
  Summary: No docstring provided.
- `_new_procedural_mode_var(self, prefix)`
  Summary: No docstring provided.
- `_get_time_var(self)`
  Summary: No docstring provided.
- `parse_procedural_statement(self, statement)`
  Summary: No docstring provided.
- `preprocess(self, expr)`
  Summary: No docstring provided.
- `parse(self, expr)`
  Summary: No docstring provided.
- `visit_Name(self, node)`
  Summary: No docstring provided.
- `visit_Constant(self, node)`
  Summary: No docstring provided.
- `visit_UnaryOp(self, node)`
  Summary: No docstring provided.
- `visit_BinOp(self, node)`
  Summary: No docstring provided.
- `visit_Compare(self, node)`
  Summary: No docstring provided.
- `visit_BoolOp(self, node)`
  Summary: No docstring provided.
- `visit_Call(self, node)`
  Summary: No docstring provided.
- `generic_visit(self, node)`
  Summary: No docstring provided.

## Class: ParsedDgsBlockDefinition

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: DgsRootBlockResult

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: DgsBlockSubgraphResult

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: GraphicConnectionInstruction

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: DgsGraphicTreeResult

- Bases: none
- Summary: Graphical internal tree reconstruction result.

### Methods

- No methods detected.

## Class: DgsStatementReportEntry

- Bases: none
- Summary: One line-by-line parsing report entry for a DGS block statement.

### Methods

- No methods detected.

## Function: _graph_to_serializable(graph)

No docstring provided.

## Function: _normalize_graph_signal_name(name)

No docstring provided.

## Function: _iter_blocks_recursive(block)

No docstring provided.

## Function: _make_identifier_map(block)

No docstring provided.

## Function: _expr_to_python(expr, identifier_map)

No docstring provided.

## Function: _const_or_expr_to_python(value, identifier_map)

No docstring provided.

## Function: _expr_to_python_natural(expr, identifier_map)

No docstring provided.

## Function: _expr_like_to_python(expr, identifier_map)

No docstring provided.

## Function: _iter_block_local_vars(block)

No docstring provided.

## Function: _find_local_var_by_name(block, var_name)

No docstring provided.

## Function: _procedural_logic_import_names(block)

No docstring provided.

## Function: _procedural_logic_entry_to_python(logic, block, identifier_map)

No docstring provided.

## Function: _emit_block_code(block, identifier_map, block_var_name, lines, child_ref_names)

No docstring provided.

## Function: _emit_template_style_module(result, subgraph, dgs_path, template_name)

No docstring provided.

## Function: _emit_tree_style_module(result, subgraph, dgs_path)

No docstring provided.

## Function: _clone_const_with_factory(value, const_factory)

No docstring provided.

## Function: _collect_block_vars_recursive(block, vars_out, consts_out)

No docstring provided.

## Function: materialize_block_with_var_factory(block_data, vf, name)

Recreate a serialized block using the target VarFactory and a runtime suffix.

## Function: _build_symbol_table(blkdef, shared_signals)

No docstring provided.

## Function: _parse_blkdef(blkdef, shared_signals)

No docstring provided.

## Function: _score_root_candidate(blkdef)

No docstring provided.

## Function: _select_root_element(circuit, parsed_blocks, root_name, root_typ_id)

No docstring provided.

## Function: _collect_reachable_blocks(root_blkdef, parsed_blocks)

No docstring provided.

## Function: _collect_internal_candidate_blocks(selected_block, parsed_blocks)

Collect candidate internal blocks for a selected composite block using only

## Function: _score_internal_candidate(selected_block, candidate_block)

Score how likely a block is to belong to the internal structure of a selected block.

## Function: _filter_internal_candidates(selected_block, candidates, min_score)

Filter candidate internal blocks using signal-overlap scoring.

## Function: _parameter_values_by_type_id(entries)

Build a unique parameter lookup keyed by block-definition identifier.

## Function: _build_block_from_parsed(parsed, shared_signals, parameter_values)

Materialize one parsed DGS block into a runtime Block.

## Function: _build_dependency_graph(parsed_blocks)

No docstring provided.

## Function: dgs_to_root_block(path, root_name, root_typ_id)

No docstring provided.

## Function: _build_direct_root_elmcomp_block(circuit, result)

Build a root ElmComp block using only its direct DGS child instances.

## Function: _build_dgs_element_index(circuit)

Build a flat DGS object index by identifier.

## Function: _build_blkdef_index(circuit)

Build a BlkDef index by identifier.

## Function: _build_graphic_node_index(circuit)

Build index of graphical-model DGS nodes by identifier.

## Function: build_graphic_node_index(circuit)

Build a public index of graphical DGS nodes by identifier.

## Function: _build_blksig_adjacency(circuit)

Build undirected adjacency graph over graphical nodes connected by BlkSig.

## Function: _graphic_connected_component(adjacency, root_id)

Return the connected component of a root graphical node.

## Function: _graphic_node_label(node)

Return a human-readable label for a graphical node.

## Function: _graphic_node_kind(node)

Return a short kind label for a graphical node.

## Function: _graphic_node_to_block(node_id, node, parsed_blocks)

Convert one graphical node into a lightweight Block for visualization.

## Function: _build_graphic_node_signal_map(circuit)

Collect normalized signal labels attached to each graphical node through BlkSig and BlkFrom definitions.

## Function: _build_graph_signal_alias_map(node_ids, node_by_id, node_signals)

No docstring provided.

## Function: _build_augmented_graphical_adjacency(node_ids, adjacency, node_by_id, node_signals, alias_map)

No docstring provided.

## Function: _graph_distance(adjacency, start_node, target_node)

No docstring provided.

## Function: _node_signal_aliases(node_id, node_signals, alias_map)

No docstring provided.

## Function: _resolve_graphic_block_connections(selected_block, child_node_ids, child_blocks, child_input_specs, child_output_specs, adjacency, node_by_id, node_signals, alias_map, root_runtime_block)

No docstring provided.

## Function: _blk_sum_slot_raw_mode(blk_sum, slot)

No docstring provided.

## Function: get_blk_sum_slot_raw_mode(blk_sum, slot)

Return the raw sign/mode code stored in a BlkSum input slot.

## Function: _blk_sum_slot_active_mode(blk_sum, slot)

No docstring provided.

## Function: get_blk_sum_slot_active_mode(blk_sum, slot)

Return the active sign/mode code stored in a BlkSum input slot.

## Function: _blk_sum_slot_mode(blk_sum, slot)

No docstring provided.

## Function: _blk_sum_signal_specs(blk_sum, circuit)

No docstring provided.

## Function: get_blk_sum_signal_specs(blk_sum, circuit)

Return the effective input terms and outputs of a DGS sum block.

## Function: _build_sum_block_from_graphic_node(blk_sum, circuit)

No docstring provided.

## Function: _selected_block_signal_universe(parsed_block)

Return the relevant signal universe of a selected composite block.

## Function: _rescue_graphic_internal_nodes(selected_block, node_by_id, node_signals, explicit_component)

Rescue disconnected graphical nodes whose signal labels belong to the selected composite universe.

## Function: extract_elmcomp_direct_instances(circuit, root_element)

Extract direct root instances from ElmComp pblk/pelm relations.

## Function: select_block_instance_from_root(circuit, result, slot_name)

Resolve a parsed block from the explicit root ElmComp slot mapping.

## Function: _reverse_dependency_graph(graph)

No docstring provided.

## Function: _closure_from_node(graph, start_node)

No docstring provided.

## Function: _select_named_block(parsed_blocks, block_name, block_id)

No docstring provided.

## Function: extract_named_block_subgraph(result, block_name, block_id, mode)

No docstring provided.

## Function: extract_named_block_internal_only(result, block_name, block_id)

Extract only the selected block without any dependency closure.

## Function: extract_root_slot_block_internal_only(dgs_path, slot_name, root_name, root_typ_id)

Extract the block associated to a root ElmComp slot and keep only that block.

## Function: extract_root_slot_block_internal_signal_tree(dgs_path, slot_name, root_name, root_typ_id)

Extract an internal hierarchy approximation for a selected root slot using

## Function: extract_root_slot_block_graphical_tree(dgs_path, slot_name, root_name, root_typ_id)

Extract the exact graphical internal tree of a root slot using BlkRef/BlkSig/BlkSum structures.

## Function: export_named_block_subgraph_to_python(dgs_path, output_path, block_name, block_id, root_name, root_typ_id, mode)

Export a selected DGS block subgraph as a standalone Python module.

## Function: export_named_block_subgraph_tree_to_python(dgs_path, output_path, block_name, block_id, root_name, root_typ_id, mode)

Export a selected DGS block subgraph as a serialized block-tree Python module.

## Function: export_root_slot_block_internal_signal_tree_to_python(dgs_path, output_path, slot_name, root_name, root_typ_id)

Export a root-slot internal signal-tree approximation as a serialized block-tree module.

## Function: export_root_slot_block_graphical_tree_to_python(dgs_path, output_path, slot_name, root_name, root_typ_id)

Export the exact graphical internal tree of a root slot as a serialized block-tree module.

## Function: export_root_slot_block_graphical_template_to_python(dgs_path, output_path, slot_name, root_name, root_typ_id)

Export the exact graphical tree of a root slot as a standalone EMT template module.

## Function: export_root_elmcomp_template_to_python(dgs_path, output_path, root_name, root_typ_id)

Export one root ElmComp as a standalone EMT template module.

## Function: export_root_slot_block_internal_signal_template_to_python(dgs_path, output_path, slot_name, root_name, root_typ_id)

Export a root-slot internal signal-tree approximation as an EMT template module.
