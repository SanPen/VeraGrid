# VeraGridEngine Module: src/VeraGridEngine/IO/file_open.py

- Original source path: `src/VeraGridEngine/IO/file_open.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 3
- Representative imports: __future__, os, json, collections.abc, typing, VeraGridEngine.Devices.multiverse, VeraGridEngine.IO.cim.cgmes.cgmes_data_parser, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.basic_structures, VeraGridEngine.data_logger, VeraGridEngine.IO.veragrid.excel_interface, VeraGridEngine.IO.veragrid.pack_unpack, VeraGridEngine.IO.matpower.legacy.matpower_parser, VeraGridEngine.IO.matpower.matpower_circuit, VeraGridEngine.IO.matpower.matpower_to_veragrid, VeraGridEngine.IO.dgs.dgs_to_veragrid

## Class: FileOpenOptions

- Bases: none
- Summary: This class is to store the extra stuff that needs to be passed to open more complex files

### Methods

- No methods detected.

## Function: open_cgmes(files, version, cgmes_map_areas_like_raw, try_to_map_dc_to_hvdc_line, cgmes_topology_mode, cgmes_create_busbar_section_for_every_connectivity_node, text_func, progress_func, cgmes_logger, cgmes_recovery_mode)

Load cgmes files

## Function: open_ucte(files, text_func, progress_func, logger)

:param files: files or list of files

## Function: determine_file_type(file_name)

Try to determine the type of file

## Class: FileOpen

- Bases: none
- Summary: File open interface

### Methods

- `open(self, text_func, progress_func)`
  Summary: Load VeraGrid compatible file
- `check_json_type(self, file_name)`
  Summary: Check the json file type from its internal data
