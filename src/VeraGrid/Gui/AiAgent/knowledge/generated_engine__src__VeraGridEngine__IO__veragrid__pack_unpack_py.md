# VeraGridEngine Module: src/VeraGridEngine/IO/veragrid/pack_unpack.py

- Original source path: `src/VeraGridEngine/IO/veragrid/pack_unpack.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 21
- Representative imports: __future__, copy, json, math, typing, pandas, numpy, enum, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices, VeraGridEngine.Devices.Parents.editable_device,  VeraGridEngine.Utils.Symbolic.symbolic_io, VeraGridEngine.Devices.types, VeraGridEngine.enumerations

## Function: get_objects_dictionary()

creates a dictionary with the types and the circuit objects

## Function: get_multiverse_node_metadata(metadata)

Extract the per-node metadata dictionary from a multiverse metadata payload.

## Function: order_multiverse_records(metadata)

Return multiverse metadata records in a parent-before-child order.

## Function: gather_model_as_data_frames(circuit, logger, legacy)

Pack the circuit information into tables (DataFrames)

## Function: profile_todict(profile)

Get a dictionary representation of the profile

## Function: profile_todict_idtag(profile)

Get a dictionary representation of the profile

## Function: profile_todict_str(profile)

Get a dictionary representation of the profile

## Function: get_profile_from_dict(profile, data, collection)

Create a profile from json dict data

## Function: veragrid_object_to_json(elm, block_saver)

:param elm:

## Function: gather_model_as_jsons(circuit)

Transform a MultiCircuit into a collection of Json files

## Function: search_property(template_elm, old_props_dict, property_to_search, logger)

Search for a property name in the template object registered properties and their old names

## Function: look_for_property(elm, property_name)

:param elm:

## Function: valid_value(val)

:param val:

## Function: look_in_collection_by_name(key, collection)

Look in a collection for an element by its name instead of by Idtag

## Class: CreatedOnTheFly

- Bases: none
- Summary: This class is to pack all those devices that are created "on the fly" to support legacy formats

### Methods

- `get_create_area(self, property_value)`
  Summary: :param property_value:
- `get_create_zone(self, property_value)`
  Summary: :param property_value:
- `get_create_substation(self, property_value)`
  Summary: :param property_value:
- `create_contingency(self, elm)`
  Summary: :param elm:
- `create_technology(self, elm, tech_name)`
  Summary: :param elm:

## Function: parse_object_type_from_dataframe(main_df, template_elm, elements_dict_by_type, time_profile, object_type_key, data, logger)

Convert a DataFrame to a list of VeraGrid devices

## Function: search_property_into_json(json_entry, prop)

Find property in Json entry

## Function: search_and_apply_json_profile(json_entry, gc_prop, elm, property_value, collection)

Search from the property profiles into the json and apply it

## Function: parse_object_type_from_json(template_elm, data_list, elements_dict_by_type, time_profile, block_parser, logger)

:param template_elm:

## Function: handle_legacy_jsons(model_data, elements_dict_by_type, logger)

Handle those legacy structures that were deprecated and removed from VeraGrid's structure

## Function: parse_veragrid_data(data, previous_circuit, text_func, progress_func, logger)

Interpret data

## Function: parse_multiverse_data(data, metadata, text_func, progress_func, logger)

:param data:
