# VeraGridEngine Module: src/VeraGridEngine/Templates/templates_common_functions.py

- Original source path: `src/VeraGridEngine/Templates/templates_common_functions.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 20
- Representative imports: __future__, numpy, typing, typing, VeraGridEngine, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.basic_structures, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.enumerations

## Function: tf_to_block(var_factory, num, den, x, y, create_state, name)

"transform definition" to block

## Function: tf_to_diffblock_with_output(var_factory, num, den, x, y, create_state, name)

num: list of numerator coefficients [b0, b1, ..., bm]

## Function: tf_to_block_with_states(var_factory, num, den, x, y, name)

num: numerator coefficients [b0,...,bm]

## Function: tf_to_block2(var_factory, num, den, x, y, name)

num: numerator coefficients [b0,...,bm]

## Function: to_implicit(block, vfactory)

Convert a block with explicit state equations to implicit form.

## Function: tf_to_diffblock_with_antiwindup(var_factory, num, den, x, y, name, sat_min, sat_max, multilinear, PI)

num: numerator coefficients [b0, ..., bm]

## Function: tf_to_diffblock_with_antiwindup_by_feedback(var_factory, num, den, x, y, name, sat_min, sat_max, Kaw)

Implements a back-calculation anti-windup controller using (u_sat - u) as feedback input.

## Function: discrete_control_block(var_factory, m, delta_m, m_max, m_min, v, v_ref, delta_v, ts, name)

No docstring provided.

## Function: deadband_block(var_factory, x, y, name, deadband)

Creates a deadband function block.

## Function: connect_line_rms_from(mdl1, mdl2)

This function substitutes input variables for output variables to connect two rms models

## Function: connect_line_rms_to(mdl1, mdl2)

This function substitutes input variables for output variables to connect two rms models

## Function: connect_line_phasor_rms_from(mdl1, mdl2)

Connect phasor RMS models for the 'from' end of a line.

## Function: connect_line_phasor_rms_to(mdl1, mdl2)

Connect phasor RMS models for the 'to' end of a line.

## Function: connect_models(mdl1, mdl2)

This function substitutes input variables for output variables to connect two rms models

## Function: set_rms_model(device, model, var_factory)

Set the RMS model

## Function: connect_line_emt_from(mdl1, mdl2)

Connects the bus voltages (mdl1) to the "from" side of the line (mdl2)

## Function: connect_line_emt_to(mdl1, mdl2)

Connects the bus voltages (mdl1) to the "to" side of the line (mdl2)

## Function: connect_vsc_emt_from(mdl1, mdl2, is_dc_bus)

Connects the bus voltages to the "from" side of the VSC model.

## Function: connect_vsc_emt_to(mdl1, mdl2, is_dc_bus)

Connects the bus voltages to the "to" side of the VSC model.

## Function: set_emt_model(device, model, var_factory)

Sets the EMT model for a given device, connects it to the bus(es),
