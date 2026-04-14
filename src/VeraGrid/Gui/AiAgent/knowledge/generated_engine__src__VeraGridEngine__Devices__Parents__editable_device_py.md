# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/editable_device.py

- Original source path: `src/VeraGridEngine/Devices/Parents/editable_device.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 4
- Top-level function count: 5
- Representative imports: __future__, random, uuid, numpy, pandas, VeraGridEngine,  typing, VeraGridEngine.basic_structures, VeraGridEngine.enumerations

## Function: uuid2idtag(val)

Remove the useless characters and format as a proper 32-char UID

## Function: parse_idtag(val)

idtag setter

## Function: smart_compare(a, b, atol)

Compares two Python objects with tolerance for numerical values.

## Class: GCProp

- Bases: none
- Summary: VeraGrid property, this class must remain immutable

### Methods

- `name(self)`
  Summary: Property name.
- `units(self)`
  Summary: Property units.
- `tpe(self)`
  Summary: Property type.
- `definition(self)`
  Summary: Property definition.
- `profile_name(self)`
  Summary: Linked profile name.
- `display(self)`
  Summary: Display flag.
- `editable(self)`
  Summary: Editable flag.
- `old_names(self)`
  Summary: Compatibility aliases.
- `is_color(self)`
  Summary: Color flag.
- `is_date(self)`
  Summary: Date flag.
- `has_profile(self)`
  Summary: Check if this property has an associated profile
- `get_class_name(self)`
  Summary: Convert the class name to a string
- `get_dict(self)`
  Summary: Get the values of this property as a dictionary

## Function: get_action_symbol(action)

:param action:

## Function: get_at(snapshot_val, profile, t)

Get a GCPROP_TYPES value from a snapshot or a profile

## Class: EditableDeviceMeta

- Bases: type
- Summary: Metaclass that pre-builds inherited class schema declarations.

### Methods

- No methods detected.

## Class: PropertyChanges

- Bases: none
- Summary: No docstring provided.

### Methods

- `set(self, property_name, selected)`
  Summary: Set merge-selection state for one property in this instance.
- `get(self, property_name)`
  Summary: Query merge-selection state for one property in this instance.
- `to_dict(self)`
  Summary: No docstring provided.
- `parse(self, data)`
  Summary: No docstring provided.
- `copy(self)`
  Summary: No docstring provided.

## Class: EditableDevice

- Bases: none
- Summary: This is the main device class from which all inherit

### Methods

- `property_list(self)`
  Summary: Class-level property list exposed as read-only instance view.
- `registered_properties(self)`
  Summary: Class-level registered properties exposed as read-only instance view.
- `non_editable_properties(self)`
  Summary: Class-level non-editable property names exposed as read-only instance view.
- `properties_with_profile(self)`
  Summary: Class-level property/profile map exposed as read-only instance view.
- `set_diff_change(self, property_name, selected)`
  Summary: Set merge-selection state for one property in this instance.
- `get_diff_change_selected(self, property_name)`
  Summary: Query merge-selection state for one property in this instance.
- `get_all_diff_changes_dict(self)`
  Summary: Get the dictionary of all diff changes
- `iter_properties_selected_to_merge(self)`
  Summary: Iterate over properties selected to be merged for this instance.
- `auto_update_enabled(self)`
  Summary: :return:
- `enable_auto_updates(self)`
  Summary: :return:
- `disable_auto_updates(self)`
  Summary: :return:
- `get_uuid(self)`
  Summary: If the idtag property looks like a UUID, it adds the dashes
- `idtag(self)`
  Summary: idtag getter
- `idtag(self, val)`
  Summary: idtag setter
- `code(self)`
  Summary: code getter
- `code(self, val)`
  Summary: code setter
- `rdfid(self)`
  Summary: No docstring provided.
- `rdfid(self, val)`
  Summary: No docstring provided.
- `flatten_idtag(self)`
  Summary: Remove useless underscore (_) and dash (-)
- `type_name(self)`
  Summary: Name of the device type
- `get_rdfid(self)`
  Summary: Convert the idtag to RDFID
- `register(self, key, tpe, units, definition, profile_name, display, editable, old_names, is_color, is_date)`
  Summary: Runtime registration is intentionally disabled.
- `get_property_name_replacements_dict(self)`
  Summary: Get dictionary of old names related to their current name
- `generate_uuid(self)`
  Summary: Generate new UUID for the idtag property
- `name(self)`
  Summary: Name of the object
- `name(self, val)`
  Summary: No docstring provided.
- `get_save_data(self)`
  Summary: Return the data that matches the edit_headers
- `get_headers(self)`
  Summary: Return a list of headers
- `get_number_of_properties(self)`
  Summary: Return the number of registered properties
- `get_properties_containing_object(self, obj)`
  Summary: Return the list of properties that contain a certain object
- `get_association_properties(self)`
  Summary: Return the list of properties that contain associate another type
- `get_snapshot_value(self, prop)`
  Summary: Return the stored object value from the property index
- `set_snapshot_value(self, property_name, value)`
  Summary: Set the value of a snapshot property
- `get_snapshot_value_by_name(self, name)`
  Summary: Return the stored object value from the property index
- `get_property_value(self, prop, t_idx)`
  Summary: Return the stored object value from the property index
- `get_property_by_idx(self, property_idx)`
  Summary: Return the stored object value from the property index
- `get_property_by_name(self, prop_name)`
  Summary: :param prop_name:
- `get_property_value_by_idx(self, property_idx, t_idx)`
  Summary: Return the stored object value from the property index
- `set_profile(self, prop, arr)`
  Summary: Set the profile from eithr an array or an actual profile object
- `set_profile_array(self, magnitude, arr)`
  Summary: Set the profile from eithr an array or an actual profile object
- `set_property_value(self, prop, value, t_idx)`
  Summary: Return the stored object value from the property index
- `get_value(self, prop, t_idx)`
  Summary: Return value regardless of the property index
- `set_value(self, prop, t_idx, value)`
  Summary: Return value regardless of the property index
- `create_profiles(self, index)`
  Summary: Create the load object default profiles
- `resize_profiles(self, index, time_frame)`
  Summary: Resize the profiles in this object
- `create_profile(self, magnitude, index)`
  Summary: Create power profile based on index
- `ensure_profiles_exist(self, index, set_profile_default_as_snapshot)`
  Summary: It might be that when loading the VeraGrid Model has properties that the file has not.
- `delete_profiles(self)`
  Summary: Delete the object profiles (set all to None)
- `resample_profiles(self, indices)`
  Summary: re-sample the object profiles (set all to None)
- `set_profile_values(self, t)`
  Summary: Set the profile values at t
- `get_profile(self, magnitude)`
  Summary: Get the profile of a property name
- `get_profile_by_prop(self, prop)`
  Summary: Get the profile of a property name
- `copy(self, forced_new_idtag)`
  Summary: Create a deep copy of this object
- `rgb2hex(r, g, b)`
  Summary: Convert R, G, B to hexadecimal tuple
- `hex2rgb(hexcode)`
  Summary: Convert hexadecimal string to rgb tuple
- `rnd_color(self)`
  Summary: Generate random colour
- `new_idtag(self)`
  Summary: Generate a new IdTag
- `replace_objects(self, old_object, new_obj, logger)`
  Summary: Replace object in this objects' properties
- `rebind_device_references(self, objects_by_idtag, props)`
  Summary: Rebind direct device-pointer properties to equivalent objects from a target lookup.
- `compare(self, other, logger, detailed_profile_comparison, nt)`
  Summary: Compare two objects
