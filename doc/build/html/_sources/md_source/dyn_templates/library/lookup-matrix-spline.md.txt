# Lookup matrix (spline)

<!-- veragrid-block-introduction:start -->
**Lookup matrix (spline)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup matrix (spline) interpolates a two-input surface using spline interpolation. Use it when you want a smoother mapped surface than linear interpolation provides.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First lookup input | model-dependent |
| Input | `yi2` | Second lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `matrix_K` | Stored lookup matrix | data object |
