# Switch sig 1->1 by sig

This switch passes one signal through under runtime signal-based switching logic. Use it when a live enable signal controls whether the path is active.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Input | `Enable` | Runtime enable signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Switched output | model-dependent |
| Parameter | `p` | Configured value used by the switch logic | model-dependent |
