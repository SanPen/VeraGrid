# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Network host for voltage-aligned renewable generator current commands."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType, RmsProblemTypes, VarPowerFlowReferenceType


def build_renewable_current_source_host(
        vf: VarFactory,
        name: str = "Renewable current source",
        problem_type: RmsProblemTypes = RmsProblemTypes.PowerBalanceVectorized,
) -> RmsModelTemplate:
    """
    Build a generator host with current commands on the machine MVA base.

    Positive active and reactive current commands inject positive P and Q.
    The RMS network consumes the resulting system-base P and Q and converts
    them to the terminal phasor current during its network assembly.
    The host has no dynamic states or current limits; the connected converter
    controller supplies those. Commands initialize from the generator's solved
    power-flow P/Q and terminal voltage.

    :param vf: Variable factory for the host and its controller assembly.
    :param name: Name of the host template.
    :param problem_type: Network voltage coordinate system.
    :return: Generator template with initialized current commands.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.GeneratorDevice

    # Read the terminal voltage in the coordinate system that the selected
    # network problem actually supplies. Both paths produce the same magnitude.
    voltage_magnitude: Expr
    input_vars: list[Var]
    voltage_mapping: dict[VarPowerFlowReferenceType, Var]
    if problem_type in (RmsProblemTypes.CurrentBalance, RmsProblemTypes.Multilinear):
        vr: Var = vf.add_var("Vr_" + name, reference=VarPowerFlowReferenceType.Vr)
        vi: Var = vf.add_var("Vi_" + name, reference=VarPowerFlowReferenceType.Vi)
        voltage_magnitude = sym.sqrt(vr * vr + vi * vi)
        input_vars = list((vr, vi))
        voltage_mapping = dict(((VarPowerFlowReferenceType.Vr, vr),
                                (VarPowerFlowReferenceType.Vi, vi)))
    elif problem_type in (
            RmsProblemTypes.PowerBalance,
            RmsProblemTypes.PowerBalanceVectorized,
            RmsProblemTypes.PowerBalanceFullVectorized,
    ):
        vm: Var = vf.add_var("Vm_" + name, reference=VarPowerFlowReferenceType.Vm)
        voltage_magnitude = vm
        input_vars = list((vm,))
        voltage_mapping = dict(((VarPowerFlowReferenceType.Vm, vm),))
    else:
        raise ValueError("Unsupported renewable current-source network formulation")
    ip_command: Var = vf.add_var("IpCommand_" + name)
    iq_command: Var = vf.add_var("IqCommand_" + name)
    ip: Var = vf.add_var("Ip_" + name)
    iq: Var = vf.add_var("Iq_" + name)
    p: Var = vf.add_var("P_" + name)
    q: Var = vf.add_var("Q_" + name)
    voltage_mapping[VarPowerFlowReferenceType.P] = p
    voltage_mapping[VarPowerFlowReferenceType.Q] = q

    # These static mappings retain both physical MVA bases. Command values
    # are per unit on the generator base; the network sees system-base power.
    machine_mva: Var = vf.add_var("MachineMva_" + name)
    system_mva: Var = vf.add_var("SystemMva_" + name)
    base_ratio: Expr = machine_mva / system_mva

    block: Block = Block(
        parameters=dict(((machine_mva, vf.add_const(value=None, name=machine_mva.name)),
                         (system_mva, vf.add_const(value=None, name=system_mva.name)))),
        algebraic_vars=list((ip, iq, p, q)),
        algebraic_eqs=list((
            ip - ip_command,
            iq - iq_command,
            p - voltage_magnitude * ip * base_ratio,
            q - voltage_magnitude * iq * base_ratio,
        )),
        in_vars=input_vars,
        out_vars=list((p, q, ip, iq)),
        init_eqs=dict(((ip, p / (voltage_magnitude * base_ratio)),
                       (iq, q / (voltage_magnitude * base_ratio)))),
        event_dict=dict(((ip_command, p / (voltage_magnitude * base_ratio)),
                         (iq_command, q / (voltage_magnitude * base_ratio)))),
        external_mapping=voltage_mapping,
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.generator_snom_mva, machine_mva),
                              (ParamPowerFlowReferenceType.Sbase, system_mva))),
        name=name,
    )
    template.block = block
    template.comment = "Voltage-aligned current source on the generator MVA base"
    return template
