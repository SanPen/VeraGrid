# Inverse Lookup array object (linear)

<!-- veragrid-block-introduction:start -->
**Inverse Lookup array object (linear)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Inverse Lookup array object (linear) maps an input back through a stored one-dimensional lookup object using linear interpolation. Use it when you need the inverse of a tabulated nonlinear relation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input value to invert through the table | model-dependent |
| Output | `yo` | Interpolated inverse lookup result | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
