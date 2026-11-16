# Native DSL lookup payload fixtures

These two additional baselines were exported from PowerFactory 24.0.2.0,
using DGS 7.0 ASCII and `/external`, in job
`8d80ddc02eb94e12bc67a87d21eab98d`. They extend the existing ElmVsc/ElmGenstat
fixtures with the native `ElmDsl.matrix` and `ElmDsl.matrix2` fields. The
original nineteen toggle fixtures remain unchanged.

`manifest.json` records hashes, source projects and cases, actual equipment
options, table counts and native export results. Both exports returned zero
without export warnings, have unique columns and IDs, and contain all pointer
targets. Files are untouched native exports.

- `genstat_lookup_tables.dgs` preserves Q(P), Q(V), protection and reference
  signal tables. The `PQ_ctrl` instance contains two separate two-point curves.
  The `Señales` instance contains curves of seven, four and eight points.
- `vsc_lookup_tables.dgs` preserves the VSC modulation and current-limiting
  curves and the wind turbine's two-dimensional coefficient table.

The parser now preserves the numerical cells on each **ElmDsl instance**.
It uses each row's declared matrix dimensions and excludes padding introduced
by the maximum table dimensions in the shared DGS header. Invalid dimensions,
missing cells and nonnumeric cells raise an error rather than becoming zeros.

For internal one-dimensional lookup arrays, `get_lookup_arrays(definition)`
associates consecutive column pairs with the `array_` names declared by the
instance's model definition. The first column of each pair stores its point
count in the first row; the adjacent cell can repeat that count or be zero;
the following rows contain x/y pairs. Values and point order are retained.
Native reference curves contain repeated x values, which are intentionally
neither sorted nor deduplicated.

For example, the native reference-signal matrix begins with
`[7, 7, 4, 4, 8, 8]`, followed by three independent pairs of columns.
The turbine's `matrix2` contains 67 rows and 49 columns; its first row starts
with `[66, 49]`, preserving PowerFactory's internal size metadata and axes.

`lapprox` now uses each instance's own curves, with linear interpolation and
constant endpoint extrapolation. Array aliases propagate through graphical
BlkRef parameters, including selectors between tables. Specialization preserves
the requested RMS/EMT domain. Nonfinite values, repeated knots and descending
knots fail explicitly; `sapprox2` remains unsupported.

The native VSC baseline imports, but its complete controller cannot run yet:
the onshore dq interface now supplies equipment-base, generator-oriented
`id`/`iq`, but its exported PLL slot has no resolved instance, so assembly
stops at `cosref`. The offshore magnitude/frequency interface remains
unsupported and its `i_acdc=0` control pair remains inactive. Wind turbine roots also require
`sapprox2`. Passing lookup tests does not establish trajectory equivalence with
PowerFactory. No native trajectory comparison has been performed for this change.

To reproduce, run `export_equipment_options.py --config lookup_exports.json`
on the licensed host with the dedicated projects and export-definition folder
prepared as documented in the equipment-option fixture README. The monitor
extensions add `matrix` and `matrix2` to the ElmDsl export fields. Verify
`provenance.json` contains `ok: true` before accepting the files.

Validation from the repository root:

```bash
.venv/bin/python -m pytest -q src/tests/FileFormats/PowerFactory/test_dgs_lookup_payload.py src/tests/FileFormats/PowerFactory/test_dgs_vsc_lookup.py
```

The tests verify native hashes, table dimensions, selected actual cell values,
array-to-column association, retention of repeated knots, rejection of malformed
payloads and compatibility with legacy files that omit matrix fields.

## BESS/VSC follow-up evidence (2026-11-10)

`vsc_import_audit_20261110.json` records the lookup-rich VSC baseline's actual
RMS import diagnostics. The BESS corpus has a separate
`../native_options_pf2024/bess_assembly_audit_20261110.json` report.

BESS variants using independent sources (`iVIsource=1`), the integrated current
controller (`i_ctrl=1`) or the alternate modulation (`i_mod=1`) still require
matching physical equipment models. The coupled BESS export supplies
`id_ref,iq_ref,i2d_ref,i2q_ref,cosref,sinref`; its current bridge implementation
requires `Pmd,Pmq,cosref,sinref`. PF2024 PWM technical reference section 5.5
specifies that with current-reference inputs and `i_ctrl=0`, modulation is held
at its initialized value. This exact selector case is now implemented; scoped
From/Goto routes also bind the BESS `cosref`/`sinref` producers. The coupled BESS
root now assembles. This does not establish load-flow activation or trajectory
equivalence; its `i_acdc=0` network control pair is still reported unsupported.
