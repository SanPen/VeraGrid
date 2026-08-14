# Switch par 1->2 by sig

This switch routes one configured parameter value to one of two outputs using a runtime selector signal. Use it when a live signal decides where a configured quantity goes.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo1` | First switched output | model-dependent |
| Output | `yo2` | Second switched output | model-dependent |
| Parameter | `K` | Configured value being routed | model-dependent |
