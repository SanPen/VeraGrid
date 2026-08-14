# Switch sig 2->1 by sig (fixed)

This switch chooses between two input signals using a runtime selector, with fixed behavior baked into the template. Use it when you need the shipped fixed form of the 2-to-1 signal switch.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected output | model-dependent |
