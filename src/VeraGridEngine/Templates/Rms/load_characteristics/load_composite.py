# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES composite-load model."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_load_composite_template(
        vfactory: VarFactory,
        name: str | None = None,
        nominal_frequency: float | None = None,
) -> RmsModelTemplate:
    """Build the sourced CGMES composite-load P and Q equations.

    :param vfactory: Factory that allocates this template's symbols.
    :param name: Optional unique runtime model name.
    :param nominal_frequency: System frequency in Hz for the model's f0 parameter.
    :return: RMS load model with solved P0/Q0 and bus-voltage bindings.
    """
    template_name: str = "LoadComposite" if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.LoadDevice
    parameter_block: Block = Block(name=f"{template_name}_parameters")
    runtime_block: Block = Block(name=template_name)

    # The EA1444 figure defines P and Q from their solved values, initial bus
    # voltage, nominal frequency, and instantaneous frequency inputs.
    p0: Var = vfactory.add_var(f"LoadComposite.P0_{template_name}")
    q0: Var = vfactory.add_var(f"LoadComposite.Q0_{template_name}")
    v0: Var = vfactory.add_var(f"LoadComposite.V0_{template_name}")
    f0: Var = vfactory.add_var(f"LoadComposite.f0_{template_name}")
    epvs: Var = vfactory.add_var(f"LoadComposite.epvs_{template_name}")
    epfs: Var = vfactory.add_var(f"LoadComposite.epfs_{template_name}")
    eqvs: Var = vfactory.add_var(f"LoadComposite.eqvs_{template_name}")
    eqfs: Var = vfactory.add_var(f"LoadComposite.eqfs_{template_name}")
    epvd: Var = vfactory.add_var(f"LoadComposite.epvd_{template_name}")
    epfd: Var = vfactory.add_var(f"LoadComposite.epfd_{template_name}")
    eqvd: Var = vfactory.add_var(f"LoadComposite.eqvd_{template_name}")
    eqfd: Var = vfactory.add_var(f"LoadComposite.eqfd_{template_name}")
    lfac: Var = vfactory.add_var(f"LoadComposite.lfac_{template_name}")
    inertia: Var = vfactory.add_var(f"LoadComposite.h_{template_name}")
    pfrac: Var = vfactory.add_var(f"LoadComposite.pfrac_{template_name}")
    for parameter in (
            epvs, epfs, eqvs, eqfs, epvd, epfd, eqvd, eqfd, lfac, inertia, pfrac,
    ):
        parameter_block.event_dict[parameter] = vfactory.add_const(
            value=None,
            name=parameter.name,
        )
    parameter_block.event_dict[p0] = vfactory.add_const(value=None, name=p0.name)
    parameter_block.event_dict[q0] = vfactory.add_const(value=None, name=q0.name)
    parameter_block.event_dict[v0] = vfactory.add_const(value=None, name=v0.name)
    parameter_block.event_dict[f0] = vfactory.add_const(
        value=nominal_frequency,
        name=f0.name,
    )
    parameter_block.api_obj_mapping[ParamPowerFlowReferenceType.Pl0] = p0
    parameter_block.api_obj_mapping[ParamPowerFlowReferenceType.Ql0] = q0
    parameter_block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = f0

    voltage: Var = vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
    frequency: Var = vfactory.add_var(f"LoadComposite.frequency_{template_name}")
    frequency_derivative: Var = vfactory.add_var(f"LoadComposite.dfdt_{template_name}")
    active_power: Var = vfactory.add_var("P", reference=VarPowerFlowReferenceType.P)
    reactive_power: Var = vfactory.add_var("Q", reference=VarPowerFlowReferenceType.Q)
    voltage_ratio: Expr = voltage / v0
    frequency_ratio: Expr = frequency / f0
    static_active: Expr = (Const(1.0) - pfrac) * voltage_ratio ** epvs * frequency_ratio ** epfs
    dynamic_active: Expr = pfrac * voltage_ratio ** epvd * (
        Const(1.0) + epfd * (frequency - f0) / f0
        + Const(2.0) * inertia * frequency_derivative / (lfac * f0)
    )
    static_reactive: Expr = (Const(1.0) - pfrac) * voltage_ratio ** eqvs * frequency_ratio ** eqfs
    dynamic_reactive: Expr = pfrac * voltage_ratio ** eqvd * frequency_ratio ** eqfd
    runtime_block.in_vars = list((voltage, frequency, frequency_derivative))
    runtime_block.algebraic_vars = list((active_power, reactive_power))
    runtime_block.algebraic_eqs = list((
        active_power - p0 * (static_active + dynamic_active),
        reactive_power - q0 * (static_reactive + dynamic_reactive),
    ))
    runtime_block.out_vars = list((active_power, reactive_power))
    parameter_block.init_eqs[v0] = voltage
    runtime_block.external_mapping[VarPowerFlowReferenceType.Vm] = voltage
    runtime_block.external_mapping[VarPowerFlowReferenceType.P] = active_power
    runtime_block.external_mapping[VarPowerFlowReferenceType.Q] = reactive_power
    template.block.children.append(parameter_block)
    template.block.children.append(runtime_block)
    template.block.in_vars = list((voltage, frequency, frequency_derivative))
    template.block.out_vars = list((active_power, reactive_power))
    template.block.external_mapping.update(runtime_block.external_mapping)
    template.comment = (
        "CGMES LoadComposite EA1444 P/Q equations; frequency and df/dt "
        "remain explicit inputs until a solved RMS frequency signal is available."
    )
    return template
