# Switch sig 1->2 by par (bool)

This switch sends one input signal to one of two outputs using a boolean parameter. Use it when the routing choice is fixed by configuration.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal to route | model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `sw` | Boolean selector for the destination | boolean or 0/1 |
