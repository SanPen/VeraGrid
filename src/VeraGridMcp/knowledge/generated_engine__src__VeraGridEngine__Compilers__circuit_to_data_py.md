# VeraGridEngine Module: src/VeraGridEngine/Compilers/circuit_to_data.py

- Original source path: `src/VeraGridEngine/Compilers/circuit_to_data.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 23
- Representative imports: __future__, numpy, cmath, typing, VeraGridEngine.basic_structures, VeraGridEngine.Devices, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.Aggregation.area, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.Devices.types, VeraGridEngine.DataStructures.battery_data, VeraGridEngine.DataStructures.passive_branch_data, VeraGridEngine.DataStructures.active_branch_data, VeraGridEngine.DataStructures.bus_data, VeraGridEngine.DataStructures.generator_data

## Function: delta2StarAdmittance(Yab, Ybc, Yca)

Converts Delta to Star in admittances

## Function: set_bus_control_voltage(i, j, remote_control, bus_name, bus_voltage_used, bus_data, candidate_Vm, use_stored_guess, logger)

Set the bus control voltage

## Function: set_bus_control_voltage_vsc(i, j, remote_control, bus_name, bus_voltage_used, bus_data, candidate_Vm, use_stored_guess, logger)

Set the bus control voltage

## Function: set_bus_control_angle_vsc(i, j, remote_control, bus_name, bus_angle_used, bus_data, candidate_Va, use_stored_guess, logger)

Set the bus control angle

## Function: set_bus_control_voltage_hvdc(i, j, remote_control, bus_name, bus_voltage_used, bus_data, candidate_Vm, use_stored_guess, logger)

Set the bus control voltage

## Function: get_bus_data(bus_data, circuit, areas_dict, t_idx, use_stored_guess)

:param bus_data: BusData

## Function: get_load_data(data, circuit, bus_dict, bus_voltage_used, bus_data, t_idx, logger, opf_results, use_stored_guess, fill_three_phase)

:param data:

## Function: get_shunt_data(data, circuit, bus_dict, bus_voltage_used, bus_data, t_idx, logger, use_stored_guess, control_remote_voltage, fill_three_phase)

:param data:

## Function: fill_generator_parent(k, data, elm, bus_dict, bus_voltage_used, logger, bus_data, t_idx, use_stored_guess, control_remote_voltage, fill_three_phase)

Fill the common ancestor of generation and batteries

## Function: get_generator_data(data, circuit, bus_dict, bus_voltage_used, logger, bus_data, t_idx, opf_results, time_series, use_stored_guess, control_remote_voltage, fill_three_phase)

:param data:

## Function: get_battery_data(data, circuit, bus_dict, bus_voltage_used, logger, bus_data, t_idx, opf_results, time_series, use_stored_guess, control_remote_voltage, fill_three_phase)

:param data:

## Function: fill_parent_branch(i, elm, data, bus_data, bus_dict, bus_voltage_used, use_stored_guess, t_idx)

:param i:

## Function: fill_controllable_branch(ii, elm, data, ctrl_data, bus_data, bus_dict, t_idx, opf_results, use_stored_guess, bus_voltage_used, Sbase, control_taps_modules, control_taps_phase, logger)

:param ii:

## Function: get_branch_data(data, ctrl_data, circuit, bus_dict, bus_data, bus_voltage_used, apply_temperature, branch_tolerance_mode, t_idx, opf_results, use_stored_guess, control_taps_modules, control_taps_phase, logger, fill_three_phase)

Compile BranchData for a time step or the snapshot

## Function: set_control_dev(k, f, t, control, control_dev, control_val, control_bus_idx, control_branch_idx, bus_dict, bus_data, bus_voltage_used, bus_angle_used, use_stored_guess, logger)

:param k: device index

## Function: get_vsc_data(data, circuit, bus_dict, branch_dict, bus_data, bus_voltage_used, t_idx, opf_results, use_stored_guess, control_remote_voltage, logger)

Compile VscData for a time step or the snapshot

## Function: get_hvdc_data(data, circuit, bus_dict, bus_data, bus_voltage_used, t_idx, opf_results, use_stored_guess, logger)

:param data:

## Function: get_fluid_node_data(data, circuit, t_idx)

:param data:

## Function: get_fluid_turbine_data(data, circuit, plant_dict, gen_dict)

:param data:

## Function: get_fluid_pump_data(data, circuit, plant_dict, gen_dict)

:param data:

## Function: get_fluid_p2x_data(data, circuit, plant_dict, gen_dict)

:param data:

## Function: get_fluid_path_data(data, circuit, plant_dict)

:param data: FluidPathData

## Function: compile_numerical_circuit_at(circuit, t_idx, apply_temperature, branch_tolerance_mode, opf_results, use_stored_guess, bus_dict, areas_dict, control_taps_modules, control_taps_phase, control_remote_voltage, fill_gep, fill_three_phase, logger)

Compile a NumericalCircuit from a MultiCircuit
