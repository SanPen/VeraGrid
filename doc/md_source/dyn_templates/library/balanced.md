# balanced

### Purpose

This block generates balanced multi-phase outputs from one reference quantity.

### Behavior

- Receives one reference signal.
- Produces coordinated outputs with balanced phase relation or balanced scaling.

### Characteristics

- Useful when one control reference must be expanded into balanced phase quantities.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Reference input signal | model-dependent |
| Output | `yo_A` | Balanced phase-A output | model-dependent |
| Output | `yo_B` | Balanced phase-B output | model-dependent |
| Output | `yo_C` | Balanced phase-C output | model-dependent |

## How to use it

- Use this block when one command or reference must be distributed into balanced phase outputs.
