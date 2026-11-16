# Native PowerFactory model-option fixtures

Captured on 9 November 2026 from PowerFactory **24.0.2.0**, using native DGS
**7.0 ASCII** export. These files are downloaded, untouched ComExport outputs.
The original source projects were copied into dedicated VeraGrid fixture
projects. Each changed option was restored after export.

`manifest.json` records SHA-256 hashes, sizes, source projects, active study
cases, option values, export results, table counts, and compute job ID.
All ten exports returned code zero, without export missing-reference warnings.
Every nonempty pointer resolves within its file. No duplicate columns remain.

## Coverage

| Files | What they exercise |
| --- | --- |
| `nine_bus_classical.dgs`, `nine_bus_standard.dgs` | Three synchronous machines; distinct native study cases and machine-type references |
| `nine_bus_avr_amplidyne.dgs` | IEEE Type 1 Amplidyne AVR, graphical macros and limiter models |
| `nine_bus_avr_pss.dgs` | AVR plus power-system stabilizer, graphical macros and nested block references |
| `bess_base.dgs` | Grid-forming BESS converter, measurements, droop, synchronization, virtual admittance, current limits and fault logic; 59 block definitions |
| `bess_current_controller_on.dgs` | Native `ElmVscmono.i_ctrl`: 0 → 1, integrated current controller |
| `bess_coupled_converter.dgs` | Native `ElmVscmono.iVIsource`: 1 → 0, independent sources → coupled converter |
| `bess_modulation_1.dgs` | Native `ElmVscmono.i_mod`: 0 → 1; numeric variant retained without guessing its enum label |
| `bess_modulation_limit_on.dgs` | Native `ElmVscmono.iVacMax`: 0 → 1, load-flow modulation-index limit |
| `bess_virtual_admittance_dynamic.dgs` | `ElmDsl.params:3`, named `va_mode`: 0 → 1, algebraic → dynamic virtual-admittance branch |

Each of the last five files changes **exactly one field** from `bess_base.dgs`
after object paths and pointer IDs are normalized. The four nine-bus study
cases are broader model configurations, not single-toggle pairs.

`va_mode` is the model-dialog option requested in this investigation: the
exported equations contain `select(va_mode, ..._dyn, ..._nodyn)`. Its value
survives parameter-name decoding and instance construction, and regression
tests verify both equation branches. `i_ctrl`, `i_mod`, and `iVIsource` instead
select built-in equipment behavior: their equations are not provided as DSL
text and need corresponding equipment implementations.

## Parser changes demonstrated by this corpus

- Decode scalar and vector forms of parameter names, block symbols, and limits.
- Preserve quoted CSV fields when specialized parsers call the base parser.
- Retain native converter options, controller constants, and PWM limit values.
- Preserve distinct DSL symbols such as `Iq_max` and `Iq_max_`; replace whole
  symbols once instead of changing substrings inside longer identifiers.
- Repair the detailed statement-support report's variable-limit validator.
- Refuse the existing coupled-voltage RMS adapter for explicitly unsupported
  converter modes in the direct importer; retain a generic template and warning.

## What remains unvalidated

**These are parser and model-selection fixtures, not validated RMS reference
trajectories.** Every block's individual equations parse, but complete composite
assembly still reports the following gaps (see `import_audit.json`):

- BESS: `GRID_VOLTAGE_FRAME(1)` has a typed-slot mismatch; the Q/Vac droop
  graphical macro's `Qref_out` route is not resolved. The native cable runs
  through a `BlkFrom` named `Qref` into the root output.
- AVR cases: a graphical root-input connector uses a position outside the
  compact exported input list (`upss`, index 5, with five declared inputs).
  This requires evidence for the native connector-index mapping before changing
  wiring behavior.
- Classical/standard machine cases: a dynamic frame slot has no resolved
  DSL/composite instance. Standalone equipment import and a complete assembled
  dynamic frame are separate checks.
- Integrated current control, independent AC/DC sources and alternate modulation
  still need equipment equations, initialization, and PowerFactory comparison.
- The exact numeric-to-label mapping of `i_mod` is not independently established.
- This set does not cover every PowerFactory device, version, or option. Existing
  HVDC V1/V2/V3 fixtures elsewhere in this directory complement these cases.

The import audit counts catalogue entries; an importable individual block is
not evidence that its whole network can simulate. No native files were patched
to hide the outstanding wiring issues.

## Reproduce and validate

Run from the repository root:

```bash
.venv/bin/python -m pytest -q src/tests/FileFormats/PowerFactory
PYTHONPATH=src .venv/bin/python trunk/power_factory_validation/dgs_contract_variants/audit_native_fixtures.py src/tests/data/grids/DGS/native_options_pf2024 --output /tmp/dgs-import-audit.json
python3 trunk/power_factory_validation/dgs_contract_variants/compare_exports.py src/tests/data/grids/DGS/native_options_pf2024/bess_base.dgs src/tests/data/grids/DGS/native_options_pf2024/bess_virtual_admittance_dynamic.dgs --match-paths
```

The validated Windows exporter and exact monitor definitions are in
`trunk/power_factory_validation/dgs_contract_variants/`. See its README for
PowerFactory prerequisites and export procedure.
