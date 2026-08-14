# Deadband offset (bypass)

Deadband offset (bypass) holds a dead zone around the center and then passes the signal with offset-style behavior once active. Use it when you need both suppression near zero and continuity outside it.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Offset deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
