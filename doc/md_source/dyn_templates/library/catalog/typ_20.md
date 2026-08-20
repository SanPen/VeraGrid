# Lookup matrix object (spline)

This is Basic Block Catalog type `20` (`Lookup matrix object (spline)`). It evaluates tabulated or array-based data using the selected lookup formulation.

<!-- veragrid-block-introduction:start -->
**Lookup matrix object (spline)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

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
0 = (yo - ((arr_{z1\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z1\_1} \cdot 1 + arr_{z1\_2} \cdot 0 + (0 + arr_{z1\_1} \cdot -1 + arr_{z1\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot \Theta\left(arr_{y1} - yi2 - 1 \times 10^{-6}\right) + (0 + (arr_{z1\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z1\_1} \cdot 1 + arr_{z1\_2} \cdot 0 + (0 + arr_{z1\_1} \cdot -1 + arr_{z1\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 1 + (arr_{z2\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z2\_1} \cdot 1 + arr_{z2\_2} \cdot 0 + (0 + arr_{z2\_1} \cdot -1 + arr_{z2\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0 + (0 + (arr_{z1\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z1\_1} \cdot 1 + arr_{z1\_2} \cdot 0 + (0 + arr_{z1\_1} \cdot -1 + arr_{z1\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot -0.5 + (arr_{z2\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z2\_1} \cdot 1 + arr_{z2\_2} \cdot 0 + (0 + arr_{z2\_1} \cdot -1 + arr_{z2\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0.5) \cdot (yi2 - arr_{y1}) + (0 + (arr_{z1\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z1\_1} \cdot 1 + arr_{z1\_2} \cdot 0 + (0 + arr_{z1\_1} \cdot -1 + arr_{z1\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0 + (arr_{z2\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z2\_1} \cdot 1 + arr_{z2\_2} \cdot 0 + (0 + arr_{z2\_1} \cdot -1 + arr_{z2\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0) \cdot (yi2 - arr_{y1}) \cdot (yi2 - arr_{y1}) + (0 + (arr_{z1\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z1\_1} \cdot 1 + arr_{z1\_2} \cdot 0 + (0 + arr_{z1\_1} \cdot -1 + arr_{z1\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z1\_1} \cdot 0 + arr_{z1\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0 + (arr_{z2\_1} \cdot \Theta\left(arr_{x1} - yi1 - 1 \times 10^{-6}\right) + (0 + arr_{z2\_1} \cdot 1 + arr_{z2\_2} \cdot 0 + (0 + arr_{z2\_1} \cdot -1 + arr_{z2\_2} \cdot 1) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) + (0 + arr_{z2\_1} \cdot 0 + arr_{z2\_2} \cdot 0) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1}) \cdot (yi1 - arr_{x1})) \cdot \Theta\left(yi1 - arr_{x1} + 1 \times 10^{-6}\right)) \cdot 0) \cdot (yi2 - arr_{y1}) \cdot (yi2 - arr_{y1}) \cdot (yi2 - arr_{y1})) \cdot \Theta\left(yi2 - arr_{y1} + 1 \times 10^{-6}\right)))
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
