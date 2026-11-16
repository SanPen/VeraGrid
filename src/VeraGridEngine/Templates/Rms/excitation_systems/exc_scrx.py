# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES ExcSCRX controlled-rectifier excitation model."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Templates.Rms.excitation_systems.scrx import build_scrx_template


def build_exc_s_c_r_x_template(vfactory: VarFactory, name: str | None = None) -> RmsModelTemplate:
    """Build the standalone ExcSCRX parameter template.

    :param vfactory: Factory used to allocate the template parameters.
    :param name: Optional runtime model name.
    :return: Model-specific template retaining this class parameter surface.
    """
    parameters: tuple[str, ...] = ('enabled', 'tatb', 'tb', 'k', 'te', 'emin', 'emax', 'cswitch', 'rcrfd')
    template_name: str = 'ExcSCRX' if name is None else name
    parameter_block: Block = Block(name=f"{template_name}_CGMES_parameters")
    for parameter_name in parameters:
        variable_name: str = f"ExcSCRX.{parameter_name}_{template_name}"
        parameter_variable = vfactory.add_var(variable_name)
        parameter_block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    runtime_template = build_scrx_template(vf=vfactory, name=template_name)
    runtime_template.block.children.append(parameter_block)
    runtime_template.block.name = template_name
    runtime_template.comment = "CGMES ExcSCRX equations: voltage error, lead-lag, bounded regulator, source selection, and field discharge."
    return runtime_template
