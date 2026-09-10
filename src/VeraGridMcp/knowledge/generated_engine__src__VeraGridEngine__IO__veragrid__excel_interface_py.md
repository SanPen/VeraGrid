# VeraGridEngine Module: src/VeraGridEngine/IO/veragrid/excel_interface.py

- Original source path: `src/VeraGridEngine/IO/veragrid/excel_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: __future__, typing, warnings, numpy, pandas, VeraGridEngine.basic_structures, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.Devices, VeraGridEngine.Devices.types, VeraGridEngine.enumerations, VeraGridEngine.IO.veragrid.pack_unpack

## Function: check_names(names, logger)

Check that the names are allowed

## Function: get_allowed_sheets()

Get the allowed sheets in the excel file

## Function: shorten_dict_keys(d, max_size)

Change dict keys to match the Excel 30 char limit

## Function: load_from_xls(filename, logger)

Loads the excel file content to a dictionary for parsing the data

## Function: interprete_excel_v2(data, logger)

Interpret the file version 2

## Function: interpret_excel_v3(data, logger)

Interpret the file version 3

## Function: save_excel_v4(circuit, file_path)

Save the circuit information in excel format
