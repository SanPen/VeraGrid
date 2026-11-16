# Colib model coverage in VeraGrid templates

## Purpose

This is a source-inventory report for offering VeraGrid implementations to the
Collaborative Open-Source Dynamic Simulation Library (Colib), and for choosing
the next models to implement in VeraGrid.

It compares `src/VeraGridEngine/Templates` with the `models/` tree in
[`CRESYM/Colib_Quarto.github.io`](https://github.com/CRESYM/Colib_Quarto.github.io),
at commit [`16d6171`](https://github.com/CRESYM/Colib_Quarto.github.io/tree/16d6171513fd1adf900d51a0ec664888d66b274a).
The VeraGrid source tree was re-inspected on 2026-11-10 after the RMS template
layout was reorganized.

## Model index

This is the report's decision table. **Exact** is a source-level identifier
match, not a validation claim. **Candidate** needs the comparison stated in
the detailed review below. **Absent** means no dedicated template was found.

| Colib model | Colib repository path | VeraGrid equivalent or candidate | Status |
| --- | --- | --- | --- |
| GENQEC | `models/1-SynchronousMachines/Generator/GENQEC/index.qmd` | `Rms/synchronous_machines/genqec_phasor_rms_template.py` | Exact identifier |
| GENROU/GENSAL | `models/1-SynchronousMachines/Generator/GENSAL/index.qmd` | `synchronous_machines/genrou.py`, `gensal.py` | Exact identifiers |
| GENTPF | `models/1-SynchronousMachines/Generator/GENTPJ/index.qmd` | `synchronous_machines/gentpf.py` | Implemented; GENTPJ family with `K_is = 0` |
| GENTPJ | `models/1-SynchronousMachines/Generator/GENTPJ/index.qmd` | `synchronous_machines/gentpj.py` | Implemented; stator-current saturation gain included |
| SM1 | `models/1-SynchronousMachines/Generator/SM1/index.qmd` | `Emt/synchronous_machines/sm1_emt_template.py` | Implemented EMT physical-winding superset; parameter mapping pending |
| AC1C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/AC1C/index.qmd` | `excitation_systems/ac1c.py` | Exact identifier |
| AC6C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/AC6C/index.qmd` | `excitation_systems/ac6c.py` | Exact identifier |
| AC7C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/AC7C/index.qmd` | `excitation_systems/ac7c.py` | Exact identifier |
| AC8C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/AC8C/index.qmd` | `excitation_systems/ac8c.py` | Exact identifier |
| AcRotatingExciter | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/AcRotatingExciter/index.qmd` | `Rms/excitation_systems/ac_rotating_exciter.py` | Implemented; exponential saturation and dynamic upper limit |
| BBSEX1 | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/BBSEX1/index.qmd` | `excitation_systems/bbsex1.py` | Exact identifier |
| DC1C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/DC1C/index.qmd` | `excitation_systems/dc1c.py` | Exact identifier |
| IEEEX2 | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/IEEEX2/index.qmd` | `excitation_systems/ieeex2.py` | Exact identifier |
| IEEX2A | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/IEEX2A/index.qmd` | `excitation_systems/ieex2a.py` | Exact identifier |
| SCRX | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/SCRX/index.qmd` | `excitation_systems/scrx.py` | Exact identifier |
| ST1C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST1C/index.qmd` | `excitation_systems/st1c.py` | Exact identifier |
| ST4C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST4C/index.qmd` | `excitation_systems/st4c.py` | Exact identifier |
| ST5C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST5C/index.qmd` | `excitation_systems/st5c.py` | Exact identifier |
| ST6C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST6C/index.qmd` | `excitation_systems/st6c.py` | Exact identifier |
| ST7C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST7C/index.qmd` | `excitation_systems/st7c.py` | Exact identifier |
| ST9C | `models/1-SynchronousMachines/ExciterAndVoltageRegulator/ST9C/index.qmd` | `excitation_systems/st9c.py` | Exact identifier |
| GAST | `models/1-SynchronousMachines/Governor/GAST/index.qmd` | `governors/gast.py` | Exact identifier |
| GovCT2/GGOV2 | `models/1-SynchronousMachines/Governor/GovCT2/index.qmd` | `governors/gov_c_t2.py` | Exact identifier |
| GovHydro4 | `models/1-SynchronousMachines/Governor/GovHydro4/index.qmd` | `governors/govhydro4.py` | Exact identifier |
| GovSteamEU | `models/1-SynchronousMachines/Governor/GovSteamEU/index.qmd` | `governors/govsteameu.py` | Exact identifier |
| HYGOV | `models/1-SynchronousMachines/Governor/HYGOV/index.qmd` | `governors/hygov.py` | Exact identifier |
| IEEEG1/GovSteam1 | `models/1-SynchronousMachines/Governor/IEEEG1/index.qmd` | `governors/ieeeg1.py` | Exact identifier |
| IEEEG2/GovSteam2 | `models/1-SynchronousMachines/Governor/IEEEG2/index.qmd` | `governors/ieeeg2.py` | Exact identifier |
| TGOV1 | `models/1-SynchronousMachines/Governor/TGOV1/index.qmd` | `governors/tgov1.py` | Exact identifier |
| TGOV3 | `models/1-SynchronousMachines/Governor/TGOV3/index.qmd` | `governors/tgov3.py` | Exact identifier |
| OEL2C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/OEL2C/index.qmd` | `excitation_limiters/oel2c.py` | Exact identifier |
| OEL3C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/OEL3C/index.qmd` | `excitation_limiters/oel3c.py` | Exact identifier |
| OEL4C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/OEL4C/index.qmd` | `excitation_limiters/oel4c.py` | Exact identifier |
| OEL5C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/OEL5C/index.qmd` | `excitation_limiters/oel5c.py` | Exact identifier |
| SCL1C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/SCL1C/index.qmd` | `excitation_limiters/scl1c.py` | Exact identifier |
| SCL2C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/SCL2C/index.qmd` | `excitation_limiters/scl2c.py` | Exact identifier |
| UEL1 | `models/1-SynchronousMachines/OverUnderExcitationLimiter/UEL1/index.qmd` | `excitation_limiters/uel1.py` | Exact identifier |
| UEL2C | `models/1-SynchronousMachines/OverUnderExcitationLimiter/UEL2C/index.qmd` | `excitation_limiters/uel2c.py` | Exact identifier |
| PSS1A | `models/1-SynchronousMachines/PowerSystemStabilizer/PSS1A/index.qmd` | `power_system_stabilizers/pss1a.py` | Exact identifier |
| PSS2C | `models/1-SynchronousMachines/PowerSystemStabilizer/PSS2C/index.qmd` | `power_system_stabilizers/pss2c.py` | Exact identifier |
| PSS3C | `models/1-SynchronousMachines/PowerSystemStabilizer/PSS3C/index.qmd` | `power_system_stabilizers/pss3c.py` | Exact identifier |
| PSS6C | `models/1-SynchronousMachines/PowerSystemStabilizer/PSS6C/index.qmd` | `power_system_stabilizers/pss6c.py` | Exact identifier |
| Frequency-dependent load | `models/2-Loads/FDLoad/index.qmd` | `Rms/load_characteristics/load_frequency_dependent.py` | Exact functional name |
| Exponential load | `models/2-Loads/ExpLoad/index.qmd` | `Rms/load_characteristics/load_exponential_template.py` | Exact functional name |
| ZIP load | `models/2-Loads/ZIPLoad/index.qmd` | `Rms/load_characteristics/load_zip_template.py` | Exact functional name |
| Single-cage induction motor | `models/2-Loads/Motor/SimpleMotor/index.qmd` | `Rms/induction_machines/single_cage_induction_motor_rms_template.py` | Implemented; third-order one-cage motor realization |
| WECC rotor-flux induction motor | `models/2-Loads/Motor/WECC_Motor/index.qmd` | `Rms/induction_machines/wecc_rotor_flux_induction_motor_rms_template.py` | Implemented; fifth-order rotor-flux realization |
| Capacitors | `models/3-CompensationAndFACTS/Capacitors/index.qmd` | `Rms/buses/shunt_template.py` | Blocked: Colib listing page has no model specification |
| Static Compensator | `models/3-CompensationAndFACTS/StaticCompensator/index.qmd` | `Rms/voltage_compensators/static_compensator_rms_template.py` | Implemented; fixed-reactance static compensation |
| EMT STATCOM (GFL) | `models/3-CompensationAndFACTS/STATCOM/index.qmd` | `Emt/converters/statcom_gfl_emt_template.py` | Implemented; control tuning and validation pending |
| LCC | `models/4-HVDC/LCC/index.qmd` | `Rms/hvdc/hvdc_rms_template.py` | Blocked: Colib listing page has no model specification |
| L2EP RMS GFL VSC | `models/4-HVDC/VSC/GridFollowingConverter/L2EP-RMS-GFL-VSC/index.qmd` | `Rms/renewable_controls/l2ep_rms_gfl_template.py` | Implemented; L2EP PLL low-voltage hysteresis included |
| UPC EMT GFL VSC | `models/4-HVDC/VSC/GridFollowingConverter/UPC-EMT-GFL-VSC/index.qmd` | `Emt/converters/upc_gfl_emt_template.py` | Implemented; balanced EMT GFL controls and DC-link interface |
| Full-Phasor GFL VSC | `models/4-HVDC/VSC/GridFollowingConverter/UPC-RMS-GFL-VSC/index.qmd` | `Rms/renewable_controls/upc_full_phasor_gfl_rms_template.py` | Implemented; variant-specific validation pending |
| UPC RMS GFL Phasor-I0 | `models/4-HVDC/VSC/GridFollowingConverter/UPC-RMS-GFL-VSC/PhasorIo/index.qmd` | `Rms/renewable_controls/upc_phasor_gfl_rms_templates.py` | Implemented; no-current-loop reduction |
| UPC RMS GFL Phasor-I1 | `models/4-HVDC/VSC/GridFollowingConverter/UPC-RMS-GFL-VSC/PhasorI1/index.qmd` | `Rms/renewable_controls/upc_phasor_gfl_rms_templates.py` | Implemented; first-order current-loop reduction |
| UPC RMS GFL Phasor-PQ1 | `models/4-HVDC/VSC/GridFollowingConverter/UPC-RMS-GFL-VSC/PhasorPQ1/index.qmd` | `Rms/renewable_controls/upc_phasor_gfl_rms_templates.py` | Implemented; first-order outer-loop reduction |
| EPRI GFM VSC | `models/4-HVDC/VSC/GridFormingConverter/EPRI-GFM-Converter/index.qmd` | `Rms/renewable_controls/colib_gfm_rms_templates.py` | Implemented; EPRI-specific validation pending |
| UPC RMS GFM VSC | `models/4-HVDC/VSC/GridFormingConverter/UPC-RMS-GFM-VSC/index.qmd` | `Rms/renewable_controls/colib_gfm_rms_templates.py` | Implemented; UPC-specific validation pending |
| UPC EMT GFM VSC | `models/4-HVDC/VSC/GridFormingConverter/UPC-EMT-GFM-VSC/index.qmd` | `Emt/converters/vsc_gfm_upc_emt.py` | Implemented; connect the external LCL filter for a complete system |
| UPC EMT point-to-point HVDC | `models/4-HVDC/VSC/Point-to-Point-HVDC/UPC-EMT-HVDC/index.qmd` | `Emt/converters/upc_point_to_point_hvdc_emt_template.py` | Implemented composition; terminal binding pending |
| RTE RMS average VSC-HVDC | `models/4-HVDC/VSC/Point-to-Point-HVDC/RTE-RMS-Average-HVDC/index.qmd` | `Rms/dc_line/rte_average_vsc_hvdc_rms_template.py` | Implemented VSC terminal; compose two terminals for a link |
| Photovoltaics | `models/5-RenewablesAndStorage/PV/index.qmd` | `Rms/solar_pv_generation/pvd1_rms_template.py`, `Emt/solar_pv_generation/pv_emt_template.py` | Blocked: Colib listing page has no model specification |
| Flywheel | `models/5-RenewablesAndStorage/Storage/Flywheel/index.qmd` | `Rms/synchronous_machines/flywheel_rms_template.py` | Implemented RMS storage template with configurable linear SOC loss |
| IEC wind turbine type 3 | `models/5-RenewablesAndStorage/Wind/iec_wt_type3/index.qmd` | `Rms/wind_generation/iec_type3_wind_turbine_rms_template.py` | Implemented Type-3A composition; P/Q controls, DFIG current source, and two-mass drivetrain |
| Bus | `models/6-NetworkComponents/Bus/index.qmd` | `Rms/buses/bus_rms_template.py`, `Emt/buses/bus_emt_template.py` | Blocked: Colib listing page has no model specification |
| Pi-equivalent line | `models/6-NetworkComponents/Line/piLine/index.qmd` | `Rms/line/pi_equivalent_line_rms_template.py` | Implemented; RMS phasor series and half-shunt admittances |
| Constant-parameter line | `models/6-NetworkComponents/Line/cpLine/index.qmd` | `Emt/line/constant_parameter_line_emt_template.py` | Implemented; three-phase Bergeron travel-time history |
| Frequency-dependent line | `models/6-NetworkComponents/Line/FDLine/index.qmd` | `Emt/line/frequency_dependent_line_emt_template.py` | Implemented; JMARTI modal frequency-sample runtime |
| Cantilever transformer | `models/6-NetworkComponents/Transformers/CantileverTransformer/index.qmd` | `Rms/transformers/cantilever_transformer_rms_template.py` | Implemented; fixed-ratio series and magnetizing branches |
| Machine protection | `models/7-Protection/MachineProtection/index.qmd` | `wind_protection_iec.py`, relay templates | Blocked: Colib category page has no model specification |
| Line protection | `models/7-Protection/LineProtection/index.qmd` | No dedicated template | Blocked: Colib category page has no model specification |
| Transformer protection | `models/7-Protection/TransformerProtection/index.qmd` | No dedicated template | Blocked: Colib category page has no model specification |
| System integrity protection schemes | `models/7-Protection/SystemIntegrityProtectionSchemes/index.qmd` | No dedicated template | Blocked: Colib category page has no model specification |
| SFRM underfrequency load shedding | `models/7-Protection/LoadShedding/UFLS/index.qmd` | `Rms/protection_relays/sfrm_ufls_rms_template.py` | Implemented; conventional two-stage UFLS |
| Absolute value | `models/8-Others/BasicControlBlocks/absoluteValue/index.qmd` | `BasicBlockCatalog/Functions/typ_354__abs.py` | Native exact scalar absolute-value block |
| Algebraic equation | `models/8-Others/BasicControlBlocks/algebraicEquation/index.qmd` | `Utils/Symbolic/block.py` | Native symbolic `Block` algebraic-residual support |
| Deadband | `models/8-Others/BasicControlBlocks/deadband/index.qmd` | `BasicBlockCatalog/Functions/typ_89__deadband_p.py`, `typ_96__deadband.py` | Native deadband catalog variants |
| Hysteresis | `models/8-Others/BasicControlBlocks/hysteresis/index.qmd` | `BasicBlockCatalog/Functions/typ_68__flipflop.py` | Native procedural latch primitive plus symbolic branch equations |
| Integrator | `models/8-Others/BasicControlBlocks/integrator/index.qmd` | `BasicBlockCatalog/Functions/typ_284__1_st.py` | Native integrator catalog variant |
| Integrator with output limits | `models/8-Others/BasicControlBlocks/limitedIntegrator/index.qmd` | `Utils/Symbolic/block_helpers.py` | Native directional non-windup integrator helper |
| Integrator with variable limits | `models/8-Others/BasicControlBlocks/integratorVariableLimits/index.qmd` | `Utils/Symbolic/block_helpers.py` | Native directional non-windup helper with symbolic bounds |
| Limiter | `models/8-Others/BasicControlBlocks/limiter/index.qmd` | `BasicBlockCatalog/Functions/typ_313__limit_p.py` | Native constant-bound scalar clamp |
| Limiter with variable bounds | `models/8-Others/BasicControlBlocks/limiterVariableBounds/index.qmd` | `BasicBlockCatalog/Functions/typ_321__limit_s.py` | Native signal-driven scalar clamp |
| PI controller | `models/8-Others/BasicControlBlocks/proportionalIntegralController/index.qmd` | `BasicBlockCatalog/Functions/typ_443__kp_1_sti.py` | Native PI catalog block |
| Limited PI controller | `models/8-Others/BasicControlBlocks/limitedProportionalIntegralController/index.qmd` | `BasicBlockCatalog/Functions/typ_440__kp_1_ti_s_s_s.py`, `typ_444__kp_ki_s_s.py` | Native PI anti-windup catalog variants |
| Fully limited PI controller | `models/8-Others/BasicControlBlocks/2limitedProportionalIntegralController/index.qmd` | `BasicBlockCatalog/Functions/typ_440__kp_1_ti_s_s_s.py`, limiter catalog blocks | Native composable PI and limiter variants |
| Switch | `models/8-Others/BasicControlBlocks/switch/index.qmd` | `BasicBlockCatalog/Functions/typ_520__switch_sig_2_1_by_sig_bool.py` through `typ_524__switch_sig_4_1_by_sig.py` | Native fixed-arity switch catalog variants |
| Timer | `models/8-Others/BasicControlBlocks/timer/index.qmd` | `BasicBlockCatalog/Functions/typ_531__timer_reset.py`, `typ_532__timer_reset_hold_reset_t0_reset_incfw.py` | Native timer/reset catalog variants |
| One-time-constant transfer function | `models/8-Others/BasicControlBlocks/transferFunction/index.qmd` | `BasicBlockCatalog/Functions/typ_146__k_1_st_p.py` | Native first-order transfer-function catalog variant |
| Events | `models/8-Others/Events/index.qmd` | RMS fault and EMT switch/fault templates | Blocked: Colib category page has no event contract |

## Reading this report

- **Exact identifier** means a VeraGrid template has the same published model
  identifier. It is suitable to propose to Colib after an equation, interface,
  licence, and validation review.
- **Family counterpart** means the device class exists, but the template is not
  evidence that it implements Colib's specified variant. It must not be
  advertised as that Colib model without a model-by-model comparison.
- **No dedicated counterpart found** means no matching template name was found
  in the Templates tree. It is an implementation candidate, not proof that the
  capability is absent elsewhere in VeraGrid.

This is deliberately a source-presence inventory. It does not claim that a
template is wired into a public API, initializes identically to the Colib
model, or has passed a transient validation case.

## Exact identifier coverage: propose to Colib after review

| Colib family | Colib model identifiers | VeraGrid template location |
| --- | --- | --- |
| Synchronous machines | `GENQEC` | `Rms/synchronous_machines/genqec_phasor_rms_template.py` |
| Synchronous machines | `GENROU`, `GENSAL` | `Rms/synchronous_machines/genrou.py`, `gensal.py` |
| Excitation systems | `AC1C`, `AC6C`, `AC7C`, `AC8C` | `Rms/excitation_systems/ac1c.py`, `ac6c.py`, `ac7c.py`, `ac8c.py` |
| Excitation systems | `BBSEX1`, `DC1C`, `IEEEX2`, `IEEX2A`, `SCRX` | `Rms/excitation_systems/bbsex1.py`, `dc1c.py`, `ieeex2.py`, `ieex2a.py`, `scrx.py` |
| Excitation systems | `ST1C`, `ST4C`, `ST5C`, `ST6C`, `ST7C`, `ST9C` | `Rms/excitation_systems/st1c.py`, `st4c.py`, `st5c.py`, `st6c.py`, `st7c.py`, `st9c.py` |
| Governors | `GAST`, `GovCT2`, `GovHydro4`, `GovSteamEU`, `HYGOV` | `Rms/governors/gast.py`, `gov_c_t2.py`, `govhydro4.py`, `govsteameu.py`, `hygov.py` |
| Governors | `IEEEG1`, `IEEEG2`, `TGOV1`, `TGOV3` | `Rms/governors/ieeeg1.py`, `ieeeg2.py`, `tgov1.py`, `tgov3.py` |
| Excitation limiters | `OEL2C`, `OEL3C`, `OEL4C`, `OEL5C`, `SCL1C`, `SCL2C`, `UEL1`, `UEL2C` | `Rms/excitation_limiters/oel2c.py`, `oel3c.py`, `oel4c.py`, `oel5c.py`, `scl1c.py`, `scl2c.py`, `uel1.py`, `uel2c.py` |
| Power-system stabilizers | `PSS1A`, `PSS2C`, `PSS3C`, `PSS6C` | `Rms/power_system_stabilizers/pss1a.py`, `pss2c.py`, `pss3c.py`, `pss6c.py` |
| Loads | Frequency-dependent load, exponential load, ZIP load | `Rms/load_characteristics/load_frequency_dependent.py`, `load_exponential_template.py`, `load_zip_template.py` |

There are 42 direct identifier matches in this table when `GENROU` and
`GENSAL` are counted separately. The matching-name set is the best first
contribution batch because it is broad, standards-oriented, and easy for Colib
maintainers to triage.

## Family counterparts: compare before reporting coverage

| Colib model or family | VeraGrid evidence | What remains to check |
| --- | --- | --- |
| `GENTPF/GENTPJ` | `synchronous_machines/gentpf.py`, `gentpj.py` | Validate parameter mapping and transient initialization. |
| `SM1` | `Emt/synchronous_machines/sm1_emt_template.py` | Validate initialization and parameter mapping of the physical-winding superset. |
| `AcRotatingExciter` | `Rms/excitation_systems/ac_rotating_exciter.py` | Validate its transient response against Dynawo/Colib cases. |
| Simple motor and WECC rotor-flux motor | `Rms/induction_machines/single_cage_induction_motor_rms_template.py`, `induction_machines/load_motor.py` | Validate parameter/base mapping and the WECC interface. |
| Capacitors | `Rms/buses/shunt_template.py` | Colib publishes only a category listing, not a capacitor model contract. |
| Grid-following VSC models (L2EP, UPC EMT, UPC RMS I0/I1/PQ1) | `Rms/renewable_controls/upc_phasor_gfl_rms_templates.py`, `Rms/converters/vsc_gfl.py`, `Emt/converters/vsc_gfl_emt.py` | Validate L2EP/EMT-specific limits and DC-link treatment. |
| Grid-forming VSC models (EPRI, UPC EMT, UPC RMS) | `Rms/converters/vsc_gfm.py`, `Emt/converters/vsc_gfm_emt.py`, `Emt/converters/vsc_gfm_upc_emt.py` | Droop/virtual-machine equations, limiters, and the published UPC/EPRI variant. |
| Point-to-point VSC-HVDC (UPC EMT, RTE RMS average) | `Rms/hvdc/hvdc_rms_template.py`, `Rms/converters/hvdc_vsc_gfl_rms_template.py`, `Emt/dc_line/dc_line_emt_template.py` | End-to-end topology, converter controls, and the stated averaging assumptions. |
| Photovoltaics | `Rms/solar_pv_generation/pvd1_rms_template.py`, `Emt/solar_pv_generation/pv_emt_template.py` | Colib publishes only a category listing, not a PV model contract. |
| IEC wind turbine type 3 | `wind_generation/wind_gen_type3a_iec.py`, `wind_gen_type3b_iec.py` | Colib's DFIG composition and controller variants. |
| Lines (pi, constant-parameter, frequency-dependent) | RMS line templates; `Emt/line/pi_line_emt_template.py`, `bergeron_line_emt_template.py`, `jmarti_line_emt_template.py` | The exact line formulation; Bergeron/JMarti is not automatically Colib's frequency-dependent line. |
| Cantilever transformer | `Rms/transformers/transformer_rms_template.py`, `Emt/transformers/transformer_emt_template.py` | The cantilever-equivalent formulation. |
| Basic control blocks | `BasicBlockCatalog/Functions/` plus RMS control templates | One-to-one block semantics, limits, reset behaviour, and initialization. |
| Events | RMS fault and EMT switch/fault templates | Colib event interface and supported event set. |

### Deep review of the family counterparts

The following review reads the Colib equations/assumptions and the cited
VeraGrid templates. It replaces the previous filename-only inference for these
models. **Status** is intentionally about behavioural compatibility, not
whether the two names resemble each other.

| Colib scope | Status | Evidence from the two sources | Consequence |
| --- | --- | --- | --- |
| `GENTPF/GENTPJ` | **Implemented** | VeraGrid now exposes distinct six-state saturated templates: GENTPF uses the flux-only saturation law and GENTPJ adds the Colib `K_is` stator-current saturation term. | Validate equations, parameters, and nonzero-`K_is` transient initialization against Colib cases. |
| `SM1` | **Implemented physical-winding superset** | VeraGrid now exposes `Emt/synchronous_machines/sm1_emt_template.py` over its ABC stator, field, and damper-winding EMT machine. | Validate Colib SM1 initialization and parameter mapping before reporting exact equivalence. |
| `AcRotatingExciter` | **Implemented** | VeraGrid now exposes the specified `Efe`/`Ir` input and `Efd`/`Vfe` output contract with `AEx exp(BEx Ve)` saturation, demagnetizing feedback, a dynamic upper integrator limit, and rectifier loading. | Validate its transient response against the published Dynawo implementation. |
| Colib single-cage induction motor | **Implemented** | VeraGrid now exposes a named third-order one-cage motor with the published linear machine and speed-dependent mechanical-load structure. | Validate SI/per-unit base conversion, torque scaling, and initialization against Colib cases. |
| Colib WECC rotor-flux motor | **Implemented** | VeraGrid now exposes a named fifth-order entry retaining the four rotor-flux and rotor-speed states, with `Ls`, `Lp`, `Lpp`, `Tp0`, `Tpp0`, and `H` through the native adaptation. | Validate state/sign conventions and SI/per-unit base mapping against Colib cases. |
| Capacitors | **Blocked** | Colib's capacitor page is only a listing frontmatter document, without equations, parameters, or interface. | Do not claim or implement a Colib capacitor model until a model page is published. |
| Static Compensator | **Implemented** | VeraGrid now exposes a named fixed-reactance template using `Qc = Vr**2 / Xc` through its constant-susceptance shunt formulation. | Validate the sign/base mapping for a target network; it is intentionally not a controlled SVC/STATCOM. |
| L2EP RMS GFL VSC | **Implemented** | VeraGrid now exposes a named L2EP entry using its differential transformer-current, PLL, P/Q control, reactive-current-first circular limiter, and `Vpll1`/`Vpll2` procedural PLL block/restart latch. | Validate the complete L2EP parameter contract against transient reference cases. |
| UPC EMT GFL VSC | **Implemented** | VeraGrid now exposes the UPC-named balanced EMT GFL converter with Clarke/Park transforms, PLL, R-L AC connection, outer P/Q control, inner current control, and terminal AC/DC current outputs. | Validate DC-boundary, current-limit, and anti-windup behaviour against Colib cases. |
| UPC RMS GFL I0/I1/PQ1 variants | **Implemented** | VeraGrid now has named I0, I1, and PQ1 entries. I0 removes current-loop dynamics; I1 retains a first-order current lag; PQ1 uses first-order power-to-current references. | Validate gains, limits, and initialization against Colib benchmark cases. |
| EPRI/UPC RMS GFM VSC | **Implemented** | VeraGrid exposes named EPRI and UPC entry points that reuse `vsc_gfm.py`, including P-f/Q-V droop, LCL-filter parameters, current limiting and anti-windup. | Validate the named variants' detailed limits and reference interfaces against their Colib specifications. |
| UPC EMT GFM VSC | **Implemented controller** | `vsc_gfm_upc_emt.py` implements the UPC GFM controls and deliberately delegates LCL electrical equations to connected EMT elements. | Connect and validate the external LCL network in a complete study. |
| UPC EMT point-to-point HVDC | **Implemented composition** | VeraGrid now provides a composite GFM, DC-line, and GFL template. | Bind terminal variables and validate the two-station link contract. |
| RTE RMS average VSC-HVDC | **Implemented terminal** | VeraGrid now provides a named RMS VSC terminal based on the existing VSC-HVDC builder. | Compose two terminals and validate limits, blocking, and fault reactive-current behaviour. |
| Photovoltaics | **Blocked** | The Colib PV page is only listing metadata, without equations, parameters, or interface. VeraGrid has several PVD1/PV EMT templates. | Do not claim or implement a Colib PV model until a model page is published. |
| IEC wind turbine type 3 | **Implemented Type-3A composition** | VeraGrid now composes its Type-3 P/Q controls, Type-3A current source, terminal feedback, and two-mass drivetrain in `Rms/wind_generation/iec_type3_wind_turbine_rms_template.py`. | Import real turbine parameters and validate Type-3A/3B variants, protection, and plant-level controls against Colib cases. |
| Pi-equivalent line | **Implemented** | VeraGrid now exposes a named RMS phasor pi line with the Colib series-admittance and equal half-shunt terminal-current equations. | Validate short-, medium-, and long-line equivalent-parameter conversion. |
| Constant-parameter travelling-wave line | **Implemented** | VeraGrid now exposes a named three-phase Bergeron line using delayed history values at both terminals, matching Colib's constant-parameter travel-time formulation. | Validate modal/phase assumptions, characteristic impedance, and initialization. |
| Frequency-dependent line | **Implemented** | VeraGrid now exposes a named JMARTI line whose companion runtime processes frequency-domain modal samples and updates the retained Norton history currents. | Validate the rational/modal fit and impulse response against a Colib frequency-dependent reference case. |
| Cantilever transformer | **Implemented** | VeraGrid now exposes a named fixed-ratio transformer with series and magnetizing branches matching the Colib cantilever-equivalent circuit. | Add a test-data adapter from open-/short-circuit values to `R`, `X`, `G`, and `B`, then validate no-load/short-circuit cases. |
| Basic control blocks | **Covered by native catalog forms** | The Colib absolute value, algebraic equation, deadband, hysteresis, integrator, limiter, PI, switch, timer, and transfer-function pages map to existing `BasicBlockCatalog` and symbolic-control primitives. | Validate numerical trajectories and event timing against Colib reference cases. |
| Events | **Partial infrastructure only** | VeraGrid has fault/switch templates; the Colib entry is a category page rather than an individual event contract. | There is no specific Colib model to claim or implement yet. |

## Source pages without an implementable model contract

The following Colib entries had no direct, dedicated template identifier in
`src/VeraGridEngine/Templates` during this scan:

| Priority | Colib model | Rationale |
| --- | --- | --- |
| Blocked | Line, machine, transformer, and system-integrity protection | Colib provides only category pages, with no equations, parameters, or interface from which to implement a model. |

## Recommended contribution sequence

1. Start with one small, reviewable exact-match batch: excitation limiters
   (`OEL*`, `SCL*`, `UEL*`). Their identifiers and source files align directly.
2. Follow with governors, PSSs, and excitation systems, preserving the exact
   Colib identifier in the proposed implementation metadata.
3. For each direct match, compare equations, parameter names/units, limiting,
   initialization, licence compatibility, and one Colib-relevant test case
   before telling Colib it is implemented.
4. Keep category-only entries blocked until Colib publishes equations,
   parameters, and interfaces sufficient for a VeraGrid technical specification.

## Scope and reproducibility

- VeraGrid scan root: `src/VeraGridEngine/Templates`.
- Colib scan root: `models/` at commit `16d6171513fd1adf900d51a0ec664888d66b274a`.
- The scan includes RMS, EMT, and basic-block template directories. RMS models
  are organized by domain (for example, excitation systems, governors, and
  synchronous machines). It excludes non-template code, tests, and generated
  artifacts.
- The named templates and their focused tests were added during this coverage
  implementation pass; the current template-test suite is the verification
  evidence for structural construction, not transient-model equivalence.
