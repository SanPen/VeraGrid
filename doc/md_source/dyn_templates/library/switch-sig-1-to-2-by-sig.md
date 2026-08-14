# Switch sig 1->2 by sig

This switch sends one input signal to one of two outputs using a runtime selector signal. Use it when the destination branch must change during simulation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal to route | model-dependent |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
