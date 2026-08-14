# Controlled current source EMT

Single-phase EMT current source driven by an input signal.

### Purpose

This block converts one runtime command signal into one imposed single-phase current injection. It is useful when another control block must directly prescribe the injected current.

### Behavior

- Receives one current command input.
- Produces one source-current output following that command.
- Leaves the resulting terminal voltage to be determined by the surrounding network.

### Characteristics

- EMT controlled source primitive.
- Single-phase ideal current injection.
- Useful for custom actuator, converter, and current-forcing assemblies.

## How it works

The block interprets the input signal as the desired source current. That current is then injected into the connected network. The block does not solve internal current-control dynamics unless those are supplied by the blocks that generate the command.

## Characteristic equations

$$
i(t) = u(t)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `u` | Commanded source value | model-dependent |
| Output | `i` | Imposed source current | A |

## How to use it

- Use it when another part of the diagram computes the source current directly.
- Use a higher-level converter block instead when the current should arise from internal power electronics and control dynamics.
