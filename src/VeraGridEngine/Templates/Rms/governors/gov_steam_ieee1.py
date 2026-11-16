# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamIEEE1 steam governor template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.ieeeg1 import (
    MultiStageSteamGovernorParameters,
    build_ieeeg1_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def build_gov_steam_i_e_e_e1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: MultiStageSteamGovernorParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES parameter surface around the matching IEEE G1 equations.

    :param vfactory: Factory that owns equation and RDF symbols.
    :param name: Optional instance label used in all runtime symbols.
    :param parameters: IEEE G1 valve, speed, and turbine-stage values.
    :return: Equation-backed governor retaining the canonical CGMES fields.
    """
    template_name: str = "GovSteamIEEE1" if name is None else name
    template: RmsModelTemplate = build_ieeeg1_template(
        vf=vfactory,
        name=template_name,
        parameters=parameters,
    )
    cgmes_parameters: tuple[str, ...] = (
        "enabled", "mwbase", "k", "t1", "t2", "t3", "uo", "uc", "pmax", "pmin",
        "t4", "k1", "k2", "t5", "k3", "k4", "t6", "k5", "k6", "t7", "k7", "k8",
    )
    for parameter_name in cgmes_parameters:
        variable_name: str = f"GovSteamIEEE1.{parameter_name}_{template_name}"
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    template.comment = "CGMES GovSteamIEEE1 mapped to the IEEE G1 rate-limited steam governor."
    return template
