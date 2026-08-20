# Distributed PV

<!-- veragrid-block-introduction:start -->
**Distributed PV** represents an energy resource and its interface controls. Storage and photovoltaic models combine source-side energy or power limits with converter commands, so available active power, DC voltage, and reactive-power control must remain mutually consistent.

## Typical use

- Use it to study renewable or storage response to voltage, frequency, and power-reference disturbances.
- Respect energy, current, DC-voltage, and active/reactive capability limits during initialization.
<!-- veragrid-block-introduction:end -->

This model represents a positive-sequence RMS distributed PV inverter with outer-loop control and current injection behavior.

### Purpose

It is a PVD1-inspired RMS distributed PV model with irradiance-dependent active-power availability, MPPT lag, voltage-reactive droop behavior, current limiting, and voltage/frequency trip windows.

### Behavior

- Uses bus voltage magnitude and angle as network inputs.
- Computes available active power from irradiance and cell temperature.
- Filters the MPPT active-power ceiling dynamically.
- Applies reactive droop behavior based on terminal voltage.
- Limits current according to converter capability and P/Q priority.
- Can reduce or block output through voltage and frequency trip logic.

### Characteristics

- Averaged RMS inverter-based resource model.
- Suitable for feeder-scale and plant-scale distributed PV dynamic studies.
- Represents availability and tripping behavior, not waveform-level converter detail.
## Characteristic equations

$$
P_{avail} = \mathrm{sat}\left(P_{rated}\frac{G}{G_{ref}}\left(1 + k_T(T_{cell}-T_{ref})\right), 0, P_{rated}\right)
$$

$$
\frac{dP_{mppt}}{dt} = \frac{P_{avail} - P_{mppt}}{T_{mppt}}
$$

$$
P = V_m I_{p,out}
$$

$$
Q = V_m I_{q,out}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the PV point of connection | pu |
| Input | `Va` | Terminal voltage angle at the PV point of connection | rad |
| Output | `P_pvd1` | Active power injected by the PV model | pu |
| Output | `Q_pvd1` | Reactive power injected by the PV model | pu |
| Variable | `Ipout_y` | Filtered active-current output state | pu |
| Variable | `Iqout_y` | Filtered reactive-current output state | pu |
| Variable | `Pmppt` | Dynamic MPPT-tracked active-power ceiling | pu |
| Variable | `Ip_cmd` | Active-current command before output lag | pu |
| Variable | `Iq_cmd` | Reactive-current command before output lag | pu |
| Variable | `Ip_max` | Active-current limit after applying current-priority logic | pu |
| Variable | `Iq_max` | Reactive-current limit after applying current-priority logic | pu |
| Variable | `P_sum` | Net active-power command after summation and limiting | pu |
| Variable | `Q_sum` | Net reactive-power command after summation and limiting | pu |
| Variable | `Q_droop` | Reactive-power contribution produced by the voltage droop logic | pu |
| Variable | `F_trip` | Frequency-trip multiplier | pu |
| Variable | `V_trip` | Voltage-trip multiplier | pu |
| Variable | `Pavail` | Available active power before MPPT lag dynamics are applied | pu |
| Parameter | `pref0` | Base active-power reference | pu |
| Parameter | `qref0` | Base reactive-power reference | pu |
| Parameter | `pext0` | External active-power offset reference | pu |
| Parameter | `qmx` | Upper reactive-power limit | pu |
| Parameter | `qmn` | Lower reactive-power limit | pu |
| Parameter | `v0` | Lower voltage breakpoint used by the droop logic | pu |
| Parameter | `v1` | Upper voltage breakpoint used by the droop logic | pu |
| Parameter | `dqdv` | Reactive-power droop slope versus voltage deviation | pu/pu |
| Parameter | `ialim` | Total current limit of the inverter model | pu |
| Parameter | `pqflag` | Priority selector between active-current and reactive-current limitation | 0/1 |
| Parameter | `tip` | Active-current output lag time constant | s |
| Parameter | `tiq` | Reactive-current output lag time constant | s |
| Parameter | `recflag` | Recovery/trip logic selector | 0/1 |
| Parameter | `ft0` | Lower frequency-trip breakpoint | Hz |
| Parameter | `ft1` | Lower frequency-recovery breakpoint | Hz |
| Parameter | `ft2` | Upper frequency-recovery breakpoint | Hz |
| Parameter | `ft3` | Upper frequency-trip breakpoint | Hz |
| Parameter | `vt0` | Lower voltage-trip breakpoint | pu |
| Parameter | `vt1` | Lower voltage-recovery breakpoint | pu |
| Parameter | `vt2` | Upper voltage-recovery breakpoint | pu |
| Parameter | `vt3` | Upper voltage-trip breakpoint | pu |
| Parameter | `Prated` | Rated active power of the PV resource | pu |
| Parameter | `G` | Irradiance input used by the availability law | pu on irradiance base |
| Parameter | `Gref` | Reference irradiance used by the availability law | pu on irradiance base |
| Parameter | `Tcell` | Cell temperature input | degC |
| Parameter | `Tref` | Reference cell temperature | degC |
| Parameter | `kT` | Temperature coefficient used in the active-power availability law | 1/degC |
| Parameter | `Tmppt` | MPPT lag time constant | s |

## How to use it

- Use it for RMS studies of distributed PV behavior under changing voltage, frequency, and available solar resource.
- Do not use it as a switching converter or waveform-level PV model.
