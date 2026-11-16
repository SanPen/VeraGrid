# Native Genstat protection and voltage-source validation

The four top-level DGS files are unedited PowerFactory 2024 / DGS7 exports from
isolated fixture project `VeraGrid DGS Genstat Options 20261110`, API job
`f27502eaace34a9fa31012c09fd9612d`. `manifest.json` records SHA-256 hashes,
selectors, changed fields, native descriptions and zero export errors/warnings.
They retain `umin`, `uonthr`, `Tondelay`, `uk` and `Pcu`.

- Current, voltage-source and constant-power variants use switch-off 0.2 pu,
  switch-on 0.3 pu and 0.1 s reconnection delay.
- The unprotected current-source variant changes only `umin` to zero.
- These four fixture networks have an unresolved controller; their assigned
  fallback explicitly preserves only the selected electrical source law.

`benchmark/` contains three further unedited native exports of a dedicated
110 kV two-bus benchmark. Job `565c9de627c241f39307ae422ed27b32` exported them
with return code zero. The source is 25 MVA, dispatch 5 MW / 1 Mvar, uk=10%,
Pcu=0. `runtime_model_2.json` records a converged VeraGrid initialization and
one finite converged 1 ms RMS step for the voltage-source benchmark.

`dynamic_reference.json` is native PowerFactory output from job
`66245ba1c6cd4584accf4bcab2eaf8bc`. It records two three-phase faults, at 0.05–0.10
and 0.15–0.17 seconds. Current-source and voltage-source simulations both
initialize and finish successfully. Injection is blocked during the dips and
remains zero until about 0.27 seconds; the second fault cancels the first
reconnection timer. Tests replay the measured voltage through VeraGrid's
compiled procedural logic and check switching agreement within one 1 ms sample.
This verifies switching semantics, not complete phasor trajectory equivalence.

The native constant-power simulation fails at the exact-zero-voltage fault;
its return code and messages are retained. It is not a successful reference
validation. A later finite-impedance benchmark attempt timed out before producing
results and adds no validation evidence.

Reproduction scripts and configurations are in
`trunk/power_factory_validation/dgs_contract_variants/`:
`genstat_protection_options.json`, `export_equipment_options.py`, and
`pf_genstat_dynamic_reference.py`.
