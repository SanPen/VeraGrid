# Switch sig 2->1 (NOT EQ K) by s/p

This switch chooses between two input signals based on whether the selector signal differs from a configured value `K`. Use it when the branch condition is an explicit not-equal comparison.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Input | `sw` | Runtime selector signal | model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `K` | Comparison value used by the switch | model-dependent |
