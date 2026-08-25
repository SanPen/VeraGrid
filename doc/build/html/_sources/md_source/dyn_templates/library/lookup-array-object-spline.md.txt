# Lookup array object (spline)

<!-- veragrid-block-introduction:start -->
**Lookup array object (spline)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup array object (spline) interpolates from a stored one-dimensional lookup object using spline interpolation. Use it when you want a smoother curve than piecewise linear interpolation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
