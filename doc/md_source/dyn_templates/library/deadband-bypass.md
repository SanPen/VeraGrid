# Deadband (bypass)

Deadband (bypass) ignores small input variations but passes the original signal through once the deadband is exceeded. Use it when you want quiet behavior near zero without offsetting the active signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Bypassed-or-suppressed output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
