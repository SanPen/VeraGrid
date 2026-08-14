# Deadband

Deadband suppresses small input changes around the center region. Use it to prevent noise or tiny errors from triggering downstream action.

$$
yo = 0 \quad \text{inside the deadband region}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Output after deadband processing | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
