# VeraGridEngine Module: src/VeraGridEngine/Utils/procedural_logic.py

- Original source path: `src/VeraGridEngine/Utils/procedural_logic.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 9
- Top-level function count: 43
- Representative imports: __future__, typing, numpy, VeraGridEngine.Simulations.EMT.problems.emt_problem_template, VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: _expr_like_to_dict(expr)

Serialize a symbolic expression or comparison used by procedural logic.

## Function: _expr_like_from_dict(data)

Deserialize a symbolic expression or comparison used by procedural logic.

## Function: _subs_expr_like(expr, mapping)

Apply a variable substitution to a procedural expression.

## Function: _build_name_mapping(var_mapping)

Build a name-to-name remapping from a generic variable substitution map.

## Function: _get_expr_like_field(data, key)

Return one serialized procedural-expression field as a dictionary.

## Function: _coerce_var_name(var_or_name)

Normalize a variable reference to its string name.

## Function: _bool_expr(expr)

Convert a boolean-like procedural input into a symbolic expression.

## Function: _value_expr(expr)

Convert a procedural scalar input into a symbolic expression.

## Function: bool_and(*args)

Build the boolean AND of one or more procedural expressions.

## Function: bool_or(*args)

Build the boolean OR of one or more procedural expressions.

## Function: bool_not(arg)

Build the boolean NOT of one procedural expression.

## Function: bool_nand(*args)

Build the boolean NAND of one or more procedural expressions.

## Function: bool_nor(*args)

Build the boolean NOR of one or more procedural expressions.

## Function: bool_eor(left, right)

Build the exclusive-OR of two procedural expressions.

## Function: select(boolexpr, when_true, when_false)

Reject equation-level select usage in the public procedural API.

## Function: ifelse(boolexpr, when_true, when_false)

Reject equation-level ifelse usage in the public procedural API.

## Class: ProceduralLogicBase

- Bases: none
- Summary: Base class for procedural logic objects attached to symbolic blocks.

### Methods

- `bind(self, problem)`
  Summary: Bind the logic to a concrete EMT problem.
- `update(self, t, x, params)`
  Summary: Update mode or event parameters before the Newton step.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the next exact event time inside the interval if known.
- `remap(self, var_mapping)`
  Summary: Clone one logic entry under a variable remapping.
- `_get_problem(self)`
  Summary: Return the bound EMT problem.
- `_get_sample_time(self, t)`
  Summary: Return the accepted sample time associated with the current update.
- `_eval_numeric(self, expr, t, x, params)`
  Summary: Evaluate a procedural expression against the accepted EMT state.
- `_eval_bool(self, expr, t, x, params)`
  Summary: Evaluate one procedural condition using the accepted EMT state.

## Class: FixedSampleLogic

- Bases: ProceduralLogicBase
- Summary: Retain the initial truth value of one condition in a runtime mode variable.

### Methods

- `bind(self, problem)`
  Summary: Resolve the runtime output slot for this logic entry.
- `update(self, t, x, params)`
  Summary: Sample the condition once and keep it fixed afterwards.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: SampledValueLogic

- Bases: ProceduralLogicBase
- Summary: Sample one expression at each accepted step and store it in a runtime mode variable.

### Methods

- `bind(self, problem)`
  Summary: Resolve the runtime output slot for this sampled value.
- `update(self, t, x, params)`
  Summary: Refresh the sampled value using the accepted state.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: FlipFlopLogic

- Bases: ProceduralLogicBase
- Summary: Store a binary set/reset latch in a runtime mode variable.

### Methods

- `bind(self, problem)`
  Summary: Resolve the runtime output slot for the latch state.
- `update(self, t, x, params)`
  Summary: Apply set/reset semantics and write the resulting latch state.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: AnalogFlipFlopLogic

- Bases: ProceduralLogicBase
- Summary: Store an analog value when a set/reset latch enters the high state.

### Methods

- `bind(self, problem)`
  Summary: Resolve the runtime output slot and reset the analog latch state.
- `update(self, t, x, params)`
  Summary: Apply analog set/reset semantics and update the held value.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: PickupDropoffLogic

- Bases: ProceduralLogicBase
- Summary: Implement a delayed pickup/dropoff relay with retained binary state.

### Methods

- `bind(self, problem)`
  Summary: Resolve the runtime output slot and clear the relay timers.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the next exact pickup or dropoff event inside one step.
- `_eval_delay(self, expr, t, x, params)`
  Summary: Evaluate one relay delay expression and clamp it to a non-negative value.
- `update(self, t, x, params)`
  Summary: Advance the relay timers and binary state.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: ResetOnRisingEdgeLogic

- Bases: ProceduralLogicBase
- Summary: Apply one value reset on the rising edge of a procedural condition.

### Methods

- `bind(self, problem)`
  Summary: Resolve whether the reset target is a state variable or a runtime parameter.
- `update(self, t, x, params)`
  Summary: Apply the reset value only on the rising edge of the reset condition.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Function: fixed_sample(output, when, name)

Build a fixed-sample selector that stores a boolean condition at initialization.

## Function: selfix(boolexpr, output, name)

Build the procedural equivalent of PowerFactory ``selfix``.

## Function: selfix_const(boolexpr, output, name)

Build the procedural equivalent of PowerFactory ``selfix_const``.

## Function: sampled_value(output, source, name)

Build a sampled runtime value updated outside the Newton residual.

## Function: lastvalue(input_expr, output, name)

Build the procedural equivalent of PowerFactory ``lastvalue``.

## Function: flipflop(boolset, boolreset, output, name)

Build the procedural equivalent of PowerFactory ``flipflop``.

## Function: aflipflop(x, boolset, boolreset, output, name)

Build the procedural equivalent of PowerFactory ``aflipflop``.

## Function: pickup_dropoff(output, boolexpr, Tpick, Tdrop, name)

Build a pickup/dropoff relay-style procedural logic entry.

## Function: picdro(boolexpr, Tpick, Tdrop, output, name)

Build the procedural equivalent of PowerFactory ``picdro``.

## Function: picdro_const(boolexpr, Tpick, Tdrop, output, name)

Build the procedural equivalent of PowerFactory ``picdro_const``.

## Function: reset(var, rst, val, name)

Build the procedural equivalent of PowerFactory ``reset``.

## Function: _iter_block_vars(block)

Collect all variables reachable from one block tree.

## Function: _find_var_by_name(block, var_name)

Find one symbolic variable by name inside a block tree.

## Class: DelayedThresholdLatchLogic

- Bases: ProceduralLogicBase
- Summary: Comparator + timer + latch procedural logic for runtime modes.

### Methods

- `bind(self, problem)`
  Summary: Resolve the monitored state and runtime mode indices.
- `_append_trace_point(self, trace_time, measured_value, comparator, timer_armed, latched, mode_value)`
  Summary: Append one point to the internal tracing arrays.
- `_record_sample_trace(self, sample_time, measured_value, params)`
  Summary: Record one trace point at the accepted physical sample time.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the next exact trip or reset event inside one solver step.
- `update(self, t, x, params)`
  Summary: Advance the delayed-threshold latch logic and tracing state.
- `get_trace_arrays(self)`
  Summary: Return the internal trace arrays as dense numpy arrays.
- `remap(self, var_mapping)`
  Summary: Clone the logic under a variable remapping.

## Class: BlockProceduralLogicUpdater

- Bases: BoundaryUpdateWrapper
- Summary: Boundary updater that delegates runtime decisions to block-attached procedural logic entries.

### Methods

- `update(self, t, x, params)`
  Summary: Forward one runtime update to all procedural logic entries.
- `get_next_forced_event_time(self, t_prev, t_target)`
  Summary: Return the earliest forced event requested by any procedural logic entry.

## Function: _base_logic_data(entry)

Serialize the common metadata shared by all procedural logic entries.

## Function: procedural_logic_entry_to_dict(entry)

Serialize one procedural logic entry.

## Function: _fixed_sample_logic_from_dict(data)

Deserialize one fixed-sample procedural logic entry.

## Function: _sampled_value_logic_from_dict(data)

Deserialize one sampled-value procedural logic entry.

## Function: _flipflop_logic_from_dict(data)

Deserialize one flip-flop procedural logic entry.

## Function: _analog_flipflop_logic_from_dict(data)

Deserialize one analog flip-flop procedural logic entry.

## Function: _pickup_dropoff_logic_from_dict(data)

Deserialize one pickup/dropoff procedural logic entry.

## Function: _reset_on_rising_edge_logic_from_dict(data)

Deserialize one reset-on-rising-edge procedural logic entry.

## Function: _delayed_threshold_latch_logic_from_dict(data)

Deserialize one delayed-threshold-latch procedural logic entry.

## Function: build_procedural_logic_entry(data)

Deserialize one procedural logic entry.

## Function: procedural_logic_to_dict(entries)

Serialize a list of procedural logic entries.

## Function: procedural_logic_from_dict(entries)

Deserialize a list of procedural logic entries.

## Function: clone_procedural_logic_entries(entries, var_mapping)

Clone procedural logic entries under a variable remapping.

## Function: build_boundary_updater_from_block(problem)

Build a boundary updater from ``problem.sys_block.procedural_logic``.
