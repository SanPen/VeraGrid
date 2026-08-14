# Deadband (parameter)

Deadband (parameter) suppresses small excursions around the center region using configured bounds. Use it to ignore small errors without needing runtime limit signals.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after deadband processing | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
| Parameter | `y_max` | Upper output or active-region bound | same as `yi` |
| Parameter | `y_min` | Lower output or active-region bound | same as `yi` |
