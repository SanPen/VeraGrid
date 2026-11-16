# Sienna round-trip implementation plan

## Objective

Make the Sienna v0.4 adapter bidirectional for every device that
`sienna_to_veragrid.py` currently converts. Every writer output must validate
against the pinned SiennaSchemas checkout, parse through the fixed-slot
models, and reconstruct the corresponding VeraGrid electrical state without
new dependencies.

Extend that objective to **all 193 non-dynamic registered Sienna v0.4 schema
types**. The 87 dynamic types are deferred by the current scope. The source
tree has 288 `Sienna*` Python
classes because eight are adapter support classes (for example,
`SiennaSystemDocument` and version helpers), not independently registered
Sienna schema types. Each of the 280 registered types must receive a written
mapping decision, implementation where VeraGrid has an equivalent, and an
appropriate round-trip test.

## Current mapping gap

The only Sienna-to-VeraGrid conversion implementation is
`sienna_to_veragrid.py`. It currently converts 24 component kinds. The
remaining registered schema types are schema-typed and JSON-readable/writable,
but they have no VeraGrid mapping yet. This plan exists to map the full 280;
parser/writer registration is not a conversion.

## Full-catalog mapping policy

| Sienna family | Current class count | Required mapping outcome |
| --- | ---: | --- |
| Core topology and common data | 78 | Map topology/device fields to VeraGrid or attach through an explicit existing VeraGrid concept. |
| Operations | 80 | Map all electrical devices and operating constraints to their VeraGrid device/profile counterparts. |
| Dynamics | 87 | Excluded from static VeraGrid conversion parity. They retain mandatory typed schema/model round trips and belong to a separate dynamics-adapter project. |
| Investments | 21 | Map to VeraGrid investment/planning objects where represented; otherwise document the absent domain equivalent. |
| Time series | 14 | Map to VeraGrid profiles/time-series structures with resolution, ownership, and scenario semantics preserved. |

An explicit unsupported-equivalence result is acceptable only after inspecting
VeraGrid's concrete model catalog and recording why no semantic target exists.
It is not acceptable to silently keep a Sienna object in an untyped bag.

## Mandatory non-dynamic round-trip matrix

Every non-dynamic registered `SiennaObjectKind` value must appear in a
machine-readable test matrix with these gates:

1. A minimal valid JSON fixture for its pinned v0.4 schema.
2. JSON schema validation using the pinned SiennaSchemas checkout.
3. Typed parse followed by typed writer output and a second schema validation.
4. A semantic field-equivalence assertion over every declared field the model
   owns, including nested model discriminators.
5. When the non-dynamic type has a static VeraGrid equivalent, Sienna-to-VeraGrid conversion,
   canonical VeraGrid-to-Sienna output, second typed parse, and electrical or
   control-state equivalence assertions.
6. When a non-dynamic type has no static VeraGrid equivalent, an explicit typed diagnostic and an
   evidence-backed catalog decision; its schema-model round trip remains
   mandatory and must still pass.

Dynamic types are intentionally not sent through `sienna_to_veragrid.py` or
`veragrid_to_sienna.py` and are deferred for this delivery. The suite reports
the full 280-kind registry and fails unless it has a decision for each of the
193 non-dynamic kinds.

## Rules

- Use only explicit fixed-slot Sienna models and declared JSON fields.
- Do not add dependencies or modify non-Sienna VeraGrid device code.
- When multiple Sienna classes collapse into one VeraGrid class, write one
  documented canonical Sienna class; exact source-class identity cannot be
  restored without forbidden origin metadata.
- Add the exported device to the broad round-trip fixture before considering
  its writer mapping complete.
- Stage each verified change.

## Canonical mapping inventory

| VeraGrid device | Reader-supported Sienna kinds | Canonical writer kind | Status |
| --- | --- | --- | --- |
| Bus / area / zone | ACBus, DCBus, Area, LoadZone | Same | verified |
| Line | Line, GenericArcImpedance, DiscreteControlledACBranch | Line | verified |
| Load | PowerLoad, StandardLoad, ExponentialLoad, MotorLoad, flexible loads | PowerLoad | verified |
| Shunt | FixedAdmittance | FixedAdmittance | verified |
| ControllableShunt | SwitchedAdmittance, FACTSControlDevice | SwitchedAdmittance | verified |
| StaticGenerator | RenewableNonDispatch | RenewableNonDispatch | verified |
| ExternalGrid | Source | Source | verified |
| Generator | ThermalStandard, hydro, renewable dispatch, condenser, hybrid | ThermalStandard | verified |
| Battery | EnergyReservoirStorage | EnergyReservoirStorage | verified |
| Transformer2W | TwoWindingTransformer + TransformerCircuit | Same pair | verified |
| Transformer3W | ThreeWindingTransformer + TransformerCircuit | Same pair | verified |
| SeriesReactance | SeriesCompensator | SeriesCompensator | verified |

## Remaining execution sequence

1. Produce a machine-readable 193-row mapping matrix: Sienna kind, source
   module, VeraGrid target, direction status, round-trip fixture, and precise
   unsupported-equivalence reason where necessary.
2. Complete electrical-network round-trip parity for the remaining branch/HVDC
   devices. Transformer3W is complete.
3. Map injection, operation, and service models to VeraGrid controls,
   profiles, and device associations.
4. Defer typed parse/write coverage for dynamic models to the dynamics-adapter
   project.
5. Map investment and time-series models to their VeraGrid planning/profile
   equivalents.
6. Retain the Transformer3W broad round-trip fixture and hidden-star-bus
   reconstruction assertions when changing either representation.
7. Exercise ControllableShunt and Battery in the broad round-trip fixture;
   verify the parser-compatible cost records and effective admittance.
8. Audit and export supported branch/HVDC devices only when a VeraGrid device
   has a direct electrical equivalent. Reject unsupported device groups with a
   precise error instead of emitting fabricated data.
9. Add regression cases for every canonical mapping: unknown bus references,
   mismatched base powers, and malformed writer-required cost payloads.
10. Run the Sienna adapter tests, compile the Sienna package, validate staged
   diffs, and inspect the supported-kind inventory against the reader.
11. Implement and run the mandatory 193-type static round-trip matrix; do not claim
    completion while any registered kind lacks a fixture, model round trip, or
    mapping decision.

## Acceptance criteria

- Every generated Sienna class has a recorded, evidence-backed VeraGrid
  mapping decision.
- The static mapping inventory reports 193 reviewed non-dynamic kinds.
- Every mapped non-dynamic class has parser, converter, writer, and round-trip coverage.
- Every unavailable target has a typed, explicit diagnostic and a documented
  inspected VeraGrid catalog reference.
- Every reader-supported electrical VeraGrid target has a canonical writer.
- The broad fixture exports, validates, reloads, and retains counts plus key
  electrical fields for all canonical target device types.
- Schema validation and typed parsing both succeed; JSON-schema acceptance
  alone is not enough.
- No non-Sienna VeraGrid source file changes and no new dependency.

## Handoff dossier: authoritative sources and model locations

This is the operational handoff. A later maintainer should verify these paths
and counts before changing the adapter.

| Purpose | Absolute location | Authority |
| --- | --- | --- |
| VeraGrid source root | `/home/santi/Git/eRoots/VeraGrid/src` | Adapter implementation and concrete VeraGrid targets. |
| Pinned SiennaSchemas checkout | `/home/santi/Git/GitHub/SiennaSchemas` | Sienna JSON-schema definitions, required fields, and enum spelling. |
| Sienna adapter | `VeraGridEngine/IO/sienna` | All adapter changes belong here. |
| Adapter tests | `tests/FileFormats/Sienna/test_sienna_adapter.py` | Broad electrical and typed-model round-trip checks. |

No code outside the Sienna adapter/test locations is authorized by this work.
There are no added dependencies: parsing, writing, and validation use the
standard library plus existing VeraGrid dependencies.

At the time of this handoff the pinned SiennaSchemas checkout is commit
`59f9a751603f02b63e886976c4595875265c0a88`; the VeraGrid checkout is commit
`c76f241d2945d1327c1db3d6b32832a8ae554d37`. Record a new schema commit before
accepting schema changes, because the adapter currently targets v0.4.0.

### Fixed-slot model implementation

| Concern | VeraGrid source | Function |
| --- | --- | --- |
| Registered types and base model | `VeraGridEngine/IO/sienna/devices/schema_object.py` | `SiennaObjectKind` is the authoritative 280-kind registry. `SiennaSchemaModel` is the fixed-slot typed base. |
| Parse registry | `VeraGridEngine/IO/sienna/devices/schema_registry.py` | Explicit parser per registered kind. |
| Writer registry | `VeraGridEngine/IO/sienna/devices/writer_registry.py` | Explicit JSON writer per registered kind. |
| System document | `VeraGridEngine/IO/sienna/devices/system_document.py` | Typed ownership for topology, buckets, associations, metadata. |
| Version gate | `VeraGridEngine/IO/sienna/devices/format_version.py` | Pins the adapter to Sienna v0.4.0. |
| Concrete models | `VeraGridEngine/IO/sienna/devices/core`, `operations`, `dynamics`, `investments`, `time_series` | One static module per schema object. |
| Validator | `VeraGridEngine/IO/sienna/sienna_json_validator.py` | Local dependency-free structural validation. |

The external schema repository follows the same domain grouping: `Core`,
`Operations`, `Dynamics`, `Investments`, and `TimeSeries`. Its root
`openapi-operations.json` is the operation-type index, and
`Core/SystemDocument.json` is the document root. For the completed three-
winding path, the field authority is
`Operations/Branch/ThreeWindingTransformer.json` together with
`Operations/Branch/TransformerCircuit.json` and `Operations/common.json`.

`rg -n 'class Sienna' VeraGridEngine/IO/sienna/devices` finds 288 classes,
but `len(SiennaObjectKind)` must be 280. The eight-class difference is support
machinery such as `SiennaSystemDocument`, not missing schema types. Do not add
dynamic models, untyped bags, or monkey-patched fields.

To locate the exact implementation module for any registered kind, use the
registry imports rather than guessing from a class name:

```bash
rg -n "SiennaObjectKind\.<kind>" VeraGridEngine/IO/sienna/devices/schema_registry.py \
    VeraGridEngine/IO/sienna/devices/writer_registry.py
```

The matching import line provides the one parser and one writer module. The
same basename under `/home/santi/Git/GitHub/SiennaSchemas` is the field schema;
the domain directories have the capitalization shown in the repository tree.

### Versioning and compatibility contract

The supported wire version is declared by
`VeraGridEngine/IO/sienna/devices/format_version.py` and serialized through
`SiennaSchemaVersion.V0_4_0`. `resolve_sienna_format_version()` is the only
accepted entry point for version selection; do not add scattered string
comparisons. Schema-version upgrades must follow this order:

1. Pin and record the new SiennaSchemas commit in this file.
2. Add a new explicit `SiennaSchemaVersion` enum value and resolution branch.
3. Regenerate or update fixed-slot model fields, parsers, and writers from the
   new schema source; preserve the old v0.4 models while files of that version
   remain supported.
4. Add one fixture per changed/new registered kind and run the full 280-row
   matrix for every supported version.
5. Add conversion compatibility rules only where the VeraGrid electrical
   meaning is unchanged; otherwise reject with a version-specific diagnostic.

The adapter must never infer a schema version from field presence. A file is
accepted only when its declared `schema_version` resolves to a supported enum.

### Conversion entry points

| Direction | Source | Entry point | Responsibility |
| --- | --- | --- | --- |
| JSON to document | `sienna_to_veragrid.py` | `load_sienna_document`, `parse_sienna_document` | Validate JSON, construct fixed-slot models, retain unconverted kinds as typed buckets. |
| Document to VeraGrid | `sienna_to_veragrid.py` | `sienna_to_veragrid` | Convert canonical static kinds; reject other kinds rather than silently discard them. |
| VeraGrid to document | `veragrid_to_sienna.py` | `veragrid_to_sienna_document` | Emit canonical v0.4 records for representable static devices. |
| File output | `veragrid_to_sienna.py` | `save_veragrid_to_sienna` | Validate then write JSON. |

Reader helpers in `sienna_to_veragrid.py` are named `_convert_<kind>`. The
implemented static reader covers topology plus `PowerLoad`, `FixedAdmittance`,
`StandardLoad`, `ExponentialLoad`, `RenewableNonDispatch`,
`SynchronousCondenser`, `MotorLoad`, `RenewableDispatch`, `Source`,
`SwitchedAdmittance`, `EnergyReservoirStorage`, `GenericArcImpedance`,
`TransformerCircuit` + `TwoWindingTransformer`, `SeriesCompensator`,
`ThermalStandard`, hydro variants, flexible-load variants,
`FACTSControlDevice`, `DiscreteControlledACBranch`,
`ThreeWindingTransformer`, and `HybridSystem`.

The writer emits one canonical kind per VeraGrid device: e.g. generator to
`ThermalStandard` and static generator to `RenewableNonDispatch`. This retains
electrical state but cannot recreate an original noncanonical Sienna class
without prohibited origin metadata.

### Implementation journal: completed work

This section records actual implementation, not planned work.

1. The Sienna model catalogue was made static. Every registered schema model
   now derives from the fixed-slot `SiennaSchemaModel` base in
   `devices/schema_object.py`; `SiennaSystemDocument` component buckets use
   `list[SiennaSchemaModel]`, not `list[object]`.
2. Parsers and writers are registered for all 280 `SiennaObjectKind` values.
   This guarantees a known concrete parser/writer path, but does **not** mean
   that all 280 types are convertible to VeraGrid yet.
3. The JSON boundary is dependency-free: `sienna_json_validator.py` validates
   the Sienna document without Pydantic or `jsonschema`; then the fixed-slot
   parser performs typed construction.
4. `sienna_to_veragrid.py` parses the document root, areas, zones, AC/DC buses,
   arcs, lines, loads, fixed shunts and all remaining known component buckets.
   Unknown-to-VeraGrid buckets stay typed until conversion decides whether to
   consume or reject them.
5. The reader has explicit helpers for `StandardLoad`, `ExponentialLoad`,
   `RenewableNonDispatch`, `SynchronousCondenser`, `MotorLoad`,
   `RenewableDispatch`, `Source`, `SwitchedAdmittance`,
   `EnergyReservoirStorage`, `GenericArcImpedance`,
   `TwoWindingTransformer`, `SeriesCompensator`, `ThermalStandard`,
   `HydroTurbine`, `HydroDispatch`, `HydroPumpTurbine`,
   `FACTSControlDevice`, `DiscreteControlledACBranch`,
   `ThreeWindingTransformer`, `HybridSystem`,
   `InterruptiblePowerLoad`, `InterruptibleStandardLoad`, and
   `ShiftablePowerLoad`.
6. `veragrid_to_sienna.py` now writes canonical records for areas, zones,
   AC/DC buses, arcs, lines, `PowerLoad`, `FixedAdmittance`,
   `RenewableNonDispatch`, `Source`, `ThermalStandard`,
   `EnergyReservoirStorage`, `SwitchedAdmittance`,
   `TransformerCircuit` + `TwoWindingTransformer`, `SeriesCompensator`, and
   `ThreeWindingTransformer`.
7. Source and thermal records receive explicit, parser-compatible neutral
   cost records. This is required because Sienna declares cost structures even
   when VeraGrid has no equivalent cost state to export.
8. The writer validates integer, positive device codes before using them as
   Sienna identifiers. It rejects unsupported electrical groups—DC lines,
   HVDC lines, VSC converters, UPFC devices, switches, multi-winding
   transformers, and current injections—instead of silently deleting them.
9. `SwitchedAdmittance` control mode is explicitly typed as
   `SiennaSwitchedAdmittanceControlMode | None` and maps using enum identity,
   rather than a string or an untyped value.
10. Transformer3W is represented as Sienna's required three terminal-to-star
    `TransformerCircuit` records plus `ThreeWindingTransformer` and an ACBus
    star node. Export omits VeraGrid's generated internal star bus; import
    recognizes the Sienna star id, permits only that hidden endpoint in arc
    validation, and lets `add_transformer3w()` recreate VeraGrid's internal
    bus. This prevents a duplicate visible star bus.

### Test implementation and present coverage

The sole adapter test module is
`tests/FileFormats/Sienna/test_sienna_adapter.py`. It currently contains:

| Test responsibility | Devices / behavior checked |
| --- | --- |
| Broad file round trip | Area, zone, AC/DC bus, line, load, fixed shunt, static generator, external grid, generator, transformer2W, series reactance, battery, controllable shunt, transformer3W. |
| Broad field checks | Circuit name/base/frequency, device counts, line R, load P, shunt B, generator limits, transformer X, battery energy, controllable-shunt B, Transformer3W x31. |
| Hidden-star regression | Sienna output contains `T3_star`; restored VeraGrid visible buses do not; one internal Transformer3W bus is recreated. |
| Additional reader kinds | Typed injection of every reader-only static load, generator, branch, storage, FACTS, and hybrid record, then VeraGrid conversion assertions. |
| Loss prevention | An unsupported Sienna `AGC` record remains visible to the parser and produces an explicit conversion failure. |
| Registry integrity | Parser and writer registry counts are asserted to equal `len(SiennaObjectKind) == 280`. |

The latest completed verification run was:

```text
tests/FileFormats/Sienna/test_sienna_adapter.py: 9 passed
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m compileall -q VeraGridEngine/IO/sienna: passed
git diff --cached --check: passed
```

### Known limitations, deliberately preserved

| Limitation | Current behavior | Reason / next action |
| --- | --- | --- |
| 193 explicit static fixtures | Not yet present | Build the required matrix; registry counts alone are insufficient. |
| Dynamic schema objects | Deferred | Excluded from this delivery by the current scope. |
| Investment / time series mapping | Typed parse/write only | Needs verified planning/profile target mapping in VeraGrid. |
| Associations and sidecars | Reader rejects non-empty association tables / time-series storage sidecar | Avoids silently dropping ownership or profile semantics. |
| HVDC and unimplemented electrical devices | Writer rejects them | No fabricated Sienna representation; implement only after matching direct VeraGrid and Sienna semantics. |
| Canonical identity | Multiple Sienna reader kinds collapse to one VeraGrid target | Re-export uses the documented canonical class; preserving original source kind needs metadata not accepted by this adapter. |

### VeraGrid model sources already inspected

| Target | Source location |
| --- | --- |
| Circuit add/ownership APIs | `VeraGridEngine/Devices/multi_circuit.py`, `VeraGridEngine/Devices/assets.py` |
| Buses, areas, zones | `VeraGridEngine/Devices/Substation` |
| Lines and branches | `VeraGridEngine/Devices/Branches` |
| Transformer3W and windings | `VeraGridEngine/Devices/Branches/transformer3w.py`, `VeraGridEngine/Devices/Branches/winding.py` |
| Loads, generators, storage, shunts | `VeraGridEngine/Devices/Injections` |
| Public device imports | `VeraGridEngine/Devices/__init__.py` |

Before a non-dynamic kind is called unsupported, inspect this catalog and put
the missing concrete target and reason into the 280-row matrix. Never use a
dictionary, `list[object]`, or `ext` field as a conversion target.

### Verification and staging

Run from `/home/santi/Git/eRoots/VeraGrid/src`:

```bash
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m pytest -q tests/FileFormats/Sienna/test_sienna_adapter.py
/home/santi/Git/eRoots/VeraGrid/.venv/bin/python -m compileall -q VeraGridEngine/IO/sienna
git diff --cached --check
git status --short -- VeraGridEngine/IO/sienna tests/FileFormats/Sienna
```

Stage only these paths:

```bash
git add VeraGridEngine/IO/sienna tests/FileFormats/Sienna
```

### In-progress state

`Transformer3W` writer output is complete and covered by the broad round trip.
Sienna stores it as three
`TransformerCircuit` records, one `ThreeWindingTransformer`, and a hidden star
bus. VeraGrid creates its own internal star bus in
`MultiCircuit.add_transformer3w()`. Export must omit VeraGrid internal buses;
import must avoid turning Sienna's hidden star bus into a visible user bus,
while still validating and resolving its arcs. The broad fixture must cover
this before the mapping status becomes verified. The current test does this
and asserts the restored `x31` and transformer count.

The mandatory 193-kind static fixture matrix is not implemented yet. A
registry-count assertion is not enough: each explicit typed fixture needs
parse/write/schema round-trip coverage. `mapping_inventory.py` now records a
conversion, nested-value, or no-static-equivalent decision for every
non-dynamic kind.
