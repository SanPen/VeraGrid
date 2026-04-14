# VeraGridEngine Module: src/VeraGridEngine/IO/file_save.py

- Original source path: `src/VeraGridEngine/IO/file_save.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 14
- Representative imports: __future__, os, datetime, typing, VeraGridEngine.IO.file_open, VeraGridEngine.IO.cim.cgmes.cgmes_create_instances, VeraGridEngine.IO.cim.cgmes.veragrid_to_cgmes, VeraGridEngine.IO.cim.cgmes.cgmes_export, VeraGridEngine.IO.cim.cgmes.cgmes_data_parser, VeraGridEngine.basic_structures, VeraGridEngine.data_logger, VeraGridEngine.IO.veragrid.json_parser, VeraGridEngine.IO.veragrid.excel_interface, VeraGridEngine.IO.veragrid.pack_unpack, VeraGridEngine.IO.dgs.veragrid_to_dgs, VeraGridEngine.IO.raw.raw_parser_writer

## Class: FileSavingOptions

- Bases: none
- Summary: This class is to store the extra stuff that needs to be passed to save more complex files

### Methods

- `get_power_flow_results(self)`
  Summary: Try to extract the power flow results

## Function: save_veragrid_excel(circuit, file_name)

Save the circuit information in excel format

## Function: save_veragrid_multiverse(file_name, multiverse, options, text_func, progress_func)

Save the circuit information in zip format

## Function: save_veragrid_circuit(circuit, file_name, options, text_func, progress_func)

Save the circuit information in zip format

## Function: save_veragrid_delta(circuit, file_name, options, text_func, progress_func)

Save the circuit information in zip format

## Function: save_veragrid_sqlite(circuit, file_name, text_func, progress_func)

Save the circuit information in sqlite

## Function: save_electrical_json_v3(circuit, file_name, options)

Save the circuit information in json format

## Function: save_cim(circuit, file_name)

Save the circuit information in CIM format

## Function: save_cgmes(circuit, file_name, options, text_func, progress_func)

Save the circuit information in CGMES format

## Function: save_veragrid_h5(circuit, file_name, text_func, progress_func)

Save the circuit information in CIM format

## Function: save_psse_raw(circuit, file_name, options)

Save the circuit information in json format

## Function: save_psse_rawx(circuit, file_name)

Save the circuit information in json format

## Function: save_newton(circuit, file_name)

Save the circuit information in sqlite

## Function: save_pgm(circuit, file_name)

Save to Power Grid Model format

## Function: save_dgs(circuit, file_name)

:return:

## Class: FileSave

- Bases: none
- Summary: FileSave

### Methods

- `save(self)`
  Summary: Save the file in the corresponding format
