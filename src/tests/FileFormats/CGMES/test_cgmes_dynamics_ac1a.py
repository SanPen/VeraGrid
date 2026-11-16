# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Focused checks for equation-backed CGMES dynamic model conversion."""


from math import atan2, cos, isclose, pi, sin
from copy import deepcopy

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.static_parameter_mapping_unified import (
    assign_static_api_object_mapping_for_device,
)
from VeraGridEngine.Templates.Rms.induction_machines.asynchronous_machine_time_constant_reactance import (
    build_asynchronous_machine_time_constant_reactance_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st3a import (
    ExcIEEEST3AParameters,
    build_exc_i_e_e_e_s_t3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st4b import (
    ExcIEEEST4BParameters,
    build_exc_i_e_e_e_s_t4_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st5b import (
    ExcIEEEST5BParameters,
    build_exc_i_e_e_e_s_t5_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st7b import (
    ExcIEEEST7BParameters,
    build_exc_i_e_e_e_s_t7_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ni import (
    ExcNIParameters,
    build_exc_n_i_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_oex3_t import (
    ExcOEX3TParameters,
    build_exc_o_e_x3_t_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_pic import (
    ExcPICParameters,
    build_exc_p_i_c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_rexs import (
    ExcREXSParameters,
    build_exc_r_e_x_s_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st2a import (
    ExcST2AParameters,
    build_exc_s_t2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st3a import (
    ExcST3AParameters,
    build_exc_s_t3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_sk import (
    ExcSKParameters,
    build_exc_s_k_template,
    exc_sk_rectifier_output,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_sexs import (
    build_exc_s_e_x_s_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_ieee2 import (
    UnderexcLimIEEE2Parameters,
    build_underexc_lim_i_e_e_e2_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_x1 import (
    UnderexcLimX1Parameters,
    build_underexc_lim_x1_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_x2 import (
    UnderexcLimX2Parameters,
    build_underexc_lim_x2_template,
)
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_ieee1 import (
    UnderexcLimIEEE1Parameters,
    build_underexc_lim_i_e_e_e1_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro2 import (
    GovHydro2Parameters,
    build_gov_hydro2_template,
    get_gov_hydro2_curve_power,
)
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_p_type4b_iec import (
    build_wind_cont_p_type4b_i_e_c_template,
)
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.procedural_logic import FlipFlopLogic
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.cim.cgmes.dynamics.conversion import (
    copy_cgmes_parameters,
    compose_machine_with_underexc_lim_x1,
    compose_machine_with_underexc_lim_x2,
    compose_machine_with_underexc_lim_i_e_e_e1,
    compose_detailed_machine_with_exc_avr1,
    compose_detailed_machine_with_exc_dc,
    convert_cgmes_dynamics,
    find_veragrid_devices,
    find_block_variable_by_name,
    find_block_initial_value,
    get_exc_ac1a_parameters,
    get_exc_ac2a_parameters,
    get_exc_ac3a_parameters,
    get_exc_ac4a_parameters,
    get_exc_ac5a_parameters,
    get_exc_ac6a_parameters,
    get_exc_ac8b_parameters,
    get_exc_ans_parameters,
    get_exc_avr1_parameters,
    get_exc_avr2_parameters,
    get_exc_avr3_parameters,
    get_exc_avr4_parameters,
    get_exc_avr5_parameters,
    get_exc_avr7_parameters,
    get_exc_bbc_parameters,
    get_exc_cz_parameters,
    get_exc_dc1a_parameters,
    get_exc_dc2a_parameters,
    get_exc_dc3a_parameters,
    get_exc_dc3a1_parameters,
    get_exc_elin1_parameters,
    get_exc_elin2_parameters,
    get_exc_hu_parameters,
    get_exc_ieee_ac1a_parameters,
    get_exc_ieee_ac2a_parameters,
    get_exc_ieee_ac3a_parameters,
    get_exc_ieee_ac4a_parameters,
    get_exc_ieee_ac5a_parameters,
    get_exc_ieee_ac6a_parameters,
    get_exc_ieee_ac7b_parameters,
    get_exc_ieee_ac8b_parameters,
    get_exc_ieee_dc1a_parameters,
    get_exc_ieee_dc2a_parameters,
    get_exc_ieee_dc3a_parameters,
    get_exc_ieee_dc4b_parameters,
    get_exc_ieee_st1a_parameters,
    get_exc_ieee_st2a_parameters,
    get_exc_ieee_st3a_parameters,
    get_exc_ieee_st4b_parameters,
    get_exc_ieee_st5b_parameters,
    get_exc_ieee_st7b_parameters,
    get_exc_ni_parameters,
    get_exc_rexs_parameters,
    get_exc_st2a_parameters,
    get_exc_st3a_parameters,
    compose_detailed_machine_with_exc_sk,
    set_exc_rexs_feedback_selector,
    get_gast_parameters,
    get_gastwd_parameters,
    get_gast4_parameters,
    get_gov_steam0_parameters,
    get_gov_steam_cc_parameters,
    get_gov_steam_f_v2_parameters,
    get_gov_steam_f_v3_parameters,
    get_gov_steam_f_v4_parameters,
    get_gov_steam_s_g_o_parameters,
    get_gov_steam_ieee1_parameters,
    get_gov_hydro1_parameters,
    get_gov_hydro2_parameters,
    get_gov_hydro3_parameters,
    get_gov_hydro4_parameters,
    get_gov_hydro_dd_parameters,
    get_gov_hydro_pelton_parameters,
    get_gov_hydro_pid_parameters,
    get_gov_hydro_pid2_parameters,
    get_gov_hydro_wpid_parameters,
    get_gov_hydro_r_parameters,
    get_gov_hydro_weh_parameters,
    get_gov_steam_b_b_parameters,
    get_gov_ct1_parameters,
    get_gov_ct2_parameters,
    compose_machine_with_vcomp_ieee_type2,
    get_turbine_governor_power_base,
    get_synchronous_machine_time_constant_reactance_parameters,
)
from VeraGridEngine.Templates.Rms import get_international_model_builders
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.energy_source import EnergySource
from VeraGridEngine.enumerations import CGMESVersions
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import SynchronousMachineOperatingMode
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.synchronous_machine import (
    SynchronousMachine as CgmesSynchronousMachine,
)
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.asynchronous_machine import (
    AsynchronousMachine as CgmesAsynchronousMachine,
)
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    EnergyConsumer,
    ExcAC1A,
    PFVArType1IEEEPFController,
    PFVArType1IEEEVArController,
    VAdjIEEE,
    ExcAC2A,
    ExcAC3A,
    ExcAC4A,
    ExcAC5A,
    ExcAC6A,
    ExcAC8B,
    ExcANS,
    ExcAVR1,
    ExcAVR2,
    ExcAVR3,
    ExcAVR4,
    ExcAVR5,
    ExcAVR7,
    ExcBBC,
    ExcCZ,
    ExcDC1A,
    ExcDC2A,
    ExcDC3A,
    ExcDC3A1,
    ExcELIN1,
    ExcELIN2,
    ExcHU,
    ExcIEEEAC1A,
    ExcIEEEAC2A,
    ExcIEEEAC3A,
    ExcIEEEAC4A,
    ExcIEEEAC5A,
    ExcIEEEAC6A,
    ExcIEEEAC7B,
    ExcIEEEAC8B,
    ExcSEXS,
    ExcIEEEDC1A,
    ExcIEEEDC2A,
    ExcIEEEDC3A,
    ExcIEEEDC4B,
    ExcIEEEST1A,
    ExcIEEEST1AUELselectorKind,
    ExcIEEEST2A,
    ExcIEEEST3A,
    ExcIEEEST4B,
    ExcST4B,
    ExcIEEEST5B,
    ExcIEEEST7B,
    ExcST7B,
    ExcST6B,
    ExcNI,
    ExcOEX3T,
    ExcPIC,
    ExcREXS,
    ExcREXSFeedbackSignalKind,
    ExcST7BOELselectorKind,
    ExcST7BUELselectorKind,
    ExcRQB,
    ExcST1A,
    ExcST2A,
    ExcST3A,
    ExcSCRX,
    GenericNonLinearLoadModelKind,
    InputSignalKind,
    LoadAggregate,
    LoadGenericNonLinear,
    LoadMotor,
    LoadStatic,
    MechLoad1,
    OverexcLim2,
    GovGAST,
    GovGAST1,
    GovGAST2,
    GovGAST3,
    GovGASTWD,
    GovGAST4,
    GovCT1,
    GovCT2,
    DroopSignalFeedbackKind,
    GovHydroIEEE0,
    GovHydroIEEE2,
    GovHydro1,
    GovHydro2,
    GovHydro3,
    GovHydro4,
    GovHydro4ModelKind,
    IfdBaseKind,
    GovHydroDD,
    GovHydroFrancis,
    GovHydroPelton,
    GovHydroPID2,
    GovHydroPID,
    GovHydroWPID,
    GovHydroR,
    GovHydroWEH,
    FrancisGovernorControlKind,
    GovSteam0,
    GovSteamBB,
    GovSteamCC,
    GovSteam1,
    GovSteam2,
    GovSteamEU,
    GovSteamIEEE1,
    GovSteamFV2,
    GovSteamFV3,
    GovSteamFV4,
    GovSteamSGO,
    GovSteamCC,
    StaticLoadModelKind,
    SynchronousMachine,
    SynchronousMachineDynamics,
    SynchronousMachineEquivalentCircuit,
    SynchronousMachineSimplified,
    SynchronousMachineTimeConstantReactance,
    UnderexcLimIEEE2,
    AsynchronousMachineTimeConstantReactance,
    AsynchronousMachineEquivalentCircuit,
    AsynchronousMachine,
    AsynchronousMachineDynamics,
    WindAeroConstIEC,
    WindAeroOneDimIEC,
    WindContCurrLimIEC,
    WindContPType4aIEC,
    WindContQIEC,
    WindContQLimIEC,
    WindGenTurbineType1aIEC,
    WindGenTurbineType1bIEC,
    WindGenType3aIEC,
    WindGenType4IEC,
    WindMechIEC,
    WindRefFrameRotIEC,
    WindTurbineType3IEC,
    WindTurbineType4aIEC,
    WindGenType3bIEC,
    AngleDegrees,
    WindPitchContPowerIEC,
    PowerElectronicsConnection,
    WindDynamicsLookupTable,
    WindLookupTableFunctionKind,
    WindQcontrolModeKind,
    WindUVRTQcontrolModeKind,
    RotorKind,
    SynchronousMachineModelKind,
    PssIEEE1A,
    PssIEEE2B,
    PssIEEE3B,
    PssIEEE4B,
    Pss1,
    Pss1A,
    Pss2B,
    Pss2ST,
    Pss5,
    PssPTIST1,
    PssPTIST3,
    PssELIN2,
    PssSB4,
    PssSH,
    PssSK,
    PssSTAB2A,
    PssWECC,
    PssRQB,
    VCompIEEEType1,
    TurbineGovernorDynamics,
)
from VeraGridEngine.IO.cim.cgmes.dynamics.schema_2_4_15 import (
    GovHydro4 as GovHydro424,
    WindAeroLinearIEC as WindAeroLinearIEC24,
    WindGenTurbineType3IEC as WindGenTurbineType3IEC24,
    WindGenTurbineType3aIEC as WindGenTurbineType3aIEC24,
    WindGenTurbineType3bIEC as WindGenTurbineType3bIEC24,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac1a import (
    ExcIEEEAC1AParameters,
    build_exc_i_e_e_e_a_c1_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac2a import (
    ExcIEEEAC2AParameters,
    build_exc_i_e_e_e_a_c2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac3a import (
    ExcIEEEAC3AParameters,
    build_exc_i_e_e_e_a_c3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac4a import (
    ExcIEEEAC4AParameters,
    build_exc_i_e_e_e_a_c4_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac5a import (
    ExcIEEEAC5AParameters,
    build_exc_i_e_e_e_a_c5_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac6a import (
    ExcIEEEAC6AParameters,
    build_exc_i_e_e_e_a_c6_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac7b import (
    ExcIEEEAC7BParameters,
    build_exc_i_e_e_e_a_c7_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac8b import (
    ExcIEEEAC8BParameters,
    build_exc_i_e_e_e_a_c8_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_dc1a import (
    ExcIEEEDC1AParameters,
    build_exc_i_e_e_e_d_c1_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_dc2a import (
    ExcIEEEDC2AParameters,
    build_exc_i_e_e_e_d_c2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_dc3a import (
    ExcIEEEDC3AParameters,
    build_exc_i_e_e_e_d_c3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_dc4b import (
    ExcIEEEDC4BParameters,
    build_exc_i_e_e_e_d_c4_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st1a import (
    ExcIEEEST1AParameters,
    build_exc_i_e_e_e_s_t1_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st2a import (
    ExcIEEEST2AParameters,
    build_exc_i_e_e_e_s_t2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac1a import (
    ExcAC1AParameters,
    build_exc_a_c1_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac2a import (
    ExcAC2AParameters,
    build_exc_a_c2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac3a import (
    ExcAC3AParameters,
    build_exc_a_c3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac4a import (
    ExcAC4AParameters,
    build_exc_a_c4_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac5a import (
    ExcAC5AParameters,
    build_exc_a_c5_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac6a import (
    ExcAC6AParameters,
    build_exc_a_c6_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac8b import (
    ExcAC8BParameters,
    build_exc_a_c8_b_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ans import (
    ExcANSParameters,
    build_exc_a_n_s_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr1 import (
    ExcAVR1Parameters,
    build_exc_a_v_r1_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr2 import (
    ExcAVR2Parameters,
    build_exc_a_v_r2_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr3 import (
    ExcAVR3Parameters,
    build_exc_a_v_r3_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr4 import (
    ExcAVR4Parameters,
    build_exc_a_v_r4_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr5 import (
    ExcAVR5Parameters,
    build_exc_a_v_r5_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr7 import (
    ExcAVR7Parameters,
    build_exc_a_v_r7_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_bbc import (
    ExcBBCParameters,
    build_exc_b_b_c_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_cz import (
    ExcCZParameters,
    build_exc_c_z_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc1a import (
    ExcDC1AParameters,
    build_exc_d_c1_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc2a import (
    ExcDC2AParameters,
    build_exc_d_c2_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc3a import (
    ExcDC3AParameters,
    build_exc_d_c3_a_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc3a1 import (
    ExcDC3A1Parameters,
    build_exc_d_c3_a1_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_elin1 import (
    ExcELIN1Parameters,
    build_exc_e_l_i_n1_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_elin2 import (
    ExcELIN2Parameters,
    build_exc_e_l_i_n2_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_hu import (
    ExcHUParameters,
    build_exc_h_u_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_scrx import (
    build_exc_s_c_r_x_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_gast import (
    build_gov_g_a_s_t_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_gast3 import (
    build_gov_g_a_s_t3_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_gast4 import (
    GovGAST4Parameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_c_t1 import (
    GovCT1Parameters,
    build_gov_c_t1_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_c_t2 import (
    GovCT2Parameters,
    build_gov_c_t2_template,
    get_gov_ct2_frequency_power_limit,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pelton import (
    GovHydroPeltonParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pid2 import (
    GovHydroPID2Parameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pid import (
    GovHydroPIDParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_w_pid import (
    GovHydroWPIDParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_r import (
    GovHydroRParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_hydro_weh import (
    GovHydroWEHParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam0 import (
    GovSteam0Parameters,
    build_gov_steam0_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_bb import (
    GovSteamBBParameters,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam1 import (
    GovSteam1Settings,
    build_gov_steam1_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_cc import (
    GovSteamCCParameters,
    build_gov_steam_c_c_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_fv2 import (
    GovSteamFV2Parameters,
    build_gov_steam_f_v2_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_fv3 import (
    GovSteamFV3Parameters,
    build_gov_steam_f_v3_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_fv4 import (
    GovSteamFV4Parameters,
    build_gov_steam_f_v4_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_ieee1 import (
    build_gov_steam_i_e_e_e1_template,
)
from VeraGridEngine.Templates.Rms.governors.gov_steam_sgo import (
    GovSteamSGOParameters,
    build_gov_steam_s_g_o_template,
)
from VeraGridEngine.Templates.Rms.load_characteristics.load_generic_non_linear import (
    build_load_generic_non_linear_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.load_motor import (
    build_load_motor_template,
)
from VeraGridEngine.Templates.Rms.load_characteristics.load_static import (
    build_load_static_template,
)
from VeraGridEngine.Templates.Rms.common.mech_load1 import (
    build_mech_load1_template,
)
from VeraGridEngine.Templates.Rms.synchronous_machines.synchronous_machine_time_constant_reactance import (
    build_synchronous_machine_time_constant_reactance_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, CmpOp, Comparison, Const, Expr, Var, eval_uid
from VeraGridEngine.Utils.procedural_logic import TimeDelayLogic
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.data_logger import DataLogger

from tests.symbolic_block_roundtrip import roundtrip_block


def test_asynchronous_machine_saturation_fields_are_retained_as_data_only() -> None:
    """Preserve inherited saturation RDF values without applying an unsourced law.

    :return: None.
    """
    dynamics: AsynchronousMachineTimeConstantReactance = AsynchronousMachineTimeConstantReactance(
        rdfid='_async_saturation_data_only'
    )
    dynamics.saturationFactor = 0.13
    dynamics.saturationFactor120 = 0.27
    template_name: str = f'AsynchronousMachineTimeConstantReactance_{dynamics.uuid}'
    template: RmsModelTemplate = build_asynchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name=template_name,
    )

    copy_cgmes_parameters(
        cgmes_object=dynamics,
        template=template,
        variable_factory=VarFactory(),
    )

    parameter_values: dict[str, float | None] = dict()
    runtime_block: Block
    parameter_variable: Var
    for runtime_block in template.block.get_all_blocks():
        for parameter_variable, parameter_value in runtime_block.event_dict.items():
            if parameter_variable.name.startswith(
                    'AsynchronousMachineTimeConstantReactance.saturationFactor'
            ):
                parameter_values[parameter_variable.name] = float(parameter_value.value)
            else:
                pass
    assert parameter_values[
        f'AsynchronousMachineTimeConstantReactance.saturationFactor_{template_name}'
    ] == pytest.approx(0.13)
    assert parameter_values[
        f'AsynchronousMachineTimeConstantReactance.saturationFactor120_{template_name}'
    ] == pytest.approx(0.27)
    assert not any(
        parameter_variable.name in ('saturationFactor', 'saturationFactor120')
        for parameter_variable in template.block.algebraic_vars
    )


@pytest.mark.parametrize('machine_q', (0.2, 0.05, 1.0))
@pytest.mark.parametrize('limiter_time', (1.5, 0.0))
def test_underexc_lim_x1_composer_seeds_connected_operating_point(
        machine_q: float,
        limiter_time: float,
) -> None:
    """Seed X1's field washout and bounded output from machine signals.

    :param machine_q: Solved reactive power selecting lower, interior, or upper limit.
    :param limiter_time: Positive dynamic or zero-time algebraic output stage.
    :return: None.
    """
    limiter_name: str = 'UnderexcLimX1_initialization'
    exciter_name: str = 'ExcIEEEAC1A_initialization'
    machine_template: RmsModelTemplate = RmsModelTemplate(name='Machine_initialization')
    machine_template.block = Block(name=machine_template.name)
    machine_reactive_power: Var = Var('Qg')
    machine_field_current: Var = Var(f'IfdPu_{exciter_name}')
    machine_field_voltage: Var = Var(f'EfdPu_{exciter_name}')
    machine_signal_values: tuple[tuple[Var, float], ...] = (
        (machine_reactive_power, machine_q),
        (machine_field_current, 0.3),
        (machine_field_voltage, 1.5),
    )
    machine_template.block.out_vars.extend((
        machine_reactive_power,
        machine_field_current,
        machine_field_voltage,
    ))
    for machine_signal, machine_signal_value in machine_signal_values:
        machine_template.block.algebraic_vars.append(machine_signal)
        machine_template.block.algebraic_eqs.append(machine_signal - Const(machine_signal_value))
        machine_template.block.init_eqs[machine_signal] = Const(machine_signal_value)
    else:
        pass
    exciter_template: RmsModelTemplate = RmsModelTemplate(name=exciter_name)
    exciter_template.block = Block(name=exciter_name)
    exciter_uel_input: Var = Var(f'UelPu_{exciter_name}')
    exciter_template.block.in_vars.append(exciter_uel_input)
    machine_template.block.children.append(exciter_template.block)
    limiter_template: RmsModelTemplate = build_underexc_lim_x1_template(
        vfactory=VarFactory(),
        name=limiter_name,
        parameters=UnderexcLimX1Parameters(
            kf2=0.5,
            tf2=0.4,
            km=2.0,
            tm=limiter_time,
            melmax=0.8,
            k=3.0,
        ),
    )

    composite_template, unsupported_ports = compose_machine_with_underexc_lim_x1(
        machine_template=machine_template,
        exciter_template=exciter_template,
        limiter_template=limiter_template,
    )

    assert composite_template is not None, unsupported_ports
    assert unsupported_ports == tuple()
    filter_state: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'FieldLowPassPu_{limiter_name}',
    )
    limited_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'LimitedExcitationPu_{limiter_name}',
    )
    output_state: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VuelPu_{limiter_name}',
    )
    assert filter_state is not None
    assert limited_output is not None
    assert output_state is not None
    filter_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        filter_state,
    )
    limited_output_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        limited_output,
    )
    output_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        output_state,
    )
    assert filter_initial is not None
    assert filter_initial.name == machine_field_voltage.name
    assert limited_output_initial is not None
    assert output_initial is not None
    assert output_initial.name == limited_output.name
    initial_variable_names: set[str] = set()
    for initial_variable in limited_output_initial.get_vars():
        initial_variable_names.add(initial_variable.name)
    else:
        pass
    assert machine_reactive_power.name in initial_variable_names
    assert machine_field_current.name in initial_variable_names
    filter_gain: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'UnderexcLimX1.kf2_{limiter_name}',
    )
    assert filter_gain is not None
    output_equation: Expr | None = None
    runtime_block: Block
    for runtime_block in composite_template.block.get_all_blocks():
        if output_state in runtime_block.algebraic_vars:
            output_equation_index: int = runtime_block.algebraic_vars.index(output_state)
            output_equation = runtime_block.algebraic_eqs[output_equation_index]
        else:
            pass
    assert output_equation is not None
    assert output_equation.eval(**{
        output_state.name: 0.25,
        limited_output.name: 0.5,
        filter_gain.name: 0.5,
        machine_field_voltage.name: 1.5,
        f'FieldLowPassPu_{limiter_name}': 1.0,
    }) == pytest.approx(0.0)
    assert_zero_initial_residuals(composite_template, dict())


@pytest.mark.parametrize('machine_p', (0.2, 0.85, 1.0))
@pytest.mark.parametrize('limiter_time', (1.5, 0.0))
def test_underexc_lim_x2_composer_seeds_connected_operating_point(
        machine_p: float,
        limiter_time: float,
) -> None:
    """Seed X2's washout memory and bounded output from machine P/Q/V.

    :param machine_p: Solved active power selecting lower, interior, or upper limit.
    :param limiter_time: Positive dynamic or zero-time algebraic output stage.
    :return: None.
    """
    limiter_name: str = 'UnderexcLimX2_initialization'
    exciter_name: str = 'ExcIEEEAC1A_X2_initialization'
    machine_template: RmsModelTemplate = RmsModelTemplate(name='Machine_X2_initialization')
    machine_template.block = Block(name=machine_template.name)
    machine_active_power: Var = Var('Pg')
    machine_reactive_power: Var = Var('Qg')
    machine_voltage: Var = Var('Vm')
    machine_signal_values: tuple[tuple[Var, float], ...] = (
        (machine_active_power, machine_p),
        (machine_reactive_power, 0.15),
        (machine_voltage, 1.0),
    )
    machine_template.block.out_vars.extend((
        machine_active_power,
        machine_reactive_power,
        machine_voltage,
    ))
    for machine_signal, machine_signal_value in machine_signal_values:
        machine_template.block.algebraic_vars.append(machine_signal)
        machine_template.block.algebraic_eqs.append(machine_signal - Const(machine_signal_value))
        machine_template.block.init_eqs[machine_signal] = Const(machine_signal_value)
    else:
        pass
    exciter_template: RmsModelTemplate = RmsModelTemplate(name=exciter_name)
    exciter_template.block = Block(name=exciter_name)
    exciter_uel_input: Var = Var(f'UelPu_{exciter_name}')
    exciter_template.block.in_vars.append(exciter_uel_input)
    machine_template.block.children.append(exciter_template.block)
    limiter_template: RmsModelTemplate = build_underexc_lim_x2_template(
        vfactory=VarFactory(),
        name=limiter_name,
        parameters=UnderexcLimX2Parameters(
            kf2=0.5,
            tf2=0.4,
            km=1.5,
            tm=limiter_time,
            melmax=0.5,
            qo=0.1,
            r=0.8,
        ),
    )

    composite_template, unsupported_ports = compose_machine_with_underexc_lim_x2(
        machine_template=machine_template,
        exciter_template=exciter_template,
        limiter_template=limiter_template,
    )

    assert composite_template is not None, unsupported_ports
    assert unsupported_ports == tuple()
    output_state: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VuelPu_{limiter_name}',
    )
    feedback_memory: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'FieldFeedbackWashoutPuMemory_{limiter_name}',
    )
    assert output_state is not None
    assert feedback_memory is not None
    output_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        output_state,
    )
    feedback_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        feedback_memory,
    )
    assert output_initial is not None
    assert feedback_initial is not None
    feedback_initial_names: set[str] = set()
    for initial_variable in feedback_initial.get_vars():
        feedback_initial_names.add(initial_variable.name)
    else:
        pass
    assert output_state.name in feedback_initial_names
    assert_zero_initial_residuals(composite_template, dict())


@pytest.mark.parametrize('with_stabilizer', (False, True))
def test_underexc_lim_ieee1_composer_uses_associated_stabilizer_or_host_input(
        with_stabilizer: bool,
) -> None:
    """Connect IEEE1 Vf to its associated PSS output when that block exists.

    :param with_stabilizer: Whether the machine graph already contains the associated PSS.
    :return: None.
    """
    machine_template: RmsModelTemplate = RmsModelTemplate(name='Machine_IEEE1')
    machine_template.block = Block(name=machine_template.name)
    machine_signals: tuple[Var, ...] = (
        Var('Vm'), Var('Va'), Var('Pg'), Var('Qg'),
    )
    machine_template.block.out_vars.extend(machine_signals)
    exciter_template: RmsModelTemplate = RmsModelTemplate(name='Exciter_IEEE1')
    exciter_template.block = Block(name=exciter_template.name)
    exciter_input: Var = Var(f'UelPu_{exciter_template.name}')
    exciter_template.block.in_vars.append(exciter_input)
    machine_template.block.children.append(exciter_template.block)
    stabilizer_template: RmsModelTemplate | None = None
    if with_stabilizer:
        stabilizer_template = RmsModelTemplate(name='Pss_IEEE1')
        stabilizer_template.block = Block(name=stabilizer_template.name)
        stabilizer_output: Var = Var(f'VsPu_{stabilizer_template.name}')
        stabilizer_template.block.out_vars.append(stabilizer_output)
        stabilizer_template.block.algebraic_vars.append(stabilizer_output)
        stabilizer_template.block.algebraic_eqs.append(stabilizer_output)
        machine_template.block.children.append(stabilizer_template.block)
    else:
        pass
    limiter_template: RmsModelTemplate = build_underexc_lim_i_e_e_e1_template(
        vfactory=VarFactory(),
        name='UnderexcLimIEEE1_composition',
        parameters=UnderexcLimIEEE1Parameters(kuf=0.5),
    )

    composite_template, unsupported_ports = compose_machine_with_underexc_lim_i_e_e_e1(
        machine_template=machine_template,
        exciter_template=exciter_template,
        limiter_template=limiter_template,
        stabilizer_template=stabilizer_template,
    )

    assert composite_template is not None, unsupported_ports
    assert unsupported_ports == tuple()
    stabilizing_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VfPu_{limiter_template.name}',
    )
    if with_stabilizer:
        assert stabilizer_template is not None
        assert stabilizing_input is None
        pss_output: Var | None = find_block_variable_by_name(
            composite_template.block,
            f'VsPu_{stabilizer_template.name}',
        )
        assert pss_output is not None
        equation_variables: set[str] = set()
        runtime_block: Block
        runtime_equation: Expr
        for runtime_block in composite_template.block.get_all_blocks():
            for runtime_equation in runtime_block.algebraic_eqs:
                for equation_variable in runtime_equation.get_vars():
                    equation_variables.add(equation_variable.name)
                else:
                    pass
            else:
                pass
        else:
            pass
        assert pss_output.name in equation_variables
        assert all(
            variable.name != f'VfPu_{limiter_template.name}'
            for variable in composite_template.block.in_vars
        )
    else:
        assert stabilizing_input is not None
        assert stabilizing_input in composite_template.block.in_vars


def test_gov_gast3_temperature_error_uses_diagram_polarity() -> None:
    """Check the EA968 thermal summer computes measured temperature minus one.

    :return: None.
    """
    template: RmsModelTemplate = build_gov_g_a_s_t3_template(VarFactory())
    temperature_integrator: Var = find_block_variable_by_name(
        template.block, 'TemperatureControllerIntegralPu_GovGAST3'
    )
    derivative_index: int = template.block.state_vars.index(temperature_integrator)
    temperature_derivative: Expr = template.block.state_eqs[derivative_index]
    assert isinstance(temperature_derivative, BinOp)
    assert temperature_derivative.op == '+'
    assert isinstance(temperature_derivative.left, BinOp)
    assert temperature_derivative.left.op == '*'
    assert isinstance(temperature_derivative.left.right, BinOp)
    assert temperature_derivative.left.right.op == '/'
    assert isinstance(temperature_derivative.left.right.left, BinOp)
    assert temperature_derivative.left.right.left.op == '-'
    assert isinstance(temperature_derivative.left.right.left.left, Var)
    assert temperature_derivative.left.right.left.left.name == 'ExhaustTemperaturePu_GovGAST3'
    assert isinstance(temperature_derivative.left.right.left.right, Const)
    assert temperature_derivative.left.right.left.right.value == 1.0
    thermal_fraction: float = 390.0 * (1.0 - 0.23) / 540.0
    exhaust_temperature: float = (1.0 - thermal_fraction) * thermal_fraction * 0.5
    assert temperature_derivative.eval(
        TemperatureControllerIntegralPu_GovGAST3=0.0,
        ExhaustTemperaturePu_GovGAST3=exhaust_temperature,
        **{'GovGAST3.tt_GovGAST3': 250.0},
    ) == 0.0
    assert temperature_derivative.eval(
        TemperatureControllerIntegralPu_GovGAST3=0.0,
        ExhaustTemperaturePu_GovGAST3=1.5,
        **{'GovGAST3.tt_GovGAST3': 250.0},
    ) == 0.002

    acceleration_state: Var = find_block_variable_by_name(
        template.block, 'AccelerationFuelReductionPu_GovGAST3'
    )
    acceleration_derivative_index: int = template.block.state_vars.index(acceleration_state)
    acceleration_derivative: Expr = template.block.state_eqs[acceleration_derivative_index]
    assert acceleration_derivative.eval(
        AccelerationFuelReductionPu_GovGAST3=0.0,
        OmegaDerivativePu_GovGAST3=0.0,
        **{'GovGAST3.bca_GovGAST3': 0.01, 'GovGAST3.kca_GovGAST3': 100.0},
    ) == 0.0
    assert acceleration_derivative.eval(
        AccelerationFuelReductionPu_GovGAST3=0.0,
        OmegaDerivativePu_GovGAST3=0.02,
        **{'GovGAST3.bca_GovGAST3': 0.01, 'GovGAST3.kca_GovGAST3': 100.0},
    ) == 1.0

    governor_state: Var = find_block_variable_by_name(
        template.block, 'GovernorIntegratorPu_GovGAST3'
    )
    governor_derivative_index: int = template.block.state_vars.index(governor_state)
    governor_derivative: Expr = template.block.state_eqs[governor_derivative_index]
    assert isclose(
        governor_derivative.eval(**{
            'PRefPu_GovGAST3': 0.5,
            'OmegaPu_GovGAST3': 0.99,
            'GovernorIntegratorPu_GovGAST3': 0.5,
            'GovGAST3.bp_GovGAST3': 0.05,
            'GovGAST3.mnef_GovGAST3': -0.05,
            'GovGAST3.mxef_GovGAST3': 0.05,
            'GovGAST3.tg_GovGAST3': 0.05,
        }),
        1.0,
        abs_tol=1e-12,
    )

    turbine_flow: Var = find_block_variable_by_name(
        template.block, 'TurbineFuelFlowPu_GovGAST3'
    )
    turbine_flow_derivative_index: int = template.block.state_vars.index(turbine_flow)
    turbine_flow_derivative: Expr = template.block.state_eqs[turbine_flow_derivative_index]
    assert isclose(
        turbine_flow_derivative.eval(**{
            'FuelControlPu_GovGAST3': 0.8,
            'TurbineFuelFlowPu_GovGAST3': 0.5,
            'GovGAST3.tc_GovGAST3': 0.2,
        }),
        1.5,
        abs_tol=1e-12,
    )


@pytest.mark.parametrize(
    ('generator_power', 'fuel_feedback_gain', 'zero_time_stages'),
    ((50.0, 0.0, False), (70.0, 0.1, False), (60.0, 0.05, True)),
)
def test_gov_gast3_initializes_at_its_temperature_limited_operating_point(
        generator_power: float,
        fuel_feedback_gain: float,
        zero_time_stages: bool,
) -> None:
    """Check the canonical thermal lower stop and machine-base power reference.

    :param generator_power: Generator active power in MW.
    :param fuel_feedback_gain: Fuel-system feedback gain.
    :param zero_time_stages: Whether to reduce five lag stages to algebraic paths.
    :return: None.
    """
    governor: GovGAST3 = GovGAST3(rdfid='_gov_gast3_initialization')
    governor.kac = fuel_feedback_gain
    if zero_time_stages:
        governor.ty = 0.0
        governor.tac = 0.0
        governor.tc = 0.0
        governor.tsi = 0.0
        governor.ttc = 0.0
    else:
        pass
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_gov_gast3_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_gast3_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovGAST3'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gov_gast3_bus')
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='gov_gast3_generator',
        P=generator_power,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    template: RmsModelTemplate | None = generator.rms_template
    assert template is not None
    assert 'GovGAST3' in template.name
    assert not any('GovGAST3' in entry.msg for entry in logger.entries)
    reference_port: Var | None = find_block_variable_by_name(
        template.block,
        f'PRefPu_GovGAST3_{governor.uuid}',
    )
    temperature_integrator: Var | None = find_block_variable_by_name(
        template.block,
        f'TemperatureControllerIntegralPu_GovGAST3_{governor.uuid}',
    )
    acceleration_integrator: Var | None = find_block_variable_by_name(
        template.block,
        f'AccelerationFuelReductionPu_GovGAST3_{governor.uuid}',
    )
    assert reference_port is not None
    assert temperature_integrator is not None
    assert acceleration_integrator is not None
    assert find_block_variable_by_name(
        template.block,
        f'OmegaPu_GovGAST3_{governor.uuid}',
    ) is None
    assert find_block_variable_by_name(
        template.block,
        f'OmegaDerivativePu_GovGAST3_{governor.uuid}',
    ) is None
    machine_speed_derivative: Var | None = find_block_variable_by_name(
        template.block,
        'OmegaDerivativePu',
    )
    assert machine_speed_derivative is not None
    reference_initial: Expr | Const | None = find_block_initial_value(template.block, reference_port)
    temperature_initial: Expr | Const | None = find_block_initial_value(
        template.block, temperature_integrator,
    )
    acceleration_initial: Expr | Const | None = find_block_initial_value(
        template.block, acceleration_integrator,
    )
    assert isinstance(reference_initial, Const)
    assert isinstance(temperature_initial, Const)
    assert isinstance(acceleration_initial, Const)
    assert reference_initial.value == (
        (1.0 + fuel_feedback_gain) * generator_power / machine.ratedS
    )
    assert temperature_initial.value == 0.0
    assert acceleration_initial.value == 0.0
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: generator_power / veragrid_model.Sbase,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
def assert_zero_initial_residuals(
        template: RmsModelTemplate,
        power_flow_values: dict[VarPowerFlowReferenceType, float],
        parameter_values: dict[Var, Const] | None = None,
        expected_state_derivatives: dict[str, float] | None = None,
) -> None:
    """Evaluate the initial DAE residual at a supplied power-flow point.

    :param template: Composed dynamic template to evaluate.
    :param power_flow_values: Solved values for external power-flow ports.
    :param parameter_values: Device-backed static initial values resolved by the RMS mapper.
    :param expected_state_derivatives: Source-supported nonzero transient derivatives by state name.
    :return: None.
    """
    runtime_blocks: list[Block] = template.block.get_all_blocks()
    initial_values: dict[int, float | complex] = dict()
    if parameter_values is not None:
        for parameter_variable, parameter_value in parameter_values.items():
            if isinstance(parameter_value.value, (int, float, complex)):
                initial_values[parameter_variable.uid] = parameter_value.value
            else:
                pass
    else:
        pass
    initial_equations: list[tuple[Var, Expr]] = list()
    for runtime_block in runtime_blocks:
        for mode_variable, mode_value in runtime_block.mode_dict.items():
            if isinstance(mode_value, Const) and isinstance(mode_value.value, (int, float)):
                initial_values[mode_variable.uid] = mode_value.value
            else:
                pass
        for variable, value in runtime_block.event_dict.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_values[variable.uid] = value.value
            elif isinstance(value, Expr) and not isinstance(value, Const):
                initial_equations.append((variable, value))
            else:
                pass
        for variable, value in runtime_block.parameters.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_values[variable.uid] = value.value
            else:
                pass
        for reference, variable in runtime_block.external_mapping.items():
            reference_value: float | None = power_flow_values.get(reference, None)
            if reference_value is None:
                pass
            else:
                initial_values[variable.uid] = reference_value
        # Solved power-flow ports override template fallback initial equations.
        external_variable_uids: set[int] = set(
            variable.uid for variable in runtime_block.external_mapping.values()
        )
        for variable, value in runtime_block.init_eqs.items():
            if variable.uid not in external_variable_uids:
                initial_equations.append((variable, value))
            else:
                pass
        initial_equations.extend(runtime_block.diff_init_eqs.items())
        for equation in runtime_block.algebraic_eqs:
            if (
                    isinstance(equation, BinOp)
                    and equation.op == "-"
                    and isinstance(equation.left, Var)
                    and equation.left in runtime_block.algebraic_vars
                    and equation.left not in runtime_block.init_eqs
            ):
                initial_equations.append((equation.left, equation.right))
            else:
                pass

    for variable, _ in initial_equations:
        initial_values.pop(variable.uid, None)
    pending_equations: list[tuple[Var, Expr]] = initial_equations
    while len(pending_equations) > 0:
        unresolved_equations: list[tuple[Var, Expr]] = list()
        progress: bool = False
        for variable, equation in pending_equations:
            dependencies: list[Var] = equation.get_vars()
            if all(dependency.uid in initial_values for dependency in dependencies):
                initial_values[variable.uid] = eval_uid(equation, initial_values)
                progress = True
            else:
                unresolved_equations.append((variable, equation))
        pending_equations = unresolved_equations
        if progress:
            pass
        else:
            derivative_values_added: bool = False
            for runtime_block in runtime_blocks:
                for derivative, equation in zip(runtime_block.diff_vars, runtime_block.state_eqs):
                    dependencies = equation.get_vars()
                    if (
                            derivative.uid not in initial_values
                            and all(dependency.uid in initial_values for dependency in dependencies)
                    ):
                        initial_values[derivative.uid] = eval_uid(equation, initial_values)
                        derivative_values_added = True
                    else:
                        pass
            if derivative_values_added:
                pass
            else:
                break

        # Resolve derivative outputs after their machine and governor states are initialized.
        pending_derivatives: list[tuple[Var, Expr]] = list()
        for runtime_block in runtime_blocks:
            for derivative, equation in zip(runtime_block.diff_vars, runtime_block.state_eqs):
                pending_derivatives.append((derivative, equation))
        while len(pending_derivatives) > 0:
            unresolved_derivatives: list[tuple[Var, Expr]] = list()
            derivative_values_added: bool = False
            for derivative, equation in pending_derivatives:
                dependencies: list[Var] = equation.get_vars()
                if (
                        derivative.uid not in initial_values
                        and all(dependency.uid in initial_values for dependency in dependencies)
                ):
                    initial_values[derivative.uid] = eval_uid(equation, initial_values)
                    derivative_values_added = True
                else:
                    unresolved_derivatives.append((derivative, equation))
            if derivative_values_added:
                pending_derivatives = unresolved_derivatives
            else:
                break

    unresolved_initializations: list[tuple[str, list[str]]] = list()
    for variable, equation in pending_equations:
        unresolved_dependencies: list[str] = list()
        for dependency in equation.get_vars():
            if dependency.uid not in initial_values:
                unresolved_dependencies.append(dependency.name)
            else:
                pass
        unresolved_initializations.append((variable.name, unresolved_dependencies))
    assert not unresolved_initializations, unresolved_initializations
    for runtime_block in runtime_blocks:
        for state_index, equation in enumerate(runtime_block.state_eqs):
            missing_variables: list[str] = list()
            for equation_variable in equation.get_vars():
                if equation_variable.uid not in initial_values:
                    missing_variables.append(equation_variable.name)
                else:
                    pass
            assert len(missing_variables) == 0, (runtime_block.name, missing_variables, equation)
            state_derivative: float = eval_uid(equation, initial_values)
            state_variable: Var = runtime_block.state_vars[state_index]
            if expected_state_derivatives is None:
                expected_derivative: float = 0.0
            else:
                expected_derivative = expected_state_derivatives.get(state_variable.name, 0.0)
            assert isclose(state_derivative, expected_derivative, abs_tol=1e-8), (
                runtime_block.name,
                state_variable.name,
                equation,
                state_derivative,
                expected_derivative,
                {
                    variable.name: initial_values[variable.uid]
                    for variable in equation.get_vars()
                },
            )
        for equation in runtime_block.algebraic_eqs:
            missing_variables: list[str] = list()
            for equation_variable in equation.get_vars():
                if equation_variable.uid not in initial_values:
                    missing_variables.append(equation_variable.name)
                else:
                    pass
            assert len(missing_variables) == 0, (runtime_block.name, missing_variables, equation)
            residual = abs(eval_uid(equation, initial_values))
            assert isclose(residual, 0.0, abs_tol=1e-8), (
                runtime_block.name,
                equation,
                residual,
                tuple(
                    (
                        variable.name,
                        initial_values[variable.uid],
                        tuple(
                            (candidate.name, str(seed))
                            for candidate, seed in runtime_block.init_eqs.items()
                            if candidate == variable
                        ),
                    )
                    for variable in equation.get_vars()
                ),
            )


def test_exc_sk_rate_limiter_initializes_from_machine_reactive_power() -> None:
    """Seed ExcSK's Q slew state on its own base at the solved machine point.

    :return: None.
    """
    machine_factory: VarFactory = VarFactory()
    machine_template: RmsModelTemplate = RmsModelTemplate(name='ExcSK_machine')
    machine_template.block = Block(name='ExcSK_machine')
    machine_initial_values: tuple[tuple[str, float], ...] = (
        ('Vm', 1.0),
        ('EfdPu', 1.1),
        ('IfdPu', 0.2),
        ('Qg', 0.25),
        ('Tm', 0.5),
        ('omega', 1.0),
    )
    machine_variables: dict[str, Var] = dict()
    for variable_name, initial_value in machine_initial_values:
        machine_variable: Var = machine_factory.add_var(variable_name)
        machine_variables[variable_name] = machine_variable
        machine_template.block.out_vars.append(machine_variable)
        machine_template.block.init_eqs[machine_variable] = Const(initial_value)
    else:
        pass

    exciter_name: str = 'ExcSK_rate_limit_check'
    exciter_template: RmsModelTemplate = build_exc_s_k_template(
        vfactory=VarFactory(),
        name=exciter_name,
        parameters=ExcSKParameters(sbase=125.0, kqob=0.05),
    )
    reactive_power_state: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'ReactivePowerRateLimitedPu_{exciter_name}',
    )
    assert reactive_power_state is not None
    composite_template: RmsModelTemplate | None = compose_detailed_machine_with_exc_sk(
        machine_template=machine_template,
        exciter_template=exciter_template,
        system_base_mva=200.0,
    )
    assert composite_template is not None

    initial_values: dict[int, float | complex] = dict()
    for runtime_block in composite_template.block.get_all_blocks():
        for variable, value in runtime_block.event_dict.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_values[variable.uid] = value.value
            else:
                pass
    else:
        pass
    initial_equation: Expr | None = find_block_initial_value(
        composite_template.block,
        reactive_power_state,
    )
    assert initial_equation is not None
    for variable_name, initial_value in machine_initial_values:
        initial_values[machine_variables[variable_name].uid] = initial_value
    else:
        pass
    reactive_power_initial: float = eval_uid(initial_equation, initial_values)
    assert isclose(reactive_power_initial, 0.4, abs_tol=1e-12)
    initial_values[reactive_power_state.uid] = reactive_power_initial

    rate_limit_block: Block | None = None
    for runtime_block in composite_template.block.get_all_blocks():
        if reactive_power_state in runtime_block.state_vars:
            rate_limit_block = runtime_block
        else:
            pass
    else:
        pass
    assert rate_limit_block is not None
    state_index: int = rate_limit_block.state_vars.index(reactive_power_state)
    rate_derivative: Expr = rate_limit_block.state_eqs[state_index]
    assert isclose(eval_uid(rate_derivative, initial_values), 0.0, abs_tol=1e-12)


@pytest.mark.parametrize(
    ('field_current', 'expected_field_voltage'),
    (
        (0.2, 1.0 - 0.577 * 0.2),
        (0.6, (0.75 - 0.6 ** 2) ** 0.5),
        (0.9, 1.732 * (1.0 - 0.9)),
        (0.433, 1.0 - 0.577 * 0.433),
        (0.75, (0.75 - 0.75 ** 2) ** 0.5),
    ),
)
def test_exc_sk_rectifier_characteristic_regions(
        field_current: float,
        expected_field_voltage: float,
) -> None:
    """Check each sourced ExcSK rectifier segment and its inclusive breakpoints.

    :param field_current: Current ratio with unit Ve and KCE.
    :param expected_field_voltage: Sourced rectifier output for that region.
    :return: None.
    """
    field_voltage: Expr = exc_sk_rectifier_output(
        field_voltage=Const(1.0),
        field_current=Const(field_current),
        kce=Const(1.0),
    )
    assert isclose(eval_uid(field_voltage, dict()), expected_field_voltage, abs_tol=1e-12)


@pytest.mark.parametrize('current_ratio', (0.2, 0.433, 0.6, 0.75, 0.9))
@pytest.mark.parametrize('regulator_integral_time', (0.0, 0.25))
@pytest.mark.parametrize('uel_integral_time', (0.0, 0.1))
def test_exc_sk_composed_field_state_inverts_rectifier(
        current_ratio: float,
        regulator_integral_time: float,
        uel_integral_time: float,
) -> None:
    """Seed the composed ExcSK state from a machine field operating point.

    :param current_ratio: Normalized current in one rectifier segment or boundary.
    :param regulator_integral_time: Zero-time or dynamic regulator-integral selection.
    :param uel_integral_time: Zero-time or dynamic UEL integrator selection.
    :return: None.
    """
    expected_field_voltage: float = eval_uid(
        exc_sk_rectifier_output(
            field_voltage=Const(1.0),
            field_current=Const(current_ratio),
            kce=Const(1.0),
        ),
        dict(),
    )
    machine_factory: VarFactory = VarFactory()
    machine_template: RmsModelTemplate = RmsModelTemplate(name='ExcSK_rectifier_machine')
    machine_template.block = Block(name='ExcSK_rectifier_machine')
    machine_initial_values: tuple[tuple[str, float], ...] = (
        ('Vm', 1.0),
        ('EfdPu', expected_field_voltage),
        ('IfdPu', current_ratio),
        ('Qg', 0.2),
        ('Tm', 0.5),
        ('omega', 1.0),
    )
    machine_variables: dict[str, Var] = dict()
    for variable_name, initial_value in machine_initial_values:
        machine_variable: Var = machine_factory.add_var(variable_name)
        machine_variables[variable_name] = machine_variable
        machine_template.block.out_vars.append(machine_variable)
        machine_template.block.init_eqs[machine_variable] = Const(initial_value)
    else:
        pass

    exciter_name: str = f'ExcSK_inverse_{current_ratio}'
    exciter_template: RmsModelTemplate = build_exc_s_k_template(
        vfactory=VarFactory(),
        name=exciter_name,
        parameters=ExcSKParameters(
            kce=1.0,
            sbase=100.0,
            tc=regulator_integral_time,
            qconoff=True,
            qz=0.2,
            kqp=0.5,
            kqi=0.1,
            k1=0.5,
            k2=0.1,
            kp=2.0,
            ti=uel_integral_time,
            tp=uel_integral_time,
        ),
    )
    exciter_field_state: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'VePu_{exciter_name}',
    )
    exciter_reactive_state: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'ReactivePowerRateLimitedPu_{exciter_name}',
    )
    exciter_uel_error: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'UnderexcitationErrorPu_{exciter_name}',
    )
    exciter_uel_output: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'UnderexcitationOutputPu_{exciter_name}',
    )
    exciter_uel_integral: Var | None = find_block_variable_by_name(
        exciter_template.block,
        f'UnderexcitationIntegralPu_{exciter_name}',
    )
    assert (
        exciter_field_state is not None
        and exciter_reactive_state is not None
        and exciter_uel_error is not None
        and exciter_uel_output is not None
    )
    composite_template: RmsModelTemplate | None = compose_detailed_machine_with_exc_sk(
        machine_template=machine_template,
        exciter_template=exciter_template,
        system_base_mva=100.0,
    )
    assert composite_template is not None
    field_state_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        exciter_field_state,
    )
    assert field_state_initial is not None
    initial_values: dict[int, float | complex] = dict()
    for runtime_block in composite_template.block.get_all_blocks():
        for variable, value in runtime_block.event_dict.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_values[variable.uid] = value.value
            else:
                pass
    else:
        pass
    for variable_name, initial_value in machine_initial_values:
        initial_values[machine_variables[variable_name].uid] = initial_value
    else:
        pass
    initial_values[exciter_reactive_state.uid] = 0.2

    field_state_value: float = eval_uid(field_state_initial, initial_values)
    assert isclose(field_state_value, 1.0, abs_tol=1e-10)
    uel_error_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        exciter_uel_error,
    )
    uel_output_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        exciter_uel_output,
    )
    assert uel_error_initial is not None and uel_output_initial is not None
    assert isclose(eval_uid(uel_error_initial, initial_values), 0.15, abs_tol=1e-12)
    assert isclose(eval_uid(uel_output_initial, initial_values), 0.3, abs_tol=1e-12)
    reconstructed_output: float = eval_uid(
        exc_sk_rectifier_output(
            field_voltage=Const(field_state_value),
            field_current=Const(current_ratio),
            kce=Const(1.0),
        ),
        dict(),
    )
    assert isclose(reconstructed_output, expected_field_voltage, abs_tol=1e-10)
    if uel_integral_time > 0.0:
        assert exciter_uel_integral is not None
        assert_zero_initial_residuals(
            composite_template,
            dict(),
            expected_state_derivatives={
                exciter_uel_integral.name: 0.15 / uel_integral_time,
            },
        )
    else:
        assert_zero_initial_residuals(composite_template, dict())


@pytest.mark.parametrize(
    'voltage, active_power, reactive_power',
    ((1.0, 0.5, -0.2), (0.95, 0.7, -0.1), (1.05, 0.2, -0.3)),
)
def test_underexc_lim_ieee2_initial_measurement_residual(
        voltage: float,
        active_power: float,
        reactive_power: float,
) -> None:
    """Check UEL2 sourced measurement and table states at nonzero terminal voltage.

    :param voltage: Nonzero terminal voltage for the literal IEEE normalization.
    :param active_power: Active-power input within the documented table range.
    :param reactive_power: Reactive-power input for a settled controller point.
    :return: None.
    """
    template_name: str = 'UnderexcLimIEEE2_residual'
    template: RmsModelTemplate = build_underexc_lim_i_e_e_e2_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=UnderexcLimIEEE2Parameters(
            tuv=0.2,
            tup=0.3,
            tuq=0.4,
            kui=0.0,
            points=(
                (0.0, -0.31), (0.3, -0.31), (0.6, -0.28), (0.9, -0.21), (1.02, 0.0),
                (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0),
            ),
        ),
    )
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: voltage,
            VarPowerFlowReferenceType.P: active_power,
            VarPowerFlowReferenceType.Q: reactive_power,
        },
    )


@pytest.mark.parametrize(
    "model_kind",
    (
        StaticLoadModelKind.exponential,
        StaticLoadModelKind.zIP1,
        StaticLoadModelKind.zIP2,
        StaticLoadModelKind.constantZ,
    ),
)
def test_load_static_equations_cover_each_cgmes_variant(
        model_kind: StaticLoadModelKind,
) -> None:
    """Retain executable P/Q equations and exact CGMES parameter events per variant.

    :param model_kind: CGMES static-load model kind under check.
    :return: None.
    """
    cgmes_object: LoadStatic = LoadStatic(rdfid=f"_load_static_{model_kind.name}")
    cgmes_object.kp1 = 0.2
    cgmes_object.kp2 = 0.3
    cgmes_object.kp3 = 0.4
    cgmes_object.kp4 = 0.1
    cgmes_object.ep1 = 2.0
    cgmes_object.ep2 = 1.0
    cgmes_object.ep3 = 0.0
    cgmes_object.kpf = 0.5
    cgmes_object.kq1 = 0.2
    cgmes_object.kq2 = 0.3
    cgmes_object.kq3 = 0.4
    cgmes_object.kq4 = 0.1
    cgmes_object.eq1 = 2.0
    cgmes_object.eq2 = 1.0
    cgmes_object.eq3 = 0.0
    cgmes_object.kqf = 0.25
    variable_factory: VarFactory = VarFactory()
    template_name: str = f"LoadStatic_{model_kind.name}"
    template: RmsModelTemplate = build_load_static_template(
        vfactory=variable_factory,
        name=template_name,
        model_kind=model_kind,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    block.unify_blocks()
    equation_variables: set[str] = set(
        variable.name
        for equation in block.algebraic_eqs
        for variable in equation.get_vars()
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )

    assert len(block.in_vars) == 2
    assert len(block.out_vars) == 2
    assert len(block.algebraic_eqs) == 2
    assert "P" in equation_variables
    assert "Q" in equation_variables
    assert event_values[f"LoadStatic.kp4_{template_name}"].value == 0.1
    assert event_values[f"LoadStatic.kqf_{template_name}"].value == 0.25
    parameter_values: tuple[tuple[str, float], ...] = (
        ("kp1", 0.2), ("kp2", 0.3), ("kp3", 0.4), ("kp4", 0.1),
        ("ep1", 2.0), ("ep2", 1.0), ("ep3", 0.0), ("kpf", 0.5),
        ("kq1", 0.2), ("kq2", 0.3), ("kq3", 0.4), ("kq4", 0.1),
        ("eq1", 2.0), ("eq2", 1.0), ("eq3", 0.0), ("kqf", 0.25),
    )
    for parameter_name, expected_value in parameter_values:
        assert event_values[
            f"LoadStatic.{parameter_name}_{template_name}"
        ].value == expected_value
    assert block.external_mapping


def test_exc_ieee_ac1a_equations_use_imported_parameters() -> None:
    """Keep zero-time topology, saturation, and RDF event mapping executable.

    :return: None.
    """
    cgmes_object: ExcIEEEAC1A = ExcIEEEAC1A(rdfid="_exc_ieee_ac1a_check")
    cgmes_object.tb = 0.0
    cgmes_object.tc = 0.0
    cgmes_object.ka = 321.0
    cgmes_object.ve1 = 4.2
    cgmes_object.seve1 = 0.12

    settings: ExcIEEEAC1AParameters = get_exc_ieee_ac1a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = "ExcIEEEAC1A_check"
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c1_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    saturation_variables: set[str] = set(
        variable.name for variable in block.state_eqs[2].get_vars()
    )

    assert "ExcIEEEAC1A" in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 3
    assert len(block.state_eqs) == 3
    assert len(block.algebraic_eqs) == 5
    assert len(block.event_dict) == 37
    assert event_values["KA_" + template_name].value == 321.0
    assert event_values["VE1_" + template_name].value == 4.2
    assert event_values["SEVE1_" + template_name].value == 0.12
    assert "SEVE1_" + template_name in saturation_variables


def test_exc_ieee_ac1a_zero_saturation_curve_is_defined() -> None:
    """Keep the explicitly disabled saturation curve numerically defined.

    :return: None.
    """
    parameters: ExcIEEEAC1AParameters = ExcIEEEAC1AParameters(
        seve1=0.0,
        seve2=0.0,
    )
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c1_a_template(
        vfactory=VarFactory(),
        name="ExcIEEEAC1A_zero_saturation_check",
        parameters=parameters,
    )

    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 5
    assert len(template.block.event_dict) == 37


def test_exc_ieee_ac2a_equations_and_rdf_mapping() -> None:
    """Check AC2A state equations, imports, and all canonical scalar settings.

    :return: None.
    """
    cgmes_object: ExcIEEEAC2A = ExcIEEEAC2A(rdfid='_exc_ieee_ac2a_equation_check')
    cgmes_object.ka = 321.0
    cgmes_object.kb = 24.0
    cgmes_object.kh = 1.2
    cgmes_object.vfemax = 4.0
    cgmes_object.ve1 = 4.2
    cgmes_object.seve1 = 0.12
    cgmes_object.ve2 = 3.2
    cgmes_object.seve2 = 0.03

    settings: ExcIEEEAC2AParameters = get_exc_ieee_ac2a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC2A_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c2_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    exciter_state: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    assert exciter_state is not None
    exciter_state_index: int = block.state_vars.index(exciter_state)
    exciter_derivative: Expr = block.state_eqs[exciter_state_index]
    derivative_variables: set[str] = set(variable.name for variable in exciter_derivative.get_vars())
    regulator_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(
        find_block_variable_by_name(block, f'SecondRegulatorPu_{template_name}')
    )]
    regulator_variables: set[str] = set(variable.name for variable in regulator_equation.get_vars())

    assert 'ExcIEEEAC2A' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 3
    assert len(block.state_eqs) == 3
    assert len(block.event_dict) == 43
    assert 'KB_' + template_name in regulator_variables
    assert 'KH_' + template_name in regulator_variables
    assert 'VFEMAX_' + template_name in derivative_variables
    assert 'SEVE1_' + template_name in derivative_variables
    assert 'VE1_' + template_name in derivative_variables
    assert event_values['KA_' + template_name].value == 321.0
    assert event_values['KB_' + template_name].value == 24.0
    assert event_values['KH_' + template_name].value == 1.2
    assert event_values['ExcIEEEAC2A.vfemax_' + template_name].value == 4.0


def test_exc_ieee_ac2a_connects_to_detailed_machine_and_initializes_field_voltage() -> None:
    """Bind AC2A to its associated generator and transfer the machine Efd seed.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac2a_bus')
    exciter: ExcIEEEAC2A = ExcIEEEAC2A(rdfid='_detailed_ac2a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac2a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    machine_field_current: Var | None = find_block_variable_by_name(composite_template.block, 'IfdPu')
    exciter_field_current: Var | None = find_block_variable_by_name(
        composite_template.block, f'IfdPu_ExcIEEEAC2A_{exciter.uuid}',
    )
    exciter_terminal_voltage: Var | None = find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEAC2A_{exciter.uuid}',
    )
    exciter_field_voltage: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC2A_{exciter.uuid}',
    )
    exciter_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'VePu_ExcIEEEAC2A_{exciter.uuid}',
    )
    assert machine_field_current is not None
    assert exciter_field_current is None
    assert exciter_terminal_voltage is None
    assert exciter_field_voltage is not None
    assert exciter_state is not None
    assert find_block_initial_value(composite_template.block, exciter_state) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_ac3a_equations_and_rdf_mapping() -> None:
    """Check AC3A self-excitation, piecewise feedback, and canonical scalar mapping.

    :return: None.
    """
    cgmes_object: ExcIEEEAC3A = ExcIEEEAC3A(rdfid='_exc_ieee_ac3a_equation_check')
    cgmes_object.ka = 37.0
    cgmes_object.kr = 3.5
    cgmes_object.kf = 0.14
    cgmes_object.kn = 0.06
    cgmes_object.efdn = 2.2
    cgmes_object.vemin = 0.08
    cgmes_object.vfemax = 15.0

    settings: ExcIEEEAC3AParameters = get_exc_ieee_ac3a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC3A_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c3_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    field_state: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    assert field_state is not None
    field_equation: Expr = block.state_eqs[block.state_vars.index(field_state)]
    field_variables: set[str] = set(variable.name for variable in field_equation.get_vars())
    feedback_equation: Expr | None = None
    feedback_variables: set[str] = set()
    feedback_state: Var | None = find_block_variable_by_name(
        block, f'FeedbackPuMemory_{template_name}',
    )
    assert feedback_state is not None
    for state_index, state in enumerate(block.state_vars):
        if state == feedback_state:
            feedback_equation = block.state_eqs[state_index]
        else:
            pass
    if feedback_equation is not None:
        feedback_variables = set(variable.name for variable in feedback_equation.get_vars())
    else:
        pass

    assert 'ExcIEEEAC3A' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 3
    assert len(block.event_dict) == 43
    assert 'KR_' + template_name in field_variables
    assert 'VFEMAX_' + template_name in field_variables
    assert 'SEVE1_' + template_name in field_variables
    assert 'VE1_' + template_name in field_variables
    assert 'KF_' + template_name in feedback_variables
    assert 'KN_' + template_name in feedback_variables
    assert 'EFDN_' + template_name in feedback_variables
    assert event_values['ExcIEEEAC3A.ka_' + template_name].value == 37.0
    assert event_values['ExcIEEEAC3A.kr_' + template_name].value == 3.5
    assert event_values['ExcIEEEAC3A.vemin_' + template_name].value == 0.08
    assert event_values['ExcIEEEAC3A.vfemax_' + template_name].value == 15.0


def test_exc_ieee_ac3a_association_connects_machine_signals() -> None:
    """Compose AC3A with its RDF-linked detailed machine and Efd operating point.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac3a_bus')
    exciter: ExcIEEEAC3A = ExcIEEEAC3A(rdfid='_detailed_ac3a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac3a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac3a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert find_block_variable_by_name(
        composite_template.block, f'IfdPu_ExcIEEEAC3A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEAC3A_{exciter.uuid}',
    ) is None
    exciter_field_voltage: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC3A_{exciter.uuid}',
    )
    exciter_field_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'VePu_ExcIEEEAC3A_{exciter.uuid}',
    )
    assert exciter_field_voltage is not None
    assert exciter_field_state is not None
    assert find_block_initial_value(composite_template.block, exciter_field_state) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_ac4a_equations_and_rdf_mapping() -> None:
    """Check AC4A lead-lag, loading compensation, and every RDF scalar mapping.

    :return: None.
    """
    cgmes_object: ExcIEEEAC4A = ExcIEEEAC4A(rdfid='_exc_ieee_ac4a_equation_check')
    cgmes_object.vimax = 8.0
    cgmes_object.vimin = -7.0
    cgmes_object.tc = 0.8
    cgmes_object.tb = 4.0
    cgmes_object.ka = 180.0
    cgmes_object.ta = 0.02
    cgmes_object.vrmax = 5.5
    cgmes_object.vrmin = -4.5
    cgmes_object.kc = 0.25

    settings: ExcIEEEAC4AParameters = get_exc_ieee_ac4a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC4A_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c4_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    regulator_state: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    assert regulator_state is not None
    regulator_index: int = block.state_vars.index(regulator_state)
    regulator_variables: set[str] = set(
        variable.name for variable in block.state_eqs[regulator_index].get_vars()
    )

    assert 'ExcIEEEAC4A' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 2
    assert len(block.event_dict) == 19
    assert 'KC_' + template_name in regulator_variables
    assert 'IfdPu_' + template_name in regulator_variables
    assert event_values['ExcIEEEAC4A.vimax_' + template_name].value == 8.0
    assert event_values['ExcIEEEAC4A.vrmin_' + template_name].value == -4.5
    assert event_values['ExcIEEEAC4A.kc_' + template_name].value == 0.25


def test_exc_ieee_ac4a_import_composes_with_its_detailed_machine() -> None:
    """Attach AC4A through its RDF machine link and close voltage/Ifd/Efd ports.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac4a_bus')
    exciter: ExcIEEEAC4A = ExcIEEEAC4A(rdfid='_detailed_ac4a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac4a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac4a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac4a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC4A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEAC4A.')
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert find_block_variable_by_name(
        composite_template.block, f'IfdPu_ExcIEEEAC4A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEAC4A_{exciter.uuid}',
    ) is None
    exciter_field_output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC4A_{exciter.uuid}',
    )
    assert exciter_field_output is not None
    assert find_block_initial_value(
        composite_template.block,
        exciter_field_output,
    ) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_ac5a_equations_and_rdf_mapping() -> None:
    """Check AC5A stabilizer, exciter saturation, and all canonical RDF values.

    :return: None.
    """
    cgmes_object: ExcIEEEAC5A = ExcIEEEAC5A(rdfid='_exc_ieee_ac5a_equation_check')
    cgmes_object.ka = 360.0
    cgmes_object.kf = 0.04
    cgmes_object.tf1 = 0.9
    cgmes_object.tf2 = 1.1
    cgmes_object.tf3 = 0.25
    cgmes_object.efd1 = 5.2
    cgmes_object.seefd1 = 0.82
    cgmes_object.efd2 = 4.1
    cgmes_object.seefd2 = 0.46

    settings: ExcIEEEAC5AParameters = get_exc_ieee_ac5a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC5A_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c5_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    voltage_error: Var | None = find_block_variable_by_name(block, f'VoltageErrorPu_{template_name}')
    exciter_state: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    assert voltage_error is not None
    assert exciter_state is not None
    voltage_error_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(voltage_error)]
    voltage_error_variables: set[str] = set(
        variable.name for variable in voltage_error_equation.get_vars()
    )
    exciter_equation: Expr = block.state_eqs[block.state_vars.index(exciter_state)]
    exciter_variables: set[str] = set(variable.name for variable in exciter_equation.get_vars())

    assert 'ExcIEEEAC5A' in get_international_model_builders()
    assert len(block.in_vars) == 3
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 4
    assert len(block.state_eqs) == 4
    assert len(block.event_dict) == 29
    assert 'KF_' + template_name in voltage_error_variables
    assert 'TF3_' + template_name in voltage_error_variables
    assert 'KE_' + template_name in exciter_variables
    assert 'SEefd1_' + template_name in exciter_variables
    assert event_values['ExcIEEEAC5A.ka_' + template_name].value == 360.0
    assert event_values['ExcIEEEAC5A.tf3_' + template_name].value == 0.25
    assert event_values['ExcIEEEAC5A.seefd1_' + template_name].value == 0.82


def test_exc_ieee_ac5a_import_composes_and_seeds_machine_field_voltage() -> None:
    """Compose AC5A with the linked detailed machine and transfer its Efd seed.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac5a_bus')
    exciter: ExcIEEEAC5A = ExcIEEEAC5A(rdfid='_detailed_ac5a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac5a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac5a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac5a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC5A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEAC5A.')
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEAC5A_{exciter.uuid}',
    ) is None
    exciter_output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC5A_{exciter.uuid}',
    )
    exciter_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'VePu_ExcIEEEAC5A_{exciter.uuid}',
    )
    assert exciter_output is not None
    assert exciter_state is not None
    assert find_block_initial_value(composite_template.block, exciter_output) is not None
    assert find_block_initial_value(composite_template.block, exciter_state) is not None
    regulator_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'RegulatorPu_ExcIEEEAC5A_{exciter.uuid}',
    )
    first_feedback_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'FeedbackFirstMemoryPu_ExcIEEEAC5A_{exciter.uuid}',
    )
    second_feedback_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'FeedbackSecondMemoryPu_ExcIEEEAC5A_{exciter.uuid}',
    )
    reference_port: Var | None = find_block_variable_by_name(
        composite_template.block, f'UsRefPu_ExcIEEEAC5A_{exciter.uuid}',
    )
    assert regulator_state is not None
    assert first_feedback_state is not None
    assert second_feedback_state is not None
    assert reference_port is not None
    assert find_block_initial_value(composite_template.block, regulator_state) is not None
    assert find_block_initial_value(composite_template.block, first_feedback_state) is not None
    assert find_block_initial_value(composite_template.block, second_feedback_state) is not None
    assert find_block_initial_value(composite_template.block, reference_port) is not None
    assert find_block_variable_by_name(
        composite_template.block, f'OmegaPu_ExcIEEEAC5A_{exciter.uuid}',
    ) is None
    assert generator.rms_template is composite_template
    standalone_machine: RmsModelTemplate | None = None
    for runtime_template in veragrid_model.rms_models:
        if (
                runtime_template.device is generator
                and runtime_template.name.startswith('SynchronousMachineTimeConstantReactance_')
                and '_with_' not in runtime_template.name
        ):
            standalone_machine = runtime_template
        else:
            pass
    assert standalone_machine is not None
    standalone_field_voltage: Var | None = find_block_variable_by_name(
        standalone_machine.block,
        'EfdPu',
    )
    assert standalone_field_voltage is not None
    standalone_field_voltage_initial: Expr | Const | None = find_block_initial_value(
        standalone_machine.block,
        standalone_field_voltage,
    )
    exciter_output_initial: Expr | Const | None = None
    exciter_runtime_block: Block
    for exciter_runtime_block in composite_template.block.get_all_blocks():
        if exciter_output in exciter_runtime_block.out_vars:
            exciter_output_initial = exciter_runtime_block.init_eqs.get(exciter_output, None)
        else:
            pass
    assert standalone_field_voltage_initial is not None
    assert exciter_output_initial is not None
    assert str(exciter_output_initial) == str(standalone_field_voltage_initial)
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_ac6a_equations_and_rdf_mapping() -> None:
    """Check AC6A limiter, rectifier equations, and all canonical RDF values.

    :return: None.
    """
    cgmes_object: ExcIEEEAC6A = ExcIEEEAC6A(rdfid='_exc_ieee_ac6a_equation_check')
    cgmes_object.ka = 420.0
    cgmes_object.tk = 0.16
    cgmes_object.tb = 8.0
    cgmes_object.tc = 2.5
    cgmes_object.kh = 80.0
    cgmes_object.vfelim = 18.0
    cgmes_object.kc = 0.19
    cgmes_object.ve1 = 7.1
    cgmes_object.seve1 = 0.22
    cgmes_object.ve2 = 5.2
    cgmes_object.seve2 = 0.05

    settings: ExcIEEEAC6AParameters = get_exc_ieee_ac6a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC6A_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c6_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=settings,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    exciter_state: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    field_voltage: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    field_current: Var | None = find_block_variable_by_name(block, f'IfdPu_{template_name}')
    assert exciter_state is not None
    assert field_voltage is not None
    assert field_current is not None
    field_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(field_voltage)]
    field_equation_variables: set[str] = set(variable.name for variable in field_equation.get_vars())
    state_equation: Expr = block.state_eqs[block.state_vars.index(exciter_state)]
    state_equation_variables: set[str] = set(variable.name for variable in state_equation.get_vars())
    limiter_output: Var | None = find_block_variable_by_name(
        block, f'FieldLimiterOutputPu_{template_name}',
    )
    assert limiter_output is not None
    limiter_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(limiter_output)]
    limiter_variables: set[str] = set(variable.name for variable in limiter_equation.get_vars())
    limiter_filter: Var | None = find_block_variable_by_name(
        block, f'FieldLimiterPuState_{template_name}',
    )
    assert limiter_filter is not None
    limiter_state_equation: Expr = block.state_eqs[block.state_vars.index(limiter_filter)]
    limiter_state_variables: set[str] = set(
        variable.name for variable in limiter_state_equation.get_vars()
    )

    assert 'ExcIEEEAC6A' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert 'OmegaPu_' + template_name in field_equation_variables
    assert 'KC_' + template_name in field_equation_variables
    assert 'KH_' + template_name in limiter_variables
    assert 'VFELIM_' + template_name in limiter_state_variables
    assert len([name for name in event_values if name.startswith('ExcIEEEAC6A.')]) == 23
    assert event_values['ExcIEEEAC6A.ka_' + template_name].value == 420.0
    assert event_values['ExcIEEEAC6A.vfelim_' + template_name].value == 18.0
    assert event_values['ExcIEEEAC6A.seve2_' + template_name].value == 0.05


def test_exc_ieee_ac6a_import_composes_with_detailed_machine() -> None:
    """Bind IEEE AC6A ports and copy its field-voltage operating-point seed.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac6a_bus')
    exciter: ExcIEEEAC6A = ExcIEEEAC6A(rdfid='_detailed_ac6a_exciter')
    exciter.vfelim = 5.239950092630077
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac6a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac6a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac6a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC6A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)
    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEAC6A.')
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    for expected_absent_name in (
            f'UsPu_ExcIEEEAC6A_{exciter.uuid}',
            f'OmegaPu_ExcIEEEAC6A_{exciter.uuid}',
            f'IfdPu_ExcIEEEAC6A_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, expected_absent_name) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC6A_{exciter.uuid}',
    )
    assert output is not None
    standalone_machine: RmsModelTemplate | None = None
    for runtime_template in veragrid_model.rms_models:
        if (
                runtime_template.device is generator
                and runtime_template.name.startswith('SynchronousMachineTimeConstantReactance_')
                and '_with_' not in runtime_template.name
        ):
            standalone_machine = runtime_template
        else:
            pass
    assert standalone_machine is not None
    machine_output: Var | None = find_block_variable_by_name(standalone_machine.block, 'EfdPu')
    assert machine_output is not None
    machine_seed: Expr | Const | None = find_block_initial_value(standalone_machine.block, machine_output)
    output_seed: Expr | Const | None = None
    for runtime_block in composite_template.block.get_all_blocks():
        if output in runtime_block.out_vars:
            output_seed = runtime_block.init_eqs.get(output, None)
        else:
            pass
    assert machine_seed is not None
    assert output_seed is not None
    assert str(output_seed) == str(machine_seed)
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_ac7b_equations_and_rdf_mapping() -> None:
    """Check AC7B cascaded regulators and its exact numeric RDF mapping.

    :return: None.
    """
    cgmes_object: ExcIEEEAC7B = ExcIEEEAC7B(rdfid='_exc_ieee_ac7b_equation_check')
    cgmes_object.kpr = 5.1
    cgmes_object.kir = 4.6
    cgmes_object.kdr = 2.0
    cgmes_object.tdr = 0.2
    cgmes_object.kpa = 62.0
    cgmes_object.kia = 55.0
    cgmes_object.kp = 3.5
    cgmes_object.kl = 8.0
    cgmes_object.kf1 = 0.19
    cgmes_object.kf2 = 0.07
    cgmes_object.kf3 = 0.03
    cgmes_object.tf = 1.3
    cgmes_object.ve1 = 6.0
    cgmes_object.seve1 = 0.4
    cgmes_object.ve2 = 3.0
    cgmes_object.seve2 = 0.07

    settings: ExcIEEEAC7BParameters = get_exc_ieee_ac7b_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC7B_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c7_b_template(
        variable_factory,
        template_name,
        settings,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    voltage_error: Var | None = find_block_variable_by_name(
        block, f'VoltageErrorPu_{template_name}',
    )
    voltage_pid: Var | None = find_block_variable_by_name(block, f'VoltagePIDPu_{template_name}')
    field_pi: Var | None = find_block_variable_by_name(block, f'FieldPIPu_{template_name}')
    derivative_memory: Var | None = find_block_variable_by_name(
        block, f'DerivativeMemoryPu_{template_name}',
    )
    exciter_state: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    equivalent_field: Var | None = find_block_variable_by_name(block, f'VfePu_{template_name}')
    delivered_field: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    assert voltage_error is not None
    assert voltage_pid is not None
    assert field_pi is not None
    assert derivative_memory is not None
    assert exciter_state is not None
    assert equivalent_field is not None
    assert delivered_field is not None
    error_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(voltage_error)]
    error_variables: set[str] = set(variable.name for variable in error_equation.get_vars())
    winding_equation: Expr = block.state_eqs[block.state_vars.index(exciter_state)]
    winding_variables: set[str] = set(variable.name for variable in winding_equation.get_vars())
    delivered_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(delivered_field)]
    delivered_variables: set[str] = set(variable.name for variable in delivered_equation.get_vars())

    assert 'ExcIEEEAC7B' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert voltage_pid in block.algebraic_vars
    assert field_pi in block.algebraic_vars
    assert f'KF1_{template_name}' in error_variables
    assert f'KF2_{template_name}' in error_variables
    assert f'KF3_{template_name}' in error_variables
    derivative_equation: Expr = block.state_eqs[block.state_vars.index(derivative_memory)]
    derivative_variables: set[str] = set(
        variable.name for variable in derivative_equation.get_vars()
    )
    assert f'TDR_{template_name}' in derivative_variables
    assert f'KL_{template_name}' in winding_variables
    assert f'VFEMAX_{template_name}' in winding_variables
    assert f'KC_{template_name}' in delivered_variables
    assert len([name for name in event_values if name.startswith('ExcIEEEAC7B.')]) == 27
    assert event_values[f'ExcIEEEAC7B.kpr_{template_name}'].value == 5.1
    assert event_values[f'ExcIEEEAC7B.kdr_{template_name}'].value == 2.0
    assert event_values[f'ExcIEEEAC7B.tdr_{template_name}'].value == 0.2
    assert event_values[f'ExcIEEEAC7B.kp_{template_name}'].value == 3.5
    assert event_values[f'ExcIEEEAC7B.seve2_{template_name}'].value == 0.07


def test_exc_ieee_ac7b_import_composes_with_detailed_machine() -> None:
    """Bind AC7B terminal voltage, field current, and machine Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac7b_bus')
    exciter: ExcIEEEAC7B = ExcIEEEAC7B(rdfid='_detailed_ac7b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac7b_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac7b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac7b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC7B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEAC7B.')
    for open_port in (
            f'UsPu_ExcIEEEAC7B_{exciter.uuid}',
            f'IfdPu_ExcIEEEAC7B_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, open_port) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC7B_{exciter.uuid}',
    )
    assert output is not None
    assert find_block_initial_value(composite_template.block, output) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )
def test_exc_ieee_ac8b_equations_and_rdf_mapping() -> None:
    """Check the canonical AC8B PID, winding, rectifier, and RDF fields.

    :return: None.
    """
    cgmes_object: ExcIEEEAC8B = ExcIEEEAC8B(rdfid='_exc_ieee_ac8b_equation_check')
    cgmes_object.kpr = 82.0
    cgmes_object.kir = 5.5
    cgmes_object.kdr = 9.0
    cgmes_object.tdr = 0.15
    cgmes_object.vrmax = 34.0
    cgmes_object.vrmin = -1.0
    cgmes_object.ka = 2.0
    cgmes_object.ta = 0.2
    cgmes_object.te = 1.4
    cgmes_object.vfemax = 5.8
    cgmes_object.vemin = 0.1
    cgmes_object.ke = 1.1
    cgmes_object.kc = 0.5
    cgmes_object.kd = 0.9
    cgmes_object.ve1 = 6.5
    cgmes_object.seve1 = 0.3
    cgmes_object.ve2 = 9.0
    cgmes_object.seve2 = 3.0

    settings: ExcIEEEAC8BParameters = get_exc_ieee_ac8b_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEAC8B_equation_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_a_c8_b_template(
        variable_factory, template_name, settings,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    pid_error: Var | None = find_block_variable_by_name(
        block, f'VoltageErrorPu_{template_name}',
    )
    winding: Var | None = find_block_variable_by_name(block, f'VePu_{template_name}')
    delivered_field: Var | None = find_block_variable_by_name(
        block, f'EfdPu_{template_name}',
    )
    derivative_memory: Var | None = find_block_variable_by_name(
        block, f'DerivativeMemoryPu_{template_name}',
    )
    regulator: Var | None = find_block_variable_by_name(
        block, f'RegulatorPu_{template_name}',
    )
    assert pid_error is not None
    assert winding is not None
    assert delivered_field is not None
    assert derivative_memory is not None
    assert regulator is not None
    error_names: set[str] = set(
        variable.name
        for variable in block.algebraic_eqs[block.algebraic_vars.index(pid_error)].get_vars()
    )
    winding_names: set[str] = set(
        variable.name for variable in block.state_eqs[block.state_vars.index(winding)].get_vars()
    )
    assert 'ExcIEEEAC8B' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    regulator_names: set[str] = set(
        variable.name for variable in block.state_eqs[
            block.state_vars.index(regulator)
        ].get_vars()
    )
    assert f'KDR_{template_name}' in regulator_names
    assert f'KC_{template_name}' in set(
        variable.name for variable in block.algebraic_eqs[
            block.algebraic_vars.index(delivered_field)
        ].get_vars()
    )
    assert f'KD_{template_name}' in winding_names
    assert f'VFEMAX_{template_name}' in winding_names
    assert 'UpssPu_' + template_name in error_names
    assert len([name for name in event_values if name.startswith('ExcIEEEAC8B.')]) == 19
    assert event_values[f'ExcIEEEAC8B.kpr_{template_name}'].value == 82.0
    assert event_values[f'ExcIEEEAC8B.tdr_{template_name}'].value == 0.15
    assert event_values[f'ExcIEEEAC8B.seve2_{template_name}'].value == 3.0

    zero_saturation: RmsModelTemplate = build_exc_i_e_e_e_a_c8_b_template(
        VarFactory(),
        'ExcIEEEAC8B_zero_saturation',
        ExcIEEEAC8BParameters(kdr=0.0, seve1=0.0, seve2=0.0),
    )
    zero_saturation_state: Var | None = find_block_variable_by_name(
        zero_saturation.block, 'VePu_ExcIEEEAC8B_zero_saturation',
    )
    assert zero_saturation_state is not None
    zero_saturation_equation: Expr = zero_saturation.block.state_eqs[
        zero_saturation.block.state_vars.index(zero_saturation_state)
    ]
    zero_saturation_names: set[str] = set(
        variable.name for variable in zero_saturation_equation.get_vars()
    )
    assert 'SEVE1_ExcIEEEAC8B_zero_saturation' not in zero_saturation_names
    assert 'DerivativeMemoryPu_ExcIEEEAC8B_zero_saturation' not in zero_saturation_names
    with pytest.raises(ValueError, match='saturation samples must both be zero or positive'):
        build_exc_i_e_e_e_a_c8_b_template(
            VarFactory(),
            'ExcIEEEAC8B_invalid_saturation',
            ExcIEEEAC8BParameters(seve1=0.0, seve2=1.0),
        )


def test_exc_ieee_ac8b_import_composes_with_detailed_machine() -> None:
    """Attach AC8B by its RDF machine association and bind machine ports.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac8b_bus')
    exciter: ExcIEEEAC8B = ExcIEEEAC8B(rdfid='_detailed_ac8b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ac8b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac8b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac8b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC8B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEAC8B.')
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEAC8B_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'IfdPu_ExcIEEEAC8B_{exciter.uuid}',
    ) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEAC8B_{exciter.uuid}',
    )
    assert output is not None
    assert find_block_initial_value(composite_template.block, output) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_dc1a_equations_selectors_and_rdf_mapping() -> None:
    """Check IEEE DC1A UEL selector, speed path, stops, and canonical fields.

    :return: None.
    """
    cgmes_object: ExcIEEEDC1A = ExcIEEEDC1A(rdfid='_exc_ieee_dc1a_equation_check')
    cgmes_object.ka = 48.0
    cgmes_object.ta = 0.08
    cgmes_object.tb = 0.2
    cgmes_object.tc = 0.1
    cgmes_object.vrmax = 1.1
    cgmes_object.vrmin = -0.8
    cgmes_object.ke = 0.2
    cgmes_object.te = 0.5
    cgmes_object.kf = 0.12
    cgmes_object.tf = 1.2
    cgmes_object.efd1 = 3.1
    cgmes_object.seefd1 = 0.33
    cgmes_object.efd2 = 2.3
    cgmes_object.seefd2 = 0.1
    cgmes_object.uelin = True
    cgmes_object.exclim = True

    parameters: ExcIEEEDC1AParameters = get_exc_ieee_dc1a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEDC1A_equation_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_d_c1_a_template(
        variable_factory, template_name, parameters,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    state: Var | None = find_block_variable_by_name(
        block, f'ExciterVoltagePu_{template_name}',
    )
    regulator_state: Var | None = find_block_variable_by_name(
        block, f'RegulatorOutputPu_{template_name}',
    )
    output: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    assert state is not None
    assert regulator_state is not None
    assert output is not None
    state_equation: Expr = block.state_eqs[block.state_vars.index(state)]
    output_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(output)]
    state_names: set[str] = set(variable.name for variable in state_equation.get_vars())
    regulator_names: set[str] = set(
        variable.name
        for variable in block.state_eqs[block.state_vars.index(regulator_state)].get_vars()
    )
    output_names: set[str] = set(variable.name for variable in output_equation.get_vars())
    assert 'ExcIEEEDC1A' in get_international_model_builders()
    assert len(block.in_vars) == 5
    assert len(block.out_vars) == 1
    assert f'VuelPu_{template_name}' in state_names
    assert f'KF_{template_name}' in regulator_names
    assert f'SEefd1_{template_name}' in state_names
    assert f'OmegaPu_{template_name}' in output_names
    assert len([name for name in event_values if name.startswith('ExcIEEEDC1A.')]) == 17
    assert event_values[f'ExcIEEEDC1A.ka_{template_name}'].value == 48.0
    assert event_values[f'ExcIEEEDC1A.uelin_{template_name}'].value == 1.0
    assert event_values[f'ExcIEEEDC1A.exclim_{template_name}'].value == 1.0

    direct_uel_template: RmsModelTemplate = build_exc_i_e_e_e_d_c1_a_template(
        VarFactory(),
        'ExcIEEEDC1A_direct_uel',
        ExcIEEEDC1AParameters(uelin=False),
    )
    direct_uel_state: Var | None = find_block_variable_by_name(
        direct_uel_template.block, 'RegulatorOutputPu_ExcIEEEDC1A_direct_uel',
    )
    assert direct_uel_state is not None
    direct_uel_names: set[str] = set(
        variable.name
        for variable in direct_uel_template.block.state_eqs[
            direct_uel_template.block.state_vars.index(direct_uel_state)
        ].get_vars()
    )
    assert 'VuelPu_ExcIEEEDC1A_direct_uel' in direct_uel_names


def test_exc_ieee_dc1a_import_composes_with_detailed_machine() -> None:
    """Bind DC1A terminal voltage, shaft speed, and Efd to its machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_dc1a_bus')
    exciter: ExcIEEEDC1A = ExcIEEEDC1A(rdfid='_detailed_ieee_dc1a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_dc1a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_dc1a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_dc1a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEDC1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEDC1A.')
    for open_port in (
            f'UsPu_ExcIEEEDC1A_{exciter.uuid}',
            f'OmegaPu_ExcIEEEDC1A_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, open_port) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEDC1A_{exciter.uuid}',
    )
    assert output is not None
    assert find_block_initial_value(composite_template.block, output) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_dc2a_equations_and_rdf_mapping() -> None:
    """Check DC2A terminal-scaled limits and its numeric EXCLIM RDF field.

    :return: None.
    """
    cgmes_object: ExcIEEEDC2A = ExcIEEEDC2A(rdfid='_exc_ieee_dc2a_equation_check')
    cgmes_object.efd1 = 3.0
    cgmes_object.efd2 = 2.2
    cgmes_object.exclim = 0.25
    cgmes_object.ka = 305.0
    cgmes_object.ke = 0.9
    cgmes_object.kf = 0.11
    cgmes_object.seefd1 = 0.28
    cgmes_object.seefd2 = 0.12
    cgmes_object.ta = 0.02
    cgmes_object.tb = 0.0
    cgmes_object.tc = 0.0
    cgmes_object.te = 1.4
    cgmes_object.tf = 0.7
    cgmes_object.uelin = True
    cgmes_object.vrmax = 5.0
    cgmes_object.vrmin = -4.8

    settings: ExcIEEEDC2AParameters = get_exc_ieee_dc2a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEDC2A_equation_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_d_c2_a_template(
        variable_factory, template_name, settings,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    field_state: Var | None = find_block_variable_by_name(
        block, f'ExciterVoltagePu_{template_name}',
    )
    regulator_state: Var | None = find_block_variable_by_name(
        block, f'RegulatorOutputPu_{template_name}',
    )
    output: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    assert field_state is not None
    assert regulator_state is not None
    assert output is not None
    field_equation: Expr = block.state_eqs[block.state_vars.index(field_state)]
    regulator_equation: Expr = block.state_eqs[block.state_vars.index(regulator_state)]
    output_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(output)]
    field_names: set[str] = set(variable.name for variable in field_equation.get_vars())
    regulator_names: set[str] = set(variable.name for variable in regulator_equation.get_vars())
    output_names: set[str] = set(variable.name for variable in output_equation.get_vars())
    assert 'ExcIEEEDC2A' in get_international_model_builders()
    assert len(block.in_vars) == 5
    assert len(block.out_vars) == 1
    assert f'EXCLIM_{template_name}' in field_names
    assert f'VuelPu_{template_name}' in field_names
    assert f'UsPu_{template_name}' in regulator_names
    assert f'VRMAX_{template_name}' in regulator_names
    assert f'OmegaPu_{template_name}' in output_names
    assert len([name for name in event_values if name.startswith('ExcIEEEDC2A.')]) == 17
    assert event_values[f'ExcIEEEDC2A.exclim_{template_name}'].value == 0.25
    assert event_values[f'ExcIEEEDC2A.uelin_{template_name}'].value == 1.0

    no_limit_template: RmsModelTemplate = build_exc_i_e_e_e_d_c2_a_template(
        VarFactory(),
        'ExcIEEEDC2A_no_field_stop',
        ExcIEEEDC2AParameters(exclim=-999.0),
    )
    no_limit_state: Var | None = find_block_variable_by_name(
        no_limit_template.block, 'ExciterVoltagePu_ExcIEEEDC2A_no_field_stop',
    )
    assert no_limit_state is not None
    no_limit_equation: Expr = no_limit_template.block.state_eqs[
        no_limit_template.block.state_vars.index(no_limit_state)
    ]
    no_limit_names: set[str] = set(
        variable.name for variable in no_limit_equation.get_vars()
    )
    assert 'EXCLIM_ExcIEEEDC2A_no_field_stop' not in no_limit_names


def test_exc_ieee_dc2a_import_composes_with_detailed_machine() -> None:
    """Bind DC2A terminal voltage, shaft speed, and Efd to its machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_dc2a_bus')
    exciter: ExcIEEEDC2A = ExcIEEEDC2A(rdfid='_detailed_ieee_dc2a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_dc2a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_dc2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_dc2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEDC2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEDC2A.')
    for open_port in (
            f'UsPu_ExcIEEEDC2A_{exciter.uuid}',
            f'OmegaPu_ExcIEEEDC2A_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, open_port) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEDC2A_{exciter.uuid}',
    )
    assert output is not None
    assert find_block_initial_value(composite_template.block, output) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_dc3a_rheostat_equations_and_rdf_mapping() -> None:
    """Check the IEEE DC3A continuous rheostat and fast-contact equations.

    :return: None.
    """
    cgmes_object: ExcIEEEDC3A = ExcIEEEDC3A(rdfid='_exc_ieee_dc3a_equation_check')
    cgmes_object.trh = 22.0
    cgmes_object.kv = 0.06
    cgmes_object.vrmax = 1.2
    cgmes_object.vrmin = -0.1
    cgmes_object.te = 0.6
    cgmes_object.ke = 0.07
    cgmes_object.efd1 = 3.4
    cgmes_object.seefd1 = 0.26
    cgmes_object.efd2 = 3.2
    cgmes_object.seefd2 = 0.07
    cgmes_object.exclim = True

    settings: ExcIEEEDC3AParameters = get_exc_ieee_dc3a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcIEEEDC3A_equation_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_d_c3_a_template(
        variable_factory, template_name, settings,
    )
    copy_cgmes_parameters(cgmes_object, template, variable_factory)
    block: Block = template.block
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in block.event_dict.items()
    )
    rheostat: Var | None = find_block_variable_by_name(block, f'RheostatPu_{template_name}')
    field: Var | None = find_block_variable_by_name(
        block, f'ExciterVoltagePu_{template_name}',
    )
    output: Var | None = find_block_variable_by_name(block, f'EfdPu_{template_name}')
    assert rheostat is not None
    assert field is not None
    assert output is not None
    rheostat_names: set[str] = set(
        variable.name for variable in block.state_eqs[block.state_vars.index(rheostat)].get_vars()
    )
    field_names: set[str] = set(
        variable.name for variable in block.state_eqs[block.state_vars.index(field)].get_vars()
    )
    output_names: set[str] = set(
        variable.name
        for variable in block.algebraic_eqs[block.algebraic_vars.index(output)].get_vars()
    )
    assert 'ExcIEEEDC3A' in get_international_model_builders()
    assert len(block.in_vars) == 4
    assert len(block.out_vars) == 1
    assert f'TRH_{template_name}' in rheostat_names
    assert f'KV_{template_name}' in rheostat_names
    assert f'VRMAX_{template_name}' in rheostat_names
    assert f'EXCLIM_{template_name}' not in field_names
    assert f'SEefd1_{template_name}' in field_names
    assert f'OmegaPu_{template_name}' in output_names
    assert len([name for name in event_values if name.startswith('ExcIEEEDC3A.')]) == 12
    assert event_values[f'ExcIEEEDC3A.trh_{template_name}'].value == 22.0
    assert event_values[f'ExcIEEEDC3A.exclim_{template_name}'].value == 1.0
    assert all('.kr_' not in name and '.ks_' not in name for name in event_values)


def test_exc_ieee_dc4b_equations_and_rdf_mapping() -> None:
    """Check DC4B canonical values, PID states, and gate-selector branches.

    :return: None.
    """
    cgmes_object: ExcIEEEDC4B = ExcIEEEDC4B(rdfid='_exc_ieee_dc4b_check')
    cgmes_object.ka = 1.3
    cgmes_object.ta = 0.18
    cgmes_object.kp = 18.0
    cgmes_object.ki = 16.0
    cgmes_object.kd = 0.2
    cgmes_object.td = 0.03
    cgmes_object.vrmax = 2.5
    cgmes_object.vrmin = -0.8
    cgmes_object.ke = 0.9
    cgmes_object.te = 0.7
    cgmes_object.kf = 0.04
    cgmes_object.tf = 1.2
    cgmes_object.efd1 = 1.7
    cgmes_object.seefd1 = 0.07
    cgmes_object.efd2 = 2.4
    cgmes_object.seefd2 = 0.25
    cgmes_object.vemin = 0.05
    cgmes_object.oelin = False
    cgmes_object.uelin = True

    settings: ExcIEEEDC4BParameters = get_exc_ieee_dc4b_parameters(cgmes_object)
    assert settings.ka == 1.3
    assert settings.kp == 18.0
    assert settings.oelin is False
    assert settings.uelin is True
    factory: VarFactory = VarFactory()
    name: str = 'ExcIEEEDC4B_equation_check'
    template: RmsModelTemplate = build_exc_i_e_e_e_d_c4_b_template(
        vfactory=factory,
        name=name,
        parameters=settings,
    )
    block: Block = template.block
    event_names: set[str] = set(variable.name for variable in block.event_dict)
    field: Var | None = find_block_variable_by_name(block, f'EfdPu_{name}')
    demand: Var | None = find_block_variable_by_name(block, f'DemandPu_{name}')
    error: Var | None = find_block_variable_by_name(block, f'ErrorPu_{name}')
    assert field is not None
    assert demand is not None
    assert error is not None
    assert len(block.in_vars) == 6
    assert len(block.out_vars) == 3
    assert len(block.state_vars) == 5
    assert f'ExcIEEEDC4B.oelin_{name}' in event_names
    assert f'ExcIEEEDC4B.uelin_{name}' in event_names
    assert any(variable.name == f'UelPu_{name}' for variable in block.in_vars)
    assert any(variable.name == f'OelPu_{name}' for variable in block.in_vars)
    error_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(error)]
    assert f'(0.0) - (OelPu_{name})' in str(error_equation)
    assert 'ExcIEEEDC4B' in get_international_model_builders()


def test_exc_ieee_st1a_equations_map_fields_and_preserve_selector_branches() -> None:
    """Check all ST1A UEL positions and the PSS selector location.

    :return: None.
    """
    cgmes_object: ExcIEEEST1A = ExcIEEEST1A(rdfid='_exc_ieee_st1a_check')
    cgmes_object.ilr = 0.2
    cgmes_object.ka = 175.0
    cgmes_object.kc = 0.09
    cgmes_object.kf = 0.04
    cgmes_object.klr = 0.3
    cgmes_object.pssin = False
    cgmes_object.ta = 0.0
    cgmes_object.tb = 8.0
    cgmes_object.tb1 = 0.5
    cgmes_object.tc = 0.8
    cgmes_object.tc1 = 0.1
    cgmes_object.tf = 1.2
    cgmes_object.vamax = 12.0
    cgmes_object.vamin = -12.0
    cgmes_object.vimax = 15.0
    cgmes_object.vimin = -15.0
    cgmes_object.vrmax = 7.0
    cgmes_object.vrmin = -6.0
    cgmes_object.uelin = ExcIEEEST1AUELselectorKind.inputHVgateErrorSignal
    settings: ExcIEEEST1AParameters = get_exc_ieee_st1a_parameters(cgmes_object)
    assert settings.ka == 175.0
    assert settings.pssin is False
    assert settings.uelin == ExcIEEEST1AUELselectorKind.inputHVgateErrorSignal

    for pss_input_at_error in (False, True):
        settings.pssin = pss_input_at_error
        for selector in ExcIEEEST1AUELselectorKind:
            settings.uelin = selector
            factory: VarFactory = VarFactory()
            name: str = f'ExcIEEEST1A_{selector.name}_{pss_input_at_error}'
            template: RmsModelTemplate = build_exc_i_e_e_e_s_t1_a_template(
                vfactory=factory,
                name=name,
                parameters=settings,
            )
            block: Block = template.block
            error: Var | None = find_block_variable_by_name(block, f'RegulatorInputPu_{name}')
            regulator: Var | None = find_block_variable_by_name(block, f'RegulatorOutputPu_{name}')
            field_voltage: Var | None = find_block_variable_by_name(block, f'EfdPu_{name}')
            assert error is not None
            assert regulator is not None
            assert field_voltage is not None
            error_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(error)]
            regulator_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(regulator)]
            field_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(field_voltage)]
            error_text: str = str(error_equation)
            regulator_text: str = str(regulator_equation)
            field_text: str = str(field_equation)
            if selector == ExcIEEEST1AUELselectorKind.ignoreUELsignal:
                assert 'UelPu_' not in error_text + regulator_text + field_text
            elif selector == ExcIEEEST1AUELselectorKind.inputAddedToErrorSignal:
                assert f'UelPu_{name}' in error_text
            elif selector == ExcIEEEST1AUELselectorKind.inputHVgateErrorSignal:
                assert f'UelPu_{name}' in error_text
            else:
                assert f'UelPu_{name}' in field_text
            if pss_input_at_error:
                assert f'UpssPu_{name}' in error_text
            else:
                assert f'UpssPu_{name}' in regulator_text
            assert len([v for v in block.event_dict if v.name.startswith('ExcIEEEST1A.')]) == 20
            assert 'ExcIEEEST1A' in get_international_model_builders()


def test_exc_ieee_st1a_import_composes_with_detailed_machine() -> None:
    """Bind ST1A terminal voltage, field current, and Efd to its generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st1a_bus')
    exciter: ExcIEEEST1A = ExcIEEEST1A(rdfid='_detailed_ieee_st1a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st1a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st1a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_st1a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEST1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'with ExcIEEEST1A_' in composite_template.comment
    assert composite_template.comment.endswith('voltage and field-current feedback.')
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEST1A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'IfdPu_ExcIEEEST1A_{exciter.uuid}',
    ) is None
    field: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEST1A_{exciter.uuid}',
    )
    assert field is not None
    assert find_block_initial_value(composite_template.block, field) is not None
    assert generator.rms_template is composite_template
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_ieee1a_signal_composes_with_ieee_st1a() -> None:
    """Connect PSS1A output to the canonical IEEE ST1A input port.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='ieee_st1a_pss_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_ieee_st1a_pss_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_ieee_st1a_pss_machine_dynamics',
    )
    excitation: ExcIEEEST1A = ExcIEEEST1A(rdfid='_ieee_st1a_pss_excitation')
    stabilizer: PssIEEE1A = PssIEEE1A(rdfid='_ieee_st1a_pss_stabilizer')
    stabilizer.inputSignalType = InputSignalKind.rotorSpeed
    generator: Generator = Generator(idtag=machine.uuid, name='ieee_st1a_pss_generator')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcIEEEST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssIEEE1A'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'PssIEEE1A_{stabilizer.uuid}' in composite_template.name
    assert f'ExcIEEEST1A_{excitation.uuid}' in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block, f'UpssPu_ExcIEEEST1A_{excitation.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEST1A_{excitation.uuid}',
    ) is None


def test_exc_ieee_st2a_equations_mapping_and_uel_selector() -> None:
    """Check ST2A compound-source equations, RDF fields, and UEL placement.

    :return: None.
    """
    cgmes_object: ExcIEEEST2A = ExcIEEEST2A(rdfid='_exc_ieee_st2a_check')
    cgmes_object.ka = 125.0
    cgmes_object.ta = 0.12
    cgmes_object.vrmax = 1.1
    cgmes_object.vrmin = -0.1
    cgmes_object.ke = 0.95
    cgmes_object.te = 0.45
    cgmes_object.kf = 0.06
    cgmes_object.tf = 0.9
    cgmes_object.kp = 4.2
    cgmes_object.ki = 7.4
    cgmes_object.kc = 1.7
    cgmes_object.efdmax = 4.0
    cgmes_object.uelin = False
    settings: ExcIEEEST2AParameters = get_exc_ieee_st2a_parameters(cgmes_object)
    assert settings.ka == 125.0
    assert settings.ki == 7.4
    assert settings.uelin is False

    for uelin in (False, True):
        settings.uelin = uelin
        factory: VarFactory = VarFactory()
        name: str = f'ExcIEEEST2A_{uelin}'
        template: RmsModelTemplate = build_exc_i_e_e_e_s_t2_a_template(
            vfactory=factory,
            name=name,
            parameters=settings,
        )
        block: Block = template.block
        field: Var | None = find_block_variable_by_name(block, f'EfdPu_{name}')
        error: Var | None = find_block_variable_by_name(block, f'ErrorPu_{name}')
        assert field is not None
        assert error is not None
        assert f'ExcIEEEST2A.uelin_{name}' in {
            variable.name for variable in block.event_dict
        }
        assert len([v for v in block.event_dict if v.name.startswith('ExcIEEEST2A.')]) == 14
        assert any(variable.name == f'VmPu_{name}' for variable in block.in_vars)
        assert any(variable.name == f'IfdPu_{name}' for variable in block.in_vars)
        assert any(variable.name == f'UelPu_{name}' for variable in block.in_vars)
        field_equation: Expr = block.state_eqs[block.state_vars.index(field)]
        assert f'BridgePu_{name}' in {variable.name for variable in field_equation.get_vars()}
        if uelin:
            assert len(block.out_vars) == 2
        else:
            error_equation: Expr = block.algebraic_eqs[block.algebraic_vars.index(error)]
            assert f'UelPu_{name}' in {variable.name for variable in error_equation.get_vars()}
            assert len(block.out_vars) == 1
    assert 'ExcIEEEST2A' in get_international_model_builders()


def test_exc_ieee_st2a_import_composes_compound_signals_with_machine() -> None:
    """Bind ST2A terminal phasors, stator current, Ifd and Efd to a machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st2a_bus')
    exciter: ExcIEEEST2A = ExcIEEEST2A(rdfid='_detailed_ieee_st2a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st2a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_st2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEST2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEST2A.')
    for open_port in (
            f'VmPu_ExcIEEEST2A_{exciter.uuid}',
            f'VrPu_ExcIEEEST2A_{exciter.uuid}',
            f'ViPu_ExcIEEEST2A_{exciter.uuid}',
            f'IrPu_ExcIEEEST2A_{exciter.uuid}',
            f'IiPu_ExcIEEEST2A_{exciter.uuid}',
            f'IfdPu_ExcIEEEST2A_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, open_port) is None
    assert find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEST2A_{exciter.uuid}',
    ) is not None


def test_exc_ieee_dc3a_import_composes_with_detailed_machine() -> None:
    """Bind DC3A terminal voltage, shaft speed, and Efd to its machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_dc3a_bus')
    exciter: ExcIEEEDC3A = ExcIEEEDC3A(rdfid='_detailed_ieee_dc3a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_dc3a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_dc3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_dc3a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEDC3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEDC3A.')
    for open_port in (
            f'UsPu_ExcIEEEDC3A_{exciter.uuid}',
            f'OmegaPu_ExcIEEEDC3A_{exciter.uuid}',
    ):
        assert find_block_variable_by_name(composite_template.block, open_port) is None
    output: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEDC3A_{exciter.uuid}',
    )
    assert output is not None
    assert find_block_initial_value(composite_template.block, output) is not None
    assert generator.rms_template is composite_template
    reference_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'UsRefPu_ExcIEEEDC3A_{exciter.uuid}',
    )
    assert reference_input is not None
    reference_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        reference_input,
    )
    assert reference_initial is not None, reference_input.name
    assert isinstance(reference_initial, Var), reference_initial
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_dc4b_import_composes_with_detailed_machine() -> None:
    """Bind DC4B sensed/terminal voltage and Efd to its physical generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_dc4b_bus')
    exciter: ExcIEEEDC4B = ExcIEEEDC4B(rdfid='_detailed_ieee_dc4b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_dc4b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_dc4b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_dc4b_generator')
    limiter: UnderexcLimIEEE2 = UnderexcLimIEEE2(rdfid='_detailed_ieee_dc4b_uel2')
    limiter.kui = 0.0
    limiter.kul = 0.0
    limiter.kuf = 0.0
    overexcitation_limiter: OverexcLim2 = OverexcLim2(
        rdfid='_detailed_ieee_dc4b_oel2',
    )
    overexcitation_limiter.koi = 0.0
    overexcitation_limiter.voimax = 10.0
    overexcitation_limiter.voimin = -10.0
    overexcitation_limiter.ifdlim = 1.0
    exciter.SynchronousMachineDynamics = machine_dynamics
    exciter.UnderexcitationLimiterDynamics = limiter
    exciter.OverexcitationLimiterDynamics = overexcitation_limiter
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    limiter.ExcitationSystemDynamics = exciter
    overexcitation_limiter.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEDC4B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['UnderexcLimIEEE2'].append(limiter)
    cgmes_model.dynamics_assets.lists['OverexcLim2'].append(overexcitation_limiter)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_OverexcLim2_' in composite_template.name
    assert '_with_UnderexcLimIEEE2_' in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block, f'UsPu_ExcIEEEDC4B_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block, f'VtPu_ExcIEEEDC4B_{exciter.uuid}',
    ) is None
    field: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcIEEEDC4B_{exciter.uuid}',
    )
    assert field is not None
    assert find_block_initial_value(composite_template.block, field) is not None
    assert generator.rms_template is composite_template


def test_exc_ac1a_equations_and_rdf_mapping() -> None:
    """Check AC1A equations, canonical parameter mapping, and open signal ports.

    :return: None.
    """
    cgmes_object: ExcAC1A = ExcAC1A(rdfid='_exc_ac1a_equation_check')
    cgmes_object.tb = 0.0
    cgmes_object.tc = 0.0
    cgmes_object.ka = 287.0
    cgmes_object.kf1 = 0.2
    cgmes_object.kf2 = 0.8
    cgmes_object.ks = 0.05
    cgmes_object.hvlvgates = True
    parameters: ExcAC1AParameters = get_exc_ac1a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC1A_equation_check'
    template: RmsModelTemplate = build_exc_a_c1_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert parameters.ka == 287.0
    assert parameters.kf1 == 0.2
    assert parameters.kf2 == 0.8
    assert parameters.ks == 0.05

    assert len(template.block.in_vars) == 7
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 5
    assert len(template.block.out_vars) == 1
    restored_block: Block = roundtrip_block(template.block)
    assert len(restored_block.in_vars) == 7
    assert event_values[f'KA_{template_name}'].value == 287.0
    assert event_values[f'KF1_{template_name}'].value == 0.2
    assert event_values[f'KF2_{template_name}'].value == 0.8
    assert event_values[f'KS_{template_name}'].value == 0.05
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
        f'OmegaPu_{template_name}',
        f'VuelPu_{template_name}',
        f'VoelPu_{template_name}',
    }


def test_exc_ac2a_equations_and_rdf_mapping() -> None:
    """Check AC2A equation stages, limiter ports, and canonical RDF mapping.

    :return: None.
    """
    cgmes_object: ExcAC2A = ExcAC2A(rdfid='_exc_ac2a_equation_check')
    cgmes_object.tb = 0.0
    cgmes_object.tc = 0.0
    cgmes_object.ka = 325.0
    cgmes_object.kb = 21.0
    cgmes_object.kb1 = 19.0
    cgmes_object.vfemax = 4.1
    cgmes_object.vlr = 4.2
    cgmes_object.kl = 8.0
    cgmes_object.ks = 0.05
    cgmes_object.hvgate = True
    cgmes_object.lvgate = True
    parameters: ExcAC2AParameters = get_exc_ac2a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC2A_equation_check'
    template: RmsModelTemplate = build_exc_a_c2_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 7
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 5
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 325.0
    assert parameters.kb == 21.0
    assert parameters.kb1 == 19.0
    assert parameters.vfemax == 4.1
    assert parameters.kl == 8.0
    assert event_values[f'KA_{template_name}'].value == 325.0
    assert event_values[f'KB_{template_name}'].value == 21.0
    assert event_values[f'KB1_{template_name}'].value == 19.0
    assert event_values[f'VAMAX_{template_name}'].value == 8.0
    assert event_values[f'VAMIN_{template_name}'].value == -8.0
    assert event_values[f'VE1_{template_name}'].value == 4.4
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
        f'OmegaPu_{template_name}',
        f'VuelPu_{template_name}',
        f'VoelPu_{template_name}',
    }


def test_exc_ac3a_equations_and_rdf_mapping() -> None:
    """Check AC3A feedback, field limits, rectifier, and canonical RDF values.

    :return: None.
    """
    cgmes_object: ExcAC3A = ExcAC3A(rdfid='_exc_ac3a_equation_check')
    cgmes_object.tb = 0.0
    cgmes_object.tc = 0.0
    cgmes_object.ka = 1.2
    cgmes_object.kr = 1.3
    cgmes_object.kf = 0.12
    cgmes_object.kn = 0.08
    cgmes_object.efdn = 2.1
    cgmes_object.kf1 = 0.7
    cgmes_object.kf2 = 0.2
    cgmes_object.ks = 0.05
    cgmes_object.vemin = 0.08
    cgmes_object.vfemax = 12.0
    parameters: ExcAC3AParameters = get_exc_ac3a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC3A_equation_check'
    template: RmsModelTemplate = build_exc_a_c3_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 6
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 4
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 1.2
    assert parameters.kr == 1.3
    assert parameters.efdn == 2.1
    assert parameters.vemin == 0.08
    assert event_values[f'KA_{template_name}'].value == 1.2
    assert event_values[f'KR_{template_name}'].value == 1.3
    assert event_values[f'EFDN_{template_name}'].value == 2.1
    assert event_values[f'VEMIN_{template_name}'].value == 0.08
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
        f'VuelPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_ac4a_equations_and_rdf_mapping() -> None:
    """Check AC4A lead-lag, limiter bounds, and RDF setting conversion.

    :return: None.
    """
    cgmes_object: ExcAC4A = ExcAC4A(rdfid='_exc_ac4a_equation_check')
    cgmes_object.vimax = 8.0
    cgmes_object.vimin = -7.0
    cgmes_object.tb = 5.0
    cgmes_object.tc = 0.5
    cgmes_object.ka = 175.0
    cgmes_object.ta = 0.02
    cgmes_object.vrmax = 5.0
    cgmes_object.vrmin = -4.0
    cgmes_object.kc = 0.12
    parameters: ExcAC4AParameters = get_exc_ac4a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC4A_equation_check'
    template: RmsModelTemplate = build_exc_a_c4_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 5
    assert len(template.block.state_vars) == 2
    assert len(template.block.state_eqs) == 2
    assert len(template.block.algebraic_eqs) == 3
    assert len(template.block.out_vars) == 1
    assert parameters.vimax == 8.0
    assert parameters.ka == 175.0
    assert parameters.kc == 0.12
    assert event_values[f'VIMAX_{template_name}'].value == 8.0
    assert event_values[f'KA_{template_name}'].value == 175.0
    assert event_values[f'KC_{template_name}'].value == 0.12
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
        f'VuelPu_{template_name}',
    }


def test_exc_ac5a_equations_and_rdf_mapping() -> None:
    """Check AC5A feedback states, exciter equations, and RDF settings.

    :return: None.
    """
    cgmes_object: ExcAC5A = ExcAC5A(rdfid='_exc_ac5a_equation_check')
    cgmes_object.ka = 420.0
    cgmes_object.kf = 0.11
    cgmes_object.tf1 = 1.2
    cgmes_object.tf2 = 0.75
    cgmes_object.tf3 = 0.1
    cgmes_object.ks = 0.05
    parameters: ExcAC5AParameters = get_exc_ac5a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC5A_equation_check'
    template: RmsModelTemplate = build_exc_a_c5_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 4
    assert len(template.block.state_eqs) == 4
    assert len(template.block.algebraic_eqs) == 3
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 420.0
    assert parameters.tf1 == 1.2
    assert parameters.tf2 == 0.75
    assert event_values[f'KA_{template_name}'].value == 420.0
    assert event_values[f'TF1_{template_name}'].value == 1.2
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_ac6a_equations_and_rdf_mapping() -> None:
    """Check AC6A cascaded regulation, field limiter, and RDF mapping.

    :return: None.
    """
    cgmes_object: ExcAC6A = ExcAC6A(rdfid='_exc_ac6a_equation_check')
    cgmes_object.ka = 510.0
    cgmes_object.tk = 0.2
    cgmes_object.tb = 8.0
    cgmes_object.tc = 2.5
    cgmes_object.kh = 90.0
    cgmes_object.vfelim = 18.0
    parameters: ExcAC6AParameters = get_exc_ac6a_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC6A_equation_check'
    template: RmsModelTemplate = build_exc_a_c6_a_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 4
    assert len(template.block.state_eqs) == 4
    assert len(template.block.algebraic_eqs) == 6
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 510.0
    assert parameters.tk == 0.2
    assert parameters.vfelim == 18.0
    assert event_values[f'KA_{template_name}'].value == 510.0
    assert event_values[f'KH_{template_name}'].value == 90.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'IfdPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_ac8b_equations_and_rdf_mapping() -> None:
    """Check AC8B PID branches, limit selectors, and canonical RDF mapping.

    :return: None.
    """
    cgmes_object: ExcAC8B = ExcAC8B(rdfid='_exc_ac8b_equation_check')
    cgmes_object.inlim = True
    cgmes_object.pidlim = True
    cgmes_object.telim = True
    cgmes_object.vtmult = True
    cgmes_object.kpr = 82.0
    cgmes_object.kir = 5.5
    cgmes_object.kdr = 11.0
    cgmes_object.tdr = 0.15
    parameters: ExcAC8BParameters = get_exc_ac8b_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcAC8B_equation_check'
    template: RmsModelTemplate = build_exc_a_c8_b_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 7
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 3
    assert len(template.block.out_vars) == 1
    assert parameters.inlim is True
    assert parameters.pidlim is True
    assert parameters.telim is True
    assert parameters.vtmult is True
    assert parameters.kpr == 82.0
    assert event_values[f'KPR_{template_name}'].value == 82.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'VuelPu_{template_name}',
        f'VoelPu_{template_name}',
        f'IfdPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_ans_equations_and_rdf_mapping() -> None:
    """Check both ExcANS regulator selectors, excitation paths, and RDF values.

    :return: None.
    """
    cgmes_object: ExcANS = ExcANS(rdfid='_exc_ans_equation_check')
    cgmes_object.blint = 1
    cgmes_object.kvfif = 1
    cgmes_object.krvecc = 1
    cgmes_object.k3 = 950.0
    cgmes_object.k2 = 18.0
    cgmes_object.t1 = 15.0
    parameters: ExcANSParameters = get_exc_ans_parameters(cgmes_object)
    variable_factory: VarFactory = VarFactory()
    template_name: str = 'ExcANS_equation_check'
    template: RmsModelTemplate = build_exc_a_n_s_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 4
    assert len(template.block.out_vars) == 1
    assert parameters.blint == 1
    assert parameters.kvfif == 1
    assert parameters.krvecc == 1
    assert parameters.k3 == 950.0
    assert event_values[f'K3_{template_name}'].value == 950.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }
    alternate_parameters: ExcANSParameters = ExcANSParameters(blint=0, kvfif=0, krvecc=0)
    alternate_template: RmsModelTemplate = build_exc_a_n_s_template(
        vfactory=VarFactory(),
        name='ExcANS_lead_lag_open_loop_check',
        parameters=alternate_parameters,
    )
    assert len(alternate_template.block.state_vars) == 3
    assert len(alternate_template.block.state_eqs) == 3
    assert len(alternate_template.block.out_vars) == 1


def test_exc_avr1_equations_and_rdf_mapping() -> None:
    """Check AVR1 washout feedback, lead-lag, saturation, and RDF values.

    :return: None.
    """
    cgmes_object: ExcAVR1 = ExcAVR1(rdfid='_exc_avr1_equation_check')
    cgmes_object.ka = 510.0
    cgmes_object.tb = 0.15
    cgmes_object.ta = 0.25
    cgmes_object.kf = 0.04
    parameters: ExcAVR1Parameters = get_exc_avr1_parameters(cgmes_object)
    template_name: str = 'ExcAVR1_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r1_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 510.0
    assert parameters.tb == 0.15
    assert event_values[f'KA_{template_name}'].value == 510.0
    assert f'RegulatorMemoryPu_{template_name}' in {
        variable.name for variable in template.block.state_vars
    }
    moving_limit_equation: str = str(template.block.state_eqs[1])
    assert 'VRMN_' in moving_limit_equation
    assert 'VRMX_' in moving_limit_equation
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }
    zero_time_template: RmsModelTemplate = build_exc_a_v_r1_template(
        vfactory=VarFactory(),
        name='ExcAVR1_zero_time_check',
        parameters=ExcAVR1Parameters(ta=0.0, tb=0.0),
    )
    assert len(zero_time_template.block.state_vars) == 2


def test_exc_avr2_equations_and_rdf_mapping() -> None:
    """Check AVR2 cascaded washout feedback, lead-lag, and RDF settings.

    :return: None.
    """
    cgmes_object: ExcAVR2 = ExcAVR2(rdfid='_exc_avr2_equation_check')
    cgmes_object.ka = 510.0
    cgmes_object.tf1 = 1.2
    cgmes_object.tf2 = 0.8
    parameters: ExcAVR2Parameters = get_exc_avr2_parameters(cgmes_object)
    template_name: str = 'ExcAVR2_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r2_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 4
    assert len(template.block.state_eqs) == 4
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 510.0
    assert parameters.tf1 == 1.2
    assert parameters.tf2 == 0.8
    assert event_values[f'TF1_{template_name}'].value == 1.2
    assert f'RegulatorMemoryPu_{template_name}' in {
        variable.name for variable in template.block.state_vars
    }
    moving_limit_equation = str(template.block.state_eqs[2])
    assert 'VRMN_' in moving_limit_equation
    assert 'VRMX_' in moving_limit_equation
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }
    zero_time_template: RmsModelTemplate = build_exc_a_v_r2_template(
        vfactory=VarFactory(),
        name='ExcAVR2_zero_time_check',
        parameters=ExcAVR2Parameters(ta=0.0, tb=0.0),
    )
    assert len(zero_time_template.block.state_vars) == 3


def test_exc_avr3_equations_and_rdf_mapping() -> None:
    """Check both bounded AVR3 filter stages and canonical parameter values.

    :return: None.
    """
    cgmes_object: ExcAVR3 = ExcAVR3(rdfid='_exc_avr3_equation_check')
    cgmes_object.ka = 2750.0
    cgmes_object.t1 = 200.0
    cgmes_object.t2 = 1.4
    cgmes_object.t3 = 0.7
    cgmes_object.t4 = 0.08
    parameters: ExcAVR3Parameters = get_exc_avr3_parameters(cgmes_object)
    template_name: str = 'ExcAVR3_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r3_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 0
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 2750.0
    assert parameters.t2 == 1.4
    assert parameters.t4 == 0.08
    assert event_values[f'T1_{template_name}'].value == 200.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }


def test_exc_avr4_equations_and_rdf_mapping() -> None:
    """Check AVR4 regulator/current filters, bounds, IMUL, and RDF mapping.

    :return: None.
    """
    cgmes_object: ExcAVR4 = ExcAVR4(rdfid='_exc_avr4_equation_check')
    cgmes_object.ka = 320.0
    cgmes_object.kif = 0.2
    cgmes_object.t1if = 50.0
    cgmes_object.t4 = 0.0
    cgmes_object.imul = True
    parameters: ExcAVR4Parameters = get_exc_avr4_parameters(cgmes_object)
    template_name: str = 'ExcAVR4_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r4_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 2
    assert len(template.block.state_eqs) == 2
    assert len(template.block.algebraic_eqs) == 3
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 320.0
    assert parameters.imul is True
    assert event_values[f'T1IF_{template_name}'].value == 50.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_avr5_equations_and_rdf_mapping() -> None:
    """Check AVR5 first-order gain, Rex voltage drop, and RDF conversion.

    :return: None.
    """
    cgmes_object: ExcAVR5 = ExcAVR5(rdfid='_exc_avr5_equation_check')
    cgmes_object.ka = 2.5
    cgmes_object.ta = 0.4
    cgmes_object.rex = 0.08
    parameters: ExcAVR5Parameters = get_exc_avr5_parameters(cgmes_object)
    template_name: str = 'ExcAVR5_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r5_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 1
    assert len(template.block.state_eqs) == 1
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.rex == 0.08
    assert event_values[f'REX_{template_name}'].value == 0.08
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_avr7_equations_and_rdf_mapping() -> None:
    """Check AVR7's three rational filters, limits, and RDF mappings.

    :return: None.
    """
    cgmes_object: ExcAVR7 = ExcAVR7(rdfid='_exc_avr7_equation_check')
    cgmes_object.k1 = 1.2
    cgmes_object.k3 = 2.5
    cgmes_object.k5 = 0.9
    cgmes_object.a1 = 0.4
    cgmes_object.a2 = 0.6
    parameters: ExcAVR7Parameters = get_exc_avr7_parameters(cgmes_object)
    template_name: str = 'ExcAVR7_equation_check'
    template: RmsModelTemplate = build_exc_a_v_r7_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 4
    assert len(template.block.out_vars) == 1
    assert parameters.k3 == 2.5
    assert parameters.a1 == 0.4
    assert event_values[f'K5_{template_name}'].value == 0.9
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }


def test_exc_avr7_composed_nonzero_operating_point_residual() -> None:
    """Back-solve AVR7's three stage memories from a nonzero machine Efd point.

    :return: None.
    """
    machine_template: RmsModelTemplate = RmsModelTemplate(name='Machine_AVR7_residual')
    machine_template.block = Block(name=machine_template.name)
    machine_voltage: Var = Var('Vm')
    machine_field_voltage: Var = Var('EfdPu')
    machine_template.block.out_vars.extend((machine_voltage, machine_field_voltage))
    machine_template.block.algebraic_vars.extend((machine_voltage, machine_field_voltage))
    machine_template.block.algebraic_eqs.extend((
        machine_voltage - Const(1.0),
        machine_field_voltage - Const(0.5),
    ))
    machine_template.block.init_eqs[machine_voltage] = Const(1.0)
    machine_template.block.init_eqs[machine_field_voltage] = Const(0.5)
    exciter_parameters: ExcAVR7Parameters = ExcAVR7Parameters(
        k1=2.0, a1=0.5, a2=1.0, t1=0.2, t2=0.4,
        vmax1=5.0, vmin1=-5.0,
        k3=3.0, a3=0.4, a4=1.0, t3=0.3, t4=0.6,
        vmax3=5.0, vmin3=-5.0,
        k5=1.5, a5=0.75, a6=1.0, t5=0.4, t6=0.8,
        vmax5=5.0, vmin5=-5.0,
    )
    exciter_template: RmsModelTemplate = build_exc_a_v_r7_template(
        vfactory=VarFactory(),
        name='ExcAVR7_residual',
        parameters=exciter_parameters,
    )

    composite_template: RmsModelTemplate | None = compose_detailed_machine_with_exc_avr1(
        machine_template=machine_template,
        exciter_template=exciter_template,
        avr7_parameters=exciter_parameters,
    )

    assert composite_template is not None
    assert_zero_initial_residuals(composite_template, dict())


def test_exc_bbc_equations_and_rdf_mapping() -> None:
    """Check BBC's compensator, bounded regulator feedback, switch, and field drop.

    :return: None.
    """
    cgmes_object: ExcBBC = ExcBBC(rdfid='_exc_bbc_equation_check')
    cgmes_object.t1 = 4.0
    cgmes_object.t2 = 0.2
    cgmes_object.t3 = 0.3
    cgmes_object.t4 = 0.5
    cgmes_object.k = 15.0
    cgmes_object.vrmin = -4.0
    cgmes_object.vrmax = 4.0
    cgmes_object.efdmin = -3.0
    cgmes_object.efdmax = 5.0
    cgmes_object.xe = 0.08
    cgmes_object.switch = True
    parameters: ExcBBCParameters = get_exc_bbc_parameters(cgmes_object)
    template_name: str = 'ExcBBC_equation_check'
    template: RmsModelTemplate = build_exc_b_b_c_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    typical_parameters: ExcBBCParameters = ExcBBCParameters()
    missing_fields: ExcBBC = ExcBBC(rdfid='_exc_bbc_defaults')
    mapped_defaults: ExcBBCParameters = get_exc_bbc_parameters(missing_fields)

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 2
    assert len(template.block.state_eqs) == 2
    assert len(template.block.algebraic_eqs) == 3
    assert len(template.block.out_vars) == 1
    assert parameters.switch is True
    assert typical_parameters.t2 == 1.0
    assert typical_parameters.t3 == 0.05
    assert typical_parameters.t4 == 0.01
    assert typical_parameters.k == 300.0
    assert typical_parameters.switch is True
    assert mapped_defaults.switch is True
    assert mapped_defaults.k == 300.0
    assert parameters.k == 15.0
    assert parameters.xe == 0.08
    assert event_values[f'SWITCH_{template_name}'].value == 1.0
    assert event_values[f'XE_{template_name}'].value == 0.08
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_cz_equations_and_rdf_mapping() -> None:
    """Check CZ's PI integrator, bounded amplifier/exciter, and exact RDF mapping.

    :return: None.
    """
    cgmes_object: ExcCZ = ExcCZ(rdfid='_exc_cz_equation_check')
    cgmes_object.kp = 2.5
    cgmes_object.tc = 0.4
    cgmes_object.vrmax = 3.0
    cgmes_object.vrmin = -2.0
    cgmes_object.ka = 12.0
    cgmes_object.ta = 0.1
    cgmes_object.ke = 0.8
    cgmes_object.te = 0.6
    cgmes_object.efdmax = 4.0
    cgmes_object.efdmin = -3.0
    parameters: ExcCZParameters = get_exc_cz_parameters(cgmes_object)
    template_name: str = 'ExcCZ_equation_check'
    template: RmsModelTemplate = build_exc_c_z_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 3
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.kp == 2.5
    assert parameters.tc == 0.4
    assert event_values[f'KA_{template_name}'].value == 12.0
    assert event_values[f'TE_{template_name}'].value == 0.6
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }


def test_exc_dc1a_equations_and_rdf_mapping() -> None:
    """Check DC1A's regulator, saturation feedback, exciter, and speed paths.

    :return: None.
    """
    cgmes_object: ExcDC1A = ExcDC1A(rdfid='_exc_dc1a_equation_check')
    cgmes_object.ka = 40.0
    cgmes_object.ks = 0.2
    cgmes_object.ta = 0.08
    cgmes_object.tb = 0.4
    cgmes_object.tc = 0.1
    cgmes_object.vrmax = 1.5
    cgmes_object.vrmin = -1.0
    cgmes_object.ke = 0.2
    cgmes_object.te = 0.5
    cgmes_object.kf = 0.08
    cgmes_object.tf = 1.2
    cgmes_object.efd1 = 3.1
    cgmes_object.seefd1 = 0.33
    cgmes_object.efd2 = 2.3
    cgmes_object.seefd2 = 0.3
    cgmes_object.exclim = True
    cgmes_object.efdmin = -2.0
    cgmes_object.efdmax = 4.0
    parameters: ExcDC1AParameters = get_exc_dc1a_parameters(cgmes_object)
    template_name: str = 'ExcDC1A_equation_check'
    template: RmsModelTemplate = build_exc_d_c1_a_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 4
    assert len(template.block.state_eqs) == 4
    assert len(template.block.algebraic_eqs) == 2
    assert len(template.block.out_vars) == 1
    assert parameters.exclim is True
    assert parameters.ks == 0.2
    assert event_values[f'KS_{template_name}'].value == 0.2
    assert event_values[f'SEefd1_{template_name}'].value == 0.33
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'OmegaPu_{template_name}',
    }
    no_speed_settings: ExcDC1AParameters = ExcDC1AParameters(ks=0.0, kf=0.0, exclim=False)
    no_speed_template: RmsModelTemplate = build_exc_d_c1_a_template(
        vfactory=VarFactory(),
        name='ExcDC1A_no_speed',
        parameters=no_speed_settings,
    )
    assert len(no_speed_template.block.in_vars) == 3
    assert len(no_speed_template.block.state_vars) == 2


def test_exc_dc2a_equations_and_rdf_mapping() -> None:
    """Check DC2A's two feedback filters, Vt-scaled limits, and field equations.

    :return: None.
    """
    cgmes_object: ExcDC2A = ExcDC2A(rdfid='_exc_dc2a_equation_check')
    cgmes_object.ka = 250.0
    cgmes_object.ks = 0.15
    cgmes_object.ta = 0.04
    cgmes_object.tb = 0.3
    cgmes_object.tc = 0.08
    cgmes_object.vrmax = 4.5
    cgmes_object.vrmin = -4.0
    cgmes_object.ke = 0.9
    cgmes_object.te = 1.1
    cgmes_object.kf = 0.12
    cgmes_object.tf = 0.7
    cgmes_object.tf1 = 0.25
    cgmes_object.efd1 = 3.05
    cgmes_object.seefd1 = 0.279
    cgmes_object.efd2 = 2.29
    cgmes_object.seefd2 = 0.117
    cgmes_object.exclim = True
    cgmes_object.vtlim = True
    parameters: ExcDC2AParameters = get_exc_dc2a_parameters(cgmes_object)
    template_name: str = 'ExcDC2A_equation_check'
    template: RmsModelTemplate = build_exc_d_c2_a_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    fixed_limit_settings: ExcDC2AParameters = ExcDC2AParameters(vtlim=False, ks=0.0)
    fixed_limit_template: RmsModelTemplate = build_exc_d_c2_a_template(
        vfactory=VarFactory(),
        name='ExcDC2A_fixed_limits',
        parameters=fixed_limit_settings,
    )
    fixed_limit_events: dict[str, object] = dict(
        (variable.name, value) for variable, value in fixed_limit_template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 5
    assert len(template.block.state_eqs) == 5
    assert len(template.block.algebraic_eqs) == 2
    assert len(template.block.out_vars) == 1
    assert parameters.vtlim is True
    assert parameters.tf1 == 0.25
    assert event_values[f'TF1_{template_name}'].value == 0.25
    assert event_values[f'VTLIM_{template_name}'].value == 1.0
    assert fixed_limit_events['VTLIM_ExcDC2A_fixed_limits'].value == 0.0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_dc2a_zero_ke_is_calibrated_at_machine_operating_point() -> None:
    """Keep RDF Ke zero while calibrating its composed initial effective value.

    :return: None.
    """
    machine_template: RmsModelTemplate = RmsModelTemplate(name='Machine_DC2A_calibration')
    machine_template.block = Block(name=machine_template.name)
    machine_voltage: Var = Var('Vm')
    machine_field_voltage: Var = Var('EfdPu')
    machine_template.block.out_vars.extend((machine_voltage, machine_field_voltage))
    machine_template.block.algebraic_vars.extend((machine_voltage, machine_field_voltage))
    machine_template.block.algebraic_eqs.extend((
        machine_voltage - Const(1.0),
        machine_field_voltage - Const(0.5),
    ))
    machine_template.block.init_eqs[machine_voltage] = Const(1.0)
    machine_template.block.init_eqs[machine_field_voltage] = Const(0.5)
    exciter_name: str = 'ExcDC2A_zero_ke'
    exciter_parameters: ExcDC2AParameters = ExcDC2AParameters(
        ka=10.0,
        ta=0.1,
        tb=0.0,
        tc=0.0,
        vrmax=5.0,
        vrmin=-5.0,
        ke=0.0,
        te=1.0,
        kf=0.1,
        tf=0.5,
        tf1=0.3,
        efd1=1.0,
        seefd1=0.05,
        efd2=2.0,
        seefd2=0.2,
        exclim=True,
        vtlim=False,
    )
    exciter_template: RmsModelTemplate = build_exc_d_c2_a_template(
        vfactory=VarFactory(),
        name=exciter_name,
        parameters=exciter_parameters,
    )

    composite_template: RmsModelTemplate | None = compose_detailed_machine_with_exc_dc(
        machine_template=machine_template,
        exciter_template=exciter_template,
        dc_parameters=exciter_parameters,
    )

    assert composite_template is not None
    standalone_ke: Const | None = None
    for variable, value in exciter_template.block.event_dict.items():
        if variable.name == f'KE_{exciter_name}' and isinstance(value, Const):
            standalone_ke = value
        else:
            pass
    else:
        pass
    assert standalone_ke is not None
    assert standalone_ke.value == 0.0
    composite_ke: Expr | Const | None = None
    for runtime_block in composite_template.block.get_all_blocks():
        for variable, value in runtime_block.event_dict.items():
            if variable.name == f'KE_{exciter_name}':
                composite_ke = value
            else:
                pass
        else:
            pass
    else:
        pass
    assert composite_ke is not None
    assert not isinstance(composite_ke, Const)
    assert_zero_initial_residuals(composite_template, dict())


def test_exc_dc3a_equations_and_rdf_mapping() -> None:
    """Check DC3A's rheostat branches, fast contacts, saturation, and flags.

    :return: None.
    """
    cgmes_object: ExcDC3A = ExcDC3A(rdfid='_exc_dc3a_equation_check')
    cgmes_object.trh = 18.0
    cgmes_object.ks = 0.2
    cgmes_object.kr = 0.03
    cgmes_object.kv = 0.06
    cgmes_object.vrmax = 4.0
    cgmes_object.vrmin = -0.5
    cgmes_object.te = 1.5
    cgmes_object.ke = 0.8
    cgmes_object.efd1 = 2.6
    cgmes_object.seefd1 = 0.1
    cgmes_object.efd2 = 3.45
    cgmes_object.seefd2 = 0.35
    cgmes_object.exclim = True
    cgmes_object.efdmax = 10.0
    cgmes_object.efdmin = -2.0
    cgmes_object.efdlim = True
    parameters: ExcDC3AParameters = get_exc_dc3a_parameters(cgmes_object)
    template_name: str = 'ExcDC3A_equation_check'
    template: RmsModelTemplate = build_exc_d_c3_a_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    normalized_parameters: ExcDC3AParameters = ExcDC3AParameters(kr=0.0, ks=0.0)
    normalized_template: RmsModelTemplate = build_exc_d_c3_a_template(
        vfactory=VarFactory(),
        name='ExcDC3A_normalized_reset',
        parameters=normalized_parameters,
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 2
    assert len(template.block.state_eqs) == 2
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.kr == 0.03
    assert parameters.efdlim is True
    assert event_values[f'KR_{template_name}'].value == 0.03
    assert event_values[f'EFDLIM_{template_name}'].value == 1.0
    assert len(normalized_template.block.in_vars) == 3
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'OmegaPu_{template_name}',
    }


def test_exc_dc3a1_equations_and_rdf_mapping() -> None:
    """Check the potential-source bridge, stabilizer, limits, and RDF mapping.

    :return: None.
    """
    cgmes_object: ExcDC3A1 = ExcDC3A1(rdfid='_exc_dc3a1_equation_check')
    cgmes_object.ka = 240.0
    cgmes_object.ta = 0.02
    cgmes_object.vrmax = 4.0
    cgmes_object.vrmin = -1.0
    cgmes_object.te = 1.2
    cgmes_object.kf = 0.2
    cgmes_object.tf = 0.5
    cgmes_object.kp = 4.0
    cgmes_object.ki = 5.0
    cgmes_object.vbmax = 10.0
    cgmes_object.exclim = False
    cgmes_object.ke = 0.9
    cgmes_object.vb1max = 8.0
    cgmes_object.vblim = False
    parameters: ExcDC3A1Parameters = get_exc_dc3a1_parameters(cgmes_object)
    template_name: str = 'ExcDC3A1_equation_check'
    template: RmsModelTemplate = build_exc_d_c3_a1_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    zero_feedback_template: RmsModelTemplate = build_exc_d_c3_a1_template(
        vfactory=VarFactory(),
        name='ExcDC3A1_zero_feedback',
        parameters=ExcDC3A1Parameters(kf=0.0, tf=0.0),
    )

    assert len(template.block.in_vars) == 5
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 1
    assert len(template.block.out_vars) == 1
    assert parameters.ka == 240.0
    assert parameters.kp == 4.0
    assert parameters.ki == 5.0
    assert parameters.exclim is False
    assert parameters.vblim is False
    assert event_values[f'KA_{template_name}'].value == 240.0
    assert event_values[f'EXCLIM_{template_name}'].value == 0.0
    assert event_values[f'VBLIM_{template_name}'].value == 0.0
    assert len(zero_feedback_template.block.state_vars) == 2
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'ItPu_{template_name}',
        f'IfdPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
    }


def test_exc_elin1_equations_and_rdf_mapping() -> None:
    """Check ELIN1's stabilizer cascades, controller, and scalar mapping.

    :return: None.
    """
    cgmes_object: ExcELIN1 = ExcELIN1(rdfid='_exc_elin1_equation_check')
    cgmes_object.tfi = 0.2
    cgmes_object.tnu = 2.5
    cgmes_object.vpu = 30.0
    cgmes_object.vpi = 10.0
    cgmes_object.vpnf = 1.5
    cgmes_object.dpnf = 0.03
    cgmes_object.tsw = 2.0
    cgmes_object.efmin = -4.0
    cgmes_object.efmax = 4.0
    cgmes_object.xe = 0.05
    cgmes_object.ks1 = 0.2
    cgmes_object.ks2 = 0.3
    cgmes_object.ts1 = 0.8
    cgmes_object.ts2 = 1.2
    cgmes_object.smax = 0.15
    parameters: ExcELIN1Parameters = get_exc_elin1_parameters(cgmes_object)
    template_name: str = 'ExcELIN1_equation_check'
    template: RmsModelTemplate = build_exc_e_l_i_n1_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.in_vars) == 5
    assert len(template.block.state_vars) == 7
    assert len(template.block.state_eqs) == 7
    assert len(template.block.out_vars) == 1
    assert parameters.tfi == 0.2
    assert parameters.dpnf == 0.03
    assert parameters.ks1 == 0.2
    assert parameters.ks2 == 0.3
    assert event_values[f'TFI_{template_name}'].value == 0.2
    assert event_values[f'DPNF_{template_name}'].value == 0.03
    assert event_values[f'SMAX_{template_name}'].value == 0.15
    assert {variable.name for variable in template.block.in_vars} == {
        f'PgPu_{template_name}',
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UsBiasPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_elin2_equations_and_rdf_mapping() -> None:
    """Check ELIN2 voltage/current loops and both brushless timing branches.

    :return: None.
    """
    cgmes_object: ExcELIN2 = ExcELIN2(rdfid='_exc_elin2_equation_check')
    cgmes_object.k1 = 0.2
    cgmes_object.k1ec = 1.5
    cgmes_object.kd1 = 10.0
    cgmes_object.tb1 = 2.0
    cgmes_object.pid1max = 1.8
    cgmes_object.ti1 = 0.5
    cgmes_object.iefmax2 = -3.0
    cgmes_object.k2 = 4.0
    cgmes_object.ketb = 0.08
    cgmes_object.upmax = 2.5
    cgmes_object.upmin = -0.2
    cgmes_object.te = 0.3
    cgmes_object.xp = 0.7
    cgmes_object.te2 = 0.8
    cgmes_object.ke2 = 0.12
    cgmes_object.ve1 = 2.5
    cgmes_object.seve1 = 0.2
    cgmes_object.ve2 = 0.5
    cgmes_object.seve2 = 0.8
    cgmes_object.tr4 = 0.4
    cgmes_object.k3 = 0.15
    cgmes_object.ti3 = 2.0
    cgmes_object.k4 = 0.25
    cgmes_object.ti4 = 1.5
    cgmes_object.iefmax = 1.2
    cgmes_object.iefmin = 0.1
    cgmes_object.efdbas = 0.2
    parameters: ExcELIN2Parameters = get_exc_elin2_parameters(cgmes_object)
    template_name: str = 'ExcELIN2_equation_check'
    template: RmsModelTemplate = build_exc_e_l_i_n2_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    bypass_template: RmsModelTemplate = build_exc_e_l_i_n2_template(
        vfactory=VarFactory(),
        name='ExcELIN2_zero_time_bypass',
        parameters=ExcELIN2Parameters(te2=0.0),
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 7
    assert len(template.block.state_eqs) == 7
    assert len(template.block.algebraic_eqs) == 2
    assert len(template.block.out_vars) == 1
    assert len(template.block.event_dict) == 27
    assert parameters.iefmax2 == -3.0
    assert parameters.seve1 == 0.2
    assert parameters.seve2 == 0.8
    assert parameters.efdbas == 0.2
    assert event_values[f'KD1_{template_name}'].value == 10.0
    assert event_values[f'K4_{template_name}'].value == 0.25
    assert event_values[f'EFDBAS_{template_name}'].value == 0.2
    assert len(bypass_template.block.state_vars) == 3
    assert len(bypass_template.block.algebraic_eqs) == 3
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_hu_equations_and_rdf_mapping() -> None:
    """Check both bounded PI loops, voltage filtering, and all RDF fields.

    :return: None.
    """
    cgmes_object: ExcHU = ExcHU(rdfid='_exc_hu_equation_check')
    cgmes_object.tr = 0.02
    cgmes_object.te = 0.2
    cgmes_object.imin = 0.2
    cgmes_object.imax = 2.0
    cgmes_object.ae = 2.5
    cgmes_object.emin = -0.7
    cgmes_object.emax = 0.9
    cgmes_object.ki = 0.25
    cgmes_object.ai = 18.0
    cgmes_object.ti = 0.02
    cgmes_object.atr = 2.0
    cgmes_object.ke = 4.0
    parameters: ExcHUParameters = get_exc_hu_parameters(cgmes_object)
    template_name: str = 'ExcHU_equation_check'
    template: RmsModelTemplate = build_exc_h_u_template(
        vfactory=VarFactory(),
        name=template_name,
        parameters=parameters,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    zero_time_template: RmsModelTemplate = build_exc_h_u_template(
        vfactory=VarFactory(),
        name='ExcHU_zero_time_stages',
        parameters=ExcHUParameters(tr=0.0, te=0.0, ti=0.0),
    )

    assert len(template.block.in_vars) == 4
    assert len(template.block.state_vars) == 3
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 4
    assert len(template.block.out_vars) == 1
    assert len(template.block.event_dict) == 12
    assert parameters.imax == 2.0
    assert parameters.ai == 18.0
    assert event_values[f'TR_{template_name}'].value == 0.02
    assert event_values[f'KI_{template_name}'].value == 0.25
    assert event_values[f'KE_{template_name}'].value == 4.0
    assert len(zero_time_template.block.state_vars) == 0
    assert {variable.name for variable in template.block.in_vars} == {
        f'UsPu_{template_name}',
        f'UsRefPu_{template_name}',
        f'UpssPu_{template_name}',
        f'IfdPu_{template_name}',
    }


def test_exc_ac1a_association_connects_to_detailed_generator() -> None:
    """Attach AC1A by RDF association and bind the detailed machine ports.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac1a_bus')
    exciter: ExcAC1A = ExcAC1A(rdfid='_detailed_exc_ac1a')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac1a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac1a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac1a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'ExcAC1A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu_ExcAC1A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'UsPu_ExcAC1A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'OmegaPu_ExcAC1A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    machine_equations: list[Expr] = list()
    for runtime_block in composite_template.block.get_all_blocks():
        if runtime_block.name.startswith('SynchronousMachineTimeConstantReactance_'):
            machine_equations.extend(runtime_block.state_eqs)
        else:
            pass
    assert any(
        variable.name == 'EfdPu_ExcAC1A_' + exciter.uuid
        for equation in machine_equations
        for variable in equation.get_vars()
    )
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


@pytest.mark.parametrize('time_constant', (0.0, 0.5))
@pytest.mark.parametrize(
    'machine_model',
    (
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        SynchronousMachineModelKind.subtransientTypeF,
        SynchronousMachineModelKind.subtransientTypeJ,
    ),
)
def test_exc_sexs_association_connects_to_detailed_generator(
        time_constant: float,
        machine_model: SynchronousMachineModelKind,
) -> None:
    """Verify SEXS RDF values and voltage/field ports reach the generator graph.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_sexs_bus')
    exciter: ExcSEXS = ExcSEXS(rdfid='_detailed_exc_sexs')
    exciter.tatb = 0.2
    exciter.tb = 0.1
    exciter.k = 10.0
    exciter.te = 0.5
    exciter.emin = -5.0
    exciter.emax = 5.0
    exciter.kc = 1.0
    exciter.tc = time_constant
    exciter.efdmin = -5.0
    exciter.efdmax = 5.0
    stabilizer: Pss1 = Pss1(rdfid='_detailed_exc_sexs_stabilizer')
    stabilizer.kw = 0.4
    stabilizer.kf = 2.0
    stabilizer.kpe = 0.3
    stabilizer.pmin = 0.25
    stabilizer.ks = 1.4
    stabilizer.vsmn = -0.08
    stabilizer.vsmx = 0.08
    stabilizer.tpe = 0.05
    stabilizer.t5 = 3.5
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_sexs_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = machine_model
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_sexs_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='detailed_sexs_generator',
        P=50.0,
        Q=10.0,
    )
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    exciter.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcSEXS'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['Pss1'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'ExcSEXS_{exciter.uuid}' in composite_template.name
    assert f'Pss1_{stabilizer.uuid}' in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block,
        f'ExcSEXS.UsPu_ExcSEXS_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'ExcSEXS.EfdPu_ExcSEXS_{exciter.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'ExcSEXS.UpssPu_ExcSEXS_{exciter.uuid}',
    ) is None
    pss_output_name: str = f'VsPu_Pss1_{stabilizer.uuid}'
    assert any(
        variable.name == pss_output_name
        for runtime_block in composite_template.block.get_all_blocks()
        for equation in runtime_block.state_eqs + runtime_block.algebraic_eqs
        for variable in equation.get_vars()
    )
    frequency_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'FrequencyDeviationPu_Pss1_{stabilizer.uuid}',
    )
    assert frequency_input is not None
    for runtime_block in composite_template.block.get_all_blocks():
        if frequency_input in runtime_block.in_vars:
            runtime_block.init_eqs[frequency_input] = Const(0.0)
        else:
            pass
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )
    parameter_name: str
    parameter_value: float
    for parameter_name, parameter_value in (
            ('tatb', 0.2), ('tb', 0.1), ('k', 10.0), ('te', 0.5),
            ('emin', -5.0), ('emax', 5.0), ('kc', 1.0), ('tc', time_constant),
            ('efdmin', -5.0), ('efdmax', 5.0),
    ):
        parameter_variable: Var | None = find_block_variable_by_name(
            composite_template.block,
            f'ExcSEXS.{parameter_name}_ExcSEXS_{exciter.uuid}',
        )
        assert parameter_variable is not None
        assert any(
            parameter_variable in runtime_block.event_dict
            and runtime_block.event_dict[parameter_variable] == Const(parameter_value)
            for runtime_block in composite_template.block.get_all_blocks()
        )
    pi_state: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'ExcSEXS.PIState_ExcSEXS_{exciter.uuid}',
    )
    if time_constant > 0.0:
        assert pi_state is not None
    else:
        assert pi_state is None


def test_exc_sexs_pi_equations_follow_the_canonical_block_cascade() -> None:
    """Check nonzero-Tc PI integration and the zero-Tc reduced topology.

    :return: None.
    """
    template_name: str = 'ExcSEXS_pi_equation_check'
    template: RmsModelTemplate = build_exc_s_e_x_s_template(
        vfactory=VarFactory(),
        name=template_name,
        tc_value=0.5,
    )
    pi_state: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.PIState_{template_name}',
    )
    lead_lag_output: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.LeadLagOutput_{template_name}',
    )
    exciter_state: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.ExciterState_{template_name}',
    )
    exciter_gain: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.k_{template_name}',
    )
    pi_gain: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.kc_{template_name}',
    )
    exciter_time: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.te_{template_name}',
    )
    pi_time: Var | None = find_block_variable_by_name(
        template.block,
        f'ExcSEXS.tc_{template_name}',
    )
    assert pi_state is not None
    assert lead_lag_output is not None
    assert exciter_state is not None
    assert exciter_gain is not None
    assert pi_gain is not None
    assert exciter_time is not None
    assert pi_time is not None
    runtime_block: Block = template.block.children[0]
    pi_equation: Expr = runtime_block.state_eqs[runtime_block.state_vars.index(pi_state)]
    exciter_equation: Expr = runtime_block.state_eqs[runtime_block.state_vars.index(exciter_state)]
    equation_values: dict[int, float] = {
        pi_state.uid: 4.0,
        lead_lag_output.uid: 3.0,
        exciter_state.uid: 2.0,
        exciter_gain.uid: 10.0,
        pi_gain.uid: 0.2,
        exciter_time.uid: 0.5,
        pi_time.uid: 0.5,
    }
    assert isclose(eval_uid(pi_equation, equation_values), 6.0, abs_tol=1e-12)
    assert isclose(eval_uid(exciter_equation, equation_values), 24.0, abs_tol=1e-12)

    zero_time_template: RmsModelTemplate = build_exc_s_e_x_s_template(
        vfactory=VarFactory(),
        name='ExcSEXS_zero_tc_check',
        tc_value=0.0,
    )
    assert find_block_variable_by_name(
        zero_time_template.block,
        'ExcSEXS.PIState_ExcSEXS_zero_tc_check',
    ) is None


def test_exc_ac2a_association_connects_to_detailed_generator() -> None:
    """Attach AC2A through the RDF machine association to a direct-axis generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac2a_bus')
    exciter: ExcAC2A = ExcAC2A(rdfid='_detailed_exc_ac2a')
    exciter.ka = 325.0
    exciter.kb = 21.0
    exciter.kb1 = 19.0
    exciter.kl = 8.0
    exciter.vlr = 4.2
    exciter.vfemax = 4.1
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac2a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'ExcAC2A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu_ExcAC2A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'UsPu_ExcAC2A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'OmegaPu_ExcAC2A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ac3a_association_connects_to_detailed_generator() -> None:
    """Attach AC3A through its RDF machine association to a direct-axis generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac3a_bus')
    exciter: ExcAC3A = ExcAC3A(rdfid='_detailed_exc_ac3a')
    exciter.kr = 3.77
    exciter.efdn = 2.1
    exciter.vemin = 0.08
    exciter.vfemax = 12.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac3a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac3a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'ExcAC3A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu_ExcAC3A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'UsPu_ExcAC3A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ac4a_association_connects_to_detailed_generator() -> None:
    """Attach AC4A through its RDF machine association to a direct-axis generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac4a_bus')
    exciter: ExcAC4A = ExcAC4A(rdfid='_detailed_exc_ac4a')
    exciter.ka = 175.0
    exciter.kc = 0.12
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac4a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac4a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac4a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC4A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'ExcAC4A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu_ExcAC4A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'UsPu_ExcAC4A_' + exciter.uuid) is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ac5a_association_connects_to_detailed_generator() -> None:
    """Attach AC5A by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac5a_bus')
    exciter: ExcAC5A = ExcAC5A(rdfid='_detailed_exc_ac5a')
    exciter.ks = 0.05
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac5a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac5a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac5a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC5A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAC5A_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAC5A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAC5A_{exciter.uuid}') is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_ExcAC5A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(composite_template.block, 'omega') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ac6a_association_connects_to_detailed_generator() -> None:
    """Attach AC6A by RDF association and bind machine voltage, speed, field current, and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac6a_bus')
    exciter: ExcAC6A = ExcAC6A(rdfid='_detailed_exc_ac6a')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac6a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac6a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac6a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC6A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAC6A_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAC6A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAC6A_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'omega') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ac8b_association_connects_to_detailed_generator() -> None:
    """Attach AC8B by RDF association and bind machine voltage, speed, field current, and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac8b_bus')
    exciter: ExcAC8B = ExcAC8B(rdfid='_detailed_exc_ac8b')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ac8b_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ac8b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac8b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAC8B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAC8B_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAC8B_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAC8B_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'omega') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert find_block_variable_by_name(composite_template.block, 'VuelPu_ExcAC8B_' + exciter.uuid) is not None
    assert find_block_variable_by_name(composite_template.block, 'VoelPu_ExcAC8B_' + exciter.uuid) is not None


def test_exc_ans_association_connects_to_detailed_generator() -> None:
    """Attach ANS by RDF association and bind machine voltage, field current, and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ans_bus')
    exciter: ExcANS = ExcANS(rdfid='_detailed_exc_ans')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_ans_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ans_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ans_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcANS'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcANS_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcANS_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcANS_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None


def test_exc_avr1_association_connects_to_detailed_generator() -> None:
    """Attach AVR1 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr1_bus')
    exciter: ExcAVR1 = ExcAVR1(rdfid='_detailed_exc_avr1')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr1_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr1_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR1'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR1_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR1_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_avr2_association_connects_to_detailed_generator() -> None:
    """Attach AVR2 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr2_bus')
    exciter: ExcAVR2 = ExcAVR2(rdfid='_detailed_exc_avr2')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr2_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr2_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr2_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR2'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR2_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR2_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR2_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_avr3_association_connects_to_detailed_generator() -> None:
    """Attach AVR3 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr3_bus')
    exciter: ExcAVR3 = ExcAVR3(rdfid='_detailed_exc_avr3')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr3_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr3_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr3_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR3'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR3_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR3_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR3_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_avr4_association_connects_to_detailed_generator() -> None:
    """Attach AVR4 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr4_bus')
    exciter: ExcAVR4 = ExcAVR4(rdfid='_detailed_exc_avr4')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr4_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr4_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr4_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR4'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR4_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR4_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR4_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_avr5_association_connects_to_detailed_generator() -> None:
    """Attach AVR5 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr5_bus')
    exciter: ExcAVR5 = ExcAVR5(rdfid='_detailed_exc_avr5')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr5_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr5_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr5_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR5'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR5_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR5_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR5_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.2,
        },
    )


def test_exc_avr7_association_connects_to_detailed_generator() -> None:
    """Attach AVR7 by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_avr7_bus')
    exciter: ExcAVR7 = ExcAVR7(rdfid='_detailed_exc_avr7')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_avr7_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_avr7_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_avr7_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcAVR7'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcAVR7_{exciter.uuid}' in composite_template.name
    assert 'ExcAVR7' in composite_template.comment
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcAVR7_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcAVR7_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_bbc_association_connects_voltage_field_current_and_efd() -> None:
    """Bind BBC's three machine signals through its RDF machine association.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_bbc_bus')
    exciter: ExcBBC = ExcBBC(rdfid='_detailed_exc_bbc')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_bbc_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_bbc_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_bbc_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcBBC'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcBBC_{exciter.uuid}' in composite_template.name
    assert 'ExcBBC' in composite_template.comment
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcBBC_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'IfdPu_ExcBBC_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcBBC_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_cz_association_connects_to_detailed_generator() -> None:
    """Attach CZ by RDF association and bind machine voltage and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_cz_bus')
    exciter: ExcCZ = ExcCZ(rdfid='_detailed_exc_cz')
    exciter.kp = 0.0
    exciter.tc = 1.0
    exciter.vrmax = 5.0
    exciter.vrmin = -5.0
    exciter.ka = 1.0
    exciter.ta = 0.0
    exciter.ke = 1.0
    exciter.te = 0.0
    exciter.efdmax = 5.0
    exciter.efdmin = -5.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_cz_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_cz_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_cz_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcCZ'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcCZ_{exciter.uuid}' in composite_template.name
    assert 'ExcCZ' in composite_template.comment
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcCZ_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcCZ_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_dc1a_association_connects_voltage_speed_and_efd() -> None:
    """Bind DC1A's voltage, conditional speed, and Efd through machine links.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_dc1a_bus')
    exciter: ExcDC1A = ExcDC1A(rdfid='_detailed_exc_dc1a')
    exciter.ks = 0.2
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_dc1a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_dc1a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_dc1a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcDC1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcDC1A_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcDC1A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'OmegaPu_ExcDC1A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcDC1A_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_dc2a_association_connects_voltage_speed_and_efd() -> None:
    """Bind DC2A's voltage, conditional speed, and Efd through machine links.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_dc2a_bus')
    exciter: ExcDC2A = ExcDC2A(rdfid='_detailed_exc_dc2a')
    exciter.ks = 0.2
    exciter.ke = 0.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_dc2a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_dc2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_dc2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcDC2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcDC2A_{exciter.uuid}' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcDC2A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'OmegaPu_ExcDC2A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcDC2A_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert exciter.ke == 0.0
    effective_ke: Expr | Const | None = None
    runtime_block: Block
    parameter_variable: Var
    parameter_value: Expr | Const
    for runtime_block in composite_template.block.get_all_blocks():
        for parameter_variable, parameter_value in runtime_block.event_dict.items():
            if parameter_variable.name == f'KE_ExcDC2A_{exciter.uuid}':
                effective_ke = parameter_value
            else:
                pass
        else:
            pass
    else:
        pass
    assert effective_ke is not None
    assert not isinstance(effective_ke, Const)
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_dc3a_association_connects_voltage_speed_and_efd() -> None:
    """Bind DC3A's voltage, conditional speed, and Efd through machine links.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_dc3a_bus')
    exciter: ExcDC3A = ExcDC3A(rdfid='_detailed_exc_dc3a')
    exciter.ks = 0.2
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_dc3a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_dc3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_dc3a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcDC3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcDC3A_{exciter.uuid}' in composite_template.name
    assert composite_template.comment == 'CGMES detailed synchronous machine with ExcDC3A.'
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcDC3A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'OmegaPu_ExcDC3A_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcDC3A_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_dc3a1_association_connects_voltage_currents_and_efd() -> None:
    """Bind DC3A1's bridge inputs and Efd output to its generator model.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_dc3a1_bus')
    exciter: ExcDC3A1 = ExcDC3A1(rdfid='_detailed_exc_dc3a1')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_dc3a1_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_dc3a1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_dc3a1_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcDC3A1'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcDC3A1_{exciter.uuid}' in composite_template.name
    assert composite_template.comment == 'CGMES detailed synchronous machine with ExcDC3A1.'
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcDC3A1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'ItPu_ExcDC3A1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'IfdPu_ExcDC3A1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcDC3A1_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_elin1_association_connects_machine_power_and_field_signals() -> None:
    """Attach ELIN1 to the generator signals required by its EA diagram.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_elin1_bus')
    exciter: ExcELIN1 = ExcELIN1(rdfid='_detailed_exc_elin1')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_elin1_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_elin1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_elin1_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcELIN1'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcELIN1_{exciter.uuid}' in composite_template.name
    assert composite_template.comment == 'CGMES detailed synchronous machine with ExcELIN1.'
    assert find_block_variable_by_name(composite_template.block, f'PgPu_ExcELIN1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcELIN1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'IfdPu_ExcELIN1_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'EfdPu_ExcELIN1_{exciter.uuid}') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_elin2_association_connects_voltage_field_current_and_efd() -> None:
    """Bind ELIN2's voltage and field-current paths to its detailed generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_elin2_bus')
    exciter: ExcELIN2 = ExcELIN2(rdfid='_detailed_exc_elin2')
    exciter.te = 0.2
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_elin2_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_elin2_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_elin2_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcELIN2'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcELIN2_{exciter.uuid}' in composite_template.name
    assert composite_template.comment == 'CGMES detailed synchronous machine with ExcELIN2.'
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcELIN2_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'IfdPu_ExcELIN2_{exciter.uuid}') is None
    exciter_field_voltage: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcELIN2_{exciter.uuid}',
    )
    exciter_field_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'BrushlessFieldVoltagePu_ExcELIN2_{exciter.uuid}',
    )
    converter_state: Var | None = find_block_variable_by_name(
        composite_template.block, f'ConverterVoltagePu_ExcELIN2_{exciter.uuid}',
    )
    assert exciter_field_voltage is not None
    assert exciter_field_state is not None
    assert converter_state is not None
    field_voltage_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block, exciter_field_voltage,
    )
    field_state_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block, exciter_field_state,
    )
    converter_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block, converter_state,
    )
    assert field_voltage_initial is not None
    assert field_state_initial is not None
    assert converter_initial is not None
    assert not isinstance(field_voltage_initial, Const)
    assert not isinstance(field_state_initial, Const)
    assert not isinstance(converter_initial, Const)
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_hu_association_transfers_machine_efd_initialization() -> None:
    """Bind ExcHU physical signals and seed its minor PI loop from machine Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_hu_bus')
    exciter: ExcHU = ExcHU(rdfid='_detailed_exc_hu')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_exc_hu_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.statorLeakageReactance = 0.15
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.05
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_hu_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_hu_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcHU'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert f'ExcHU_{exciter.uuid}' in composite_template.name
    assert composite_template.comment == 'CGMES detailed synchronous machine with ExcHU.'
    exciter_field_voltage: Var | None = find_block_variable_by_name(
        composite_template.block, f'EfdPu_ExcHU_{exciter.uuid}',
    )
    minor_integrator: Var | None = find_block_variable_by_name(
        composite_template.block, f'MinorIntegratorPu_ExcHU_{exciter.uuid}',
    )
    assert find_block_variable_by_name(composite_template.block, f'UsPu_ExcHU_{exciter.uuid}') is None
    assert find_block_variable_by_name(composite_template.block, f'IfdPu_ExcHU_{exciter.uuid}') is None
    assert exciter_field_voltage is not None
    assert minor_integrator is not None
    field_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block, exciter_field_voltage,
    )
    minor_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block, minor_integrator,
    )
    assert field_initial is not None
    assert minor_initial is not None
    assert not isinstance(field_initial, Const)
    assert not isinstance(minor_initial, Const)
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None


def test_exc_scrx_reuses_rms_equations_with_cgmes_parameter_mapping() -> None:
    """Drive the reused SCRX equation block from its exact CGMES fields.

    :return: None.
    """
    cgmes_object: ExcSCRX = ExcSCRX(rdfid="_exc_scrx_check")
    cgmes_object.tatb = 0.25
    cgmes_object.tb = 0.4
    cgmes_object.k = 18.0
    cgmes_object.te = 0.08
    cgmes_object.emin = -3.0
    cgmes_object.emax = 4.0
    cgmes_object.cswitch = True
    cgmes_object.rcrfd = 0.12
    variable_factory: VarFactory = VarFactory()
    template_name: str = "ExcSCRX_check"
    template: RmsModelTemplate = build_exc_s_c_r_x_template(
        vfactory=variable_factory,
        name=template_name,
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    event_values: dict[str, object] = dict()
    block: Block
    for block in template.block.get_all_blocks():
        for variable, value in block.event_dict.items():
            event_values[variable.name] = value

    assert event_values[f"ExcSCRX.k_{template_name}"].value == 18.0
    assert event_values[f"avr.K_{template_name}"].value == 18.0
    assert event_values[f"avr.tA_{template_name}"].value == 0.1
    assert event_values[f"avr.tB_{template_name}"].value == 0.4
    assert event_values[f"avr.tE_{template_name}"].value == 0.08
    assert event_values[f"avr.VrMinPu_{template_name}"].value == -3.0
    assert event_values[f"avr.VrMaxPu_{template_name}"].value == 4.0
    assert event_values[f"avr.CSwitch_{template_name}"].value == 1.0
    assert event_values[f"avr.RcToRfd_{template_name}"].value == 0.12


def test_exc_ieee_ac1a_association_respects_simplified_machine_limits() -> None:
    """Retain the exciter association without inventing an Efd machine port.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name="bus")
    exciter: ExcIEEEAC1A = ExcIEEEAC1A(rdfid="_exciter")
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_machine_dynamics"
    )
    machine: SynchronousMachine = SynchronousMachine(rdfid="_machine")
    generator: Generator = Generator(idtag=machine.uuid, name="machine")
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists["ExcIEEEAC1A"].append(exciter)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    assert len(veragrid_model.rms_models) == 2
    assert any(
        model.device is generator and model.name.startswith("ExcIEEEAC1A_")
        for model in veragrid_model.rms_models
    )
    assert generator.rms_template is not None
    assert generator.rms_template.name.startswith("SynchronousMachineSimplified_")
    assert any(
        entry.msg.startswith("CGMES SynchronousMachineSimplified has no Efd input")
        for entry in logger.entries
    )


def test_exc_ieee_ac1a_connects_to_detailed_direct_axis_machine() -> None:
    """Connect AC1A feedback and output through the CGMES machine association.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ac1a_bus')
    exciter: ExcIEEEAC1A = ExcIEEEAC1A(rdfid='_detailed_ac1a_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_detailed_ac1a_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ac1a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ac1a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEAC1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'ExcIEEEAC1A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'IfdPu_ExcIEEEAC1A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UsPu_ExcIEEEAC1A_{exciter.uuid}',
    ) is None
    field_current_signal: Var | None = find_block_variable_by_name(
        composite_template.block,
        'IfdPu',
    )
    assert field_current_signal is not None
    field_voltage_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'EfdPu_ExcIEEEAC1A_{exciter.uuid}',
    )
    assert field_voltage_output is not None
    machine_state_equations: list[Expr] = list()
    exciter_equations: list[Expr] = list()
    for runtime_block in composite_template.block.get_all_blocks():
        if runtime_block.name.startswith('SynchronousMachineTimeConstantReactance_'):
            machine_state_equations.extend(runtime_block.state_eqs)
        elif runtime_block.name.startswith(f'ExcIEEEAC1A_{exciter.uuid}'):
            exciter_equations.extend(runtime_block.state_eqs)
            exciter_equations.extend(runtime_block.algebraic_eqs)
        else:
            pass
    assert any(field_voltage_output in equation.get_vars() for equation in machine_state_equations)
    assert any(field_current_signal in equation.get_vars() for equation in exciter_equations)
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


@pytest.mark.parametrize(
    "signal_kind",
    (
        InputSignalKind.rotorSpeed,
        InputSignalKind.rotorAngularFrequencyDeviation,
        InputSignalKind.generatorElectricalPower,
        InputSignalKind.busVoltage,
    ),
)
@pytest.mark.parametrize("use_detailed_machine", (False, True))
@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
@pytest.mark.parametrize(
    'model_type',
    (
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        SynchronousMachineModelKind.subtransientSimplified,
    ),
)
def test_pss_ieee1a_selected_signal_connects_through_exciter_to_machine(
        signal_kind: InputSignalKind,
        use_detailed_machine: bool,
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> None:
    """Bind the CGMES PSS selector, exciter voltage, and PSS output ports.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name="bus")
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid="_machine")
    machine_dynamics: SynchronousMachineSimplified | SynchronousMachineTimeConstantReactance
    if use_detailed_machine:
        machine_dynamics = SynchronousMachineTimeConstantReactance(rdfid="_machine_dynamics")
        machine_dynamics.rotorType = rotor_type
        machine_dynamics.modelType = model_type
        machine_dynamics.inertia = 4.0
        machine_dynamics.xDirectSync = 1.8
        machine_dynamics.xDirectTrans = 0.3
        machine_dynamics.xDirectSubtrans = 0.2
        machine_dynamics.xQuadSync = 1.7
        machine_dynamics.xQuadTrans = 0.55
        machine_dynamics.xQuadSubtrans = 0.2
        machine_dynamics.tpdo = 5.0
        machine_dynamics.tppdo = 0.04
        machine_dynamics.statorLeakageReactance = 0.12
        machine_dynamics.statorResistance = 0.0
        machine_dynamics.tpqo = 0.7
        machine_dynamics.tppqo = 0.05
        machine.ratedS = 100.0
        machine.ratedPowerFactor = 1.0
    else:
        machine_dynamics = SynchronousMachineSimplified(rdfid="_machine_dynamics")
    excitation: ExcST1A = ExcST1A(rdfid="_excitation")
    stabilizer: PssIEEE1A = PssIEEE1A(rdfid="_stabilizer")
    stabilizer.inputSignalType = signal_kind
    generator: Generator = Generator(idtag=machine.uuid, name="machine")
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    if use_detailed_machine:
        cgmes_model.dynamics_assets.lists["SynchronousMachineTimeConstantReactance"].append(machine_dynamics)
    else:
        cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["ExcST1A"].append(excitation)
    cgmes_model.dynamics_assets.lists["PssIEEE1A"].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    assert generator.rms_template is not None, logger.get_message() + ''.join(
        str(entry) for entry in logger.entries
    )
    assert "PssIEEE1A_" in generator.rms_template.name
    assert "ExcST1A_" in generator.rms_template.name
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f"SignalPu_PssIEEE1A_{stabilizer.uuid}",
    ) is None
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f"UpssPu_ExcST1A_{excitation.uuid}",
    ) is None
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f"UsPu_ExcST1A_{excitation.uuid}",
    ) is None
    if signal_kind == InputSignalKind.rotorAngularFrequencyDeviation:
        assert any(
            variable.name.startswith("PssRotorSpeedDeviationPu_0_")
            for block in generator.rms_template.block.get_all_blocks()
            for variable in block.algebraic_vars
        )
    else:
        pass
    if use_detailed_machine:
        assert find_block_variable_by_name(generator.rms_template.block, "EfdPu") is None
        field_voltage_output: Var | None = find_block_variable_by_name(
            generator.rms_template.block,
            f"EfdPu_ExcST1A_{excitation.uuid}",
        )
        assert field_voltage_output is not None
        assert find_block_variable_by_name(generator.rms_template.block, 'ItPu') is not None
        if model_type == SynchronousMachineModelKind.subtransientSimplifiedDirectAxis:
            assert find_block_variable_by_name(
                generator.rms_template.block,
                f"IfdPu_ExcST1A_{excitation.uuid}",
            ) is None
            assert find_block_variable_by_name(generator.rms_template.block, 'IfdPu') is not None
        else:
            assert find_block_variable_by_name(
                generator.rms_template.block,
                f"IfdPu_ExcST1A_{excitation.uuid}",
            ) is not None
        machine_field_equations: list[Expr] = list()
        for runtime_block in generator.rms_template.block.get_all_blocks():
            if runtime_block.name.startswith("SynchronousMachineTimeConstantReactance_"):
                machine_field_equations.extend(runtime_block.state_eqs)
            else:
                pass
        assert any(field_voltage_output in equation.get_vars() for equation in machine_field_equations)
        assert not any(
            entry.msg.startswith("CGMES SynchronousMachineSimplified has no Efd input")
            for entry in logger.entries
        )
    else:
        assert_zero_initial_residuals(
            template=generator.rms_template,
            power_flow_values={
                VarPowerFlowReferenceType.Vm: 1.0,
                VarPowerFlowReferenceType.Va: 0.0,
                VarPowerFlowReferenceType.P: 0.0,
                VarPowerFlowReferenceType.Q: 0.0,
            },
        )
        assert any(
            entry.msg.startswith("CGMES SynchronousMachineSimplified has no Efd input")
            for entry in logger.entries
        )


@pytest.mark.parametrize(
    ("signal_1_kind", "signal_2_kind"),
    (
        (InputSignalKind.rotorSpeed, InputSignalKind.rotorAngularFrequencyDeviation),
        (InputSignalKind.generatorElectricalPower, InputSignalKind.busVoltage),
        (InputSignalKind.rotorAngularFrequencyDeviation, InputSignalKind.generatorElectricalPower),
        (InputSignalKind.busVoltage, InputSignalKind.rotorSpeed),
    ),
)
def test_pss_ieee2b_selected_signals_connect_through_exciter_to_machine(
        signal_1_kind: InputSignalKind,
        signal_2_kind: InputSignalKind,
) -> None:
    """Bind both CGMES PSS2B selectors and check the composed initial DAE point.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name="pss2b_bus")
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid="_pss2b_machine")
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_pss2b_machine_dynamics"
    )
    excitation: ExcST1A = ExcST1A(rdfid="_pss2b_excitation")
    stabilizer: PssIEEE2B = PssIEEE2B(rdfid="_pss2b_stabilizer")
    stabilizer.inputSignal1Type = signal_1_kind
    stabilizer.inputSignal2Type = signal_2_kind
    generator: Generator = Generator(idtag=machine.uuid, name="pss2b_machine")
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["ExcST1A"].append(excitation)
    cgmes_model.dynamics_assets.lists["PssIEEE2B"].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert "PssIEEE2B_" in composite_template.name
    assert "ExcST1A_" in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block,
        f"Signal1Pu_PssIEEE2B_{stabilizer.uuid}",
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f"Signal2Pu_PssIEEE2B_{stabilizer.uuid}",
    ) is None
    if InputSignalKind.rotorAngularFrequencyDeviation in (
            stabilizer.inputSignal1Type,
            stabilizer.inputSignal2Type,
    ):
        assert any(
            variable.name.startswith("PssRotorSpeedDeviationPu_")
            for runtime_block in composite_template.block.get_all_blocks()
            for variable in runtime_block.algebraic_vars
        )
    else:
        pass
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_ieee3b_default_selectors_compose_both_machine_inputs() -> None:
    """Check IEEE3B's canonical default power/speed selectors in composition.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_ieee3b_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_ieee3b_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_ieee3b_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_ieee3b_excitation')
    stabilizer: PssIEEE3B = PssIEEE3B(rdfid='_pss_ieee3b_stabilizer')
    stabilizer.ks1 = 0.7
    stabilizer.ks2 = 1.4
    stabilizer.vstmax = 0.08
    stabilizer.vstmin = -0.08
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssIEEE3B'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss_ieee3b_generator')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'PssIEEE3B_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal1Pu_PssIEEE3B_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal2Pu_PssIEEE3B_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    assert any(
        variable.name == f'PssIEEE3B.ks1_PssIEEE3B_{stabilizer.uuid}'
        and value == Const(0.7)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert any(
        variable.name == f'PssIEEE3B.ks2_PssIEEE3B_{stabilizer.uuid}'
        and value == Const(1.4)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )


def test_pss_rqb_exciter_and_governor_compose_to_detailed_machine() -> None:
    """Verify the required ExcRQB/PssRQB chain and mechanical-power source.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='rqb_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_rqb_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_rqb_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    excitation: ExcRQB = ExcRQB(rdfid='_rqb_exciter')
    stabilizer: PssRQB = PssRQB(rdfid='_rqb_stabilizer')
    overexcitation_limiter: OverexcLim2 = OverexcLim2(rdfid='_rqb_oel')
    overexcitation_limiter.koi = 0.0
    overexcitation_limiter.voimax = 1.0
    overexcitation_limiter.voimin = -1.0
    overexcitation_limiter.ifdlim = 1.0
    governor: GovSteam1 = GovSteam1(rdfid='_rqb_governor')
    governor.mwbase = 100.0
    governor.k = 25.0
    governor.t3 = 0.1
    governor.gv1 = 0.0
    governor.pgv1 = 0.0
    governor.gv2 = 0.2
    governor.pgv2 = 0.2
    governor.gv3 = 0.4
    governor.pgv3 = 0.4
    governor.gv4 = 0.6
    governor.pgv4 = 0.6
    governor.gv5 = 0.8
    governor.pgv5 = 0.8
    governor.gv6 = 1.0
    governor.pgv6 = 1.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    excitation.OverexcitationLimiterDynamics = overexcitation_limiter
    overexcitation_limiter.ExcitationSystemDynamics = excitation
    stabilizer.ExcitationSystemDynamics = excitation
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(idtag=machine.uuid, name='rqb_generator', P=50.0, Q=10.0)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['ExcRQB'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssRQB'].append(stabilizer)
    cgmes_model.dynamics_assets.lists['OverexcLim2'].append(overexcitation_limiter)
    cgmes_model.dynamics_assets.lists['GovSteam1'].append(governor)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'ExcRQB_{excitation.uuid}' in composite_template.name
    assert f'PssRQB_{stabilizer.uuid}' in composite_template.name
    assert f'GovSteam1_{governor.uuid}' in composite_template.name
    assert f'OverexcLim2_{overexcitation_limiter.uuid}' in composite_template.name
    assert find_block_variable_by_name(
        composite_template.block,
        f'PmPu_PssRQB_{stabilizer.uuid}',
    ) is None
    rqb_reference: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'UsRefPu_ExcRQB_{excitation.uuid}',
    )
    assert rqb_reference is not None
    rqb_reference_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        rqb_reference,
    )
    assert rqb_reference_initial is not None, (rqb_reference, rqb_reference_initial)
    assert not any(
        variable.name == rqb_reference.name
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.external_mapping.values()
    )
    pss_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VsPu_PssRQB_{stabilizer.uuid}',
    )
    assert pss_output is not None
    assert pss_output not in composite_template.block.in_vars
    oel_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'OelPu_OverexcLim2_{overexcitation_limiter.uuid}',
    )
    exciter_oel_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'OelPu_ExcRQB_{excitation.uuid}',
    )
    assert oel_output is not None
    assert exciter_oel_input is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_sk_binds_power_frequency_and_field_current_to_generator() -> None:
    """Check PssSK's three channels and exciter output on a detailed generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_sk_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_sk_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_pss_sk_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    excitation: ExcST1A = ExcST1A(rdfid='_pss_sk_exciter')
    stabilizer: PssSK = PssSK(rdfid='_pss_sk_stabilizer')
    stabilizer.k1 = -0.3
    stabilizer.k2 = -0.15
    stabilizer.k3 = 10.0
    generator: Generator = Generator(idtag=machine.uuid, name='pss_sk_generator', P=50.0, Q=10.0)
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssSK'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\\n'.join(entry.msg for entry in logger.entries)
    assert f'PssSK_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    for port_name in ('PePu', 'FrequencyDeviationPu', 'IfdPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_PssSK_{stabilizer.uuid}',
        ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    pss_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VsPu_PssSK_{stabilizer.uuid}',
    )
    assert pss_output is not None
    assert pss_output not in composite_template.block.in_vars


def test_pss_stab2a_maps_canonical_fields_and_composes_to_exciter() -> None:
    """Check the canonical STAB2A adapter through physical-device composition.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_stab2a_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_stab2a_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_stab2a_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_stab2a_exciter')
    stabilizer: PssSTAB2A = PssSTAB2A(rdfid='_pss_stab2a_stabilizer')
    stabilizer.k2 = 1.7
    stabilizer.k3 = 0.8
    stabilizer.k4 = 0.4
    stabilizer.k5 = 1.1
    stabilizer.t2 = 1.5
    stabilizer.t3 = 0.2
    stabilizer.t5 = 0.3
    stabilizer.hlim = 0.15
    generator: Generator = Generator(idtag=machine.uuid, name='pss_stab2a_generator', P=50.0, Q=10.0)
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssSTAB2A'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\\n'.join(entry.msg for entry in logger.entries)
    assert f'PssSTAB2A_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert any(
        variable.name == f'PssSTAB2A.k2_PssSTAB2A_{stabilizer.uuid}'
        and value == Const(1.7)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssSTAB2A_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    assert generator.rms_template is composite_template


def test_pss_ptist1_import_composes_and_balances_nonzero_power_point() -> None:
    """Check PssPTIST1 scalar mapping, machine signals, and exciter connection.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_ptist1_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_ptist1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_pss_ptist1_machine_dynamics',
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    excitation: ExcST1A = ExcST1A(rdfid='_pss_ptist1_exciter')
    stabilizer: PssPTIST1 = PssPTIST1(rdfid='_pss_ptist1_stabilizer')
    stabilizer.m = 0.3
    stabilizer.tf = 2.0
    stabilizer.tp = 0.1
    stabilizer.t1 = 0.2
    stabilizer.t2 = 0.5
    stabilizer.t3 = 0.1
    stabilizer.t4 = 0.4
    stabilizer.k = 1.2
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssPTIST1'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss_ptist1_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'PssPTIST1_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert any(
        variable.name == f'PssPTIST1.k_PssPTIST1_{stabilizer.uuid}'
        and value == Const(1.2)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_PssPTIST1_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssPTIST1_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VtPu_PssPTIST1_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    pss_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VsPu_PssPTIST1_{stabilizer.uuid}',
    )
    assert pss_output is not None
    assert pss_output not in composite_template.block.in_vars


def test_pss_ptist3_import_maps_discrete_fields_and_connects_machine_signals() -> None:
    """Check PTIST3 scalar conversion and machine/exciter signal composition.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_ptist3_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_ptist3_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_ptist3_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_ptist3_exciter')
    stabilizer: PssPTIST3 = PssPTIST3(rdfid='_pss_ptist3_stabilizer')
    stabilizer.m = 0.25
    stabilizer.tf = 2.0
    stabilizer.tp = 0.1
    stabilizer.t1 = 0.2
    stabilizer.t2 = 0.5
    stabilizer.t3 = 0.1
    stabilizer.t4 = 0.4
    stabilizer.k = 1.1
    stabilizer.dtf = 0.02
    stabilizer.dtp = 0.04
    stabilizer.dtc = 0.1
    stabilizer.a0 = 1.0
    stabilizer.b0 = 1.0
    stabilizer.a3 = 1.0
    stabilizer.b3 = 1.0
    stabilizer.isw = False
    stabilizer.nav = 3.0
    stabilizer.ncl = 2.0
    stabilizer.ncr = 4.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssPTIST3'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss_ptist3_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'PssPTIST3_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert any(
        variable.name == f'PssPTIST3.k_PssPTIST3_{stabilizer.uuid}'
        and value == Const(1.1)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert any(
        variable.name == f'PssPTIST3.nav_PssPTIST3_{stabilizer.uuid}'
        and value == Const(3.0)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_PssPTIST3_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssPTIST3_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VtPu_PssPTIST3_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    assert any(
        logic.name == f'PssPTIST3.SampledAverageAndLimit_PssPTIST3_{stabilizer.uuid}'
        for runtime_block in composite_template.block.get_all_blocks()
        for logic in runtime_block.procedural_logic
    )


def test_pss2st_import_connects_selected_signals_voltage_gate_and_exciter() -> None:
    """Check both Pss2ST selectors, voltage gating, and physical composition.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss2st_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss2st_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss2st_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss2st_exciter')
    stabilizer: Pss2ST = Pss2ST(rdfid='_pss2st_stabilizer')
    stabilizer.inputSignal1Type = InputSignalKind.rotorAngularFrequencyDeviation
    stabilizer.inputSignal2Type = InputSignalKind.generatorElectricalPower
    stabilizer.k1 = 1.25
    stabilizer.k2 = 0.75
    stabilizer.t1 = 0.2
    stabilizer.t2 = 0.3
    stabilizer.t3 = 0.4
    stabilizer.t4 = 2.0
    stabilizer.t5 = 0.1
    stabilizer.t6 = 0.5
    stabilizer.t7 = 0.2
    stabilizer.t8 = 0.6
    stabilizer.t9 = 0.1
    stabilizer.t10 = 0.4
    stabilizer.lsmax = 0.2
    stabilizer.lsmin = -0.2
    stabilizer.vcu = 1.1
    stabilizer.vcl = 0.9
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['Pss2ST'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss2st_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'Pss2ST_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    mapped_gain: bool = any(
        variable.name == f'Pss2ST.k1_Pss2ST_{stabilizer.uuid}'
        and value == Const(1.25)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert mapped_gain
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal1Pu_Pss2ST_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal2Pu_Pss2ST_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VctPu_Pss2ST_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VsPu_Pss2ST_{stabilizer.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None


def test_pss1_import_binds_machine_speed_power_and_preserves_frequency_host_input() -> None:
    """Check Pss1's distinct speed, power, frequency, and exciter paths.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss1_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss1_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss1_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss1_exciter')
    stabilizer: Pss1 = Pss1(rdfid='_pss1_stabilizer')
    stabilizer.kw = 0.4
    stabilizer.kf = 2.0
    stabilizer.kpe = 0.3
    stabilizer.pmin = 0.25
    stabilizer.ks = 1.4
    stabilizer.vsmn = -0.08
    stabilizer.vsmx = 0.08
    stabilizer.tpe = 0.05
    stabilizer.t5 = 3.5
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['Pss1'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss1_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'Pss1_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert any(
        variable.name == f'Pss1.ks_Pss1_{stabilizer.uuid}'
        and value == Const(1.4)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_Pss1_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_Pss1_{stabilizer.uuid}',
    ) is None
    frequency_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'FrequencyDeviationPu_Pss1_{stabilizer.uuid}',
    )
    assert frequency_input is not None
    assert frequency_input in composite_template.block.in_vars
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None


def test_pss1a_import_maps_delayed_selector_and_composes_terminal_voltage() -> None:
    """Check Pss1A delay, selected Pe input, Vct gate, and exciter connection.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss1a_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss1a_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss1a_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss1a_exciter')
    stabilizer: Pss1A = Pss1A(rdfid='_pss1a_stabilizer')
    stabilizer.inputSignalType = InputSignalKind.generatorElectricalPower
    stabilizer.a3 = 1.0
    stabilizer.a5 = 0.1
    stabilizer.a6 = 1.0
    stabilizer.a4 = 1.0
    stabilizer.a8 = 1.0
    stabilizer.t1 = 0.2
    stabilizer.t2 = 0.5
    stabilizer.t3 = 0.1
    stabilizer.t4 = 0.4
    stabilizer.t5 = 3.5
    stabilizer.t6 = 0.05
    stabilizer.ks = 1.3
    stabilizer.vrmax = 0.2
    stabilizer.vrmin = -0.2
    stabilizer.vcu = 1.1
    stabilizer.vcl = 0.9
    stabilizer.kd = True
    stabilizer.tdelay = 0.03
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['Pss1A'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss1a_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'Pss1A_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    assert any(
        variable.name == f'Pss1A.ks_Pss1A_{stabilizer.uuid}'
        and value == Const(1.3)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert any(
        variable.name == f'Pss1A.kd_Pss1A_{stabilizer.uuid}'
        and value == Const(True)
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert find_block_variable_by_name(
        composite_template.block,
        f'SignalPu_Pss1A_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VctPu_Pss1A_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VsPu_Pss1A_{stabilizer.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None


def test_pss2b_import_maps_dual_channels_and_connects_exciter() -> None:
    """Check Pss2B selector conversion and both physical machine channels.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss2b_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss2b_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss2b_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss2b_exciter')
    stabilizer: Pss2B = Pss2B(rdfid='_pss2b_stabilizer')
    stabilizer.inputSignal1Type = InputSignalKind.rotorSpeed
    stabilizer.inputSignal2Type = InputSignalKind.generatorElectricalPower
    stabilizer.ks1 = 4.0
    stabilizer.ks2 = 0.6
    stabilizer.ks3 = 0.8
    stabilizer.ks4 = 1.2
    stabilizer.n = 1
    stabilizer.m = 2
    stabilizer.vstmax = 0.1
    stabilizer.vstmin = -0.1
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['Pss2B'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss2b_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'Pss2B_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    for parameter_name, expected_value in (('ks1', 4.0), ('ks3', 0.8), ('ks4', 1.2)):
        assert any(
            variable.name == f'Pss2B.{parameter_name}_Pss2B_{stabilizer.uuid}'
            and value == Const(expected_value)
            for runtime_block in composite_template.block.get_all_blocks()
            for variable, value in runtime_block.event_dict.items()
        )
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal1Pu_Pss2B_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal2Pu_Pss2B_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VsPu_Pss2B_{stabilizer.uuid}',
    ) is not None


def test_pss5_speed_mode_import_connects_power_speed_and_exciter() -> None:
    """Check Pss5's speed-mode selector and machine/exciter signal wiring.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss5_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss5_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss5_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss5_exciter')
    stabilizer: Pss5 = Pss5(rdfid='_pss5_stabilizer')
    stabilizer.isfreq = True
    stabilizer.kpe = 0.45
    stabilizer.kf = 3.0
    stabilizer.kpss = 1.2
    stabilizer.pmm = 0.2
    stabilizer.tw1 = 3.5
    stabilizer.tpe = 0.05
    stabilizer.vsmn = -0.1
    stabilizer.vsmx = 0.1
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['Pss5'].append(stabilizer)
    generator: Generator = Generator(idtag=machine.uuid, name='pss5_generator', P=50.0, Q=10.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, '\n'.join(entry.msg for entry in logger.entries)
    assert f'Pss5_{stabilizer.uuid}' in composite_template.name
    assert f'ExcST1A_{excitation.uuid}' in composite_template.name
    for parameter_name, expected_value in (('kpe', 0.45), ('kf', 3.0), ('kpss', 1.2)):
        assert any(
            variable.name == f'Pss5.{parameter_name}_Pss5_{stabilizer.uuid}'
            and value == Const(expected_value)
            for runtime_block in composite_template.block.get_all_blocks()
            for variable, value in runtime_block.event_dict.items()
        )
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_Pss5_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_Pss5_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'FrequencyPu_Pss5_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'UpssPu_ExcST1A_{excitation.uuid}',
    ) is None


def test_invalid_pss_ieee4b_stage_is_retained_without_aborting_conversion() -> None:
    """Keep an improper PssIEEE4B RDF stage while importing other models.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='invalid_pss_ieee4b_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_invalid_pss_ieee4b_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_invalid_pss_ieee4b_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_invalid_pss_ieee4b_excitation')
    stabilizer: PssIEEE4B = PssIEEE4B(rdfid='_invalid_pss_ieee4b_stabilizer')
    stabilizer.tl1 = 0.1
    stabilizer.tl2 = 0.0
    generator: Generator = Generator(idtag=machine.uuid, name='invalid_pss_ieee4b_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssIEEE4B'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    assert generator.rms_template is not None
    assert any(
        'CGMES PssIEEE4B parameter topology is not realizable' in entry.msg
        and stabilizer.rdfid == entry.device
        for entry in logger.entries
    )


def test_pss_ieee4b_import_binds_speed_and_balances_composed_initial_point() -> None:
    """Check the valid PssIEEE4B mapping, machine signal, and initial residuals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_ieee4b_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_ieee4b_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_ieee4b_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_ieee4b_excitation')
    stabilizer: PssIEEE4B = PssIEEE4B(rdfid='_pss_ieee4b_stabilizer')
    stabilizer.kl = 8.0
    generator: Generator = Generator(idtag=machine.uuid, name='pss_ieee4b_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssIEEE4B'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'SpeedDeviationPu_PssIEEE4B_{stabilizer.uuid}',
    ) is None
    assert any(
        variable.name == f'PssIEEE4B.kl_PssIEEE4B_{stabilizer.uuid}'
        and isinstance(value, Const)
        and value.value == 8.0
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_pss_sh_import_maps_parameters_and_balances_composed_initial_point() -> None:
    """Check PssSH RDF conversion, electrical-power binding, and DAE balance.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_sh_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_sh_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_sh_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_sh_excitation')
    stabilizer: PssSH = PssSH(rdfid='_pss_sh_stabilizer')
    stabilizer.k = 1.7
    stabilizer.k0 = 0.2
    generator: Generator = Generator(idtag=machine.uuid, name='pss_sh_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssSH'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssSH_{stabilizer.uuid}',
    ) is None
    assert any(
        variable.name == f'PssSH.k_PssSH_{stabilizer.uuid}'
        and isinstance(value, Const)
        and value.value == 1.7
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_sb4_seeds_open_power_reference_from_machine_operating_point() -> None:
    """Seed PssSB4's unassociated reference to the measured machine power.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_sb4_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_sb4_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_sb4_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_sb4_excitation')
    stabilizer: PssSB4 = PssSB4(rdfid='_pss_sb4_stabilizer')
    stabilizer.tt = 0.2
    stabilizer.kx = 0.5
    stabilizer.tx2 = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='pss_sb4_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssSB4'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssSB4_{stabilizer.uuid}',
    ) is None
    power_reference: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'PRefPu_PssSB4_{stabilizer.uuid}',
    )
    assert power_reference is not None
    assert any(
        power_reference in runtime_block.in_vars
        for runtime_block in composite_template.block.get_all_blocks()
    )
    power_reference_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        power_reference,
    )
    assert isinstance(power_reference_initial, Var)
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_elin2_import_maps_filters_and_balances_nonzero_power_point() -> None:
    """Check PssELIN2 parameter conversion, Pe wiring, and DAE equilibrium.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_elin2_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_elin2_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_elin2_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_elin2_excitation')
    stabilizer: PssELIN2 = PssELIN2(rdfid='_pss_elin2_stabilizer')
    stabilizer.ts1 = 0.2
    stabilizer.ts2 = 0.3
    stabilizer.ts3 = 0.1
    stabilizer.ts4 = 2.0
    stabilizer.ts5 = 1.0
    stabilizer.ts6 = 0.5
    stabilizer.ks1 = 1.2
    stabilizer.ks2 = 0.8
    stabilizer.ppss = 1.5
    stabilizer.apss = 0.5
    stabilizer.psslim = 0.2
    generator: Generator = Generator(idtag=machine.uuid, name='pss_elin2_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssELIN2'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'PePu_PssELIN2_{stabilizer.uuid}',
    ) is None
    assert any(
        variable.name == f'PssELIN2.ks1_PssELIN2_{stabilizer.uuid}'
        and isinstance(value, Const)
        and value.value == 1.2
        for runtime_block in composite_template.block.get_all_blocks()
        for variable, value in runtime_block.event_dict.items()
    )
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pss_wecc_import_binds_selected_signals_and_balances_initial_point() -> None:
    """Check WECC PSS selector conversion and composed terminal-voltage gating.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='pss_wecc_bus')
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_pss_wecc_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_pss_wecc_machine_dynamics',
    )
    excitation: ExcST1A = ExcST1A(rdfid='_pss_wecc_excitation')
    stabilizer: PssWECC = PssWECC(rdfid='_pss_wecc_stabilizer')
    stabilizer.k1 = 0.7
    stabilizer.k2 = 0.3
    stabilizer.inputSignal1Type = InputSignalKind.generatorElectricalPower
    stabilizer.inputSignal2Type = InputSignalKind.rotorAngularFrequencyDeviation
    generator: Generator = Generator(idtag=machine.uuid, name='pss_wecc_machine')
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    excitation.SynchronousMachineDynamics = machine_dynamics
    excitation.PowerSystemStabilizerDynamics = stabilizer
    stabilizer.ExcitationSystemDynamics = excitation
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['ExcST1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['PssWECC'].append(stabilizer)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal1Pu_PssWECC_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'Signal2Pu_PssWECC_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'TerminalVoltagePu_PssWECC_{stabilizer.uuid}',
    ) is None
    voltage_reference: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'VoltageReferencePu_PssWECC_{stabilizer.uuid}',
    )
    assert voltage_reference is not None
    assert any(
        voltage_reference in runtime_block.in_vars
        for runtime_block in composite_template.block.get_all_blocks()
    )
    voltage_reference_initial: Expr | Const | None = find_block_initial_value(
        composite_template.block,
        voltage_reference,
    )
    assert isinstance(voltage_reference_initial, Var)
    assert voltage_reference_initial.name == 'Vm'
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_synchronous_machine_time_constant_reactance_parameter_template() -> None:
    """Retain selectors and scalar parameters without claiming equations.

    :return: None.
    """
    machine_parameters: tuple[tuple[str, float], ...] = (
        ('inertia', 4.0), ('damping', 0.0), ('nominalFrequency', 50.0),
        ('xDirectSync', 1.8), ('xDirectTrans', 0.3), ('xDirectSubtrans', 0.2),
        ('xQuadSync', 1.7), ('xQuadSubtrans', 0.2),
        ('tpdo', 5.0), ('tppdo', 0.04), ('tpqo', 0.7), ('tppqo', 0.0),
    )
    template: RmsModelTemplate = build_synchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name='salient_simplified',
        rotor_type=RotorKind.salientPole,
        model_type=SynchronousMachineModelKind.subtransientSimplified,
        parameters=machine_parameters,
    )
    machine_block: Block = template.block.children[0]
    assert len(machine_block.state_vars) == 0
    assert len(machine_block.state_eqs) == 0
    assert len(machine_block.algebraic_eqs) == 0
    assert len(machine_block.event_dict) == len(machine_parameters) + 2
    assert 'required operating-point bases are pending' in template.comment
    selector_values: dict[str, float | None] = dict()
    for selector_variable, selector_constant in machine_block.event_dict.items():
        selector_values[selector_variable.name.split('_')[0]] = selector_constant.value
    assert selector_values['rotorType'] == float(list(RotorKind).index(RotorKind.salientPole))
    assert selector_values['modelType'] == float(
        list(SynchronousMachineModelKind).index(SynchronousMachineModelKind.subtransientSimplified)
    )


def test_other_field_current_base_preserves_ampere_value_without_inventing_ratio() -> None:
    """Retain an explicit ampere base when its air-gap conversion is unknown.

    :return: None.
    """
    dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_other_field_current_base'
    )
    dynamics.ifdBaseType = IfdBaseKind.other
    dynamics.ifdBaseValue = 37.5
    parameters: dict[str, float] = dict(
        get_synchronous_machine_time_constant_reactance_parameters(dynamics, 50.0, 100.0)
    )
    assert parameters['ifdBaseType'] == float(list(IfdBaseKind).index(IfdBaseKind.other))
    assert parameters['ifdBaseValue'] == 37.5
    assert 'fieldCurrentBaseRatio' not in parameters


@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
@pytest.mark.parametrize(
    'model_type',
    (
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        SynchronousMachineModelKind.subtransientSimplified,
    ),
)
def test_synchronous_machine_time_constant_reactance_import_attaches_to_generator(
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> None:
    """Attach supported simplified models and retain their full RDF record.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='machine_bus')
    dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_machine_dynamics'
    )
    dynamics.rotorType = rotor_type
    dynamics.modelType = model_type
    dynamics.ifdBaseType = IfdBaseKind.ifag
    dynamics.ifdBaseValue = 37.5
    dynamics.inertia = 4.0
    dynamics.damping = 0.0
    dynamics.statorLeakageReactance = 0.12
    dynamics.statorResistance = 0.003
    dynamics.saturationFactor = 0.1
    dynamics.saturationFactor120 = 0.2
    dynamics.saturationFactorQAxis = 0.15
    dynamics.saturationFactor120QAxis = 0.25
    dynamics.efdBaseRatio = 1.1
    dynamics.xDirectSync = 1.8
    dynamics.xDirectTrans = 0.3
    dynamics.xDirectSubtrans = 0.2
    dynamics.xQuadSync = 1.7
    dynamics.xQuadTrans = 0.55
    dynamics.xQuadSubtrans = 0.2
    dynamics.tpdo = 5.0
    dynamics.tppdo = 0.04
    dynamics.tpqo = 0.7
    dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='machine')
    dynamics.SynchronousMachine = machine
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    machine_template: RmsModelTemplate | None = None
    for dynamic_template in veragrid_model.rms_models:
        if dynamic_template.device is generator and dynamic_template.name.startswith(
                'SynchronousMachineTimeConstantReactance_'
        ):
            machine_template = dynamic_template
        else:
            pass
    assert machine_template is not None
    runtime_block: Block | None = None
    parameter_block: Block | None = None
    for candidate_block in machine_template.block.children:
        if len(candidate_block.external_mapping) > 0:
            runtime_block = candidate_block
        else:
            parameter_block = candidate_block
    assert runtime_block is not None
    assert parameter_block is not None
    expected_state_count: int = 4 + int(rotor_type == RotorKind.roundRotor)
    if model_type == SynchronousMachineModelKind.subtransientSimplified:
        expected_state_count += 1
        armature_constant_variable: Var | None = None
        armature_constant_value: float | None = None
        for variable, value in runtime_block.event_dict.items():
            if variable.name.startswith('Taa') and isinstance(value, Const) and isinstance(value.value, (int, float)):
                armature_constant_variable = variable
                armature_constant_value = float(value.value)
            else:
                pass
        assert armature_constant_variable is not None
        assert armature_constant_value is not None
        x_ad: float = 1.8 - 0.12
        x_ad_leakage: float = 0.3 - 0.12
        x_fd: float = x_ad_leakage * x_ad / (x_ad - x_ad_leakage)
        x_subtransient_leakage: float = 0.2 - 0.12
        x_1d: float = (
            x_subtransient_leakage * x_ad * x_fd
            / (x_ad * x_fd - x_subtransient_leakage * (x_ad + x_fd))
        )
        r_1d: float = (
            x_ad * x_fd + x_1d * (x_ad + x_fd)
        ) / (2.0 * pi * 50.0 * 0.04 * (x_ad + x_fd))
        assert isclose(armature_constant_value, x_1d / r_1d, abs_tol=1.0e-12)
    else:
        pass
    assert len(runtime_block.state_vars) == expected_state_count
    expected_algebraic_equation_count: int = 11
    if model_type == SynchronousMachineModelKind.subtransientSimplifiedDirectAxis:
        expected_algebraic_equation_count += 1
    else:
        pass
    assert len(runtime_block.algebraic_eqs) == expected_algebraic_equation_count
    assert len(runtime_block.init_eqs) >= len(runtime_block.state_vars)
    assert VarPowerFlowReferenceType.P in runtime_block.external_mapping
    assert VarPowerFlowReferenceType.Q in runtime_block.external_mapping
    machine_parameters_by_name: dict[str, float | None] = dict()
    for event_block in machine_template.block.get_all_blocks():
        for parameter_variable, parameter_value in event_block.event_dict.items():
            machine_parameters_by_name[parameter_variable.name.split('_')[0]] = parameter_value.value
    assert machine_parameters_by_name['ifdBaseType'] == float(list(IfdBaseKind).index(IfdBaseKind.ifag))
    assert machine_parameters_by_name['ifdBaseValue'] == 37.5
    assert machine_parameters_by_name['statorLeakageReactance'] == 0.12
    assert machine_parameters_by_name['statorResistance'] == 0.003
    assert machine_parameters_by_name['saturationFactor'] == 0.1
    assert machine_parameters_by_name['saturationFactor120'] == 0.2
    assert machine_parameters_by_name['saturationFactorQAxis'] == 0.15
    assert machine_parameters_by_name['saturationFactor120QAxis'] == 0.25
    assert machine_parameters_by_name['efdBaseRatio'] == 1.1
    assert generator.rms_template is machine_template
    assert_zero_initial_residuals(
        template=machine_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    'model_type',
    (SynchronousMachineModelKind.subtransientTypeF, SynchronousMachineModelKind.subtransientTypeJ),
)
def test_cgmes_type_fj_machine_import_maps_and_attaches(
        model_type: SynchronousMachineModelKind,
) -> None:
    """Check Type F/J RDF conversion, physical attachment, and initialized machine equations.

    :param model_type: Canonical Type F or Type J selector.
    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_type_fj_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid=f'_{model_type.name}_machine_dynamics'
    )
    dynamics.rotorType = RotorKind.roundRotor
    dynamics.modelType = model_type
    dynamics.inertia = 4.0
    dynamics.damping = 0.0
    dynamics.statorResistance = 0.003
    dynamics.statorLeakageReactance = 0.12
    dynamics.saturationFactor = 0.1
    dynamics.saturationFactor120 = 0.2
    dynamics.ks = 0.05 if model_type == SynchronousMachineModelKind.subtransientTypeJ else 0.0
    dynamics.xDirectSync = 1.8
    dynamics.xDirectTrans = 0.3
    dynamics.xDirectSubtrans = 0.2
    dynamics.xQuadSync = 1.7
    dynamics.xQuadTrans = 0.55
    dynamics.xQuadSubtrans = 0.2
    dynamics.tpdo = 5.0
    dynamics.tppdo = 0.04
    dynamics.tpqo = 0.7
    dynamics.tppqo = 0.05
    dynamics.SynchronousMachine = machine
    generator: Generator = Generator(idtag=machine.uuid, name='type_fj_machine', P=50.0)
    veragrid_model.add_bus(Bus(name='type_fj_bus'))
    veragrid_model.add_generator(bus=veragrid_model.buses[0], api_obj=generator)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(dynamics)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate | None = generator.rms_template
    assert template is not None
    assert len(template.block.children[1].state_vars) == 6
    assert find_block_variable_by_name(template.block, 'IfdPu') is None
    assert find_block_variable_by_name(template.block, 'ItPu') is not None
    assert any(
        variable.name.casefold() == 'ks'
        and isinstance(value, Const)
        and value.value == dynamics.ks
        for variable, value in template.block.children[1].event_dict.items()
    )
    assert find_block_variable_by_name(template.block, 'IfdPu') is None
    assert_zero_initial_residuals(
        template=template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.2,
        },
    )


def test_asynchronous_machine_uses_network_frequency() -> None:
    """Use the circuit frequency instead of the RMS builder's default 50 Hz.

    :return: None.
    """
    template: RmsModelTemplate = build_asynchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name='asynchronous_frequency_check',
        nominal_frequency_hz=60.0,
    )
    frequency_values: list[float] = list()
    for block in template.block.get_all_blocks():
        for variable, value in block.event_dict.items():
            if variable.name == 'FNomHz_asynchronous_frequency_check':
                frequency_values.append(value.value)
            else:
                pass
    assert frequency_values == [60.0]


def test_load_motor_uses_network_frequency() -> None:
    """Use circuit frequency in the CGMES aggregate motor equations.

    :return: None.
    """
    template: RmsModelTemplate = build_load_motor_template(
        vfactory=VarFactory(),
        name='load_motor_frequency_check',
        nominal_frequency_hz=60.0,
    )
    frequency_values: list[float] = list()
    for block in template.block.get_all_blocks():
        for variable, value in block.event_dict.items():
            if variable.name == 'FNomHz_load_motor_frequency_check':
                frequency_values.append(value.value)
            else:
                pass
    assert frequency_values == [60.0]


def test_asynchronous_equivalent_circuit_converts_to_time_constant_model() -> None:
    """Convert the canonical EA912 equivalent circuit into the shared equations.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(fbase=60.0)
    machine: CgmesAsynchronousMachine = CgmesAsynchronousMachine(
        rdfid='_async_equivalent_machine'
    )
    machine.ratedS = 100.0
    dynamics: AsynchronousMachineEquivalentCircuit = AsynchronousMachineEquivalentCircuit(
        rdfid='_async_equivalent_dynamics'
    )
    dynamics.AsynchronousMachine = machine
    dynamics.xm = 3.0
    dynamics.xlr1 = 0.3
    dynamics.xlr2 = 0.1
    dynamics.rr1 = 0.02
    dynamics.rr2 = 0.04
    dynamics.statorLeakageReactance = 0.1
    dynamics.statorResistance = 0.01
    dynamics.inertia = 1.2
    dynamics.damping = 0.0
    dynamics.saturationFactor = 0.03
    dynamics.saturationFactor120 = 0.1
    generator: Generator = Generator(idtag=machine.uuid, name='async_equivalent_generator', P=50.0)
    veragrid_model.add_bus(Bus(name='async_equivalent_bus'))
    veragrid_model.add_generator(bus=veragrid_model.buses[0], api_obj=generator)
    cgmes_model.dynamics_assets.lists['AsynchronousMachineEquivalentCircuit'].append(dynamics)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    assert len(veragrid_model.rms_models) == 1
    template: RmsModelTemplate = veragrid_model.rms_models[0]
    assert template.device is generator
    expected_values: dict[str, float] = {
        'xs': 3.1,
        'xp': 0.1 + 3.0 * 0.3 / 3.3,
        'xpp': 0.1 + (3.0 * 0.3 * 0.1) / (3.0 * 0.3 + 3.0 * 0.1 + 0.3 * 0.1),
        'tpo': 3.3 / (2.0 * pi * 60.0 * 0.02),
        'tppo': (3.0 * 0.3 + 3.0 * 0.1 + 0.3 * 0.1)
        / (2.0 * pi * 60.0 * 0.04 * 3.3),
        'statorResistance': 0.01,
        'inertia': 1.2,
        'damping': 0.0,
        'statorLeakageReactance': 0.1,
        'saturationFactor': 0.03,
        'saturationFactor120': 0.1,
    }
    observed_values: dict[str, float] = dict()
    for block in template.block.get_all_blocks():
        for variable, value in block.event_dict.items():
            for parameter_name, expected_value in expected_values.items():
                if (
                        variable.name.startswith(
                            f'AsynchronousMachineTimeConstantReactance.{parameter_name}_'
                        )
                        and isinstance(value, Const)
                        and isinstance(value.value, (float, int))
                ):
                    observed_values[parameter_name] = float(value.value)
                else:
                    pass
    assert observed_values.keys() == expected_values.keys()
    for parameter_name, expected_value in expected_values.items():
        assert isclose(observed_values[parameter_name], expected_value, abs_tol=1.0e-12)


@pytest.mark.parametrize(
    'governor_kind', (
        'GovSteam0', 'GovSteam1', 'GovSteam2', 'GovGAST', 'GovGAST1', 'GovGAST2', 'GovGAST3', 'GovGAST4',
        'GovGASTWD', 'GovHydro1', 'GovHydro2', 'GovHydro3', 'GovHydroDD',
        'GovHydroDD_cv', 'GovHydroFrancis_mechanical',
        'GovHydroFrancis_transient', 'GovHydroFrancis_electrohydraulic',
        'GovHydroIEEE0', 'GovHydroIEEE2',
        'GovHydroPelton',
        'GovHydro4_simple', 'GovHydro4_francis_pelton', 'GovHydro4_kaplan',
        'GovHydro3_double_derivative', 'GovSteamIEEE1',
        pytest.param(
            'GovSteamEU',
            marks=pytest.mark.xfail(
                reason=(
                    'IEC 61970-302:2023-06 §5.3.6.52 note 7 assumes zero losses; '
                    'the solved induction-machine point has shaft/electrical power mismatch'
                ),
                strict=True,
            ),
        ),
        'GovSteamFV2', 'GovSteamFV4',
    ),
)
def test_asynchronous_machine_composes_governor_at_nonzero_pq(
        governor_kind: str,
) -> None:
    """Balance canonical asynchronous-machine governor associations at nonzero P/Q.

    :param governor_kind: CGMES governor class selected for composition.
    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    machine: CgmesAsynchronousMachine = CgmesAsynchronousMachine(
        rdfid='_async_governed_machine',
    )
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: AsynchronousMachineTimeConstantReactance = (
        AsynchronousMachineTimeConstantReactance(rdfid='_async_governed_dynamics')
    )
    machine_dynamics.AsynchronousMachine = machine
    machine_dynamics.xs = 3.0
    machine_dynamics.xp = 0.3
    machine_dynamics.xpp = 0.2
    machine_dynamics.tpo = 0.6
    machine_dynamics.tppo = 0.05
    machine_dynamics.inertia = 1.2
    machine_dynamics.damping = 0.0
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.statorLeakageReactance = 0.1
    # This reactive point is solved against the active shared double-cage equations.
    governor: (
        GovSteam0 | GovSteam1 | GovSteam2 | GovGAST | GovGAST1 | GovGAST2 | GovGAST3 | GovGAST4
        | GovGASTWD | GovHydro1 | GovHydro2 | GovHydro3 | GovHydroDD | GovHydroFrancis
        | GovHydroIEEE0 | GovHydroIEEE2
        | GovHydroPelton
        | GovHydro4 | GovSteamIEEE1 | GovSteamEU | GovSteamFV2 | GovSteamFV4
    )
    if governor_kind == 'GovSteam0':
        governor = GovSteam0(rdfid='_async_governed_gov_steam0')
        governor.r = 0.04
        governor.t1 = 0.0
        governor.vmax = 1.1
        governor.vmin = 0.1
        governor.t2 = 0.0
        governor.t3 = 0.0
        governor.dt = 0.08
    elif governor_kind == 'GovSteam1':
        governor = GovSteam1(rdfid='_async_governed_gov_steam1')
        governor.k = 25.0
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.1
        governor.t4 = 0.3
        governor.t5 = 5.0
        governor.t6 = 0.5
        governor.t7 = 0.0
        governor.uo = 0.12
        governor.uc = -0.14
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.valve = True
        governor.gv1 = 0.0
        governor.pgv1 = 0.0
        governor.gv2 = 0.2
        governor.pgv2 = 0.2
        governor.gv3 = 0.4
        governor.pgv3 = 0.4
        governor.gv4 = 0.6
        governor.pgv4 = 0.6
        governor.gv5 = 0.8
        governor.pgv5 = 0.8
        governor.gv6 = 1.0
        governor.pgv6 = 1.0
    elif governor_kind == 'GovGAST4':
        governor = GovGAST4(rdfid='_async_governed_gov_gast4')
        governor.bp = 0.04
        governor.tv = 0.2
        governor.ta = 4.0
        governor.tc = 0.6
        governor.tcm = 0.15
        governor.ktm = 0.25
        governor.tm = 0.3
        governor.rymx = 1.2
        governor.rymn = 0.05
        governor.mxef = 0.06
        governor.mnef = -0.04
    elif governor_kind == 'GovGAST1':
        governor = GovGAST1(rdfid='_async_governed_gov_gast1')
        governor.mwbase = 80.0
        governor.r = 0.04
        governor.t1 = 0.2
        governor.t2 = 0.3
        governor.t3 = 1.0
        governor.lmax = 1.0
        governor.kt = 0.5
        governor.vmax = 1.0
        governor.vmin = 0.0
        governor.fidle = 0.18
        governor.rmax = 1.0
        governor.loadinc = 0.125
        governor.tltr = 5.0
        governor.ltrate = 0.02
        governor.a = 0.8
        governor.b = 1.0
        governor.db1 = 0.0
        governor.eps = 0.0
        governor.db2 = 0.0
        governor.gv1 = 0.0
        governor.pgv1 = 0.0
        governor.gv2 = 0.2
        governor.pgv2 = 0.2
        governor.gv3 = 0.4
        governor.pgv3 = 0.4
        governor.gv4 = 0.6
        governor.pgv4 = 0.6
        governor.gv5 = 0.8
        governor.pgv5 = 0.8
        governor.gv6 = 1.0
        governor.pgv6 = 1.0
        governor.ka = 1.0
        governor.t4 = 0.1
        governor.t5 = 0.2
    elif governor_kind == 'GovGAST2':
        governor = GovGAST2(rdfid='_async_governed_gov_gast2')
        governor.mwbase = 80.0
        governor.w = 20.0
        governor.x = 0.0
        governor.y = 0.1
        governor.z = 1
        governor.etd = 0.0
        governor.tcd = 0.0
        governor.trate = 80.0
        governor.t = 0.0
        governor.tmax = 1.0
        governor.tmin = 0.0
        governor.ecr = 0.0
        governor.k3 = 1.0
        governor.a = 1.0
        governor.b = 1.0
        governor.c = 1.0
        governor.tf = 0.0
        governor.kf = 0.0
        governor.k5 = 0.0
        governor.k4 = 1.0
        governor.t3 = 0.0
        governor.t4 = 0.0
        governor.tt = 0.0
        governor.t5 = 0.0
        governor.af1 = 0.0
        governor.bf1 = 0.0
        governor.af2 = 0.0
        governor.bf2 = 1.0
        governor.cf2 = 0.23
        governor.tr = 1.0
        governor.k6 = 0.0
        governor.tc = 1.0
    elif governor_kind == 'GovGAST':
        governor = GovGAST(rdfid='_async_governed_gov_gast')
        governor.mwbase = 80.0
        governor.r = 0.04
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.0
        governor.at = 0.95
        governor.kt = 2.5
        governor.vmax = 1.1
        governor.vmin = 0.1
        governor.dturb = 0.08
    elif governor_kind == 'GovGAST3':
        governor = GovGAST3(rdfid='_async_governed_gov_gast3')
        governor.bp = 0.05
        governor.tg = 0.05
        governor.rcmx = 1.0
        governor.rcmn = -0.1
        governor.ky = 1.0
        governor.ty = 0.2
        governor.tac = 0.1
        governor.kac = 0.0
        governor.tc = 0.2
        governor.bca = 0.005
        governor.kca = 10.0
        governor.dtc = 390.0
        governor.ka = 0.23
        governor.tsi = 1.0
        governor.ksi = 0.5
        governor.ttc = 1.0
        governor.tfen = 540.0
        governor.td = 0.1
        governor.tt = 1.0
        governor.mxef = 0.05
        governor.mnef = -0.05
    elif governor_kind == 'GovGASTWD':
        governor = GovGASTWD(rdfid='_async_governed_gov_gastwd')
        governor.mwbase = 80.0
        governor.trate = 80.0
    elif governor_kind == 'GovSteam2':
        governor = GovSteam2(rdfid='_async_governed_gov_steam2')
        governor.k = 20.0
        governor.dbf = 0.01
        governor.t1 = 0.45
        governor.t2 = 0.1
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.mxef = 1.0
        governor.mnef = -1.0
    elif governor_kind == 'GovSteamIEEE1':
        governor = GovSteamIEEE1(rdfid='_async_governed_gov_steam_ieee1')
        governor.mwbase = 80.0
        governor.k = 31.0
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.25
        governor.uo = 0.12
        governor.uc = -0.14
        governor.pmax = 1.1
        governor.pmin = 0.1
        governor.t4 = 0.2
        governor.k1 = 0.3
        governor.k2 = 0.0
        governor.k3 = 0.3
        governor.k4 = 0.0
        governor.k5 = 0.2
        governor.k6 = 0.0
        governor.k7 = 0.2
        governor.k8 = 0.0
    elif governor_kind == 'GovSteamEU':
        governor = GovSteamEU(rdfid='_async_governed_gov_steam_eu')
        governor.mwbase = 80.0
        governor.tp = 0.07
        governor.ke = 0.65
        governor.tip = 2.0
        governor.tdp = 0.1
        governor.tfp = 0.2
        governor.tf = 0.5
        governor.kfcor = 20.0
        governor.db1 = 0.0
        governor.wfmax = 0.05
        governor.wfmin = -0.05
        governor.pmax = 1.0
        governor.ten = 0.1
        governor.tw = 0.5
        governor.komegacor = 20.0
        governor.db2 = 0.0004
        governor.wwmax = 0.1
        governor.wwmin = -1.0
        governor.wmax1 = 1.025
        governor.wmax2 = 1.05
        governor.tvhp = 0.1
        governor.cho = 0.17
        governor.chc = -3.3
        governor.hhpmax = 1.0
        governor.tvip = 0.15
        governor.cio = 0.123
        governor.cic = -2.2
        governor.simx = 0.425
        governor.thp = 0.31
        governor.trh = 8.0
        governor.tlp = 0.45
        governor.prhmax = 1.4
        governor.khp = 0.277
        governor.klp = 0.723
        governor.tb = 100.0
    elif governor_kind == 'GovSteamFV2':
        governor = GovSteamFV2(rdfid='_async_governed_gov_steam_fv2')
        governor.mwbase = 80.0
        governor.t1 = 0.2
        governor.vmax = 1.0
        governor.vmin = 0.0
        governor.k = 0.3
        governor.t3 = 0.3
        governor.dt = 0.04
        governor.tt = 0.4
        governor.r = 0.05
        governor.ta = 0.1
        governor.tb = 0.2
        governor.tc = 0.5
        governor.ti = 0.0
    elif governor_kind == 'GovSteamFV4':
        governor = GovSteamFV4(rdfid='_async_governed_gov_steam_fv4')
    elif governor_kind == 'GovHydro1':
        governor = GovHydro1(rdfid='_async_governed_gov_hydro1')
        governor.mwbase = 80.0
        governor.rperm = 0.05
        governor.rtemp = 0.3
        governor.tr = 5.0
        governor.tf = 0.05
        governor.tg = 0.5
        governor.velm = 0.2
        governor.gmax = 1.0
        governor.gmin = 0.0
        governor.tw = 1.0
        governor.at = 1.0
        governor.dturb = 0.02
        governor.qnl = 0.08
        governor.hdam = 1.21
    elif governor_kind == 'GovHydro2':
        governor = GovHydro2(rdfid='_async_governed_gov_hydro2')
        governor.mwbase = 80.0
        governor.db1 = 0.12
        governor.eps = 0.02
    elif governor_kind.startswith('GovHydro3'):
        governor = GovHydro3(rdfid='_async_governed_gov_hydro3')
        governor.mwbase = 80.0
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.governorControl = governor_kind != 'GovHydro3_double_derivative'
        governor.rgate = 0.05
        governor.relec = 0.05
        governor.td = 0.1
        governor.tf = 0.1
        governor.tp = 0.1
        governor.velop = 0.2
        governor.velcl = -0.2
        governor.k1 = 1.0
        governor.k2 = 0.2
        governor.ki = 0.5
        governor.kg = 1.0
        governor.tt = 0.5
        governor.tw = 2.0
        governor.at = 1.2
        governor.dturb = 0.2
        governor.qnl = 0.0
        governor.h0 = 1.0
    elif governor_kind.startswith('GovHydroDD'):
        governor = GovHydroDD(rdfid='_async_governed_gov_hydro_dd')
        governor.mwbase = 80.0
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.r = 0.05
        governor.td = 0.1
        governor.tf = 0.1
        governor.tp = 0.1
        governor.velop = 0.2
        governor.velcl = 0.2
        governor.k1 = 1.0
        governor.k2 = 0.2
        governor.ki = 0.5
        governor.kg = 1.0
        governor.tturb = 1.0
        governor.aturb = -1.0
        governor.bturb = 0.5
        governor.tt = 0.5
        governor.gv1 = 0.0
        governor.pgv1 = 0.0
        governor.gv2 = 0.2
        governor.pgv2 = 0.2
        governor.gv3 = 0.4
        governor.pgv3 = 0.4
        governor.gv4 = 0.6
        governor.pgv4 = 0.6
        governor.gv5 = 0.8
        governor.pgv5 = 0.8
        governor.gv6 = 1.0
        governor.pgv6 = 1.0
        governor.gmax = 1.0
        governor.gmin = 0.0
        governor.inputSignal = governor_kind != 'GovHydroDD_cv'
    elif governor_kind.startswith('GovHydroFrancis'):
        governor = GovHydroFrancis(rdfid='_async_governed_gov_hydro_francis')
        if governor_kind == 'GovHydroFrancis_transient':
            governor.governorControl = FrancisGovernorControlKind.mechanicHydraulicTransientFeedback
        elif governor_kind == 'GovHydroFrancis_electrohydraulic':
            governor.governorControl = FrancisGovernorControlKind.electromechanicalElectrohydraulic
        else:
            governor.governorControl = FrancisGovernorControlKind.mechanicHydrolicTachoAccelerator
        governor.waterTunnelSurgeChamberSimulation = False
        governor.am = 0.7
        governor.av0 = 30.0
        governor.av1 = 700.0
        governor.bp = 0.05
        governor.db1 = 0.0
        governor.etamax = 1.05
        governor.h1 = 4.0
        governor.h2 = 40.0
        governor.hn = 250.0
        governor.kc = 0.025
        governor.kg = 0.025
        governor.kt = 0.25
        governor.qc0 = 0.1
        governor.qn = 250.0
        governor.ta = 3.0
        governor.td = 0.1
        governor.ts = 0.5
        governor.twnc = 1.0
        governor.twng = 3.0
        governor.tx = 1.0
        governor.va = 0.06
        governor.valvmax = 1.1
        governor.valvmin = 0.0
        governor.vc = -0.06
        governor.zsfc = 25.0
    elif governor_kind == 'GovHydroIEEE0':
        governor = GovHydroIEEE0(rdfid='_async_governed_gov_hydro_ieee0')
        governor.mwbase = 80.0
        governor.k = 20.0
        governor.t1 = 0.25
        governor.t2 = 0.0
        governor.t3 = 0.1
        governor.t4 = 0.0
        governor.pmax = 1.0
        governor.pmin = 0.0
    elif governor_kind == 'GovHydroIEEE2':
        governor = GovHydroIEEE2(rdfid='_async_governed_gov_hydro_ieee2')
        governor.mwbase = 80.0
        governor.tg = 0.5
        governor.tp = 0.03
        governor.uo = 0.1
        governor.uc = -0.1
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.rperm = 0.05
        governor.rtemp = 0.5
        governor.tr = 12.0
        governor.tw = 2.0
        governor.kturb = 1.0
        governor.aturb = -1.0
        governor.bturb = 0.5
        governor.gv1 = 0.0
        governor.gv2 = 0.2
        governor.gv3 = 0.4
        governor.gv4 = 0.6
        governor.gv5 = 0.8
        governor.gv6 = 1.0
        governor.pgv1 = 0.0
        governor.pgv2 = 0.16
        governor.pgv3 = 0.34
        governor.pgv4 = 0.55
        governor.pgv5 = 0.79
        governor.pgv6 = 1.0
    elif governor_kind == 'GovHydroPelton':
        governor = GovHydroPelton(rdfid='_async_governed_gov_hydro_pelton')
        governor.av0 = 30.0
        governor.av1 = 700.0
        governor.bp = 0.05
        governor.db1 = 0.0
        governor.db2 = 0.01
        governor.h1 = 4.0
        governor.h2 = 40.0
        governor.hn = 250.0
        governor.kc = 0.025
        governor.kg = 0.025
        governor.qc0 = 0.1
        governor.qn = 250.0
        governor.simplifiedPelton = True
        governor.staticCompensating = False
        governor.ta = 3.0
        governor.ts = 0.5
        governor.tv = 0.3
        governor.twnc = 1.0
        governor.twng = 3.0
        governor.tx = 0.5
        governor.va = 0.06
        governor.valvmax = 1.1
        governor.valvmin = 0.0
        governor.vav = 0.1
        governor.vc = -0.06
        governor.vcv = -0.1
        governor.waterTunnelSurgeChamberSimulation = False
        governor.zsfc = 25.0
    elif governor_kind.startswith('GovHydro4'):
        governor = GovHydro4(rdfid='_async_governed_gov_hydro4')
        governor.mwbase = 80.0
        if governor_kind == 'GovHydro4_kaplan':
            governor.model = GovHydro4ModelKind.kaplan
        elif governor_kind == 'GovHydro4_francis_pelton':
            governor.model = GovHydro4ModelKind.francisPelton
        else:
            governor.model = GovHydro4ModelKind.simple
        governor.gmax = 1.0
        governor.gmin = 0.0
        governor.tg = 0.5
        governor.tp = 0.1
        governor.uo = 0.2
        governor.uc = -0.2
        governor.rperm = 0.05
        governor.rtemp = 0.3
        governor.tr = 5.0
        governor.tw = 1.0
        governor.at = 1.2
        governor.dturb = 0.2
        governor.hdam = 1.0
        governor.qnl = 0.08
        governor.db1 = 0.0
        governor.eps = 0.0
        governor.db2 = 0.0
        if governor_kind == 'GovHydro4_kaplan':
            governor.bmax = 1.2
            governor.tblade = 3.0
            governor.gv0 = 0.0
            governor.gv1 = 0.2
            governor.gv2 = 0.4
            governor.gv3 = 0.6
            governor.gv4 = 0.8
            governor.gv5 = 0.9
            governor.pgv0 = 0.0
            governor.pgv1 = 0.18
            governor.pgv2 = 0.36
            governor.pgv3 = 0.54
            governor.pgv4 = 0.72
            governor.pgv5 = 0.9
            governor.bgv0 = 0.0
            governor.bgv1 = 0.1
            governor.bgv2 = 0.22
            governor.bgv3 = 0.37
            governor.bgv4 = 0.56
            governor.bgv5 = 0.75
        else:
            pass
    if isinstance(governor, (GovSteam0, GovSteam1)):
        governor.mwbase = 80.0
    else:
        pass
    governor.AsynchronousMachineDynamics = machine_dynamics
    machine_dynamics.TurbineGovernorDynamics = governor
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='async_governed_generator',
        P=50.0,
        Q=-35.28582188560699,
    )
    generator.Snom = 100.0
    bus: Bus = Bus(name='async_governed_bus')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['AsynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists[governor.__class__.__name__].append(governor)

    conversion_logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=conversion_logger,
    )

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None, [entry.msg for entry in conversion_logger.entries]
    assert governor.__class__.__name__ in composite.name, [
        entry.msg for entry in conversion_logger.entries
    ]
    if governor_kind == 'GovSteamFV2':
        fast_valving_time: Var | None = None
        for equation_block in composite.block.get_all_blocks():
            for equation_collection in (equation_block.algebraic_eqs, equation_block.state_eqs):
                for equation in equation_collection:
                    for equation_variable in equation.get_vars():
                        if equation_variable.name == 'glob_time':
                            fast_valving_time = equation_variable
                        else:
                            pass
        assert fast_valving_time is not None
        composite.block.update_model(fast_valving_time, Const(0.0))
    else:
        pass
    assert_zero_initial_residuals(
        template=composite,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            # Use the current shared induction equations' P/Q-consistent operating point.
            VarPowerFlowReferenceType.Q: -0.3528582188560699,
        },
    )


def test_synchronous_equivalent_circuit_converts_and_attaches_to_generator() -> None:
    """Convert a zero-Canay round-rotor circuit through the EA880 equations.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0, Sbase=100.0)
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_sync_equivalent_machine'
    )
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    dynamics: SynchronousMachineEquivalentCircuit = SynchronousMachineEquivalentCircuit(
        rdfid='_sync_equivalent_dynamics'
    )
    dynamics.SynchronousMachine = machine
    dynamics.xad = 1.8
    dynamics.rfd = 0.001
    dynamics.xfd = 0.3
    dynamics.r1d = 0.02
    dynamics.x1d = 0.1
    dynamics.xf1d = 0.0
    dynamics.xaq = 1.7
    dynamics.r1q = 0.03
    dynamics.x1q = 0.55
    dynamics.r2q = 0.04
    dynamics.x2q = 0.2
    dynamics.statorLeakageReactance = 0.12
    dynamics.statorResistance = 0.003
    dynamics.inertia = 4.0
    dynamics.saturationFactor = 0.1
    dynamics.saturationFactor120 = 0.2
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='sync_equivalent_generator',
        P=50.0,
        Q=10.0,
    )
    veragrid_model.add_bus(Bus(name='sync_equivalent_bus'))
    veragrid_model.add_generator(bus=veragrid_model.buses[0], api_obj=generator)
    cgmes_model.dynamics_assets.lists['SynchronousMachineEquivalentCircuit'].append(dynamics)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    assert len(veragrid_model.rms_models) == 1
    template: RmsModelTemplate = veragrid_model.rms_models[0]
    assert template.device is generator
    assert template.name.startswith('SynchronousMachineEquivalentCircuit_')
    assert 'converted to the existing zero-Canay subtransient realization' in template.comment
    expected_values: dict[str, float] = {
        'xDirectSync': 1.92,
        'xDirectTrans': 0.12 + 1.8 * 0.3 / 2.1,
        'xDirectSubtrans': 0.12 + 1.8 * 0.3 * 0.1 / (1.8 * 0.3 + 1.8 * 0.1 + 0.3 * 0.1),
        'xQuadSync': 1.82,
        'xQuadTrans': 0.12 + 1.7 * 0.55 / 2.25,
        'xQuadSubtrans': 0.12 + 1.7 * 0.55 * 0.2 / (1.7 * 0.55 + 1.7 * 0.2 + 0.55 * 0.2),
        'tc': 0.0,
    }
    observed_values: dict[str, float] = dict()
    for block in template.block.get_all_blocks():
        for variable, value in block.event_dict.items():
            for parameter_name, expected_value in expected_values.items():
                if (
                        variable.name.startswith(
                            f'{parameter_name}_SynchronousMachineEquivalentCircuit_'
                        )
                        and isinstance(value, Const)
                        and isinstance(value.value, (float, int))
                ):
                    observed_values[parameter_name] = float(value.value)
                else:
                    pass
    assert observed_values.keys() == expected_values.keys()
    for parameter_name, expected_value in expected_values.items():
        assert isclose(observed_values[parameter_name], expected_value, abs_tol=1.0e-12)


def test_wind_type1a_parameter_records_follow_rdf_machine_association() -> None:
    """Attach type 1a and its required aerodynamic record through RDF links.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    asynchronous_machine: CgmesAsynchronousMachine = CgmesAsynchronousMachine(
        rdfid='_wind_type1a_equipment'
    )
    asynchronous_dynamics: AsynchronousMachineDynamics = AsynchronousMachineDynamics(
        rdfid='_wind_type1a_machine_dynamics'
    )
    turbine: WindGenTurbineType1aIEC = WindGenTurbineType1aIEC(rdfid='_wind_type1a_dynamics')
    aerodynamic: WindAeroConstIEC = WindAeroConstIEC(rdfid='_wind_type1a_aero')
    mechanical: WindMechIEC = WindMechIEC(rdfid='_wind_type1a_mechanical')
    asynchronous_dynamics.AsynchronousMachine = asynchronous_machine
    asynchronous_machine.ratedS = 100.0
    asynchronous_machine.ratedPowerFactor = 0.8
    asynchronous_dynamics.WindTurbineType1or2Dynamics = turbine
    turbine.AsynchronousMachineDynamics = asynchronous_dynamics
    turbine.WindAeroConstIEC = aerodynamic
    turbine.WindMechIEC = mechanical
    aerodynamic.WindGenTurbineType1aIEC = turbine
    mechanical.WindTurbineType1or2IEC = turbine
    generator: Generator = Generator(idtag=asynchronous_machine.uuid, name='wind_type1a')
    generator.Snom = 100.0
    generator.P = 50.0
    veragrid_model.add_bus(Bus(name='wind_type1a_bus'))
    veragrid_model.add_generator(bus=veragrid_model.buses[0], api_obj=generator)
    cgmes_model.dynamics_assets.lists['WindGenTurbineType1aIEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindAeroConstIEC'].append(aerodynamic)
    cgmes_model.dynamics_assets.lists['WindMechIEC'].append(mechanical)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    attached_names: set[str] = set()
    for runtime_model in veragrid_model.rms_models:
        if runtime_model.device is generator:
            attached_names.add(runtime_model.name.split('_')[0])
        else:
            pass
    assert 'WindMechIEC' in attached_names
    wind_chain: RmsModelTemplate | None = None
    for runtime_model in veragrid_model.rms_models:
        if runtime_model.device is generator and 'with_WindMechIEC_' in runtime_model.name:
            wind_chain = runtime_model
        else:
            pass
    assert wind_chain is not None
    constant_power: Var | None = find_block_variable_by_name(
        wind_chain.block,
        f'PaeroPu_WindMechIEC_{mechanical.uuid}',
    )
    turbine_speed: Var | None = find_block_variable_by_name(
        wind_chain.block,
        f'OmegaWtrPu_WindMechIEC_{mechanical.uuid}',
    )
    assert constant_power is not None
    assert turbine_speed is not None
    assert all(
        constant_power not in runtime_block.in_vars
        for runtime_block in wind_chain.block.get_all_blocks()
    )
    constant_power_equation: Expr | None = None
    for runtime_block in wind_chain.block.get_all_blocks():
        if constant_power in runtime_block.algebraic_vars:
            constant_power_equation = runtime_block.algebraic_eqs[
                runtime_block.algebraic_vars.index(constant_power)
            ]
        else:
            pass
    assert constant_power_equation is not None
    constant_power_dependencies: set[str] = set(
        variable.name for variable in constant_power_equation.get_vars()
    )
    assert constant_power.name in constant_power_dependencies
    assert turbine_speed.name in constant_power_dependencies
    constant_power_initial: Expr | Const | None = None
    for runtime_block in wind_chain.block.get_all_blocks():
        if constant_power in runtime_block.init_eqs:
            constant_power_initial = runtime_block.init_eqs[constant_power]
        else:
            pass
    assert isinstance(constant_power_initial, Const)
    assert isclose(float(constant_power_initial.value), 0.625, abs_tol=1.0e-12)


def test_wind_type1b_composes_induction_machine_shaft_torque_once() -> None:
    """Couple the Type 1b drivetrain to its sourced induction generator model.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    asynchronous_machine: CgmesAsynchronousMachine = CgmesAsynchronousMachine(
        rdfid='_wind_type1b_equipment'
    )
    asynchronous_machine.ratedS = 100.0
    asynchronous_machine.ratedPowerFactor = 0.8
    machine_dynamics: AsynchronousMachineTimeConstantReactance = AsynchronousMachineTimeConstantReactance(
        rdfid='_wind_type1b_machine_dynamics'
    )
    machine_dynamics.AsynchronousMachine = asynchronous_machine
    machine_dynamics.xs = 3.0
    machine_dynamics.xp = 0.3
    machine_dynamics.xpp = 0.2
    machine_dynamics.tpo = 0.6
    machine_dynamics.tppo = 0.05
    machine_dynamics.inertia = 1.2
    machine_dynamics.damping = 0.0
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.statorLeakageReactance = 0.1
    turbine: WindGenTurbineType1bIEC = WindGenTurbineType1bIEC(rdfid='_wind_type1b_turbine')
    turbine.AsynchronousMachineDynamics = machine_dynamics
    turbine.AsynchronousMachineDynamics.WindTurbineType1or2Dynamics = turbine
    mechanical: WindMechIEC = WindMechIEC(rdfid='_wind_type1b_mechanical')
    mechanical.cdrt = 0.02
    mechanical.hgen = 1.2
    mechanical.hwtr = 3.0
    mechanical.kdrt = 2.0
    mechanical.WindTurbineType1or2IEC = turbine
    turbine.WindMechIEC = mechanical
    pitch: WindPitchContPowerIEC = WindPitchContPowerIEC(rdfid='_wind_type1b_pitch')
    pitch.dpmax = 0.1
    pitch.dpmin = -0.1
    pitch.pmin = 0.0
    pitch.pset = 0.8
    pitch.t1 = 0.5
    pitch.tr = 0.1
    pitch.uuvrt = 0.8
    turbine.WindPitchContPowerIEC = pitch
    pitch.WindGenTurbineType1bIEC = turbine
    first_delay: WindDynamicsLookupTable = WindDynamicsLookupTable(rdfid='_wind_type1b_delay_1')
    first_delay.input = 0.0
    first_delay.output = 0.1
    first_delay.sequence = 1
    first_delay.lookupTableFunctionType = WindLookupTableFunctionKind.tduwt
    first_delay.WindPitchContPowerIEC = pitch
    second_delay: WindDynamicsLookupTable = WindDynamicsLookupTable(rdfid='_wind_type1b_delay_2')
    second_delay.input = 1.0
    second_delay.output = 0.2
    second_delay.sequence = 2
    second_delay.lookupTableFunctionType = WindLookupTableFunctionKind.tduwt
    second_delay.WindPitchContPowerIEC = pitch
    pitch.WindDynamicsLookupTable.extend((first_delay, second_delay))
    generator: Generator = Generator(
        idtag=asynchronous_machine.uuid,
        name='wind_type1b_generator',
        P=50.0,
        Snom=100.0,
    )
    bus: Bus = Bus(name='wind_type1b_bus')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['AsynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['WindGenTurbineType1bIEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindMechIEC'].append(mechanical)
    cgmes_model.dynamics_assets.lists['WindPitchContPowerIEC'].append(pitch)
    cgmes_model.dynamics_assets.lists['WindDynamicsLookupTable'].extend((first_delay, second_delay))

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    machine_template_name: str = f'AsynchronousMachineTimeConstantReactance_{machine_dynamics.uuid}'
    mechanical_template_name: str = f'WindMechIEC_{mechanical.uuid}'
    machine_speed: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'OmegaPu_{machine_template_name}',
    )
    machine_torque_input: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'TmPu_{machine_template_name}',
    )
    machine_air_gap_torque: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'TeGeneratorPu_{machine_template_name}',
    )
    turbine_air_gap_power: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'PagPu_{mechanical_template_name}',
    )
    shaft_torque: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'TshaftPu_{mechanical_template_name}',
    )
    assert machine_speed is not None
    assert machine_torque_input is not None
    assert machine_air_gap_torque is not None
    assert turbine_air_gap_power is not None
    assert shaft_torque is not None
    assert sum(
        int(machine_speed in runtime_block.state_vars)
        for runtime_block in composite_template.block.get_all_blocks()
    ) == 1
    assert find_block_variable_by_name(
        composite_template.block,
        f'OmegaGenPu_{mechanical_template_name}',
    ) is None
    machine_torque_equation: Expr | None = None
    turbine_power_equation: Expr | None = None
    for runtime_block in composite_template.block.get_all_blocks():
        if machine_torque_input in runtime_block.algebraic_vars:
            machine_torque_equation = runtime_block.algebraic_eqs[
                runtime_block.algebraic_vars.index(machine_torque_input)
            ]
        else:
            pass
        if turbine_air_gap_power in runtime_block.algebraic_vars:
            turbine_power_equation = runtime_block.algebraic_eqs[
                runtime_block.algebraic_vars.index(turbine_air_gap_power)
            ]
        else:
            pass
    assert machine_torque_equation is not None
    assert turbine_power_equation is not None
    machine_torque_dependencies: set[str] = set(
        variable.name for variable in machine_torque_equation.get_vars()
    )
    turbine_power_dependencies: set[str] = set(
        variable.name for variable in turbine_power_equation.get_vars()
    )
    assert machine_torque_input.name in machine_torque_dependencies
    assert shaft_torque.name in machine_torque_dependencies
    assert turbine_air_gap_power.name in turbine_power_dependencies
    assert machine_speed.name in turbine_power_dependencies
    assert machine_air_gap_torque.name in turbine_power_dependencies


def test_type_fj_exciter_is_retained_without_invented_field_current_port() -> None:
    """Keep an associated AC1A standalone when Type F/J has no Ifd output.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_type_fj_exciter_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_type_fj_exciter_machine_dynamics'
    )
    machine_dynamics.rotorType = RotorKind.roundRotor
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientTypeF
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    excitation: ExcIEEEAC1A = ExcIEEEAC1A(rdfid='_type_fj_ac1a')
    excitation.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = excitation
    generator: Generator = Generator(idtag=machine.uuid, name='type_fj_exciter_machine')
    veragrid_model.add_bus(Bus(name='type_fj_exciter_bus'))
    veragrid_model.add_generator(bus=veragrid_model.buses[0], api_obj=generator)
    cgmes_model.dynamics_assets.lists['ExcIEEEAC1A'].append(excitation)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    assert generator.rms_template is not None
    assert generator.rms_template.name.startswith('SynchronousMachineTimeConstantReactance_')
    assert find_block_variable_by_name(generator.rms_template.block, 'IfdPu') is None
    assert any(
        runtime_model.device is generator and runtime_model.name.startswith('ExcIEEEAC1A_')
        for runtime_model in veragrid_model.rms_models
    )
    assert any(
        entry.msg.startswith('CGMES machine selector does not provide the complete ExcIEEEAC1A')
        for entry in logger.entries
    )


def test_synchronous_machine_dynamics_schema_preserves_inherited_rdf_fields() -> None:
    """Register exact inherited and local machine RDF descriptors.

    :return: None.
    """
    machine: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_schema_machine'
    )
    assert 'SynchronousMachine' in machine.get_declared_property_names()
    assert 'damping' in machine.get_declared_property_names()
    assert 'inertia' in machine.get_declared_property_names()
    assert 'saturationFactorQAxis' in machine.get_declared_property_names()
    assert 'efdBaseRatio' in machine.get_declared_property_names()
    assert 'ifdBaseType' in machine.get_declared_property_names()
    assert 'ifdBaseValue' in machine.get_declared_property_names()
    assert 'rotorType' in machine.get_declared_property_names()
    assert 'modelType' in machine.get_declared_property_names()
    assert 'tppqo' in machine.get_declared_property_names()


def test_cgmes_salient_simplified_direct_axis_initial_point_balances() -> None:
    """Check the EA axis equations at a nonzero active/reactive operating point.

    :return: None.
    """
    parameters: tuple[tuple[str, float], ...] = (
        ('nominalFrequency', 50.0), ('inertia', 4.0), ('damping', 0.0),
        ('xDirectSync', 1.8), ('xDirectTrans', 0.3), ('xDirectSubtrans', 0.2),
        ('xQuadSync', 1.7), ('xQuadTrans', 0.55), ('xQuadSubtrans', 0.2),
        ('tpdo', 5.0), ('tppdo', 0.05), ('tppqo', 0.05),
        ('statorLeakageReactance', 0.15), ('statorResistance', 0.01),
        ('ratedS', 100.0),
        ('systemBaseMVA', 100.0),
    )
    template: RmsModelTemplate = build_synchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name='direct_axis_residual',
        rotor_type=RotorKind.salientPole,
        model_type=SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        parameters=parameters,
    )
    runtime_block: Block = template.block.children[1]

    # At Vm=1, Va=0, compute the power-flow current and the EA machine equilibrium.
    active_power: float = 0.5
    reactive_power: float = 0.2
    x_direct: float = 1.8
    x_direct_transient: float = 0.3
    x_quad: float = 1.7
    x_quad_subtransient: float = 0.2
    current_real: float = active_power
    current_imaginary: float = -reactive_power
    delta_sine_coefficient: float = 1.0 - x_quad * current_imaginary
    delta_cosine_coefficient: float = -x_quad * current_real
    delta: float = atan2(-delta_cosine_coefficient, delta_sine_coefficient)
    current_d: float = current_real * sin(delta) - current_imaginary * cos(delta)
    current_q: float = current_real * cos(delta) + current_imaginary * sin(delta)
    voltage_d: float = sin(delta)
    voltage_q: float = cos(delta)
    ed_subtransient: float = (x_quad - x_quad_subtransient) * current_q
    eq_prime: float = voltage_q + x_direct_transient * current_d
    ed: float = ed_subtransient + x_quad_subtransient * current_q
    eq: float = eq_prime - x_direct_transient * current_d
    electrical_power: float = ed * current_d + eq * current_q
    field_voltage: float = voltage_q + x_direct * current_d

    assert isclose(voltage_d, x_quad * current_q, abs_tol=1.0e-12)
    assert isclose(ed, voltage_d, abs_tol=1.0e-12)
    assert isclose(eq, voltage_q, abs_tol=1.0e-12)
    assert isclose(ed_subtransient, (x_quad - x_quad_subtransient) * current_q, abs_tol=1.0e-12)
    assert isclose(eq_prime, field_voltage - (x_direct - x_direct_transient) * current_d, abs_tol=1.0e-12)
    assert isclose(electrical_power, active_power, abs_tol=1.0e-12)
    assert isclose(voltage_q * current_d - voltage_d * current_q, reactive_power, abs_tol=1.0e-12)
    assert len(runtime_block.state_vars) == 4
    assert len(runtime_block.init_eqs) >= len(runtime_block.state_vars)
    assert_zero_initial_residuals(
        template=template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: active_power,
            VarPowerFlowReferenceType.Q: reactive_power,
        },
    )


@pytest.mark.parametrize(
    'model_type',
    (SynchronousMachineModelKind.subtransientTypeF, SynchronousMachineModelKind.subtransientTypeJ),
)
@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
def test_cgmes_type_fj_machine_initial_point_balances(
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> None:
    """Check Type F/J saturation and rotor-specific equilibrium at nonzero P/Q.

    :param rotor_type: Round-rotor or salient-pole selector.
    :param model_type: Canonical Type F or Type J selector.
    :return: None.
    """
    parameters: tuple[tuple[str, float], ...] = (
        ('nominalFrequency', 50.0), ('inertia', 4.0), ('damping', 0.0),
        ('xDirectSync', 1.8), ('xDirectTrans', 0.3), ('xDirectSubtrans', 0.2),
        ('xQuadSync', 1.7), ('xQuadTrans', 0.55), ('xQuadSubtrans', 0.2),
        ('tpdo', 5.0), ('tppdo', 0.04), ('tpqo', 0.7), ('tppqo', 0.05),
        ('statorLeakageReactance', 0.12), ('statorResistance', 0.003),
        ('saturationFactor', 0.1), ('saturationFactor120', 0.2),
        ('ks', 0.05 if model_type == SynchronousMachineModelKind.subtransientTypeJ else 0.0),
        ('ratedS', 100.0), ('systemBaseMVA', 100.0),
    )
    template: RmsModelTemplate = build_synchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name=f'{model_type.name}_residual',
        rotor_type=rotor_type,
        model_type=model_type,
        parameters=parameters,
    )
    runtime_block: Block = template.block.children[1]
    expected_state_count: int = 6 if rotor_type == RotorKind.roundRotor else 5
    assert len(runtime_block.state_vars) == expected_state_count
    assert_zero_initial_residuals(
        template=template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.2,
        },
    )


@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
def test_cgmes_full_subtransient_machine_initial_point_balances(
        rotor_type: RotorKind,
) -> None:
    """Check both EA848/EA850 zero-Canay machine equations at nonzero P/Q.

    :param rotor_type: Round-rotor or salient-pole selector.
    :return: None.
    """
    parameters: tuple[tuple[str, float], ...] = (
        ('nominalFrequency', 50.0), ('inertia', 4.0), ('damping', 0.0),
        ('xDirectSync', 1.8), ('xDirectTrans', 0.3), ('xDirectSubtrans', 0.2),
        ('xQuadSync', 1.7), ('xQuadTrans', 0.55), ('xQuadSubtrans', 0.2),
        ('tpdo', 5.0), ('tppdo', 0.04), ('tpqo', 0.7), ('tppqo', 0.05),
        ('statorLeakageReactance', 0.12), ('statorResistance', 0.003),
        ('saturationFactor', 0.1), ('saturationFactor120', 0.2),
        ('saturationFactorQAxis', 0.15), ('saturationFactor120QAxis', 0.25),
        ('ratedS', 100.0), ('systemBaseMVA', 100.0), ('tc', 0.0),
    )
    template: RmsModelTemplate = build_synchronous_machine_time_constant_reactance_template(
        vfactory=VarFactory(),
        name=f'{rotor_type.name}_subtransient_residual',
        rotor_type=rotor_type,
        model_type=SynchronousMachineModelKind.subtransient,
        parameters=parameters,
    )
    runtime_block: Block = template.block.children[1]
    expected_state_count: int = 6 if rotor_type is RotorKind.roundRotor else 5
    assert len(runtime_block.state_vars) == expected_state_count
    assert any(variable.name == 'IfdPu' for variable in runtime_block.out_vars)
    power_flow_values: dict[VarPowerFlowReferenceType, float] = {
        VarPowerFlowReferenceType.Vm: 1.0,
        VarPowerFlowReferenceType.Va: 0.0,
        VarPowerFlowReferenceType.P: 0.5,
        VarPowerFlowReferenceType.Q: 0.2,
    }
    seeded_template: RmsModelTemplate = deepcopy(template)
    for block in seeded_template.block.get_all_blocks():
        block.external_mapping.pop(VarPowerFlowReferenceType.P, None)
        block.external_mapping.pop(VarPowerFlowReferenceType.Q, None)
        for reference, power_value in (
                (VarPowerFlowReferenceType.P, 0.5),
                (VarPowerFlowReferenceType.Q, 0.2),
        ):
            seeded_variable: Var | None = None
            for variable in block.algebraic_vars:
                if variable.ref is reference:
                    seeded_variable = variable
                else:
                    pass
            if seeded_variable is not None:
                block.init_eqs[seeded_variable] = Const(power_value)
            else:
                pass
    assert_zero_initial_residuals(
        template=seeded_template,
        power_flow_values=power_flow_values,
    )


@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
@pytest.mark.parametrize(
    'model_type',
    (
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        SynchronousMachineModelKind.subtransientSimplified,
        SynchronousMachineModelKind.subtransientTypeF,
        SynchronousMachineModelKind.subtransientTypeJ,
    ),
)
def test_cgmes_time_constant_reactance_composes_governor_on_rated_s_base(
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> None:
    """Balance GovSteam0 shaft power against each supported machine variant.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_direct_axis_governed_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_direct_axis_governed_machine_dynamics'
    )
    machine_dynamics.rotorType = rotor_type
    machine_dynamics.modelType = model_type
    machine_dynamics.inertia = 4.0
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.ks = 0.05 if model_type == SynchronousMachineModelKind.subtransientTypeJ else 0.0
    machine_dynamics.SynchronousMachine = machine
    governor: GovSteam0 = GovSteam0(rdfid='_direct_axis_governor')
    governor.mwbase = 100.0
    governor.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='direct_axis_governed_generator',
        P=50.0,
        Q=20.0,
    )
    bus: Bus = Bus(name='direct_axis_governed_bus')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['GovSteam0'].append(governor)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert 'GovSteam0' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'Tm') is None
    governor_power_outputs: list[Var] = list()
    for runtime_block in composite_template.block.get_all_blocks():
        for output_variable in runtime_block.out_vars:
            if output_variable.name.startswith('PmPu_'):
                governor_power_outputs.append(output_variable)
            else:
                pass
    assert len(governor_power_outputs) == 1
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.2,
        },
    )


@pytest.mark.parametrize('rotor_type', (RotorKind.salientPole, RotorKind.roundRotor))
@pytest.mark.parametrize(
    'model_type',
    (
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
        SynchronousMachineModelKind.subtransientSimplified,
    ),
)
def test_cgmes_direct_axis_machine_scales_mechanical_load_base(
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> None:
    """Scale MechLoad1 system-base power onto a different machine ratedS base.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_direct_axis_load_machine')
    machine.ratedS = 200.0
    machine.ratedPowerFactor = 1.0
    machine.operatingMode = SynchronousMachineOperatingMode.motor
    machine_dynamics: SynchronousMachineTimeConstantReactance = SynchronousMachineTimeConstantReactance(
        rdfid='_direct_axis_load_machine_dynamics'
    )
    machine_dynamics.rotorType = rotor_type
    machine_dynamics.modelType = model_type
    machine_dynamics.inertia = 4.0
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine_dynamics.SynchronousMachine = machine
    mechanical_load: MechLoad1 = MechLoad1(rdfid='_direct_axis_mechanical_load')
    mechanical_load.a = 0.2
    mechanical_load.b = 0.3
    mechanical_load.d = 0.0
    mechanical_load.e = 2.0
    mechanical_load.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.MechanicalLoadDynamics = mechanical_load
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='direct_axis_load_generator',
        P=-50.0,
        Q=-20.0,
    )
    bus: Bus = Bus(name='direct_axis_load_bus')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists['MechLoad1'].append(mechanical_load)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, [entry.msg for entry in logger.entries]
    load_bridge_output: Var | None = find_block_variable_by_name(
        composite_template.block,
        f'MechLoadMachinePu_{composite_template.name}',
    )
    assert load_bridge_output is not None
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: -0.5,
            VarPowerFlowReferenceType.Q: -0.2,
        },
    )


def test_load_motor_component_association_resolves_physical_load() -> None:
    """Import a non-function-block load model through its aggregate owner.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    energy_consumer: EnergyConsumer = EnergyConsumer(rdfid="_load")
    aggregate: LoadAggregate = LoadAggregate(rdfid="_aggregate")
    motor: LoadMotor = LoadMotor(rdfid="_motor")
    load: Load = Load(idtag=energy_consumer.uuid, name="load")
    aggregate.EnergyConsumer.append(energy_consumer)
    aggregate.LoadMotor = motor
    motor.LoadAggregate = aggregate
    cgmes_model.dynamics_assets.lists["LoadMotor"].append(motor)
    veragrid_model.add_load(api_obj=load)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    assert find_veragrid_devices(motor, {energy_consumer.uuid: load}) == [load]
    assert len(veragrid_model.rms_models) == 0
    assert any('requires finite numeric ls, lp, and lpp' in entry.msg for entry in logger.entries)


def test_mech_load1_equations_and_machine_operating_point_seed() -> None:
    """Build the MechLoad1 torque curve and seed it from its associated machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    mechanical_load: MechLoad1 = MechLoad1(rdfid="_mechanical_load")
    mechanical_load.a = 0.2
    mechanical_load.b = 0.3
    mechanical_load.d = 0.1
    mechanical_load.e = 2.0
    machine_dynamics: SynchronousMachineDynamics = SynchronousMachineDynamics(
        rdfid="_machine_dynamics_mechanical_load"
    )
    machine: SynchronousMachine = SynchronousMachine(rdfid="_machine_mechanical_load")
    generator: Generator = Generator(
        idtag=machine.uuid,
        name="mechanical_load_machine",
        P=80.0,
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.MechanicalLoadDynamics = mechanical_load
    mechanical_load.SynchronousMachineDynamics = machine_dynamics
    cgmes_model.dynamics_assets.lists["MechLoad1"].append(mechanical_load)
    veragrid_model.add_generator(bus=Bus(name="mechanical_load_bus"), api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    imported_template: RmsModelTemplate = veragrid_model.rms_models[0]
    imported_template.block.unify_blocks()
    event_values: dict[str, object] = dict(
        (variable.name, value)
        for variable, value in imported_template.block.event_dict.items()
    )
    equation_variables: set[str] = set(
        variable.name
        for equation in imported_template.block.algebraic_eqs
        for variable in equation.get_vars()
    )

    assert imported_template.device is generator
    assert event_values[f"MechLoad1.a_{imported_template.name}"].value == 0.2
    assert event_values[f"MechLoad1.e_{imported_template.name}"].value == 2.0
    assert imported_template.block.init_eqs[imported_template.block.algebraic_vars[0]].value == 0.8
    assert "OmegaPu" in equation_variables
    assert len(imported_template.block.algebraic_eqs) == 1
    assert imported_template.block.algebraic_vars[0].name == "PmechPu"


def test_simplified_machine_composes_mechanical_load_and_attaches_runtime() -> None:
    """Connect MechLoad1 speed and torque to its simplified machine host.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid="_composed_machine")
    machine.operatingMode = SynchronousMachineOperatingMode.motor
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_composed_machine_dynamics"
    )
    mechanical_load: MechLoad1 = MechLoad1(rdfid="_composed_mechanical_load")
    mechanical_load.a = 0.2
    mechanical_load.b = 0.3
    mechanical_load.d = 0.1
    mechanical_load.e = 2.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.MechanicalLoadDynamics = mechanical_load
    mechanical_load.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(idtag=machine.uuid, name="composed_generator", P=-80.0)
    veragrid_model.add_generator(bus=Bus(name="composed_generator_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["MechLoad1"].append(mechanical_load)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.device is generator
    assert composite_template in veragrid_model.rms_models
    assert generator.rms_model.get_all_blocks()
    state_equations: list[Expr] = list()
    algebraic_equations: list[Expr] = list()
    for block in composite_template.block.get_all_blocks():
        state_equations.extend(block.state_eqs)
        algebraic_equations.extend(block.algebraic_eqs)
    state_variable_names: set[str] = set()
    for equation in state_equations:
        state_variable_names.update(variable.name for variable in equation.get_vars())
    mechanical_variable_names: set[str] = set()
    for equation in algebraic_equations:
        mechanical_variable_names.update(variable.name for variable in equation.get_vars())

    assert "PmechPu" not in state_variable_names
    assert "Tm" not in state_variable_names
    assert "PmechPu" in mechanical_variable_names
    assert "omega" in mechanical_variable_names
    assert "OmegaPu" not in mechanical_variable_names

    runtime_state_variable_names: set[str] = set()
    runtime_mechanical_variable_names: set[str] = set()
    for block in generator.rms_model.get_all_blocks():
        for equation in block.state_eqs:
            runtime_state_variable_names.update(
                variable.name for variable in equation.get_vars()
            )
        for equation in block.algebraic_eqs:
            runtime_mechanical_variable_names.update(
                variable.name for variable in equation.get_vars()
            )
    assert "PmechPu" not in runtime_state_variable_names
    assert "PmechPu" in runtime_mechanical_variable_names
    assert "omega" in runtime_mechanical_variable_names

    load_block: Block | None = None
    for block in composite_template.block.get_all_blocks():
        for output_variable in block.out_vars:
            if output_variable.name == "PmechPu":
                load_block = block
            else:
                pass
    assert load_block is not None
    load_power: Var = load_block.out_vars[0]
    assert load_block.init_eqs[load_power].value == 0.8

    # Evaluate the imported initialization graph from the solved bus power-flow
    # values and require every machine/load DAE residual to vanish at t=0.
    initialization_values: dict[int, float | complex] = dict()
    reference_values: dict[VarPowerFlowReferenceType, float] = {
        VarPowerFlowReferenceType.Vm: 1.0,
        VarPowerFlowReferenceType.Va: 0.0,
        VarPowerFlowReferenceType.P: -0.8,
        VarPowerFlowReferenceType.Q: 0.0,
    }
    initialization_equations: list[tuple[Var, Expr]] = list()
    for block in composite_template.block.get_all_blocks():
        for parameter_variable, parameter_value in block.event_dict.items():
            if isinstance(parameter_value, Const) and isinstance(
                    parameter_value.value,
                    (int, float, complex),
            ):
                initialization_values[parameter_variable.uid] = parameter_value.value
            elif isinstance(parameter_value, Expr) and not isinstance(parameter_value, Const):
                initialization_equations.append((parameter_variable, parameter_value))
            else:
                pass
        for parameter_variable, parameter_value in block.parameters.items():
            if isinstance(parameter_value, Const) and isinstance(
                    parameter_value.value,
                    (int, float, complex),
            ):
                initialization_values[parameter_variable.uid] = parameter_value.value
            else:
                pass
        for reference, mapped_variable in block.external_mapping.items():
            reference_value: float | None = reference_values.get(reference, None)
            if reference_value is None:
                pass
            else:
                initialization_values[mapped_variable.uid] = reference_value
        initialization_equations.extend(block.init_eqs.items())
        initialization_equations.extend(block.diff_init_eqs.items())

    for initialized_variable, initialization_expression in initialization_equations:
        initialization_values.pop(initialized_variable.uid, None)

    pending_initializations: list[tuple[Var, Expr]] = initialization_equations
    initialized_variable_uids: set[int] = set()
    while len(pending_initializations) > 0:
        unresolved_initializations: list[tuple[Var, Expr]] = list()
        values_added: bool = False
        for initialized_variable, initialization_expression in pending_initializations:
            dependencies: list[Var] = initialization_expression.get_vars()
            if all(dependency.uid in initialization_values for dependency in dependencies):
                initialized_value: float | complex = eval_uid(
                    initialization_expression,
                    initialization_values,
                )
                if initialized_variable.uid in initialized_variable_uids:
                    previous_value: float | complex = initialization_values[initialized_variable.uid]
                    assert isclose(abs(initialized_value - previous_value), 0.0, abs_tol=1e-8), (
                        initialized_variable.name,
                        initialized_value,
                        previous_value,
                    )
                else:
                    initialization_values[initialized_variable.uid] = initialized_value
                    initialized_variable_uids.add(initialized_variable.uid)
                    values_added = True
            else:
                unresolved_initializations.append((initialized_variable, initialization_expression))
        pending_initializations = unresolved_initializations
        if values_added:
            pass
        else:
            break

    assert not pending_initializations
    for block in composite_template.block.get_all_blocks():
        for equation in block.state_eqs:
            assert isclose(abs(eval_uid(equation, initialization_values)), 0.0, abs_tol=1e-8)
        for equation in block.algebraic_eqs:
            assert isclose(abs(eval_uid(equation, initialization_values)), 0.0, abs_tol=1e-8)


def test_asynchronous_motor_composes_mech_load1_at_solved_operating_point() -> None:
    """Balance the canonical asynchronous motor, shaft-load curve, and equipment link.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    machine: CgmesAsynchronousMachine = CgmesAsynchronousMachine(
        rdfid='_mechload_async_motor',
    )
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: AsynchronousMachineTimeConstantReactance = (
        AsynchronousMachineTimeConstantReactance(rdfid='_mechload_async_motor_dynamics')
    )
    machine_dynamics.AsynchronousMachine = machine
    machine_dynamics.xs = 3.0
    machine_dynamics.xp = 0.3
    machine_dynamics.xpp = 0.2
    machine_dynamics.tpo = 0.6
    machine_dynamics.tppo = 0.05
    machine_dynamics.inertia = 1.2
    machine_dynamics.damping = 0.0
    machine_dynamics.statorResistance = 0.01
    machine_dynamics.statorLeakageReactance = 0.1
    mechanical_load: MechLoad1 = MechLoad1(rdfid='_mechload_async_curve')
    mechanical_load.a = 0.2
    mechanical_load.b = 0.3
    mechanical_load.d = 0.1
    mechanical_load.e = 2.0
    machine_dynamics.MechanicalLoadDynamics = mechanical_load
    mechanical_load.AsynchronousMachineDynamics = machine_dynamics

    generator: Generator = Generator(
        idtag=machine.uuid,
        name='mechload_async_motor',
        P=-50.0,
        Q=-36.02683024772576,
    )
    generator.Snom = 100.0
    bus: Bus = Bus(name='mechload_async_motor_bus')
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['AsynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['MechLoad1'].append(mechanical_load)

    conversion_logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=conversion_logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.device is generator
    assert 'MechLoad1' in composite_template.name, [
        entry.msg for entry in conversion_logger.entries
    ]
    assert composite_template in veragrid_model.rms_models
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: -0.5,
            VarPowerFlowReferenceType.Q: -0.3602683024772576,
        },
    )


def test_simplified_machine_keeps_mechanical_load_and_governor_separate() -> None:
    """Retain unsupported simultaneous shaft-load and turbine-governor models.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid="_combined_load_governor_machine"
    )
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine.operatingMode = SynchronousMachineOperatingMode.motor
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_combined_load_governor_machine_dynamics"
    )
    mechanical_load: MechLoad1 = MechLoad1(rdfid="_combined_mechanical_load")
    mechanical_load.a = 0.2
    mechanical_load.b = 0.3
    mechanical_load.d = 0.1
    mechanical_load.e = 2.0
    governor: GovSteam0 = GovSteam0(rdfid="_combined_steam0_governor")
    governor.mwbase = 100.0
    governor.r = 0.05
    governor.t1 = 0.2
    governor.vmax = 2.0
    governor.vmin = 0.0
    governor.t2 = 0.0
    governor.t3 = 0.5
    governor.dt = 0.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.MechanicalLoadDynamics = mechanical_load
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    mechanical_load.SynchronousMachineDynamics = machine_dynamics
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(
        idtag=machine.uuid,
        name="combined_load_governor_generator",
        P=80.0,
    )
    veragrid_model.add_generator(bus=Bus(name="combined_load_governor_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["MechLoad1"].append(mechanical_load)
    cgmes_model.dynamics_assets.lists["GovSteam0"].append(governor)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None, logger.get_message() + " " + repr(logger.entries)
    assert composite.device is generator
    assert composite in veragrid_model.rms_models
    assert "MechLoad1" not in composite.name
    assert "GovSteam0" not in composite.name
    assert find_block_variable_by_name(composite.block, "Tm") is not None
    assert any(
        "MechLoad1 is defined for a synchronous motor" in entry.msg
        for entry in logger.entries
    )
    assert any(
        "MechLoad1" in template.name
        for template in veragrid_model.rms_models
    )
    assert any(
        "GovSteam0" in template.name
        for template in veragrid_model.rms_models
    )


@pytest.mark.parametrize(
    ("governor_kind", "explicit_mwbase"),
    (
        ("gast", True), ("gast", False), ("steam0", True), ("steam0", False),
        ("sgo", True), ("sgo", False),
        ("steam1", True), ("steam1", False),
        ("ieee1", True), ("ieee1", False),
    ),
)
def test_simplified_machine_composes_supported_governor_with_mwbase_conversion(
        governor_kind: str,
        explicit_mwbase: bool,
) -> None:
    """Connect supported governor speed and MWBASE-scaled power to the machine.

    :param governor_kind: Equation-backed governor selected for this composition.
    :param explicit_mwbase: Whether the governor has a positive explicit MWBASE.
    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid="_gast_composed_machine"
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_gast_composed_machine_dynamics"
    )
    if governor_kind == "gast":
        governor: TurbineGovernorDynamics = GovGAST(rdfid="_gast_composed_governor")
        governor.mwbase = 100.0 if explicit_mwbase else 0.0
        governor.r = 0.04
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.0
        governor.at = 1.0
        governor.kt = 2.5
        governor.vmax = 1.1
        governor.vmin = 0.1
        governor.dturb = 0.08
    elif governor_kind == "steam0":
        governor = GovSteam0(rdfid="_steam0_composed_governor")
        governor.mwbase = 100.0 if explicit_mwbase else 0.0
        governor.r = 0.04
        governor.t1 = 0.0
        governor.vmax = 1.1
        governor.vmin = 0.1
        governor.t2 = 0.0
        governor.t3 = 0.0
        governor.dt = 0.08
    elif governor_kind == "sgo":
        governor = GovSteamSGO(rdfid="_steam_sgo_composed_governor")
        governor.mwbase = 100.0 if explicit_mwbase else 0.0
        governor.t1 = 0.2
        governor.t2 = 0.05
        governor.t3 = 0.3
        governor.t4 = 0.4
        governor.t5 = 1.0
        governor.t6 = 0.2
        governor.k1 = 0.05
        governor.k2 = 0.3
        governor.k3 = 0.3
        governor.pmax = 1.0
        governor.pmin = 0.0
    elif governor_kind == "steam1":
        governor = GovSteam1(rdfid="_steam1_composed_governor")
        governor.mwbase = 100.0 if explicit_mwbase else 0.0
        governor.k = 25.0
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.1
        governor.t4 = 0.3
        governor.t5 = 5.0
        governor.t6 = 0.5
        governor.t7 = 0.0
        governor.pmax = 1.0
        governor.pmin = 0.0
        governor.valve = True
        governor.gv1 = 0.0
        governor.pgv1 = 0.0
        governor.gv2 = 0.2
        governor.pgv2 = 0.2
        governor.gv3 = 0.4
        governor.pgv3 = 0.4
        governor.gv4 = 0.6
        governor.pgv4 = 0.6
        governor.gv5 = 0.8
        governor.pgv5 = 0.8
        governor.gv6 = 1.0
        governor.pgv6 = 1.0
    else:
        governor = GovSteamIEEE1(rdfid="_steam_ieee1_composed_governor")
        governor.mwbase = 100.0 if explicit_mwbase else 0.0
        governor.k = 31.0
        governor.t1 = 0.0
        governor.t2 = 0.0
        governor.t3 = 0.25
        governor.uo = 0.12
        governor.uc = -0.14
        governor.pmax = 1.1
        governor.pmin = 0.1
        governor.t4 = 0.2
        governor.k1 = 0.3
        governor.k2 = 0.0
        governor.k3 = 0.3
        governor.k4 = 0.0
        governor.k5 = 0.2
        governor.k6 = 0.0
        governor.k7 = 0.2
        governor.k8 = 0.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(
        idtag=machine.uuid,
        name="gast_composed_generator",
        P=80.0,
    )
    veragrid_model.add_generator(bus=Bus(name="gast_composed_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists[governor.__class__.__name__].append(governor)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.device is generator
    assert composite_template in veragrid_model.rms_models
    machine_speed_output: Var | None = None
    governor_speed_input: Var | None = None
    machine_torque_input: Var | None = None
    bridge_torque_output: Var | None = None
    for block in composite_template.block.get_all_blocks():
        for variable in block.in_vars:
            if variable.name.startswith("MachineTorquePu_"):
                machine_torque_input = variable
            elif variable.name == "omega":
                governor_speed_input = variable
            else:
                pass
        for variable in block.out_vars:
            if variable.name == "omega":
                machine_speed_output = variable
            elif variable.name.startswith("MachineTorquePu_"):
                bridge_torque_output = variable
            else:
                pass
    assert machine_speed_output is not None
    assert governor_speed_input is not None
    assert machine_torque_input is not None
    assert bridge_torque_output is not None
    assert machine_speed_output.uid == governor_speed_input.uid
    assert machine_torque_input.uid == bridge_torque_output.uid
    assert_zero_initial_residuals(
        template=composite_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.4,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_negative_governor_mwbase_does_not_use_nameplate_fallback() -> None:
    """Keep an invalid negative MWBASE distinct from the zero-value fallback.

    :return: None.
    """
    governor: GovGAST = GovGAST(rdfid="_negative_gast_mwbase")
    governor.mwbase = -1.0

    assert get_turbine_governor_power_base(governor) is None


def test_mech_load1_initial_power_curve_is_normalized_at_nominal_speed() -> None:
    """Keep the polynomial torque curve at unit gain when speed is nominal.

    :return: None.
    """
    template: RmsModelTemplate = build_mech_load1_template(
        vfactory=VarFactory(),
        name="MechLoad1_nominal_check",
        initial_power=0.8,
    )
    template.block.unify_blocks()

    assert template.block.init_eqs[template.block.algebraic_vars[0]].value == 0.8
    assert template.block.init_eqs[template.block.in_vars[0]].value == 1.0


def test_load_static_model_kind_and_device_are_imported() -> None:
    """Dispatch the RDF load variant and retain its association to the real load.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    energy_consumer: EnergyConsumer = EnergyConsumer(rdfid="_static_load")
    aggregate: LoadAggregate = LoadAggregate(rdfid="_static_aggregate")
    static_model: LoadStatic = LoadStatic(rdfid="_static_model")
    static_model.staticLoadModelType = StaticLoadModelKind.zIP2
    static_model.kp1 = 0.2
    static_model.kp2 = 0.3
    static_model.kp3 = 0.4
    static_model.kp4 = 0.1
    static_model.kpf = 0.05
    static_model.kq1 = 0.2
    static_model.kq2 = 0.3
    static_model.kq3 = 0.4
    static_model.kq4 = 0.1
    static_model.kqf = 0.02
    static_model.LoadAggregate = aggregate
    aggregate.LoadStatic = static_model
    aggregate.EnergyConsumer.append(energy_consumer)
    load: Load = Load(idtag=energy_consumer.uuid, name="static_load")
    cgmes_model.dynamics_assets.lists["LoadStatic"].append(static_model)
    veragrid_model.add_load(api_obj=load)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    imported_template: RmsModelTemplate = veragrid_model.rms_models[0]
    imported_block: Block = imported_template.block
    imported_block.unify_blocks()
    runtime_event_values: dict[str, object] = dict(
        (variable.name, value)
        for variable, value in imported_block.event_dict.items()
    )
    equation_variables: set[str] = set(
        variable.name
        for equation in imported_block.algebraic_eqs
        for variable in equation.get_vars()
    )

    assert len(veragrid_model.rms_models) == 1
    assert imported_template.device is load
    assert imported_template.comment.endswith("zIP2 equations.")
    assert len(imported_block.algebraic_eqs) == 2
    assert "LoadStatic.kp4_" + imported_template.name in runtime_event_values
    assert runtime_event_values[
        "LoadStatic.kp4_" + imported_template.name
    ].value == 0.1
    assert "LoadStatic.kq4_" + imported_template.name in equation_variables


@pytest.mark.parametrize(
    'model_kind', (
        GenericNonLinearLoadModelKind.exponentialRecovery,
        GenericNonLinearLoadModelKind.loadAdaptive,
    ),
)
def test_generic_nonlinear_recovery_model_maps_to_physical_load(
        model_kind: GenericNonLinearLoadModelKind,
) -> None:
    """Import each nonlinear recovery kind and balance it at a solved load point.

    :param model_kind: Canonical CGMES generic nonlinear load kind.
    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    energy_consumer: EnergyConsumer = EnergyConsumer(rdfid="_gnld_load")
    nonlinear_load: LoadGenericNonLinear = LoadGenericNonLinear(rdfid="_gnld_model")
    nonlinear_load.genericNonLinearLoadModelType = model_kind
    nonlinear_load.tp = 4.0
    nonlinear_load.tq = 8.0
    nonlinear_load.ls = 0.0
    nonlinear_load.lt = 2.0
    nonlinear_load.bs = 0.0
    nonlinear_load.bt = 2.0
    nonlinear_load.EnergyConsumer.append(energy_consumer)
    load: Load = Load(idtag=energy_consumer.uuid, name="gnld_load", P=40.0, Q=12.0)
    bus: Bus = Bus(name="gnld_bus")
    bus.Vm0 = 0.95
    veragrid_model.add_bus(bus)
    veragrid_model.add_load(bus=bus, api_obj=load)
    cgmes_model.dynamics_assets.lists["LoadGenericNonLinear"].append(nonlinear_load)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    imported_template: RmsModelTemplate = veragrid_model.rms_models[0]
    imported_block: Block = imported_template.block
    imported_block.unify_blocks()
    runtime_event_values: dict[str, object] = dict(
        (variable.name, value)
        for variable, value in imported_block.event_dict.items()
    )
    equation_groups: tuple[list[Expr], list[Expr]] = (
        imported_block.state_eqs,
        imported_block.algebraic_eqs,
    )
    equation_variables: set[str] = set()
    for equation_group in equation_groups:
        for equation in equation_group:
            for variable in equation.get_vars():
                equation_variables.add(variable.name)

    assert len(veragrid_model.rms_models) == 1
    assert imported_template.device is load
    assert len(imported_block.state_vars) == 2
    assert len(imported_block.state_eqs) == 2
    assert len(imported_block.algebraic_eqs) == 7
    assert len(imported_block.init_eqs) == 4
    assert ParamPowerFlowReferenceType.Pl0 in imported_block.api_obj_mapping
    assert ParamPowerFlowReferenceType.Ql0 in imported_block.api_obj_mapping
    assert runtime_event_values[
        f"LoadGenericNonLinear.tp_{imported_template.name}"
    ].value == 4.0
    assert runtime_event_values[
        f"LoadGenericNonLinear.bt_{imported_template.name}"
    ].value == 2.0
    assert f"LoadGenericNonLinear.ls_{imported_template.name}" in equation_variables
    assert f"LoadGenericNonLinear.lt_{imported_template.name}" in equation_variables
    static_parameter_values: dict[Var, Const] = dict()
    assign_static_api_object_mapping_for_device(
        grid=veragrid_model,
        device=load,
        mdl=imported_block,
        problem_mapping=static_parameter_values,
    )
    assert_zero_initial_residuals(
        template=imported_template,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 0.95,
            VarPowerFlowReferenceType.P: -0.4,
            VarPowerFlowReferenceType.Q: -0.12,
        },
        parameter_values=static_parameter_values,
    )


def test_generic_nonlinear_zero_recovery_time_removes_state() -> None:
    """Use the algebraic steady-state limit when one recovery time is zero.

    :return: None.
    """
    template: RmsModelTemplate = build_load_generic_non_linear_template(
        vfactory=VarFactory(),
        name="LoadGenericNonLinear_zero_time",
        model_kind=GenericNonLinearLoadModelKind.exponentialRecovery,
        tp_value=0.0,
        tq_value=2.0,
    )
    block: Block = template.block
    block.unify_blocks()
    state_names: set[str] = set(variable.name for variable in block.state_vars)

    assert len(block.state_vars) == 1
    assert len(block.state_eqs) == 1
    assert len(block.algebraic_eqs) == 5
    assert not any(
        state_name.startswith("ActiveRecovery_")
        for state_name in state_names
    )


def test_gov_gast_zero_time_stages_are_algebraic_and_mapped() -> None:
    """Build imported zero-time GAST stages without artificial dynamic states.

    :return: None.
    """
    cgmes_object: GovGAST = GovGAST(rdfid="_gov_gast_check")
    cgmes_object.mwbase = 100.0
    cgmes_object.r = 0.04
    cgmes_object.t1 = 0.0
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.0
    cgmes_object.at = 0.95
    cgmes_object.kt = 2.5
    cgmes_object.vmax = 1.1
    cgmes_object.vmin = 0.1
    cgmes_object.dturb = 0.08
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name="gast_bus")
    machine: SynchronousMachine = SynchronousMachine(rdfid="_gast_machine")
    machine_dynamics: SynchronousMachineDynamics = SynchronousMachineDynamics(
        rdfid="_gast_machine_dynamics"
    )
    generator: Generator = Generator(idtag=machine.uuid, name="gast_machine", P=50.0)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    cgmes_model.dynamics_assets.lists["GovGAST"].append(cgmes_object)
    cgmes_model.dynamics_assets.lists["SynchronousMachineDynamics"].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    imported_template: RmsModelTemplate = veragrid_model.rms_models[0]
    template_name: str = imported_template.name
    runtime_block: Block = imported_template.block.children[0]
    reference_port: Var | None = None
    for runtime_input in runtime_block.in_vars:
        if runtime_input.name.startswith("PRefPu_"):
            reference_port = runtime_input
        else:
            pass
    runtime_events: dict[str, object] = dict(
        (variable.name, value) for variable, value in runtime_block.event_dict.items()
    )
    source_events: dict[str, object] = dict(
        (variable.name, value) for variable, value in imported_template.block.event_dict.items()
    )

    assert len(veragrid_model.rms_models) == 1
    assert imported_template.device is generator
    assert reference_port is not None
    assert runtime_block.init_eqs[reference_port].value == 0.5
    assert len(runtime_block.state_vars) == 0
    assert len(runtime_block.in_vars) == 2
    assert len(runtime_block.out_vars) == 2
    assert runtime_events["R_" + template_name].value == 0.04
    assert runtime_events["T1_" + template_name].value == 0.0
    assert runtime_events["T2_" + template_name].value == 0.0
    assert runtime_events["T3_" + template_name].value == 0.0
    assert runtime_events["AT_" + template_name].value == 0.95
    assert runtime_events["KT_" + template_name].value == 2.5
    assert runtime_events["VMAX_" + template_name].value == 1.1
    assert runtime_events["VMIN_" + template_name].value == 0.1
    assert runtime_events["Dturb_" + template_name].value == 0.08
    assert source_events["GovGAST.mwbase_" + template_name].value == 100.0

    cgmes_object.t1 = 0.1
    cgmes_object.t2 = 0.4
    cgmes_object.t3 = 3.0
    dynamic_template: RmsModelTemplate = build_gov_g_a_s_t_template(
        vfactory=VarFactory(),
        name="GovGAST_positive_time_check",
        parameters=get_gast_parameters(cgmes_object),
    )

    assert len(dynamic_template.block.children[0].state_vars) == 3


def test_gov_gast1_equations_initialize_at_constant_power() -> None:
    """Check GAST_GE conversion, machine composition, and DAE equilibrium.

    :return: None.
    """
    cgmes_object: GovGAST1 = GovGAST1(rdfid='_gov_gast1_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.r = 0.04
    cgmes_object.t1 = 0.2
    cgmes_object.t2 = 0.3
    cgmes_object.t3 = 1.0
    cgmes_object.lmax = 1.0
    cgmes_object.kt = 0.5
    cgmes_object.vmax = 1.0
    cgmes_object.vmin = 0.0
    cgmes_object.fidle = 0.18
    cgmes_object.rmax = 1.0
    cgmes_object.loadinc = 0.125
    cgmes_object.tltr = 5.0
    cgmes_object.ltrate = 0.02
    cgmes_object.a = 0.8
    cgmes_object.b = 1.0
    cgmes_object.db1 = 0.0
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.0
    cgmes_object.ka = 1.0
    cgmes_object.t4 = 0.1
    cgmes_object.t5 = 0.2

    machine: SynchronousMachine = SynchronousMachine(rdfid='_gast1_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gast1_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovGAST1'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='gast1_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='gast1_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )
    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 5
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )

    valve_states: list[Var] = [
        variable
        for runtime_block in template.block.get_all_blocks()
        for variable in runtime_block.state_vars
        if variable.name.startswith('ValvePositionPu_')
    ]
    assert len(valve_states) == 1
    valve_state: Var = valve_states[0]
    valve_block: Block = next(
        runtime_block
        for runtime_block in template.block.get_all_blocks()
        if valve_state in runtime_block.state_vars
    )
    valve_rate_equation: Expr = valve_block.state_eqs[valve_block.state_vars.index(valve_state)]
    valve_rate_parameters: set[str] = set(
        variable.name for variable in valve_rate_equation.get_vars()
    )
    assert any(name.startswith('RMAX_') for name in valve_rate_parameters)
    assert any(name.startswith('LTRATE_') for name in valve_rate_parameters)
    assert any(name.startswith('LOADINC_') for name in valve_rate_parameters)
    valve_rate_values: dict[int, float | complex] = dict()
    valve_rate_variables: list[Var] = valve_rate_equation.get_vars()
    for equation_variable in valve_rate_variables:
        valve_rate_values[equation_variable.uid] = 0.0
    else:
        pass
    for runtime_block in template.block.get_all_blocks():
        for parameter_variable, parameter_value in runtime_block.parameters.items():
            if isinstance(parameter_value, Const) and isinstance(
                    parameter_value.value, (int, float, complex)
            ):
                valve_rate_values[parameter_variable.uid] = parameter_value.value
            else:
                pass
        for event_variable, event_value in runtime_block.event_dict.items():
            if isinstance(event_value, Const) and isinstance(
                    event_value.value, (int, float, complex)
            ):
                valve_rate_values[event_variable.uid] = event_value.value
            else:
                pass
    else:
        pass
    for equation_variable in valve_rate_variables:
        if equation_variable.name.startswith('ValvePositionPu_'):
            valve_rate_values[equation_variable.uid] = 0.625
        elif equation_variable.name.startswith('ValveAveragePu_'):
            valve_rate_values[equation_variable.uid] = 0.5
        elif equation_variable.name.startswith('InputLeadLagPu_'):
            valve_rate_values[equation_variable.uid] = 2.0
        elif equation_variable.name.startswith('LoadLimitPu_'):
            valve_rate_values[equation_variable.uid] = 0.0
        else:
            pass
    else:
        pass
    exact_boundary_rate: float = float(eval_uid(valve_rate_equation, valve_rate_values))
    valve_state_value: float = 0.6250001
    for equation_variable in valve_rate_variables:
        if equation_variable.name.startswith('ValvePositionPu_'):
            valve_rate_values[equation_variable.uid] = valve_state_value
        else:
            pass
    else:
        pass
    above_boundary_rate: float = float(eval_uid(valve_rate_equation, valve_rate_values))
    valve_state_value = 0.6249
    for equation_variable in valve_rate_variables:
        if equation_variable.name.startswith('ValvePositionPu_'):
            valve_rate_values[equation_variable.uid] = valve_state_value
        else:
            pass
    else:
        pass
    below_boundary_rate: float = float(eval_uid(valve_rate_equation, valve_rate_values))
    assert isclose(exact_boundary_rate, 1.0, abs_tol=1e-8)
    assert isclose(above_boundary_rate, 0.02, abs_tol=1e-8)
    assert isclose(below_boundary_rate, 1.0, abs_tol=1e-8)


def test_gov_gast2_equations_compose_at_constant_power() -> None:
    """Check GAST2 fuel, thermal, zero-delay, and generator signal paths.

    :return: None.
    """
    cgmes_object: GovGAST2 = GovGAST2(rdfid='_gov_gast2_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.w = 20.0
    cgmes_object.x = 0.0
    cgmes_object.y = 0.1
    cgmes_object.z = 1
    cgmes_object.etd = 0.0
    cgmes_object.tcd = 0.0
    cgmes_object.trate = 100.0
    cgmes_object.t = 0.0
    cgmes_object.tmax = 1.0
    cgmes_object.tmin = 0.0
    cgmes_object.ecr = 0.0
    cgmes_object.k3 = 1.0
    cgmes_object.a = 1.0
    cgmes_object.b = 1.0
    cgmes_object.c = 1.0
    cgmes_object.tf = 0.0
    cgmes_object.kf = 0.0
    cgmes_object.k5 = 0.0
    cgmes_object.k4 = 1.0
    cgmes_object.t3 = 0.0
    cgmes_object.t4 = 0.0
    cgmes_object.tt = 0.0
    cgmes_object.t5 = 0.0
    cgmes_object.af1 = 0.0
    cgmes_object.bf1 = 0.0
    cgmes_object.af2 = 0.0
    cgmes_object.bf2 = 1.0
    cgmes_object.cf2 = 0.0
    cgmes_object.tr = 1.0
    cgmes_object.k6 = 0.0
    cgmes_object.tc = 1.0

    machine: SynchronousMachine = SynchronousMachine(rdfid='_gast2_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gast2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovGAST2'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='gast2_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='gast2_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_gastwd_fields_and_composed_equilibrium() -> None:
    """Check GovGASTWD RDF mapping, feedback wiring, and zero-time equilibrium.

    :return: None.
    """
    cgmes_object: GovGASTWD = GovGASTWD(rdfid='_gov_gastwd_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.kdroop = 0.05
    cgmes_object.kp = 1.0
    cgmes_object.ki = 1.0
    cgmes_object.kd = 0.02
    cgmes_object.etd = 0.0
    cgmes_object.tcd = 0.0
    cgmes_object.trate = 100.0
    cgmes_object.t = 0.0
    cgmes_object.tmax = 1.0
    cgmes_object.tmin = 0.0
    cgmes_object.ecr = 0.0
    cgmes_object.k3 = 1.0
    cgmes_object.a = 1.0
    cgmes_object.b = 1.0
    cgmes_object.c = 1.0
    cgmes_object.tf = 0.0
    cgmes_object.kf = 0.0
    cgmes_object.k5 = 0.0
    cgmes_object.k4 = 1.0
    cgmes_object.t3 = 0.0
    cgmes_object.t4 = 0.0
    cgmes_object.tt = 0.0
    cgmes_object.t5 = 0.0
    cgmes_object.af1 = 0.0
    cgmes_object.bf1 = 0.0
    cgmes_object.af2 = 0.0
    cgmes_object.bf2 = 1.0
    cgmes_object.cf2 = 0.0
    cgmes_object.tr = 900.0
    cgmes_object.k6 = 0.23
    cgmes_object.tc = 1000.0
    cgmes_object.td = 0.0

    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovGASTWD.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == (
        'mwbase', 'kdroop', 'kp', 'ki', 'kd', 'etd', 'tcd', 'trate', 't', 'tmax',
        'tmin', 'ecr', 'k3', 'a', 'b', 'c', 'tf', 'kf', 'k5', 'k4', 't3', 't4',
        'tt', 't5', 'af1', 'bf1', 'af2', 'bf2', 'cf2', 'tr', 'k6', 'tc', 'td',
    )
    gastwd_parameters = get_gastwd_parameters(cgmes_object)
    assert (
        gastwd_parameters.mwbase, gastwd_parameters.kdroop, gastwd_parameters.kp,
        gastwd_parameters.ki, gastwd_parameters.kd, gastwd_parameters.trate,
        gastwd_parameters.td,
    ) == (100.0, 0.05, 1.0, 1.0, 0.02, 100.0, 0.0)

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_gastwd_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gastwd_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovGASTWD'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gastwd_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='gastwd_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert template.device is generator
    assert template in veragrid_model.rms_models
    model_blocks: list[Block] = template.block.get_all_blocks()
    power_transducer_is_present: bool = any(
        variable.name.startswith('PowerTransducerPu_')
        for model_block in model_blocks
        for variable in model_block.state_vars + model_block.algebraic_vars
    )
    assert power_transducer_is_present
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_gast4_rdf_fields_and_composed_equilibrium() -> None:
    """Check canonical GovGAST4 fields, equation mapping, and machine equilibrium.

    :return: None.
    """
    cgmes_object: GovGAST4 = GovGAST4(rdfid='_gov_gast4_check')
    cgmes_object.bp = 0.04
    cgmes_object.tv = 0.2
    cgmes_object.ta = 4.0
    cgmes_object.tc = 0.6
    cgmes_object.tcm = 0.15
    cgmes_object.ktm = 0.25
    cgmes_object.tm = 0.3
    cgmes_object.rymx = 1.2
    cgmes_object.rymn = 0.05
    cgmes_object.mxef = 0.06
    cgmes_object.mnef = -0.04

    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovGAST4.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == (
        'bp', 'tv', 'ta', 'tc', 'tcm', 'ktm', 'tm', 'rymx', 'rymn', 'mxef', 'mnef',
    )
    parameters: GovGAST4Parameters = get_gast4_parameters(cgmes_object)
    assert (
        parameters.bp, parameters.tv, parameters.ta, parameters.tc,
        parameters.tcm, parameters.ktm, parameters.tm, parameters.rymx,
        parameters.rymn, parameters.mxef, parameters.mnef,
    ) == (0.04, 0.2, 4.0, 0.6, 0.15, 0.25, 0.3, 1.2, 0.05, 0.06, -0.04)

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_gast4_machine'
    )
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gast4_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovGAST4'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gast4_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='gast4_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert template.device is generator
    assert template in veragrid_model.rms_models
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_steam_cc_fields_and_zero_time_equilibrium() -> None:
    """Check GovSteamCC RDF mapping and its all-bypassed turbine topology.

    :return: None.
    """
    cgmes_object: GovSteamCC = GovSteamCC(rdfid='_gov_steam_cc_check')
    cgmes_object.mwbase = 150.0
    cgmes_object.pmaxhp = 1.1
    cgmes_object.rhp = 0.04
    cgmes_object.t1hp = 0.0
    cgmes_object.t3hp = 0.0
    cgmes_object.t4hp = 0.0
    cgmes_object.t5hp = 0.0
    cgmes_object.fhp = 0.35
    cgmes_object.dhp = 0.2
    cgmes_object.pmaxlp = 0.9
    cgmes_object.rlp = 0.06
    cgmes_object.t1lp = 0.0
    cgmes_object.t3lp = 0.0
    cgmes_object.t4lp = 0.0
    cgmes_object.t5lp = 0.0
    cgmes_object.flp = 0.65
    cgmes_object.dlp = 0.3
    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovSteamCC.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == (
        'mwbase', 'pmaxhp', 'rhp', 't1hp', 't3hp', 't4hp', 't5hp', 'fhp', 'dhp',
        'pmaxlp', 'rlp', 't1lp', 't3lp', 't4lp', 't5lp', 'flp', 'dlp',
    )
    parameters: GovSteamCCParameters = get_gov_steam_cc_parameters(cgmes_object)
    assert (
        parameters.mwbase, parameters.pmaxhp, parameters.rhp, parameters.t1hp,
        parameters.t3hp, parameters.t4hp, parameters.t5hp, parameters.fhp,
        parameters.dhp, parameters.pmaxlp, parameters.rlp, parameters.t1lp,
        parameters.t3lp, parameters.t4lp, parameters.t5lp, parameters.flp,
        parameters.dlp,
    ) == (
        150.0, 1.1, 0.04, 0.0, 0.0, 0.0, 0.0, 0.35, 0.2, 0.9, 0.06,
        0.0, 0.0, 0.0, 0.0, 0.65, 0.3,
    )

    template: RmsModelTemplate = build_gov_steam_c_c_template(
        vfactory=VarFactory(),
        name='GovSteamCC_zero_time_check',
        parameters=parameters,
    )
    runtime_blocks: list[Block] = template.block.get_all_blocks()
    assert len(template.block.in_vars) == 2
    assert len(template.block.out_vars) == 4
    assert len(runtime_blocks[0].state_vars) == 0
    assert_zero_initial_residuals(template, {})


def test_gov_steam_cc_composes_one_governor_across_two_machines() -> None:
    """Check one GovSteamCC state set, cross-root shafts, and solved operating point.

    :return: None.
    """
    governor: GovSteamCC = GovSteamCC(rdfid='_gov_steam_cc_pair')
    governor.mwbase = 100.0
    governor.pmaxhp = 1.0
    governor.rhp = 0.05
    governor.t1hp = 0.2
    governor.t3hp = 0.3
    governor.t4hp = 0.4
    governor.t5hp = 3.0
    governor.fhp = 0.3
    governor.dhp = 0.0
    governor.pmaxlp = 1.0
    governor.rlp = 1.0 / 20.25
    governor.t1lp = 0.25
    governor.t3lp = 0.35
    governor.t4lp = 0.45
    governor.t5lp = 4.0
    governor.flp = 0.7
    governor.dlp = 0.0

    hp_machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_gov_steam_cc_hp_machine'
    )
    hp_machine.ratedS = 100.0
    hp_machine.ratedPowerFactor = 1.0
    lp_machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_gov_steam_cc_lp_machine'
    )
    lp_machine.ratedS = 50.0
    lp_machine.ratedPowerFactor = 1.0
    hp_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_steam_cc_hp_dynamics'
    )
    hp_dynamics.SynchronousMachine = hp_machine
    lp_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_steam_cc_lp_dynamics'
    )
    lp_dynamics.SynchronousMachine = lp_machine
    governor.HighPressureSynchronousMachineDynamics = hp_dynamics
    governor.LowPressureSynchronousMachineDynamics = lp_dynamics

    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    cgmes_model.dynamics_assets.lists['GovSteamCC'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(hp_dynamics)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(lp_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    hp_bus: Bus = Bus(name='gov_steam_cc_hp_bus')
    lp_bus: Bus = Bus(name='gov_steam_cc_lp_bus')
    hp_generator: Generator = Generator(
        idtag=hp_machine.uuid,
        name='gov_steam_cc_hp_generator',
        P=50.0,
    )
    lp_generator: Generator = Generator(
        idtag=lp_machine.uuid,
        name='gov_steam_cc_lp_generator',
        P=25.0,
    )
    veragrid_model.add_bus(hp_bus)
    veragrid_model.add_bus(lp_bus)
    veragrid_model.add_generator(bus=hp_bus, api_obj=hp_generator)
    veragrid_model.add_generator(bus=lp_bus, api_obj=lp_generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    assert hp_generator.rms_template is not None
    assert lp_generator.rms_template is not None
    hp_template: RmsModelTemplate = hp_generator.rms_template
    lp_template: RmsModelTemplate = lp_generator.rms_template
    assert 'GovSteamCC' in hp_template.name
    assert 'GovSteamCC' in lp_template.name
    hp_root: Block = hp_generator.rms_model
    lp_root: Block = lp_generator.rms_model
    hp_speed: Var | None = find_block_variable_by_name(lp_root, 'omega')
    lp_governor_power: Var | None = find_block_variable_by_name(
        hp_root,
        f'gov.PmLpMW_{governor.__class__.__name__}_{governor.uuid}',
    )
    assert hp_speed is not None
    assert lp_governor_power is not None
    assert any(
        runtime_block.find_var_in_equations(hp_speed)
        for runtime_block in hp_root.get_all_blocks()
    )
    assert any(
        runtime_block.find_var_in_equations(lp_governor_power)
        for runtime_block in lp_root.get_all_blocks()
    )
    assert all(
        not state_variable.name.startswith('GovSteamCC')
        for runtime_block in lp_root.get_all_blocks()
        for state_variable in runtime_block.state_vars
    )
    assert_zero_initial_residuals(
        hp_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
    assert_zero_initial_residuals(
        lp_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.125,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_steam_f_v2_maps_fast_valving_and_composes_machine() -> None:
    """Check canonical fields, fast-valving time path, and machine equilibrium.

    :return: None.
    """
    governor: GovSteamFV2 = GovSteamFV2(rdfid='_gov_steam_f_v2_check')
    governor.mwbase = 100.0
    governor.t1 = 0.2
    governor.vmax = 1.0
    governor.vmin = 0.0
    governor.k = 0.3
    governor.t3 = 0.3
    governor.dt = 0.04
    governor.tt = 0.4
    governor.r = 0.05
    governor.ta = 0.1
    governor.tb = 0.2
    governor.tc = 0.5
    governor.ti = 0.0
    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovSteamFV2.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == (
        'mwbase', 't1', 'vmax', 'vmin', 'k', 't3', 'dt', 'tt', 'r', 'ta', 'tb', 'tc', 'ti',
    )
    parameters: GovSteamFV2Parameters = get_gov_steam_f_v2_parameters(governor)
    assert (
        parameters.mwbase, parameters.t1, parameters.vmax, parameters.vmin,
        parameters.k, parameters.t3, parameters.dt, parameters.tt, parameters.r,
        parameters.ta, parameters.tb, parameters.tc,
        parameters.ti,
    ) == (100.0, 0.2, 1.0, 0.0, 0.3, 0.3, 0.04, 0.4, 0.05, 0.1, 0.2, 0.5, 0.0)

    standalone_template: RmsModelTemplate = build_gov_steam_f_v2_template(
        vfactory=VarFactory(),
        name='GovSteamFV2_operating_point_check',
        parameters=parameters,
    )
    global_time: Var | None = None
    for equation_block in standalone_template.block.get_all_blocks():
        for equation_collection in (equation_block.algebraic_eqs, equation_block.state_eqs):
            for equation in equation_collection:
                for equation_variable in equation.get_vars():
                    if equation_variable.name == 'glob_time':
                        global_time = equation_variable
                    else:
                        pass
    assert global_time is not None
    standalone_template.block.update_model(global_time, Const(0.0))
    assert_zero_initial_residuals(standalone_template, {})
    zero_time_template: RmsModelTemplate = build_gov_steam_f_v2_template(
        vfactory=VarFactory(),
        name='GovSteamFV2_zero_time_check',
        parameters=GovSteamFV2Parameters(t1=0.0, t3=0.0, tt=0.0),
    )
    assert all(
        len(equation_block.state_vars) == 0
        for equation_block in zero_time_template.block.get_all_blocks()
    )

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_gov_steam_f_v2_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_steam_f_v2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovSteamFV2'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gov_steam_f_v2_bus')
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='gov_steam_f_v2_generator',
        P=50.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    assert generator.rms_template is not None
    assert 'GovSteamFV2' in generator.rms_template.name
    reference_input: Var | None = find_block_variable_by_name(
        generator.rms_model,
        f'gov.omegaRefPu_GovSteamFV2_{governor.uuid}',
    )
    assert reference_input is not None
    assert any(
        initial_variable.uid == reference_input.uid
        and isinstance(initial_expression, Const)
        and initial_expression.value == 1.025
        for runtime_block in generator.rms_model.get_all_blocks()
        for initial_variable, initial_expression in runtime_block.init_eqs.items()
    )
    imported_template: RmsModelTemplate = deepcopy(generator.rms_template)
    imported_global_time: Var | None = None
    for equation_block in imported_template.block.get_all_blocks():
        for equation_collection in (equation_block.algebraic_eqs, equation_block.state_eqs):
            for equation in equation_collection:
                for equation_variable in equation.get_vars():
                    if equation_variable.name == 'glob_time':
                        imported_global_time = equation_variable
                    else:
                        pass
    assert imported_global_time is not None
    imported_template.block.update_model(imported_global_time, Const(0.0))
    assert_zero_initial_residuals(
        imported_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_steam_f_v3_maps_curve_and_composes_machine() -> None:
    """Check FV3 canonical parameters and zero-time composed equilibrium.

    :return: None.
    """
    governor: GovSteamFV3 = GovSteamFV3(rdfid='_gov_steam_f_v3_check')
    governor.mwbase = 100.0
    governor.k = 0.3
    governor.t1 = 0.2
    governor.t2 = 0.4
    governor.t3 = 0.1
    governor.uo = 0.1
    governor.uc = -0.2
    governor.pmax = 1.25
    governor.pmin = 0.0
    governor.t4 = 0.2
    governor.k1 = 0.2
    governor.t5 = 0.5
    governor.k2 = 0.2
    governor.t6 = 10.0
    governor.k3 = 0.6
    governor.ta = 0.1
    governor.tb = 0.2
    governor.tc = 0.5
    governor.prmax = 1.1
    governor.gv1 = 0.0
    governor.pgv1 = 0.0
    governor.gv2 = 0.25
    governor.pgv2 = 0.25
    governor.gv3 = 0.5
    governor.pgv3 = 0.5
    governor.gv4 = 0.75
    governor.pgv4 = 0.75
    governor.gv5 = 1.0
    governor.pgv5 = 1.0
    governor.gv6 = 1.25
    governor.pgv6 = 1.25
    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovSteamFV3.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == (
        'mwbase', 'k', 't1', 't2', 't3', 'uo', 'uc', 'pmax', 'pmin', 't4', 'k1',
        't5', 'k2', 't6', 'k3', 'ta', 'tb', 'tc', 'prmax', 'gv1', 'pgv1', 'gv2',
        'pgv2', 'gv3', 'pgv3', 'gv4', 'pgv4', 'gv5', 'pgv5', 'gv6', 'pgv6',
    )
    parameters: GovSteamFV3Parameters = get_gov_steam_f_v3_parameters(governor)
    assert parameters.gv_points == (0.0, 0.25, 0.5, 0.75, 1.0, 1.25)
    assert parameters.pgv_points == (0.0, 0.25, 0.5, 0.75, 1.0, 1.25)

    standalone_template: RmsModelTemplate = build_gov_steam_f_v3_template(
        vfactory=VarFactory(),
        name='GovSteamFV3_operating_point_check',
        parameters=parameters,
    )
    standalone_global_time: Var | None = None
    for equation_block in standalone_template.block.get_all_blocks():
        for equation in equation_block.algebraic_eqs + equation_block.state_eqs:
            for equation_variable in equation.get_vars():
                if equation_variable.name == 'glob_time':
                    standalone_global_time = equation_variable
                else:
                    pass
    assert standalone_global_time is not None
    standalone_template.block.update_model(standalone_global_time, Const(0.0))
    standalone_reference: Var | None = find_block_variable_by_name(
        standalone_template.block,
        'PmRefPu_GovSteamFV3_operating_point_check',
    )
    assert standalone_reference is not None
    for equation_block in standalone_template.block.get_all_blocks():
        if standalone_reference in equation_block.init_eqs:
            equation_block.init_eqs[standalone_reference] = Const(0.5)
        else:
            pass
    assert_zero_initial_residuals(standalone_template, {})

    zero_stage_template: RmsModelTemplate = build_gov_steam_f_v3_template(
        vfactory=VarFactory(),
        name='GovSteamFV3_zero_stage_check',
        parameters=GovSteamFV3Parameters(t4=0.0, t6=0.0),
    )
    assert all(
        len(equation_block.state_vars) >= 2
        for equation_block in zero_stage_template.block.get_all_blocks()
    )

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_gov_steam_f_v3_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_steam_f_v3_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovSteamFV3'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gov_steam_f_v3_bus')
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='gov_steam_f_v3_generator',
        P=50.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )
    assert generator.rms_template is not None
    assert 'GovSteamFV3' in generator.rms_template.name
    composed_reference: Var | None = find_block_variable_by_name(
        generator.rms_template.block,
        f'PmRefPu_GovSteamFV3_{governor.uuid}',
    )
    assert composed_reference is not None
    assert any(
        initial_variable.uid == composed_reference.uid
        and isinstance(initial_expression, Const)
        and initial_expression.value == 0.5
        for runtime_block in generator.rms_template.block.get_all_blocks()
        for initial_variable, initial_expression in runtime_block.init_eqs.items()
    )
    composed_template: RmsModelTemplate = deepcopy(generator.rms_template)
    composed_global_time: Var | None = None
    for equation_block in composed_template.block.get_all_blocks():
        for equation in equation_block.algebraic_eqs + equation_block.state_eqs:
            for equation_variable in equation.get_vars():
                if equation_variable.name == 'glob_time':
                    composed_global_time = equation_variable
                else:
                    pass
    assert composed_global_time is not None
    composed_template.block.update_model(composed_global_time, Const(0.0))
    assert_zero_initial_residuals(
        composed_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    ('generator_power', 'control_valve_maximum', 'intercept_valve_maximum'),
    ((0.0, 1.1, 1.1), (50.0, 0.42279320785824, 1.1), (92.36631016042782, 0.5, 0.56)),
)
def test_gov_steam_f_v4_maps_and_composes_machine(
        generator_power: float,
        control_valve_maximum: float,
        intercept_valve_maximum: float,
) -> None:
    """Check all FV4 RDF fields and machine-base operating-point equilibrium.

    :param generator_power: Generator active power in MW for the operating point.
    :param control_valve_maximum: Control-valve position upper bound.
    :param intercept_valve_maximum: Intercept-valve position upper bound.
    :return: None.
    """
    governor: GovSteamFV4 = GovSteamFV4(rdfid='_gov_steam_f_v4_check')
    parameter_names: tuple[str, ...] = (
        'kf1', 'kf3', 'lps', 'lpi', 'mxef', 'mnef', 'crmx', 'crmn', 'kpt', 'kit',
        'rvgmx', 'rvgmn', 'svmx', 'svmn', 'srmx', 'srmn', 'kpp', 'kip',
        'rsmimx', 'rsmimn', 'kmp1', 'kmp2', 'srsmp', 'ta', 'tc', 'ty', 'yhpmx',
        'yhpmn', 'tam', 'tcm', 'ympmx', 'ympmn', 'y', 'thp', 'trh', 'tmp',
        'khp', 'pr1', 'pr2', 'psmn', 'kpc', 'kic', 'kdc', 'tdc', 'cpsmx',
        'cpsmn', 'krc', 'tf1', 'tf2', 'tv', 'ksh',
    )
    for parameter_index, parameter_name in enumerate(parameter_names):
        governor.set_declared_property_value(parameter_name, float(parameter_index + 1))
    # Restore valid signs, breakpoints, limits, and times for an executable model.
    governor.lps = 0.03
    governor.lpi = -0.15
    governor.mxef = 0.05
    governor.mnef = -0.05
    governor.crmx = 1.2
    governor.crmn = 0.0
    governor.rvgmx = 1.2
    governor.rvgmn = 0.0
    governor.svmx = 0.0333
    governor.svmn = -0.0333
    governor.srmx = 1.1
    governor.srmn = 0.0
    governor.rsmimx = 1.1
    governor.rsmimn = 0.0
    governor.kmp1 = 0.5
    governor.kmp2 = 3.5
    governor.srsmp = 0.43
    governor.ta = 0.8
    governor.tc = 0.5
    governor.ty = 0.1
    governor.yhpmx = 1.1
    governor.yhpmn = 0.0
    governor.tam = 0.8
    governor.tcm = 0.5
    governor.ympmx = 1.1
    governor.ympmn = 0.0
    governor.y = 0.13
    governor.thp = 0.15
    governor.trh = 10.0
    governor.tmp = 0.4
    governor.khp = 0.35
    governor.pr1 = 0.2
    governor.pr2 = 0.75
    governor.psmn = 1.0
    governor.kpc = 0.5
    governor.kic = 0.0033
    governor.kdc = 1.0
    governor.tdc = 90.0
    governor.cpsmx = 1.0
    governor.cpsmn = -1.0
    governor.krc = 0.05
    governor.tf1 = 10.0
    governor.tf2 = 10.0
    governor.tv = 60.0
    governor.ksh = 0.08
    # Each point places one or both servo positions exactly at a tested configured stop.
    governor.yhpmx = control_valve_maximum
    governor.ympmx = intercept_valve_maximum
    rdf_fields: tuple[str, ...] = tuple(
        property_definition.property_name
        for property_definition in GovSteamFV4.LOCAL_CGMES_PROPERTIES
    )
    assert rdf_fields == parameter_names
    parameters: GovSteamFV4Parameters = get_gov_steam_f_v4_parameters(governor)
    assert parameters.kf1 == 1.0
    assert parameters.kf3 == 2.0
    assert parameters.ksh == 0.08

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_gov_steam_f_v4_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_gov_steam_f_v4_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovSteamFV4'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    bus: Bus = Bus(name='gov_steam_f_v4_bus')
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='gov_steam_f_v4_generator',
        P=generator_power,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )
    assert not any(
        'GovSteamFV4 bounds cannot reproduce' in entry.msg
        for entry in logger.entries
    )
    assert generator.rms_template is not None
    assert 'GovSteamFV4' in generator.rms_template.name
    composed_template: RmsModelTemplate = deepcopy(generator.rms_template)
    if generator_power == 0.0:
        pressure_integral: Var | None = find_block_variable_by_name(
            composed_template.block,
            f'GovSteamFV4PressureIntegralPu_GovSteamFV4_{governor.uuid}',
        )
        control_valve: Var | None = find_block_variable_by_name(
            composed_template.block,
            f'GovSteamFV4ControlValvePu_GovSteamFV4_{governor.uuid}',
        )
        assert pressure_integral is not None
        assert control_valve is not None
        pressure_integral_initial: Expr | Const | None = find_block_initial_value(
            composed_template.block, pressure_integral,
        )
        control_valve_initial: Expr | Const | None = find_block_initial_value(
            composed_template.block, control_valve,
        )
        assert isinstance(pressure_integral_initial, Const)
        assert isinstance(control_valve_initial, Const)
        assert isclose(pressure_integral_initial.value, parameters.cpsmn, abs_tol=1e-12)
        assert isclose(control_valve_initial.value, parameters.yhpmn, abs_tol=1e-12)
    elif generator_power in (50.0, 92.36631016042782):
        control_valve: Var | None = find_block_variable_by_name(
            composed_template.block,
            f'GovSteamFV4ControlValvePu_GovSteamFV4_{governor.uuid}',
        )
        intercept_valve: Var | None = find_block_variable_by_name(
            composed_template.block,
            f'GovSteamFV4InterceptValvePu_GovSteamFV4_{governor.uuid}',
        )
        assert control_valve is not None
        assert intercept_valve is not None
        control_valve_initial = find_block_initial_value(composed_template.block, control_valve)
        intercept_valve_initial = find_block_initial_value(composed_template.block, intercept_valve)
        assert isinstance(control_valve_initial, Const)
        assert isinstance(intercept_valve_initial, Const)
        assert isclose(control_valve_initial.value, parameters.yhpmx, abs_tol=1e-12)
        if generator_power == 92.36631016042782:
            assert isclose(intercept_valve_initial.value, parameters.ympmx, abs_tol=1e-12)
        else:
            pass
    else:
        pass
    assert_zero_initial_residuals(
        composed_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: generator_power / veragrid_model.Sbase,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro_ieee0_equations_compose_at_constant_power() -> None:
    """Check hydro governor equations and imported MWBASE on its generator.

    :return: None.
    """
    cgmes_object: GovHydroIEEE0 = GovHydroIEEE0(rdfid='_gov_hydro_ieee0_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.k = 20.0
    cgmes_object.t1 = 0.25
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.1
    cgmes_object.t4 = 0.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_hydro_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroIEEE0'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro1_equations_compose_at_constant_power() -> None:
    """Check the nonlinear dam-head governor initializes and drives the machine.

    :return: None.
    """
    cgmes_object: GovHydro1 = GovHydro1(rdfid='_gov_hydro1_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.rperm = 0.05
    cgmes_object.rtemp = 0.3
    cgmes_object.tr = 5.0
    cgmes_object.tf = 0.05
    cgmes_object.tg = 0.5
    cgmes_object.velm = 0.2
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.tw = 1.0
    cgmes_object.at = 1.0
    cgmes_object.dturb = 0.02
    cgmes_object.qnl = 0.08
    cgmes_object.hdam = 1.21

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_hydro1_machine')
    machine.ratedS = 120.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro1_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    assert isclose(get_gov_hydro1_parameters(cgmes_object).dturb, 0.024)
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydro1'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro1_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro1_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro2_equations_compose_at_constant_power() -> None:
    """Check GovHydro2 curve/deadband mapping and generator initialization.

    :return: None.
    """
    cgmes_object: GovHydro2 = GovHydro2(rdfid='_gov_hydro2_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.tg = 0.5
    cgmes_object.tp = 0.03
    cgmes_object.uo = 0.1
    cgmes_object.uc = -0.1
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.rperm = 0.05
    cgmes_object.rtemp = 0.5
    cgmes_object.tr = 12.0
    cgmes_object.tw = 2.0
    cgmes_object.kturb = 1.0
    cgmes_object.aturb = -1.0
    cgmes_object.bturb = 0.5
    cgmes_object.db1 = 0.12
    cgmes_object.eps = 0.02
    cgmes_object.db2 = 0.1
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.1
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.3
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.55
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 0.78
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_hydro2_machine'
    )
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    assert isclose(get_gov_hydro2_parameters(cgmes_object, 60.0).nominal_frequency, 60.0)
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydro2'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0)
    bus: Bus = Bus(name='hydro2_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro2_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro2_zero_pilot_lag_rate_stops_and_curve_endpoints() -> None:
    """Check exact pilot bypass, directional gate stops, and endpoint curve segments.

    :return: None.
    """
    parameters: GovHydro2Parameters = GovHydro2Parameters(
        tp=0.0,
        gv_points=(0.2, 0.4, 0.6, 0.8, 0.0, 0.0),
        pgv_points=(0.1, 0.3, 0.55, 0.78, 0.0, 0.0),
    )
    template: RmsModelTemplate = build_gov_hydro2_template(
        vfactory=VarFactory(),
        name='gov_hydro2_zero_pilot',
        parameters=parameters,
    )
    block: Block = template.block.children[0]
    assert not any(
        variable.name.startswith('PilotValvePu_gov_hydro2_zero_pilot')
        for variable in block.state_vars
    )
    gate_state: Var | None = find_block_variable_by_name(
        block,
        'GateOpeningPu_gov_hydro2_zero_pilot',
    )
    gate_rate: Var | None = find_block_variable_by_name(
        block,
        'GateRatePuPerSecond_gov_hydro2_zero_pilot',
    )
    assert gate_state is not None
    assert gate_rate is not None
    gate_rate_equation: Expr | None = None
    for equation in block.algebraic_eqs:
        if isinstance(equation, BinOp) and equation.left is gate_rate:
            gate_rate_equation = equation.right
        else:
            pass
    assert gate_rate_equation is not None
    assert isclose(
        gate_rate_equation.eval(
            PilotValvePu_gov_hydro2_zero_pilot=2.0,
            **{
                'GovHydro2.tg_gov_hydro2_zero_pilot': parameters.tg,
                'GovHydro2.uo_gov_hydro2_zero_pilot': parameters.uo,
                'GovHydro2.uc_gov_hydro2_zero_pilot': parameters.uc,
            },
        ),
        parameters.uo,
        abs_tol=1.0e-12,
    )
    assert isclose(
        gate_rate_equation.eval(
            PilotValvePu_gov_hydro2_zero_pilot=-2.0,
            **{
                'GovHydro2.tg_gov_hydro2_zero_pilot': parameters.tg,
                'GovHydro2.uo_gov_hydro2_zero_pilot': parameters.uo,
                'GovHydro2.uc_gov_hydro2_zero_pilot': parameters.uc,
            },
        ),
        parameters.uc,
        abs_tol=1.0e-12,
    )

    first_gate: float = parameters.gv_points[0]
    first_power: float = parameters.pgv_points[0]
    below_first_gate: float = 0.1
    below_first_expected: float = parameters.pmax * first_power * below_first_gate / first_gate
    assert isclose(
        get_gov_hydro2_curve_power(parameters, below_first_gate),
        below_first_expected,
        abs_tol=1.0e-12,
    )
    last_gate: float = parameters.gv_points[3]
    last_power: float = parameters.pgv_points[3]
    above_last_gate: float = 0.9
    above_last_expected: float = parameters.pmax * (
        last_power + (1.0 - last_power) * (above_last_gate - last_gate) / (1.0 - last_gate)
    )
    assert isclose(
        get_gov_hydro2_curve_power(parameters, above_last_gate),
        above_last_expected,
        abs_tol=1.0e-12,
    )


def test_gov_hydro2_speed_deadband_exact_pickup_and_dropout() -> None:
    """Check strict deadband pickup and inclusive dropout at exact boundaries.

    :return: None.
    """
    parameters: GovHydro2Parameters = GovHydro2Parameters(
        db1=0.125,
        eps=0.0625,
        nominal_frequency=1.0,
    )
    template: RmsModelTemplate = build_gov_hydro2_template(
        vfactory=VarFactory(),
        name='gov_hydro2_deadband_boundary',
        parameters=parameters,
    )
    positive_logic: FlipFlopLogic = template.block.children[0].procedural_logic[0]
    negative_logic: FlipFlopLogic = template.block.children[0].procedural_logic[1]
    threshold: float = parameters.db1
    pickup: float = parameters.db1 + parameters.eps
    deadband_parameters: dict[str, float] = {
        'GovHydro2.db1_gov_hydro2_deadband_boundary': parameters.db1,
        'GovHydro2.eps_gov_hydro2_deadband_boundary': parameters.eps,
    }
    assert isclose(positive_logic.set_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=pickup,
        **deadband_parameters,
    ), 0.0)
    assert isclose(positive_logic.set_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=pickup + 1.0e-8,
        **deadband_parameters,
    ), 1.0)
    assert isclose(positive_logic.reset_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=threshold,
        **deadband_parameters,
    ), 1.0)
    assert isclose(positive_logic.reset_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=threshold + 1.0e-8,
        **deadband_parameters,
    ), 0.0)
    assert isclose(negative_logic.set_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=-pickup,
        **deadband_parameters,
    ), 0.0)
    assert isclose(negative_logic.set_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=-pickup - 1.0e-8,
        **deadband_parameters,
    ), 1.0)
    assert isclose(negative_logic.reset_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=-threshold,
        **deadband_parameters,
    ), 1.0)
    assert isclose(negative_logic.reset_expr.eval(
        SpeedDeviationPu_gov_hydro2_deadband_boundary=-threshold - 1.0e-8,
        **deadband_parameters,
    ), 0.0)


def test_gov_hydro3_equations_compose_at_constant_power() -> None:
    """Check GovHydro3 field mapping and operating-point machine composition.

    :return: None.
    """
    cgmes_object: GovHydro3 = GovHydro3(rdfid='_gov_hydro3_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.governorControl = True
    cgmes_object.rgate = 0.05
    cgmes_object.relec = 0.05
    cgmes_object.td = 0.1
    cgmes_object.tf = 0.1
    cgmes_object.tp = 0.1
    cgmes_object.velop = 0.2
    cgmes_object.velcl = -0.2
    cgmes_object.k1 = 1.0
    cgmes_object.k2 = 0.2
    cgmes_object.ki = 0.5
    cgmes_object.kg = 1.0
    cgmes_object.tt = 0.5
    cgmes_object.db1 = 0.0
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0
    cgmes_object.tw = 2.0
    cgmes_object.at = 1.2
    cgmes_object.dturb = 0.2
    cgmes_object.qnl = 0.0
    cgmes_object.h0 = 1.0
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_hydro3_machine'
    )
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro3_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    assert isclose(get_gov_hydro3_parameters(cgmes_object, 60.0).nominal_frequency, 60.0)
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydro3'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0, fbase=60.0)
    bus: Bus = Bus(name='hydro3_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro3_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
    mapped_control_flag: bool = any(
        variable.name.startswith('GovHydro3.governorControl_')
        for model_block in template.block.get_all_blocks()
        for variable in model_block.event_dict
    )
    assert mapped_control_flag


def test_gov_hydro4_equations_compose_at_constant_power() -> None:
    """Check GovHydro4 simple-turbine initialization and machine composition.

    :return: None.
    """
    cgmes_object: GovHydro4 = GovHydro4(rdfid='_gov_hydro4_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.model = GovHydro4ModelKind.simple
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.tg = 0.5
    cgmes_object.tp = 0.1
    cgmes_object.uo = 0.2
    cgmes_object.uc = -0.2
    cgmes_object.rperm = 0.05
    cgmes_object.rtemp = 0.3
    cgmes_object.tr = 5.0
    cgmes_object.tw = 1.0
    cgmes_object.at = 1.2
    cgmes_object.dturb = 0.2
    cgmes_object.hdam = 1.0
    cgmes_object.qnl = 0.08
    cgmes_object.db1 = 0.0
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_hydro4_machine'
    )
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro4_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    mapped_parameters = get_gov_hydro4_parameters(cgmes_object, 50.0)
    assert mapped_parameters.model.value == 'simple'
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydro4'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0)
    bus: Bus = Bus(name='hydro4_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro4_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro4_kaplan_bgv_initialization_composes_at_constant_power() -> None:
    """Check Kaplan blade-curve equilibrium and associated machine composition.

    :return: None.
    """
    cgmes_object: GovHydro4 = GovHydro4(rdfid='_gov_hydro4_kaplan_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.model = GovHydro4ModelKind.kaplan
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.tg = 0.5
    cgmes_object.tp = 0.1
    cgmes_object.uo = 0.2
    cgmes_object.uc = -0.2
    cgmes_object.rperm = 0.05
    cgmes_object.rtemp = 0.3
    cgmes_object.tr = 5.0
    cgmes_object.tw = 1.0
    cgmes_object.at = 1.2
    cgmes_object.dturb = 0.2
    cgmes_object.hdam = 1.0
    cgmes_object.qnl = 0.08
    cgmes_object.bmax = 1.2
    cgmes_object.tblade = 3.0
    cgmes_object.gv0 = 0.0
    cgmes_object.gv1 = 0.2
    cgmes_object.gv2 = 0.4
    cgmes_object.gv3 = 0.6
    cgmes_object.gv4 = 0.8
    cgmes_object.gv5 = 0.9
    cgmes_object.pgv0 = 0.0
    cgmes_object.pgv1 = 0.18
    cgmes_object.pgv2 = 0.36
    cgmes_object.pgv3 = 0.54
    cgmes_object.pgv4 = 0.72
    cgmes_object.pgv5 = 0.9
    cgmes_object.bgv0 = 0.0
    cgmes_object.bgv1 = 0.1
    cgmes_object.bgv2 = 0.22
    cgmes_object.bgv3 = 0.37
    cgmes_object.bgv4 = 0.56
    cgmes_object.bgv5 = 0.75

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_hydro4_kaplan_machine',
    )
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro4_kaplan_machine_dynamics',
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    mapped_parameters = get_gov_hydro4_parameters(cgmes_object, 50.0)
    assert mapped_parameters.model.value == 'kaplan'
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydro4'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0)
    bus: Bus = Bus(name='hydro4_kaplan_bus')
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='hydro4_kaplan_machine',
        P=50.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro4_2_4_15_adapter_uses_legacy_qn1_and_curve_selector() -> None:
    """Check the legacy RDF field names without relying on the 2020 model enum.

    :return: None.
    """
    cgmes_object: GovHydro424 = GovHydro424(rdfid='_gov_hydro4_2415_adapter')
    cgmes_object.qn1 = 0.12
    cgmes_object.gv0 = 0.0
    cgmes_object.gv1 = 0.2
    cgmes_object.gv2 = 0.4
    cgmes_object.gv3 = 0.6
    cgmes_object.gv4 = 0.8
    cgmes_object.gv5 = 1.0

    mapped_parameters = get_gov_hydro4_parameters(cgmes_object, 50.0)

    assert mapped_parameters.qnl == 0.12
    assert mapped_parameters.model.value == 'francisPelton'


@pytest.mark.parametrize(
    'control_kind',
    (
        FrancisGovernorControlKind.mechanicHydrolicTachoAccelerator,
        FrancisGovernorControlKind.mechanicHydraulicTransientFeedback,
        FrancisGovernorControlKind.electromechanicalElectrohydraulic,
    ),
)
@pytest.mark.parametrize('waterway_enabled', (False, True))
@pytest.mark.parametrize('zero_time_stages', (False, True))
def test_gov_hydro_francis_control_modes_compose_at_constant_power(
        control_kind: FrancisGovernorControlKind,
        waterway_enabled: bool,
        zero_time_stages: bool,
) -> None:
    """Check each RDF control selection, machine coupling, and steady seed.

    :param control_kind: Canonical RDF enum selecting one Francis regulator.
    :return: None.
    """
    cgmes_object: GovHydroFrancis = GovHydroFrancis(
        rdfid=f'_gov_hydro_francis_{control_kind.name}'
    )
    cgmes_object.governorControl = control_kind
    cgmes_object.waterTunnelSurgeChamberSimulation = waterway_enabled
    cgmes_object.am = 0.7
    cgmes_object.av0 = 30.0
    cgmes_object.av1 = 700.0
    cgmes_object.bp = 0.05
    cgmes_object.db1 = 0.0
    cgmes_object.etamax = 1.05
    cgmes_object.h1 = 40.0 if waterway_enabled else 4.0
    cgmes_object.h2 = 400.0 if waterway_enabled else 40.0
    cgmes_object.hn = 250.0
    cgmes_object.kc = 0.025
    cgmes_object.kg = 0.025
    cgmes_object.kt = 0.25
    cgmes_object.qc0 = 0.1
    cgmes_object.qn = 250.0
    cgmes_object.ta = 3.0
    cgmes_object.td = 0.0 if zero_time_stages else 6.0
    cgmes_object.ts = 0.0 if zero_time_stages else 0.5
    cgmes_object.twnc = 1.0
    cgmes_object.twng = 3.0
    cgmes_object.tx = 1.0
    cgmes_object.va = 0.06
    cgmes_object.valvmax = 1.1
    cgmes_object.valvmin = 0.0
    cgmes_object.vc = -0.06
    cgmes_object.zsfc = 250.0 if waterway_enabled else 25.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid=f'_francis_machine_{control_kind.name}'
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid=f'_francis_machine_dynamics_{control_kind.name}'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroFrancis'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0)
    bus: Bus = Bus(name='francis_bus')
    generator: Generator = Generator(
        idtag=machine.uuid, name='francis_machine', P=50.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    parameter_values: dict[str, float] = dict()
    equation_names: set[str] = set()
    algebraic_signal_names: set[str] = set()
    for runtime_block in template.block.get_all_blocks():
        for variable, expression in runtime_block.event_dict.items():
            if variable.name.startswith('GovHydroFrancis.') and isinstance(expression, Const):
                if isinstance(expression.value, (int, float)):
                    parameter_values[variable.name.split('.')[1].split('_')[0]] = float(expression.value)
                else:
                    pass
            else:
                pass
        for equation in runtime_block.state_eqs + runtime_block.algebraic_eqs:
            equation_names.update(variable.name for variable in equation.get_vars())
        algebraic_signal_names.update(
            variable.name for variable in runtime_block.algebraic_vars
        )
    assert parameter_values['governorControl'] == float(
        list(FrancisGovernorControlKind).index(control_kind) + 1
    )
    assert parameter_values['hn'] == 250.0
    assert 'OmegaDerivativePu' in equation_names
    assert any(name.startswith('TurbineEfficiencyPu_') for name in algebraic_signal_names)
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize('simplified_pelton', (True, False))
@pytest.mark.parametrize('waterway_enabled', (False, True))
@pytest.mark.parametrize('zero_time_stages', (False, True))
def test_gov_hydro_pelton_maps_and_composes_at_constant_power(
        simplified_pelton: bool,
        waterway_enabled: bool,
        zero_time_stages: bool,
) -> None:
    """Check Pelton selectors, RDF mapping, and machine operating-point residuals.

    :param simplified_pelton: Select the simplified turbine characteristic.
    :param waterway_enabled: Select detailed tunnel/surge-chamber equations.
    :param zero_time_stages: Reduce governor and waterway lags algebraically.
    :return: None.
    """
    cgmes_object: GovHydroPelton = GovHydroPelton(
        rdfid=f'_gov_hydro_pelton_{simplified_pelton}_{waterway_enabled}_{zero_time_stages}'
    )
    cgmes_object.av0 = 30.0
    cgmes_object.av1 = 700.0
    cgmes_object.bp = 0.05
    cgmes_object.db1 = 0.0
    cgmes_object.db2 = 0.01
    cgmes_object.h1 = 40.0 if waterway_enabled else 4.0
    cgmes_object.h2 = 400.0 if waterway_enabled else 40.0
    cgmes_object.hn = 250.0
    cgmes_object.kc = 0.025
    cgmes_object.kg = 0.025
    cgmes_object.qc0 = 0.1
    cgmes_object.qn = 250.0
    cgmes_object.simplifiedPelton = simplified_pelton
    cgmes_object.staticCompensating = True
    cgmes_object.ta = 3.0
    cgmes_object.ts = 0.0 if zero_time_stages else 0.5
    cgmes_object.tv = 0.0 if zero_time_stages else 0.3
    cgmes_object.twnc = 0.0 if zero_time_stages else 1.0
    cgmes_object.twng = 0.0 if zero_time_stages else 3.0
    cgmes_object.tx = 0.0 if zero_time_stages else 0.5
    cgmes_object.va = 0.06
    cgmes_object.valvmax = 1.1
    cgmes_object.valvmin = 0.0
    cgmes_object.vav = 0.1
    cgmes_object.vc = -0.06
    cgmes_object.vcv = -0.1
    cgmes_object.waterTunnelSurgeChamberSimulation = waterway_enabled
    cgmes_object.zsfc = 250.0 if waterway_enabled else 25.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid=f'_pelton_machine_{simplified_pelton}_{waterway_enabled}_{zero_time_stages}'
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid=f'_pelton_machine_dynamics_{simplified_pelton}_{waterway_enabled}_{zero_time_stages}'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroPelton'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0, fbase=50.0)
    bus: Bus = Bus(name='pelton_bus')
    generator: Generator = Generator(
        idtag=machine.uuid, name='pelton_machine', P=50.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    mapped_parameters: GovHydroPeltonParameters = get_gov_hydro_pelton_parameters(
        cgmes_object, 50.0,
    )
    parameter_values: dict[str, float] = dict()
    equation_names: set[str] = set()
    for runtime_block in template.block.get_all_blocks():
        for variable, expression in runtime_block.event_dict.items():
            if variable.name.startswith('GovHydroPelton.') and isinstance(expression, Const):
                if isinstance(expression.value, (int, float)):
                    parameter_name: str = variable.name.split('.')[1].split('_')[0]
                    parameter_values[parameter_name] = float(expression.value)
                else:
                    pass
            else:
                pass
        for equation in runtime_block.state_eqs + runtime_block.algebraic_eqs:
            equation_names.update(variable.name for variable in equation.get_vars())
    assert parameter_values['simplifiedPelton'] == float(simplified_pelton)
    assert parameter_values['staticCompensating'] == 1.0
    assert parameter_values['waterTunnelSurgeChamberSimulation'] == float(waterway_enabled)
    assert mapped_parameters.simplified_pelton is simplified_pelton
    assert mapped_parameters.static_compensating is True
    assert mapped_parameters.waterway_enabled is waterway_enabled
    assert parameter_values['db1'] == 0.0
    assert 'OmegaDerivativePu' in equation_names
    assert any(name.startswith('PeltonNeedlePositionPu_') for name in equation_names)
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize('input_signal', (True, False))
@pytest.mark.parametrize('zero_time_stages', (True, False))
def test_gov_hydro_dd_equations_compose_at_constant_power(
        input_signal: bool,
        zero_time_stages: bool,
) -> None:
    """Check GovHydroDD input-signal mapping and integrated machine residuals.

    :return: None.
    """
    cgmes_object: GovHydroDD = GovHydroDD(rdfid='_gov_hydro_dd_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.r = 0.05
    cgmes_object.td = 0.0 if zero_time_stages else 0.1
    cgmes_object.tf = 0.0 if zero_time_stages else 0.1
    cgmes_object.tp = 0.0 if zero_time_stages else 0.1
    cgmes_object.velop = 0.2
    cgmes_object.velcl = 0.2
    cgmes_object.k1 = 1.0
    cgmes_object.k2 = 0.2
    cgmes_object.ki = 0.5
    cgmes_object.kg = 1.0
    cgmes_object.tturb = 0.0 if zero_time_stages else 1.0
    cgmes_object.aturb = -1.0
    cgmes_object.bturb = 0.5
    cgmes_object.tt = 0.0 if zero_time_stages else 0.5
    cgmes_object.db1 = 0.0
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.0
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.inputSignal = input_signal

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid='_hydro_dd_machine'
    )
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_dd_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    assert get_gov_hydro_dd_parameters(cgmes_object).input_signal is input_signal
    assert len(GovHydroDD.LOCAL_CGMES_PROPERTIES) == 35
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroDD'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    assert len(GovHydroDD.LOCAL_CGMES_PROPERTIES) == 35

    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0, fbase=50.0)
    bus: Bus = Bus(name='hydro_dd_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_dd_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.25,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro_ieee2_equations_compose_at_constant_power() -> None:
    """Check hydro governor curve mapping, initialization, and composition.

    :return: None.
    """
    cgmes_object: GovHydroIEEE2 = GovHydroIEEE2(rdfid='_gov_hydro_ieee2_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.tg = 0.5
    cgmes_object.tp = 0.03
    cgmes_object.uo = 0.1
    cgmes_object.uc = -0.1
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.rperm = 0.05
    cgmes_object.rtemp = 0.5
    cgmes_object.tr = 12.0
    cgmes_object.tw = 2.0
    cgmes_object.kturb = 1.0
    cgmes_object.aturb = -1.0
    cgmes_object.bturb = 0.5
    cgmes_object.gv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.pgv2 = 0.16
    cgmes_object.pgv3 = 0.34
    cgmes_object.pgv4 = 0.55
    cgmes_object.pgv5 = 0.79
    cgmes_object.pgv6 = 1.0

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_hydro_ieee2_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_ieee2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroIEEE2'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_ieee2_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_ieee2_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 2
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
    mapped_curve_field: bool = any(
        variable.name.startswith('GovHydroIEEE2.gv6_')
        and isinstance(value, Const)
        and value.value == 1.0
        for model_block in template.block.get_all_blocks()
        for variable, value in model_block.event_dict.items()
    )
    assert mapped_curve_field


@pytest.mark.parametrize("feedback_signal", (False, True))
@pytest.mark.parametrize("treg", (0.0, 0.02))
def test_gov_hydro_pid2_maps_and_composes_at_constant_power(
        feedback_signal: bool,
        treg: float,
) -> None:
    """Check canonical fields, selector mapping, bases, and PID2 equilibrium wiring.

    :param feedback_signal: Gate-feedback selector from the CGMES RDF record.
    :param treg: Droop measurement time, including its algebraic zero-time reduction.
    :return: None.
    """
    cgmes_object: GovHydroPID2 = GovHydroPID2(rdfid=f'_gov_hydro_pid2_{feedback_signal}')
    cgmes_object.mwbase = 100.0
    cgmes_object.treg = treg
    cgmes_object.rperm = 0.05
    cgmes_object.kp = 2.0
    cgmes_object.ki = 1.0
    cgmes_object.kd = 0.1
    cgmes_object.ta = 0.1
    cgmes_object.tb = 0.2
    cgmes_object.velmax = 0.2
    cgmes_object.velmin = -0.15
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.tw = 1.0
    cgmes_object.d = 0.5
    cgmes_object.g0 = 0.08
    cgmes_object.g1 = 0.4
    cgmes_object.p1 = 0.3
    cgmes_object.g2 = 0.7
    cgmes_object.p2 = 0.65
    cgmes_object.p3 = 1.0
    cgmes_object.atw = 1.0
    cgmes_object.feedbackSignal = feedback_signal

    mapped_parameters: GovHydroPID2Parameters = get_gov_hydro_pid2_parameters(cgmes_object)
    assert (
        mapped_parameters.mwbase,
        mapped_parameters.treg,
        mapped_parameters.rperm,
        mapped_parameters.kp,
        mapped_parameters.ki,
        mapped_parameters.kd,
        mapped_parameters.ta,
        mapped_parameters.tb,
        mapped_parameters.velmax,
        mapped_parameters.velmin,
        mapped_parameters.gmax,
        mapped_parameters.gmin,
        mapped_parameters.tw,
        mapped_parameters.d,
        mapped_parameters.g0,
        mapped_parameters.g1,
        mapped_parameters.p1,
        mapped_parameters.g2,
        mapped_parameters.p2,
        mapped_parameters.p3,
        mapped_parameters.atw,
        mapped_parameters.feedbackSignal,
    ) == (
        100.0,
        treg,
        0.05,
        2.0,
        1.0,
        0.1,
        0.1,
        0.2,
        0.2,
        -0.15,
        1.0,
        0.0,
        1.0,
        0.5,
        0.08,
        0.4,
        0.3,
        0.7,
        0.65,
        1.0,
        1.0,
        feedback_signal,
    )

    machine: SynchronousMachine = SynchronousMachine(rdfid='_hydro_pid2_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_pid2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroPID2'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_pid2_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_pid2_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 4
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
    mapped_selector: bool = any(
        variable.name.startswith('RPERM_')
        and isinstance(value, Const)
        and value.value == 0.05
        for model_block in template.block.get_all_blocks()
        for variable, value in model_block.event_dict.items()
    )
    assert mapped_selector


@pytest.mark.parametrize("input_signal", (False, True))
@pytest.mark.parametrize("td_tf", ((0.0, 0.0), (0.0, 0.1), (0.1, 0.1)))
def test_gov_hydro_pid_maps_and_composes_at_constant_power(
        input_signal: bool,
        td_tf: tuple[float, float],
) -> None:
    """Check canonical GovHydroPID fields, feedback selector, and equilibrium wiring.

    :param input_signal: Selects electrical-power or gate-position feedback.
    :param td_tf: Speed-detector and derivative-filter times, including zero branches.
    :return: None.
    """
    cgmes_object: GovHydroPID = GovHydroPID(rdfid=f'_gov_hydro_pid_{input_signal}_{td_tf[1]}')
    cgmes_object.mwbase = 100.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.r = 0.05
    cgmes_object.td = td_tf[0]
    cgmes_object.tf = td_tf[1]
    cgmes_object.tp = 0.35
    cgmes_object.velop = 0.09
    cgmes_object.velcl = -0.14
    cgmes_object.kd = 1.11
    cgmes_object.kp = 0.1
    cgmes_object.ki = 0.36
    cgmes_object.kg = 2.5
    cgmes_object.tturb = 0.8
    cgmes_object.aturb = -1.0
    cgmes_object.bturb = 0.5
    cgmes_object.tt = 0.02
    cgmes_object.db1 = 0.0
    cgmes_object.inputSignal = input_signal
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0
    cgmes_object.gv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.pgv2 = 0.15
    cgmes_object.pgv3 = 0.33
    cgmes_object.pgv4 = 0.55
    cgmes_object.pgv5 = 0.78
    cgmes_object.pgv6 = 1.0

    mapped_parameters: GovHydroPIDParameters = get_gov_hydro_pid_parameters(cgmes_object)
    assert (
        mapped_parameters.mwbase,
        mapped_parameters.pmax,
        mapped_parameters.pmin,
        mapped_parameters.r,
        mapped_parameters.td,
        mapped_parameters.tf,
        mapped_parameters.tp,
        mapped_parameters.velop,
        mapped_parameters.velcl,
        mapped_parameters.kd,
        mapped_parameters.kp,
        mapped_parameters.ki,
        mapped_parameters.kg,
        mapped_parameters.tturb,
        mapped_parameters.aturb,
        mapped_parameters.bturb,
        mapped_parameters.tt,
        mapped_parameters.db1,
        mapped_parameters.inputSignal,
        mapped_parameters.eps,
        mapped_parameters.db2,
        *mapped_parameters.gv_points,
        *mapped_parameters.pgv_points,
    ) == (
        100.0,
        1.0,
        0.0,
        0.05,
        td_tf[0],
        td_tf[1],
        0.35,
        0.09,
        -0.14,
        1.11,
        0.1,
        0.36,
        2.5,
        0.8,
        -1.0,
        0.5,
        0.02,
        0.0,
        input_signal,
        0.0,
        0.0,
        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0,
        0.0,
        0.15,
        0.33,
        0.55,
        0.78,
        1.0,
    )

    machine: SynchronousMachine = SynchronousMachine(rdfid='_hydro_pid_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_pid_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroPID'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_pid_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_pid_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 4
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize("treg", (0.0, 0.02))
@pytest.mark.parametrize("ta_tb", ((0.0, 0.0), (0.1, 0.0), (0.1, 0.2)))
def test_gov_hydro_wpid_maps_and_composes_at_constant_power(
        treg: float,
        ta_tb: tuple[float, float],
) -> None:
    """Check canonical WPID mapping and machine-composed equilibrium.

    :param treg: Electrical-power measurement time, including its zero-time branch.
    :param ta_tb: Controller and gate-servo filter times.
    :return: None.
    """
    cgmes_object: GovHydroWPID = GovHydroWPID(rdfid=f'_gov_hydro_wpid_{treg}_{ta_tb}')
    cgmes_object.mwbase = 100.0
    cgmes_object.treg = treg
    cgmes_object.reg = 0.05
    cgmes_object.kp = 0.1
    cgmes_object.ki = 0.36
    cgmes_object.kd = 1.11
    cgmes_object.ta = ta_tb[0]
    cgmes_object.tb = ta_tb[1]
    cgmes_object.velmax = 0.2
    cgmes_object.velmin = -0.15
    cgmes_object.gatmax = 1.0
    cgmes_object.gatmin = 0.0
    cgmes_object.tw = 1.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.d = 0.5
    cgmes_object.gv1 = 0.3
    cgmes_object.pgv1 = 0.3
    cgmes_object.gv2 = 0.7
    cgmes_object.pgv2 = 0.65
    cgmes_object.gv3 = 1.0
    cgmes_object.pgv3 = 1.0
    assert len(GovHydroWPID.LOCAL_CGMES_PROPERTIES) == 22
    mapped_parameters: GovHydroWPIDParameters = get_gov_hydro_wpid_parameters(cgmes_object)
    assert mapped_parameters.mwbase == 100.0
    assert mapped_parameters.treg == treg
    assert mapped_parameters.ta == ta_tb[0]
    assert mapped_parameters.tb == ta_tb[1]
    assert mapped_parameters.pgv3 == 1.0

    machine: SynchronousMachine = SynchronousMachine(rdfid='_hydro_wpid_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_wpid_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroWPID'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)

    veragrid_model: MultiCircuit = MultiCircuit(fbase=50.0)
    bus: Bus = Bus(name='hydro_wpid_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_wpid_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )

    template: RmsModelTemplate = generator.rms_template
    assert len(template.block.get_all_blocks()) >= 4
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_hydro_r_fourth_order_lead_lag_composes_at_constant_power() -> None:
    """Check GovHydroR field mapping, device composition, and zero-time equilibrium.

    :return: None.
    """
    cgmes_object: GovHydroR = GovHydroR(rdfid='_gov_hydro_r_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.r = 0.05
    cgmes_object.td = 0.0
    cgmes_object.t1 = 0.0
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.0
    cgmes_object.t4 = 0.0
    cgmes_object.t5 = 0.0
    cgmes_object.t6 = 0.0
    cgmes_object.t7 = 0.0
    cgmes_object.t8 = 0.0
    cgmes_object.tp = 0.0
    cgmes_object.velop = 0.2
    cgmes_object.velcl = -0.2
    cgmes_object.ki = 0.0
    cgmes_object.kg = 1.0
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.tt = 0.0
    cgmes_object.inputSignal = True
    cgmes_object.db1 = 0.0
    cgmes_object.eps = 0.0
    cgmes_object.db2 = 0.0
    cgmes_object.tw = 0.0
    cgmes_object.at = 1.0
    cgmes_object.dturb = 0.0
    cgmes_object.qnl = 0.0
    cgmes_object.h0 = 1.0
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.2
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.4
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.6
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 0.8
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.0
    mapped_parameters: GovHydroRParameters = get_gov_hydro_r_parameters(cgmes_object)
    assert mapped_parameters.inputSignal is True
    assert mapped_parameters.gv_points == (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    assert len(GovHydroR.LOCAL_CGMES_PROPERTIES) == 42

    machine: SynchronousMachine = SynchronousMachine(rdfid='_hydro_r_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_r_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroR'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_r_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_r_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )
    assert_zero_initial_residuals(
        generator.rms_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    'feedback_signal,tpe,tp,tdv,tw',
    (
        (False, 0.1, 0.1, 0.1, 1.0),
        (True, 0.1, 0.1, 0.1, 1.0),
        (False, 0.0, 0.0, 0.0, 0.0),
        (True, 0.0, 0.0, 0.0, 0.0),
    ),
)
def test_gov_hydro_weh_maps_curves_and_composes_at_constant_power(
        feedback_signal: bool,
        tpe: float,
        tp: float,
        tdv: float,
        tw: float,
) -> None:
    """Check GovHydroWEH RDF mapping, both feedback paths, and zero-time limits.

    :param feedback_signal: Select the PID-output feedback alternative.
    :param tpe: Electrical-power transducer time.
    :param tp: Pilot-valve time.
    :param tdv: Distribution-valve time.
    :param tw: Water-column time.
    :return: None.
    """
    cgmes_object: GovHydroWEH = GovHydroWEH(rdfid='_gov_hydro_weh_check')
    cgmes_object.mwbase = 100.0
    cgmes_object.rpg = 0.05
    cgmes_object.rpp = 0.05
    cgmes_object.tpe = tpe
    cgmes_object.kp = 2.0
    cgmes_object.ki = 5.0
    cgmes_object.kd = 0.5
    cgmes_object.td = 0.05
    cgmes_object.tp = tp
    cgmes_object.tdv = tdv
    cgmes_object.tg = 0.5
    cgmes_object.gtmxop = 0.2
    cgmes_object.gtmxcl = -0.2
    cgmes_object.gmax = 1.0
    cgmes_object.gmin = 0.0
    cgmes_object.dturb = 0.1
    cgmes_object.tw = tw
    cgmes_object.db = 0.0
    cgmes_object.dpv = 0.0
    cgmes_object.dicn = 0.0
    cgmes_object.feedbackSignal = feedback_signal
    cgmes_object.gv1 = 0.0
    cgmes_object.gv2 = 0.25
    cgmes_object.gv3 = 0.5
    cgmes_object.gv4 = 0.75
    cgmes_object.gv5 = 1.0
    cgmes_object.fl1 = 0.0
    cgmes_object.fl2 = 0.25
    cgmes_object.fl3 = 0.5
    cgmes_object.fl4 = 0.75
    cgmes_object.fl5 = 1.0
    cgmes_object.fp1 = 0.0
    cgmes_object.fp2 = 0.1
    cgmes_object.fp3 = 0.2
    cgmes_object.fp4 = 0.3
    cgmes_object.fp5 = 0.4
    cgmes_object.fp6 = 0.5
    cgmes_object.fp7 = 0.6
    cgmes_object.fp8 = 0.7
    cgmes_object.fp9 = 0.8
    cgmes_object.fp10 = 1.0
    cgmes_object.pmss1 = 0.0
    cgmes_object.pmss2 = 0.1
    cgmes_object.pmss3 = 0.2
    cgmes_object.pmss4 = 0.3
    cgmes_object.pmss5 = 0.4
    cgmes_object.pmss6 = 0.5
    cgmes_object.pmss7 = 0.6
    cgmes_object.pmss8 = 0.7
    cgmes_object.pmss9 = 0.8
    cgmes_object.pmss10 = 1.0
    mapped_parameters: GovHydroWEHParameters = get_gov_hydro_weh_parameters(cgmes_object)
    assert mapped_parameters.feedbackSignal is feedback_signal
    assert (
        mapped_parameters.rpg, mapped_parameters.rpp, mapped_parameters.tpe,
        mapped_parameters.kp, mapped_parameters.ki, mapped_parameters.kd,
        mapped_parameters.td, mapped_parameters.tp, mapped_parameters.tdv,
        mapped_parameters.tg, mapped_parameters.gtmxop, mapped_parameters.gtmxcl,
        mapped_parameters.gmax, mapped_parameters.gmin, mapped_parameters.dturb,
        mapped_parameters.tw, mapped_parameters.db, mapped_parameters.dpv,
        mapped_parameters.dicn,
    ) == (
        cgmes_object.rpg, cgmes_object.rpp, cgmes_object.tpe, cgmes_object.kp,
        cgmes_object.ki, cgmes_object.kd, cgmes_object.td, cgmes_object.tp,
        cgmes_object.tdv, cgmes_object.tg, cgmes_object.gtmxop, cgmes_object.gtmxcl,
        cgmes_object.gmax, cgmes_object.gmin, cgmes_object.dturb, cgmes_object.tw,
        cgmes_object.db, cgmes_object.dpv, cgmes_object.dicn,
    )
    assert mapped_parameters.gate_points == (0.0, 0.25, 0.5, 0.75, 1.0)
    assert mapped_parameters.turbine_flow_points == (
        0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0,
    )
    assert len(GovHydroWEH.LOCAL_CGMES_PROPERTIES) == 51

    machine: SynchronousMachine = SynchronousMachine(rdfid='_hydro_weh_machine')
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_hydro_weh_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovHydroWEH'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='hydro_weh_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='hydro_weh_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )
    assert_zero_initial_residuals(
        generator.rms_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    'peflag,t1,t4,t5,t6',
    (
        (False, 0.1, 0.15, 12.0, 0.75),
        (True, 0.1, 0.15, 12.0, 0.75),
        (False, 0.0, 0.0, 0.0, 0.0),
        (True, 0.0, 0.0, 0.0, 0.0),
    ),
)
def test_gov_steam_bb_maps_and_composes_at_constant_power(
        peflag: bool,
        t1: float,
        t4: float,
        t5: float,
        t6: float,
) -> None:
    """Check GovSteamBB mappings, feedback selection, turbine weights, and zero times.

    :param peflag: Select electrical-power input when true.
    :param t1: Electrical-power transducer time.
    :param t4: Steam-output time.
    :param t5: Intermediate-pressure turbine time.
    :param t6: Low-pressure turbine time.
    :return: None.
    """
    cgmes_object: GovSteamBB = GovSteamBB(rdfid='_gov_steam_bb_check')
    cgmes_object.fcut = 0.002
    cgmes_object.ks = 21.0
    cgmes_object.kls = 0.1
    cgmes_object.kg = 1.0
    cgmes_object.t1 = t1
    cgmes_object.kp = 1.0
    cgmes_object.tn = 1.0
    cgmes_object.kd = 1.0
    cgmes_object.td = 0.1
    cgmes_object.pmax = 1.0
    cgmes_object.pmin = 0.0
    cgmes_object.t4 = t4
    cgmes_object.k2 = 0.75
    cgmes_object.t5 = t5
    cgmes_object.k3 = 0.5
    cgmes_object.t6 = t6
    cgmes_object.peflag = peflag
    mapped_parameters: GovSteamBBParameters = get_gov_steam_b_b_parameters(cgmes_object)
    assert mapped_parameters.peflag is peflag
    assert (
        mapped_parameters.fcut, mapped_parameters.ks, mapped_parameters.kls,
        mapped_parameters.kg, mapped_parameters.t1, mapped_parameters.kp,
        mapped_parameters.tn, mapped_parameters.kd, mapped_parameters.td,
        mapped_parameters.pmax, mapped_parameters.pmin, mapped_parameters.t4,
        mapped_parameters.k2, mapped_parameters.t5, mapped_parameters.k3,
        mapped_parameters.t6,
    ) == (
        cgmes_object.fcut, cgmes_object.ks, cgmes_object.kls, cgmes_object.kg,
        cgmes_object.t1, cgmes_object.kp, cgmes_object.tn, cgmes_object.kd,
        cgmes_object.td, cgmes_object.pmax, cgmes_object.pmin, cgmes_object.t4,
        cgmes_object.k2, cgmes_object.t5, cgmes_object.k3, cgmes_object.t6,
    )
    assert len(GovSteamBB.LOCAL_CGMES_PROPERTIES) == 17

    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_steam_bb_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_steam_bb_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(cgmes_object)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    cgmes_model.dynamics_assets.lists['GovSteamBB'].append(cgmes_object)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='steam_bb_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='steam_bb_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=DataLogger(),
    )
    assert_zero_initial_residuals(
        generator.rms_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    'feedback',
    (
        DroopSignalFeedbackKind.electricalPower,
        DroopSignalFeedbackKind.none,
        DroopSignalFeedbackKind.fuelValveStroke,
        DroopSignalFeedbackKind.governorOutput,
    ),
)
def test_gov_ct1_maps_and_composes_supported_feedback_paths(
        feedback: DroopSignalFeedbackKind,
) -> None:
    """Map GovCT1 and verify its supported GGOV1 equilibrium with the machine.

    :param feedback: Canonical RDF droop-feedback enumeration.
    :return: None.
    """
    governor: GovCT1 = GovCT1(rdfid='_gov_ct1_check')
    governor.mwbase = 0.0
    governor.r = 0.05
    governor.rselect = feedback
    governor.tpelec = 0.1
    governor.maxerr = 0.2
    governor.minerr = -0.2
    governor.kpgov = 10.0
    governor.kigov = 2.0
    governor.kdgov = 0.0
    governor.tdgov = 1.0
    governor.vmax = 1.0
    governor.vmin = 0.0
    governor.tact = 0.5
    governor.kturb = 1.5
    governor.wfnl = 0.2
    governor.tb = 0.5
    governor.tc = 0.0
    governor.wfspd = True
    governor.teng = 0.0
    governor.tfload = 3.0
    governor.kpload = 2.0
    governor.kiload = 0.67
    governor.ldref = 1.0
    governor.dm = 0.0
    governor.ropen = 0.1
    governor.rclose = -0.1
    governor.kimw = 0.01
    governor.aset = 0.01
    governor.ka = 10.0
    governor.ta = 0.1
    governor.db = 0.0
    governor.tsa = 0.0
    governor.tsb = 0.0
    governor.rup = 99.0
    governor.rdown = -99.0
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_ct1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_ct1_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    mapped: GovCT1Parameters = get_gov_ct1_parameters(governor)
    assert mapped.mwbase == 100.0
    assert mapped.rselect is feedback
    assert mapped.ka == 10.0 and mapped.teng == 0.0
    assert len(GovCT1.LOCAL_CGMES_PROPERTIES) == 35

    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovCT1'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name='ct1_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='ct1_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )
    assert generator.rms_template is not None, logger.get_message() + str(logger.entries[0])
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f'OmegaDerivativePu_GovCT1_{governor.uuid}',
    ) is None
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f'FsrAccelerationPu_GovCT1_{governor.uuid}',
    ) is not None
    assert_zero_initial_residuals(
        generator.rms_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_gov_ct1_builds_acceleration_and_transport_paths() -> None:
    """Check sourced acceleration limiting and fuel transport stages.

    :return: None.
    """
    acceleration_template: RmsModelTemplate = build_gov_c_t1_template(
        VarFactory(),
        parameters=GovCT1Parameters(ka=1.0, ta=0.1),
    )
    assert find_block_variable_by_name(
        acceleration_template.block,
        f'OmegaDerivativePu_{acceleration_template.name}',
    ) is not None
    assert find_block_variable_by_name(
        acceleration_template.block,
        f'FsrAccelerationPu_{acceleration_template.name}',
    ) is not None
    with pytest.raises(ValueError, match='positive ta'):
        build_gov_c_t1_template(
            VarFactory(),
            parameters=GovCT1Parameters(ka=1.0, ta=0.0),
        )
    transport_template: RmsModelTemplate = build_gov_c_t1_template(
        VarFactory(),
        parameters=GovCT1Parameters(teng=0.1),
    )
    assert any(
        procedural_logic.name.startswith('GovCT1.FuelTransportDelay_')
        for procedural_logic in transport_template.block.procedural_logic
    )


def test_gov_ct2_frequency_limit_curve_and_composed_initial_residuals() -> None:
    """Check the GGOV2 limit curve and its imported machine operating point.

    :return: None.
    """
    frequency_points: tuple[float, ...] = (59.0, 58.0, 57.0) + (0.0,) * 7
    power_points: tuple[float, ...] = (0.9, 0.8, 0.7) + (0.0,) * 7
    assert get_gov_ct2_frequency_power_limit(
        60.0, frequency_points, power_points,
    ) is None
    assert isclose(get_gov_ct2_frequency_power_limit(
        58.5, frequency_points, power_points,
    ), 0.85)
    assert isclose(get_gov_ct2_frequency_power_limit(
        56.0, frequency_points, power_points,
    ), 0.7)

    governor: GovCT2 = GovCT2(rdfid='_gov_ct2_check')
    governor.mwbase = 100.0
    governor.r = 0.05
    governor.rselect = DroopSignalFeedbackKind.electricalPower
    governor.tpelec = 0.1
    governor.maxerr = 0.2
    governor.minerr = -0.2
    governor.kpgov = 10.0
    governor.kigov = 2.0
    governor.kdgov = 0.0
    governor.tdgov = 1.0
    governor.vmax = 1.0
    governor.vmin = 0.0
    governor.tact = 0.5
    governor.kturb = 1.5
    governor.wfnl = 0.2
    governor.tb = 0.5
    governor.tc = 0.0
    governor.wfspd = False
    governor.teng = 0.0
    governor.tfload = 3.0
    governor.kpload = 2.0
    governor.kiload = 0.67
    governor.ldref = 1.0
    governor.dm = 0.0
    governor.ropen = 0.1
    governor.rclose = -0.1
    governor.kimw = 0.01
    governor.aset = 10.0
    governor.ka = 10.0
    governor.ta = 0.1
    governor.db = 0.0
    governor.tsa = 0.0
    governor.tsb = 0.0
    governor.rup = 99.0
    governor.rdown = -99.0
    governor.prate = 0.017
    governor.flim1 = frequency_points[0]
    governor.plim1 = power_points[0]
    governor.flim2 = frequency_points[1]
    governor.plim2 = power_points[1]
    governor.flim3 = frequency_points[2]
    governor.plim3 = power_points[2]
    governor.flim4 = 0.0
    governor.plim4 = 0.0
    governor.flim5 = 0.0
    governor.plim5 = 0.0
    governor.flim6 = 0.0
    governor.plim6 = 0.0
    governor.flim7 = 0.0
    governor.plim7 = 0.0
    governor.flim8 = 0.0
    governor.plim8 = 0.0
    governor.flim9 = 0.0
    governor.plim9 = 0.0
    governor.flim10 = 0.0
    governor.plim10 = 0.0
    assert len(GovCT2.LOCAL_CGMES_PROPERTIES) == 56
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_ct2_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid='_ct2_machine_dynamics'
    )
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    mapped: GovCT2Parameters = get_gov_ct2_parameters(governor, 60.0)
    assert mapped.mwbase == 100.0
    assert mapped.flim_points == frequency_points
    assert mapped.plim_points == power_points
    cgmes_model: CgmesCircuit = CgmesCircuit()
    cgmes_model.dynamics_assets.lists['GovCT2'].append(governor)
    cgmes_model.dynamics_assets.lists['SynchronousMachineSimplified'].append(machine_dynamics)
    veragrid_model: MultiCircuit = MultiCircuit()
    veragrid_model.Sbase = 100.0
    bus: Bus = Bus(name='ct2_bus')
    generator: Generator = Generator(idtag=machine.uuid, name='ct2_machine', P=50.0)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    logger: DataLogger = DataLogger()
    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )
    assert generator.rms_template is not None, logger.get_message() + str(logger.entries[0])
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f'OmegaDerivativePu_GovCT2_{governor.uuid}',
    ) is None
    assert find_block_variable_by_name(
        generator.rms_template.block,
        f'FsrAccelerationPu_GovCT2_{governor.uuid}',
    ) is not None
    assert_zero_initial_residuals(
        generator.rms_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )
    acceleration_template: RmsModelTemplate = build_gov_c_t2_template(
        VarFactory(),
        parameters=GovCT2Parameters(ka=1.0, ta=0.1),
    )
    assert find_block_variable_by_name(
        acceleration_template.block,
        f'OmegaDerivativePu_{acceleration_template.name}',
    ) is not None
    assert find_block_variable_by_name(
        acceleration_template.block,
        f'FsrAccelerationPu_{acceleration_template.name}',
    ) is not None
    with pytest.raises(ValueError, match='positive ta'):
        build_gov_c_t2_template(
            VarFactory(),
            parameters=GovCT2Parameters(ka=1.0, ta=0.0),
        )
    delayed_template: RmsModelTemplate = build_gov_c_t2_template(
        VarFactory(),
        parameters=GovCT2Parameters(teng=0.1),
    )
    assert any(
        isinstance(procedural_logic, TimeDelayLogic)
        and procedural_logic.name.startswith('GovCT2.FuelTransportDelay_')
        for runtime_block in delayed_template.block.get_all_blocks()
        for procedural_logic in runtime_block.procedural_logic
    )


def test_gov_steam0_zero_time_stages_and_imported_reference() -> None:
    """Import GovSteam0 settings and initialize its reference on MWBASE.

    :return: None.
    """
    cgmes_object: GovSteam0 = GovSteam0(rdfid="_gov_steam0_check")
    cgmes_object.mwbase = 125.0
    cgmes_object.r = 0.05
    cgmes_object.t1 = 0.0
    cgmes_object.vmax = 1.1
    cgmes_object.vmin = 0.2
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.0
    cgmes_object.dt = 0.04
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit()
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name="steam_bus")
    machine: SynchronousMachine = SynchronousMachine(rdfid="_steam_machine")
    machine_dynamics: SynchronousMachineDynamics = SynchronousMachineDynamics(
        rdfid="_steam_machine_dynamics"
    )
    generator: Generator = Generator(idtag=machine.uuid, name="steam_machine", P=50.0)
    cgmes_object.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    cgmes_model.dynamics_assets.lists["GovSteam0"].append(cgmes_object)
    cgmes_model.dynamics_assets.lists["SynchronousMachineDynamics"].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    imported_template: RmsModelTemplate = veragrid_model.rms_models[0]
    runtime_block: Block = imported_template.block.children[0]
    reference_port: Var | None = None
    for runtime_input in runtime_block.in_vars:
        if runtime_input.name.startswith("PRefPu_"):
            reference_port = runtime_input
        else:
            pass
    runtime_events: dict[str, object] = dict(
        (variable.name, value) for variable, value in runtime_block.event_dict.items()
    )
    source_events: dict[str, object] = dict(
        (variable.name, value) for variable, value in imported_template.block.event_dict.items()
    )

    assert len(veragrid_model.rms_models) == 1
    assert imported_template.device is generator
    assert len(runtime_block.state_vars) == 0
    assert reference_port is not None
    assert runtime_block.init_eqs[reference_port].value == 0.4
    assert runtime_events["R_" + imported_template.name].value == 0.05
    assert runtime_events["T1_" + imported_template.name].value == 0.0
    assert runtime_events["Vmax_" + imported_template.name].value == 1.1
    assert runtime_events["Vmin_" + imported_template.name].value == 0.2
    assert runtime_events["T2_" + imported_template.name].value == 0.0
    assert runtime_events["T3_" + imported_template.name].value == 0.0
    assert runtime_events["Dt_" + imported_template.name].value == 0.04
    assert source_events["GovSteam0.mwbase_" + imported_template.name].value == 125.0

    positive_template: RmsModelTemplate = build_gov_steam0_template(
        vfactory=VarFactory(),
        name="GovSteam0_positive_time_check",
        parameters=GovSteam0Parameters(t1=0.1, t2=0.0, t3=10.0),
    )

    assert len(positive_template.block.children[0].state_vars) == 2

    with pytest.raises(ValueError, match="T3=0 requires T2=0"):
        build_gov_steam0_template(
            vfactory=VarFactory(),
            name="GovSteam0_improper_zero_time_check",
            parameters=GovSteam0Parameters(t2=0.1, t3=0.0),
        )


def test_gov_steam1_rdf_curve_events_drive_equations_and_zero_time_limits() -> None:
    """Map the RDF valve curve into equations and remove zero-time lag states.

    :return: None.
    """
    cgmes_object: GovSteam1 = GovSteam1(rdfid="_gov_steam1_curve_check")
    cgmes_object.t1 = 0.0
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.2
    cgmes_object.t4 = 0.0
    cgmes_object.t5 = 0.0
    cgmes_object.t6 = 0.0
    cgmes_object.t7 = 0.0
    cgmes_object.valve = True
    cgmes_object.gv1 = 0.0
    cgmes_object.pgv1 = 0.0
    cgmes_object.gv2 = 0.2
    cgmes_object.pgv2 = 0.25
    cgmes_object.gv3 = 0.4
    cgmes_object.pgv3 = 0.5
    cgmes_object.gv4 = 0.6
    cgmes_object.pgv4 = 0.75
    cgmes_object.gv5 = 0.8
    cgmes_object.pgv5 = 1.0
    cgmes_object.gv6 = 1.0
    cgmes_object.pgv6 = 1.25
    template_name: str = "GovSteam1_curve_check"
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_gov_steam1_template(
        vfactory=variable_factory,
        name=template_name,
        settings=GovSteam1Settings(
            times=(0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0),
            valve=True,
            gv_points=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            pgv_points=(0.0, 0.25, 0.5, 0.75, 1.0, 1.25),
        ),
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    template.block.unify_blocks()
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )
    equation_variables: set[str] = set(
        variable.name
        for equation in template.block.algebraic_eqs
        for variable in equation.get_vars()
    )

    assert len(template.block.state_vars) == 1
    assert len(template.block.out_vars) == 3
    assert event_values[f"GovSteam1.pgv4_{template_name}"].value == 0.75
    assert "GovSteam1.gv4_" + template_name in equation_variables
    assert "GovSteam1.pgv4_" + template_name in equation_variables
    assert "gov.omegaPu_" + template_name in {
        variable.name for variable in template.block.in_vars
    }


def test_gov_steam1_rejects_improper_zero_time_transfer() -> None:
    """Reject a nonzero transfer numerator time when T1 equals zero.

    :return: None.
    """
    with pytest.raises(ValueError, match="T1=0 requires T2=0"):
        build_gov_steam1_template(
            vfactory=VarFactory(),
            name="GovSteam1_improper_zero_time_check",
            settings=GovSteam1Settings(
                times=(0.0, 0.1, 0.2, 0.3, 5.0, 0.5, 0.0),
                valve=True,
                gv_points=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
                pgv_points=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            ),
        )


def test_gov_steam1_import_attaches_and_connects_generator_ports() -> None:
    """Attach the imported GovSteam1 model and connect its machine signals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid="_steam1_machine")
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_steam1_machine_dynamics"
    )
    governor: GovSteam1 = GovSteam1(rdfid="_steam1_governor")
    governor.mwbase = 100.0
    governor.k = 25.0
    governor.t3 = 0.1
    governor.gv1 = 0.0
    governor.pgv1 = 0.0
    governor.gv2 = 0.2
    governor.pgv2 = 0.2
    governor.gv3 = 0.4
    governor.pgv3 = 0.4
    governor.gv4 = 0.6
    governor.pgv4 = 0.6
    governor.gv5 = 0.8
    governor.pgv5 = 0.8
    governor.gv6 = 1.0
    governor.pgv6 = 1.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(idtag=machine.uuid, name="steam1_generator", P=80.0)
    veragrid_model.add_generator(bus=Bus(name="steam1_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["GovSteam1"].append(governor)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None
    assert composite.device is generator
    assert composite in veragrid_model.rms_models
    runtime_blocks: list[Block] = composite.block.get_all_blocks()
    governor_speed: Var | None = None
    machine_speed: Var | None = None
    governor_power: Var | None = None
    imported_fields: dict[str, object] = dict()
    for runtime_block in runtime_blocks:
        for input_variable in runtime_block.in_vars:
            if input_variable.name == "omega":
                governor_speed = input_variable
            else:
                pass
        for output_variable in runtime_block.out_vars:
            if output_variable.name == "omega":
                machine_speed = output_variable
            elif output_variable.name.startswith("PmPu_"):
                governor_power = output_variable
            else:
                pass
        for event_variable, event_value in runtime_block.event_dict.items():
            if event_variable.name.startswith("GovSteam1.pgv4_"):
                imported_fields["pgv4"] = event_value
            else:
                pass

    assert governor_speed is not None
    assert machine_speed is not None
    assert governor_speed.uid == machine_speed.uid
    assert governor_power is not None
    assert imported_fields["pgv4"].value == 0.6


def test_gov_steam_ieee1_maps_to_rate_limited_rms_equations() -> None:
    """Use the matching IEEE G1 graph and map the canonical RDF coefficients.

    :return: None.
    """
    cgmes_object: GovSteamIEEE1 = GovSteamIEEE1(rdfid="_gov_steam_ieee1_check")
    cgmes_object.k = 31.0
    cgmes_object.t1 = 0.0
    cgmes_object.t2 = 0.0
    cgmes_object.t3 = 0.25
    cgmes_object.uo = 0.12
    cgmes_object.uc = -0.14
    cgmes_object.pmax = 1.1
    cgmes_object.pmin = 0.1
    cgmes_object.t4 = 0.2
    cgmes_object.k1 = 0.3
    cgmes_object.k2 = 0.0
    cgmes_object.k3 = 0.3
    cgmes_object.k4 = 0.0
    cgmes_object.k5 = 0.2
    cgmes_object.k6 = 0.0
    cgmes_object.k7 = 0.2
    cgmes_object.k8 = 0.0
    template_name: str = "GovSteamIEEE1_check"
    variable_factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_gov_steam_i_e_e_e1_template(
        vfactory=variable_factory,
        name=template_name,
        parameters=get_gov_steam_ieee1_parameters(cgmes_object),
    )
    copy_cgmes_parameters(
        cgmes_object=cgmes_object,
        template=template,
        variable_factory=variable_factory,
    )
    event_values: dict[str, object] = dict(
        (variable.name, value) for variable, value in template.block.event_dict.items()
    )

    assert len(template.block.state_vars) == 5
    assert len(template.block.algebraic_eqs) > 0
    assert event_values[f"K_{template_name}"].value == 31.0
    assert event_values[f"T3_{template_name}"].value == 0.25
    assert event_values[f"K1_{template_name}"].value == 0.3
    assert len(template.block.out_vars) == 3


def test_gov_steam2_equations_map_and_compose_with_simplified_machine() -> None:
    """Map GovSteam2 controls and connect its speed and power to the generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid="b0000000000000000000000000000000"
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_steam2_machine_dynamics"
    )
    governor: GovSteam2 = GovSteam2(rdfid="_steam2_governor")
    governor.k = 20.0
    governor.dbf = 0.0
    governor.t1 = 0.45
    governor.t2 = 0.1
    governor.pmax = 1.0
    governor.pmin = 0.0
    governor.mxef = 1.0
    governor.mnef = -1.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(idtag=machine.uuid, name="steam2_generator", P=80.0)
    veragrid_model.add_generator(bus=Bus(name="steam2_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["GovSteam2"].append(governor)

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None, logger.get_message() + " " + repr(logger.entries)
    assert composite.device is generator
    assert composite in veragrid_model.rms_models
    equation_variables: set[str] = set()
    event_values: dict[str, object] = dict()
    governor_input_found: bool = False
    for runtime_block in composite.block.get_all_blocks():
        for input_variable in runtime_block.in_vars:
            if input_variable.name.startswith("gov.omegaPu_"):
                governor_input_found = True
            else:
                pass
        for event_variable, event_value in runtime_block.event_dict.items():
            if event_variable.name.startswith(("K_", "T1_", "T2_", "PMaxPu_")):
                event_values[event_variable.name.split("_")[0]] = event_value
            else:
                pass
        for equation in runtime_block.state_eqs:
            equation_variables.update(variable.name for variable in equation.get_vars())
        for equation in runtime_block.algebraic_eqs:
            equation_variables.update(variable.name for variable in equation.get_vars())

    assert not governor_input_found
    assert "omega" in equation_variables
    assert "Tm" not in equation_variables
    assert "Pg" in equation_variables
    assert event_values["K"].value == 20.0
    assert event_values["T1"].value == 0.45
    assert event_values["T2"].value == 0.1
    assert event_values["PMaxPu"].value == 1.0
    assert_zero_initial_residuals(
        template=composite,
        power_flow_values={
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.4,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(("tf_value", "tw_value"), ((0.1, 0.02), (0.0, 0.0)))
@pytest.mark.parametrize("tdp_value", (0.1, 0.0))
@pytest.mark.parametrize("tfp_value", (0.1, 0.0))
def test_gov_steam_eu_maps_parameters_and_composes_machine_signals(
        tf_value: float,
        tw_value: float,
        tdp_value: float,
        tfp_value: float,
) -> None:
    """Map the IEC GovSteamEU fields and bind all machine-owned runtime inputs.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid="a0000000000000000000000000000000"
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_steam_eu_machine_dynamics"
    )
    governor: GovSteamEU = GovSteamEU(rdfid="_steam_eu_governor")
    governor.mwbase = 100.0
    governor.tp = 0.07
    governor.ke = 0.65
    governor.tip = 2.0
    governor.tdp = tdp_value
    governor.tfp = tfp_value
    governor.tf = tf_value
    governor.kfcor = 20.0
    governor.db1 = 0.0
    governor.wfmax = 0.05
    governor.wfmin = -0.05
    governor.pmax = 1.0
    governor.ten = 0.1
    governor.tw = tw_value
    governor.komegacor = 20.0
    governor.db2 = 0.0004
    governor.wwmax = 0.1
    governor.wwmin = -1.0
    governor.wmax1 = 1.025
    governor.wmax2 = 1.05
    governor.tvhp = 0.1
    governor.cho = 0.17
    governor.chc = -3.3
    governor.hhpmax = 1.0
    governor.tvip = 0.15
    governor.cio = 0.123
    governor.cic = -2.2
    governor.simx = 0.425
    governor.thp = 0.31
    governor.trh = 8.0
    governor.tlp = 0.45
    governor.prhmax = 1.4
    governor.khp = 0.277
    governor.klp = 0.723
    governor.tb = 100.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(idtag=machine.uuid, name="steam_eu_generator", P=80.0)
    veragrid_model.add_generator(bus=Bus(name="steam_eu_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["GovSteamEU"].append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics

    convert_cgmes_dynamics(
        cgmes_model=cgmes_model,
        veragrid_model=veragrid_model,
        logger=logger,
    )

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None, logger.get_message() + " " + repr(logger.entries)
    assert composite.device is generator
    assert composite in veragrid_model.rms_models
    runtime_blocks: list[Block] = composite.block.get_all_blocks()
    event_values: dict[str, object] = dict()
    initial_values: dict[str, float] = dict()
    equation_variables: set[str] = set()
    frequency_filter_state_found: bool = False
    speed_filter_state_found: bool = False
    derivative_filter_state_found: bool = False
    for runtime_block in runtime_blocks:
        for state_variable in runtime_block.state_vars:
            if state_variable.name.startswith("gov.firstOrdertfT.y_"):
                frequency_filter_state_found = True
            else:
                pass
            if state_variable.name.startswith("gov.firstOrdertOmega.y_"):
                speed_filter_state_found = True
            else:
                pass
            if state_variable.name.startswith("gov.derivativetDPctPc.x_"):
                derivative_filter_state_found = True
            else:
                pass
        for event_variable, event_value in runtime_block.event_dict.items():
            if event_variable.name.startswith(("gov.PBaseMw_", "gov.PGenBaseMw_", "gov.tF_", "gov.tOmega_", "gov.tDp_", "gov.tFp_", "gov.KE_")):
                event_values[event_variable.name.split("_")[0]] = event_value
            else:
                pass
        for input_variable, initial_value in runtime_block.init_eqs.items():
            if input_variable.name.startswith(("gov.PRefPu_", "gov.PGenPu_")):
                initial_values[input_variable.name.split("_")[0]] = initial_value.value
            else:
                pass
        for equation in runtime_block.algebraic_eqs:
            equation_variables.update(variable.name for variable in equation.get_vars())

    assert event_values["gov.PBaseMw"].value == 100.0
    assert event_values["gov.PGenBaseMw"].value == 100.0
    assert event_values["gov.tF"].value == tf_value
    assert event_values["gov.tOmega"].value == tw_value
    assert event_values["gov.tDp"].value == tdp_value
    assert event_values["gov.tFp"].value == tfp_value
    assert event_values["gov.KE"].value == 0.65
    assert initial_values["gov.PRefPu"] == 0.8
    assert "MachineElectricalPowerPu_" + composite.name in equation_variables
    assert "Pg" in equation_variables
    assert frequency_filter_state_found is (tf_value != 0.0)
    assert speed_filter_state_found is (tw_value != 0.0)
    assert derivative_filter_state_found is (tdp_value != 0.0 and tfp_value != 0.0)
    ideal_derivative_found: bool = False
    for runtime_block in runtime_blocks:
        for differential_variable in runtime_block.diff_vars:
            if differential_variable.name.startswith("d_gov.addPe.y_"):
                ideal_derivative_found = True
            else:
                pass
    assert ideal_derivative_found is (tdp_value != 0.0 and tfp_value == 0.0)

    initial_bindings: dict[int, float | complex] = dict()
    initial_equations: list[tuple[Var, Expr]] = list()
    power_flow_values: dict[VarPowerFlowReferenceType, float] = {
        VarPowerFlowReferenceType.Vm: 1.0,
        VarPowerFlowReferenceType.Va: 0.0,
        VarPowerFlowReferenceType.P: 0.4,
        VarPowerFlowReferenceType.Q: 0.0,
    }
    for runtime_block in runtime_blocks:
        for variable in runtime_block.algebraic_vars:
            if variable.name.startswith((
                    "GridFrequencyPu_",
                    "GridFrequencyReferencePu_",
                    "GovernorSpeedReferencePu_",
            )):
                initial_bindings[variable.uid] = 1.0
            else:
                pass
    for runtime_block in runtime_blocks:
        for variable, value in runtime_block.event_dict.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_bindings[variable.uid] = value.value
            elif isinstance(value, Expr) and not isinstance(value, Const):
                initial_equations.append((variable, value))
            else:
                pass
        for variable, value in runtime_block.parameters.items():
            if isinstance(value, Const) and isinstance(value.value, (int, float, complex)):
                initial_bindings[variable.uid] = value.value
            else:
                pass
        for reference, variable in runtime_block.external_mapping.items():
            reference_value: float | None = power_flow_values.get(reference, None)
            if reference_value is None:
                pass
            else:
                initial_bindings[variable.uid] = reference_value
        initial_equations.extend(runtime_block.init_eqs.items())
        initial_equations.extend(runtime_block.diff_init_eqs.items())
        for equation in runtime_block.algebraic_eqs:
            if (
                    isinstance(equation, BinOp)
                    and equation.op == "-"
                    and isinstance(equation.left, Var)
                    and equation.left in runtime_block.algebraic_vars
                    and equation.left not in runtime_block.init_eqs
            ):
                initial_equations.append((equation.left, equation.right))
            else:
                pass

    for variable, equation in initial_equations:
        initial_bindings.pop(variable.uid, None)
    pending_equations: list[tuple[Var, Expr]] = initial_equations
    while len(pending_equations) > 0:
        unresolved_equations: list[tuple[Var, Expr]] = list()
        progress: bool = False
        for variable, equation in pending_equations:
            dependencies: list[Var] = equation.get_vars()
            if all(dependency.uid in initial_bindings for dependency in dependencies):
                initial_bindings[variable.uid] = eval_uid(equation, initial_bindings)
                progress = True
            else:
                unresolved_equations.append((variable, equation))
        pending_equations = unresolved_equations
        if progress:
            pass
        else:
            for runtime_block in runtime_blocks:
                for derivative_variable, derivative_equation in zip(
                        runtime_block.diff_vars,
                        runtime_block.state_eqs,
                ):
                    dependencies = derivative_equation.get_vars()
                    if all(dependency.uid in initial_bindings for dependency in dependencies):
                        initial_bindings[derivative_variable.uid] = eval_uid(
                            derivative_equation,
                            initial_bindings,
                        )
                    else:
                        pass
            break

    assert not pending_equations
    for runtime_block in runtime_blocks:
        for equation in runtime_block.state_eqs:
            unresolved_variables: list[str] = list()
            for equation_variable in equation.get_vars():
                if equation_variable.uid not in initial_bindings:
                    unresolved_variables.append(equation_variable.name)
                else:
                    pass
            assert not unresolved_variables, (runtime_block.name, equation, unresolved_variables)
            assert isclose(abs(eval_uid(equation, initial_bindings)), 0.0, abs_tol=1e-8)
        for equation in runtime_block.algebraic_eqs:
            unresolved_variables: list[str] = list()
            for equation_variable in equation.get_vars():
                if equation_variable.uid not in initial_bindings:
                    unresolved_variables.append(equation_variable.name)
                else:
                    pass
            assert not unresolved_variables, unresolved_variables
            assert isclose(abs(eval_uid(equation, initial_bindings)), 0.0, abs_tol=1e-8)

def test_gov_steam_sgo_maps_all_parameters_and_composes_steady_state() -> None:
    """Map all SGO RDF parameters and initialize the composed machine graph.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=200.0)
    logger: DataLogger = DataLogger()
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(
        rdfid="_steam_sgo_machine"
    )
    machine.ratedS = 125.0
    machine.ratedPowerFactor = 0.8
    machine_dynamics: SynchronousMachineSimplified = SynchronousMachineSimplified(
        rdfid="_steam_sgo_machine_dynamics"
    )
    governor: GovSteamSGO = GovSteamSGO(rdfid="_steam_sgo_governor")
    governor.mwbase = 100.0
    governor.t1 = 0.2
    governor.t2 = 0.05
    governor.t3 = 0.3
    governor.t4 = 0.4
    governor.t5 = 1.0
    governor.t6 = 0.2
    governor.k1 = 0.05
    governor.k2 = 0.3
    governor.k3 = 0.3
    governor.pmax = 1.0
    governor.pmin = 0.0
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.TurbineGovernorDynamics.append(governor)
    governor.SynchronousMachineDynamics = machine_dynamics
    generator: Generator = Generator(
        idtag=machine.uuid,
        name="steam_sgo_generator",
        P=60.0,
    )
    veragrid_model.add_generator(bus=Bus(name="steam_sgo_bus"), api_obj=generator)
    cgmes_model.dynamics_assets.lists["SynchronousMachineSimplified"].append(machine_dynamics)
    cgmes_model.dynamics_assets.lists["GovSteamSGO"].append(governor)

    mapped_parameters = get_gov_steam_s_g_o_parameters(governor)
    assert mapped_parameters.mwbase == 100.0
    assert mapped_parameters.pmin == 0.0
    assert mapped_parameters.k3 == 0.3
    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite: RmsModelTemplate | None = generator.rms_template
    assert composite is not None, logger.get_message() + " " + repr(logger.entries)
    assert composite.device is generator
    assert composite in veragrid_model.rms_models
    assert "GovSteamSGO" in composite.name
    event_names: set[str] = set()
    for runtime_block in composite.block.get_all_blocks():
        for event_variable in runtime_block.event_dict:
            if event_variable.name.startswith("GovSteamSGO."):
                event_names.add(event_variable.name.split("_")[0].split(".")[1])
            else:
                pass
    assert event_names == {
        "enabled", "mwbase", "t1", "t2", "t3", "t4", "t5", "t6",
        "k1", "k2", "k3", "pmax", "pmin",
    }
    assert_zero_initial_residuals(
        deepcopy(composite),
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.3,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


@pytest.mark.parametrize(
    ("t1", "t2", "t3", "t4", "t5", "t6"),
    ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.2, 0.05, 0.3, 0.4, 1.0, 0.2)),
)
def test_gov_steam_sgo_equations_reduce_zero_time_stages(
        t1: float,
        t2: float,
        t3: float,
        t4: float,
        t5: float,
        t6: float,
) -> None:
    """Keep SGO lag and lead-lag structures valid at exact zero times.

    :param t1: Controller lag time.
    :param t2: Controller lead time.
    :param t3: Governor lag time.
    :param t4: Steam chest time.
    :param t5: Reheater time.
    :param t6: Low pressure turbine time.
    :return: None.
    """
    parameters: GovSteamSGOParameters = GovSteamSGOParameters(
        t1=t1, t2=t2, t3=t3, t4=t4, t5=t5, t6=t6,
    )
    template: RmsModelTemplate = build_gov_steam_s_g_o_template(
        VarFactory(),
        "GovSteamSGO_zero_time_check",
        parameters,
    )
    state_names: tuple[str, ...] = tuple(
        state_variable.name for state_variable in template.block.state_vars
    )
    assert ("GovSteamSGOControllerPuState_" in " ".join(state_names)) is (t1 > 0.0)
    assert ("GovSteamSGOValvePu_" in " ".join(state_names)) is (t3 > 0.0)
    assert ("GovSteamSGOSteamChestPu_" in " ".join(state_names)) is (t4 > 0.0)
    assert ("GovSteamSGOReheaterPu_" in " ".join(state_names)) is (t5 > 0.0)
    assert ("GovSteamSGOLowPressurePu_" in " ".join(state_names)) is (t6 > 0.0)


def test_exc_ieee_st3a_maps_canonical_fields_and_builds_compound_equations() -> None:
    """Check RDF mapping and non-shell ST3A equation graph construction.

    :return: None.
    """
    cgmes_object: ExcIEEEST3A = ExcIEEEST3A(rdfid='_exc_ieee_st3a_check')
    cgmes_object.kp = 2.25
    cgmes_object.thetap = 12.0
    cgmes_object.ta = 0.0
    settings: ExcIEEEST3AParameters = get_exc_ieee_st3a_parameters(cgmes_object)
    assert settings.kp == 2.25
    assert settings.thetap == 12.0
    assert settings.ta == 0.0

    template: RmsModelTemplate = build_exc_i_e_e_e_s_t3_a_template(
        VarFactory(),
        name='ExcIEEEST3A_equation_check',
        parameters=settings,
    )
    runtime_block: Block = template.block.children[0]
    assert len(runtime_block.state_eqs) == 2
    assert len(runtime_block.algebraic_eqs) == 12
    assert len([var for var in runtime_block.event_dict if var.name.startswith('ExcIEEEST3A.')]) == 20

    nonzero_ta_template: RmsModelTemplate = build_exc_i_e_e_e_s_t3_a_template(
        VarFactory(),
        name='ExcIEEEST3A_nonzero_ta_check',
        parameters=ExcIEEEST3AParameters(ta=0.1),
    )
    nonzero_ta_block: Block = nonzero_ta_template.block.children[0]
    regulator_state: Var | None = find_block_variable_by_name(
        nonzero_ta_block,
        'VRState_ExcIEEEST3A_nonzero_ta_check',
    )
    regulator_output: Var | None = find_block_variable_by_name(
        nonzero_ta_block,
        'VR_ExcIEEEST3A_nonzero_ta_check',
    )
    assert regulator_state is not None
    assert regulator_output is not None
    assert len(nonzero_ta_block.state_eqs) == 3
    assert len(nonzero_ta_block.algebraic_eqs) == 13
    regulator_state_equation: Expr = nonzero_ta_block.state_eqs[
        nonzero_ta_block.state_vars.index(regulator_state)
    ]
    regulator_output_equation: Expr = nonzero_ta_block.algebraic_eqs[
        nonzero_ta_block.algebraic_vars.index(regulator_output)
    ]
    regulator_state_variables: set[str] = set(
        variable.name for variable in regulator_state_equation.get_vars()
    )
    regulator_output_variables: set[str] = set(
        variable.name for variable in regulator_output_equation.get_vars()
    )
    assert any(name.startswith('LAW1_y') for name in regulator_state_variables)
    assert any(name.startswith('TA') for name in regulator_state_variables)
    assert regulator_state.name in regulator_state_variables
    assert regulator_output.name in regulator_output_variables
    assert any(name.startswith('VRMIN') for name in regulator_output_variables)
    assert any(name.startswith('VRMAX') for name in regulator_output_variables)


def test_exc_ieee_st3a_import_composes_with_direct_axis_machine() -> None:
    """Bind ST3A dq, field-current and field-voltage ports to its machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st3a_bus')
    exciter: ExcIEEEST3A = ExcIEEEST3A(rdfid='_detailed_ieee_st3a_exciter')
    exciter.ta = 0.1
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st3a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(
        idtag=machine.uuid,
        name='detailed_ieee_st3a_generator',
        P=50.0,
        Q=20.0,
    )
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEST3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEST3A.')
    for exciter_input in ('XadIfd_', 'Vm_', 'Vd_', 'Vq_', 'Id_', 'Iq_', 'vpss'):
        assert find_block_variable_by_name(composite_template.block, exciter_input) is None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.2,
        },
    )


def test_exc_st3a_equations_and_canonical_fields() -> None:
    """Check canonical ExcST3A fields and its standalone equation graph.

    :return: None.
    """
    exciter: ExcST3A = ExcST3A(rdfid='_exc_st3a_check')
    template: RmsModelTemplate = build_exc_s_t3_a_template(VarFactory(), name='ExcST3A_check')
    block: Block = template.block
    primitive_blocks: list[Block] = block.get_all_blocks()
    assert sum(len(primitive.state_eqs) for primitive in primitive_blocks) == 2
    assert sum(len(primitive.algebraic_eqs) for primitive in primitive_blocks) == 9
    assert sum(
        len([variable for variable in primitive.event_dict if variable.name.startswith('ExcST3A.')])
        for primitive in primitive_blocks
    ) == 21
    assert tuple(
        property_definition.property_name
        for property_definition in ExcST3A.LOCAL_CGMES_PROPERTIES
    ) == (
        'vimax', 'vimin', 'kj', 'tb', 'tc', 'efdmax', 'km', 'tm', 'vrmax',
        'vrmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax',
        'ks', 'ks1',
    )


def test_exc_st3a_import_composes_with_direct_axis_machine_at_nonzero_power() -> None:
    """Check ExcST3A machine association and operating-point residuals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_cgmes_st3a_bus')
    exciter: ExcST3A = ExcST3A(rdfid='_detailed_cgmes_st3a_exciter')
    exciter.vrmax = 5.0
    exciter.vrmin = -5.0
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_cgmes_st3a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_cgmes_st3a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_cgmes_st3a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcST3A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_ExcST3A_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert find_block_variable_by_name(composite_template.block, 'EfdPu') is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )
def test_exc_ieee_st4b_maps_and_builds_cascaded_pi_equations() -> None:
    """Check all canonical ST4B mappings and the two PI state equations.

    :return: None.
    """
    cgmes_object: ExcIEEEST4B = ExcIEEEST4B(rdfid='_exc_ieee_st4b_check')
    cgmes_object.kpr = 3.0
    cgmes_object.kir = 0.75
    cgmes_object.kpm = 2.0
    cgmes_object.kim = 0.5
    cgmes_object.thetap = 8.0
    settings: ExcIEEEST4BParameters = get_exc_ieee_st4b_parameters(cgmes_object)
    assert (settings.kpr, settings.kir, settings.kpm, settings.kim, settings.thetap) == (
        3.0, 0.75, 2.0, 0.5, 8.0,
    )
    template: RmsModelTemplate = build_exc_i_e_e_e_s_t4_b_template(
        VarFactory(),
        name='ExcIEEEST4B_equation_check',
        parameters=settings,
    )
    block: Block = template.block
    assert len(block.state_eqs) == 3
    assert len(block.algebraic_eqs) == 6
    assert len([var for var in block.event_dict if var.name.startswith('ExcIEEEST4B.')]) == 16


def test_exc_ieee_st4b_import_composes_with_direct_axis_machine() -> None:
    """Bind ST4B compound source and field feedback to its machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st4b_bus')
    exciter: ExcIEEEST4B = ExcIEEEST4B(rdfid='_detailed_ieee_st4b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st4b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st4b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_st4b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEST4B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEST4B.')
    for port_name in ('UsPu', 'VrPu', 'ViPu', 'IrPu', 'IiPu', 'IfdPu', 'EfdPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_{exciter.uuid}',
        ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'EfdPu_{exciter.uuid}',
    ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_exc_st4b_import_composes_with_direct_axis_machine_at_nonzero_power() -> None:
    """Check CGMES ExcST4B parameter retention and machine equilibrium wiring.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_cgmes_st4b_bus')
    exciter: ExcST4B = ExcST4B(rdfid='_detailed_cgmes_st4b_exciter')
    exciter.kpr = 2.8
    exciter.kir = 0.6
    exciter.ta = 0.02
    exciter.kpm = 1.7
    exciter.kim = 0.4
    exciter.vmmax = 5.0
    exciter.kp = 1.2
    exciter.ki = 0.3
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_cgmes_st4b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_cgmes_st4b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_cgmes_st4b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcST4B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_ExcST4B_' in composite_template.name
    assert any(
        variable.name.startswith('ExcST4B.kpr_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.event_dict
    )
    exciter_template_name: str = composite_template.name.rsplit('_with_', 1)[1]
    for port_name in ('UsPu', 'VrPu', 'ViPu', 'IrPu', 'IiPu', 'IfdPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_{exciter_template_name}',
        ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_cgmes_2415_type3a_composes_to_power_electronics_equipment() -> None:
    """Check the canonical 2.4.15 Type 3A graph and physical-equipment link.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    equipment: EnergySource = EnergySource(
        rdfid='_wind_type3a_equipment'
    )
    turbine: WindGenTurbineType3aIEC24 = WindGenTurbineType3aIEC24(
        rdfid='_wind_type3a_turbine'
    )
    turbine.EnergySource = equipment
    turbine.kpc = 1.0
    turbine.tic = 0.1
    turbine.xs = 0.1
    aerodynamic: WindAeroLinearIEC24 = WindAeroLinearIEC24(
        rdfid='_wind_type3a_aerodynamic'
    )
    aerodynamic.dpomega = 0.0
    aerodynamic.dptheta = 0.0
    aerodynamic.omegazero = 1.0
    aerodynamic.pavail = 0.5
    aerodynamic.thetazero = 0.0
    aerodynamic.WindGenTurbineType3IEC = turbine
    turbine.WindAeroLinearIEC = aerodynamic
    mechanical: WindMechIEC = WindMechIEC(rdfid='_wind_type3a_mechanical')
    mechanical.cdrt = 0.02
    mechanical.hgen = 1.2
    mechanical.hwtr = 3.0
    mechanical.kdrt = 2.0
    mechanical.WindTurbineType3IEC = turbine
    turbine.WindMechIEC = mechanical

    bus: Bus = Bus(name='wind_type3a_bus')
    generator: Generator = Generator(
        idtag=equipment.uuid,
        name='wind_type3a_generator',
        P=50.0,
        Snom=100.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    veragrid_devices: dict[str, object] = dict()
    veragrid_devices[equipment.uuid] = generator
    assert find_veragrid_devices(turbine, veragrid_devices) == [generator]
    assert find_veragrid_devices(aerodynamic, veragrid_devices) == [generator]
    assert find_veragrid_devices(mechanical, veragrid_devices) == [generator]
    cgmes_model.dynamics_assets.lists['WindGenTurbineType3aIEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindAeroLinearIEC'].append(aerodynamic)
    cgmes_model.dynamics_assets.lists['WindMechIEC'].append(mechanical)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, logger.get_message() + ''.join(
        str(entry) for entry in logger.entries
    )
    assert 'WindAeroLinearIEC' in composite_template.name
    assert composite_template.device is generator
    assert any(
        variable.name.startswith('PaeroPu_WindAeroLinearIEC_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.algebraic_vars
    )
    assert any(
        variable.name.startswith('TshaftPu_WindMechIEC_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.algebraic_vars
    )
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_cgmes_type4a_type3a_generator_composes_network_current() -> None:
    """Check Type 4A's Type 3A alternative through its physical current boundary.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    equipment: PowerElectronicsConnection = PowerElectronicsConnection(
        rdfid='_wind_type4a_type3a_equipment',
    )
    turbine: WindTurbineType4aIEC = WindTurbineType4aIEC(
        rdfid='_wind_type4a_type3a_turbine',
    )
    turbine.PowerElectronicsConnection = equipment
    generator_model: WindGenType3aIEC = WindGenType3aIEC(
        rdfid='_wind_type4a_type3a_generator_model',
    )
    generator_model.dipmax = 1.0
    generator_model.diqmax = 1.0
    generator_model.xs = 0.1
    generator_model.kpc = 1.0
    generator_model.tic = 0.1
    generator_model.WindTurbineType4IEC = turbine
    turbine.WindGenType3aIEC = generator_model
    power_control: WindContPType4aIEC = WindContPType4aIEC(
        rdfid='_wind_type4a_type3a_power_control',
    )
    power_control.WindTurbineType4aIEC = turbine
    turbine.WindContPType4aIEC = power_control
    current_limiter: WindContCurrLimIEC = WindContCurrLimIEC(
        rdfid='_wind_type4a_type3a_current_limiter',
    )
    current_limiter.imax = 1.0
    current_limiter.imaxdip = 1.0
    current_limiter.kpqu = 1.0
    current_limiter.mdfslim = True
    current_limiter.mqpri = False
    current_limiter.tufiltcl = 0.0
    current_limiter.upqumax = 1.2
    current_limiter.WindTurbineType3or4IEC = turbine
    turbine.WindContCurrLimIEC = current_limiter
    active_curve_records: list[WindDynamicsLookupTable] = list()
    reactive_curve_records: list[WindDynamicsLookupTable] = list()
    for sequence, voltage, current in ((1, 0.0, 1.0), (2, 2.0, 1.0)):
        active_record: WindDynamicsLookupTable = WindDynamicsLookupTable(
            rdfid=f'_wind_type4a_type3a_ipmax_{sequence}',
        )
        active_record.sequence = sequence
        active_record.input = voltage
        active_record.output = current
        active_record.lookupTableFunctionType = WindLookupTableFunctionKind.ipmax
        active_record.WindContCurrLimIEC = current_limiter
        active_curve_records.append(active_record)
        reactive_record: WindDynamicsLookupTable = WindDynamicsLookupTable(
            rdfid=f'_wind_type4a_type3a_iqmax_{sequence}',
        )
        reactive_record.sequence = sequence
        reactive_record.input = voltage
        reactive_record.output = current
        reactive_record.lookupTableFunctionType = WindLookupTableFunctionKind.iqmax
        reactive_record.WindContCurrLimIEC = current_limiter
        reactive_curve_records.append(reactive_record)
    else:
        pass
    current_limiter.WindDynamicsLookupTable.extend(active_curve_records)
    current_limiter.WindDynamicsLookupTable.extend(reactive_curve_records)
    reactive_controller: WindContQIEC = WindContQIEC(
        rdfid='_wind_type4a_type3a_reactive_controller',
    )
    reactive_controller.windQcontrolModesType = WindQcontrolModeKind.reactivePower
    reactive_controller.windUVRTQcontrolModesType = WindUVRTQcontrolModeKind.mode0
    reactive_controller.WindTurbineType3or4IEC = turbine
    turbine.WIndContQIEC = reactive_controller
    reactive_limit: WindContQLimIEC = WindContQLimIEC(
        rdfid='_wind_type4a_type3a_reactive_limit',
    )
    reactive_limit.qmax = 1.0
    reactive_limit.qmin = -1.0
    reactive_limit.WindTurbineType3or4IEC = turbine
    turbine.WindContQLimIEC = reactive_limit
    reference_frame: WindRefFrameRotIEC = WindRefFrameRotIEC(
        rdfid='_wind_type4a_type3a_reference_frame',
    )
    reference_frame.tpll = 0.01
    reference_frame.upll1 = 0.0
    reference_frame.upll2 = 0.0
    reference_frame.WindTurbineType3or4IEC = turbine
    turbine.WindRefFrameRotIEC = reference_frame
    bus: Bus = Bus(name='wind_type4a_type3a_bus')
    generator: Generator = Generator(
        idtag=equipment.uuid,
        name='wind_type4a_type3a_generator',
        P=50.0,
        Snom=100.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['WindTurbineType4aIEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindGenType3aIEC'].append(generator_model)
    cgmes_model.dynamics_assets.lists['WindContPType4aIEC'].append(power_control)
    cgmes_model.dynamics_assets.lists['WindContCurrLimIEC'].append(current_limiter)
    cgmes_model.dynamics_assets.lists['WindContQIEC'].append(reactive_controller)
    cgmes_model.dynamics_assets.lists['WindContQLimIEC'].append(reactive_limit)
    cgmes_model.dynamics_assets.lists['WindDynamicsLookupTable'].extend(
        active_curve_records + reactive_curve_records
    )
    cgmes_model.dynamics_assets.lists['WindRefFrameRotIEC'].append(reference_frame)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    template: RmsModelTemplate | None = generator.rms_template
    assert template is not None, logger.get_message() + ''.join(
        str(entry) for entry in logger.entries
    )
    assert template.device is generator
    assert 'WindGenType3aIEC' in template.name
    assert template.block.external_mapping[VarPowerFlowReferenceType.Ir] is not None
    assert template.block.external_mapping[VarPowerFlowReferenceType.Ii] is not None
    assert find_block_variable_by_name(
        template.block,
        f'IreSystemPu_WindContPType4aIEC_{power_control.uuid}_with_WindGenType3aIEC_{generator_model.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        template.block,
        f'IqCmdPu_WindGenType3aIEC_{generator_model.uuid}',
    ) is None
    assert find_block_variable_by_name(
        template.block,
        f'IqCmdPu_WindContQIEC_{reactive_controller.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        template.block,
        f'FreezePu_WindContQIEC_{reactive_controller.uuid}',
    ) is not None


def test_cgmes_type4a_type4_generator_maps_and_composes() -> None:
    """Check the canonical Type 4 generator parameters in its Type 4A graph.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    equipment: PowerElectronicsConnection = PowerElectronicsConnection(
        rdfid='_wind_type4a_type4_equipment',
    )
    turbine: WindTurbineType4aIEC = WindTurbineType4aIEC(
        rdfid='_wind_type4a_type4_turbine',
    )
    turbine.PowerElectronicsConnection = equipment
    generator_model: WindGenType4IEC = WindGenType4IEC(
        rdfid='_wind_type4a_type4_generator_model',
    )
    generator_model.dipmax = 0.5
    generator_model.diqmax = 0.3
    generator_model.diqmin = -0.2
    generator_model.tg = 0.04
    generator_model.WindTurbineType4aIEC = turbine
    turbine.WindGenType4IEC = generator_model
    power_control: WindContPType4aIEC = WindContPType4aIEC(
        rdfid='_wind_type4a_type4_power_control',
    )
    power_control.dpmaxp4a = 0.2
    power_control.tpordp4a = 0.02
    power_control.tufiltp4a = 0.05
    power_control.WindTurbineType4aIEC = turbine
    turbine.WindContPType4aIEC = power_control
    reference_frame: WindRefFrameRotIEC = WindRefFrameRotIEC(
        rdfid='_wind_type4a_type4_reference_frame',
    )
    reference_frame.tpll = 0.01
    reference_frame.upll1 = 0.0
    reference_frame.upll2 = 0.0
    reference_frame.WindTurbineType3or4IEC = turbine
    turbine.WindRefFrameRotIEC = reference_frame
    current_limiter: WindContCurrLimIEC = WindContCurrLimIEC(
        rdfid='_wind_type4a_type4_current_limiter',
    )
    current_limiter.imax = 1.2
    current_limiter.imaxdip = 1.0
    current_limiter.kpqu = 1.0
    current_limiter.mdfslim = True
    current_limiter.mqpri = False
    current_limiter.tufiltcl = 0.0
    current_limiter.upqumax = 1.2
    current_limiter.WindTurbineType3or4IEC = turbine
    turbine.WindContCurrLimIEC = current_limiter
    limiter_curve_records: list[WindDynamicsLookupTable] = list()
    for sequence, lookup_kind, output_value in (
            (1, WindLookupTableFunctionKind.ipmax, 1.2),
            (2, WindLookupTableFunctionKind.ipmax, 1.2),
            (1, WindLookupTableFunctionKind.iqmax, 1.2),
            (2, WindLookupTableFunctionKind.iqmax, 1.2),
    ):
        lookup_record: WindDynamicsLookupTable = WindDynamicsLookupTable(
            rdfid=f'_wind_type4a_type4_limit_{lookup_kind.name}_{sequence}',
        )
        lookup_record.sequence = sequence
        lookup_record.input = 0.0 if sequence == 1 else 2.0
        lookup_record.output = output_value
        lookup_record.lookupTableFunctionType = lookup_kind
        lookup_record.WindContCurrLimIEC = current_limiter
        limiter_curve_records.append(lookup_record)
    else:
        pass
    current_limiter.WindDynamicsLookupTable.extend(limiter_curve_records)
    reactive_limit: WindContQLimIEC = WindContQLimIEC(
        rdfid='_wind_type4a_type4_reactive_limit',
    )
    reactive_limit.qmax = 1.0
    reactive_limit.qmin = -1.0
    reactive_limit.WindTurbineType3or4IEC = turbine
    turbine.WindContQLimIEC = reactive_limit
    reactive_controller: WindContQIEC = WindContQIEC(
        rdfid='_wind_type4a_type4_reactive_controller',
    )
    reactive_controller.windQcontrolModesType = WindQcontrolModeKind.reactivePower
    reactive_controller.windUVRTQcontrolModesType = WindUVRTQcontrolModeKind.mode0
    reactive_controller.WindTurbineType3or4IEC = turbine
    turbine.WIndContQIEC = reactive_controller
    bus: Bus = Bus(name='wind_type4a_type4_bus')
    generator: Generator = Generator(
        idtag=equipment.uuid,
        name='wind_type4a_type4_generator',
        P=50.0,
        Snom=100.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['WindTurbineType4aIEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindGenType4IEC'].append(generator_model)
    cgmes_model.dynamics_assets.lists['WindContPType4aIEC'].append(power_control)
    cgmes_model.dynamics_assets.lists['WindContCurrLimIEC'].append(current_limiter)
    cgmes_model.dynamics_assets.lists['WindContQLimIEC'].append(reactive_limit)
    cgmes_model.dynamics_assets.lists['WindContQIEC'].append(reactive_controller)
    cgmes_model.dynamics_assets.lists['WindDynamicsLookupTable'].extend(limiter_curve_records)
    cgmes_model.dynamics_assets.lists['WindRefFrameRotIEC'].append(reference_frame)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    template: RmsModelTemplate | None = generator.rms_template
    assert template is not None, logger.get_message() + ''.join(
        str(entry) for entry in logger.entries
    )
    assert template.device is generator
    assert 'WindGenType4IEC' in template.name
    assert template.block.external_mapping[VarPowerFlowReferenceType.Ir] is not None
    assert template.block.external_mapping[VarPowerFlowReferenceType.Ii] is not None
    for parameter_name, expected_value in (
            ('dipmax', 0.5), ('diqmax', 0.3), ('diqmin', -0.2), ('tg', 0.04),
    ):
        matching_parameters: list[tuple[Var, Const]] = list()
        for runtime_block in template.block.get_all_blocks():
            for parameter_variable, parameter_value in runtime_block.event_dict.items():
                if parameter_variable.name.startswith(f'WindGenType4IEC.{parameter_name}_'):
                    assert isinstance(parameter_value, Const)
                    matching_parameters.append((parameter_variable, parameter_value))
                else:
                    pass
        assert len(matching_parameters) == 1
        assert matching_parameters[0][1].value == expected_value
    assert_zero_initial_residuals(
        template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_wind_type4b_p_control_keeps_ipmax_out_of_power_command() -> None:
    """Keep Figure 36 current limits separate from the Figure 34 command.

    :return: None.
    """
    template: RmsModelTemplate = build_wind_cont_p_type4b_i_e_c_template(
        vfactory=VarFactory(),
        name='wind_type4b_p_control',
        initial_power=0.5,
    )
    input_names: tuple[str, ...] = tuple(variable.name for variable in template.block.in_vars)
    assert not any(input_name.startswith('IpMaxPu_') for input_name in input_names)
    command: Var | None = find_block_variable_by_name(
        template.block,
        'IpCmdPu_wind_type4b_p_control',
    )
    assert command is not None
    command_equation: Expr | None = None
    for equation in template.block.algebraic_eqs:
        if isinstance(equation, BinOp) and equation.left is command:
            command_equation = equation.right
        else:
            pass
    assert command_equation is not None
    assert all(not variable.name.startswith('IpMaxPu_') for variable in command_equation.get_vars())


def test_cgmes_type3b_composes_reference_frame_and_network_current() -> None:
    """Check Type 3B current-source composition through its PLL and equipment.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    equipment: PowerElectronicsConnection = PowerElectronicsConnection(
        rdfid='_wind_type3b_equipment'
    )
    turbine: WindTurbineType3IEC = WindTurbineType3IEC(
        rdfid='_wind_type3b_turbine'
    )
    turbine.PowerElectronicsConnection = equipment
    generator_model: WindGenType3bIEC = WindGenType3bIEC(
        rdfid='_wind_type3b_generator_model'
    )
    generator_model.dipmax = 1.0
    generator_model.diqmax = 1.0
    generator_model.xs = 0.1
    generator_model.tg = 0.02
    generator_model.two = 0.01
    generator_model.mwtcwp = False
    generator_model.WindTurbineType3IEC = turbine
    turbine.WindGenType3IEC = generator_model
    aerodynamic: WindAeroOneDimIEC = WindAeroOneDimIEC(
        rdfid='_wind_type3b_aerodynamic'
    )
    aerodynamic.ka = 0.0
    aerodynamic.thetaomega = AngleDegrees(rdfid='_wind_type3b_reference_pitch')
    aerodynamic.thetaomega.value = 0.0
    aerodynamic.WindTurbineType3IEC = turbine
    turbine.WindAeroOneDimIEC = aerodynamic
    mechanical: WindMechIEC = WindMechIEC(rdfid='_wind_type3b_mechanical')
    mechanical.cdrt = 0.02
    mechanical.hgen = 1.2
    mechanical.hwtr = 3.0
    mechanical.kdrt = 2.0
    mechanical.WindTurbineType3IEC = turbine
    turbine.WindMechIEC = mechanical
    reference_frame: WindRefFrameRotIEC = WindRefFrameRotIEC(
        rdfid='_wind_type3b_reference_frame'
    )
    reference_frame.tpll = 0.01
    reference_frame.upll1 = 0.0
    reference_frame.upll2 = 0.0
    reference_frame.WindTurbineType3or4IEC = turbine
    turbine.WindRefFrameRotIEC = reference_frame

    bus: Bus = Bus(name='wind_type3b_bus')
    bus.Va0 = 0.2
    generator: Generator = Generator(
        idtag=equipment.uuid,
        name='wind_type3b_generator',
        P=50.0,
        Snom=100.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    cgmes_model.dynamics_assets.lists['WindTurbineType3IEC'].append(turbine)
    cgmes_model.dynamics_assets.lists['WindGenType3bIEC'].append(generator_model)
    cgmes_model.dynamics_assets.lists['WindAeroOneDimIEC'].append(aerodynamic)
    cgmes_model.dynamics_assets.lists['WindMechIEC'].append(mechanical)
    cgmes_model.dynamics_assets.lists['WindRefFrameRotIEC'].append(reference_frame)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None, logger.get_message() + ''.join(
        str(entry) for entry in logger.entries
    )
    assert composite_template.device is generator
    assert any(
        variable.name.startswith('IreSystemPu_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.algebraic_vars
    )
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.2,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_cgmes_2415_type3b_retains_ambiguous_fducw_but_builds_without_crowbar() -> None:
    """Keep the malformed scalar curve as RDF and build the disabled-crowbar case.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    equipment: EnergySource = EnergySource(
        rdfid='_wind_type3b_2415_equipment',
    )
    generator_model: WindGenTurbineType3bIEC24 = WindGenTurbineType3bIEC24(
        rdfid='_wind_type3b_2415_model',
    )
    generator_model.EnergySource = equipment
    generator_model.dipmax = 1.0
    generator_model.diqmax = 1.0
    generator_model.fducw = 1.0
    generator_model.mwtcwp = True
    generator_model.tg = 0.02
    generator_model.two = 0.01
    generator_model.xs = 0.1
    bus: Bus = Bus(name='wind_type3b_2415_bus')
    bus.Va0 = 0.2
    enabled_generator: Generator = Generator(
        idtag=equipment.uuid,
        name='wind_type3b_2415_generator',
        P=50.0,
        Snom=100.0,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=enabled_generator)
    cgmes_model.dynamics_assets.lists['WindGenTurbineType3bIEC'].append(generator_model)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    assert enabled_generator.rms_template is None
    diagnostic_messages: list[str] = [entry.msg for entry in logger.entries]
    assert any('no canonical curve sample encoding exists' in message for message in diagnostic_messages)

    disabled_cgmes_model: CgmesCircuit = CgmesCircuit()
    disabled_model: WindGenTurbineType3bIEC24 = WindGenTurbineType3bIEC24(
        rdfid='_wind_type3b_2415_disabled_model',
    )
    disabled_model.EnergySource = equipment
    disabled_model.dipmax = 1.0
    disabled_model.diqmax = 1.0
    disabled_model.fducw = 1.0
    disabled_model.mwtcwp = False
    disabled_model.tg = 0.02
    disabled_model.two = 0.01
    disabled_model.xs = 0.1
    aerodynamic_model: WindAeroLinearIEC24 = WindAeroLinearIEC24(
        rdfid='_wind_type3b_2415_aerodynamic',
    )
    aerodynamic_model.dpomega = 0.0
    aerodynamic_model.dptheta = 0.0
    aerodynamic_model.omegazero = 1.0
    aerodynamic_model.pavail = 0.5
    aerodynamic_model.thetazero = AngleDegrees(rdfid='_wind_type3b_2415_pitch_reference')
    aerodynamic_model.thetazero.value = 0.0
    aerodynamic_model.WindGenTurbineType3IEC = disabled_model
    disabled_model.WindAeroLinearIEC = aerodynamic_model
    mechanical_model: WindMechIEC = WindMechIEC(rdfid='_wind_type3b_2415_mechanical')
    mechanical_model.cdrt = 0.02
    mechanical_model.hgen = 1.2
    mechanical_model.hwtr = 3.0
    mechanical_model.kdrt = 2.0
    mechanical_model.WindTurbineType3IEC = disabled_model
    disabled_model.WindMechIEC = mechanical_model
    disabled_cgmes_model.dynamics_assets.lists['WindGenTurbineType3bIEC'].append(disabled_model)
    disabled_cgmes_model.dynamics_assets.lists['WindAeroLinearIEC'].append(aerodynamic_model)
    disabled_cgmes_model.dynamics_assets.lists['WindMechIEC'].append(mechanical_model)
    disabled_logger: DataLogger = DataLogger()

    convert_cgmes_dynamics(disabled_cgmes_model, veragrid_model, disabled_logger)

    composite_template: RmsModelTemplate | None = enabled_generator.rms_template
    assert composite_template is not None, disabled_logger.get_message() + repr(disabled_logger.entries)
    assert any(
        variable.name.startswith('IreSystemPu_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.algebraic_vars
    )
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.2,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_exc_ieee_st5b_maps_all_fields_and_builds_channel_equations() -> None:
    """Check all canonical ST5B values reach the three-channel graph.

    :return: None.
    """
    cgmes_object: ExcIEEEST5B = ExcIEEEST5B(rdfid='_exc_ieee_st5b_check')
    cgmes_object.kr = 25.0
    cgmes_object.t1 = 0.08
    cgmes_object.kc = 0.15
    cgmes_object.toc1 = 0.06
    cgmes_object.tuc2 = 0.12
    settings: ExcIEEEST5BParameters = get_exc_ieee_st5b_parameters(cgmes_object)
    assert (settings.kr, settings.t1, settings.kc, settings.toc1, settings.tuc2) == (
        25.0, 0.08, 0.15, 0.06, 0.12,
    )
    template: RmsModelTemplate = build_exc_i_e_e_e_s_t5_b_template(
        VarFactory(),
        name='ExcIEEEST5B_equation_check',
        parameters=settings,
    )
    assert len(template.block.state_eqs) == 7
    assert len(template.block.algebraic_eqs) == 15
    assert len([var for var in template.block.event_dict if var.name.startswith('ExcIEEEST5B.')]) == 17


def test_exc_ieee_st5b_import_composes_and_initializes_direct_axis_machine() -> None:
    """Attach ST5B and check its composed operating-point equations.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st5b_bus')
    exciter: ExcIEEEST5B = ExcIEEEST5B(rdfid='_detailed_ieee_st5b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st5b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st5b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_st5b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcIEEEST5B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcIEEEST5B.')
    for port_name in ('UsPu', 'VsPu', 'IfdPu', 'VtPu', 'UelPu', 'OelPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_{exciter.uuid}',
        ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ieee_st7b_maps_selectors_and_builds_feedback_graph() -> None:
    """Check canonical ST7B scalar/enum mapping and graph equations.

    :return: None.
    """
    cgmes_object: ExcIEEEST7B = ExcIEEEST7B(rdfid='_exc_ieee_st7b_check')
    cgmes_object.kpa = 18.0
    cgmes_object.kh = 0.8
    cgmes_object.uelin = ExcST7BUELselectorKind.outputHVgate
    cgmes_object.oelin = ExcST7BOELselectorKind.inputLVgate
    settings: ExcIEEEST7BParameters = get_exc_ieee_st7b_parameters(cgmes_object)
    assert settings.kpa == 18.0
    assert settings.kh == 0.8
    assert settings.uelin == ExcST7BUELselectorKind.outputHVgate
    assert settings.oelin == ExcST7BOELselectorKind.inputLVgate
    template: RmsModelTemplate = build_exc_i_e_e_e_s_t7_b_template(
        VarFactory(),
        name='ExcIEEEST7B_equation_check',
        parameters=settings,
    )
    assert len(template.block.state_eqs) == 3
    assert len(template.block.algebraic_eqs) == 10
    assert len([var for var in template.block.event_dict if var.name.startswith('ExcIEEEST7B.')]) == 15


@pytest.mark.parametrize('use_ieee_class', (True, False))
def test_exc_st7b_import_composes_and_initializes_direct_axis_machine(
        use_ieee_class: bool,
) -> None:
    """Attach either canonical ST7B class and balance machine Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_ieee_st7b_bus')
    exciter: ExcIEEEST7B | ExcST7B
    if use_ieee_class:
        exciter = ExcIEEEST7B(rdfid='_detailed_ieee_st7b_exciter')
    else:
        exciter = ExcST7B(rdfid='_detailed_cgmes_st7b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_ieee_st7b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_ieee_st7b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_ieee_st7b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    if use_ieee_class:
        cgmes_model.dynamics_assets.lists['ExcIEEEST7B'].append(exciter)
    else:
        cgmes_model.dynamics_assets.lists['ExcST7B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcST7B.')
    for port_name in ('UsPu', 'VsPu', 'UelPu', 'VtPu', 'OelPu', 'EfdPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_{exciter.uuid}',
        ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_ni_maps_builds_both_supply_modes_and_composes_machine() -> None:
    """Check ExcNI RDF mapping, retained unsupported R, and machine wiring.

    :return: None.
    """
    exciter: ExcNI = ExcNI(rdfid='_detailed_exc_ni_exciter')
    exciter.busFedSelector = True
    exciter.ka = 24.0
    exciter.r = 0.0
    settings: ExcNIParameters = get_exc_ni_parameters(exciter)
    assert settings.bus_fed_selector is True
    assert settings.ka == 24.0
    independent_template: RmsModelTemplate = build_exc_n_i_template(
        VarFactory(),
        name='ExcNI_independent_check',
        parameters=settings,
    )
    assert len(independent_template.block.state_eqs) == 4
    assert len([var for var in independent_template.block.event_dict if var.name.startswith('ExcNI.')]) == 10
    assert 'R=0' in independent_template.comment

    exciter.busFedSelector = False
    terminal_settings: ExcNIParameters = get_exc_ni_parameters(exciter)
    terminal_template: RmsModelTemplate = build_exc_n_i_template(
        VarFactory(),
        name='ExcNI_terminal_check',
        parameters=terminal_settings,
    )
    assert len(terminal_template.block.state_eqs) == 4

    exciter.r = 0.2
    retained_template: RmsModelTemplate = build_exc_n_i_template(
        VarFactory(),
        name='ExcNI_nonzero_r_check',
        parameters=get_exc_ni_parameters(exciter),
    )
    assert len(retained_template.block.state_eqs) == 0
    assert len(retained_template.block.event_dict) == 10

    cgmes_model: CgmesCircuit = CgmesCircuit(cgmes_version=CGMESVersions.v3_0_0)
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_ni_bus')
    exciter = ExcNI(rdfid='_detailed_exc_ni_attached_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_ni_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_ni_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_ni_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcNI'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcNI.')
    for port_name in ('UsPu', 'VsPu', 'UelPu', 'VtPu', 'EfdPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_{exciter.uuid}',
        ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_exc_scrx_import_composes_runtime_ports_and_machine_initial_state() -> None:
    """Wire SCRX regulator inputs to machine voltage, field current, and Efd.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_scrx_bus')
    exciter: ExcSCRX = ExcSCRX(rdfid='_detailed_exc_scrx_exciter')
    exciter.tatb = 0.25
    exciter.tb = 0.4
    exciter.k = 18.0
    exciter.te = 0.08
    exciter.emin = -3.0
    exciter.emax = 4.0
    exciter.cswitch = True
    exciter.rcrfd = 0.12
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_scrx_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_scrx_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_scrx_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcSCRX'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcSCRX.')
    for port_name in (
        'avr.IRotorPu', 'avr.UOelPu', 'avr.UPssPu', 'avr.URefPu', 'avr.UStatorPu',
        'avr.UUelPu', 'avr.UtPu',
    ):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcSCRX_{exciter.uuid}',
        ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_exc_pic_builds_pi_bridge_and_field_equation_graph() -> None:
    """Check ExcPIC equation states and exact canonical parameter events.

    :return: None.
    """
    parameters: ExcPICParameters = ExcPICParameters(te=0.2, tf1=0.3, tf2=0.4, kf=0.05)
    template: RmsModelTemplate = build_exc_p_i_c_template(
        VarFactory(),
        name='ExcPIC_equation_check',
        parameters=parameters,
    )
    assert len(template.block.state_vars) == 5
    assert len(template.block.state_eqs) == 5
    assert len(template.block.in_vars) == 8
    assert len(template.block.out_vars) == 1
    assert len([var for var in template.block.event_dict if var.name.startswith('ExcPIC.')]) == 23

    exciter: ExcPIC = ExcPIC(rdfid='_exc_pic_mapping_check')
    exciter.ka = 4.0
    exciter.kp = 7.0
    exciter.kc = 0.11
    mapped_template: RmsModelTemplate = build_exc_p_i_c_template(
        VarFactory(),
        name='ExcPIC_mapping_check',
    )
    copy_cgmes_parameters(
        cgmes_object=exciter,
        template=mapped_template,
        variable_factory=VarFactory(),
    )
    mapped_values: dict[str, object] = dict()
    for variable, value in mapped_template.block.event_dict.items():
        mapped_values[variable.name] = value
    assert mapped_values['ExcPIC.ka_ExcPIC_mapping_check'].value == 4.0
    assert mapped_values['ExcPIC.kp_ExcPIC_mapping_check'].value == 7.0
    assert mapped_values['ExcPIC.kc_ExcPIC_mapping_check'].value == 0.11


def test_exc_pic_import_composes_to_detailed_machine() -> None:
    """Attach the ExcPIC phasor bridge to the linked direct-axis generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_pic_bus')
    exciter: ExcPIC = ExcPIC(rdfid='_detailed_exc_pic_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_pic_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_pic_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_pic_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcPIC'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcPIC.')
    for port_name in (
        'VtRePu', 'VtImPu', 'ItRePu', 'ItImPu', 'IfdPu', 'UsPu', 'UsRefPu',
    ):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcPIC_ExcPIC_{exciter.uuid}',
        ) is None
    for port_name in ('UpssPu',):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcPIC_ExcPIC_{exciter.uuid}',
        ) is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.0,
            VarPowerFlowReferenceType.Q: 0.0,
        },
    )


def test_exc_oex3t_equations_parameter_mapping_and_zero_time_reduction() -> None:
    """Check ExcOEX3T's sourced stage equations and all canonical scalar fields.

    :return: None.
    """
    settings: ExcOEX3TParameters = ExcOEX3TParameters(
        t1=0.2,
        t2=0.1,
        t3=0.3,
        t4=0.05,
        ka=4.0,
        t5=0.4,
        t6=0.2,
        vrmax=5.0,
        vrmin=-5.0,
        te=0.6,
        kf=0.02,
        tf=0.7,
        kc=0.1,
        kd=0.03,
        ke=1.0,
        e1=2.0,
        see1=0.1,
        e2=3.0,
        see2=0.2,
    )
    template: RmsModelTemplate = build_exc_o_e_x3_t_template(
        VarFactory(),
        name='ExcOEX3T_equation_check',
        parameters=settings,
    )
    assert len(template.block.state_vars) == 5
    assert len(template.block.state_eqs) == 5
    assert len(template.block.in_vars) == 7
    assert len(template.block.out_vars) == 1
    assert len([var for var in template.block.event_dict if var.name.startswith('ExcOEX3T.')]) == 19

    exciter: ExcOEX3T = ExcOEX3T(rdfid='_exc_oex3t_mapping_check')
    exciter.t1 = settings.t1
    exciter.t2 = settings.t2
    exciter.t3 = settings.t3
    exciter.t4 = settings.t4
    exciter.ka = settings.ka
    exciter.t5 = settings.t5
    exciter.t6 = settings.t6
    exciter.vrmax = settings.vrmax
    exciter.vrmin = settings.vrmin
    exciter.te = settings.te
    exciter.kf = settings.kf
    exciter.tf = settings.tf
    exciter.kc = settings.kc
    exciter.kd = settings.kd
    exciter.ke = settings.ke
    exciter.e1 = settings.e1
    exciter.see1 = settings.see1
    exciter.e2 = settings.e2
    exciter.see2 = settings.see2
    mapped_template: RmsModelTemplate = build_exc_o_e_x3_t_template(
        VarFactory(),
        name='ExcOEX3T_mapping_check',
        parameters=settings,
    )
    copy_cgmes_parameters(
        cgmes_object=exciter,
        template=mapped_template,
        variable_factory=VarFactory(),
    )
    mapped_values: dict[str, object] = dict()
    for variable, value in mapped_template.block.event_dict.items():
        mapped_values[variable.name] = value
    expected_mapping: dict[str, float] = {
        't1': settings.t1,
        't2': settings.t2,
        't3': settings.t3,
        't4': settings.t4,
        'ka': settings.ka,
        't5': settings.t5,
        't6': settings.t6,
        'vrmax': settings.vrmax,
        'vrmin': settings.vrmin,
        'te': settings.te,
        'kf': settings.kf,
        'tf': settings.tf,
        'kc': settings.kc,
        'kd': settings.kd,
        'ke': settings.ke,
        'e1': settings.e1,
        'see1': settings.see1,
        'e2': settings.e2,
        'see2': settings.see2,
    }
    for parameter_name, expected_value in expected_mapping.items():
        assert mapped_values[
            f'ExcOEX3T.{parameter_name}_ExcOEX3T_mapping_check'
        ].value == expected_value

    zero_time_template: RmsModelTemplate = build_exc_o_e_x3_t_template(
        VarFactory(),
        name='ExcOEX3T_zero_time_check',
    )
    assert len(zero_time_template.block.state_vars) == 0
    assert len(zero_time_template.block.state_eqs) == 0
    assert len(zero_time_template.block.out_vars) == 1


def test_exc_oex3t_import_composes_to_detailed_machine() -> None:
    """Connect ExcOEX3T runtime ports to its associated detailed generator.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_oex3t_bus')
    exciter: ExcOEX3T = ExcOEX3T(rdfid='_detailed_exc_oex3t_exciter')
    exciter.t1 = 0.2
    exciter.t2 = 0.1
    exciter.t3 = 0.3
    exciter.t4 = 0.05
    exciter.ka = 4.0
    exciter.t5 = 0.4
    exciter.t6 = 0.2
    exciter.vrmax = 5.0
    exciter.vrmin = -5.0
    exciter.te = 0.6
    exciter.kf = 0.02
    exciter.tf = 0.7
    exciter.kc = 0.1
    exciter.kd = 0.03
    exciter.ke = 1.0
    exciter.e1 = 2.0
    exciter.see1 = 0.1
    exciter.e2 = 3.0
    exciter.see2 = 0.2
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_oex3t_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_oex3t_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_oex3t_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcOEX3T'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcOEX3T.')
    for port_name in (
        'VRefPu', 'VcPu', 'UvarPu', 'VsPu', 'VoelPu', 'VuelPu', 'IfdPu', 'EfdPu',
    ):
        port_variable: Var | None = find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcOEX3T_ExcOEX3T_{exciter.uuid}',
        )
        if port_name in ('VRefPu', 'UvarPu', 'VsPu', 'VoelPu', 'VuelPu', 'EfdPu'):
            assert port_variable is not None
        else:
            assert port_variable is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_rexs_equations_mapping_and_selector_reduction() -> None:
    """Check ExcREXS equations, exact RDF fields, selector mapping, and bypasses.

    :return: None.
    """
    settings: ExcREXSParameters = ExcREXSParameters(
        e1=2.0, e2=3.0, fbf_code=1, flimf=1.0, kc=0.08, kd=0.03, ke=1.0,
        kefd=0.7, kf=0.05, kh=0.2, kii=0.4, kip=1.5, ks=1.0, kvi=0.3,
        kvp=4.0, kvphz=0.1, nvphz=0.8, se1=0.1, se2=0.2, ta=0.1,
        tb1=0.2, tb2=0.3, tc1=0.05, tc2=0.08, te=0.5, tf=0.4,
        tf1=0.1, tf2=0.2, tp=0.15, vcmax=1.2, vfmax=5.0, vfmin=-5.0,
        vimax=0.5, vrmax=6.0, vrmin=-6.0, xc=0.1,
    )
    template: RmsModelTemplate = build_exc_r_e_x_s_template(
        VarFactory(), name='ExcREXS_equation_check', parameters=settings,
    )
    assert len(template.block.event_dict) == 36
    assert len(template.block.in_vars) == 10
    assert len(template.block.out_vars) == 1
    assert len(template.block.state_vars) == 9
    assert len(template.block.state_eqs) == 9
    assert any(variable.name == 'FieldVoltage_ExcREXS_ExcREXS_equation_check'
               for variable in template.block.state_vars)
    assert any(variable.name == 'FeedbackWashout_ExcREXS_ExcREXS_equation_check'
               for variable in template.block.state_vars)
    equation_variables: set[int] = set()
    for equation in template.block.state_eqs:
        for variable in equation.get_vars():
            equation_variables.add(variable.uid)
    for equation in template.block.algebraic_eqs:
        for variable in equation.get_vars():
            equation_variables.add(variable.uid)
    for parameter_variable in template.block.event_dict:
        assert parameter_variable.uid in equation_variables

    exciter: ExcREXS = ExcREXS(rdfid='_exc_rexs_mapping_check')
    exciter.e1 = settings.e1
    exciter.e2 = settings.e2
    exciter.fbf = ExcREXSFeedbackSignalKind.fieldCurrent
    exciter.flimf = settings.flimf
    exciter.kc = settings.kc
    exciter.kd = settings.kd
    exciter.ke = settings.ke
    exciter.kefd = settings.kefd
    exciter.kf = settings.kf
    exciter.kh = settings.kh
    exciter.kii = settings.kii
    exciter.kip = settings.kip
    exciter.ks = settings.ks
    exciter.kvi = settings.kvi
    exciter.kvp = settings.kvp
    exciter.kvphz = settings.kvphz
    exciter.nvphz = settings.nvphz
    exciter.se1 = settings.se1
    exciter.se2 = settings.se2
    exciter.ta = settings.ta
    exciter.tb1 = settings.tb1
    exciter.tb2 = settings.tb2
    exciter.tc1 = settings.tc1
    exciter.tc2 = settings.tc2
    exciter.te = settings.te
    exciter.tf = settings.tf
    exciter.tf1 = settings.tf1
    exciter.tf2 = settings.tf2
    exciter.tp = settings.tp
    exciter.vcmax = settings.vcmax
    exciter.vfmax = settings.vfmax
    exciter.vfmin = settings.vfmin
    exciter.vimax = settings.vimax
    exciter.vrmax = settings.vrmax
    exciter.vrmin = settings.vrmin
    exciter.xc = settings.xc
    mapped_template: RmsModelTemplate = build_exc_r_e_x_s_template(
        VarFactory(), name='ExcREXS_mapping_check', parameters=settings,
    )
    mapping_factory: VarFactory = VarFactory()
    copy_cgmes_parameters(exciter, mapped_template, mapping_factory)
    set_exc_rexs_feedback_selector(exciter, mapped_template, mapping_factory)
    mapped_values: dict[str, object] = dict()
    for variable, value in mapped_template.block.event_dict.items():
        mapped_values[variable.name] = value
    expected_values: tuple[tuple[str, float], ...] = (
        ('e1', settings.e1), ('e2', settings.e2), ('flimf', settings.flimf),
        ('kc', settings.kc), ('kd', settings.kd), ('ke', settings.ke),
        ('kefd', settings.kefd), ('kf', settings.kf), ('kh', settings.kh),
        ('kii', settings.kii), ('kip', settings.kip), ('ks', settings.ks),
        ('kvi', settings.kvi), ('kvp', settings.kvp), ('kvphz', settings.kvphz),
        ('nvphz', settings.nvphz), ('se1', settings.se1), ('se2', settings.se2),
        ('ta', settings.ta), ('tb1', settings.tb1), ('tb2', settings.tb2),
        ('tc1', settings.tc1), ('tc2', settings.tc2), ('te', settings.te),
        ('tf', settings.tf), ('tf1', settings.tf1), ('tf2', settings.tf2),
        ('tp', settings.tp), ('vcmax', settings.vcmax), ('vfmax', settings.vfmax),
        ('vfmin', settings.vfmin), ('vimax', settings.vimax), ('vrmax', settings.vrmax),
        ('vrmin', settings.vrmin), ('xc', settings.xc),
    )
    for parameter_name, expected_value in expected_values:
        mapped_value: object = mapped_values[f'ExcREXS.{parameter_name}_ExcREXS_mapping_check']
        assert mapped_value.value == expected_value
    assert mapped_values['ExcREXS.fbf_ExcREXS_mapping_check'].value == 1.0
    exciter.fbf = ExcREXSFeedbackSignalKind.outputVoltage
    assert get_exc_rexs_parameters(exciter).fbf_code == 2
    exciter.fbf = ExcREXSFeedbackSignalKind.fieldVoltage
    assert get_exc_rexs_parameters(exciter).fbf_code == 0

    zero_time_template: RmsModelTemplate = build_exc_r_e_x_s_template(
        VarFactory(), name='ExcREXS_zero_time_check',
        parameters=ExcREXSParameters(kvp=1.0, kip=1.0, te=1.0),
    )
    assert len(zero_time_template.block.state_vars) == 1
    assert len(zero_time_template.block.state_eqs) == 1


def test_exc_rexs_import_composes_and_initializes_detailed_machine() -> None:
    """Associate ExcREXS to the RDF-linked machine and check startup residuals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_rexs_bus')
    exciter: ExcREXS = ExcREXS(rdfid='_detailed_exc_rexs_exciter')
    exciter.e1 = 2.0
    exciter.e2 = 3.0
    exciter.fbf = ExcREXSFeedbackSignalKind.fieldCurrent
    exciter.flimf = 0.0
    exciter.kc = 0.08
    exciter.kd = 0.03
    exciter.ke = 1.0
    exciter.kefd = 0.1
    exciter.kf = 0.05
    exciter.kh = 0.2
    exciter.kii = 0.5
    exciter.kip = 1.0
    exciter.ks = 1.0
    exciter.kvi = 0.5
    exciter.kvp = 2.0
    exciter.kvphz = 0.1
    exciter.nvphz = 0.9
    exciter.se1 = 0.1
    exciter.se2 = 0.2
    exciter.ta = 0.1
    exciter.tb1 = 0.2
    exciter.tb2 = 0.3
    exciter.tc1 = 0.05
    exciter.tc2 = 0.08
    exciter.te = 0.5
    exciter.tf = 0.4
    exciter.tf1 = 0.1
    exciter.tf2 = 0.2
    exciter.tp = 0.15
    exciter.vcmax = 2.0
    exciter.vfmax = 5.0
    exciter.vfmin = -5.0
    exciter.vimax = 5.0
    exciter.vrmax = 5.0
    exciter.vrmin = -5.0
    exciter.xc = 0.1
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_rexs_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_rexs_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_rexs_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcREXS'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('ExcREXS.')
    assert find_block_variable_by_name(
        composite_template.block,
        f'VRefPu_ExcREXS_ExcREXS_{exciter.uuid}',
    ) is not None
    for port_name in (
        'VcPu', 'VtermPu', 'ItermRePu', 'ItermImPu', 'VsPu', 'IfdPu', 'SpeedPu',
    ):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcREXS_ExcREXS_{exciter.uuid}',
        ) is None
    for port_name in ('VuelPu', 'VoelPu'):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcREXS_ExcREXS_{exciter.uuid}',
        ) is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_exc_st2a_equations_map_rdf_fields_and_reduce_zero_times() -> None:
    """Check ExcST2A equations, exact RDF mappings, and zero-time stages.

    :return: None.
    """
    settings: ExcST2AParameters = ExcST2AParameters(
        ka=120.0, ta=0.15, vrmax=2.0, vrmin=-2.0, ke=1.0, te=0.5,
        kf=0.05, tf=0.7, kp=4.88, ki=8.0, kc=0.12, efdmax=4.0,
        uelin=True, tb=0.2, tc=0.05,
    )
    template: RmsModelTemplate = build_exc_s_t2_a_template(
        VarFactory(), 'ExcST2A_equation_check', settings,
    )
    assert len(template.block.event_dict) == 16
    assert len(template.block.in_vars) == 9
    assert len(template.block.out_vars) == 1
    assert len(template.block.state_vars) == 4
    equation_variables: set[int] = set()
    for equation in template.block.state_eqs + template.block.algebraic_eqs:
        for variable in equation.get_vars():
            equation_variables.add(variable.uid)
    for parameter_variable in template.block.event_dict:
        if parameter_variable.name.startswith('ExcST2A.enabled_'):
            pass
        else:
            assert parameter_variable.uid in equation_variables

    exciter: ExcST2A = ExcST2A(rdfid='_exc_st2a_mapping')
    exciter.ka = settings.ka
    exciter.ta = settings.ta
    exciter.vrmax = settings.vrmax
    exciter.vrmin = settings.vrmin
    exciter.ke = settings.ke
    exciter.te = settings.te
    exciter.kf = settings.kf
    exciter.tf = settings.tf
    exciter.kp = settings.kp
    exciter.ki = settings.ki
    exciter.kc = settings.kc
    exciter.efdmax = settings.efdmax
    exciter.uelin = settings.uelin
    exciter.tb = settings.tb
    exciter.tc = settings.tc
    mapped_template: RmsModelTemplate = build_exc_s_t2_a_template(
        VarFactory(), 'ExcST2A_mapping_check', settings,
    )
    copy_cgmes_parameters(exciter, mapped_template, VarFactory())
    mapped_values: dict[str, object] = dict()
    for variable, value in mapped_template.block.event_dict.items():
        mapped_values[variable.name] = value
    expected_values: tuple[tuple[str, float], ...] = (
        ('ka', settings.ka), ('ta', settings.ta), ('vrmax', settings.vrmax),
        ('vrmin', settings.vrmin), ('ke', settings.ke), ('te', settings.te),
        ('kf', settings.kf), ('tf', settings.tf), ('kp', settings.kp),
        ('ki', settings.ki), ('kc', settings.kc), ('efdmax', settings.efdmax),
        ('tb', settings.tb), ('tc', settings.tc), ('uelin', 1.0),
    )
    for parameter_name, expected_value in expected_values:
        assert mapped_values[f'ExcST2A.{parameter_name}_ExcST2A_mapping_check'].value == expected_value

    zero_time_template: RmsModelTemplate = build_exc_s_t2_a_template(
        VarFactory(),
        'ExcST2A_zero_time',
        ExcST2AParameters(ta=0.0, tf=0.0, kf=0.0, tb=0.0, tc=0.0),
    )
    assert len(zero_time_template.block.state_vars) == 1
    with pytest.raises(ValueError, match='lead Tc requires positive lag Tb'):
        build_exc_s_t2_a_template(
            VarFactory(), 'ExcST2A_invalid_lead', ExcST2AParameters(tb=0.0, tc=0.1),
        )


def test_exc_st2a_import_composes_and_initializes_detailed_machine() -> None:
    """Associate ExcST2A to its machine and assert the composed initial state.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_exc_st2a_bus')
    exciter: ExcST2A = ExcST2A(rdfid='_detailed_exc_st2a_exciter')
    stabilizer: PssIEEE1A = PssIEEE1A(rdfid='_detailed_exc_st2a_stabilizer')
    voltage_compensator: VCompIEEEType1 = VCompIEEEType1(
        rdfid='_detailed_exc_st2a_voltage_compensator',
    )
    voltage_compensator.rc = 0.02
    voltage_compensator.xc = 0.04
    voltage_compensator.tr = 0.0
    stabilizer.inputSignalType = InputSignalKind.rotorSpeed
    exciter.ka = 120.0
    exciter.ta = 0.15
    exciter.vrmax = 2.0
    exciter.vrmin = -2.0
    exciter.ke = 1.0
    exciter.te = 0.5
    exciter.kf = 0.05
    exciter.tf = 0.7
    exciter.kp = 4.88
    exciter.ki = 8.0
    exciter.kc = 0.12
    exciter.efdmax = 4.0
    exciter.uelin = False
    exciter.tb = 0.2
    exciter.tc = 0.05
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_exc_st2a_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_exc_st2a_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_exc_st2a_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    exciter.PowerSystemStabilizerDynamics = stabilizer
    voltage_compensator.ExcitationSystemDynamics = exciter
    stabilizer.ExcitationSystemDynamics = exciter
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcST2A'].append(exciter)
    cgmes_model.dynamics_assets.lists['PssIEEE1A'].append(stabilizer)
    cgmes_model.dynamics_assets.lists['VCompIEEEType1'].append(voltage_compensator)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(machine_dynamics)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert composite_template.comment.endswith('exciter and PSS.')
    assert find_block_variable_by_name(
        composite_template.block,
        f'VRefPu_ExcST2A_{exciter.uuid}',
    ) is not None
    for port_name in (
        'VsPu', 'VuelPu', 'VmPu', 'VrPu', 'ViPu', 'IrPu', 'IiPu', 'IfdPu',
    ):
        assert find_block_variable_by_name(
            composite_template.block,
            f'{port_name}_ExcST2A_{exciter.uuid}',
        ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'EfdPu_ExcST2A_{exciter.uuid}',
    ) is not None
    assert find_block_variable_by_name(
        composite_template.block,
        f'SignalPu_PssIEEE1A_{stabilizer.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VsPu_ExcST2A_{exciter.uuid}',
    ) is None
    assert find_block_variable_by_name(
        composite_template.block,
        f'VcPu_VCompIEEEType1_{voltage_compensator.uuid}',
    ) is None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_vcomp_ieee_type2_composes_with_exc_st2a_voltage_port() -> None:
    """Connect Type 2 compensation to ExcST2A's canonical ``VmPu`` port.

    :return: None.
    """
    machine_template: RmsModelTemplate = RmsModelTemplate(name='machine')
    machine_block: Block = Block(name='machine')
    machine_block.out_vars = list((Var('Vm'), Var('Va')))
    machine_template.block = machine_block

    exciter_template: RmsModelTemplate = RmsModelTemplate(name='ExcST2A_fixture')
    exciter_block: Block = Block(name='ExcST2A_fixture')
    exciter_block.in_vars = list((Var('VmPu_ExcST2A_fixture'),))
    exciter_template.block = exciter_block
    machine_template.block.children.append(exciter_block)

    compensator_template: RmsModelTemplate = RmsModelTemplate(name='VCompIEEEType2_fixture')
    compensator_block: Block = Block(name='VCompIEEEType2_fixture')
    compensator_block.in_vars = list((
        Var('VtRePu_VCompIEEEType2_fixture'),
        Var('VtImPu_VCompIEEEType2_fixture'),
    ))
    compensator_block.out_vars = list((Var('UsPu_VCompIEEEType2_fixture'),))
    compensator_template.block = compensator_block

    composite_template, unsupported_ports = compose_machine_with_vcomp_ieee_type2(
        machine_template=machine_template,
        exciter_template=exciter_template,
        compensator_template=compensator_template,
        remote_currents=tuple(),
    )

    assert composite_template is not None, unsupported_ports
    assert unsupported_ports == tuple()


def test_exc_st6b_import_composes_with_direct_axis_machine_at_nonzero_power() -> None:
    """Check ExcST6B machine association and operating-point residuals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_cgmes_st6b_bus')
    exciter: ExcST6B = ExcST6B(rdfid='_detailed_cgmes_st6b_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_cgmes_st6b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_cgmes_st6b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_cgmes_st6b_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcST6B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_ExcST6B_' in composite_template.name
    assert find_block_variable_by_name(composite_template.block, 'IfdPu') is not None
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_pfvar_type1_var_controller_composes_with_adjuster_and_exciter() -> None:
    """Check RDF-linked Type I VAr control initializes with a detailed machine.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='cgmes_pfvar_type1_bus')
    exciter: ExcAC1A = ExcAC1A(rdfid='_cgmes_pfvar_type1_exciter')
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_cgmes_pfvar_type1_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_cgmes_pfvar_type1_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='cgmes_pfvar_type1_generator')
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    controller: PFVArType1IEEEPFController = PFVArType1IEEEPFController(
        rdfid='_cgmes_pfvar_type1_controller',
    )
    controller.ovex = False
    controller.tpfc = 5.0
    controller.vitmin = 0.1
    controller.vpf = 0.9805806756909201
    controller.vpfcbw = 0.02
    controller.vpfref = 0.9805806756909201
    controller.vvtmax = 1.05
    controller.vvtmin = 0.95
    adjuster: VAdjIEEE = VAdjIEEE(rdfid='_cgmes_pfvar_type1_adjuster')
    adjuster.vadjf = 1.0
    adjuster.adjslew = 300.0
    adjuster.vadjmax = 1.1
    adjuster.vadjmin = 0.9
    adjuster.taon = 0.1
    adjuster.taoff = 0.5
    controller.ExcitationSystemDynamics = exciter
    controller.VoltageAdjusterDynamics = adjuster
    exciter.PFVArControllerType1Dynamics = controller
    adjuster.PFVArControllerType1Dynamics = controller
    cgmes_model.dynamics_assets.lists['ExcAC1A'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['PFVArType1IEEEPFController'].append(controller)
    cgmes_model.dynamics_assets.lists['VAdjIEEE'].append(adjuster)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_PFVArType1IEEEPFController_' in composite_template.name
    assert 'VAdjIEEE' in composite_template.name
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.02,
            VarPowerFlowReferenceType.Va: 0.05,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )


def test_underexc_lim_ieee2_import_composes_with_st7b_and_machine() -> None:
    """Check UEL2 RDF associations, ST7B feedback, and composed initial residuals.

    :return: None.
    """
    cgmes_model: CgmesCircuit = CgmesCircuit()
    veragrid_model: MultiCircuit = MultiCircuit(Sbase=100.0)
    logger: DataLogger = DataLogger()
    bus: Bus = Bus(name='detailed_uel2_st7b_bus')
    exciter: ExcST7B = ExcST7B(rdfid='_detailed_uel2_st7b_exciter')
    exciter.uelin = ExcST7BUELselectorKind.inputHVgate
    machine_dynamics: SynchronousMachineTimeConstantReactance = (
        SynchronousMachineTimeConstantReactance(rdfid='_detailed_uel2_st7b_machine_dynamics')
    )
    machine_dynamics.rotorType = RotorKind.salientPole
    machine_dynamics.modelType = SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
    machine_dynamics.ifdBaseType = IfdBaseKind.ifag
    machine_dynamics.ifdBaseValue = 37.5
    machine_dynamics.inertia = 4.0
    machine_dynamics.damping = 0.0
    machine_dynamics.statorLeakageReactance = 0.12
    machine_dynamics.statorResistance = 0.003
    machine_dynamics.saturationFactor = 0.1
    machine_dynamics.saturationFactor120 = 0.2
    machine_dynamics.saturationFactorQAxis = 0.15
    machine_dynamics.saturationFactor120QAxis = 0.25
    machine_dynamics.efdBaseRatio = 1.1
    machine_dynamics.xDirectSync = 1.8
    machine_dynamics.xDirectTrans = 0.3
    machine_dynamics.xDirectSubtrans = 0.2
    machine_dynamics.xQuadSync = 1.7
    machine_dynamics.xQuadTrans = 0.55
    machine_dynamics.xQuadSubtrans = 0.2
    machine_dynamics.tpdo = 5.0
    machine_dynamics.tppdo = 0.04
    machine_dynamics.tpqo = 0.7
    machine_dynamics.tppqo = 0.05
    machine: CgmesSynchronousMachine = CgmesSynchronousMachine(rdfid='_detailed_uel2_st7b_machine')
    machine.ratedS = 100.0
    machine.ratedPowerFactor = 1.0
    generator: Generator = Generator(idtag=machine.uuid, name='detailed_uel2_st7b_generator')
    limiter: UnderexcLimIEEE2 = UnderexcLimIEEE2(rdfid='_detailed_uel2_limiter')
    limiter.kui = 0.0
    limiter.kul = 0.0
    limiter.kuf = 0.0
    limiter.kfb = 1.0
    exciter.SynchronousMachineDynamics = machine_dynamics
    machine_dynamics.SynchronousMachine = machine
    machine_dynamics.ExcitationSystemDynamics = exciter
    exciter.SynchronousMachineDynamics = machine_dynamics
    exciter.UnderexcitationLimiterDynamics = limiter
    limiter.ExcitationSystemDynamics = exciter
    cgmes_model.dynamics_assets.lists['ExcST7B'].append(exciter)
    cgmes_model.dynamics_assets.lists['SynchronousMachineTimeConstantReactance'].append(
        machine_dynamics,
    )
    cgmes_model.dynamics_assets.lists['UnderexcLimIEEE2'].append(limiter)
    veragrid_model.add_bus(bus)
    veragrid_model.add_generator(bus=bus, api_obj=generator)
    assert find_veragrid_devices(limiter, {machine.uuid: generator}) == [generator]

    convert_cgmes_dynamics(cgmes_model, veragrid_model, logger)

    composite_template: RmsModelTemplate | None = generator.rms_template
    assert composite_template is not None
    assert '_with_UnderexcLimIEEE2_' in composite_template.name, [entry.msg for entry in logger.entries]
    assert any(
        variable.name.startswith('VuelPu_UnderexcLimIEEE2_')
        for runtime_block in composite_template.block.get_all_blocks()
        for variable in runtime_block.out_vars
    )
    assert_zero_initial_residuals(
        composite_template,
        {
            VarPowerFlowReferenceType.Vm: 1.0,
            VarPowerFlowReferenceType.Va: 0.0,
            VarPowerFlowReferenceType.P: 0.5,
            VarPowerFlowReferenceType.Q: 0.1,
        },
    )
