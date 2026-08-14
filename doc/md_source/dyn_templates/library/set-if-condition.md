# Set if condition

Set if condition selects between two input values using a runtime condition. Use it when you want explicit conditional assignment behavior in the signal path.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Input | `y_true` | Value used when the condition is true | model-dependent |
| Input | `y_false` | Value used when the condition is false | model-dependent |
| Output | `yo` | Selected output | model-dependent |
