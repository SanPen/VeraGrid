# Lookup matrix object (spline)

<!-- veragrid-block-introduction:start -->
**Lookup matrix object (spline)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup matrix object (spline) interpolates a two-input surface from a stored matrix object using spline interpolation. Use it when you need a smoother reusable 2D table.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First lookup input | model-dependent |
| Input | `yi2` | Second lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `omatrix_K` | Stored lookup-matrix object | data object |
