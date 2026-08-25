# Generic

<!-- veragrid-block-introduction:start -->
**Generic** is a reusable symbolic building block for dynamic models. Its inputs, outputs, parameters, equations, and runtime logic define a mathematical signal relation that can be composed with network, machine, converter, and control subsystems.

## Typical use

- Use it when assembling or extending a dynamic model with the documented symbolic relation.
- Inspect equations and interface units before connecting it to blocks from another physical domain.
<!-- veragrid-block-introduction:end -->

Placeholder dynamic block for custom signal/state wiring.

## Purpose and behavior

The Generic block is an empty structural starting point for a user-authored
dynamic model. General options define how many input and output ports are
created. The DAE model tab then lets the author add parameters, algebraic
variables, states, differential variables, initialization equations, and the
equations that relate them.

The block has no physical law until equations are added. Consequently, a newly
created Generic block should not be interpreted as a gain, source, or load.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `state_*` | Configured state inputs | model-dependent |
| Input | `alg_*` | Configured algebraic inputs | model-dependent |
| Output | `state_*` | Configured state outputs | model-dependent |
| Output | `alg_*` | Configured algebraic outputs | model-dependent |

## How to use it

1. Select the required input/output counts in General options.
2. Add typed symbols in the DAE model tab.
3. Write and validate the equations before applying them.
4. Connect only the exported variables that form the public block interface.

Use a catalogue block instead when an equivalent documented physical or control
model already exists.
