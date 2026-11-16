## ControllableShunt

A `ControllableShunt` provides reactive support with continuous, discrete, locked or Q-V droop control.

### Q-V droop control

With `Qdroop` in MVAr per pu, the shunt requests `Q = Qdroop * (Vset - abs(Vcontrol))`
and limits its susceptance to `[Bmin, Bmax]`, in MVAr at 1 pu. Positive-sequence power
flow can use a remote control bus. Three-phase power flow uses the local `abs(U1)`.

Existing native models with `Qdroop = 0` and a rated `Snom` retain their original curve
`Q = Snom * (Vset - abs(U1)) / (droop/100)`. The measured magnitude is clamped
between `Vmin` and `Vmax`, and Q follows the original curve without a B limit.
This legacy configuration requires a positive rating and droop percentage and a local ABC AC bus.

In ABC, Q is the total three-phase reactive injection. For Y/D,
`Bpu = (Q/Sbase) / (abs(U1)^2 + abs(U2)^2)` and `Iabc = -j*Bpu*(Uabc-U0)`.
For Yg, include `abs(U0)^2` in the denominator and use `Uabc` directly.
Thus delta blocks I0 while retaining I2, and total Q still follows the same droop law.
In balance this reduces to the positive-sequence equivalent. Legacy models retain
fixed G in the network admittance. Fixed B and step data are excluded from the droop
susceptance. No additional Newton unknowns are required.

The settings survive native save/load and island slicing. This implementation covers
power flow, not OPF/dynamics or reverse DGS export of droop settings.

### Continuous voltage control in ABC power flow

Continuous control automatically regulates the local positive-sequence voltage magnitude,
`abs(U1) = Vset`, where `U1 = (Ua + a*Ub + a^2*Uc)/3` and `a = exp(j*2*pi/3)`.
It adjusts one common susceptance for the three phases. Phase voltage magnitudes may
differ under imbalance; there is no option to constrain them independently.

The device retains its physical shunt response: current is proportional to voltage,
including its negative-sequence component. **Yg** also carries zero-sequence current;
**Y** and **D** block terminal I0. No extra earth connection or U0 constraint is added.
For Y/D, the current depends on `Uabc - U0`; for Yg it depends on `Uabc`.
All three phases and local voltage control are required. Explicit-neutral and remote
continuous ABC regulation currently produce a diagnostic instead of changing the connection.

The existing `Bmin`/`Bmax` convention is retained: the injected nominal susceptance lies
between `-Bmax` and `-Bmin`, in MVAr at 1 pu. With reactive-limit enforcement enabled,
reaching a bound releases voltage regulation and holds susceptance constant. Terminal
reactive power therefore varies with voltage squared; it is not clamped as a constant Q.
Total conductance `G` remains a fixed balanced admittance. The initial `B` is replaced
by the solved susceptance, so it is not counted twice. At an ideal slack bus, the shunt
keeps its fixed `G + j*B` and does not add another voltage constraint.

`Vset` and `active` profiles are respected. With `use_kw`, conductance and nominal
susceptance inputs are converted from kW/kVAr to MW/MVAr. Independent phase inputs
do not define separate controls in continuous mode.

Colocated U1 generators and continuous shunts share one voltage constraint and must
use the same setpoint. Their existing capability ranges determine participation:
the common control variable moves each device through the same fraction of its range.
Generator limits apply to terminal Q; shunt limits apply to nominal susceptance.
The implementation reuses the existing U1 residual and limit enforcement, without
changes to numerical solvers or Jacobian routines.

Discrete and locked control retain their existing behaviour. Positive-sequence power
flow retains its existing formulation. This extension does not add short-circuit or
dynamic control equations.

### PowerFactory import

Without explicit VSC import, an `ElmSvs` in voltage control is represented
by a `ControllableShunt`. Its susceptances connect AB/BC/CA, so import uses
**D**. ABC regulation uses U1 and a common susceptance, as for PowerFactory's balanced
SVS control with positive-sequence voltage selected.

For continuous voltage control without droop, when bank data are available the importer
reuses the existing VSC-route range:
`Bmin = qmin*nxcap + Qfixcap*nfixcap` and `Bmax = tcrmax + Qfixcap*nfixcap`.
Here, native `qmin` describes one capacitor step, not the whole bank. Legacy exports
without bank data retain the earlier `qmin/qmax` fallback. Reimport the DGS to update
previously imported connections and bank limits.

With droop enabled the importer sets `Qdroop = 100 * Srated / ddroop`, maps the
capacitor and reactor limits to `Bmin` and `Bmax`, and uses the configured control
bus and voltage target. The separate [StaticGenerator Q-V droop](static_generator.md)
uses its own current-source model. Reimport DGS to apply this mapping to existing SVCs.
