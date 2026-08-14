# Switch par 2->1 by sig

This switch chooses between two configured parameter values using a runtime selector signal. Use it when a live condition should choose which constant reaches the output.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `K1` | First configured candidate value | model-dependent |
| Parameter | `K2` | Second configured candidate value | model-dependent |
