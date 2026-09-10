# VeraGridEngine Module: src/VeraGridEngine/Templates/Rms/bus_phasor_rms_template.py

- Original source path: `src/VeraGridEngine/Templates/Rms/bus_phasor_rms_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 5
- Representative imports: __future__, typing, typing, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.rms_template, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.enumerations

## Class: BusPhasorRmsTemplate

- Bases: RmsModelTemplate
- Summary: Phasor-based RMS template for buses using real and imaginary voltage components.

### Methods

- No methods detected.

## Function: initialize_bus_phasor_rms(bus, vf)

Initialize the phasor-based RMS model for a bus.

## Function: get_bus_phasor_rms_algebraic_vars(bus_rms_model)

Get the algebraic variables (Vr, Vi) from the phasor bus model.

## Function: check_empty_bus(bus_rms_model)

Check if the bus model has no algebraic variables.

## Function: polar_to_phasor(Vm, Va)

Convert polar coordinates (magnitude, angle) to phasor (real, imaginary).

## Function: phasor_to_polar(Vr, Vi)

Convert phasor (real, imaginary) to polar coordinates (magnitude, angle).
