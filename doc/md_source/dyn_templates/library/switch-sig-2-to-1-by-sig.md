# Switch sig 2->1 by sig

This switch chooses between two input signals using a runtime selector signal. Use it for standard live 2-to-1 switching.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected output | model-dependent |
