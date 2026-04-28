# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Templates.Emt.bus_emt_template import BusEmtTemplate

from VeraGridEngine.Templates.Emt.load_RLC_emt_template import (get_shunt_c_emt_template,
                                                                get_shunt_l_emt_template,
                                                                get_shunt_r_emt_template, )
from VeraGridEngine.Templates.Emt.generator_emt_type_template import (get_simple_generator_emt_template,
                                                                      get_generator_sauer_pai_type_emt_template,
                                                                      get_exciter_emt,
                                                                      get_governor_emt,
                                                                      get_stabilizer_emt,
                                                                      get_complete_generator_template_emt)
from VeraGridEngine.Templates.Emt.load_exponential_emt_template import get_exponential_load_emt
from VeraGridEngine.Templates.Emt.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.Templates.Emt.thevenin_equivalent_emt_generator_template import get_generator_thevenin_rl_emt_template
from VeraGridEngine.Templates.Emt.converter_emt_template import get_emt_ideal_converter, get_full_pseudo_emt_converter
from VeraGridEngine.Templates.Emt.converter_switched_emt_template import get_switched_emt_converter
from VeraGridEngine.Templates.Emt.bridge_2level_3ph_emt_template import get_bridge_2level_3ph_emt_template
from VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_template import get_bridge_filter_2level_3ph_emt_template
from VeraGridEngine.Templates.Emt.bridge_filter_control_2level_3ph_emt_template import get_bridge_filter_control_2level_3ph_emt_template
from VeraGridEngine.Templates.Emt.dc_load_emt_template import get_dc_load_emt_template
from VeraGridEngine.Templates.Emt.dc_line_emt_template import get_dc_line_emt_template
from VeraGridEngine.Templates.Emt.valve_emt_template import get_valve_emt_template
from VeraGridEngine.Templates.Emt.transformer_emt_template import get_transformer_emt_template
from VeraGridEngine.Templates.Emt.xfmr_emt_template import get_xfmr_emt_template

# the following are functions that generate templates depending on the specific object

from VeraGridEngine.Templates.Emt.bergeron_line_emt_template import get_bergeron_line_emt_template
from VeraGridEngine.Templates.Emt.pi_line_emt_template import get_pi_line_emt_template
# from VeraGridEngine.Templates.Emt.transformer_emt_template import get_transformer_emt_template
# from VeraGridEngine.Templates.Emt.xfmr_emt_template import get_xfmr_emt_template

