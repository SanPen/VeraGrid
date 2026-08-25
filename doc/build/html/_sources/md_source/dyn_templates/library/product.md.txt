# Product

<!-- veragrid-block-introduction:start -->
**Product** is a mathematical signal-processing primitive. It forms an algebraic relation between inputs, parameters, and outputs and is commonly combined with dynamic and nonlinear blocks to construct larger control equations without introducing an independent physical state.

## Typical use

- Use it to express the exact algebraic operation required by a controller or measurement chain.
- Check signal dimensions, signs, and zero-division or domain restrictions where applicable.
<!-- veragrid-block-introduction:end -->

The Product block multiplies numerator inputs and divides by denominator
inputs. General options controls how many ports participate in each group.

## Characteristic equation

$$
y = \frac{\prod_i u_i}{\prod_j v_j}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `mul_i` | Numerator factors | model-dependent |
| Input | `div_j` | Denominator factors | model-dependent |
| Output | `y` | Algebraic product or ratio | derived from inputs |

The model author must ensure that denominator signals do not reach zero.
