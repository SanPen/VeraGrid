# Selector (constant)

Selector (constant) outputs one of two configured constants based on a runtime condition. Use it when the logic is dynamic but the two candidate outputs are fixed numbers.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Runtime condition that chooses the branch | boolean, 0/1, or model-dependent |
| Output | `yo` | Selected constant output | model-dependent |
| Parameter | `K_true` | Constant used when the condition is true | model-dependent |
| Parameter | `K_false` | Constant used when the condition is false | model-dependent |
