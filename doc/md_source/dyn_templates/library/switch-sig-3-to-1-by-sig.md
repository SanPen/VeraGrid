# Switch sig 3->1 by sig

This switch chooses one of three input signals using a runtime selector signal. Use it when one signal path must be selected from three live candidates.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `yi3` | Third candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | model-dependent |
| Output | `yo` | Selected output | model-dependent |
