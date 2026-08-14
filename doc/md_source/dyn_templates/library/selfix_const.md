# Selfix const

### Purpose

This block keeps or fixes one selected signal path according to one constant selector parameter.

### Behavior

- Receives candidate signals.
- Uses one fixed selection parameter.
- Outputs the selected path.

### Characteristics

- Useful for fixed routing choices in reusable templates.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `s1` | First candidate signal | model-dependent |
| Input | `s2` | Second candidate signal | model-dependent |
| Output | `yo` | Selected output signal | model-dependent |
| Parameter | `sel` | Fixed selector parameter | integer or boolean |

## How to use it

- Use this block when the signal route should remain fixed for one template instance.
