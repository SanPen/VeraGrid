# J. Martí frequency-dependent EMT line

<!-- veragrid-block-introduction:start -->
**J. Martí frequency-dependent EMT line** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

The J. Martí line is a travelling-wave transmission-line model with
frequency-dependent modal propagation and characteristic admittance. It fits
rational functions to sampled line data and uses those fitted poles and
residues during the EMT simulation.

## Model workflow

1. Obtain frequency samples automatically from the line and its assigned tower
   or underground-cable template, or import compatible samples from an NPZ
   file.
2. Transform the phase-domain samples to modal coordinates.
3. Fit the characteristic admittance and propagation terms with vector fitting.
4. Apply optional passivity checks and correction settings.
5. Store the resulting runtime bundle on the symbolic line block.

## Characteristic relations

In the frequency domain, terminal currents are related to terminal voltages by
the fitted characteristic admittance `Y_c(s)` and propagation operator `H(s)`:

$$
I_f(s) = Y_c(s)V_f(s) - H(s)I_t(s)
$$

$$
I_t(s) = Y_c(s)V_t(s) - H(s)I_f(s)
$$

## Special settings

The Special settings tab contains the complete former creation-dialogue
configuration: phases, sample source, nominal and sweep frequencies, imported
sample path, vector-fitting orders and tolerances, iteration limits, weighting,
stability enforcement, delay handling, and passivity tolerances. Applying the
dialogue reconstructs the model from these values.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `vf_X` | From-terminal phase voltage | V or p.u. |
| Input | `vt_X` | To-terminal phase voltage | V or p.u. |
| Output | `net_conn_if_X` | From-terminal network current | A or p.u. |
| Output | `net_conn_it_X` | To-terminal network current | A or p.u. |

The default topology is ABC without neutral. Enable neutral only when the
connected network and line data both provide a neutral conductor.
