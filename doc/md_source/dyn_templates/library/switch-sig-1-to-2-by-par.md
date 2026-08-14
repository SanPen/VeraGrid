# Switch sig 1->2 by par

This switch sends one input signal to one of two outputs using a parameterized selector. Use it when the output branch is chosen during block configuration.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal to route | model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `sw` | Selector for the destination | boolean, 0/1, or model-dependent |
