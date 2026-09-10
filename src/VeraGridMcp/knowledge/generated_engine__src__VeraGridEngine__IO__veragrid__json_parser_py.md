# VeraGridEngine Module: src/VeraGridEngine/IO/veragrid/json_parser.py

- Original source path: `src/VeraGridEngine/IO/veragrid/json_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 12
- Representative imports: __future__, json, typing, warnings, numpy, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.IO.veragrid.contingency_parser, VeraGridEngine.IO.veragrid.generic_io_functions, VeraGridEngine.Devices,  VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Simulations.driver_template, VeraGridEngine.enumerations

## Function: add_to_dict(main_dict, data_to_append, key)

Append d2 into a list of d at the key

## Function: add_to_dict2(main_dict, data, key)

Add data to the main dictionary at the given key if it does not exists already

## Function: profile_to_json(profile)

Convert a Profile to a json dictionary

## Function: json_to_profile(profile, d)

Assign a json profile to a Profile object

## Function: get_profiles_dict(elm)

:return:

## Function: parse_json_data(data)

Parse JSON structure into VeraGrid MultiCircuit

## Function: set_object_properties(elm, prop, entry)

Set the properties of an object

## Function: parse_json_data_v3(data, logger)

Json parser for V3

## Function: parse_json_data_v2(data, logger)

New Json parser

## Function: parse_json(file_name)

Parse JSON file into Circuit

## Function: get_obj_ref(elm)

get the idtag and if none return an empty str

## Function: save_json_file_v3(file_path, circuit, simulation_drivers)

Save JSON file
