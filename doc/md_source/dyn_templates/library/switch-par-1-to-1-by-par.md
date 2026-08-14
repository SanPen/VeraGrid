# Switch par 1->1 by par

This switch passes one input through under parameter-controlled switching logic. Use it when switching behavior is configured entirely from block parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Switched output | model-dependent |
| Parameter | `Enable` | Enable setting for the switch | boolean, 0/1, or model-dependent |
| Parameter | `p` | Associated configured value used by the block | model-dependent |
