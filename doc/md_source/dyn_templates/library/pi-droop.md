# PI droop

PI droop generates an output from a condition signal with pick-up and drop-out timing supplied as inputs.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `condition` | Activation condition | boolean or logical flag |
| Input | `Tpick` | Pick-up delay input | s |
| Input | `Tdrop` | Drop-out delay input | s |
| Output | `yo` | Droop controller output | model-dependent |
