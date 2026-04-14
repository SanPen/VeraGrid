# PowerFactory Validation

This exporter already validates the generated FMUs with FMPy.

For DIgSILENT PowerFactory, the repository now includes a helper entry point:

```bash
python -m trunk.veragrid_fmu_export.pf_validation rms
python -m trunk.veragrid_fmu_export.pf_validation emt
python C:\Users\andre\PycharmProjects\VeraGrid\trunk\veragrid_fmu_export\pf_validation.py rms --project "Project_prueba" --study-case "Caso Base"
python C:\Users\andre\PycharmProjects\VeraGrid\trunk\veragrid_fmu_export\pf_validation.py rms --project "Project_prueba" --study-case "Caso Base" --configure --agent-name "Test"
```

If you run `pf_validation.py` directly from PyCharm with no arguments, it now uses IDE defaults:

- pilot: `rms`
- project: `Project_prueba`
- study case: `Caso Base`
- agent: `Test`
- configure: enabled
- execute: enabled

You can change those defaults in `trunk/veragrid_fmu_export/pf_validation.py` under `IDE_PLAY_DEFAULTS`.

What it does:

- exports the selected pilot FMU
- probes the local PowerFactory Python API installation
- checks whether a valid PowerFactory license can be obtained
- optionally activates a chosen PowerFactory project and study case
- can attach the exported FMU automatically to `ComCosim.tableExtFMU` by creating/updating an `ElmAgent`
- prints a manual import checklist for the generated FMU

What it does not yet do automatically:

- wire the FMU signals to other FMUs or network signals automatically

Current recommendation:

- open PowerFactory manually first
- run `pf_validation.py` with `--configure`
- avoid `--allow-engine` unless you explicitly want an engine-mode PowerFactory session

Recommended manual validation once you bring the license:

1. Run `python -m trunk.veragrid_fmu_export.pf_validation rms`
2. Confirm `license_available` becomes `True`
3. Import the FMU path reported by the script into a clean PowerFactory project
4. For the RMS pilot, feed constant `Vm_=1.0`, `Va_=0.0` and verify `P≈1.0`, `Q≈0.1`
5. For the EMT pilot, feed balanced three-phase voltages and verify non-zero injected currents
6. Save any PowerFactory rejection/error message exactly as shown so the importer integration can be tightened
