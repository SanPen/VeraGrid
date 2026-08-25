# Lookup array object (linear)

This is Basic Block Catalog type `14` (`Lookup array object (linear)`). It evaluates tabulated or array-based data using the selected lookup formulation.

<!-- veragrid-block-introduction:start -->
**Lookup array object (linear)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Arrays and Matrices`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 1.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - (arr_{y1} \cdot \Theta\left(arr_{x1} - yi - 1 \times 10^{-6}\right) + (\frac{arr_{y2} - arr_{y1}}{arr_{x2} - arr_{x1}} \cdot yi + arr_{y1} - \frac{arr_{y2} - arr_{y1}}{arr_{x2} - arr_{x1}} \cdot arr_{x1}) \cdot \Theta\left(yi - arr_{x1} + 1 \times 10^{-6}\right) \cdot \Theta\left(arr_{x2} - yi - 1 \times 10^{-6}\right) + (\frac{arr_{y3} - arr_{y2}}{arr_{x3} - arr_{x2}} \cdot yi + arr_{y2} - \frac{arr_{y3} - arr_{y2}}{arr_{x3} - arr_{x2}} \cdot arr_{x2}) \cdot \Theta\left(yi - arr_{x2} + 1 \times 10^{-6}\right) \cdot \Theta\left(arr_{x3} - yi - 1 \times 10^{-6}\right) + arr_{y3} \cdot \Theta\left(yi - arr_{x3} + 1 \times 10^{-6}\right)))
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `oarray_K` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
