# Switch sig 2->1 by par

This switch chooses between two input signals using a parameterized selector. Use it when the branch choice is set by configuration rather than by a runtime signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `sw` | Selector deciding which input is passed through | boolean, 0/1, or model-dependent |
