# Lookup matrix object (linear)

This is Basic Block Catalog type `19` (`Lookup matrix object (linear)`). It evaluates tabulated or array-based data using the selected lookup formulation.

<!-- veragrid-block-introduction:start -->
**Lookup matrix object (linear)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Arrays and Matrices`.
- Inputs: 2.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 1.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - (0 + (arr_{z1\_1} \cdot (1 - \frac{arr_{x1} + (yi1 - arr_{x1}) \cdot \Theta\left(yi1 - arr_{x1}\right) - (yi1 - arr_{x2}) \cdot \Theta\left(yi1 - arr_{x2}\right) - arr_{x1}}{arr_{x2} - arr_{x1}}) \cdot (1 - \frac{arr_{y1} + (yi2 - arr_{y1}) \cdot \Theta\left(yi2 - arr_{y1}\right) - (yi2 - arr_{y2}) \cdot \Theta\left(yi2 - arr_{y2}\right) - arr_{y1}}{arr_{y2} - arr_{y1}}) + arr_{z1\_2} \cdot \frac{arr_{x1} + (yi1 - arr_{x1}) \cdot \Theta\left(yi1 - arr_{x1}\right) - (yi1 - arr_{x2}) \cdot \Theta\left(yi1 - arr_{x2}\right) - arr_{x1}}{arr_{x2} - arr_{x1}} \cdot (1 - \frac{arr_{y1} + (yi2 - arr_{y1}) \cdot \Theta\left(yi2 - arr_{y1}\right) - (yi2 - arr_{y2}) \cdot \Theta\left(yi2 - arr_{y2}\right) - arr_{y1}}{arr_{y2} - arr_{y1}}) + arr_{z2\_1} \cdot (1 - \frac{arr_{x1} + (yi1 - arr_{x1}) \cdot \Theta\left(yi1 - arr_{x1}\right) - (yi1 - arr_{x2}) \cdot \Theta\left(yi1 - arr_{x2}\right) - arr_{x1}}{arr_{x2} - arr_{x1}}) \cdot \frac{arr_{y1} + (yi2 - arr_{y1}) \cdot \Theta\left(yi2 - arr_{y1}\right) - (yi2 - arr_{y2}) \cdot \Theta\left(yi2 - arr_{y2}\right) - arr_{y1}}{arr_{y2} - arr_{y1}} + arr_{z2\_2} \cdot \frac{arr_{x1} + (yi1 - arr_{x1}) \cdot \Theta\left(yi1 - arr_{x1}\right) - (yi1 - arr_{x2}) \cdot \Theta\left(yi1 - arr_{x2}\right) - arr_{x1}}{arr_{x2} - arr_{x1}} \cdot \frac{arr_{y1} + (yi2 - arr_{y1}) \cdot \Theta\left(yi2 - arr_{y1}\right) - (yi2 - arr_{y2}) \cdot \Theta\left(yi2 - arr_{y2}\right) - arr_{y1}}{arr_{y2} - arr_{y1}}) \cdot \Theta\left(arr_{x1} + (yi1 - arr_{x1}) \cdot \Theta\left(yi1 - arr_{x1}\right) - (yi1 - arr_{x2}) \cdot \Theta\left(yi1 - arr_{x2}\right) - arr_{x1} + 1 \times 10^{-6}\right) \cdot \Theta\left(arr_{y1} + (yi2 - arr_{y1}) \cdot \Theta\left(yi2 - arr_{y1}\right) - (yi2 - arr_{y2}) \cdot \Theta\left(yi2 - arr_{y2}\right) - arr_{y1} + 1 \times 10^{-6}\right)))
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | Input signal consumed by the block | model-dependent |
| Input | `yi2` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `omatrix_K` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
