# DC load

This model represents a DC load for EMT studies.

### Purpose

It is a DC EMT load model composed of a constant-power term and a conductance term.

### Behavior

- Uses DC bus voltage as its only external input.
- Computes DC current and DC power.
- Follows the EMT convention where current and power are positive when entering the bus.
- A consuming DC load therefore produces negative DC current and negative DC power in this sign convention.

### Characteristics

- Algebraic DC EMT load model.
- Suitable for DC-side network studies.
- Very simple and computationally light.
## Characteristic equations

$$
i_{dc} + \frac{P_{dc,static}}{v_{dc} + \varepsilon} + g_{dc,static} v_{dc} = 0
$$

$$
p_{dc} = v_{dc} i_{dc}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_dc` | DC bus voltage at the load connection point | pu |
| Output | `i_dc` | DC current entering the bus from the load model sign convention | pu |
| Variable | `i_dc` | Algebraic DC current variable | pu |
| Variable | `p_dc` | Algebraic DC power variable | pu |
| Parameter | `Pl0` | Constant-power load term used by the DC load equation | pu |
| Parameter | `g` | Conductance term of the DC load | pu |

## How to use it

- Use this template when you need a simple DC load in EMT studies.
- If the DC load must have switching, converter control, or dynamic energy-storage behavior, use a more detailed model instead.
