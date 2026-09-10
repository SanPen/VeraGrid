# VeraGridEngine Module: src/VeraGridEngine/IO/cim/cgmes/cgmes_export.py

- Original source path: `src/VeraGridEngine/IO/cim/cgmes/cgmes_export.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: zipfile, io, rdflib, rdflib.graph, rdflib.namespace, typing, json, os, VeraGridEngine.IO.cim.cgmes.cgmes_circuit, VeraGridEngine.IO.cim.cgmes.rdfs_serializations, VeraGridEngine.IO.cim.cgmes.rdfs_infos, VeraGridEngine.IO.cim.cgmes.cgmes_enums, VeraGridEngine.enumerations, xml.etree.ElementTree, xml.dom.minidom

## Function: get_available_cgmes_profiles(cgmes_version)

No docstring provided.

## Class: CimExporter

- Bases: none
- Summary: No docstring provided.

### Methods

- `export(self, file_name)`
  Summary: No docstring provided.
- `serialize(self, stream, profile)`
  Summary: No docstring provided.
- `supports_profile(self, profile)`
  Summary: No docstring provided.
- `is_in_profile(self, instance_profiles, model_profile)`
  Summary: No docstring provided.
- `generate_full_model_elements(self, profile)`
  Summary: No docstring provided.
- `in_profile(filters, profile)`
  Summary: No docstring provided.
- `attr_in_profile(self, attr_filters, profile)`
  Summary: No docstring provided.
- `generate_other_elements(self, profile)`
  Summary: No docstring provided.
