# PI droop (constant)

`PI droop (constant)` provides the same timed droop behavior as `PI droop`, but uses fixed pick-up and drop-out parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Activation condition | boolean or logical flag |
| Output | `yo` | Droop controller output | model-dependent |
| Parameter | `Tpick` | Pick-up delay | s |
| Parameter | `Tdrop` | Drop-out delay | s |
