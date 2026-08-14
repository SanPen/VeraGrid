# Backlash

Backlash models a mechanical-style play zone where small reversals do not immediately change the output. Use it when gear slack or hysteretic motion should be represented.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after backlash behavior | same as `yi` |
| State | `Backlash__x` | Internal stored position for the backlash element | same as `yi` |
| Parameter | `db` | Backlash width | same as `yi` |
