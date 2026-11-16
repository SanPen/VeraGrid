# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Assign the shared non-generator RMS models for large benchmark grids."""

from __future__ import annotations

from VeraGridEngine.enumerations import ParamPowerFlowReferenceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.shunt_template import get_shunt_template
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import get_transformer2w_rms
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
import VeraGridEngine.api as gce


def assign_standard_network_rms_models(grid: gce.MultiCircuit, prefix: str) -> None:
    """Assign standard RMS models to all non-generator network devices.

    :param grid: VeraGrid network whose generators are configured separately.
    :param prefix: Stable model-name prefix.
    :return: None.
    """
    bus_index: int
    for bus_index, bus in enumerate(grid.buses):
        initialize_bus_rms(bus, vf=grid.var_factory)

    line_index: int
    for line_index, line in enumerate(grid.lines):
        set_rms_model(
            device=line,
            model=get_line_rms_template(
                grid.var_factory,
                name=f"{prefix}_line_{line_index + 1}",
            ).block,
            var_factory=grid.var_factory,
        )

    transformer_index: int
    for transformer_index, transformer in enumerate(grid.transformers2w):
        set_rms_model(
            device=transformer,
            model=get_transformer2w_rms(grid.var_factory).block,
            var_factory=grid.var_factory,
        )

    load_index: int
    for load_index, load in enumerate(grid.loads):
        set_rms_model(
            device=load,
            model=get_load_rms_template(
                grid.var_factory,
                name=f"{prefix}_load_{load_index + 1}",
            ).block,
            var_factory=grid.var_factory,
        )

    shunt_index: int
    for shunt_index, shunt in enumerate(grid.shunts):
        shunt_model = get_shunt_template(
            grid.var_factory,
            name=f"{prefix}_shunt_{shunt_index + 1}",
            phasor=False,
        ).block
        shunt_vm = shunt_model.E(VarPowerFlowReferenceType.Vm)
        shunt_p = shunt_model.E(VarPowerFlowReferenceType.P)
        shunt_q = shunt_model.E(VarPowerFlowReferenceType.Q)
        shunt_g = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.g]
        shunt_b = shunt_model.api_obj_mapping[ParamPowerFlowReferenceType.b]
        shunt_model.event_dict[shunt_g] = grid.var_factory.add_const(
            value=shunt.G / grid.Sbase,
            name="g",
        )
        shunt_model.event_dict[shunt_b] = grid.var_factory.add_const(
            value=shunt.B / grid.Sbase,
            name="b",
        )
        shunt_model.init_eqs[shunt_p] = -shunt_g * shunt_vm ** 2
        shunt_model.init_eqs[shunt_q] = shunt_b * shunt_vm ** 2
        set_rms_model(
            device=shunt,
            model=shunt_model,
            var_factory=grid.var_factory,
        )
