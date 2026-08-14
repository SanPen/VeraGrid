# Gradient limiter (constant)

Gradient limiter (constant) restricts how fast the output is allowed to rise or fall. Use it to prevent sudden ramps from propagating downstream.

$$
gradmin \le \frac{d yo}{dt} \le gradmax
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Requested signal | model-dependent |
| Output | `yo` | Rate-limited output | model-dependent |
| Parameter | `gradmax` | Maximum upward gradient | output units/s |
| Parameter | `gradmin` | Maximum downward gradient | output units/s |
