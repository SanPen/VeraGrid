# Ground EMT

<!-- veragrid-block-introduction:start -->
**Ground EMT** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

Electrical ground reference for EMT networks.

### Purpose

This block provides the reference potential of an EMT electrical network. Use it whenever one electrical subsystem needs an explicit ground or neutral reference.

### Behavior

- Exposes one grounding terminal.
- Defines the electrical reference potential for the connected subsystem.
- Does not inject dynamic behavior by itself.

### Characteristics

- EMT network utility block.
- Zero-reference node.
- Required in circuits that need an explicit ground connection.

## How it works

The block anchors the connected node to the model reference potential. It does not contain internal dynamics or parameters; it simply provides the electrical datum needed by the network equations.

## Characteristic equations

$$
v_{gnd} = 0
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Terminal | `gnd` | Reference node connection | model-dependent |

## How to use it

- Use it anywhere one EMT subsystem requires an explicit zero-potential reference.
- Avoid leaving floating subnetworks unintentionally when one physical ground is required for correct behavior.
