# VeraGridEngine Module: src/VeraGridEngine/Templates/Rms/vsc_gfl.py

- Original source path: `src/VeraGridEngine/Templates/Rms/vsc_gfl.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 8
- Representative imports: numpy, math, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.rms_template, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Templates.templates_common_functions, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.enumerations

## Function: inverse_park_transform_block(vfactory, v_dq, theta, aux_vars, multilinear, name)

Create a symbolic inverse Park transform (dq → abc) block for voltages.

## Function: park_transform_block(vfactory, v_abc, theta, multilinear, aux_vars, name)

Create a symbolic Park transform (abc → dq) block for voltages and currents.

## Function: pll_transform_rms(vfactory, Vm, Va, name)

No docstring provided.

## Function: pll_transform(vfactory, v_abc, multilinear, name)

No docstring provided.

## Function: build_gfl_converter_model(vfactory, inputs, control1, control2, multilinear)

Build power control loop model for Grid Following Converter.

## Function: trafo_gfl_converter_model(vfactory, inputs, control1, control2)

GFL converter model for transformer-coupled setup.

## Function: VscGflBuild(vfactory, name, control1, control2)

VSC GFL (Grid Following) model

## Function: TrafoGflBuild(vfactory, name, control1, control2)

Transformer-coupled GFL model where AC-from side is internal converter bus
