# Switch sw equal C 2s->1s

This switch compares the selector signal to `C` and chooses between two input signals based on equality. Use it when the branch condition is `sw == C`.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First candidate input | model-dependent |
| Input | `sw` | Selector signal being compared | model-dependent |
| Input | `yi2` | Second candidate input | model-dependent |
| Output | `yo` | Selected output | model-dependent |
| Parameter | `C` | Comparison value | model-dependent |
