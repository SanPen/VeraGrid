# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

# from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_exc_gov_sat_template import get_complete_generator_template_rms, get_genqec_rms, get_governor_rms, get_stabilizer_rms, get_exciter_rms
from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_exc_gov_sat_template_v2 import get_complete_generator_template_rms, get_genqec_rms, get_governor_rms, get_stabilizer_rms, get_exciter_rms
from VeraGridEngine.Templates.Rms.synchronous_machines.gencls_rms_template import get_gencls_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow_rms_template import get_genrow_rms_template
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template, get_dc_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.bus_phasor_rms_template import initialize_bus_phasor_rms
from VeraGridEngine.Templates.Rms.line.line_phasor_rms_template import get_line_phasor_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_phasor_current_rms_template import get_load_phasor_current_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_phasor_rms_template import get_complete_generator_template_phasor
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template_legacy import initialize_trafo_rms
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_phasor_rms_template import get_genqec_phasor
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvd1_rms_template import get_pvd1_rms_template, get_pvd1_complete_rms_template, get_pvd1_dc_mppt_rms_template, get_pvd1_dc_link_mppt_rms_template, get_pvd1_dc_link_bess_rms_template
from VeraGridEngine.Templates.Rms.battery_energy_storage.esd1_rms_template import get_esd1_rms_template
from VeraGridEngine.Templates.Rms.common.voltage_source_template import VoltageSourceBuild
from VeraGridEngine.Templates.Rms.converters.vsc_gfl_dclinked import build_vsc_rms
from VeraGridEngine.Templates.Rms.converters.hvdc_vsc_gfl_rms_template_v2 import (
    HvdcVscGflRmsTemplate,
    VscActiveControlRmsTemplate,
    VscReactiveControlRmsTemplate,
    build_hvdc_vsc_gfl_rms,
    build_vsc_pll_rms,
    build_vsc_electrical_rms,
    build_vsc_active_control_rms,
    build_vsc_reactive_control_rms,
    build_vsc_current_limiter_rms,
    build_vsc_vd_hat_rms,
    build_vsc_vq_hat_rms,
    build_vsc_dc_link_rms,
    get_hvdc_vdc_q_vsc_rms,
    get_hvdc_pdc_q_vsc_rms,
)
from VeraGridEngine.Templates.Rms.dc_line.dc_line_rms_template_v2 import DcLineRmsTemplateV2, build_dc_line_rms_v2
from VeraGridEngine.Templates.Rms.dc_line.dc_voltage_source import DCPVSourceAveraged
from VeraGridEngine.Templates.Rms.common.basic_devices import get_pll_transform_rms, get_pi_current_controller, get_pi_power_controller, get_gfl_converter_rms
from VeraGridEngine.Templates.Rms.common.empty_rms_template import get_empty_rms_template


from VeraGridEngine.Templates.Rms.excitation_systems.ac1a import build_ac1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac1c import build_ac1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac2c import build_ac2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac4c import build_ac4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac5c import build_ac5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc2c import build_dc2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc3a import build_dc3a_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc4c import build_dc4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc4b import build_dc4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6a import build_ac6a_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c import build_ac6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac7b import build_ac7b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac7c import build_ac7c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8b import build_ac8b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8c import build_ac8c_template
from VeraGridEngine.Templates.Rms.excitation_systems.bbsex1 import build_bbsex1_template
from VeraGridEngine.Templates.Rms.battery_energy_storage.besscbcurrentsourcenoplantcontrol import build_besscbcurrentsourcenoplantcontrol_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc1a import build_dc1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc1c import build_dc1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac1 import build_exac1_template
from VeraGridEngine.Templates.Rms.governors.ivogo import build_ivogo_template
from VeraGridEngine.Templates.Rms.governors.degov import build_degov_template
from VeraGridEngine.Templates.Rms.governors.degov1d import build_degov1d_template
from VeraGridEngine.Templates.Rms.governors.degov1 import build_degov1_template
from VeraGridEngine.Templates.Rms.governors.govhydro4 import build_govhydro4_template
from VeraGridEngine.Templates.Rms.governors.govsteam1 import build_govsteam1_template
from VeraGridEngine.Templates.Rms.governors.govsteameu import build_govsteameu_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1 import build_ieeeg1_template
from VeraGridEngine.Templates.Rms.governors.ieeeg2 import build_ieeeg2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet1 import build_ieeet1_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex2 import build_ieeex2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieex2a import build_ieex2a_template
from VeraGridEngine.Templates.Rms.excitation_limiters.maxex2 import build_maxex2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel2c import build_oel2c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel3c import build_oel3c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel4c import build_oel4c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel5c import build_oel5c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ivost import build_ivost_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1aomega import build_pss1aomega_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1apgen import build_pss1apgen_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2a import build_pss2a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2b import build_pss2b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2c import build_pss2c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss3b import build_pss3b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss3c import build_pss3c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss6c import build_pss6c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.psskundur import build_psskundur_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvcurrentsourcebnoplantcontrol import build_pvcurrentsourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvvoltagesourceanoplantcontrol import build_pvvoltagesourceanoplantcontrol_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvvoltagesourcebnoplantcontrol import build_pvvoltagesourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.renewable_controls.reecb import build_reecb_template
from VeraGridEngine.Templates.Rms.renewable_controls.reecc import build_reecc_template
from VeraGridEngine.Templates.Rms.renewable_controls.regcbcs import build_regcbcs_template
from VeraGridEngine.Templates.Rms.renewable_controls.repca import build_repca_template
from VeraGridEngine.Templates.Rms.excitation_limiters.scl1c import build_scl1c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.scl2c import build_scl2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.scrx import build_scrx_template
from VeraGridEngine.Templates.Rms.excitation_systems.sexs import build_sexs_template
from VeraGridEngine.Templates.Rms.excitation_systems.st1a import build_st1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.st1c import build_st1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st4b import build_st4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st4c import build_st4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st5b import build_st5b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st5c import build_st5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st6b import build_st6b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st6c import build_st6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st7b import build_st7b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st7c import build_st7c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st9c import build_st9c_template
from VeraGridEngine.Templates.Rms.governors.tgov3 import build_tgov3_template
from VeraGridEngine.Templates.Rms.governors.tgov2 import build_tgov2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.uel1 import build_uel1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.uel2c import build_uel2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.vrkundur import build_vrkundur_template
from VeraGridEngine.Templates.Rms.wind_generation.wpp4bcurrentsource2020 import build_wpp4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4acurrentsource import build_wt4acurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4acurrentsource2020 import build_wt4acurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4bcurrentsource2020 import build_wt4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4bcurrentsource import build_wt4bcurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4injector import build_wt4injector_template
from VeraGridEngine.Templates.Rms.wind_generation.wtg4acurrentsource import build_wtg4acurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wtg4bcurrentsource import build_wtg4bcurrentsource_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeevc_1981 import build_ieeevc_1981_template
from VeraGridEngine.Templates.Rms.excitation_systems.esdc2a import build_esdc2a_template
from VeraGridEngine.Templates.Rms.protection_relays.frqtpa import build_frqtpa_template
from VeraGridEngine.Templates.Rms.protection_relays.vtgtpa import build_vtgtpa_template
from VeraGridEngine.Templates.Rms.protection_relays.frqtpat import build_frqtpat_template
from VeraGridEngine.Templates.Rms.protection_relays.vtgtpat import build_vtgtpat_template
from VeraGridEngine.Templates.Rms.induction_machines.cimtr1 import build_cimtr1_template
from VeraGridEngine.Templates.Rms.induction_machines.cimw import build_cimw_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gensal import build_gensal_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou import build_genrou_template
from VeraGridEngine.Templates.Rms.governors.ggov1 import build_ggov1_template
from VeraGridEngine.Templates.Rms.governors.hygov import build_hygov_template
from VeraGridEngine.Templates.Rms.governors.hygovr1 import build_hygovr1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.ieel import build_ieel_template
from VeraGridEngine.Templates.Rms.governors.tgov1 import build_tgov1_template

from VeraGridEngine.Templates.Rms.excitation_systems.ieet1b import build_ieet1b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exni import build_exni_template
from VeraGridEngine.Templates.Rms.excitation_systems.expic1 import build_expic1_template

import keyword
import re

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import InternationalStandardModel
from VeraGridEngine.Utils.Symbolic.symbolic import Var

from VeraGridEngine.Templates.Rms.excitation_systems.ac1a import build_ac1a_template
from VeraGridEngine.Templates.Rms.auxiliary_signals.cpaaut import build_cpaaut_template
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import build_wt12t1_drive_train_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac1c import build_ac1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6a import build_ac6a_template, build_esac6a_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c import build_ac6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c2 import build_ac6c2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac7b import build_ac7b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac7c import build_ac7c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8b import build_ac8b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac8c import build_ac8c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c import build_ac9c_controller_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac11c import build_ac11c_template
from VeraGridEngine.Templates.Rms.excitation_systems.bbsex1 import build_bbsex1_template
from VeraGridEngine.Templates.Rms.battery_energy_storage.besscbcurrentsourcenoplantcontrol import build_besscbcurrentsourcenoplantcontrol_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc1a import build_dc1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc1c import build_dc1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac1 import build_exac1_template
from VeraGridEngine.Templates.Rms.common.brushless_exciter import build_brushless_exciter_base
from VeraGridEngine.Templates.Rms.governors.ivogo import build_ivogo_template
from VeraGridEngine.Templates.Rms.governors.degov import build_degov_template
from VeraGridEngine.Templates.Rms.governors.degov1d import build_degov1d_template
from VeraGridEngine.Templates.Rms.governors.degov1 import build_degov1_template
from VeraGridEngine.Templates.Rms.governors.govhydro4 import build_govhydro4_template
from VeraGridEngine.Templates.Rms.governors.govsteam1 import build_govsteam1_template
from VeraGridEngine.Templates.Rms.governors.govsteameu import build_govsteameu_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1 import build_ieeeg1_template
from VeraGridEngine.Templates.Rms.governors.ieeeg1d import build_ieeeg1d_template
from VeraGridEngine.Templates.Rms.governors.lcfb1 import build_lcfb1_template
from VeraGridEngine.Templates.Rms.governors.ieeeg2 import build_ieeeg2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet1 import build_ieeet1_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet2 import build_ieeet2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1 import build_ieeex1_template
from VeraGridEngine.Templates.Rms.excitation_systems.esdc1a import build_esdc1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exdc2 import build_exdc2_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac5a import build_esac5a_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac8b import build_esac8b_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc2c import build_dc2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc3a import build_dc3a_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc4c import build_dc4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.dc4b import build_dc4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac4c import build_ac4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac2c import build_ac2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac3c import build_ac3c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ac5c import build_ac5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet3 import build_ieeet3_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex3 import build_ieeex3_template
from VeraGridEngine.Templates.Rms.excitation_systems.esst1a import build_esst1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.budczt import build_budczt_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac4 import build_exac4_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac4a import build_esac4a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac1a import build_exac1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac1a import build_esac1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac2 import build_exac2_template
from VeraGridEngine.Templates.Rms.excitation_systems.exac3 import build_exac3_template
from VeraGridEngine.Templates.Rms.excitation_systems.exbas import build_exbas_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieet1a import build_ieet1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieet1b import build_ieet1b_template
from VeraGridEngine.Templates.Rms.excitation_systems.exni import build_exni_template
from VeraGridEngine.Templates.Rms.excitation_systems.expic1 import build_expic1_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet4 import build_ieeet4_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeet5 import build_ieeet5_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex4 import build_ieeex4_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieet5a import build_ieet5a_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac2a import build_esac2a_template
from VeraGridEngine.Templates.Rms.excitation_systems.esac3a import build_esac3a_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex2 import build_ieeex2_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieex2a import build_ieex2a_template
from VeraGridEngine.Templates.Rms.excitation_limiters.maxex2 import build_maxex2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel2c import build_oel2c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel3c import build_oel3c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel4c import build_oel4c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.oel5c import build_oel5c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ivost import build_ivost_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ostb2t import build_ostb2t_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.bepsst import build_bepsst_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1aomega import build_pss1aomega_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import build_ieeest_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1a import build_pss1a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss4b import build_pss4b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.iee2st import build_iee2st_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss1apgen import build_pss1apgen_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2a import build_pss2a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2b import build_pss2b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2c import build_pss2c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss3b import build_pss3b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss3c import build_pss3c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss6c import build_pss6c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss7c import build_pss7c_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerParameters
from VeraGridEngine.Templates.Rms.power_system_stabilizers.psskundur import build_psskundur_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvcurrentsourcebnoplantcontrol import build_pvcurrentsourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvvoltagesourceanoplantcontrol import build_pvvoltagesourceanoplantcontrol_template
from VeraGridEngine.Templates.Rms.solar_pv_generation.pvvoltagesourcebnoplantcontrol import build_pvvoltagesourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.renewable_controls.reecb import build_reecb_template
from VeraGridEngine.Templates.Rms.renewable_controls.reecc import build_reecc_template
from VeraGridEngine.Templates.Rms.renewable_controls.regcbcs import build_regcbcs_template
from VeraGridEngine.Templates.Rms.renewable_controls.repca import build_repca_template
from VeraGridEngine.Templates.Rms.excitation_limiters.scl1c import build_scl1c_template
from VeraGridEngine.Templates.Rms.excitation_limiters.scl2c import build_scl2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.scrx import build_scrx_template
from VeraGridEngine.Templates.Rms.excitation_systems.sexs import build_sexs_template
from VeraGridEngine.Templates.Rms.excitation_systems.st1a import build_st1a_template
from VeraGridEngine.Templates.Rms.excitation_systems.st1c import build_st1c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st4b import build_st4b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st4c import build_st4c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st5b import build_st5b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st5c import build_st5c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st6b import build_st6b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st6c import build_st6c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st7b import build_st7b_template
from VeraGridEngine.Templates.Rms.excitation_systems.st7c import build_st7c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st8c import build_st8c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st9c import build_st9c_template
from VeraGridEngine.Templates.Rms.excitation_systems.st10c import build_st10c_template
from VeraGridEngine.Templates.Rms.governors.tgov3 import build_tgov3_template
from VeraGridEngine.Templates.Rms.governors.tgov2 import build_tgov2_template
from VeraGridEngine.Templates.Rms.governors.tgov4 import build_tgov4_thermal_train
from VeraGridEngine.Templates.Rms.excitation_limiters.uel1 import build_uel1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.uel2c import build_uel2c_template
from VeraGridEngine.Templates.Rms.excitation_systems.vrkundur import build_vrkundur_template
from VeraGridEngine.Templates.Rms.wind_generation.wpp4bcurrentsource2020 import build_wpp4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4acurrentsource import build_wt4acurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4acurrentsource2020 import build_wt4acurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4bcurrentsource2020 import build_wt4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4bcurrentsource import build_wt4bcurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wt4injector import build_wt4injector_template
from VeraGridEngine.Templates.Rms.wind_generation.wtg4acurrentsource import build_wtg4acurrentsource_template
from VeraGridEngine.Templates.Rms.wind_generation.wtg4bcurrentsource import build_wtg4bcurrentsource_template
from VeraGridEngine.Templates.Rms.excitation_systems.ieeevc_1981 import build_ieeevc_1981_template
from VeraGridEngine.Templates.Rms.excitation_systems.esdc2a import build_esdc2a_template
from VeraGridEngine.Templates.Rms.protection_relays.frqtpat import build_frqtpat_template
from VeraGridEngine.Templates.Rms.protection_relays.vtgtpat import build_vtgtpat_template
from VeraGridEngine.Templates.Rms.protection_relays.frqtpa import build_frqtpa_template
from VeraGridEngine.Templates.Rms.protection_relays.vtgtpa import build_vtgtpa_template
from VeraGridEngine.Templates.Rms.induction_machines.cimtr1 import build_cimtr1_template
from VeraGridEngine.Templates.Rms.induction_machines.cimtr2 import build_cimtr2_template
from VeraGridEngine.Templates.Rms.induction_machines.cimtr3 import build_cimtr3_template
from VeraGridEngine.Templates.Rms.induction_machines.cimtr4 import build_cimtr4_template
from VeraGridEngine.Templates.Rms.induction_machines.cimw import build_cimw_template
from VeraGridEngine.Templates.Rms.induction_machines.psse_cim_motor import (
    build_cim5_template,
    build_cim6_template,
)
from VeraGridEngine.Templates.Rms.induction_machines.psse_cim_motor import (
    PsseCimMotorModel,
    PsseCimMotorParameters,
    PsseCimMotorType,
    build_psse_cim_motor_template,
    calculate_cimw_c0,
)
from VeraGridEngine.Templates.Rms.synchronous_machines.gensal import build_gensal_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou import build_genrou_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gentra import build_gentra_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genroe import build_genroe_template
from VeraGridEngine.Templates.Rms.synchronous_machines.gensae import build_gensae_template
from VeraGridEngine.Templates.Rms.governors.ggov1 import build_ggov1_template
from VeraGridEngine.Templates.Rms.governors.ggov1d import build_ggov1d_template
from VeraGridEngine.Templates.Rms.governors.bbgov1 import build_bbgov1_template
from VeraGridEngine.Templates.Rms.governors.hygov import build_hygov_template
from VeraGridEngine.Templates.Rms.excitation_limiters.ieel import build_ieel_template
from VeraGridEngine.Templates.Rms.governors.tgov1 import build_tgov1_template
from VeraGridEngine.Templates.Rms.governors.gastd import build_gastd_template
from VeraGridEngine.Templates.Rms.governors.ieesgod import build_ieesgod_template
from VeraGridEngine.Templates.Rms.governors.hygovd import build_hygovd_template
from VeraGridEngine.Templates.Rms.governors.hygov2 import build_hygov2_template
from VeraGridEngine.Templates.Rms.governors.hygovr1 import build_hygovr1_template
from VeraGridEngine.Templates.Rms.governors.hygov2d import build_hygov2d_template
from VeraGridEngine.Templates.Rms.governors.pidgov import build_pidgov_template
from VeraGridEngine.Templates.Rms.governors.pidgovd import build_pidgovd_template
from VeraGridEngine.Templates.Rms.governors.tgov1d import build_tgov1d_template
from VeraGridEngine.Templates.Rms.governors.gast import build_gast_template
from VeraGridEngine.Templates.Rms.governors.gast2a import build_gast2a_template
from VeraGridEngine.Templates.Rms.governors.ieeeg3 import build_ieeeg3_template
from VeraGridEngine.Templates.Rms.governors.ieeeg3d import build_ieeeg3d_template
from VeraGridEngine.Templates.Rms.governors.ieesgo import build_ieesgo_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab1 import build_stab1_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab2a import build_stab2a_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab3 import build_stab3_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stab4 import build_stab4_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.stabni import build_stabni_template
from VeraGridEngine.Templates.Rms.voltage_compensators.comp import build_comp_template
from VeraGridEngine.Templates.Rms.voltage_compensators.compcc import build_compcc_template
from VeraGridEngine.Templates.Rms.voltage_compensators.ccomp4a import build_ccomp4a_template
from VeraGridEngine.Templates.Rms.voltage_compensators.remcmp import build_remcmp_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex1 import build_mnlex1_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex2 import build_mnlex2_template
from VeraGridEngine.Templates.Rms.excitation_limiters.mnlex3 import build_mnlex3_template
from VeraGridEngine.Templates.Rms.excitation_systems.exst2 import build_exst2_template
from VeraGridEngine.Templates.Rms.excitation_systems.exst2a import build_exst2a_template
from VeraGridEngine.Templates.Rms.excitation_systems.esst2a import build_esst2a_template


def _build_python_identifier(source_name: str) -> str:
    """Convert one imported Modelica symbol name into a Python identifier.

    The Dynamic Block Properties editor serializes symbolic equations as
    Python source. Modelica hierarchy separators, array indices and generated
    names such as ``$START`` therefore need a stable identifier spelling.

    :param source_name: Symbol name emitted by the Modelica importer.
    :return: Python-compatible spelling of the same symbolic name.
    """
    identifier: str = re.sub(r"[^0-9A-Za-z_]", "_", source_name)
    identifier = re.sub(r"_+", "_", identifier)

    # Keep even unusual generated names representable in editable source.
    if len(identifier) == 0:
        identifier = "variable"
    else:
        pass

    if identifier[0].isdigit() or keyword.iskeyword(identifier):
        identifier = f"variable_{identifier}"
    else:
        pass

    return identifier


def get_international_model_builders() -> dict[str, object]:
    """Return builders for imported international standard models.

    :return: International model names mapped to their template builders.
    """
    from VeraGridEngine.Templates.Rms.international_models import (
        get_international_model_builders as get_builders,
    )

    return get_builders()


def _normalize_imported_variable_names(
        vf: VarFactory,
        existing_variable_uids: set[int],
) -> None:
    """Normalize only the variables allocated by one imported template.

    Symbolic identity is UID-based, so changing a variable's serialization
    name leaves the equations unchanged. Existing editor variables are kept
    untouched, and deterministic suffixes avoid collisions after punctuation
    is converted to underscores.

    :param vf: Factory containing both existing and newly imported variables.
    :param existing_variable_uids: Stable identities present before import.
    :return: None.
    """
    all_variables: list[Var] = list()
    new_variables: list[Var] = list()
    seen_variable_uids: set[int] = set()
    occupied_names: set[str] = set()
    variable_uid: int
    variable: Var

    # Differential variables can live in their own factory registry. Merge
    # both registries once while retaining their stable insertion order.
    for variable_uid, variable in vf.get_vars_dict().items():
        if variable_uid not in seen_variable_uids:
            all_variables.append(variable)
            seen_variable_uids.add(variable_uid)
        else:
            pass

    for variable_uid, variable in vf.get_diff_var_dict().items():
        if variable_uid not in seen_variable_uids:
            all_variables.append(variable)
            seen_variable_uids.add(variable_uid)
        else:
            pass

    # Reserve the spellings owned by the editor before this model was added.
    for variable in all_variables:
        if variable.non_mutable_uid in existing_variable_uids:
            occupied_names.add(variable.name)
        else:
            new_variables.append(variable)

    # Rename the imported surface without changing any symbolic UID links.
    for variable in new_variables:
        base_identifier: str = _build_python_identifier(variable.name)
        unique_identifier: str = base_identifier
        suffix: int = 2
        while unique_identifier in occupied_names:
            unique_identifier = f"{base_identifier}_{suffix}"
            suffix += 1

        variable.set_name(unique_identifier)
        occupied_names.add(unique_identifier)


def build_international_standard_template(
        model: InternationalStandardModel,
        vf: VarFactory,
        name: str | None = None,
) -> RmsModelTemplate:
    """
    Materialize one international-standard dynamic model without function pointers.

    :param model: Enumerated dynamic model to materialize.
    :type model: InternationalStandardModel
    :param vf: Variable factory that owns the symbolic variables.
    :type vf: VarFactory
    :param name: Optional runtime instance name.
    :type name: str | None
    :return: Materialized international-standard RMS dynamic template.
    :rtype: RmsModelTemplate
    """
    template: RmsModelTemplate
    existing_variable_uids: set[int] = set(vf.get_vars_dict().keys())
    existing_variable_uids.update(vf.get_diff_var_dict().keys())

    # Dispatch explicitly so every supported state is visible and statically imported.
    if model == InternationalStandardModel.AC1A:
        template = build_ac1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC1C:
        template = build_ac1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC6A:
        template = build_ac6a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC6A:
        template = build_esac6a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC6C:
        template = build_ac6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC6C2:
        template = build_ac6c2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC7B:
        template = build_ac7b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC7C:
        template = build_ac7c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC8B:
        template = build_ac8b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC8C:
        template = build_ac8c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC9C:
        template = build_ac9c_controller_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC11C:
        template = build_ac11c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BBSEX1:
        template = build_bbsex1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL:
        template = build_besscbcurrentsourcenoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BBGOV1:
        template = build_bbgov1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC1A:
        template = build_dc1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC1C:
        template = build_dc1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC1:
        template = build_brushless_exciter_base(vf, 'EXAC1' if name is None else name)
    elif model == InternationalStandardModel.GOVHYDRO4:
        template = build_govhydro4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GOVSTEAM1:
        template = build_govsteam1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GOVSTEAMEU:
        template = build_govsteameu_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IVOGO:
        template = build_ivogo_template(vf, name)
    elif model == InternationalStandardModel.DEGOV:
        template = build_degov_template(vf, name)
    elif model == InternationalStandardModel.DEGOV1D:
        template = build_degov1d_template(vf, name)
    elif model == InternationalStandardModel.DEGOV1:
        template = build_degov1_template(vf, name)
    elif model == InternationalStandardModel.IEEEG1:
        template = build_ieeeg1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEG1D:
        template = build_ieeeg1d_template(vf=vf, name=name)
    elif model == InternationalStandardModel.LCFB1:
        template = build_lcfb1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEG2:
        template = build_ieeeg2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET1:
        template = build_ieeet1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET2:
        template = build_ieeet2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEX1:
        template = build_ieeex1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESDC1A:
        template = build_esdc1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXDC2:
        template = build_exdc2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEX2:
        template = build_ieeex2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEX2A:
        template = build_ieex2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.MAXEX2:
        template = build_maxex2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL2C:
        template = build_oel2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL3C:
        template = build_oel3c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL4C:
        template = build_oel4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL5C:
        template = build_oel5c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS1AOMEGA:
        template = build_pss1aomega_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS1APGEN:
        template = build_pss1apgen_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2A:
        template = build_pss2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2B:
        template = build_pss2b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2C:
        template = build_pss2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS3B:
        template = build_pss3b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS3C:
        template = build_pss3c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS6C:
        template = build_pss6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS7C:
        template = build_pss7c_template(vf=vf, name='PSS7C' if name is None else name,
            parameters=RampStabilizerParameters(),
            canonical_gains=(1.0,1.0,1.0,1.0,1.0), canonical_times=(1.0,1.0,1.0,1.0),
            canonical_stage_gains=(1.0,1.0), pss_on=-1.0, pss_off=0.0, xcomp=0.0, tcomp=1.0)
    elif model == InternationalStandardModel.PSSKUNDUR:
        template = build_psskundur_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL:
        template = build_pvcurrentsourcebnoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL:
        template = build_pvvoltagesourceanoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL:
        template = build_pvvoltagesourcebnoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REECB:
        template = build_reecb_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REECC:
        template = build_reecc_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REGCBCS:
        template = build_regcbcs_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REPCA:
        template = build_repca_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCL1C:
        template = build_scl1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCL2C:
        template = build_scl2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCRX:
        template = build_scrx_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SEXS:
        template = build_sexs_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST1A:
        template = build_st1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST1C:
        template = build_st1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST4B:
        template = build_st4b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST4C:
        template = build_st4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST5B:
        template = build_st5b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST5C:
        template = build_st5c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST6B:
        template = build_st6b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST6C:
        template = build_st6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST7B:
        template = build_st7b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST7C:
        template = build_st7c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST8C:
        template = build_st8c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST9C:
        template = build_st9c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST10C:
        template = build_st10c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV2:
        template = build_tgov2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV3:
        template = build_tgov3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV4:
        template = build_tgov4_thermal_train(
            vf=vf, name='TGOV4' if name is None else name,
        )
    elif model == InternationalStandardModel.UEL1:
        template = build_uel1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.UEL2C:
        template = build_uel2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.VRKUNDUR:
        template = build_vrkundur_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WPP4BCURRENTSOURCE2020:
        template = build_wpp4bcurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE:
        template = build_wt4acurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE2020:
        template = build_wt4acurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE2020:
        template = build_wt4bcurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE:
        template = build_wt4bcurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4INJECTOR:
        template = build_wt4injector_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WTG4ACURRENTSOURCE:
        template = build_wtg4acurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WTG4BCURRENTSOURCE:
        template = build_wtg4bcurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEVC_1981:
        template = build_ieeevc_1981_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESDC2A:
        template = build_esdc2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.FRQTPA:
        template = build_frqtpa_template(vf=vf, name=name)
    elif model == InternationalStandardModel.VTGTPA:
        template = build_vtgtpa_template(vf=vf, name=name)
    elif model == InternationalStandardModel.FRQTPAT:
        template = build_frqtpat_template(vf=vf, name=name)
    elif model == InternationalStandardModel.VTGTPAT:
        template = build_vtgtpat_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMTR1:
        template = build_cimtr1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMTR2:
        template = build_cimtr2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMTR3:
        template = build_cimtr3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMTR4:
        template = build_cimtr4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIM5:
        template = build_cim5_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIM6:
        template = build_cim6_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMW:
        template = build_cimw_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENSAL:
        template = build_gensal_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENROU:
        template = build_genrou_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENTRA:
        template = build_gentra_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENROE:
        template = build_genroe_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GGOV1D:
        template = build_ggov1d_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GASTD:
        template = build_gastd_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEESGOD:
        template = build_ieesgod_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOV2:
        template = build_hygov2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOVR1:
        template = build_hygovr1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PIDGOV:
        template = build_pidgov_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PIDGOVD:
        template = build_pidgovd_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOV2D:
        template = build_hygov2d_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOVD:
        template = build_hygovd_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV1D:
        template = build_tgov1d_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GGOV1:
        template = build_ggov1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOV:
        template = build_hygov_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEL:
        template = build_ieel_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV1:
        template = build_tgov1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GAST:
        template = build_gast_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GAST2A:
        template = build_gast2a_template(
            vf=vf, name='GAST2A' if name is None else name,
        )
    elif model == InternationalStandardModel.IEEEG3:
        template = build_ieeeg3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEG3D:
        template = build_ieeeg3d_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEESGO:
        template = build_ieesgo_template(vf=vf, name=name)
    elif model == InternationalStandardModel.STAB1:
        template = build_stab1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.STAB2A:
        template = build_stab2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.STAB3:
        template = build_stab3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.STAB4:
        template = build_stab4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IVOST:
        template = build_ivost_template(vf, name)
    elif model == InternationalStandardModel.STABNI:
        template = build_stabni_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEST:
        template = build_ieeest_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BEPSST:
        template = build_bepsst_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OSTB2T:
        template = build_ostb2t_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OSTB5T:
        template = build_ostb2t_template(vf=vf, name='OSTB5T' if name is None else name)
    elif model == InternationalStandardModel.PSS1A:
        template = build_pss1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS4B:
        template = build_pss4b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEE2ST:
        template = build_iee2st_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BUDCZT:
        template = build_budczt_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESST1A:
        template = build_esst1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET3:
        template = build_ieeet3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEX3:
        template = build_ieeex3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC4C:
        template = build_dc4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC4B:
        template = build_dc4b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC3A:
        template = build_dc3a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC2C:
        template = build_dc2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC8B:
        template = build_esac8b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC5A:
        template = build_esac5a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC4:
        template = build_exac4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC5C:
        template = build_ac5c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC2C:
        template = build_ac2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC3C:
        template = build_ac3c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC4C:
        template = build_ac4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC4A:
        template = build_esac4a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENSAE:
        template = build_gensae_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC1A:
        template = build_exac1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC1A:
        template = build_esac1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC2:
        template = build_exac2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC3:
        template = build_exac3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXBAS:
        template = build_exbas_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXPIC1:
        template = build_expic1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXNI:
        template = build_exni_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEET1B:
        template = build_ieet1b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEET1A:
        template = build_ieet1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET4:
        template = build_ieeet4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET5:
        template = build_ieeet5_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEX4:
        template = build_ieeex4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEET5A:
        template = build_ieet5a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC2A:
        template = build_esac2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESAC3A:
        template = build_esac3a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.COMP:
        template = build_comp_template(vf=vf, name=name)
    elif model == InternationalStandardModel.COMPCC:
        template = build_compcc_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CCOMP4A:
        template = build_ccomp4a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CPAAUT:
        template = build_cpaaut_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT12T1:
        template = build_wt12t1_drive_train_template(
            vf=vf, name='WT12T1 drive train' if name is None else name,
        )
    elif model == InternationalStandardModel.REMCMP:
        template = build_remcmp_template(vf=vf, name=name)
    elif model == InternationalStandardModel.MNLEX1:
        template = build_mnlex1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.MNLEX2:
        template = build_mnlex2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.MNLEX3:
        template = build_mnlex3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXST2A:
        template = build_exst2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESST2A:
        template = build_esst2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXST2:
        template = build_exst2_template(vf=vf, name=name)
    else:
        from VeraGridEngine.Templates.Rms.international_models import (
            get_international_model_builders,
        )

        international_model_builders: dict[str, object] = get_international_model_builders()
        builder: object | None = international_model_builders.get(model.name, None)
        if builder is None:
            raise ValueError(f"Unsupported international-standard model: {model!s}")
        else:
            template = builder(vfactory=vf, name=name)

    # Imported Modelica names contain hierarchy and index punctuation that is
    # not valid in the editor's Python equation representation.
    _normalize_imported_variable_names(
        vf=vf,
        existing_variable_uids=existing_variable_uids,
    )

    return template
