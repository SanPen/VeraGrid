# Deadband discontinuous

Deadband discontinuous creates a hard transition at the deadband edge. Use it when you need explicit on/off style deadband behavior instead of a smooth re-entry.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after discontinuous deadband processing | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
