# Selector

Selector outputs `y_true` when the condition is active and `y_false` otherwise. Use it for simple runtime branching between two signal paths.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Input | `y_true` | Output value used when the condition is true | model-dependent |
| Input | `y_false` | Output value used when the condition is false | model-dependent |
| Output | `yo` | Selected output | model-dependent |
