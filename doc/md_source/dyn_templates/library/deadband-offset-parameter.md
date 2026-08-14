# Deadband offset (parameter)

Deadband offset (parameter) suppresses a central region and then resumes with an offset-style output using configured bounds. Use it when the output should not jump directly back to the raw input outside the deadband.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Offset deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
| Parameter | `y_max` | Upper output or active-region bound | same as `yi` |
| Parameter | `y_min` | Lower output or active-region bound | same as `yi` |
