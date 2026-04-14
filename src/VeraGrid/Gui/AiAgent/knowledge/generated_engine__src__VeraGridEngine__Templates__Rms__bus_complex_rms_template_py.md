# VeraGridEngine Module: src/VeraGridEngine/Templates/Rms/bus_complex_rms_template.py

- Original source path: `src/VeraGridEngine/Templates/Rms/bus_complex_rms_template.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 7
- Representative imports: __future__, typing, numpy, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.rms_template, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Utils.Symbolic.symbolic

## Class: BusComplexRmsTemplate

- Bases: RmsModelTemplate
- Summary: Complex phasor-based RMS template for buses using a single complex voltage variable.

### Methods

- No methods detected.

## Function: initialize_bus_complex_rms(bus, vf)

Initialize the complex phasor-based RMS model for a bus.

## Function: get_bus_complex_rms_algebraic_vars(bus_rms_model)

Get the algebraic variables (Vr, Vi) from the complex bus model.

## Function: get_bus_complex_voltage(bus_rms_model)

Get the complex voltage variable from the bus model.

## Function: polar_to_complex(Vm, Va)

Convert polar coordinates (magnitude, angle) to complex phasor.

## Function: complex_to_polar(V)

Convert complex phasor to polar coordinates (magnitude, angle).

## Function: complex_to_real_imag(V)

Convert complex phasor to real and imaginary components.

## Function: real_imag_to_complex(Vr, Vi)

Convert real and imaginary components to complex phasor.
