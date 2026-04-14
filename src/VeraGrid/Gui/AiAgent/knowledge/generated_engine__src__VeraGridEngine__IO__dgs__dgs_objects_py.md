# VeraGridEngine Module: src/VeraGridEngine/IO/dgs/dgs_objects.py

- Original source path: `src/VeraGridEngine/IO/dgs/dgs_objects.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 63
- Top-level function count: 3
- Representative imports: __future__, csv, typing

## Function: _split_dgs_line(line)

Split a DGS record honoring quoted semicolons.

## Function: _parse_elm_dsl_param_value(raw)

Parse one ElmDsl parameter value from the DGS row.

## Class: DgsProperty

- Bases: none
- Summary: Dgs Property

### Methods

- `parse(self, raw)`
  Summary: :param raw: incoming value
- `format(self, value)`
  Summary: :param value:

## Class: DGSElement

- Bases: none
- Summary: Base class

### Methods

- `parse_line(cls, line, header_map)`
  Summary: Parse a DGS data line using a header-derived column map.
- `to_dgs_line(self)`
  Summary: Create DGS line

## Class: ChaRef

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ChaVec

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmComp

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: ElmDsl

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `get_parameter_map(self)`
  Summary: Return the instance parameter mapping using the DGS order.
- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: BlkFrom

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: BlkGoto

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: BlkRef

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: BlkSig

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: BlkSlot

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: BlkSum

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmAsm

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmCoup

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmBranch

- Bases: DGSElement
- Summary: Branch element container (PowerFactory/DGS).

### Methods

- No methods detected.

## Class: ElmFeeder

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmGenstat

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmLne

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmSind

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypSind

- Bases: DGSElement
- Summary: PowerFactory Series Reactor type (TypSind).

### Methods

- No methods detected.

## Class: ElmLnesec

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmLod

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmLodlv

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmLodlvp

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmNet

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmShnt

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmSvs

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmSite

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmSubstat

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmSym

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmTerm

- Bases: DGSElement
- Summary: *  FID: Unique identifier for DGS file

### Methods

- No methods detected.

## Class: ElmTr2

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmTr3

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmXnet

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: ElmZone

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: General

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: BlkDef

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `_split_symbol_field(raw)`
  Summary: No docstring provided.
- `_append_unique_symbols(cls, target, raw)`
  Summary: Append parsed symbols to a target list preserving order and uniqueness.
- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: IntFolder

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: IntRef

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: IntTemplate

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: Matrix

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: IntGrf

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: IntGrfcon

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: IntGrfnet

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: RelFuse

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: StaCubic

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: StaSwitch

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: StaCt

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: StaVt

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypSwitch

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: Parse TypSwitch and tolerate several header aliases used by DGS variants.

## Class: TypAsmo

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypFuse

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypLne

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypLod

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypSym

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypTr2

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Class: TypTr3

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- No methods detected.

## Function: _dgs_get(parts, header_map, key)

Get the raw column value for a given DGS key.

## Class: TypCon

- Bases: DGSElement
- Summary: PowerFactory conductor type (TypCon) mapped to VeraGrid Wire.

### Methods

- No methods detected.

## Class: TypCt

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: TypGeo

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.

## Class: TypVt

- Bases: DGSElement
- Summary: No docstring provided.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: No docstring provided.
- `to_dgs_line(self)`
  Summary: No docstring provided.

## Class: TypTow

- Bases: DGSElement
- Summary: PowerFactory tower type (TypTow) mapped to VeraGrid OverheadLineType.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: Parse TypTow data line including variable-sized arrays/matrices.

## Class: ElmTow

- Bases: DGSElement
- Summary: PowerFactory line coupling (ElmTow) that binds ElmLne circuits to a tower geometry.

### Methods

- `parse_line(cls, line, header_map)`
  Summary: Parse ElmTow data line including variable-sized vectors.
