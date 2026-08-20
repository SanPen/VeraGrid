# Lookup array object (linear)

<!-- veragrid-block-introduction:start -->
**Lookup array object (linear)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup array object (linear) interpolates from a stored one-dimensional lookup object using linear interpolation. Use it when the table is managed as a reusable object rather than inline points.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
