# VeraGridEngine Module: src/VeraGridEngine/IO/veragrid/zip_interface.py

- Original source path: `src/VeraGridEngine/IO/veragrid/zip_interface.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 13
- Representative imports: json, io, os, numpy, chardet, pandas, zipfile, warnings, typing, VeraGridEngine.Devices.types, VeraGridEngine.basic_structures, VeraGridEngine.IO.veragrid.generic_io_functions, VeraGridEngine.Simulations.driver_template, VeraGridEngine.IO.veragrid.pack_unpack, VeraGridEngine.Devices

## Function: load_json_from_file_pointer(file_pointer)

Load JSON from a file pointer using orjson if available, falling back to json.

## Function: save_results_in_zip(f_zip_ptr, filename_zip, sessions_data, folder, text_func, progress_func)

:param f_zip_ptr:

## Function: save_multiverse_data_to_zip(f_zip_ptr, multiverse, filename_zip, text_func, progress_func, logger)

Save only the multiverse-specific payload into an already opened VeraGrid archive.

## Function: save_single_circuit_data_to_zip(f_zip_ptr, circuit, sessions_data, filename_zip, text_func, progress_func, logger)

Save the non-multiverse circuit payload into an already opened VeraGrid archive.

## Function: save_veragrid_data_to_zip(filename_zip, circuit, sessions_data, json_files, text_func, progress_func, logger)

Save a list of DataFrames to a zip file without saving to disk the csv files

## Function: save_veragrid_multiverse_data_to_zip(filename_zip, json_files, multiverse, text_func, progress_func, logger)

Save a list of DataFrames to a zip file without saving to disk the csv files

## Function: save_results_only(filename_zip, sessions_data, text_func, progress_func)

Save the results into a new file

## Function: read_data_frame_from_zip(file_pointer, extension, index_col, logger)

read DataFrame

## Function: get_frames_from_zip(file_name_zip, text_func, progress_func, logger)

Open the csv files from a zip file

## Function: get_session_tree(file_name_zip)

Get the sessions structure

## Function: load_session_driver_objects(file_name_zip, session_name, study_name)

Get the sessions structure

## Function: get_xml_content(file_ptr)

Reads the content of a file

## Function: get_xml_from_zip(file_name_zip, text_func, progress_func)

Get the .xml files from a zip file
