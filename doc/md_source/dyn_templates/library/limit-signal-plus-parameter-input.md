# Limit (signal + parameter input)

This Limit variant combines runtime limit inputs with stored fallback bounds. Use it when the active limit signals may vary but parameter values still define the configured range.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Input | `yi_max` | Runtime upper-bound input | same as `yi` |
| Input | `yi_min` | Runtime lower-bound input | same as `yi` |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_max` | Configured upper limit | same as `yi` |
| Parameter | `y_min` | Configured lower limit | same as `yi` |
