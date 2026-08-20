# Lookup array 1x3 (linear fixed)

This is Basic Block Catalog type `10` (`Lookup array 1x3 (linear_fixed)`). It evaluates tabulated or array-based data using the selected lookup formulation.

<!-- veragrid-block-introduction:start -->
**Lookup array 1x3 (linear fixed)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Arrays and Matrices`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 7.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (Lookup array 1x3 (linear_{fixed)\_m} - (proc_{select\_4} \cdot (proc_{selfix\_0} \cdot 0 + (1 - proc_{selfix\_0}) \cdot Lookup array 1x3 (linear_{fixed)\_m1}) + (1 - proc_{select\_4}) \cdot (proc_{select\_3} \cdot Lookup array 1x3 (linear_{fixed)\_m1} + (1 - proc_{select\_3}) \cdot (proc_{select\_2} \cdot Lookup array 1x3 (linear_{fixed)\_m2} + (1 - proc_{select\_2}) \cdot (proc_{selfix\_1} \cdot 0 + (1 - proc_{selfix\_1}) \cdot Lookup array 1x3 (linear_{fixed)\_m2})))))
$$

$$
0 = (Lookup array 1x3 (linear_{fixed)\_n} - (proc_{select\_9} \cdot (proc_{selfix\_5} \cdot arr_{y1} + (1 - proc_{selfix\_5}) \cdot (arr_{y2} - Lookup array 1x3 (linear_{fixed)\_m} \cdot arr_{x2})) + (1 - proc_{select\_9}) \cdot (proc_{select\_8} \cdot (arr_{y2} - Lookup array 1x3 (linear_{fixed)\_m} \cdot arr_{x2}) + (1 - proc_{select\_8}) \cdot (proc_{select\_7} \cdot (arr_{y3} - Lookup array 1x3 (linear_{fixed)\_m} \cdot arr_{x3}) + (1 - proc_{select\_7}) \cdot (proc_{selfix\_6} \cdot arr_{y3} + (1 - proc_{selfix\_6}) \cdot (arr_{y3} - Lookup array 1x3 (linear_{fixed)\_m} \cdot arr_{x3}))))))
$$

$$
0 = (yo - (Lookup array 1x3 (linear_{fixed)\_m} \cdot yi + Lookup array 1x3 (linear_{fixed)\_n}))
$$

$$
Lookup array 1x3 (linear_{fixed)\_m1}(t_0) = (\frac{arr_{y2} - arr_{y1}}{arr_{x2} - arr_{x1}})
$$

$$
Lookup array 1x3 (linear_{fixed)\_m2}(t_0) = (\frac{arr_{y3} - arr_{y2}}{arr_{x3} - arr_{x2}})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `arr_x1` | Configurable model parameter | model-dependent |
| Parameter | `arr_x2` | Configurable model parameter | model-dependent |
| Parameter | `arr_x3` | Configurable model parameter | model-dependent |
| Parameter | `arr_y1` | Configurable model parameter | model-dependent |
| Parameter | `arr_y2` | Configurable model parameter | model-dependent |
| Parameter | `arr_y3` | Configurable model parameter | model-dependent |
| Parameter | `vClip` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
