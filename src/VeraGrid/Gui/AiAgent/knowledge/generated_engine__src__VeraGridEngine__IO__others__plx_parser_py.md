# VeraGridEngine Module: src/VeraGridEngine/IO/others/plx_parser.py

- Original source path: `src/VeraGridEngine/IO/others/plx_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 11
- Top-level function count: 3
- Representative imports: os, datetime, pandas, numpy, enum, zipfile, xml.etree, VeraGridEngine.Devices, VeraGridEngine.Devices.multi_circuit

## Class: XmlDictConfig

- Bases: dict
- Summary: Note: need to add a root into if no exising

### Methods

- `update_shim(self, a_dict)`
  Summary: :param a_dict:

## Class: PlxBusMode

- Bases: Enum
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxElement

- Bases: none
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxNode

- Bases: PlxElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxGenerator

- Bases: PlxElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlexosBattery

- Bases: PlxGenerator
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxLine

- Bases: PlxElement
- Summary: No docstring provided.

### Methods

- `get_key(self, sep)`
  Summary: Split the name in the plexos way to get the new key
- `get_highest_voltage(self)`
  Summary: Return the highest voltage at which this line is connected
- `delete_zero_coordinates(self)`
  Summary: :return:
- `get_coordinates(self)`
  Summary: Get polyline of coordinates

## Class: PlxTransformer

- Bases: PlxLine
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxZone

- Bases: PlxElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxRegion

- Bases: PlxElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: PlxModel

- Bases: none
- Summary: No docstring provided.

### Methods

- `load_project_file(self, fname)`
  Summary: Load a PLEXOS project file
- `load_profile(self, path, zip_file_pointer)`
  Summary: Attempt loading the profile
- `load_profile_if_necessary(self, key, path, zip_file_pointer)`
  Summary: Load a profile is necessary
- `parse_zip(self, fname)`
  Summary: Parse zip file with the plexos xml and the profiles utilized
- `parse_excel(fname)`
  Summary: Parse excel export of the plexos file
- `parse_xml(self, fname, zip_file_pointer)`
  Summary: Parse PLEXOS file
- `parse_data(self, objects, memberships, properties, zip_file_pointer)`
  Summary: Pass the loaded DataFrames to model objects
- `get_buses_dictionary(self)`
  Summary: Get dictionary relating the bus name to the latitude, longitude, voltage and name
- `get_all_branches_dictionary(self)`
  Summary: Returns a dictionary with all the Branches by the name
- `get_branch_ratings(self, n)`
  Summary: Get DataFrame with the dynamic branch ratings

## Function: get_st_generation_sent_out(plexos_results_folder)

Get the generation auxiliary use from a PLEXOS results folder

## Function: get_st_node_load(plexos_results_folder, parse_dates)

Get the node load use from a PLEXOS results folder

## Function: plx_to_veragrid(mdl, plexos_results_folder, time_indices, text_func, prog_func)

Reads plexos model with results and creates a VeraGrid model
