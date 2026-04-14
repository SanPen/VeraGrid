# VeraGridEngine Module: src/VeraGridEngine/IO/others/rte_parser.py

- Original source path: `src/VeraGridEngine/IO/others/rte_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 7
- Representative imports: os, json, xml.etree.ElementTree, typing, VeraGridEngine.data_logger, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures, VeraGridEngine.IO.veragrid.zip_interface, VeraGridEngine.Devices, re, numpy

## Function: read_cgmes_files(cim_files, logger)

Reads a list of .zip or xml into a dictionary of file name -> list of text lines

## Function: parse_xml_text(text_lines)

Fill the XML into the objects

## Function: find_id(child)

Try to find the ID of an element

## Function: find_class_name(child)

Try to find the CIM class name

## Function: fix_child_result_datatype(child_result)

No docstring provided.

## Function: parse_xml_to_dict(xml_element)

Parse element into dictionary

## Function: rte2veragrid(file_name, logger)

Read the RTE internal grid format
