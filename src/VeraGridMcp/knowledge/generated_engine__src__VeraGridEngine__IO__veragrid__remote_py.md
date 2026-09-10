# VeraGridEngine Module: src/VeraGridEngine/IO/veragrid/remote.py

- Original source path: `src/VeraGridEngine/IO/veragrid/remote.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 5
- Representative imports: __future__, os, typing, uuid, numpy, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.enumerations, VeraGridEngine.basic_structures, VeraGridEngine.IO.veragrid.pack_unpack, VeraGridEngine.IO.file_system, VeraGridEngine.Simulations.driver_handler, VeraGridEngine.Simulations.types

## Class: RemoteInstruction

- Bases: none
- Summary: Remote instruction class

### Methods

- `get_data(self)`
  Summary: :return:
- `parse_data(self, data)`
  Summary: :param data:

## Class: RemoteJob

- Bases: none
- Summary: Remote job class

### Methods

- `cancel(self)`
  Summary: :return:
- `get_data(self)`
  Summary: :return:
- `parse_data(self, data)`
  Summary: :param data:

## Function: get_certificate_path()

Get a path to the certificates

## Function: get_certificate(base_url, certificate_path, pwd, logger)

Try connecting to the server

## Function: gather_model_as_jsons_for_communication(circuit, instruction)

Create a Json with the same information expected for loading with `parse_veragrid_data`

## Function: send_json_data(json_data, endpoint_url, certificate)

Send a file along with instructions about the file

## Function: run_job(grid, job)

Function to run a job, this is a simple function
