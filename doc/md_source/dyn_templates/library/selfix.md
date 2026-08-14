# Selfix

### Purpose

This block keeps or fixes one selected signal path according to one runtime condition.

### Behavior

- Receives candidate signals and one runtime selection condition.
- Outputs the chosen signal.

### Characteristics

- Useful in supervisory logic when the active signal path depends on operating conditions.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate signal | model-dependent |
| Input | `s2` | Second candidate signal | model-dependent |
| Input | `sel` | Runtime selection signal | integer, boolean, or model-dependent |
| Output | `yo` | Selected output signal | model-dependent |

## How to use it

- Use this block when a signal path must be selected dynamically during simulation.
