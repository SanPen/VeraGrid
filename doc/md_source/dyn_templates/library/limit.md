# Limit

Limit clips an input to a configured upper range with a small tolerance parameter. Use it when you need a simple saturating ceiling behavior from a single input.

$$
yo \le y_{max}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance used around the limit | same as `yi` |
| Parameter | `y_max` | Upper limit | same as `yi` |
