# Grounding link EMT

<!-- veragrid-block-introduction:start -->
**Grounding link EMT** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Ground connection element used to tie a node to reference.

## Internal composition

The grounding link connects one exposed node to an internal Ground EMT child.
The path can be solid or can contain selected R, L, and C branches. When several
passive branches are enabled they share the same node-to-ground voltage and
their currents contribute to the exported grounding current.

General options choose the included branches, their direct values, whether the
connection is solid, and whether the block is nested in another template. A
non-solid link requires at least one passive branch.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Terminal | `node` | Network node being grounded | model-dependent |
| Terminal | `gnd` | Ground reference node | model-dependent |
| Parameter | `R` | Grounding resistance | ohm |

## How to use it

- Use a solid connection only for an ideal ground constraint.
- Keep enabled R/L/C values physically meaningful and numerically well scaled.
- Do not enable neutral on unrelated phase blocks merely to compensate for a
  missing grounding topology; model the intended neutral path explicitly.
