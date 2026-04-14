# VeraGridEngine Module: src/VeraGridEngine/IO/raw/raw_parser_writer.py

- Original source path: `src/VeraGridEngine/IO/raw/raw_parser_writer.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 10
- Representative imports: __future__, chardet, re, datetime, typing, VeraGridEngine.IO.raw.raw_writer_comment_map, VeraGridEngine.basic_structures, VeraGridEngine.IO.raw.devices.area, VeraGridEngine.IO.raw.devices.branch, VeraGridEngine.IO.raw.devices.bus, VeraGridEngine.IO.raw.devices.facts, VeraGridEngine.IO.raw.devices.generator, VeraGridEngine.IO.raw.devices.induction_machine, VeraGridEngine.IO.raw.devices.inter_area, VeraGridEngine.IO.raw.devices.load, VeraGridEngine.IO.raw.devices.fixed_shunt

## Function: delete_comment(raw_line)

:param raw_line:

## Function: interpret_line(raw_line, splitter)

Split text into arguments and parse each of them to an appropriate format (int, float or string)

## Function: read_and_split(file_name, text_func, progress_func)

Read the text file and split it into sections

## Function: is_3w(row, bus_set)

If this a 3W transformer?

## Function: is_one_line_for_induction_machine(row)

Is this a one line induction machine?

## Function: check_end_of_impedance_table(row)

Check the insane impedance line termination criteria

## Function: is_valid(value)

No docstring provided.

## Function: format_lines(data1, logger)

Format PSSe lines

## Function: read_raw(filename, text_func, progress_func, logger)

:param filename:

## Function: write_raw(file_name, psse_model, version)

Write PsseCircuit as .raw version 33
