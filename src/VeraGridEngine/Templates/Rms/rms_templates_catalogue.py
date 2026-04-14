# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import List, Dict

from VeraGridEngine.enumerations import DeviceType

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.Rms.bus_rms_template import BusRmsTemplate
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import GenqecExcGovSat
from VeraGridEngine.Templates.Rms.generator_rms_template import get_generator_rms_template
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import LoadRmsTemplate

templ_bus = BusRmsTemplate()

templ_genqec = GenqecExcGovSat()

templ_gen_0 = get_generator_rms_template()
templ_gen_1 = get_generator_rms_template()

templ_line_0 = get_line_rms_template()
templ_line_1 = get_line_rms_template()

templ_load = LoadRmsTemplate()

Templates: List[RmsModelTemplate] = [templ_bus, templ_genqec, templ_gen_0, templ_gen_1, templ_line_0, templ_line_1,
                                     templ_load]


def get_generator_catalogue() -> tuple[List[str], Dict[str, RmsModelTemplate]]:
    """

    :return:
    """
    generator_templ_catalogue = dict()
    generator_templ_list = []
    for templ in Templates:
        if templ.tpe == DeviceType.GeneratorDevice:
            generator_templ_list.append(templ.name)
            generator_templ_catalogue[templ.name] = templ

    return generator_templ_list, generator_templ_catalogue


def get_bus_catalogue() -> tuple[List[str], Dict[str, RmsModelTemplate]]:
    bus_templ_catalogue = dict()
    bus_templ_list = []
    for templ in Templates:
        if templ.tpe == DeviceType.BusDevice:
            bus_templ_list.append(templ.name)
            bus_templ_catalogue[templ.name] = templ

    return bus_templ_list, bus_templ_catalogue


def get_line_catalogue() -> tuple[List[str], Dict[str, RmsModelTemplate]]:
    line_templ_catalogue = dict()
    line_templ_list = []
    for templ in Templates:
        if templ.tpe == DeviceType.LineDevice:
            line_templ_list.append(templ.name)
            line_templ_catalogue[templ.name] = templ

    return line_templ_list, line_templ_catalogue


def get_load_catalogue() -> tuple[List[str], Dict[str, RmsModelTemplate]]:
    load_templ_catalogue = dict()
    load_templ_list = []
    for templ in Templates:
        if templ.tpe == DeviceType.LoadDevice:
            load_templ_list.append(templ.name)
            load_templ_catalogue[templ.name] = templ

    return load_templ_list, load_templ_catalogue
