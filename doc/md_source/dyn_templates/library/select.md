# Select

### Purpose

This block selects one signal from a set of candidate inputs according to one selector rule.

### Behavior

- Receives multiple candidate inputs.
- Uses one selector condition or index.
- Outputs the selected signal.

### Characteristics

- Useful in supervisory control and mode management.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate input signal | model-dependent |
| Input | `s2` | Second candidate input signal | model-dependent |
| Input | `sel` | Selector input deciding which signal is passed through | integer, boolean, or model-dependent |
| Output | `yo` | Selected output signal | model-dependent |

## How to use it

- Use this block when one control chain must choose between several source signals.
