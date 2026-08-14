# Switch par 2->1 by par

This switch chooses between two configured parameter values and sends the result to one output. Use it when the chosen constant should be selected at configuration time.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `sw` | Selector choosing between the configured values | boolean, 0/1, or model-dependent |
| Parameter | `K1` | First configured candidate value | model-dependent |
| Parameter | `K2` | Second configured candidate value | model-dependent |
