# Lookup array 1x4 (linear variable)

<!-- veragrid-block-introduction:start -->
**Lookup array 1x4 (linear variable)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Lookup array 1x4 (linear variable) interpolates between four x-y points supplied as signals. Use it when both the curve shape and the lookup input change at runtime.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Input | `arr_x1` | First x-coordinate input | same as `yi` |
| Input | `arr_x2` | Second x-coordinate input | same as `yi` |
| Input | `arr_x3` | Third x-coordinate input | same as `yi` |
| Input | `arr_x4` | Fourth x-coordinate input | same as `yi` |
| Input | `arr_y1` | Output value for `arr_x1` | same as `yo` |
| Input | `arr_y2` | Output value for `arr_x2` | same as `yo` |
| Input | `arr_y3` | Output value for `arr_x3` | same as `yo` |
| Input | `arr_y4` | Output value for `arr_x4` | same as `yo` |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `vClip` | Clipping control | boolean, 0/1, or model-dependent |
