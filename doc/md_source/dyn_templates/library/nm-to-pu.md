# Nm -> p.u.

Nm -> p.u. converts torque in newton-meters to per-unit torque using the configured base values. Use it when mechanical torque must be normalized for control blocks.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `M` | Torque input | Nm |
| Output | `m` | Torque in per unit | p.u. |
| Parameter | `freqbase` | Base frequency used by the conversion | Hz |
| Parameter | `Zp` | Pole-pair or pole-count-related parameter | model-dependent |
| Parameter | `Pel_base` | Electrical power base | W or model-dependent |
