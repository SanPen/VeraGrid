# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Standalone equation blocks for CGMES dynamic models."""

from VeraGridEngine.Templates.Rms.induction_machines.asynchronous_machine_time_constant_reactance import build_asynchronous_machine_time_constant_reactance_template
from VeraGridEngine.Templates.Rms.excitation_limiters.disc_exc_cont_ieee_dec1_a import build_disc_exc_cont_i_e_e_e_d_e_c1_a_template
from VeraGridEngine.Templates.Rms.excitation_limiters.disc_exc_cont_ieee_dec2_a import build_disc_exc_cont_i_e_e_e_d_e_c2_a_template
from VeraGridEngine.Templates.Rms.excitation_limiters.disc_exc_cont_ieee_dec3_a import build_disc_exc_cont_i_e_e_e_d_e_c3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac1a import build_exc_a_c1_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac2a import build_exc_a_c2_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac3a import build_exc_a_c3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac4a import build_exc_a_c4_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac5a import build_exc_a_c5_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac6a import build_exc_a_c6_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ac8b import build_exc_a_c8_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ans import build_exc_a_n_s_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr1 import build_exc_a_v_r1_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr2 import build_exc_a_v_r2_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr3 import build_exc_a_v_r3_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr4 import build_exc_a_v_r4_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr5 import build_exc_a_v_r5_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_avr7 import build_exc_a_v_r7_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_bbc import build_exc_b_b_c_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_cz import build_exc_c_z_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc1a import build_exc_d_c1_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc2a import build_exc_d_c2_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc3a import build_exc_d_c3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_dc3a1 import build_exc_d_c3_a1_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_elin1 import build_exc_e_l_i_n1_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_elin2 import build_exc_e_l_i_n2_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_hu import build_exc_h_u_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac1a import build_exc_i_e_e_e_a_c1_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac2a import build_exc_i_e_e_e_a_c2_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac3a import build_exc_i_e_e_e_a_c3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac4a import build_exc_i_e_e_e_a_c4_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_ac5a import build_exc_i_e_e_e_a_c5_a_template
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
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st3a import build_exc_i_e_e_e_s_t3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st4b import build_exc_i_e_e_e_s_t4_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st5b import build_exc_i_e_e_e_s_t5_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st6b import build_exc_i_e_e_e_s_t6_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ieee_st7b import build_exc_i_e_e_e_s_t7_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_ni import build_exc_n_i_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_oex3_t import (
    ExcOEX3TParameters,
    build_exc_o_e_x3_t_template,
)
from VeraGridEngine.Templates.Rms.excitation_systems.exc_pic import build_exc_p_i_c_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_rexs import build_exc_r_e_x_s_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_rqb import build_exc_r_q_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_scrx import build_exc_s_c_r_x_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_sexs import build_exc_s_e_x_s_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_sk import build_exc_s_k_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st1a import build_exc_s_t1_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st2a import build_exc_s_t2_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st3a import build_exc_s_t3_a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st4b import build_exc_s_t4_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st6b import build_exc_s_t6_b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exc_st7b import build_exc_s_t7_b_template
from VeraGridEngine.Templates.Rms.governors.gov_c_t1 import build_gov_c_t1_template
from VeraGridEngine.Templates.Rms.governors.gov_c_t2 import build_gov_c_t2_template
from VeraGridEngine.Templates.Rms.governors.gov_gast import build_gov_g_a_s_t_template
from VeraGridEngine.Templates.Rms.governors.gov_gast1 import build_gov_g_a_s_t1_template
from VeraGridEngine.Templates.Rms.governors.gov_gast2 import build_gov_g_a_s_t2_template
from VeraGridEngine.Templates.Rms.governors.gov_gast3 import build_gov_g_a_s_t3_template
from VeraGridEngine.Templates.Rms.governors.gov_gast4 import build_gov_g_a_s_t4_template
from VeraGridEngine.Templates.Rms.governors.gov_gast_wd import build_gov_g_a_s_t_w_d_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro1 import build_gov_hydro1_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro2 import build_gov_hydro2_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro3 import build_gov_hydro3_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro4 import build_gov_hydro4_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_d_d import build_gov_hydro_d_d_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_francis import build_gov_hydro_francis_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_ieee0 import build_gov_hydro_i_e_e_e0_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_ieee2 import build_gov_hydro_i_e_e_e2_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pid import build_gov_hydro_p_i_d_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pid2 import build_gov_hydro_p_i_d2_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_pelton import build_gov_hydro_pelton_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_r import build_gov_hydro_r_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_weh import build_gov_hydro_w_e_h_template
from VeraGridEngine.Templates.Rms.governors.gov_hydro_w_pid import build_gov_hydro_w_p_i_d_template
from VeraGridEngine.Templates.Rms.governors.gov_steam0 import build_gov_steam0_template
from VeraGridEngine.Templates.Rms.governors.gov_steam1 import build_gov_steam1_template
from VeraGridEngine.Templates.Rms.governors.gov_steam2 import build_gov_steam2_template
from VeraGridEngine.Templates.Rms.governors.gov_steam_bb import build_gov_steam_b_b_template
from VeraGridEngine.Templates.Rms.governors.gov_steam_cc import build_gov_steam_c_c_template
from VeraGridEngine.Templates.Rms.governors.gov_steam_e_u import build_gov_steam_e_u_template
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
from VeraGridEngine.Templates.Rms.governors.gov_steam_ieee1 import build_gov_steam_i_e_e_e1_template
from VeraGridEngine.Templates.Rms.governors.gov_steam_sgo import (
    GovSteamSGOParameters,
    build_gov_steam_s_g_o_template,
)
from VeraGridEngine.Templates.Rms.load_characteristics.load_composite import build_load_composite_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_generic_non_linear import build_load_generic_non_linear_template
from VeraGridEngine.Templates.Rms.induction_machines.load_motor import build_load_motor_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_static import build_load_static_template
from VeraGridEngine.Templates.Rms.common.mech_load1 import build_mech_load1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.overexc_lim2 import build_overexc_lim2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.overexc_lim_ieee import build_overexc_lim_i_e_e_e_template
from VeraGridEngine.Templates.Rms.excitation_limiters.overexc_lim_x1 import build_overexc_lim_x1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.overexc_lim_x2 import build_overexc_lim_x2_template
from VeraGridEngine.Templates.Rms.voltage_compensators.p_f_v_ar_type1_ieee_p_f_controller import build_p_f_v_ar_type1_i_e_e_e_p_f_controller_template
from VeraGridEngine.Templates.Rms.voltage_compensators.p_f_v_ar_type1_ieee_v_ar_controller import build_p_f_v_ar_type1_i_e_e_e_v_ar_controller_template
from VeraGridEngine.Templates.Rms.voltage_compensators.p_f_v_ar_type2_common1 import build_p_f_v_ar_type2_common1_template
from VeraGridEngine.Templates.Rms.voltage_compensators.p_f_v_ar_type2_ieee_p_f_controller import build_p_f_v_ar_type2_i_e_e_e_p_f_controller_template
from VeraGridEngine.Templates.Rms.voltage_compensators.p_f_v_ar_type2_ieee_v_ar_controller import build_p_f_v_ar_type2_i_e_e_e_v_ar_controller_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1 import build_pss1_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1_a import build_pss1_a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2_b import build_pss2_b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2_s_t import build_pss2_s_t_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss5 import build_pss5_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_elin2 import build_pss_e_l_i_n2_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ieee1a import build_pss_i_e_e_e1_a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ieee2b import build_pss_i_e_e_e2_b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ieee3b import build_pss_i_e_e_e3_b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ieee4b import build_pss_i_e_e_e4_b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ptist1 import build_pss_p_t_i_s_t1_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_ptist3 import build_pss_p_t_i_s_t3_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_rqb import build_pss_r_q_b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_sb4 import build_pss_s_b4_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_sh import build_pss_s_h_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_sk import build_pss_s_k_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_stab2a import build_pss_s_t_a_b2_a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss_wecc import build_pss_w_e_c_c_template
from VeraGridEngine.Templates.Rms.synchronous_machines.synchronous_machine_simplified import build_synchronous_machine_simplified_template
from VeraGridEngine.Templates.Rms.synchronous_machines.synchronous_machine_time_constant_reactance import build_synchronous_machine_time_constant_reactance_template
from VeraGridEngine.Templates.Rms.governors.turb_lcfb1 import build_turb_l_c_f_b1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim2_simplified import build_underexc_lim2_simplified_template
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_ieee1 import build_underexc_lim_i_e_e_e1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_ieee2 import build_underexc_lim_i_e_e_e2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_x1 import build_underexc_lim_x1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.underexc_lim_x2 import build_underexc_lim_x2_template
from VeraGridEngine.Templates.Rms.voltage_compensators.v_adj_ieee import build_v_adj_i_e_e_e_template
from VeraGridEngine.Templates.Rms.voltage_compensators.v_comp_ieee_type1 import build_v_comp_i_e_e_e_type1_template
from VeraGridEngine.Templates.Rms.voltage_compensators.v_comp_ieee_type2 import build_v_comp_i_e_e_e_type2_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_aero_one_dim_iec import build_wind_aero_one_dim_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_aero_two_dim_iec import build_wind_aero_two_dim_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_aero_linear_iec import build_wind_aero_linear_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_curr_lim_iec import build_wind_cont_curr_lim_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_p_type3_iec import build_wind_cont_p_type3_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_p_type4a_iec import build_wind_cont_p_type4a_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_p_type4b_iec import build_wind_cont_p_type4b_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_pitch_angle_iec import build_wind_cont_pitch_angle_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_q_iec import build_wind_cont_q_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_q_p_q_u_lim_iec import build_wind_cont_q_p_q_u_lim_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_cont_rotor_r_iec import build_wind_cont_rotor_r_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_gen_type3a_iec import build_wind_gen_type3a_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_gen_type3b_iec import build_wind_gen_type3b_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_gen_type4_iec import build_wind_gen_type4_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_mech_iec import build_wind_mech_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_pitch_cont_power_iec import build_wind_pitch_cont_power_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_pitch_cont_emul_iec import build_wind_pitch_cont_emul_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_plant_freq_pcontrol_iec import build_wind_plant_freq_pcontrol_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_plant_reactive_control_iec import (
    WindPlantReactiveControlMode,
    build_wind_plant_reactive_control_i_e_c_template,
)
from VeraGridEngine.Templates.Rms.wind_generation.wind_protection_iec import build_wind_protection_i_e_c_template
from VeraGridEngine.Templates.Rms.wind_generation.wind_ref_frame_rot_iec import build_wind_ref_frame_rot_i_e_c_template

def get_international_model_builders() -> dict[str, object]:
    """Return the canonical international RMS builder registry.

    :return: Canonical model names mapped to their statically imported builders.
    """
    builders: dict[str, object] = dict(
        AsynchronousMachineTimeConstantReactance=build_asynchronous_machine_time_constant_reactance_template,
        DiscExcContIEEEDEC1A=build_disc_exc_cont_i_e_e_e_d_e_c1_a_template,
        DiscExcContIEEEDEC2A=build_disc_exc_cont_i_e_e_e_d_e_c2_a_template,
        DiscExcContIEEEDEC3A=build_disc_exc_cont_i_e_e_e_d_e_c3_a_template,
        ExcAC1A=build_exc_a_c1_a_template,
        ExcAC2A=build_exc_a_c2_a_template,
        ExcAC3A=build_exc_a_c3_a_template,
        ExcAC4A=build_exc_a_c4_a_template,
        ExcAC5A=build_exc_a_c5_a_template,
        ExcAC6A=build_exc_a_c6_a_template,
        ExcAC8B=build_exc_a_c8_b_template,
        ExcANS=build_exc_a_n_s_template,
        ExcAVR1=build_exc_a_v_r1_template,
        ExcAVR2=build_exc_a_v_r2_template,
        ExcAVR3=build_exc_a_v_r3_template,
        ExcAVR4=build_exc_a_v_r4_template,
        ExcAVR5=build_exc_a_v_r5_template,
        ExcAVR7=build_exc_a_v_r7_template,
        ExcBBC=build_exc_b_b_c_template,
        ExcCZ=build_exc_c_z_template,
        ExcDC1A=build_exc_d_c1_a_template,
        ExcDC2A=build_exc_d_c2_a_template,
        ExcDC3A=build_exc_d_c3_a_template,
        ExcDC3A1=build_exc_d_c3_a1_template,
        ExcELIN1=build_exc_e_l_i_n1_template,
        ExcELIN2=build_exc_e_l_i_n2_template,
        ExcHU=build_exc_h_u_template,
        ExcIEEEAC1A=build_exc_i_e_e_e_a_c1_a_template,
        ExcIEEEAC2A=build_exc_i_e_e_e_a_c2_a_template,
        ExcIEEEAC3A=build_exc_i_e_e_e_a_c3_a_template,
        ExcIEEEAC4A=build_exc_i_e_e_e_a_c4_a_template,
        ExcIEEEAC5A=build_exc_i_e_e_e_a_c5_a_template,
        ExcIEEEAC6A=build_exc_i_e_e_e_a_c6_a_template,
        ExcIEEEAC7B=build_exc_i_e_e_e_a_c7_b_template,
        ExcIEEEAC8B=build_exc_i_e_e_e_a_c8_b_template,
        ExcIEEEDC1A=build_exc_i_e_e_e_d_c1_a_template,
        ExcIEEEDC2A=build_exc_i_e_e_e_d_c2_a_template,
        ExcIEEEDC3A=build_exc_i_e_e_e_d_c3_a_template,
        ExcIEEEDC4B=build_exc_i_e_e_e_d_c4_b_template,
        ExcIEEEST1A=build_exc_i_e_e_e_s_t1_a_template,
        ExcIEEEST2A=build_exc_i_e_e_e_s_t2_a_template,
        ExcIEEEST3A=build_exc_i_e_e_e_s_t3_a_template,
        ExcIEEEST4B=build_exc_i_e_e_e_s_t4_b_template,
        ExcIEEEST5B=build_exc_i_e_e_e_s_t5_b_template,
        ExcIEEEST6B=build_exc_i_e_e_e_s_t6_b_template,
        ExcIEEEST7B=build_exc_i_e_e_e_s_t7_b_template,
        ExcNI=build_exc_n_i_template,
        ExcOEX3T=build_exc_o_e_x3_t_template,
        ExcPIC=build_exc_p_i_c_template,
        ExcREXS=build_exc_r_e_x_s_template,
        ExcRQB=build_exc_r_q_b_template,
        ExcSCRX=build_exc_s_c_r_x_template,
        ExcSEXS=build_exc_s_e_x_s_template,
        ExcSK=build_exc_s_k_template,
        ExcST1A=build_exc_s_t1_a_template,
        ExcST2A=build_exc_s_t2_a_template,
        ExcST3A=build_exc_s_t3_a_template,
        ExcST4B=build_exc_s_t4_b_template,
        ExcST6B=build_exc_s_t6_b_template,
        ExcST7B=build_exc_s_t7_b_template,
        GovCT1=build_gov_c_t1_template,
        GovCT2=build_gov_c_t2_template,
        GovGAST=build_gov_g_a_s_t_template,
        GovGAST1=build_gov_g_a_s_t1_template,
        GovGAST2=build_gov_g_a_s_t2_template,
        GovGAST3=build_gov_g_a_s_t3_template,
        GovGAST4=build_gov_g_a_s_t4_template,
        GovGASTWD=build_gov_g_a_s_t_w_d_template,
        GovHydro1=build_gov_hydro1_template,
        GovHydro2=build_gov_hydro2_template,
        GovHydro3=build_gov_hydro3_template,
        GovHydro4=build_gov_hydro4_template,
        GovHydroDD=build_gov_hydro_d_d_template,
        GovHydroFrancis=build_gov_hydro_francis_template,
        GovHydroIEEE0=build_gov_hydro_i_e_e_e0_template,
        GovHydroIEEE2=build_gov_hydro_i_e_e_e2_template,
        GovHydroPID=build_gov_hydro_p_i_d_template,
        GovHydroPID2=build_gov_hydro_p_i_d2_template,
        GovHydroPelton=build_gov_hydro_pelton_template,
        GovHydroR=build_gov_hydro_r_template,
        GovHydroWEH=build_gov_hydro_w_e_h_template,
        GovHydroWPID=build_gov_hydro_w_p_i_d_template,
        GovSteam0=build_gov_steam0_template,
        GovSteam1=build_gov_steam1_template,
        GovSteam2=build_gov_steam2_template,
        GovSteamBB=build_gov_steam_b_b_template,
        GovSteamCC=build_gov_steam_c_c_template,
        GovSteamEU=build_gov_steam_e_u_template,
        GovSteamFV2=build_gov_steam_f_v2_template,
        GovSteamFV3=build_gov_steam_f_v3_template,
        GovSteamFV4=build_gov_steam_f_v4_template,
        GovSteamIEEE1=build_gov_steam_i_e_e_e1_template,
        GovSteamSGO=build_gov_steam_s_g_o_template,
        LoadComposite=build_load_composite_template,
        LoadGenericNonLinear=build_load_generic_non_linear_template,
        LoadMotor=build_load_motor_template,
        LoadStatic=build_load_static_template,
        MechLoad1=build_mech_load1_template,
        OverexcLim2=build_overexc_lim2_template,
        OverexcLimIEEE=build_overexc_lim_i_e_e_e_template,
        OverexcLimX1=build_overexc_lim_x1_template,
        OverexcLimX2=build_overexc_lim_x2_template,
        PFVArType1IEEEPFController=build_p_f_v_ar_type1_i_e_e_e_p_f_controller_template,
        PFVArType1IEEEVArController=build_p_f_v_ar_type1_i_e_e_e_v_ar_controller_template,
        PFVArType2Common1=build_p_f_v_ar_type2_common1_template,
        PFVArType2IEEEPFController=build_p_f_v_ar_type2_i_e_e_e_p_f_controller_template,
        PFVArType2IEEEVArController=build_p_f_v_ar_type2_i_e_e_e_v_ar_controller_template,
        Pss1=build_pss1_template,
        Pss1A=build_pss1_a_template,
        Pss2B=build_pss2_b_template,
        Pss2ST=build_pss2_s_t_template,
        Pss5=build_pss5_template,
        PssELIN2=build_pss_e_l_i_n2_template,
        PssIEEE1A=build_pss_i_e_e_e1_a_template,
        PssIEEE2B=build_pss_i_e_e_e2_b_template,
        PssIEEE3B=build_pss_i_e_e_e3_b_template,
        PssIEEE4B=build_pss_i_e_e_e4_b_template,
        PssPTIST1=build_pss_p_t_i_s_t1_template,
        PssPTIST3=build_pss_p_t_i_s_t3_template,
        PssRQB=build_pss_r_q_b_template,
        PssSB4=build_pss_s_b4_template,
        PssSH=build_pss_s_h_template,
        PssSK=build_pss_s_k_template,
        PssSTAB2A=build_pss_s_t_a_b2_a_template,
        PssWECC=build_pss_w_e_c_c_template,
        SynchronousMachineSimplified=build_synchronous_machine_simplified_template,
        SynchronousMachineTimeConstantReactance=build_synchronous_machine_time_constant_reactance_template,
        TurbLCFB1=build_turb_l_c_f_b1_template,
        UnderexcLim2Simplified=build_underexc_lim2_simplified_template,
        UnderexcLimIEEE1=build_underexc_lim_i_e_e_e1_template,
        UnderexcLimIEEE2=build_underexc_lim_i_e_e_e2_template,
        UnderexcLimX1=build_underexc_lim_x1_template,
        UnderexcLimX2=build_underexc_lim_x2_template,
        VAdjIEEE=build_v_adj_i_e_e_e_template,
        VCompIEEEType1=build_v_comp_i_e_e_e_type1_template,
        VCompIEEEType2=build_v_comp_i_e_e_e_type2_template,
        WindAeroOneDimIEC=build_wind_aero_one_dim_i_e_c_template,
        WindAeroLinearIEC=build_wind_aero_linear_i_e_c_template,
        WindAeroTwoDimIEC=build_wind_aero_two_dim_i_e_c_template,
        WindContCurrLimIEC=build_wind_cont_curr_lim_i_e_c_template,
        WindContPType3IEC=build_wind_cont_p_type3_i_e_c_template,
        WindContPType4aIEC=build_wind_cont_p_type4a_i_e_c_template,
        WindContPType4bIEC=build_wind_cont_p_type4b_i_e_c_template,
        WindContPitchAngleIEC=build_wind_cont_pitch_angle_i_e_c_template,
        WindContQIEC=build_wind_cont_q_i_e_c_template,
        WindContQPQULimIEC=build_wind_cont_q_p_q_u_lim_i_e_c_template,
        WindContRotorRIEC=build_wind_cont_rotor_r_i_e_c_template,
        WindGenType3aIEC=build_wind_gen_type3a_i_e_c_template,
        WindGenType3bIEC=build_wind_gen_type3b_i_e_c_template,
        WindGenTurbineType3aIEC=build_wind_gen_type3a_i_e_c_template,
        WindGenType4IEC=build_wind_gen_type4_i_e_c_template,
        WindMechIEC=build_wind_mech_i_e_c_template,
        WindPitchContPowerIEC=build_wind_pitch_cont_power_i_e_c_template,
        WindPitchContEmulIEC=build_wind_pitch_cont_emul_i_e_c_template,
        WindPlantFreqPcontrolIEC=build_wind_plant_freq_pcontrol_i_e_c_template,
        WindPlantReactiveControlIEC=build_wind_plant_reactive_control_i_e_c_template,
        WindProtectionIEC=build_wind_protection_i_e_c_template,
        WindRefFrameRotIEC=build_wind_ref_frame_rot_i_e_c_template,
    )
    return builders
