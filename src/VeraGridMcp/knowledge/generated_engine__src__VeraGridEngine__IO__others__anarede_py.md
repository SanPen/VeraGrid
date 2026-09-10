# VeraGridEngine Module: src/VeraGridEngine/IO/others/anarede.py

- Original source path: `src/VeraGridEngine/IO/others/anarede.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 19
- Top-level function count: 2
- Representative imports: __future__, chardet, typing, VeraGridEngine.Devices, VeraGridEngine.Devices.multi_circuit, VeraGridEngine.basic_structures

## Function: _parse_fixed(line, start, end, dtype, implicit_decimals)

Extract substring by fixed columns and convert to the desired dtype.

## Class: PwfVoltageGroup

- Bases: none
- Summary: PwfBus

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfBus

- Bases: none
- Summary: PwfBus

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, vg_dict)`
  Summary: :param vg_dict:

## Class: PwfLine

- Bases: none
- Summary: PwfLine

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfGenerator

- Bases: none
- Summary: PwfGenerator

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfLoad

- Bases: none
- Summary: PwfLoad

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfTransformer

- Bases: none
- Summary: PwfTransformer

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfShunt

- Bases: none
- Summary: PwfShunt

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfStaticCompensator

- Bases: none
- Summary: StaticCompensator

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfDCLine

- Bases: none
- Summary: PwfDCLine

### Methods

- `parse(self, line)`
  Summary: :param line:
- `to_veragrid(self, bus_dict)`
  Summary: :param bus_dict:

## Class: PwfGeneratorReactance

- Bases: none
- Summary: PwfGeneratorReactance

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfVoltageLimitGroup

- Bases: none
- Summary: PwfVoltageLimitGroup

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfEquipmentConnection

- Bases: none
- Summary: PwfEquipmentConnection

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfTransformerSettings

- Bases: none
- Summary: PwfTransformerSettings

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfGeneratorIdentification

- Bases: none
- Summary: PwfGeneratorIdentification

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfMotorConfiguration

- Bases: none
- Summary: PwfMotorConfiguration

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfComment

- Bases: none
- Summary: PwfComment

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfInjection

- Bases: none
- Summary: PwfInjection

### Methods

- `parse(self, line)`
  Summary: :param line:

## Class: PwfNetwork

- Bases: none
- Summary: PwfNetwork

### Methods

- `add_device(self, device)`
  Summary: Add a device to the appropriate list based on its class type.
- `to_veragrid(self)`
  Summary: :return:

## Function: _split_sections(file_name)

Splits a PWF file into sections based on the delimiter "99999".

## Class: PWFParser

- Bases: none
- Summary: PWFParser

### Methods

- `to_veragrid(self)`
  Summary: Convert Anarede grid to VeraGrid
