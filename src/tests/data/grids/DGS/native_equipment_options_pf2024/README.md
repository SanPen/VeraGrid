# Native PowerFactory equipment-option fixtures

22 unedited PowerFactory 2024 / DGS 7 ASCII exports, downloaded from dedicated
fixture projects. `manifest.json` records native attributes, study cases, return
codes, warnings, SHA-256 hashes and changed values. The original ten machine/AVR/
BESS exports remain in the sibling `native_options_pf2024` directory.

- 11 ElmVsc variants plus two baselines cover topology, integrated current
  control, modulation, independent AC/DC sources, arm-reactor DC handling and
  modulation limiting. Some options are specific to RMS, EMT or load flow;
  changing a native field is not evidence that it changes RMS equations.
- Five ElmGenstat model/reference-machine variants plus one baseline cover
  automatic, current, voltage, impedance and power source selection.
- Three additional Genstat exports isolate `iDelay` and `Tdelay`. The 20 ms
  variant deliberately leaves `iDelay=0`: changing the time constant alone must
  not enable lag. Native float values are compared with numerical tolerance.

## Current validation

`test_dgs_equipment_options.py` verifies hashes, unique headers, pointer closure,
exact one-field pair differences, selector preservation, parallel-unit source
laws and unsupported selections. `test_dgs_native_regressions.py` checks the
controlled Genstat delay flag, power-base scaling, frame rotation and analytic
lag derivatives. These are equation/assembly checks, not PF trajectory parity.

`import_audit.json` records full RMS network imports. All 22 calls return, but
several physical models remain unavailable. Repeated diagnostics and identical
parallel-device assignments are summarized with counts.

- Genstat constant current/impedance/power fallback laws are preserved with an
  explicit warning when their controller cannot be imported. This does not
  reproduce the controller dynamics. Automatic mode with an unresolved
  controller, voltage-source/reference-machine mode and enabled delay in the
  fallback remain inactive.
- Controlled Genstat supports current-source equations with optional internal
  angle lag and voltage-source equations when uk/Pcu are exported. External dq
  reference bindings remain unsupported. The original voltage-mode fixture lacks
  reactor columns and therefore remains inactive; see the separate
  native_genstat_protection_pf2024 corpus for the new voltage/protection fixtures.
- Native controllers still expose unsupported array-valued `lapprox` and
  `sapprox2` expressions. Several VSC options remain unsupported.

Reproduce the main exports with `export_equipment_options.py` and
`equipment_options.json`; use `genstat_delay_options.json` for the delay trio.
Scripts are in `trunk/power_factory_validation/dgs_contract_variants/`.

### Additional delay-option fixtures

The current manifest also includes three native delay-option files: a baseline,
`iDelay` enabled, and a changed `Tdelay`. The folder now contains 22 exports
(four baselines and eighteen variants). The updated audit includes all 22.
The raw source schema preserves these fields. When a complete controller cannot
be assembled, enabled dq-reference delay requires explicit equipment support
and is kept inactive by the simple fallback. Changing the time constant with
the delay disabled preserves the current-source fallback.
