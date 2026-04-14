# VeraGridEngine Module: src/VeraGridEngine/Devices/Parents/physical_device.py

- Original source path: `src/VeraGridEngine/Devices/Parents/physical_device.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, datetime, typing, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Aggregation.modelling_authority, VeraGridEngine.Devices.Associations.association, VeraGridEngine.enumerations

## Class: PhysicalDevice

- Bases: EditableDevice
- Summary: Parent class for Injections, Branches, Buses and other physical devices

### Methods

- `commissioned_date(self)`
  Summary: :return:
- `commissioned_date(self, val)`
  Summary: No docstring provided.
- `set_commissioned_year(self, year, month, day)`
  Summary: Helper function to set the commissioning date of the asset
- `get_commissioned_date_as_date(self)`
  Summary: Get the commissioned date as datetime
- `decommissioned_date(self)`
  Summary: :return:
- `decommissioned_date(self, val)`
  Summary: No docstring provided.
- `set_decommissioned_year(self, year, month, day)`
  Summary: Helper function to set the decommissioning date of the asset
- `get_decommissioned_date_as_date(self)`
  Summary: Get the commissioned date as datetime
- `associate_owner(self, owner, val)`
  Summary: Associate a technology with this injection device
- `owners_list(self)`
  Summary: Bus
