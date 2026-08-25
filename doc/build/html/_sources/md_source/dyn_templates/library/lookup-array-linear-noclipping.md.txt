# Lookup array (linear noclipping)

<!-- veragrid-block-introduction:start -->
**Lookup array (linear noclipping)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup array (linear noclipping) interpolates from a one-dimensional table without clipping the input to the stored range. Use it when extrapolation or out-of-range handling should follow the template behavior instead of saturating.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `array_K` | Stored lookup array | data object |
