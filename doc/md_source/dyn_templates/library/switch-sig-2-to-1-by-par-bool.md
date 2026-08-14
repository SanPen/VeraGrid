# Switch sig 2->1 by par (bool)

This switch chooses between two input signals using a boolean parameter. Use it when the branch should be fixed when the block is configured.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `sw` | Boolean selector | boolean or 0/1 |
