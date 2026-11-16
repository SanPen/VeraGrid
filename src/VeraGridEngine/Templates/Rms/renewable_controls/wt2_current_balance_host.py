# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Current-balance network attachment for the unsaturated Type 2 wind core."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.wt2g1_electrical_core import Wt2g1ElectricalSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1_pseudo_governor import Wt12a1Settings
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1u_b_active_stall import Wt12a1uBSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import Wt12t1DriveTrainSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_unsaturated_chain import build_wt2_unsaturated_chain
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_active_stall_chain import build_wt2_active_stall_chain
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import Wt2e1Settings
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowReferenceType, VarPowerFlowReferenceType


def build_wt2_current_balance_host(
        vf: VarFactory, name: str = 'WT2 current-balance generator',
        machine_settings: Wt2g1ElectricalSettings | None = None,
        governor_settings: Wt12a1Settings | None = None,
        shaft_settings: Wt12t1DriveTrainSettings | None = None,
        resistance_settings: Wt2e1Settings | None = None,
        active_stall_settings: Wt12a1uBSettings | None = None,
) -> RmsModelTemplate:
    """Attach WT2 machine P/Q to a live phasor bus on the system MVA base.

    The fixed hidden shunt makes initial network Q match the power-flow Q;
    the source's machine-side active power must already match the generator's
    solved power-flow P. Nonzero saturation remains unsupported.

    :param vf: Circuit-owned symbolic variable factory.
    :param name: Unique generator-template name.
    :param machine_settings: Electrical data and initial terminal phasor.
    :param governor_settings: WT12A1 pseudo-governor data.
    :param shaft_settings: WT12T1 shaft data.
    :param resistance_settings: WT2E1 and WT2G1 power-slip curve data.
    :param active_stall_settings: Optional WT12A1U_B replacement for WT12A1.
    :return: Generator template with current-balance voltage and P/Q mappings.
    :raises ValueError: Both alternative mechanical controllers were selected.
    """
    selected: Wt2g1ElectricalSettings = (
        Wt2g1ElectricalSettings() if machine_settings is None else machine_settings
    )
    if active_stall_settings is not None and governor_settings is not None:
        raise ValueError('WT2 accepts either WT12A1 or WT12A1U_B, not both')
    elif active_stall_settings is not None:
        template: RmsModelTemplate = build_wt2_active_stall_chain(
            vf, name, selected, active_stall_settings, shaft_settings, resistance_settings,
        )
    else:
        template = build_wt2_unsaturated_chain(
            vf, name, selected, governor_settings, shaft_settings, resistance_settings,
        )
    block: Block = template.block
    machine_vd: Var = block.in_vars[0]
    machine_vq: Var = block.in_vars[1]
    machine_p: Var = block.out_vars[0]
    machine_q: Var = block.out_vars[1]
    power_reference: Var | None = None
    speed_reference: Var | None = None
    curve_offset: Var
    if active_stall_settings is None:
        power_reference = block.in_vars[2]
        speed_reference = block.in_vars[3]
        curve_offset = block.in_vars[4]
    else:
        curve_offset = block.in_vars[2]
    vr: Var = vf.add_var('Vr_' + name, reference=VarPowerFlowReferenceType.Vr)
    vi: Var = vf.add_var('Vi_' + name, reference=VarPowerFlowReferenceType.Vi)
    vd: Var = vf.add_var('VdNetworkPu_' + name)
    vq: Var = vf.add_var('VqNetworkPu_' + name)
    network_p: Var = vf.add_var('PSystemPu_' + name)
    network_q: Var = vf.add_var('QSystemPu_' + name)
    q_shunt: Var = vf.add_var('HiddenQShuntMachinePu_' + name)
    machine_mva: Var = vf.add_var('MachineMva_' + name)
    system_mva: Var = vf.add_var('SystemMva_' + name)
    ratio: Expr = machine_mva / system_mva
    initial_voltage_squared: Const = Const(selected.initial_vd ** 2 + selected.initial_vq ** 2)

    # In the source d/q convention, q aligns with the real network phasor and
    # d is its negative imaginary component. The hidden shunt scales with V².
    block.update_model_bulk({machine_vd: vd, machine_vq: vq})
    block.algebraic_vars.extend((vd, vq, network_p, network_q))
    block.algebraic_eqs.extend((vd + vi, vq - vr,
                                 network_p - machine_p * ratio,
                                 network_q - (machine_q + q_shunt
                                              * (vd * vd + vq * vq)
                                              / initial_voltage_squared) * ratio))
    block.event_dict[q_shunt] = network_q / ratio - machine_q
    if power_reference is not None and speed_reference is not None:
        initial_power: Expr = block.init_eqs[machine_p]
        if isinstance(initial_power, Const):
            block.event_dict[power_reference] = initial_power
        else:
            raise ValueError('WT2 initial electrical power must be a solved constant')
        block.event_dict[speed_reference] = Const(selected.initial_speed)
    else:
        pass
    block.event_dict[curve_offset] = block.init_eqs[curve_offset]
    block.parameters[machine_mva] = Const(1.)
    block.parameters[system_mva] = Const(1.)
    block.in_vars = list((vr, vi))
    block.out_vars.extend((network_p, network_q))
    block.external_mapping.update({VarPowerFlowReferenceType.Vr: vr,
                                   VarPowerFlowReferenceType.Vi: vi,
                                   VarPowerFlowReferenceType.P: network_p,
                                   VarPowerFlowReferenceType.Q: network_q})
    block.api_obj_mapping.update({ParamPowerFlowReferenceType.generator_snom_mva: machine_mva,
                                  ParamPowerFlowReferenceType.Sbase: system_mva})
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'Unsaturated Type 2 induction generator with live phasor P/Q and initialized Q shunt'
    return template
