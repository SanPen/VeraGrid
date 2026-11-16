# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES PssIEEE2B stabilizer template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.power_system_stabilizers.pss2b import build_pss2b_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerParameters, StabilizerInterface


def build_pss_i_e_e_e2_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: RampStabilizerParameters | None = None,
) -> RmsModelTemplate:
    """Build PssIEEE2B equations and retain the RDF parameter names.

    :param vfactory: Factory used to allocate the template symbols.
    :param name: Optional unique runtime instance name.
    :param parameters: Parsed CGMES values used to select exact bypass stages.
    :return: Executable two-input PSS with an open pair of measurement ports.
    """
    template_name: str = "PssIEEE2B" if name is None else name
    template: RmsModelTemplate = build_pss2b_template(
        vf=vfactory,
        name=template_name,
        parameters=parameters,
        interface=StabilizerInterface.SELECTED_SIGNALS,
    )
    template.comment = (
        "CGMES PssIEEE2B: clipped dual input, four washouts, T6/T7 lags, "
        "ramp tracking, three lead-lag stages, and output clipping."
    )

    # Keep the original scalar names for inspectable, lossless CGMES import.
    parameter_names: tuple[str, ...] = (
        'vsi1max', 'vsi1min', 'tw1', 'tw2', 'vsi2max', 'vsi2min', 'tw3', 'tw4',
        't1', 't2', 't3', 't4', 't6', 't7', 't8', 't9', 't10', 't11',
        'ks1', 'ks2', 'ks3', 'n', 'm', 'vstmax', 'vstmin',
    )
    for parameter_name in parameter_names:
        variable_name: str = f"PssIEEE2B.{parameter_name}_{template_name}"
        parameter_variable = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
