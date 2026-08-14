# Analog flip-flop

Analog flip-flop stores a logical output state, driven by an analog trigger input together with explicit set and reset signals.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Analog trigger input | model-dependent |
| Input | `set` | Set command | boolean or logical flag |
| Input | `rst` | Reset command | boolean or logical flag |
| Output | `yo` | Latched output state | model-dependent |
