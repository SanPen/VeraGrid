# Switch sig 4->1 by sig

This switch chooses one of four input signals using a runtime selector signal. Use it when supervisory logic must route one of four live sources.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `yi3` | Third candidate input | model-dependent |
| Input | `yi4` | Fourth candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | model-dependent |
| Output | `yo` | Selected output | model-dependent |
