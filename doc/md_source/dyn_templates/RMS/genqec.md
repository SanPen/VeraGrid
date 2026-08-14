# GENQEC

This model represents the `GENQEC` synchronous machine block used within the RMS complete generator model.

### Purpose

`GENQEC` is the internal synchronous-machine RMS model with electromechanical dynamics, transient emf states, dq electrical equations, and quadratic magnetic saturation.

### Behavior

- Receives terminal voltage magnitude and angle from the network-facing wrapper.
- Receives mechanical torque from the governor and field voltage from the exciter.
- Produces electrical active and reactive power, electromagnetic torque, machine speed, and exciter feedback signals.
- Couples rotor swing dynamics, dq electrical equations, and saturation behavior.

### Characteristics

- Positive-sequence RMS synchronous-machine model.
- Includes rotor angle and speed dynamics.
- Includes transient internal emf states.
- Includes quadratic saturation through the air-gap flux channel.
## Characteristic equations

$$
\frac{d\delta}{dt} = (\omega - 1) w_s
$$

$$
\frac{d\omega}{dt} = \frac{T_m - T_e - D(\omega - 1)}{M}
$$

$$
\frac{dE_q'}{dt} = \frac{V_f - \mathrm{Sat}\,E_{q1}}{T_{d0}'}
$$

$$
\frac{dE_d'}{dt} = -\frac{\mathrm{Sat}\,E_{d1}}{T_{q0}'}
$$

$$
P_g = V_d I_d + V_q I_q
$$

$$
Q_g = V_q I_d - V_d I_q
$$

$$
T_e = \Psi_d I_q - \Psi_q I_d
$$

$$
S_a = \frac{A}{2}\left((\Psi_{ag} - B) + \sqrt{(\Psi_{ag} - B)^2 + \varepsilon}\right)^2
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the generator bus | pu |
| Input | `Va` | Terminal voltage angle at the generator bus | rad |
| Input | `Tm` | Mechanical torque signal received from the governor block | pu |
| Input | `Vf` | Field-voltage signal received from the exciter block | pu |
| Output | `Pg` | Generator active power injection computed by the machine model | pu |
| Output | `Qg` | Generator reactive power injection computed by the machine model | pu |
| Output | `omega` | Rotor speed output shared with the stabilizer and governor | pu |
| Output | `IRPu` | Exciter feedback quantity exported to the exciter block | pu |
| Output | `Te` | Electromagnetic torque exported to the governor/composite model | pu |
| Variable | `delta` | Rotor electrical angle state | rad |
| Variable | `omega` | Rotor electrical speed state | pu |
| Variable | `Eq_prime` | q-axis transient internal emf state | pu |
| Variable | `Ed_prime` | d-axis transient internal emf state | pu |
| Variable | `Psid_prime` | d-axis transient flux-related state | pu |
| Variable | `Psiq_prime` | q-axis transient flux-related state | pu |
| Variable | `Pg` | Algebraic active-power variable | pu |
| Variable | `Qg` | Algebraic reactive-power variable | pu |
| Variable | `Id` | d-axis stator current | pu |
| Variable | `Iq` | q-axis stator current | pu |
| Variable | `Vd` | d-axis terminal voltage | pu |
| Variable | `Vq` | q-axis terminal voltage | pu |
| Variable | `Psid` | d-axis flux linkage quantity | pu |
| Variable | `Psiq` | q-axis flux linkage quantity | pu |
| Variable | `Te` | Electromagnetic torque variable | pu |
| Variable | `IRPu` | Exciter feedback quantity derived from the internal emf channel | pu |
| Variable | `Xd_2prime_sat` | Saturated subtransient d-axis reactance | pu |
| Variable | `Xq_2prime_sat` | Saturated subtransient q-axis reactance | pu |
| Variable | `Sa` | Saturation increment | pu |
| Variable | `Sat` | Total saturation multiplier | pu |
| Variable | `V_qag` | q-axis air-gap voltage-related quantity | pu |
| Variable | `V_dag` | d-axis air-gap voltage-related quantity | pu |
| Variable | `Psi_ag` | Air-gap flux magnitude used by the saturation law | pu |
| Parameter | `fn` | Nominal electrical frequency | Hz |
| Parameter | `ws` | Synchronous electrical angular speed | rad/s |
| Parameter | `M` | Inertia constant used in the swing equation | pu-based model constant |
| Parameter | `D` | Damping coefficient used in the swing equation | pu-based model constant |
| Parameter | `Rs` | Stator resistance parameter | pu |
| Parameter | `Ra` | Armature resistance parameter used in the dq algebraic equations | pu |
| Parameter | `Xd` | d-axis synchronous reactance | pu |
| Parameter | `Xq` | q-axis synchronous reactance | pu |
| Parameter | `Xd_prime` | d-axis transient reactance | pu |
| Parameter | `Xq_prime` | q-axis transient reactance | pu |
| Parameter | `Xd_2prime` | d-axis subtransient reactance | pu |
| Parameter | `Xq_2prime` | q-axis subtransient reactance | pu |
| Parameter | `Xl` | Leakage reactance | pu |
| Parameter | `Td0_prime` | d-axis open-circuit transient time constant | s |
| Parameter | `Tq0_prime` | q-axis open-circuit transient time constant | s |
| Parameter | `Td0_2prime` | d-axis open-circuit subtransient time constant | s |
| Parameter | `Tq0_2prime` | q-axis open-circuit subtransient time constant | s |
| Parameter | `A` | Quadratic saturation gain parameter | pu |
| Parameter | `B` | Saturation knee-shift parameter | pu |

## How to use it

- Treat `GENQEC` as the machine core of the RMS `Complete generator` package.
- Use the higher-level `Complete generator` template when you want the machine already wired to governor, exciter, and stabilizer blocks.
