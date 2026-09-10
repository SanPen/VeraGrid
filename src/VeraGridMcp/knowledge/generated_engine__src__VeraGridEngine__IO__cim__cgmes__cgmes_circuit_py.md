# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_circuit.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_circuit.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 3
- Top-level function count: 12
- Representative imports: typing, enum, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_2_4_15_assets, VeraGridEngine.IO.cim.cgmes.cgmes_assets.cgmes_3_0_0_assets, VeraGridEngine.data_logger, VeraGridEngine.IO.cim.cgmes.cgmes_property, VeraGridEngine.IO.base.base_circuit, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.IO.cim.cgmes.cgmes_typing, VeraGridEngine.IO.cim.cgmes.cgmes_data_parser, VeraGridEngine.enumerations

## Class: ReferenceIndex

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ReferenceResolutionContext

- Bases: none
- Summary: Cache-aware reference resolver context for one linking pass.

### Methods

- `_ensure_recovery_indexes(self)`
  Summary: Lazily build tolerant indexes only when recovery is actually needed.
- `resolve(self, token)`
  Summary: Resolve one token using strict cache first and tolerant cache second.

## Function: find_attribute(obj, property_name, association_inverse_dict)

:param obj:

## Function: normalize_reference_token(value)

Normalize a CGMES reference token to a canonical lookup string.

## Function: form_uuid_hyphenated(value)

Convert a 32-hex UUID token to hyphenated UUID form.

## Function: get_reference_candidates(value)

Build candidate reference keys for tolerant reference resolution.

## Function: get_reference_candidates_cached(value, reference_candidates_cache)

Fetch cached reference candidates for a token.

## Function: add_index_entry(index, key, obj)

Add an object to a reference index, tracking ambiguous keys.

## Function: build_reference_index(objects_dict)

Build tolerant reference index from subject IDs, UUIDs and mRIDs.

## Function: resolve_reference_token(token, all_objects_dict, all_objects_dict_boundary, enable_reference_recovery, model_index, boundary_index, reference_candidates_cache, resolution_cache)

Resolve reference token with strict and recovery fallback chains.

## Function: find_references(elements_by_type, all_objects_dict, all_objects_dict_boundary, association_inverse_dict, logger, mark_used, recovery_mode)

Replaces the references in the "actual" properties of the objects

## Function: convert_data_to_objects(data, all_objects_dict, all_objects_dict_boundary, elements_by_type, class_dict, association_inverse_dict, logger, cgmes_recovery_mode)

Convert CGMES data dictionaries to proper CGMES objects

## Function: convert_class_data_to_objects(class_name, objects_dict, object_template, all_objects_dict, all_objects_dict_boundary, logger)

Convert one CGMES class dictionary into instantiated CGMES objects.

## Function: is_valid_cgmes(cgmes_version)

Check if the version is CGMES

## Class: CgmesCircuit

- Bases: BaseCircuit
- Summary: CgmesCircuit

### Methods

- `assets(self)`
  Summary: :return:
- `parse_files(self, data_parser, delete_unused, detect_circular_references)`
  Summary: Parse CGMES files into this class
- `assign_data_to_lists(self)`
  Summary: Assign the data from all_objects_dict to the appropriate lists in the circuit
- `set_data(self, data, boundary_set)`
  Summary: :param data:
- `meta_programmer(self)`
  Summary: This function is here to help in the class programming by inverse engineering
- `add(self, elm)`
  Summary: Add generic object to the circuit
- `get_properties(self)`
  Summary: Get list of CIM properties
- `get_class_properties(self)`
  Summary: :return:
- `get_objects_list(self, elm_type)`
  Summary: :param elm_type:
- `emit_text(self, val)`
  Summary: :param val:
- `emit_progress(self, val)`
  Summary: :param val:
- `clear(self)`
  Summary: Clear the circuit
- `check_type(xml, class_types, starters, enders)`
  Summary: Checks if we are starting an object of the predefined types
- `delete_unused(self)`
  Summary: Delete elements that have no references to them
- `parse_xml_text(self, text_lines)`
  Summary: Fill the XML into the objects
- `get_data_frames_dictionary(self)`
  Summary: Get dictionary of DataFrames
- `to_excel(self, fname)`
  Summary: :param fname:
- `detect_circular_references(self)`
  Summary: Detect circular references
- `get_circular_references(self)`
  Summary: Detect circular references
- `get_model_xml(self, profiles)`
  Summary: Get a dictionary of xml per CGMES profile
