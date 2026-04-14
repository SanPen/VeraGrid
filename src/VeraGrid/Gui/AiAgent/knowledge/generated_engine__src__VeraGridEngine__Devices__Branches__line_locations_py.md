# VeraGridEngine Module: src/VeraGridEngine/Devices/Branches/line_locations.py

- Original source path: `src/VeraGridEngine/Devices/Branches/line_locations.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 2
- Top-level function count: 0
- Representative imports: typing, numpy, pandas, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.enumerations

## Class: LineLocation

- Bases: EditableDevice
- Summary: Line location object

### Methods

- No methods detected.

## Class: LineLocations

- Bases: EditableDevice
- Summary: LineLocations

### Methods

- `get_locations(self)`
  Summary: Get list of LineLocation
- `add(self, sequence, latitude, longitude, altitude, idtag)`
  Summary: Append row to this object (very slow)
- `add_location(self, lat, long, alt)`
  Summary: Add a location to the line
- `remove(self, loc)`
  Summary: No docstring provided.
- `parse(self, data)`
  Summary: Parse Json data
- `copy(self)`
  Summary: No docstring provided.
- `set(self, data)`
  Summary: Parse Json data
- `to_list(self)`
  Summary: Convert data to list of lists for Json usage
- `to_df(self)`
  Summary: Convert data to DataFrame
