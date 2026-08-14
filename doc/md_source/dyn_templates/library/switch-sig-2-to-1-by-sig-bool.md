# Switch sig 2->1 by sig (bool)

This switch chooses between two input signals using a boolean runtime selector. Use it when the branch should react directly to a live logical signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Boolean runtime selector | boolean or 0/1 |
| Output | `yo` | Selected output | model-dependent |
