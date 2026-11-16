# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected renewable converter and electrical current-limit components."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.regca1_low_voltage import (
    Regca1LowVoltageSettings,
    build_regca1_low_voltage_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_current_limit import (
    Reeca1CurrentLimitSettings,
    build_reeca1_current_limit_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_active_power import (
    Reeca1ActivePowerMode,
    Reeca1ActivePowerSettings,
    build_reeca1_active_power_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_voltage_support import (
    Reeca1VoltageSupportSettings,
    build_reeca1_voltage_support_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import (
    Reeca1ConstantQSettings,
    build_reeca1_constant_q_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_pf import (
    Reeca1ConstantPfSettings,
    build_reeca1_constant_pf_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_coordinated_qv import (
    Reeca1CoordinatedQvSettings,
    build_reeca1_coordinated_qv_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_local_voltage import (
    Reeca1LocalVoltageSettings,
    build_reeca1_local_voltage_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reecc1_battery import (
    Reecc1BatterySettings,
    build_reecc1_battery_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtdta1_drive_train import (
    Wtdta1DriveTrainSettings,
    build_wtdta1_drive_train_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtara1_aerodynamic import (
    Wtara1AerodynamicSettings,
    build_wtara1_aerodynamic_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wttqa1_torque import (
    Wttqa1TorqueSettings,
    build_wttqa1_torque_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wtpta1_pitch import (
    Wtpta1PitchSettings,
    build_wtpta1_pitch_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_active_plant import (
    Repca1ActivePlantSettings,
    build_repca1_active_plant_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_reactive_plant import (
    Repca1ReactiveMode,
    Repca1ReactivePlantSettings,
    Repca1VoltageCompensation,
    build_repca1_reactive_plant_template,
    repca1_line_drop_voltage,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, RmsProblemTypes, VarPowerFlowReferenceType


def build_renewable_partial_chain(
        vf: VarFactory,
        name: str = 'Renewable converter and current limits',
        converter_settings: Regca1LowVoltageSettings | None = None,
        current_limit_settings: Reeca1CurrentLimitSettings | None = None,
        active_power_settings: Reeca1ActivePowerSettings | None = None,
        drive_train_settings: Wtdta1DriveTrainSettings | None = None,
        aerodynamic_settings: Wtara1AerodynamicSettings | None = None,
        torque_settings: Wttqa1TorqueSettings | None = None,
        pitch_settings: Wtpta1PitchSettings | None = None,
        plant_settings: Repca1ActivePlantSettings | None = None,
        plant_reactive_settings: Repca1ReactivePlantSettings | None = None,
        reactive_power_settings: Reeca1ConstantQSettings | None = None,
        power_factor_settings: Reeca1ConstantPfSettings | None = None,
        coordinated_qv_settings: Reeca1CoordinatedQvSettings | None = None,
        local_voltage_settings: Reeca1LocalVoltageSettings | None = None,
        voltage_support_settings: Reeca1VoltageSupportSettings | None = None,
        battery_settings: Reecc1BatterySettings | None = None,
        problem_type: RmsProblemTypes = RmsProblemTypes.PowerBalanceVectorized,
) -> RmsModelTemplate:
    """Connect voltage-dependent REECA current limits to the REGCA low-voltage core.

    Raw current orders initialize from the individual generator power flow.
    Selected active and reactive controls replace their current orders with
    Pref and Qext, or the power-factor reference, on the generator MVA base.
    The electrical current-limit outputs drive the converter lag states on the
    same generator MVA base. The connected core includes REGCA1's converged
    high-voltage correction and REECA1 current/fault control. Remote measurement
    wiring and several source mode combinations remain outside this builder;
    source import must validate its supported selectors before activation.

    :param vf: Shared symbolic variable factory.
    :param name: Unique generator template name.
    :param converter_settings: Low-voltage converter parameters.
    :param current_limit_settings: REECA VDL and priority parameters.
    :param active_power_settings: Optional Pord lag and power-order limits.
    :param drive_train_settings: Optional WTDTA1 shaft feeding generator speed.
    :param aerodynamic_settings: Optional WTARA1 pitch-to-shaft power stage.
    :param torque_settings: Optional WTTQA1 power reference from shaft speed.
    :param pitch_settings: Optional WTPTA1 blade pitch feeding WTARA1.
    :param plant_settings: Optional REPCA1 active plant-power path.
    :param plant_reactive_settings: Optional REPCA1 local Q-control path.
    :param reactive_power_settings: Optional local constant-Q path and Tiq lag.
    :param power_factor_settings: Optional PFFLAG=1 source for the reactive path.
    :param coordinated_qv_settings: Optional QFLAG=1, VFLAG=1 Q/V regulators.
    :param local_voltage_settings: Optional QFLAG=1, VFLAG=0 voltage regulator.
    :param voltage_support_settings: Optional voltage-fault injection and recovery state.
    :param battery_settings: Optional REEC_C energy state and charging bounds.
    :param problem_type: Network voltage coordinate system.
    :return: Connected native generator template with explicit current limits.
    """
    if plant_settings is not None and active_power_settings is None:
        raise ValueError('REPCA1 active plant path requires REECA1 active power')
    elif plant_reactive_settings is not None and (reactive_power_settings is None
                                                  or power_factor_settings is not None
                                                  or coordinated_qv_settings is not None
                                                  or local_voltage_settings is not None):
        raise ValueError('REPCA1 Q mode requires the REECA1 constant-Q branch')
    elif (plant_settings is not None and torque_settings is None and active_power_settings is not None
          and active_power_settings.mode is Reeca1ActivePowerMode.TORQUE_TIMES_SPEED):
        raise ValueError('REPCA1 plant Pref requires REECA1 direct-power mode without WTTQA1')
    elif pitch_settings is not None and (aerodynamic_settings is None or torque_settings is None):
        raise ValueError('WTPTA1 requires WTARA1 and WTTQA1 in the Type 3 wind chain')
    elif torque_settings is not None and (drive_train_settings is None or active_power_settings is None
                                        or active_power_settings.mode is not Reeca1ActivePowerMode.POWER
                                        or voltage_support_settings is None):
        raise ValueError('WTTQA1 requires WTDTA1, REECA1 PFLAG=0 and voltage-fault support')
    elif aerodynamic_settings is not None and drive_train_settings is None:
        raise ValueError('WTARA1 aerodynamic stage requires a WTDTA1 drive train')
    elif drive_train_settings is not None and torque_settings is None and (active_power_settings is None
                                             or active_power_settings.mode is not Reeca1ActivePowerMode.TORQUE_TIMES_SPEED):
        raise ValueError('WTDTA1 connection requires REECA1 speed-dependent power mode')
    elif power_factor_settings is not None and reactive_power_settings is None:
        raise ValueError('REECA1 power-factor mode requires reactive-current settings')
    elif coordinated_qv_settings is not None and (reactive_power_settings is not None or power_factor_settings is not None):
        raise ValueError('REECA1 Q/V and constant Q/pf modes cannot be combined')
    elif coordinated_qv_settings is not None and voltage_support_settings is None:
        raise ValueError('REECA1 Q/V mode requires voltage-fault settings')
    elif local_voltage_settings is not None and (reactive_power_settings is not None
                                                 or power_factor_settings is not None
                                                 or coordinated_qv_settings is not None):
        raise ValueError('REECA1 local-voltage mode cannot be combined with another Q mode')
    elif local_voltage_settings is not None and voltage_support_settings is None:
        raise ValueError('REECA1 local-voltage mode requires voltage-fault settings')
    elif current_limit_settings is not None and current_limit_settings.thld2 > 0 and voltage_support_settings is None:
        raise ValueError('REECA1 Thld2 requires voltage-fault settings')
    elif battery_settings is not None and (active_power_settings is None
          or not active_power_settings.bidirectional
          or active_power_settings.pmin >= 0.0
          or active_power_settings.mode is not Reeca1ActivePowerMode.POWER
          or drive_train_settings is not None or aerodynamic_settings is not None
          or torque_settings is not None or pitch_settings is not None):
        raise ValueError('REECC1 battery requires negative-minimum bidirectional direct-power control without wind mechanics')
    else:
        pass
    selected_current_settings: Reeca1CurrentLimitSettings = (
        Reeca1CurrentLimitSettings() if current_limit_settings is None else current_limit_settings
    )
    if battery_settings is not None and not selected_current_settings.bidirectional_active_current:
        selected_current_settings = Reeca1CurrentLimitSettings(
            imax=selected_current_settings.imax,
            reactive_curve=selected_current_settings.reactive_curve,
            active_curve=selected_current_settings.active_curve,
            priority=selected_current_settings.priority,
            trv=selected_current_settings.trv,
            thld2=selected_current_settings.thld2,
            bidirectional_active_current=True,
        )
    else:
        pass
    template: RmsModelTemplate = build_regca1_low_voltage_template(
        vf=vf, name=name, settings=converter_settings, problem_type=problem_type,
    )
    host: Block = template.block
    converter_ip_order: Var = list(host.event_dict)[0]
    converter_iq_order: Var = list(host.event_dict)[1]
    initial_ip: Expr = host.event_dict[converter_ip_order]
    initial_iq: Expr = host.event_dict[converter_iq_order]
    # The reactive lag follows its solved command; the active lag is initialized
    # from the LVPL-limited target and later composed with REECA's current limit.
    host.init_eqs[host.state_vars[1]] = initial_iq
    limiter: RmsModelTemplate = build_reeca1_current_limit_template(
        vf=vf, name=name + ' current limits', settings=selected_current_settings,
    )
    limiter_block: Block = limiter.block

    # A phasor network supplies Vr/Vi, while a polar network supplies Vm.
    # Both feed the same limiter voltage input without creating a second bus.
    voltage: Var
    initial_voltage: Expr
    if problem_type in (RmsProblemTypes.CurrentBalance, RmsProblemTypes.Multilinear):
        vr: Var = host.external_mapping[VarPowerFlowReferenceType.Vr]
        vi: Var = host.external_mapping[VarPowerFlowReferenceType.Vi]
        voltage = vf.add_var('MeasuredVoltage_' + name)
        magnitude: Expr = sym.sqrt(vr * vr + vi * vi)
        host.algebraic_vars.append(voltage)
        host.algebraic_eqs.append(voltage - magnitude)
        host.init_eqs[voltage] = magnitude
        initial_voltage = magnitude
    else:
        voltage = host.external_mapping[VarPowerFlowReferenceType.Vm]
        initial_voltage = voltage


    filtered_voltage: Var = limiter_block.state_vars[0] if limiter_block.state_vars else voltage
    support_block: Block | None = None
    if voltage_support_settings is not None:
        support: RmsModelTemplate = build_reeca1_voltage_support_template(
            vf=vf, name=name + ' voltage support', settings=voltage_support_settings,
        )
        support_block = support.block
    else:
        pass

    plant_pref: Var | None = None
    if plant_settings is not None:
        plant_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        plant_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        plant_system_p: Var = host.external_mapping[VarPowerFlowReferenceType.P]
        initial_plant_power: Expr = plant_system_p * plant_system_mva / plant_machine_mva
        plant_order: Var = vf.add_var('PlantPowerOrder_' + name)
        plant_frequency: Var = vf.add_var('PlantFrequencyOrder_' + name)
        frequency_reference: Var = vf.add_var('PlantFrequencyReferenceOrder_' + name)
        host.event_dict[plant_order] = initial_plant_power
        host.event_dict[plant_frequency] = Const(1.)
        host.event_dict[frequency_reference] = Const(1.)
        plant: RmsModelTemplate = build_repca1_active_plant_template(
            vf=vf, name=name + ' plant active', settings=plant_settings,
        )
        plant_block: Block = plant.block
        plant_inputs: dict[Var, Expr] = dict(((plant_block.in_vars[0], initial_plant_power),
                                               (plant_block.in_vars[1], plant_order),
                                               (plant_block.in_vars[2], plant_frequency),
                                               (plant_block.in_vars[3], frequency_reference)))
        host.state_vars.extend(plant_block.state_vars)
        host.diff_vars.extend(plant_block.diff_vars)
        host.algebraic_vars.extend(plant_block.algebraic_vars)
        plant_equation: Expr
        for plant_equation in plant_block.state_eqs:
            host.state_eqs.append(plant_equation.subs(plant_inputs))
        for plant_equation in plant_block.algebraic_eqs:
            host.algebraic_eqs.append(plant_equation.subs(plant_inputs))
        plant_signal: Var
        for plant_signal in plant_block.state_vars:
            host.init_eqs[plant_signal] = initial_plant_power
        for plant_signal in plant_block.algebraic_vars:
            host.init_eqs[plant_signal] = initial_plant_power
        host.event_dict.update(plant_block.event_dict)
        plant_pref = plant_block.out_vars[0]
    else:
        pass

    # Build the pitch state before WTARA1 so its angle can drive the
    # aerodynamic equation; connect its four inputs once their signals exist.
    pitch_block: Block | None = None
    if pitch_settings is not None and aerodynamic_settings is not None:
        pitch: RmsModelTemplate = build_wtpta1_pitch_template(
            vf=vf, name=name + ' pitch', settings=pitch_settings,
            initial_pitch=aerodynamic_settings.theta0,
        )
        pitch_block = pitch.block
    else:
        pass

    drive_speed: Var | None = None
    turbine_speed: Var | None = None
    if drive_train_settings is not None:
        # Shaft electrical power uses the solved generator injection on the
        # same machine base as mechanical torque and the REECA power order.
        drive_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        drive_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        drive_system_p: Var = host.external_mapping[VarPowerFlowReferenceType.P]
        initial_machine_power: Expr = drive_system_p * drive_system_mva / drive_machine_mva
        mechanical_order: Var = vf.add_var('MechanicalPowerOrder_' + name)
        host.event_dict[mechanical_order] = initial_machine_power
        mechanical_power_signal: Var = mechanical_order
        if aerodynamic_settings is not None:
            pitch_order: Var
            if pitch_block is None:
                pitch_order = vf.add_var('PitchAngleOrder_' + name)
                host.event_dict[pitch_order] = Const(aerodynamic_settings.theta0)
            else:
                pitch_order = pitch_block.out_vars[0]
            aerodynamic: RmsModelTemplate = build_wtara1_aerodynamic_template(
                vf=vf, name=name + ' aerodynamic', settings=aerodynamic_settings,
            )
            aerodynamic_block: Block = aerodynamic.block
            aerodynamic_inputs: dict[Var, Var] = dict(((aerodynamic_block.in_vars[0], pitch_order),
                                                       (aerodynamic_block.in_vars[1], mechanical_order)))
            host.algebraic_vars.extend(aerodynamic_block.algebraic_vars)
            aerodynamic_equation: Expr
            for aerodynamic_equation in aerodynamic_block.algebraic_eqs:
                host.algebraic_eqs.append(aerodynamic_equation.subs(aerodynamic_inputs))
            aerodynamic_signal: Var
            for aerodynamic_signal in aerodynamic_block.algebraic_vars:
                host.init_eqs[aerodynamic_signal] = aerodynamic_block.init_eqs[aerodynamic_signal].subs(aerodynamic_inputs)
            host.event_dict.update(aerodynamic_block.event_dict)
            mechanical_power_signal = aerodynamic_block.out_vars[0]
        else:
            pass
        drive: RmsModelTemplate = build_wtdta1_drive_train_template(
            vf=vf, name=name + ' drive train', settings=drive_train_settings,
        )
        drive_block: Block = drive.block
        drive_inputs: dict[Var, Expr] = dict(((drive_block.in_vars[0], initial_machine_power),
                                              (drive_block.in_vars[1], mechanical_power_signal)))
        host.state_vars.extend(drive_block.state_vars)
        host.diff_vars.extend(drive_block.diff_vars)
        host.algebraic_vars.extend(drive_block.algebraic_vars)
        drive_equation: Expr
        for drive_equation in drive_block.state_eqs:
            host.state_eqs.append(drive_equation.subs(drive_inputs))
        for drive_equation in drive_block.algebraic_eqs:
            host.algebraic_eqs.append(drive_equation.subs(drive_inputs))
        drive_signal: Var
        for drive_signal in drive_block.state_vars:
            host.init_eqs[drive_signal] = drive_block.init_eqs[drive_signal].subs(drive_inputs)
        for drive_signal in drive_block.algebraic_vars:
            host.init_eqs[drive_signal] = drive_block.init_eqs[drive_signal].subs(drive_inputs)
        host.event_dict.update(drive_block.event_dict)
        drive_speed = drive_block.out_vars[0]
        turbine_speed = drive_block.out_vars[1]
    else:
        pass

    torque_pref: Var | None = None
    torque_speed_reference: Var | None = None
    if torque_settings is not None and drive_speed is not None and support_block is not None:
        torque_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        torque_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        torque_system_p: Var = host.external_mapping[VarPowerFlowReferenceType.P]
        initial_torque_power: Expr = torque_system_p * torque_system_mva / torque_machine_mva
        pref0_order: Var
        if plant_pref is None:
            pref0_order = vf.add_var('TorquePref0Order_' + name)
            host.event_dict[pref0_order] = initial_torque_power
            plant_pref = pref0_order
        else:
            pref0_order = plant_pref
        torque: RmsModelTemplate = build_wttqa1_torque_template(
            vf=vf, name=name + ' torque', settings=torque_settings,
        )
        torque_block: Block = torque.block
        torque_inputs: dict[Var, Expr] = dict(((torque_block.in_vars[0], initial_torque_power),
                                               (torque_block.in_vars[1], drive_speed),
                                               (torque_block.in_vars[2], pref0_order),
                                               (torque_block.in_vars[3], support_block.out_vars[1]),
                                               (torque_block.in_vars[4], torque_machine_mva)))
        host.state_vars.extend(torque_block.state_vars)
        host.diff_vars.extend(torque_block.diff_vars)
        host.algebraic_vars.extend(torque_block.algebraic_vars)
        torque_equation: Expr
        for torque_equation in torque_block.state_eqs:
            host.state_eqs.append(torque_equation.subs(torque_inputs))
        for torque_equation in torque_block.algebraic_eqs:
            host.algebraic_eqs.append(torque_equation.subs(torque_inputs))
        torque_signal: Var
        for torque_signal in torque_block.state_vars:
            host.init_eqs[torque_signal] = torque_block.init_eqs[torque_signal].subs(torque_inputs)
        for torque_signal in torque_block.algebraic_vars:
            host.init_eqs[torque_signal] = torque_block.init_eqs[torque_signal].subs(torque_inputs)
        host.event_dict.update(torque_block.event_dict)
        torque_pref = torque_block.out_vars[0]
        torque_speed_reference = torque_block.out_vars[1]
    else:
        pass

    active_command: Var = converter_ip_order
    active_pord: Var | None = None
    if active_power_settings is not None:
        # Pref belongs on the generator MVA base. It is an event input so a
        # future plant controller can update it without changing PF seeding.
        machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        system_p: Var = host.external_mapping[VarPowerFlowReferenceType.P]
        initial_power: Expr = system_p * system_mva / machine_mva
        initial_pref: Expr = initial_power
        if drive_train_settings is not None and active_power_settings.mode is Reeca1ActivePowerMode.TORQUE_TIMES_SPEED:
            # In PFLAG speed mode Pref is a torque request, so the solved
            # electrical power must be divided by initial generator speed.
            initial_pref = initial_power / Const(drive_train_settings.initial_speed)
        else:
            pass
        host.event_dict.pop(converter_ip_order)
        pref_order: Var
        if torque_pref is None:
            if plant_pref is None:
                pref_order = vf.add_var('PrefOrder_' + name)
                host.event_dict[pref_order] = initial_pref
            else:
                pref_order = plant_pref
        else:
            pref_order = torque_pref
        active: RmsModelTemplate = build_reeca1_active_power_template(
            vf=vf, name=name + ' active power', settings=active_power_settings,
        )
        active_block: Block = active.block
        active_inputs: dict[Var, Var] = dict(((active_block.in_vars[0], pref_order),
                                              (active_block.in_vars[1], filtered_voltage)))
        if active_power_settings.mode is Reeca1ActivePowerMode.TORQUE_TIMES_SPEED:
            if drive_speed is None:
                # A stand-alone partial chain accepts a speed event until a
                # WTDTA1 mechanical model is included in this same block.
                speed_order: Var = vf.add_var('TurbineSpeedOrder_' + name)
                host.event_dict[speed_order] = Const(1.)
                active_inputs[active_block.in_vars[2]] = speed_order
            else:
                active_inputs[active_block.in_vars[2]] = drive_speed
        else:
            pass
        host.state_vars.extend(active_block.state_vars)
        host.diff_vars.extend(active_block.diff_vars)
        host.algebraic_vars.extend(active_block.algebraic_vars)
        active_equation: Expr
        for active_equation in active_block.state_eqs:
            host.state_eqs.append(active_equation.subs(active_inputs))
        for active_equation in active_block.algebraic_eqs:
            host.algebraic_eqs.append(active_equation.subs(active_inputs))
        active_signal: Var
        for active_signal in active_block.state_vars:
            if active_signal.name.startswith('PrefSlewPu_'):
                host.init_eqs[active_signal] = initial_pref
            else:
                host.init_eqs[active_signal] = initial_power
        for active_signal in active_block.algebraic_vars:
            if active_signal is active_block.out_vars[0]:
                host.init_eqs[active_signal] = initial_ip
            else:
                host.init_eqs[active_signal] = initial_power
        host.event_dict.update(active_block.event_dict)
        active_command = active_block.out_vars[0]
        if active_power_settings.tpord > 0:
            active_pord = next(signal for signal in active_block.state_vars
                               if signal.name.startswith('PordPu_'))
        else:
            active_pord = next(signal for signal in active_block.algebraic_vars
                               if signal.name.startswith('PordPu_'))
    else:
        pass

    if (pitch_block is not None and turbine_speed is not None and torque_speed_reference is not None
            and active_pord is not None and plant_pref is not None):
        pitch_inputs: dict[Var, Var] = dict(((pitch_block.in_vars[0], turbine_speed),
                                             (pitch_block.in_vars[1], torque_speed_reference),
                                             (pitch_block.in_vars[2], active_pord),
                                             (pitch_block.in_vars[3], plant_pref)))
        host.state_vars.extend(pitch_block.state_vars)
        host.diff_vars.extend(pitch_block.diff_vars)
        host.algebraic_vars.extend(pitch_block.algebraic_vars)
        pitch_equation: Expr
        for pitch_equation in pitch_block.state_eqs:
            host.state_eqs.append(pitch_equation.subs(pitch_inputs))
        for pitch_equation in pitch_block.algebraic_eqs:
            host.algebraic_eqs.append(pitch_equation.subs(pitch_inputs))
        pitch_signal: Var
        for pitch_signal in pitch_block.state_vars:
            host.init_eqs[pitch_signal] = pitch_block.init_eqs[pitch_signal].subs(pitch_inputs)
        for pitch_signal in pitch_block.algebraic_vars:
            host.init_eqs[pitch_signal] = pitch_block.init_eqs[pitch_signal].subs(pitch_inputs)
        host.event_dict.update(pitch_block.event_dict)
    else:
        pass

    battery_command: Var | None = None
    if battery_settings is not None:
        # Paux enters after Pord/voltage conversion but before converter limits.
        auxiliary_current: Var = vf.add_var('PauxCurrentOrder_' + name)
        host.event_dict[auxiliary_current] = Const(0.0)
        battery_input_power: Expr = (
            host.external_mapping[VarPowerFlowReferenceType.P]
            * host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
            / host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        )
        battery: RmsModelTemplate = build_reecc1_battery_template(
            vf=vf, name=name + ' battery', settings=battery_settings,
        )
        battery_block: Block = battery.block
        battery_inputs: dict[Var, Expr] = dict((
            (battery_block.in_vars[0], battery_input_power),
            (battery_block.in_vars[1], active_command),
            (battery_block.in_vars[2], auxiliary_current),
            (battery_block.in_vars[3], Const(-selected_current_settings.imax)),
            (battery_block.in_vars[4], Const(selected_current_settings.imax)),
        ))
        host.state_vars.extend(battery_block.state_vars)
        host.diff_vars.extend(battery_block.diff_vars)
        host.algebraic_vars.extend(battery_block.algebraic_vars)
        battery_equation: Expr
        for battery_equation in battery_block.state_eqs:
            host.state_eqs.append(battery_equation.subs(battery_inputs))
        for battery_equation in battery_block.algebraic_eqs:
            host.algebraic_eqs.append(battery_equation.subs(battery_inputs))
        battery_signal: Var
        for battery_signal in battery_block.state_vars:
            host.init_eqs[battery_signal] = battery_block.init_eqs[battery_signal].subs(battery_inputs)
        for battery_signal in battery_block.algebraic_vars:
            if battery_signal is battery_block.out_vars[1]:
                initial_pmin: Expr = (
                    Const(0.0) if battery_settings.soc_initial >= battery_settings.soc_maximum
                    else Const(-selected_current_settings.imax)
                )
                host.init_eqs[battery_signal] = initial_pmin
            elif battery_signal is battery_block.out_vars[2]:
                initial_pmax: Expr = (
                    Const(0.0) if battery_settings.soc_initial <= battery_settings.soc_minimum
                    else Const(selected_current_settings.imax)
                )
                host.init_eqs[battery_signal] = initial_pmax
            elif battery_signal is battery_block.out_vars[3]:
                host.init_eqs[battery_signal] = initial_ip
            else:
                host.init_eqs[battery_signal] = battery_block.init_eqs[battery_signal].subs(battery_inputs)
        host.event_dict.update(battery_block.event_dict)
        battery_command = battery_block.out_vars[3]
    else:
        pass

    plant_qext: Var | None = None
    if plant_reactive_settings is not None:
        plant_q_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        plant_q_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        plant_system_q: Var = host.external_mapping[VarPowerFlowReferenceType.Q]
        initial_plant_q: Expr = plant_system_q * plant_q_system_mva / plant_q_machine_mva
        plant_system_p_for_voltage: Var = host.external_mapping[VarPowerFlowReferenceType.P]
        initial_plant_p_for_voltage: Expr = (plant_system_p_for_voltage * plant_q_system_mva
                                             / plant_q_machine_mva)
        plant_q_reference: Expr = initial_plant_q
        plant_voltage_reference: Expr = voltage
        if plant_reactive_settings.mode is Repca1ReactiveMode.Q_CONTROL:
            plant_q_order: Var = vf.add_var('PlantReactiveOrder_' + name)
            host.event_dict[plant_q_order] = initial_plant_q
            plant_q_reference = plant_q_order
        else:
            plant_voltage_order: Var = vf.add_var('PlantVoltageOrder_' + name)
            initial_compensated_voltage: Expr
            if plant_reactive_settings.compensation is Repca1VoltageCompensation.LINE_DROP:
                initial_compensated_voltage = repca1_line_drop_voltage(
                    voltage, initial_plant_p_for_voltage, initial_plant_q,
                    Const(plant_reactive_settings.rc), Const(plant_reactive_settings.xc),
                )
            else:
                initial_compensated_voltage = voltage + Const(plant_reactive_settings.kc) * initial_plant_q
            host.event_dict[plant_voltage_order] = initial_compensated_voltage
            plant_voltage_reference = plant_voltage_order
        plant_q_controller: RmsModelTemplate = build_repca1_reactive_plant_template(
            vf=vf, name=name + ' plant reactive', settings=plant_reactive_settings,
        )
        plant_q_block: Block = plant_q_controller.block
        plant_q_inputs: dict[Var, Expr] = dict(((plant_q_block.in_vars[0], initial_plant_q),
                                                 (plant_q_block.in_vars[1], plant_q_reference),
                                                 (plant_q_block.in_vars[2], voltage),
                                                 (plant_q_block.in_vars[3], plant_voltage_reference),
                                                 (plant_q_block.in_vars[4], initial_plant_p_for_voltage)))
        host.state_vars.extend(plant_q_block.state_vars)
        host.diff_vars.extend(plant_q_block.diff_vars)
        host.algebraic_vars.extend(plant_q_block.algebraic_vars)
        plant_q_equation: Expr
        for plant_q_equation in plant_q_block.state_eqs:
            host.state_eqs.append(plant_q_equation.subs(plant_q_inputs))
        for plant_q_equation in plant_q_block.algebraic_eqs:
            host.algebraic_eqs.append(plant_q_equation.subs(plant_q_inputs))
        plant_q_signal: Var
        for plant_q_signal in plant_q_block.state_vars:
            host.init_eqs[plant_q_signal] = plant_q_block.init_eqs[plant_q_signal].subs(plant_q_inputs)
        for plant_q_signal in plant_q_block.algebraic_vars:
            host.init_eqs[plant_q_signal] = plant_q_block.init_eqs[plant_q_signal].subs(plant_q_inputs)
        host.event_dict.update(plant_q_block.event_dict)
        plant_qext = plant_q_block.out_vars[0]
    else:
        pass

    reactive_command: Expr = converter_iq_order
    if reactive_power_settings is not None:
        # The QFLAG=0 branch owns a power reference on the generator base,
        # replacing the raw current order only after PF initialization.
        q_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        q_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        system_q: Var = host.external_mapping[VarPowerFlowReferenceType.Q]
        initial_qext: Expr = system_q * q_system_mva / q_machine_mva
        host.event_dict.pop(converter_iq_order)
        reactive_reference: Var
        if power_factor_settings is None:
            if plant_qext is None:
                qext_order: Var = vf.add_var('QextOrder_' + name)
                host.event_dict[qext_order] = initial_qext
                reactive_reference = qext_order
            else:
                reactive_reference = plant_qext
        else:
            # PFFLAG=1 replaces Qext with filtered electrical power times
            # the pf angle captured from the solved generator P and Q.
            system_p_for_pf: Var = host.external_mapping[VarPowerFlowReferenceType.P]
            initial_pe: Expr = system_p_for_pf * q_system_mva / q_machine_mva
            pf_angle: Var = vf.add_var('PfAngle_' + name)
            host.event_dict[pf_angle] = sym.atan2(system_q, system_p_for_pf)
            pf_controller: RmsModelTemplate = build_reeca1_constant_pf_template(
                vf=vf, name=name + ' constant pf', settings=power_factor_settings,
            )
            pf_block: Block = pf_controller.block
            pf_inputs: dict[Var, Expr] = dict(((pf_block.in_vars[0], initial_pe),
                                               (pf_block.in_vars[1], pf_angle)))
            host.state_vars.extend(pf_block.state_vars)
            host.diff_vars.extend(pf_block.diff_vars)
            host.algebraic_vars.extend(pf_block.algebraic_vars)
            pf_equation: Expr
            for pf_equation in pf_block.state_eqs:
                host.state_eqs.append(pf_equation.subs(pf_inputs))
            for pf_equation in pf_block.algebraic_eqs:
                host.algebraic_eqs.append(pf_equation.subs(pf_inputs))
            pf_signal: Var
            for pf_signal in pf_block.state_vars:
                host.init_eqs[pf_signal] = initial_pe
            for pf_signal in pf_block.algebraic_vars:
                if pf_signal is pf_block.out_vars[0]:
                    host.init_eqs[pf_signal] = initial_qext
                else:
                    host.init_eqs[pf_signal] = initial_pe
            host.event_dict.update(pf_block.event_dict)
            reactive_reference = pf_block.out_vars[0]
        q_controller: RmsModelTemplate = build_reeca1_constant_q_template(
            vf=vf, name=name + ' constant Q', settings=reactive_power_settings,
        )
        q_block: Block = q_controller.block
        q_inputs: dict[Var, Var] = dict(((q_block.in_vars[0], reactive_reference),
                                         (q_block.in_vars[1], filtered_voltage)))
        host.state_vars.extend(q_block.state_vars)
        host.diff_vars.extend(q_block.diff_vars)
        host.algebraic_vars.extend(q_block.algebraic_vars)
        q_equation: Expr
        for q_equation in q_block.state_eqs:
            host.state_eqs.append(q_equation.subs(q_inputs))
        for q_equation in q_block.algebraic_eqs:
            host.algebraic_eqs.append(q_equation.subs(q_inputs))
        q_signal: Var
        for q_signal in q_block.state_vars:
            host.init_eqs[q_signal] = initial_iq
        for q_signal in q_block.algebraic_vars:
            host.init_eqs[q_signal] = initial_iq
        host.event_dict.update(q_block.event_dict)
        reactive_command = q_block.out_vars[0]
    elif coordinated_qv_settings is not None and support_block is not None:
        # QFLAG=1 and VFLAG=1 cascade the Q and voltage PI regulators. The
        # source fault flag freezes their memories, while Iqmax tracks the
        # same live capability used by the final current-limit block.
        qv_machine_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.generator_snom_mva]
        qv_system_mva: Var = host.api_obj_mapping[ParamPowerFlowReferenceType.Sbase]
        qv_system_q: Var = host.external_mapping[VarPowerFlowReferenceType.Q]
        initial_qref: Expr = qv_system_q * qv_system_mva / qv_machine_mva
        q_reference_order: Var = vf.add_var('QReferenceOrder_' + name)
        host.event_dict.pop(converter_iq_order)
        host.event_dict[q_reference_order] = initial_qref
        qv_controller: RmsModelTemplate = build_reeca1_coordinated_qv_template(
            vf=vf, name=name + ' coordinated Q V', settings=coordinated_qv_settings,
        )
        qv_block: Block = qv_controller.block
        qv_inputs: dict[Var, Expr] = dict(((qv_block.in_vars[0], q_reference_order),
                                           (qv_block.in_vars[1], initial_qref),
                                           (qv_block.in_vars[2], filtered_voltage),
                                           (qv_block.in_vars[3], support_block.out_vars[1]),
                                           (qv_block.in_vars[4], limiter_block.out_vars[2])))
        host.state_vars.extend(qv_block.state_vars)
        host.diff_vars.extend(qv_block.diff_vars)
        host.algebraic_vars.extend(qv_block.algebraic_vars)
        qv_equation: Expr
        for qv_equation in qv_block.state_eqs:
            host.state_eqs.append(qv_equation.subs(qv_inputs))
        for qv_equation in qv_block.algebraic_eqs:
            host.algebraic_eqs.append(qv_equation.subs(qv_inputs))
        qv_state_index: int
        qv_state: Var
        for qv_state_index, qv_state in enumerate(qv_block.state_vars):
            if qv_state_index == 0:
                host.init_eqs[qv_state] = initial_voltage
            else:
                host.init_eqs[qv_state] = initial_iq
        qv_signal: Var
        for qv_signal in qv_block.algebraic_vars:
            if qv_signal.name.startswith('QRegulatorVoltageReferencePu_'):
                host.init_eqs[qv_signal] = initial_voltage
            else:
                host.init_eqs[qv_signal] = initial_iq
        host.event_dict.update(qv_block.event_dict)
        reactive_command = qv_block.out_vars[0]
    elif local_voltage_settings is not None and support_block is not None:
        # VFLAG=0 bypasses the Q PI and adds user Vbias to the local reference.
        # The reference starts at solved Vt minus that bias for zero PI error.
        voltage_reference_order: Var = vf.add_var('VoltageReferenceOrder_' + name)
        host.event_dict.pop(converter_iq_order)
        host.event_dict[voltage_reference_order] = initial_voltage - vf.add_const(local_voltage_settings.vbias)
        voltage_controller: RmsModelTemplate = build_reeca1_local_voltage_template(
            vf=vf, name=name + ' local voltage', settings=local_voltage_settings,
        )
        voltage_block: Block = voltage_controller.block
        voltage_inputs: dict[Var, Var] = dict(((voltage_block.in_vars[0], voltage_reference_order),
                                               (voltage_block.in_vars[1], filtered_voltage),
                                               (voltage_block.in_vars[2], support_block.out_vars[1]),
                                               (voltage_block.in_vars[3], limiter_block.out_vars[2])))
        host.state_vars.extend(voltage_block.state_vars)
        host.diff_vars.extend(voltage_block.diff_vars)
        host.algebraic_vars.extend(voltage_block.algebraic_vars)
        voltage_equation: Expr
        for voltage_equation in voltage_block.state_eqs:
            host.state_eqs.append(voltage_equation.subs(voltage_inputs))
        for voltage_equation in voltage_block.algebraic_eqs:
            host.algebraic_eqs.append(voltage_equation.subs(voltage_inputs))
        voltage_state: Var
        for voltage_state in voltage_block.state_vars:
            host.init_eqs[voltage_state] = initial_iq
        voltage_signal: Var
        for voltage_signal in voltage_block.algebraic_vars:
            host.init_eqs[voltage_signal] = initial_iq
        host.event_dict.update(voltage_block.event_dict)
        reactive_command = voltage_block.out_vars[0]
    else:
        pass
    if voltage_support_settings is not None and support_block is not None:
        # Vref0=0 samples the solved bus voltage once; a nonzero source value
        # remains fixed while the live and filtered voltage signals move.
        reference: Var = vf.add_var('Vref0_' + name)
        if voltage_support_settings.vref0 == 0:
            host.event_dict[reference] = initial_voltage
        else:
            host.event_dict[reference] = vf.add_const(voltage_support_settings.vref0)
        support_inputs: dict[Var, Var] = dict(((support_block.in_vars[0], voltage),
                                               (support_block.in_vars[1], filtered_voltage),
                                               (support_block.in_vars[2], reference)))
        host.algebraic_vars.extend(support_block.algebraic_vars)
        support_equation: Expr
        for support_equation in support_block.algebraic_eqs:
            host.algebraic_eqs.append(support_equation.subs(support_inputs))
        host.init_eqs[support_block.out_vars[0]] = Const(0.)
        host.init_eqs[support_block.out_vars[1]] = Const(0.)
        host.event_dict.update(support_block.event_dict)
        host.mode_dict.update(support_block.mode_dict)
        support_logic: ProceduralLogicBase
        for support_logic in support_block.procedural_logic:
            host.procedural_logic.append(support_logic.remap(support_inputs))
        reactive_command = reactive_command + support_block.out_vars[0]
    else:
        pass

    # The vectorized RMS compiler groups generator state and algebraic
    # equations by one root equivalence class. Substitute the limiter's open
    # ports into that root; retain the original power-flow event orders.
    limiter_active_command: Expr = active_command if battery_command is None else battery_command
    limiter_inputs: dict[Var, Expr] = dict(((limiter_block.in_vars[0], voltage),
                                           (limiter_block.in_vars[1], limiter_active_command),
                                           (limiter_block.in_vars[2], reactive_command)))
    if selected_current_settings.thld2 > 0 and support_block is not None:
        limiter_inputs[limiter_block.in_vars[3]] = support_block.out_vars[1]
    else:
        pass
    converter_inputs: dict[Var, Var] = dict(((converter_ip_order, limiter_block.out_vars[0]),
                                            (converter_iq_order, limiter_block.out_vars[1])))
    host.algebraic_vars.extend(limiter_block.algebraic_vars)
    host.state_vars.extend(limiter_block.state_vars)
    host.diff_vars.extend(limiter_block.diff_vars)
    limiter_state_equation: Expr
    for limiter_state_equation in limiter_block.state_eqs:
        host.state_eqs.append(limiter_state_equation.subs(limiter_inputs))
    limiter_state: Var
    for limiter_state in limiter_block.state_vars:
        host.init_eqs[limiter_state] = limiter_block.init_eqs[limiter_state].subs(limiter_inputs)
    limiter_equation: Expr
    for limiter_equation in limiter_block.algebraic_eqs:
        host.algebraic_eqs.append(limiter_equation.subs(limiter_inputs))
    index: int
    state_equation: Expr
    for index, state_equation in enumerate(host.state_eqs):
        host.state_eqs[index] = state_equation.subs(converter_inputs)
    host.init_eqs[host.state_vars[0]] = host.init_eqs[host.state_vars[0]].subs(converter_inputs)
    host.event_dict.update(limiter_block.event_dict)
    host.mode_dict.update(limiter_block.mode_dict)
    limiter_logic: ProceduralLogicBase
    for limiter_logic in limiter_block.procedural_logic:
        host.procedural_logic.append(limiter_logic.remap(limiter_inputs))
    host.init_eqs[limiter_block.out_vars[0]] = initial_ip
    host.init_eqs[limiter_block.out_vars[1]] = initial_iq
    host.init_eqs[limiter_block.out_vars[2]] = limiter_block.init_eqs[limiter_block.out_vars[2]]
    if active_power_settings is None:
        template.comment = 'Connected renewable current limits and low-voltage converter'
    else:
        template.comment = 'Connected renewable active-power order, current limits and low-voltage converter'
    if voltage_support_settings is not None:
        template.comment += ' with voltage-fault current injection'
    else:
        pass
    if power_factor_settings is not None:
        template.comment += ' and local constant-pf control'
    elif reactive_power_settings is not None:
        template.comment += ' and local constant-Q control'
    elif coordinated_qv_settings is not None:
        template.comment += ' and coordinated Q/V control'
    elif local_voltage_settings is not None:
        template.comment += ' and local terminal-voltage control'
    else:
        pass
    return template
