# VeraGridEngine Module: src/VeraGridEngine/IO/cim/db/psse_lookup_db.py

- Original source path: `src/VeraGridEngine/IO/cim/db/psse_lookup_db.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 1
- Representative imports: os, pandas, VeraGridEngine.IO.cim.db.base_db, VeraGridEngine.IO.cim.db.file_system, VeraGridEngine.IO.raw.devices.psse_circuit

## Class: PSSeLookUpDb

- Bases: BaseDb
- Summary: No docstring provided.

### Methods

- `read_db_file(self, file_name)`
  Summary: This function reads the DB from an excel file
- `write_db_file(self, file_name)`
  Summary: Write DB to excel
- `get_df(self, name)`
  Summary: No docstring provided.
- `get_available_table_names(self)`
  Summary: Get a list of the available tables
- `get_from_psse_lookup(df)`
  Summary: Get a dictionary with the PSSe id as key and the RDFID as value
- `get_structures_names(self)`
  Summary: No docstring provided.

## Function: create_PSSeLookUpDb(circuit)

No docstring provided.
