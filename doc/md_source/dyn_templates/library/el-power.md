# El. Power

El. Power converts generator-side quantities into an electrical power output using the configured base information. Use it when the model needs a direct electrical power signal from `pgt` and `cosn`.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `pgt` | Input power-related quantity | model-dependent |
| Input | `cosn` | Power-factor-related input | model-dependent |
| Output | `pelec` | Electrical power output | power |
| Parameter | `IPB` | Configured base or scaling value | model-dependent |
