# Deadband stepped (parameter)

Deadband stepped (parameter) uses configured bounds and resumes with step-like behavior outside the dead region. Use it when the output should change in a more quantized way at the threshold.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Stepped deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
| Parameter | `y_max` | Upper output or active-region bound | same as `yi` |
| Parameter | `y_min` | Lower output or active-region bound | same as `yi` |
