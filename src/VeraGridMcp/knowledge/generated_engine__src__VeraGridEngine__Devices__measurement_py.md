# VeraGridEngine Module: src/VeraGridEngine/Devices/measurement.py

- Original source path: `src/VeraGridEngine/Devices/measurement.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 13
- Top-level function count: 1
- Representative imports: __future__, typing, numpy, VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.Devices.Parents.pointer_device_parent, VeraGridEngine.Devices.Substation.bus, VeraGridEngine.Devices.Branches.line, VeraGridEngine.Devices.Branches.dc_line, VeraGridEngine.Devices.Branches.transformer, VeraGridEngine.Devices.Branches.winding, VeraGridEngine.Devices.Branches.switch, VeraGridEngine.Devices.Branches.series_reactance, VeraGridEngine.Devices.Branches.upfc, VeraGridEngine.Devices.Injections.generator,  VeraGridEngine.enumerations

## Class: MeasurementTemplate

- Bases: PointerDeviceParent
- Summary: Measurement class

### Methods

- `value_prof(self)`
  Summary: Cost profile
- `value_prof(self, val)`
  Summary: No docstring provided.
- `get_value_at(self, t)`
  Summary: :param t:
- `sigma_prof(self)`
  Summary: Cost profile
- `sigma_prof(self, val)`
  Summary: No docstring provided.
- `get_sigma_at(self, t)`
  Summary: :param t:
- `get_value_pu_at(self, t, Sbase)`
  Summary: Get measurement per-unit value at a given point
- `get_standard_deviation_pu_at(self, t, Sbase)`
  Summary: Get measurement per-unit standard deviation at a given point
- `value(self)`
  Summary: Get ``value``.
- `value(self, val)`
  Summary: Set ``value``.
- `sigma(self)`
  Summary: Get ``sigma``.
- `sigma(self, val)`
  Summary: Set ``sigma``.

## Class: PiMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: QiMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: PgMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: QgMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: VmMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: VaMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: PfMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: QfMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: PtMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Class: QtMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- No methods detected.

## Function: get_i_base(Sbase, Vbase)

No docstring provided.

## Class: IfMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- `get_value_pu_at(self, t, Sbase)`
  Summary: No docstring provided.
- `get_standard_deviation_pu_at(self, t, Sbase)`
  Summary: No docstring provided.

## Class: ItMeasurement

- Bases: MeasurementTemplate
- Summary: Measurement class

### Methods

- `device(self)`
  Summary: device getter
- `get_value_pu_at(self, t, Sbase)`
  Summary: No docstring provided.
- `get_standard_deviation_pu_at(self, t, Sbase)`
  Summary: No docstring provided.
