# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES static-load models."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import StaticLoadModelKind
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_load_static_template(
        vfactory: VarFactory,
        name: str | None = None,
        model_kind: StaticLoadModelKind | None = None,
) -> RmsModelTemplate:
    """Build the selected CGMES static-load voltage/frequency equations.

    :param vfactory: Factory that owns this template's symbols.
    :param name: Optional unique runtime model name.
    :param model_kind: CGMES ZIP/exponential/constant-impedance variant.
    :return: RMS load model with P/Q network ports and RDF parameter events.
    """
    template_name: str = "LoadStatic" if name is None else name
    selected_kind: StaticLoadModelKind = (
        StaticLoadModelKind.constantZ if model_kind is None else model_kind
    )
    if isinstance(selected_kind, StaticLoadModelKind):
        pass
    else:
        raise TypeError("LoadStatic model kind must be a StaticLoadModelKind")

    # The selected voltage terms match the standard model variant; zero-power
    # terms stay present as equations because the RDF parameters remain mutable.
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.LoadDevice
    runtime_block: Block = Block(name=template_name)
    vm: Var = vfactory.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
    frequency_deviation: Var = vfactory.add_var("frequencyDeviation")
    p0: Var = vfactory.add_var("P0", reference=ParamPowerFlowReferenceType.Pl0)
    q0: Var = vfactory.add_var("Q0", reference=ParamPowerFlowReferenceType.Ql0)
    p: Var = vfactory.add_var("P", reference=VarPowerFlowReferenceType.P)
    q: Var = vfactory.add_var("Q", reference=VarPowerFlowReferenceType.Q)

    kp1: Var = vfactory.add_var(f"LoadStatic.kp1_{template_name}")
    kp2: Var = vfactory.add_var(f"LoadStatic.kp2_{template_name}")
    kp3: Var = vfactory.add_var(f"LoadStatic.kp3_{template_name}")
    kp4: Var = vfactory.add_var(f"LoadStatic.kp4_{template_name}")
    ep1: Var = vfactory.add_var(f"LoadStatic.ep1_{template_name}")
    ep2: Var = vfactory.add_var(f"LoadStatic.ep2_{template_name}")
    ep3: Var = vfactory.add_var(f"LoadStatic.ep3_{template_name}")
    kpf: Var = vfactory.add_var(f"LoadStatic.kpf_{template_name}")
    kq1: Var = vfactory.add_var(f"LoadStatic.kq1_{template_name}")
    kq2: Var = vfactory.add_var(f"LoadStatic.kq2_{template_name}")
    kq3: Var = vfactory.add_var(f"LoadStatic.kq3_{template_name}")
    kq4: Var = vfactory.add_var(f"LoadStatic.kq4_{template_name}")
    eq1: Var = vfactory.add_var(f"LoadStatic.eq1_{template_name}")
    eq2: Var = vfactory.add_var(f"LoadStatic.eq2_{template_name}")
    eq3: Var = vfactory.add_var(f"LoadStatic.eq3_{template_name}")
    kqf: Var = vfactory.add_var(f"LoadStatic.kqf_{template_name}")

    # None keeps missing RDF data visible to the runtime parameter validator.
    runtime_block.event_dict[kp1] = vfactory.add_const(value=None, name=kp1.name)
    runtime_block.event_dict[kp2] = vfactory.add_const(value=None, name=kp2.name)
    runtime_block.event_dict[kp3] = vfactory.add_const(value=None, name=kp3.name)
    runtime_block.event_dict[kp4] = vfactory.add_const(value=None, name=kp4.name)
    runtime_block.event_dict[ep1] = vfactory.add_const(value=None, name=ep1.name)
    runtime_block.event_dict[ep2] = vfactory.add_const(value=None, name=ep2.name)
    runtime_block.event_dict[ep3] = vfactory.add_const(value=None, name=ep3.name)
    runtime_block.event_dict[kpf] = vfactory.add_const(value=None, name=kpf.name)
    runtime_block.event_dict[kq1] = vfactory.add_const(value=None, name=kq1.name)
    runtime_block.event_dict[kq2] = vfactory.add_const(value=None, name=kq2.name)
    runtime_block.event_dict[kq3] = vfactory.add_const(value=None, name=kq3.name)
    runtime_block.event_dict[kq4] = vfactory.add_const(value=None, name=kq4.name)
    runtime_block.event_dict[eq1] = vfactory.add_const(value=None, name=eq1.name)
    runtime_block.event_dict[eq2] = vfactory.add_const(value=None, name=eq2.name)
    runtime_block.event_dict[eq3] = vfactory.add_const(value=None, name=eq3.name)
    runtime_block.event_dict[kqf] = vfactory.add_const(value=None, name=kqf.name)
    runtime_block.event_dict[p0] = vfactory.add_const(value=None, name=p0.name)
    runtime_block.event_dict[q0] = vfactory.add_const(value=None, name=q0.name)

    active_voltage_term: Expr
    reactive_voltage_term: Expr
    active_frequency_term: Expr
    reactive_frequency_term: Expr
    active_power: Expr
    reactive_power: Expr
    if selected_kind is StaticLoadModelKind.constantZ:
        active_power: Expr = p0 * (vm ** Const(2.0))
        reactive_power: Expr = q0 * (vm ** Const(2.0))
    elif selected_kind is StaticLoadModelKind.exponential:
        active_voltage_term = kp1 * (vm ** ep1) + kp2 * (vm ** ep2) + kp3 * (vm ** ep3)
        reactive_voltage_term = kq1 * (vm ** eq1) + kq2 * (vm ** eq2) + kq3 * (vm ** eq3)
        active_power = p0 * active_voltage_term * (Const(1.0) + kpf * frequency_deviation)
        reactive_power = q0 * reactive_voltage_term * (Const(1.0) + kqf * frequency_deviation)
    elif selected_kind is StaticLoadModelKind.zIP1:
        active_voltage_term = kp1 * (vm ** Const(2.0)) + kp2 * vm + kp3
        reactive_voltage_term = kq1 * (vm ** Const(2.0)) + kq2 * vm + kq3
        active_power = p0 * active_voltage_term * (Const(1.0) + kpf * frequency_deviation)
        reactive_power = q0 * reactive_voltage_term * (Const(1.0) + kqf * frequency_deviation)
    else:
        active_voltage_term = kp1 * (vm ** Const(2.0)) + kp2 * vm + kp3
        reactive_voltage_term = kq1 * (vm ** Const(2.0)) + kq2 * vm + kq3
        active_frequency_term = Const(1.0) + kpf * frequency_deviation
        reactive_frequency_term = Const(1.0) + kqf * frequency_deviation
        active_power = p0 * active_voltage_term + p0 * kp4 * active_frequency_term
        reactive_power = q0 * reactive_voltage_term + q0 * kq4 * reactive_frequency_term
    runtime_block.in_vars = list((vm, frequency_deviation))
    runtime_block.algebraic_vars = list((p, q))
    runtime_block.algebraic_eqs = list((p - active_power, q - reactive_power))
    runtime_block.out_vars = list((p, q))
    runtime_block.api_obj_mapping[ParamPowerFlowReferenceType.Pl0] = p0
    runtime_block.api_obj_mapping[ParamPowerFlowReferenceType.Ql0] = q0
    runtime_block.external_mapping[VarPowerFlowReferenceType.Vm] = vm
    runtime_block.external_mapping[VarPowerFlowReferenceType.P] = p
    runtime_block.external_mapping[VarPowerFlowReferenceType.Q] = q
    template.block.children.append(runtime_block)
    template.block.in_vars = list((vm, frequency_deviation))
    template.block.out_vars = list((p, q))
    template.block.external_mapping.update(runtime_block.external_mapping)
    template.comment = f"CGMES LoadStatic {selected_kind.name} equations."
    return template
