# Switch par 1->2 by par

This switch routes one configured parameter value to one of two outputs using a parameterized selector. Use it when the split destination is fixed by block setup.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `sw` | Selector choosing which output receives the active value | boolean, 0/1, or model-dependent |
| Parameter | `K` | Configured value being routed | model-dependent |
