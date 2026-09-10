# VeraGridEngine Module: src/VeraGridEngine/Templates/Emt/vsc_gfl_emt.py

- Original source path: `src/VeraGridEngine/Templates/Emt/vsc_gfl_emt.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 5
- Representative imports: typing, numpy, math, VeraGridEngine.enumerations, VeraGridEngine.Devices.Dynamic.emt_template, VeraGridEngine.Utils.Symbolic.block, VeraGridEngine.Templates.templates_common_functions, VeraGridEngine.Devices.Dynamic.var_factory, VeraGridEngine.Utils.Symbolic.symbolic, VeraGridEngine.enumerations

## Function: inverse_park_transform_block(vfactory, v_dq, theta, aux_vars, multilinear, name)

Create a symbolic inverse Park transform (dq → abc) block for voltages.

## Function: park_transform_block(vfactory, v_abc, theta, multilinear, aux_vars, name)

Create a symbolic Park transform (abc → dq) block for voltages and currents.

## Function: pll_transform(vfactory, v_abc, multilinear, name)

EMT PLL using instantaneous three-phase voltages.

## Function: build_gfl_converter_model_emt(vfactory, inputs, control1, control2, multilinear)

Build power control loop model for Grid Following Converter for EMT simulation.

## Function: VscGflEmtBuild(vfactory, name, control1, control2)

VSC GFL (Grid Following) EMT model
