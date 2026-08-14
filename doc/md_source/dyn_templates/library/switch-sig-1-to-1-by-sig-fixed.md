# Switch sig 1->1 by sig (fixed)

This switch passes one signal through under a runtime enable input and a configured fixed setting. Use it when you need to gate a signal path with one live signal and one stored configuration value.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Input | `Enable` | Runtime enable signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Switched output | model-dependent |
| Parameter | `p` | Configured value used by the switch logic | model-dependent |
