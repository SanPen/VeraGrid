# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/dynamic_parent.py

- Original source path: `src/VeraGridEngine/Devices/Parents/dynamic_parent.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, VeraGridEngine.Devices.Parents.physical_device, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Devices.Dynamic.rms_template, VeraGridEngine.Devices.Dynamic.emt_template, VeraGridEngine.enumerations, VeraGridEngine.Utils.Symbolic.symbolic_io

## Class: DynamicDevice

- Bases: PhysicalDevice
- Summary: Parent class for devices with dynamic models

### Methods

- `set_rms_var_factory(self, val)`
  Summary: Set the var factory pointer
- `set_emt_var_factory(self, val)`
  Summary: Set the var factory pointer
- `rms_model(self)`
  Summary: Get the RMS model
- `rms_model(self, val)`
  Summary: No docstring provided.
- `emt_model(self)`
  Summary: Get the EMT model
- `emt_model(self, val)`
  Summary: No docstring provided.
- `rms_template(self)`
  Summary: Get the RMS model
- `rms_template(self, val)`
  Summary: No docstring provided.
- `emt_template(self)`
  Summary: Get the EMT template
- `emt_template(self, val)`
  Summary: No docstring provided.
