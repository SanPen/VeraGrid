# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType


def get_empty_emt_template(vf: VarFactory, name: str = "empty_template") -> EmtModelTemplate:
    """
    EMT empty template. Used to empty the block
    :param vf: grid.var_factory
    :param name: string to identify the model
    :return: EmtModelTemplate
    """

    templ = EmtModelTemplate()
    templ.name = name
    templ.block.name = name
    templ.tpe = DeviceType.NoDevice
    templ.block = Block()

    return templ