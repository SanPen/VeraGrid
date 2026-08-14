# Set if condition (constant)

Set if condition (constant) chooses between two configured constants using a runtime condition. Use it when the decision changes at runtime but the candidate outputs are fixed.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected constant output | model-dependent |
| Parameter | `K_true` | Constant used when the condition is true | model-dependent |
| Parameter | `K_false` | Constant used when the condition is false | model-dependent |
