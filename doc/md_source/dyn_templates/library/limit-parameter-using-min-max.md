# Limit (parameter) (using min/max)

This Limit variant uses a single parameter carrying the limit range. Use it when your model stores the allowed minimum and maximum together.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `y_lim` | Stored min/max limit definition | same as `yi` |
