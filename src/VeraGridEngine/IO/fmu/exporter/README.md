# VeraGrid FMU Export

Non-invasive FMI 2.0 Co-Simulation export pipeline for VeraGrid symbolic `Block` models.

Current design goals:

- keep the existing Python runtime untouched
- snapshot and reconstruct `Block` models through `to_dict()` / `Block.parse()`
- flatten models on an isolated copy
- build one deterministic export IR shared by XML and C generation
- generate a standalone C runtime template for the resulting FMU

The package lives under `trunk/veragrid_fmu_export` on purpose so it can evolve without changing the current engine package layout.

Pilot models and validation:

- `python -m trunk.veragrid_fmu_export.host_validation rms`
- `python -m trunk.veragrid_fmu_export.host_validation emt`

These pilot flows currently exercise:

- one real RMS-derived VeraGrid model: `FrequencyLoadBuild`
- one real EMT-derived VeraGrid model: `get_generator_thevenin_rl_emt_template`
- export to FMI 2.0 Co-Simulation FMU
- FMU validation and simulation through FMPy

Windows host note:

- the validation helpers extract FMUs into the FMU output folder instead of `%TEMP%`, which avoids Windows Application Control policies that block unsigned DLL loads from temporary directories
- hosts that insist on extracting FMUs internally (for example some Simulink setups) may still need a trusted extraction directory via `TEMP` / `TMP`, or a code-signing / allow-list rule for the generated FMU DLLs
