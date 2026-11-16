# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES time-constant/reactance synchronous-machine realizations."""

from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import RotorKind, SynchronousMachineModelKind
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_synchronous_machine_time_constant_reactance_template(
        vfactory: VarFactory,
        name: str | None = None,
        rotor_type: RotorKind | None = None,
        model_type: SynchronousMachineModelKind | None = None,
        parameters: tuple[tuple[str, float], ...] = tuple(),
) -> RmsModelTemplate:
    """Build a sourced selector realization or retain the exact input record.

    Simplified, Type F/J, and zero-Canay full subtransient realizations follow
    their separate local CGMES EA diagrams. Nonzero Canay reactance and selector
    combinations without a sourced equation remain parameter records.

    :param vfactory: Factory used to allocate symbolic model variables.
    :param name: Optional runtime model name.
    :param rotor_type: Canonical CGMES rotor selector.
    :param model_type: Canonical CGMES model selector.
    :param parameters: Numeric CGMES fields and resolved power bases.
    :return: Equation-backed generator template for the supported selector,
        otherwise a parameter-only record.
    """
    template_name: str = 'SynchronousMachineTimeConstantReactance' if name is None else name
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    parameter_block: Block = Block(name=template_name)
    parameter_values: dict[str, float] = dict()

    # Keep every imported parameter visible even when this selector is not yet runnable.
    for parameter_name, parameter_value in parameters:
        parameter_variable: Var = vfactory.add_var(f'{parameter_name}_{template_name}')
        parameter_values[parameter_name] = parameter_value
        parameter_block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameter_value,
            name=parameter_variable.name,
        )

    # Store canonical selector identities using the established ordinal event representation.
    for selector_name, selector_value in (('rotorType', rotor_type), ('modelType', model_type)):
        selector_variable: Var = vfactory.add_var(f'{selector_name}_{template_name}')
        selector_index: float | None
        if selector_value is None:
            selector_index = None
        else:
            selector_index = float(list(type(selector_value)).index(selector_value))
        parameter_block.event_dict[selector_variable] = vfactory.add_const(
            value=selector_index,
            name=selector_variable.name,
        )

    required_parameters: tuple[str, ...] = (
        'nominalFrequency', 'inertia', 'xDirectSync', 'xDirectTrans',
        'xQuadSync', 'xQuadSubtrans', 'tpdo', 'tppqo', 'ratedS', 'systemBaseMVA',
    )
    is_simplified_model: bool = model_type in (
        SynchronousMachineModelKind.subtransientSimplified,
        SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
    )
    is_type_fj_model: bool = model_type in (
        SynchronousMachineModelKind.subtransientTypeF,
        SynchronousMachineModelKind.subtransientTypeJ,
    )
    if is_simplified_model or is_type_fj_model:
        required_parameters += (
            'xDirectSubtrans', 'tppdo', 'statorLeakageReactance', 'statorResistance',
        )
    else:
        pass
    if rotor_type == RotorKind.roundRotor and model_type in (
            SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
            SynchronousMachineModelKind.subtransientSimplified,
    ):
        required_parameters += ('xQuadTrans', 'tpqo')
    else:
        pass
    if rotor_type == RotorKind.roundRotor and is_type_fj_model:
        required_parameters += ('xQuadTrans', 'tpqo')
    else:
        pass
    if model_type == SynchronousMachineModelKind.subtransient:
        required_parameters += ('xDirectSubtrans', 'tppdo', 'statorLeakageReactance', 'statorResistance')
        if rotor_type == RotorKind.roundRotor:
            required_parameters += ('xQuadTrans', 'tpqo', 'statorLeakageReactance', 'statorResistance')
        else:
            required_parameters += ('xQuadTrans', 'tpqo')
    else:
        pass
    if 'damping' in parameter_values:
        pass
    else:
        parameter_values['damping'] = 0.0
    if 'efdBaseRatio' in parameter_values:
        pass
    else:
        # IEC 61970-457 gives unity as the typical exciter/generator Efd-base ratio.
        parameter_values['efdBaseRatio'] = 1.0
    if 'saturationFactor' in parameter_values:
        pass
    else:
        # The canonical RDF typical S1 keeps machine equations and Ifd base conversion aligned.
        parameter_values['saturationFactor'] = 0.02
    if 'saturationFactor120' in parameter_values:
        pass
    else:
        parameter_values['saturationFactor120'] = 0.12
    if 'fieldCurrentBaseRatio' in parameter_values:
        pass
    elif 'ifdBaseType' not in parameter_values:
        # Direct template callers without an RDF selector use the canonical ifag default.
        parameter_values['fieldCurrentBaseRatio'] = 1.0
    else:
        pass

    is_supported_selector: bool = (
        (
            rotor_type in (RotorKind.roundRotor, RotorKind.salientPole)
            and model_type in (
            SynchronousMachineModelKind.subtransientSimplifiedDirectAxis,
            SynchronousMachineModelKind.subtransientSimplified,
            )
        )
        or (
            rotor_type in (RotorKind.roundRotor, RotorKind.salientPole)
            and is_type_fj_model
        )
        or (
            rotor_type in (RotorKind.roundRotor, RotorKind.salientPole)
            and model_type == SynchronousMachineModelKind.subtransient
        )
    )
    has_supported_tc_equations: bool = True
    if 'ks' in parameter_values:
        pass
    else:
        parameter_values['ks'] = 0.0
    if model_type == SynchronousMachineModelKind.subtransient:
        # The EA generator defaults define one zero-Canay realization without inventing omitted inputs.
        if 'tc' in parameter_values and parameter_values['tc'] == 0.0:
            pass
        elif 'tc' not in parameter_values:
            parameter_values['tc'] = 0.0
        else:
            # TODO: implement nonzero-tc damping equations; current EA equations assume zero Canay reactance.
            has_supported_tc_equations = False
        if rotor_type == RotorKind.roundRotor:
            if 'xQuadSubtrans' not in parameter_values and 'xDirectSubtrans' in parameter_values:
                parameter_values['xQuadSubtrans'] = parameter_values['xDirectSubtrans']
            else:
                pass
            if 'saturationFactorQAxis' not in parameter_values and 'saturationFactor' in parameter_values:
                parameter_values['saturationFactorQAxis'] = parameter_values['saturationFactor']
            else:
                pass
            if 'saturationFactor120QAxis' not in parameter_values and 'saturationFactor120' in parameter_values:
                parameter_values['saturationFactor120QAxis'] = parameter_values['saturationFactor120']
            else:
                pass
        else:
            if 'xQuadTrans' not in parameter_values and 'xDirectSubtrans' in parameter_values:
                parameter_values['xQuadTrans'] = parameter_values['xDirectSubtrans']
            else:
                pass
            if 'xQuadSubtrans' not in parameter_values and 'xDirectSubtrans' in parameter_values:
                parameter_values['xQuadSubtrans'] = parameter_values['xDirectSubtrans']
            else:
                pass
            parameter_values['saturationFactorQAxis'] = 0.0
            parameter_values['saturationFactor120QAxis'] = 0.0
        if 'saturationFactorQAxis' not in parameter_values and 'saturationFactor' in parameter_values:
            parameter_values['saturationFactorQAxis'] = parameter_values['saturationFactor']
        else:
            pass
        if 'saturationFactor120QAxis' not in parameter_values and 'saturationFactor120' in parameter_values:
            parameter_values['saturationFactor120QAxis'] = parameter_values['saturationFactor120']
        else:
            pass
        if rotor_type is RotorKind.salientPole:
            parameter_values['saturationFactorQAxis'] = 0.0
            parameter_values['saturationFactor120QAxis'] = 0.0
        else:
            pass
    else:
        pass
    has_equation_parameters: bool = has_supported_tc_equations
    if math.isfinite(parameter_values['efdBaseRatio']) and parameter_values['efdBaseRatio'] > 0.0:
        pass
    else:
        has_equation_parameters = False
    for parameter_name in required_parameters:
        if parameter_name in parameter_values:
            pass
        else:
            has_equation_parameters = False
    saturation_coefficients: tuple[float, float] | None = None
    if is_type_fj_model or model_type == SynchronousMachineModelKind.subtransient:
        saturation_coefficients = calculate_scaled_quadratic_saturation_coefficients(
            saturation_1=parameter_values.get('saturationFactor', 0.0),
            saturation_1_2=parameter_values.get('saturationFactor120', 0.0),
        )
        if saturation_coefficients is None and is_type_fj_model:
            has_equation_parameters = False
        else:
            pass
    else:
        pass
    if is_supported_selector and is_simplified_model and has_equation_parameters:
        armature_time_constant: float | None = calculate_d_axis_armature_time_constant(
            nominal_frequency=parameter_values['nominalFrequency'],
            x_direct_sync=parameter_values['xDirectSync'],
            x_direct_trans=parameter_values['xDirectTrans'],
            x_direct_subtrans=parameter_values['xDirectSubtrans'],
            stator_leakage=parameter_values['statorLeakageReactance'],
            transient_time=parameter_values['tpdo'],
            subtransient_time=parameter_values['tppdo'],
        )
        if armature_time_constant is not None:
            parameter_values['armatureTimeConstant'] = armature_time_constant
        else:
            has_equation_parameters = False
    else:
        pass
    if (
            is_supported_selector
            and model_type == SynchronousMachineModelKind.subtransient
            and has_equation_parameters
    ):
        runtime_block = build_subtransient_machine_block(
            vfactory=vfactory,
            name=template_name,
            parameters=parameter_values,
            rotor_type=rotor_type,
            saturation_coefficients=saturation_coefficients,
        )
        template.tpe = DeviceType.GeneratorDevice
        template.block.children.append(parameter_block)
        template.block.children.append(runtime_block)
        template.block.external_mapping = dict(runtime_block.external_mapping)
        template.block.in_vars = list(runtime_block.in_vars)
        template.block.out_vars = list(runtime_block.out_vars)
        template.block.name = template_name
        template.comment = f'CGMES zero-Canay SynchronousMachineTimeConstantReactance {rotor_type.name} subtransient model.'
    elif is_supported_selector and has_equation_parameters and is_type_fj_model:
        runtime_block = build_subtransient_type_fj_machine_block(
            vfactory=vfactory,
            name=template_name,
            parameters=parameter_values,
            rotor_type=rotor_type,
            model_type=model_type,
            saturation_coefficients=saturation_coefficients,
        )
        template.tpe = DeviceType.GeneratorDevice
        template.block.children.append(parameter_block)
        template.block.children.append(runtime_block)
        template.block.external_mapping = dict(runtime_block.external_mapping)
        template.block.in_vars = list(runtime_block.in_vars)
        template.block.out_vars = list(runtime_block.out_vars)
        template.block.name = template_name
        template.comment = (
            f'CGMES SynchronousMachineTimeConstantReactance {rotor_type.name} '
            f'{model_type.name} model.'
        )
    elif is_supported_selector and has_equation_parameters:
        runtime_block: Block = build_subtransient_simplified_machine_block(
            vfactory=vfactory,
            name=template_name,
            parameters=parameter_values,
            rotor_type=rotor_type,
            model_type=model_type,
        )
        template.tpe = DeviceType.GeneratorDevice
        template.block.children.append(parameter_block)
        template.block.children.append(runtime_block)
        template.block.external_mapping = dict(runtime_block.external_mapping)
        template.block.in_vars = list(runtime_block.in_vars)
        template.block.out_vars = list(runtime_block.out_vars)
        template.block.name = template_name
        template.comment = (
            f'CGMES SynchronousMachineTimeConstantReactance {rotor_type.name} '
            f'{model_type.name} model.'
        )
    else:
        template.block.children.append(parameter_block)
        template.block.name = template_name
        if model_type == SynchronousMachineModelKind.subtransient:
            # EA848/EA850 require flux-linkage equations; Type F/J has another rotor realization.
            template.comment = (
                'CGMES parameters retained; nonzero tc damping is unsupported because '
                'the local EA material does not define its differential equations.'
            )
        else:
            template.comment = (
                'CGMES parameters retained; equations or required operating-point bases are pending for this selector.'
            )

    # Publish each machine's dynamic terminal-current phasor so linked CGMES controllers can consume GenJ.
    if template.tpe == DeviceType.GeneratorDevice:
        power_real: Var | None = template.block.external_mapping.get(VarPowerFlowReferenceType.P, None)
        power_reactive: Var | None = template.block.external_mapping.get(VarPowerFlowReferenceType.Q, None)
        voltage_magnitude: Var | None = template.block.external_mapping.get(VarPowerFlowReferenceType.Vm, None)
        voltage_angle: Var | None = template.block.external_mapping.get(VarPowerFlowReferenceType.Va, None)
        if (
                power_real is not None
                and power_reactive is not None
                and voltage_magnitude is not None
                and voltage_angle is not None
        ):
            current_real: Var = vfactory.add_var(
                f'IrSystemPu_{template_name}', reference=VarPowerFlowReferenceType.Ir,
            )
            current_imaginary: Var = vfactory.add_var(
                f'IiSystemPu_{template_name}', reference=VarPowerFlowReferenceType.Ii,
            )
            current_bridge: Block = Block(name=f'{template_name}_terminal_current')
            current_bridge.in_vars = list((power_real, power_reactive, voltage_magnitude, voltage_angle))
            current_bridge.algebraic_vars = list((current_real, current_imaginary))
            current_bridge.algebraic_eqs = list((
                current_real * voltage_magnitude
                - power_real * sym.cos(voltage_angle)
                - power_reactive * sym.sin(voltage_angle),
                current_imaginary * voltage_magnitude
                - power_real * sym.sin(voltage_angle)
                + power_reactive * sym.cos(voltage_angle),
            ))
            current_bridge.init_eqs[current_real] = (
                power_real * sym.cos(voltage_angle) + power_reactive * sym.sin(voltage_angle)
            ) / voltage_magnitude
            current_bridge.init_eqs[current_imaginary] = (
                power_real * sym.sin(voltage_angle) - power_reactive * sym.cos(voltage_angle)
            ) / voltage_magnitude
            template.block.children.append(current_bridge)
            template.block.out_vars.extend((current_real, current_imaginary))
            template.block.external_mapping[VarPowerFlowReferenceType.Ir] = current_real
            template.block.external_mapping[VarPowerFlowReferenceType.Ii] = current_imaginary
        else:
            pass
    else:
        pass
    return template


def calculate_scaled_quadratic_saturation_coefficients(
        saturation_1: float,
        saturation_1_2: float,
) -> tuple[float, float] | None:
    """Fit the PSS/E scaled-quadratic saturation curve from CGMES S1/S12.

    :param saturation_1: Saturation factor at air-gap flux 1.0 pu.
    :param saturation_1_2: Saturation factor at air-gap flux 1.2 pu.
    :return: Threshold and gain for ``B * max(x - A, 0)**2 / x``; ``None`` if invalid.
    """
    if saturation_1 == 0.0 and saturation_1_2 == 0.0:
        return 1.0, 0.0
    elif (
            math.isfinite(saturation_1)
            and math.isfinite(saturation_1_2)
            and 0.0 < saturation_1 < saturation_1_2
    ):
        ratio: float = math.sqrt(saturation_1 / (1.2 * saturation_1_2))
        if ratio != 1.0:
            threshold: float = 1.2 + 0.2 / (ratio - 1.0)
            gain: float = saturation_1_2 * 1.2 * (ratio - 1.0) ** 2 / 0.04
            return threshold, gain
        else:
            return None
    else:
        return None


def evaluate_scaled_quadratic_saturation(
        value: Expr,
        threshold: Expr,
        gain: Expr,
) -> Expr:
    """Evaluate the PSS/E scaled-quadratic saturation curve symbolically.

    :param value: Air-gap flux argument.
    :param threshold: Curve onset coefficient fitted from S1/S12.
    :param gain: Curve gain fitted from S1/S12.
    :return: Saturation value ``B * max(value - A, 0)**2 / value``.
    """
    positive_value: Expr = sym.max(value, sym.Const(1.0e-9))
    positive_excess: Expr = sym.max(value - threshold, sym.Const(0.0))
    return gain * positive_excess ** sym.Const(2.0) / positive_value


def build_subtransient_machine_block(
        vfactory: VarFactory,
        name: str,
        parameters: dict[str, float],
        rotor_type: RotorKind,
        saturation_coefficients: tuple[float, float] | None,
) -> Block:
    """Build the zero-Canay full subtransient machine from EA848–EA851.

    :param vfactory: Factory used to allocate machine variables.
    :param name: Runtime machine name.
    :param parameters: Canonical machine properties and rated/system bases.
    :param rotor_type: Rotor selector choosing two q states or one q state.
    :param saturation_coefficients: Direct-axis scaled-quadratic S1/S12 fit.
    :return: Full subtransient generator block with a machine-side Ifd output.
    """
    block: Block = Block(name=name)
    vm_var: Var = vfactory.add_var('Vm', reference=VarPowerFlowReferenceType.Vm)
    va_var: Var = vfactory.add_var('Va', reference=VarPowerFlowReferenceType.Va)
    pg_var: Var = vfactory.add_var('Pg', reference=VarPowerFlowReferenceType.P)
    qg_var: Var = vfactory.add_var('Qg', reference=VarPowerFlowReferenceType.Q)
    tm_var: Var = vfactory.add_var('Tm', shared_reference='tm_reference')
    efd_var: Var = vfactory.add_var('EfdPu', shared_reference='efd_reference')
    delta_var: Var = vfactory.add_var('delta', shared_reference='delta_reference')
    omega_var: Var = vfactory.add_var('omega', shared_reference='omega_reference')
    eq_prime_var: Var = vfactory.add_var('EqPrime')
    eq_subtransient_var: Var = vfactory.add_var('EqSubtransient')
    ed_prime_var: Var | None = None
    if rotor_type is RotorKind.roundRotor:
        ed_prime_var = vfactory.add_var('EdPrime')
    else:
        pass
    ed_subtransient_var: Var = vfactory.add_var('EdSubtransient')
    eq1_var: Var = vfactory.add_var('Eq1')
    eq2_var: Var = vfactory.add_var('Eq2')
    ed1_var: Var = vfactory.add_var('Ed1')
    ed2_var: Var = vfactory.add_var('Ed2')
    vd_var: Var = vfactory.add_var('Vd', shared_reference='vd_reference')
    vq_var: Var = vfactory.add_var('Vq', shared_reference='vq_reference')
    id_var: Var = vfactory.add_var('Id', shared_reference='id_reference')
    iq_var: Var = vfactory.add_var('Iq', shared_reference='iq_reference')
    te_var: Var = vfactory.add_var('Te', shared_reference='te_reference')
    terminal_current_var: Var = vfactory.add_var('ItPu')
    field_current_var: Var | None = None
    field_current_base_ratio_var: Var | None = None
    if 'fieldCurrentBaseRatio' in parameters:
        field_current_var = vfactory.add_var('IfdPu')
        field_current_base_ratio_var = vfactory.add_var(f'IfdBaseRatioEquation_{name}')
        block.event_dict[field_current_base_ratio_var] = vfactory.add_const(
            value=parameters['fieldCurrentBaseRatio'],
            name=field_current_base_ratio_var.name,
        )
    else:
        pass
    psi_airgap_var: Var = vfactory.add_var('PsiAirgap')
    saturation_d_var: Var = vfactory.add_var('SaturationDAxis')
    saturation_q_var: Var | None = None
    if rotor_type is RotorKind.roundRotor:
        saturation_q_var = vfactory.add_var('SaturationQAxis')
    else:
        pass
    frequency_var: Var = vfactory.add_var('fn')
    inertia_var: Var = vfactory.add_var('H')
    damping_var: Var = vfactory.add_var('D')
    xd_var: Var = vfactory.add_var('Xd')
    xdp_var: Var = vfactory.add_var('Xdp')
    xdpp_var: Var = vfactory.add_var('Xdpp')
    xq_var: Var = vfactory.add_var('Xq')
    xqp_var: Var | None = None
    xqpp_var: Var = vfactory.add_var('Xqpp')
    tpdo_var: Var = vfactory.add_var('Tdop')
    tppdo_var: Var = vfactory.add_var('Tdopp')
    tpqo_var: Var | None = None
    tppqo_var: Var = vfactory.add_var('Tqopp')
    leakage_var: Var = vfactory.add_var('Xl')
    resistance_var: Var = vfactory.add_var('Rs')
    machine_base_var: Var = vfactory.add_var('ratedS')
    system_base_var: Var = vfactory.add_var('systemBaseMVA')
    saturation_a_var: Var = vfactory.add_var('SaturationThreshold')
    saturation_b_var: Var = vfactory.add_var('SaturationGain')
    saturation_a_q_var: Var | None = None
    saturation_b_q_var: Var | None = None
    ks_var: Var = vfactory.add_var('Ks')

    parameter_variables: tuple[tuple[Var, float], ...] = (
        (frequency_var, parameters['nominalFrequency']),
        (inertia_var, parameters['inertia']),
        (damping_var, parameters['damping']),
        (xd_var, parameters['xDirectSync']),
        (xdp_var, parameters['xDirectTrans']),
        (xdpp_var, parameters['xDirectSubtrans']),
        (xq_var, parameters['xQuadSync']),
        (xqpp_var, parameters['xQuadSubtrans']),
        (tpdo_var, parameters['tpdo']),
        (tppdo_var, parameters['tppdo']),
        (tppqo_var, parameters['tppqo']),
        (leakage_var, parameters['statorLeakageReactance']),
        (resistance_var, parameters['statorResistance']),
        (machine_base_var, parameters['ratedS']),
        (system_base_var, parameters['systemBaseMVA']),
        (saturation_a_var, 1.0 if saturation_coefficients is None else saturation_coefficients[0]),
        (saturation_b_var, 0.0 if saturation_coefficients is None else saturation_coefficients[1]),
        (ks_var, parameters['ks']),
    )
    for parameter_variable, parameter_value in parameter_variables:
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameter_value,
            name=parameter_variable.name,
        )
    if rotor_type is RotorKind.roundRotor and saturation_q_var is not None:
        saturation_q_coefficients: tuple[float, float] | None = calculate_scaled_quadratic_saturation_coefficients(
            saturation_1=parameters['saturationFactorQAxis'],
            saturation_1_2=parameters['saturationFactor120QAxis'],
        )
        if saturation_q_coefficients is None:
            saturation_q_coefficients = (1.0, 0.0)
        else:
            pass
        saturation_a_q_var = vfactory.add_var('SaturationQThreshold')
        saturation_b_q_var = vfactory.add_var('SaturationQGain')
        xqp_var = vfactory.add_var('Xqp')
        tpqo_var = vfactory.add_var('Tqop')
        for parameter_variable, parameter_value in (
                (saturation_a_q_var, saturation_q_coefficients[0]),
                (saturation_b_q_var, saturation_q_coefficients[1]),
                (xqp_var, parameters['xQuadTrans']),
                (tpqo_var, parameters['tpqo']),
        ):
            block.event_dict[parameter_variable] = vfactory.add_const(
                value=parameter_value,
                name=parameter_variable.name,
            )
    else:
        pass

    one: Expr = sym.Const(1.0)
    two: Expr = sym.Const(2.0)
    efd_base_ratio_var: Var = vfactory.add_var(f'EfdBaseRatioEquation_{name}')
    block.event_dict[efd_base_ratio_var] = vfactory.add_const(
        value=parameters['efdBaseRatio'],
        name=efd_base_ratio_var.name,
    )
    efd_base_ratio: Expr = efd_base_ratio_var
    efd_generator_base: Expr = efd_var * efd_base_ratio
    machine_to_system: Expr = machine_base_var / system_base_var
    xd_damper_transient: Expr = (xd_var - xdp_var) / saturation_d_var
    xd_damper_subtransient: Expr = (xd_var - xdpp_var) / saturation_d_var
    xd_saturated: Expr = (xdpp_var - leakage_var) / saturation_d_var + leakage_var
    xq_saturated: Expr
    xq_damper_subtransient: Expr
    saturation_excess: Expr = evaluate_scaled_quadratic_saturation(
        value=psi_airgap_var,
        threshold=saturation_a_var,
        gain=saturation_b_var,
    )
    if rotor_type is RotorKind.roundRotor and (
            saturation_q_var is not None
            and saturation_a_q_var is not None
            and saturation_b_q_var is not None
            and xqp_var is not None
            and tpqo_var is not None
    ):
        saturation_q_excess: Expr = evaluate_scaled_quadratic_saturation(
            value=psi_airgap_var,
            threshold=saturation_a_q_var,
            gain=saturation_b_q_var,
        )
        saturation_q_expression: Expr = one + saturation_q_excess
        xq_saturated = (xqpp_var - leakage_var) / saturation_q_expression + leakage_var
        xq_damper_subtransient = (xq_var - xqpp_var) / saturation_q_expression
        xq_damper_transient: Expr = (xq_var - xqp_var) / saturation_q_expression
    else:
        saturation_q_expression = one
        xq_saturated = (xqpp_var - leakage_var) + leakage_var
        xq_damper_subtransient = xq_var - xqpp_var
        xq_damper_transient = sym.Const(0.0)
    saturation_d_expression: Expr = one + saturation_excess
    block.state_vars = list((delta_var, omega_var, eq_prime_var, eq_subtransient_var))
    block.state_eqs = list((
        sym.Const(2.0 * math.pi) * frequency_var * (omega_var - one),
        (tm_var - te_var - damping_var * (omega_var - one)) / (two * inertia_var),
        (efd_generator_base - saturation_d_expression * eq1_var) / tpdo_var,
        -saturation_d_expression * ((xdp_var - xdpp_var) / (xd_var - xdpp_var)) * eq2_var / tppdo_var,
    ))
    if rotor_type is RotorKind.roundRotor and ed_prime_var is not None and tpqo_var is not None:
        block.state_vars.extend((ed_prime_var, ed_subtransient_var))
        block.state_eqs.extend((
            -saturation_q_expression * ed1_var / tpqo_var,
            -saturation_q_expression * ((xqp_var - xqpp_var) / (xq_var - xqpp_var)) * ed2_var / tppqo_var,
        ))
    else:
        block.state_vars.append(ed_subtransient_var)
        block.state_eqs.append(-ed2_var / tppqo_var)

    block.algebraic_vars = list((
        eq1_var, eq2_var, ed1_var, ed2_var, vd_var, vq_var, id_var, iq_var,
        pg_var, qg_var, te_var, terminal_current_var,
        psi_airgap_var, saturation_d_var,
    ))
    if field_current_var is not None:
        block.algebraic_vars.append(field_current_var)
    else:
        pass
    if saturation_q_var is not None:
        block.algebraic_vars.extend((saturation_q_var,))
    else:
        pass
    if ed_prime_var is not None:
        block.algebraic_vars.extend((ed_prime_var,))
    else:
        pass
    algebraic_equations: list[Expr] = list((
        vm_var * sym.sin(delta_var - va_var) - vd_var,
        vm_var * sym.cos(delta_var - va_var) - vq_var,
        eq_subtransient_var - (eq1_var + eq2_var - id_var * xd_damper_subtransient),
        eq_prime_var - (eq1_var + eq2_var - ((xdp_var - xdpp_var) / (xd_var - xdpp_var)) * eq2_var - id_var * xd_damper_transient),
        ed_subtransient_var - (ed1_var + ed2_var + iq_var * xq_damper_subtransient),
        saturation_d_var - saturation_d_expression,
        psi_airgap_var - sym.sqrt((vq_var + iq_var * resistance_var + id_var * leakage_var) ** two + (vd_var + id_var * resistance_var - iq_var * leakage_var) ** two),
        vd_var - (omega_var * ed_subtransient_var + iq_var * xq_saturated - id_var * resistance_var),
        vq_var - (omega_var * eq_subtransient_var - id_var * xd_saturated - iq_var * resistance_var),
        te_var - (eq_subtransient_var * iq_var + ed_subtransient_var * id_var),
        machine_to_system * (vd_var * id_var + vq_var * iq_var) - pg_var,
        machine_to_system * (vq_var * id_var - vd_var * iq_var) - qg_var,
        terminal_current_var - sym.sqrt(id_var ** two + iq_var ** two),
    ))
    if field_current_var is not None and field_current_base_ratio_var is not None:
        algebraic_equations.append(
            field_current_var
            - (saturation_d_expression * eq1_var + (xd_var - xdp_var) * id_var)
            * field_current_base_ratio_var
        )
    else:
        pass
    if rotor_type is RotorKind.roundRotor and saturation_q_var is not None:
        algebraic_equations.extend((
            saturation_q_var - saturation_q_expression,
            ed_prime_var - (ed1_var + ed2_var - ((xqp_var - xqpp_var) / (xq_var - xqpp_var)) * ed2_var + iq_var * xq_damper_transient),
        ))
    else:
        algebraic_equations.extend((ed1_var,))
    block.algebraic_eqs = algebraic_equations
    block.in_vars = list((vm_var, va_var, tm_var, efd_var))
    block.out_vars = list((
        pg_var, qg_var, omega_var, te_var, eq_prime_var, eq_subtransient_var,
        ed_subtransient_var, id_var, iq_var, terminal_current_var,
    ))
    if field_current_var is not None:
        block.out_vars.append(field_current_var)
    else:
        pass
    if ed_prime_var is not None:
        block.out_vars.append(ed_prime_var)
    else:
        pass

    voltage_complex: Expr = vm_var * sym.exp(sym.Const(1j) * va_var)
    machine_power: Expr = (pg_var + sym.Const(1j) * qg_var) / machine_to_system
    current_complex: Expr = sym.conj(machine_power / voltage_complex)
    current_real: Expr = sym.real(current_complex)
    current_imaginary: Expr = sym.imag(current_complex)
    xq_synchronous: Expr = (xq_var - leakage_var) / saturation_q_expression + leakage_var
    delta_value: Expr = sym.atan2(
        vm_var * sym.sin(va_var) + xq_synchronous * current_real + resistance_var * current_imaginary,
        vm_var * sym.cos(va_var) - xq_synchronous * current_imaginary + resistance_var * current_real,
    )
    block.init_eqs = dict()
    block.init_eqs[delta_var] = delta_value
    block.init_eqs[omega_var] = one
    current_dq: Expr = current_complex * sym.exp(-sym.Const(1j) * (delta_var - sym.Const(math.pi / 2.0)))
    block.init_eqs[id_var] = sym.real(current_dq)
    block.init_eqs[iq_var] = sym.imag(current_dq)
    block.init_eqs[vd_var] = vm_var * sym.sin(delta_var - va_var)
    block.init_eqs[vq_var] = vm_var * sym.cos(delta_var - va_var)
    # The air-gap flux magnitude is rotation invariant, so derive it from the
    # terminal phasors before the saturated q-axis angle is initialized.
    block.init_eqs[psi_airgap_var] = sym.sqrt(
        (vm_var * sym.cos(va_var) + resistance_var * current_real
         - leakage_var * current_imaginary) ** two
        + (vm_var * sym.sin(va_var) + resistance_var * current_imaginary
           + leakage_var * current_real) ** two
    )
    block.init_eqs[saturation_d_var] = saturation_d_expression
    if saturation_q_var is not None:
        block.init_eqs[saturation_q_var] = saturation_q_expression
    else:
        pass
    # Recover the field winding state from the terminal operating point;
    # deriving it from Efd would cycle through Efd's own initializer.
    block.init_eqs[eq1_var] = eq_subtransient_var + id_var * xd_damper_subtransient
    block.init_eqs[eq2_var] = sym.Const(0.0)
    block.init_eqs[ed1_var] = sym.Const(0.0)
    block.init_eqs[ed2_var] = sym.Const(0.0)
    block.init_eqs[eq_subtransient_var] = vq_var + id_var * xd_saturated + iq_var * resistance_var
    block.init_eqs[ed_subtransient_var] = vd_var - iq_var * xq_saturated + id_var * resistance_var
    block.init_eqs[eq_prime_var] = eq_subtransient_var + id_var * (xdp_var - xdpp_var) / saturation_d_expression
    if ed_prime_var is not None:
        block.init_eqs[ed_prime_var] = ed_subtransient_var - iq_var * (xqp_var - xqpp_var) / saturation_q_expression
    else:
        pass
    block.init_eqs[te_var] = eq_subtransient_var * iq_var + ed_subtransient_var * id_var
    block.init_eqs[terminal_current_var] = sym.sqrt(id_var ** two + iq_var ** two)
    if field_current_var is not None and field_current_base_ratio_var is not None:
        block.init_eqs[field_current_var] = (
            saturation_d_expression * eq1_var + (xd_var - xdp_var) * id_var
        ) * field_current_base_ratio_var
    else:
        pass
    block.init_eqs[tm_var] = te_var
    block.init_eqs[efd_var] = saturation_d_expression * eq1_var / efd_base_ratio
    block.init_eqs[pg_var] = pg_var
    block.init_eqs[qg_var] = qg_var
    block.external_mapping = dict()
    block.external_mapping[VarPowerFlowReferenceType.Vm] = vm_var
    block.external_mapping[VarPowerFlowReferenceType.Va] = va_var
    block.external_mapping[VarPowerFlowReferenceType.P] = pg_var
    block.external_mapping[VarPowerFlowReferenceType.Q] = qg_var
    block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = frequency_var
    return block


def build_subtransient_type_fj_machine_block(
        vfactory: VarFactory,
        name: str,
        parameters: dict[str, float],
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
        saturation_coefficients: tuple[float, float] | None,
) -> Block:
    """Build the round-rotor Type F/J model from the CGMES EA diagram.

    :param vfactory: Factory used to allocate machine variables.
    :param name: Runtime machine name.
    :param parameters: Canonical machine parameters and resolved power bases.
    :param rotor_type: Canonical rotor selector, choosing one or two q-axis states.
    :param model_type: Canonical Type F or Type J selector.
    :param saturation_coefficients: ``(A, B)`` fit from S1/S12.
    :return: Generator block with four rotor states and saturated stator equations.
    """
    block: Block = Block(name=name)
    vm_var: Var = vfactory.add_var('Vm', reference=VarPowerFlowReferenceType.Vm)
    va_var: Var = vfactory.add_var('Va', reference=VarPowerFlowReferenceType.Va)
    pg_var: Var = vfactory.add_var('Pg', reference=VarPowerFlowReferenceType.P)
    qg_var: Var = vfactory.add_var('Qg', reference=VarPowerFlowReferenceType.Q)
    tm_var: Var = vfactory.add_var('Tm', shared_reference='tm_reference')
    efd_var: Var = vfactory.add_var('EfdPu', shared_reference='efd_reference')
    delta_var: Var = vfactory.add_var('delta', shared_reference='delta_reference')
    omega_var: Var = vfactory.add_var('omega', shared_reference='omega_reference')
    eq_prime_var: Var = vfactory.add_var('EqPrime')
    eq_subtransient_var: Var = vfactory.add_var('EqSubtransient')
    ed_prime_var: Var | None = None
    xqp_var: Var | None = None
    tqop_var: Var | None = None
    if rotor_type == RotorKind.roundRotor:
        ed_prime_var = vfactory.add_var('EdPrime')
        xqp_var = vfactory.add_var('Xqp')
        tqop_var = vfactory.add_var('Tqop')
    else:
        pass
    ed_subtransient_var: Var = vfactory.add_var('EdSubtransient')
    vd_var: Var = vfactory.add_var('Vd', shared_reference='vd_reference')
    vq_var: Var = vfactory.add_var('Vq', shared_reference='vq_reference')
    id_var: Var = vfactory.add_var('Id', shared_reference='id_reference')
    iq_var: Var = vfactory.add_var('Iq', shared_reference='iq_reference')
    te_var: Var = vfactory.add_var('Te', shared_reference='te_reference')
    omega_derivative_var: Var = vfactory.add_var('OmegaDerivativePu')
    terminal_current_var: Var = vfactory.add_var('ItPu')
    field_current_var: Var | None = None
    eq1_var: Var = vfactory.add_var('Eq1')
    eq2_var: Var = vfactory.add_var('Eq2')
    ed1_var: Var = vfactory.add_var('Ed1')
    ed2_var: Var = vfactory.add_var('Ed2')
    psi_airgap_var: Var = vfactory.add_var('PsiAirgap')
    saturation_d_var: Var = vfactory.add_var('SaturationDAxis')
    saturation_q_var: Var = vfactory.add_var('SaturationQAxis')
    xd_subtransient_saturated_var: Var = vfactory.add_var('XdSubtransientSaturated')
    xq_subtransient_saturated_var: Var = vfactory.add_var('XqSubtransientSaturated')
    frequency_var: Var = vfactory.add_var('fn')
    inertia_var: Var = vfactory.add_var('H')
    damping_var: Var = vfactory.add_var('D')
    xd_var: Var = vfactory.add_var('Xd')
    xdp_var: Var = vfactory.add_var('Xdp')
    xdpp_var: Var = vfactory.add_var('Xdpp')
    xq_var: Var = vfactory.add_var('Xq')
    xqpp_var: Var = vfactory.add_var('Xqpp')
    tdop_var: Var = vfactory.add_var('Tdop')
    tdopp_var: Var = vfactory.add_var('Tdopp')
    tqopp_var: Var = vfactory.add_var('Tqopp')
    leakage_var: Var = vfactory.add_var('Xl')
    resistance_var: Var = vfactory.add_var('Rs')
    machine_base_var: Var = vfactory.add_var('ratedS')
    system_base_var: Var = vfactory.add_var('systemBaseMVA')
    saturation_a_var: Var = vfactory.add_var('SaturationThreshold')
    saturation_b_var: Var = vfactory.add_var('SaturationGain')
    ks_var: Var = vfactory.add_var('Ks')

    parameter_variables: tuple[tuple[Var, float], ...] = (
        (frequency_var, parameters['nominalFrequency']),
        (inertia_var, parameters['inertia']),
        (damping_var, parameters['damping']),
        (xd_var, parameters['xDirectSync']),
        (xdp_var, parameters['xDirectTrans']),
        (xdpp_var, parameters['xDirectSubtrans']),
        (xq_var, parameters['xQuadSync']),
        (xqpp_var, parameters['xQuadSubtrans']),
        (tdop_var, parameters['tpdo']),
        (tdopp_var, parameters['tppdo']),
        (tqopp_var, parameters['tppqo']),
        (leakage_var, parameters['statorLeakageReactance']),
        (resistance_var, parameters['statorResistance']),
        (machine_base_var, parameters['ratedS']),
        (system_base_var, parameters['systemBaseMVA']),
        (saturation_a_var, saturation_coefficients[0]),
        (saturation_b_var, saturation_coefficients[1]),
        (ks_var, parameters['ks']),
    )
    for parameter_variable, parameter_value in parameter_variables:
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameter_value,
            name=parameter_variable.name,
        )
    if xqp_var is not None and tqop_var is not None:
        block.event_dict[xqp_var] = vfactory.add_const(
            value=parameters['xQuadTrans'],
            name=xqp_var.name,
        )
        block.event_dict[tqop_var] = vfactory.add_const(
            value=parameters['tpqo'],
            name=tqop_var.name,
        )
    else:
        pass

    one: Expr = sym.Const(1.0)
    two: Expr = sym.Const(2.0)
    efd_base_ratio_var: Var = vfactory.add_var(f'EfdBaseRatioEquation_{name}')
    block.event_dict[efd_base_ratio_var] = vfactory.add_const(
        value=parameters['efdBaseRatio'],
        name=efd_base_ratio_var.name,
    )
    efd_base_ratio: Expr = efd_base_ratio_var
    efd_generator_base: Expr = efd_var * efd_base_ratio
    machine_to_system: Expr = machine_base_var / system_base_var
    xd_damper_transient: Expr = (xd_var - xdp_var) / saturation_d_var
    xd_damper_subtransient: Expr = (xd_var - xdpp_var) / saturation_d_var
    xq_damper_transient: Expr
    if xqp_var is not None:
        xq_damper_transient = (xq_var - xqp_var) / saturation_q_var
    else:
        xq_damper_transient = sym.Const(0.0)
    xq_damper_subtransient: Expr = (xq_var - xqpp_var) / saturation_q_var
    saturation_argument: Expr
    if model_type == SynchronousMachineModelKind.subtransientTypeJ:
        sign_id: Expr = sym.heaviside(id_var) - sym.heaviside(-id_var)
        saturation_argument = psi_airgap_var + ks_var * terminal_current_var * sign_id
    else:
        saturation_argument = psi_airgap_var
    saturation_excess: Expr = evaluate_scaled_quadratic_saturation(
        value=saturation_argument,
        threshold=saturation_a_var,
        gain=saturation_b_var,
    )
    xd_saturated: Expr = (xdpp_var - leakage_var) / saturation_d_var + leakage_var
    xq_saturated: Expr = (xqpp_var - leakage_var) / saturation_q_var + leakage_var
    xd_synchronous_saturated: Expr = (xd_var - leakage_var) / saturation_d_var + leakage_var
    xq_synchronous_saturated: Expr = (xq_var - leakage_var) / saturation_q_var + leakage_var

    block.state_vars = list((delta_var, omega_var, eq_prime_var, eq_subtransient_var))
    block.state_eqs = list((
        sym.Const(2.0 * math.pi) * frequency_var * (omega_var - one),
        (tm_var - te_var - damping_var * (omega_var - one)) / (two * inertia_var),
        (efd_generator_base - saturation_d_var * eq1_var) / tdop_var,
        -saturation_d_var * ((xdp_var - xdpp_var) / (xd_var - xdpp_var)) * eq2_var / tdopp_var,
    ))
    if ed_prime_var is not None and xqp_var is not None and tqop_var is not None:
        block.state_vars.extend((ed_prime_var, ed_subtransient_var))
        block.state_eqs.extend((
            -saturation_q_var * ed1_var / tqop_var,
            -saturation_q_var * ((xqp_var - xqpp_var) / (xq_var - xqpp_var)) * ed2_var / tqopp_var,
        ))
    else:
        block.state_vars.append(ed_subtransient_var)
        block.state_eqs.append(-saturation_q_var * ed2_var / tqopp_var)
    block.algebraic_vars = list((
        vd_var, vq_var, id_var, iq_var, pg_var, qg_var, te_var,
        omega_derivative_var, terminal_current_var,
        eq1_var, eq2_var, ed1_var, ed2_var, psi_airgap_var,
        saturation_d_var, saturation_q_var,
        xd_subtransient_saturated_var, xq_subtransient_saturated_var,
    ))
    if ed_prime_var is not None:
        block.algebraic_vars.append(ed_prime_var)
    else:
        pass
    algebraic_equations: list[Expr] = list((
        vm_var * sym.sin(delta_var - va_var) - vd_var,
        vm_var * sym.cos(delta_var - va_var) - vq_var,
        eq_subtransient_var - (eq1_var + eq2_var - id_var * xd_damper_subtransient),
        ed_subtransient_var - (ed1_var + ed2_var + iq_var * xq_damper_subtransient),
        eq_prime_var - (
            eq1_var + eq2_var
            - ((xdp_var - xdpp_var) / (xd_var - xdpp_var)) * eq2_var
            - id_var * xd_damper_transient
        ),
        saturation_d_var - (one + saturation_excess),
        saturation_q_var - (one + (xq_var / xd_var) * saturation_excess),
        xd_subtransient_saturated_var - xd_saturated,
        xq_subtransient_saturated_var - xq_saturated,
        psi_airgap_var - sym.sqrt(
            (vq_var + iq_var * resistance_var + id_var * leakage_var) ** two
            + (vd_var + id_var * resistance_var - iq_var * leakage_var) ** two
        ),
        vd_var - (omega_var * ed_subtransient_var + iq_var * xq_subtransient_saturated_var - id_var * resistance_var),
        vq_var - (omega_var * eq_subtransient_var - id_var * xd_subtransient_saturated_var - iq_var * resistance_var),
        te_var - (eq_subtransient_var * iq_var + ed_subtransient_var * id_var),
        machine_to_system * (vd_var * id_var + vq_var * iq_var) - pg_var,
        machine_to_system * (vq_var * id_var - vd_var * iq_var) - qg_var,
        omega_derivative_var - (tm_var - te_var - damping_var * (omega_var - one)) / (two * inertia_var),
        terminal_current_var - sym.sqrt(id_var ** two + iq_var ** two),
    ))
    if field_current_var is not None:
        block.algebraic_vars.append(field_current_var)
        algebraic_equations.append(
            field_current_var - (saturation_d_var * eq1_var + (xd_var - xdp_var) * id_var)
        )
    else:
        pass
    if ed_prime_var is not None and xqp_var is not None:
        algebraic_equations.append(ed_prime_var - (
            ed1_var + ed2_var
            - ((xqp_var - xqpp_var) / (xq_var - xqpp_var)) * ed2_var
            + iq_var * xq_damper_transient
        ))
    else:
        algebraic_equations.append(ed1_var)
    block.algebraic_eqs = algebraic_equations
    block.in_vars = list((vm_var, va_var, tm_var, efd_var))
    block.out_vars = list((
        pg_var, qg_var, omega_var, te_var, eq_subtransient_var,
        ed_subtransient_var, id_var, iq_var, omega_derivative_var,
        terminal_current_var,
    ))
    if field_current_var is not None:
        block.out_vars.append(field_current_var)
    else:
        pass

    voltage_complex: Expr = vm_var * sym.exp(sym.Const(1j) * va_var)
    machine_power: Expr = (pg_var + sym.Const(1j) * qg_var) / machine_to_system
    current_complex: Expr = sym.conj(machine_power / voltage_complex)
    current_real: Expr = sym.real(current_complex)
    current_imaginary: Expr = sym.imag(current_complex)
    airgap_network_real: Expr = vm_var * sym.cos(va_var) + resistance_var * current_real - leakage_var * current_imaginary
    airgap_network_imaginary: Expr = -vm_var * sym.sin(va_var) - resistance_var * current_imaginary - leakage_var * current_real
    psi_airgap_power_flow: Expr = sym.sqrt(airgap_network_real ** two + airgap_network_imaginary ** two)
    saturation_argument_power_flow: Expr
    delta_power_flow: Expr
    saturation_d_power_flow: Expr
    saturation_q_power_flow: Expr
    if model_type == SynchronousMachineModelKind.subtransientTypeJ:
        current_magnitude: Expr = sym.sqrt(current_real ** two + current_imaginary ** two)
        saturation_argument_positive: Expr = psi_airgap_power_flow + ks_var * current_magnitude
        saturation_argument_negative: Expr = psi_airgap_power_flow - ks_var * current_magnitude
        saturation_q_positive: Expr = one + (xq_var / xd_var) * evaluate_scaled_quadratic_saturation(
            value=saturation_argument_positive,
            threshold=saturation_a_var,
            gain=saturation_b_var,
        )
        saturation_q_negative: Expr = one + (xq_var / xd_var) * evaluate_scaled_quadratic_saturation(
            value=saturation_argument_negative,
            threshold=saturation_a_var,
            gain=saturation_b_var,
        )
        xq_synchronous_positive: Expr = (xq_var - leakage_var) / saturation_q_positive + leakage_var
        xq_synchronous_negative: Expr = (xq_var - leakage_var) / saturation_q_negative + leakage_var
        delta_sine_positive: Expr = (
            vm_var * sym.cos(va_var) - xq_synchronous_positive * current_imaginary
            + resistance_var * current_real
        )
        delta_cosine_positive: Expr = (
            -vm_var * sym.sin(va_var) - xq_synchronous_positive * current_real
            - resistance_var * current_imaginary
        )
        delta_sine_negative: Expr = (
            vm_var * sym.cos(va_var) - xq_synchronous_negative * current_imaginary
            + resistance_var * current_real
        )
        delta_cosine_negative: Expr = (
            -vm_var * sym.sin(va_var) - xq_synchronous_negative * current_real
            - resistance_var * current_imaginary
        )
        delta_positive: Expr = sym.atan2(-delta_cosine_positive, delta_sine_positive)
        delta_negative: Expr = sym.atan2(-delta_cosine_negative, delta_sine_negative)
        id_positive: Expr = current_real * sym.sin(delta_positive) - current_imaginary * sym.cos(delta_positive)
        id_negative: Expr = current_real * sym.sin(delta_negative) - current_imaginary * sym.cos(delta_negative)
        choose_positive: Expr = sym.heaviside(id_positive)
        choose_negative: Expr = (one - choose_positive) * sym.heaviside(-id_negative)
        choose_zero: Expr = one - choose_positive - choose_negative
        delta_unsaturated: Expr = sym.atan2(
            vm_var * sym.sin(va_var) + xq_var * current_real + resistance_var * current_imaginary,
            vm_var * sym.cos(va_var) - xq_var * current_imaginary + resistance_var * current_real,
        )
        saturation_argument_power_flow = (
            choose_positive * saturation_argument_positive
            + choose_negative * saturation_argument_negative
            + choose_zero * psi_airgap_power_flow
        )
        saturation_d_power_flow = one + evaluate_scaled_quadratic_saturation(
            value=saturation_argument_power_flow,
            threshold=saturation_a_var,
            gain=saturation_b_var,
        )
        saturation_q_power_flow = (
            choose_positive * saturation_q_positive
            + choose_negative * saturation_q_negative
            + choose_zero * (one + (xq_var / xd_var) * evaluate_scaled_quadratic_saturation(
                value=psi_airgap_power_flow,
                threshold=saturation_a_var,
                gain=saturation_b_var,
            ))
        )
        delta_power_flow = (
            choose_positive * delta_positive
            + choose_negative * delta_negative
            + choose_zero * delta_unsaturated
        )
    else:
        saturation_argument_power_flow = psi_airgap_power_flow
        saturation_excess_power_flow: Expr = evaluate_scaled_quadratic_saturation(
            value=saturation_argument_power_flow,
            threshold=saturation_a_var,
            gain=saturation_b_var,
        )
        saturation_d_power_flow = one + saturation_excess_power_flow
        saturation_q_power_flow = one + (xq_var / xd_var) * saturation_excess_power_flow
        xq_synchronous_power_flow: Expr = (
            (xq_var - leakage_var) / saturation_q_power_flow + leakage_var
        )
        delta_power_flow = sym.atan2(
            vm_var * sym.sin(va_var)
            + xq_synchronous_power_flow * current_real
            + resistance_var * current_imaginary,
            vm_var * sym.cos(va_var)
            - xq_synchronous_power_flow * current_imaginary
            + resistance_var * current_real,
        )
    block.init_eqs = dict()
    block.init_eqs[delta_var] = delta_power_flow
    block.init_eqs[omega_var] = one
    current_dq: Expr = current_complex * sym.exp(
        -sym.Const(1j) * (delta_var - sym.Const(math.pi / 2.0))
    )
    block.init_eqs[id_var] = sym.real(current_dq)
    block.init_eqs[iq_var] = sym.imag(current_dq)
    block.init_eqs[vd_var] = vm_var * sym.sin(delta_var - va_var)
    block.init_eqs[vq_var] = vm_var * sym.cos(delta_var - va_var)
    block.init_eqs[psi_airgap_var] = psi_airgap_power_flow
    block.init_eqs[saturation_d_var] = saturation_d_power_flow
    block.init_eqs[saturation_q_var] = saturation_q_power_flow
    block.init_eqs[xd_subtransient_saturated_var] = xd_saturated
    block.init_eqs[xq_subtransient_saturated_var] = xq_saturated
    block.init_eqs[eq_subtransient_var] = vq_var + id_var * xd_saturated + iq_var * resistance_var
    block.init_eqs[ed_subtransient_var] = vd_var - iq_var * xq_saturated + id_var * resistance_var
    block.init_eqs[eq_prime_var] = (
        eq_subtransient_var + id_var * (xdp_var - xdpp_var) / saturation_d_var
    )
    if ed_prime_var is not None and xqp_var is not None:
        block.init_eqs[ed_prime_var] = (
            ed_subtransient_var - iq_var * (xqp_var - xqpp_var) / saturation_q_var
        )
    else:
        pass
    block.init_eqs[eq2_var] = sym.Const(0.0)
    block.init_eqs[ed2_var] = sym.Const(0.0)
    block.init_eqs[eq1_var] = eq_subtransient_var + id_var * xd_damper_subtransient
    block.init_eqs[ed1_var] = sym.Const(0.0)
    block.init_eqs[te_var] = eq_subtransient_var * iq_var + ed_subtransient_var * id_var
    block.init_eqs[omega_derivative_var] = sym.Const(0.0)
    block.init_eqs[terminal_current_var] = sym.sqrt(id_var ** two + iq_var ** two)
    block.init_eqs[tm_var] = te_var
    block.init_eqs[efd_var] = saturation_d_var * eq1_var / efd_base_ratio
    if field_current_var is not None:
        block.init_eqs[field_current_var] = saturation_d_var * eq1_var + (xd_var - xdp_var) * id_var
    else:
        pass

    block.external_mapping = dict()
    block.external_mapping[VarPowerFlowReferenceType.Vm] = vm_var
    block.external_mapping[VarPowerFlowReferenceType.Va] = va_var
    block.external_mapping[VarPowerFlowReferenceType.P] = pg_var
    block.external_mapping[VarPowerFlowReferenceType.Q] = qg_var
    block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = frequency_var
    return block


def calculate_d_axis_armature_time_constant(
        nominal_frequency: float,
        x_direct_sync: float,
        x_direct_trans: float,
        x_direct_subtrans: float,
        stator_leakage: float,
        transient_time: float,
        subtransient_time: float,
) -> float | None:
    """Derive the EA armature time constant from the RDF conversion identities.

    :param nominal_frequency: Machine frequency in hertz.
    :param x_direct_sync: Synchronous direct-axis reactance in pu.
    :param x_direct_trans: Transient direct-axis reactance in pu.
    :param x_direct_subtrans: Subtransient direct-axis reactance in pu.
    :param stator_leakage: Stator leakage reactance in pu.
    :param transient_time: Direct-axis transient time constant in seconds.
    :param subtransient_time: Direct-axis subtransient time constant in seconds.
    :return: Equivalent-circuit ``X1d/R1d`` in seconds, or ``None`` for invalid data.
    """
    # Remove stator leakage so the RDF identities operate on the rotor mutual reactances.
    x_ad: float = x_direct_sync - stator_leakage
    x_ad_leakage: float = x_direct_trans - stator_leakage
    x_subtrans_leakage: float = x_direct_subtrans - stator_leakage
    field_denominator: float = x_ad - x_ad_leakage
    if nominal_frequency > 0.0 and transient_time > 0.0 and subtransient_time > 0.0:
        pass
    else:
        return None
    if x_ad > 0.0 and x_ad_leakage > 0.0 and field_denominator > 0.0 and x_subtrans_leakage > 0.0:
        # Invert X'd to recover field leakage before solving the X''d damper branch.
        x_fd: float = x_ad_leakage * x_ad / field_denominator
        equivalent_denominator: float = (
            x_ad * x_fd - x_subtrans_leakage * (x_ad + x_fd)
        )
        if equivalent_denominator > 0.0:
            # Invert X''d and T''do to recover the damper reactance and resistance.
            x_1d: float = x_subtrans_leakage * x_ad * x_fd / equivalent_denominator
            rotor_denominator: float = (
                2.0 * math.pi * nominal_frequency * subtransient_time * (x_ad + x_fd)
            )
            r_1d: float = (
                x_ad * x_fd + x_1d * (x_ad + x_fd)
            ) / rotor_denominator
            if x_1d > 0.0 and r_1d > 0.0:
                return x_1d / r_1d
            else:
                return None
        else:
            return None
    else:
        return None


def build_subtransient_simplified_machine_block(
        vfactory: VarFactory,
        name: str,
        parameters: dict[str, float],
        rotor_type: RotorKind,
        model_type: SynchronousMachineModelKind,
) -> Block:
    """Build one of the CGMES simplified synchronous-machine realizations.

    :param vfactory: Factory used to allocate machine symbols.
    :param name: Runtime model name.
    :param parameters: Complete numeric machine fields and power bases.
    :param rotor_type: Rotor selector choosing one or two q-axis windings.
    :param model_type: Selector choosing one or two d-axis windings.
    :return: Generator block with power-flow ports, differential states, and
        operating-point initialization.
    """
    block: Block = Block(name=name)

    # Power-flow variables are expressed on the network base, while machine currents and torques use ratedS.
    vm_var: Var = vfactory.add_var('Vm', reference=VarPowerFlowReferenceType.Vm)
    va_var: Var = vfactory.add_var('Va', reference=VarPowerFlowReferenceType.Va)
    pg_var: Var = vfactory.add_var('Pg', reference=VarPowerFlowReferenceType.P)
    qg_var: Var = vfactory.add_var('Qg', reference=VarPowerFlowReferenceType.Q)
    tm_var: Var = vfactory.add_var('Tm', shared_reference='tm_reference')
    efd_var: Var = vfactory.add_var('EfdPu', shared_reference='efd_reference')

    # The EA diagram has one field state on d and one damper state on q for this selector.
    delta_var: Var = vfactory.add_var('delta', shared_reference='delta_reference')
    omega_var: Var = vfactory.add_var('omega', shared_reference='omega_reference')
    eq_prime_var: Var = vfactory.add_var('EqPrime')
    eq_subtransient_var: Var | None = None
    if model_type == SynchronousMachineModelKind.subtransientSimplified:
        eq_subtransient_var = vfactory.add_var('EqSubtransient')
    else:
        pass
    ed_subtransient_var: Var = vfactory.add_var('EdSubtransient')
    ed_transient_var: Var | None = None
    if rotor_type == RotorKind.roundRotor:
        ed_transient_var = vfactory.add_var('EdPrime')
    else:
        pass
    omega_derivative_var: Var = vfactory.add_var('OmegaDerivativePu')

    # Algebraic variables expose stator current, terminal power, and internal voltage to linked controls.
    vd_var: Var = vfactory.add_var('Vd', shared_reference='vd_reference')
    vq_var: Var = vfactory.add_var('Vq', shared_reference='vq_reference')
    id_var: Var = vfactory.add_var('Id', shared_reference='id_reference')
    iq_var: Var = vfactory.add_var('Iq', shared_reference='iq_reference')
    ed_var: Var = vfactory.add_var('Ed')
    eq_var: Var = vfactory.add_var('Eq')
    te_var: Var = vfactory.add_var('Te', shared_reference='te_reference')
    terminal_current_var: Var = vfactory.add_var('ItPu')
    field_current_var: Var | None = None
    field_current_base_ratio_var: Var | None = None
    if (
            model_type == SynchronousMachineModelKind.subtransientSimplifiedDirectAxis
            and 'fieldCurrentBaseRatio' in parameters
    ):
        field_current_var = vfactory.add_var('IfdPu')
    else:
        pass

    # Canonical inputs select only the quantities present in the EA realization.
    frequency_var: Var = vfactory.add_var('fn')
    inertia_var: Var = vfactory.add_var('H')
    damping_var: Var = vfactory.add_var('D')
    xd_var: Var = vfactory.add_var('Xd')
    xdp_var: Var = vfactory.add_var('Xdp')
    xdpp_var: Var | None = None
    tdopp_var: Var | None = None
    taa_var: Var | None = None
    if eq_subtransient_var is not None:
        xdpp_var = vfactory.add_var('Xdpp')
        tdopp_var = vfactory.add_var('Tdopp')
        taa_var = vfactory.add_var('Taa')
    else:
        pass
    xq_var: Var = vfactory.add_var('Xq')
    xqp_var: Var | None = None
    tqop_var: Var | None = None
    if rotor_type == RotorKind.roundRotor:
        xqp_var = vfactory.add_var('Xqp')
        tqop_var = vfactory.add_var('Tqop')
    else:
        pass
    xqpp_var: Var = vfactory.add_var('Xqpp')
    tdop_var: Var = vfactory.add_var('Tdop')
    tqopp_var: Var = vfactory.add_var('Tqopp')
    machine_base_var: Var = vfactory.add_var('ratedS')
    system_base_var: Var = vfactory.add_var('systemBaseMVA')
    parameter_variables: tuple[tuple[Var, str], ...] = (
        (frequency_var, 'nominalFrequency'), (inertia_var, 'inertia'),
        (damping_var, 'damping'), (xd_var, 'xDirectSync'),
        (xdp_var, 'xDirectTrans'), (xq_var, 'xQuadSync'),
        (xqpp_var, 'xQuadSubtrans'), (tdop_var, 'tpdo'),
        (tqopp_var, 'tppqo'), (machine_base_var, 'ratedS'),
        (system_base_var, 'systemBaseMVA'),
    )
    if xdpp_var is not None and tdopp_var is not None and taa_var is not None:
        parameter_variables += (
            (xdpp_var, 'xDirectSubtrans'),
            (tdopp_var, 'tppdo'),
            (taa_var, 'armatureTimeConstant'),
        )
    else:
        pass
    if xqp_var is not None and tqop_var is not None:
        parameter_variables += ((xqp_var, 'xQuadTrans'), (tqop_var, 'tpqo'))
    else:
        pass
    for parameter_variable, parameter_name in parameter_variables:
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=parameters[parameter_name],
            name=parameter_variable.name,
        )
    if field_current_var is not None:
        field_current_base_ratio_var = vfactory.add_var(f'IfdBaseRatioEquation_{name}')
        block.event_dict[field_current_base_ratio_var] = vfactory.add_const(
            value=parameters['fieldCurrentBaseRatio'],
            name=field_current_base_ratio_var.name,
        )
    else:
        pass

    # The rotor equations use the network electrical speed and the CGMES inertia/damping convention.
    one: Expr = sym.Const(1.0)
    two: Expr = sym.Const(2.0)
    efd_base_ratio_var: Var = vfactory.add_var(f'EfdBaseRatioEquation_{name}')
    block.event_dict[efd_base_ratio_var] = vfactory.add_const(
        value=parameters['efdBaseRatio'],
        name=efd_base_ratio_var.name,
    )
    efd_base_ratio: Expr = efd_base_ratio_var
    efd_generator_base: Expr = efd_var * efd_base_ratio
    synchronous_speed: Expr = two * sym.Const(math.pi) * frequency_var
    machine_to_system: Expr = machine_base_var / system_base_var
    block.state_vars = list((delta_var, omega_var, eq_prime_var))
    block.state_eqs = list((
        synchronous_speed * (omega_var - one),
        (tm_var - te_var - damping_var * (omega_var - one)) / (two * inertia_var),
        (efd_generator_base - (xd_var - xdp_var) * id_var - eq_prime_var) / tdop_var,
    ))
    if eq_subtransient_var is not None and xdpp_var is not None and tdopp_var is not None and taa_var is not None:
        gamma_d: Expr = (tdopp_var / tdop_var) * (xd_var - xdp_var)
        block.state_vars.append(eq_subtransient_var)
        block.state_eqs[-1] = (
            efd_generator_base * (one - taa_var / tdop_var)
            - (xd_var - xdp_var - gamma_d) * id_var
            - eq_prime_var
        ) / tdop_var
        block.state_eqs.append(
            (
                (taa_var / tdop_var) * efd_generator_base
                - (xdp_var - xdpp_var + gamma_d) * id_var
                + eq_prime_var - eq_subtransient_var
            ) / tdopp_var
        )
    else:
        pass
    if rotor_type == RotorKind.roundRotor and ed_transient_var is not None and xqp_var is not None and tqop_var is not None:
        gamma_q: Expr = (tqopp_var / tqop_var) * (xq_var - xqp_var)
        block.state_vars.extend((ed_transient_var, ed_subtransient_var))
        block.state_eqs.extend((
            ((xq_var - xqp_var - gamma_q) * iq_var - ed_transient_var) / tqop_var,
            ((xqp_var - xqpp_var + gamma_q) * iq_var + ed_transient_var - ed_subtransient_var) / tqopp_var,
        ))
    else:
        block.state_vars.append(ed_subtransient_var)
        block.state_eqs.append(((xq_var - xqpp_var) * iq_var - ed_subtransient_var) / tqopp_var)

    # The diagram outputs E'q-X'd*id and E''d+X''q*iq as the two stator-axis voltages.
    block.algebraic_vars = list((
        vd_var, vq_var, ed_var, eq_var, id_var, iq_var, te_var,
        pg_var, qg_var, omega_derivative_var, terminal_current_var,
    ))
    block.algebraic_eqs = list((
        vm_var * sym.sin(delta_var - va_var) - vd_var,
        vm_var * sym.cos(delta_var - va_var) - vq_var,
        ed_subtransient_var + xqpp_var * iq_var - ed_var,
        (
            eq_subtransient_var - xdpp_var * id_var - eq_var
            if eq_subtransient_var is not None and xdpp_var is not None
            else eq_prime_var - xdp_var * id_var - eq_var
        ),
        vd_var - ed_var,
        vq_var - eq_var,
        ed_var * id_var + eq_var * iq_var - te_var,
        ed_var * id_var * machine_to_system + eq_var * iq_var * machine_to_system - pg_var,
        (vq_var * id_var - vd_var * iq_var) * machine_to_system - qg_var,
        omega_derivative_var
        - (tm_var - te_var - damping_var * (omega_var - one)) / (two * inertia_var),
        sym.sqrt(id_var ** two + iq_var ** two) - terminal_current_var,
    ))
    if field_current_var is not None and field_current_base_ratio_var is not None:
        # With no d-axis damper, E'q and its transient current drop define the field-current output.
        block.algebraic_vars.append(field_current_var)
        block.algebraic_eqs.append(
            field_current_var
            - (eq_prime_var + (xd_var - xdp_var) * id_var) * field_current_base_ratio_var
        )
    else:
        pass
    block.in_vars = list((vm_var, va_var, tm_var, efd_var))
    block.out_vars = list((
        pg_var, qg_var, omega_var, te_var, eq_var, ed_var,
        id_var, iq_var, omega_derivative_var, terminal_current_var,
    ))
    if field_current_var is not None:
        block.out_vars.append(field_current_var)
    else:
        pass

    # Solve the steady q-axis relation Vd=Xq*Iq for rotor angle, then seed both axis states from the phasor point.
    voltage_complex: Expr = vm_var * sym.exp(sym.Const(1j) * va_var)
    machine_power: Expr = (pg_var + sym.Const(1j) * qg_var) / machine_to_system
    current_complex: Expr = sym.conj(machine_power / voltage_complex)
    current_real: Expr = sym.real(current_complex)
    current_imaginary: Expr = sym.imag(current_complex)
    delta_sine_coefficient: Expr = vm_var * sym.cos(va_var) - xq_var * current_imaginary
    delta_cosine_coefficient: Expr = -vm_var * sym.sin(va_var) - xq_var * current_real
    block.init_eqs = dict()
    block.init_eqs[delta_var] = sym.atan2(-delta_cosine_coefficient, delta_sine_coefficient)
    block.init_eqs[omega_var] = one
    current_dq: Expr = current_complex * sym.exp(
        -sym.Const(1j) * (delta_var - sym.Const(math.pi / 2.0))
    )
    block.init_eqs[id_var] = sym.real(current_dq)
    block.init_eqs[iq_var] = sym.imag(current_dq)
    block.init_eqs[vd_var] = vm_var * sym.sin(delta_var - va_var)
    block.init_eqs[vq_var] = vm_var * sym.cos(delta_var - va_var)
    if rotor_type == RotorKind.roundRotor and ed_transient_var is not None and xqp_var is not None and tqop_var is not None:
        gamma_q = (tqopp_var / tqop_var) * (xq_var - xqp_var)
        block.init_eqs[ed_transient_var] = (xq_var - xqp_var - gamma_q) * iq_var
        block.init_eqs[ed_subtransient_var] = (xq_var - xqpp_var) * iq_var
    else:
        block.init_eqs[ed_subtransient_var] = (xq_var - xqpp_var) * iq_var
    if eq_subtransient_var is not None and xdpp_var is not None and tdopp_var is not None and taa_var is not None:
        gamma_d = (tdopp_var / tdop_var) * (xd_var - xdp_var)
        block.init_eqs[eq_subtransient_var] = vq_var + xdpp_var * id_var
        block.init_eqs[eq_prime_var] = (
            eq_subtransient_var
            + (xdp_var - xdpp_var + gamma_d) * id_var
            - (taa_var / tdop_var) * efd_generator_base
        )
    else:
        block.init_eqs[eq_prime_var] = vq_var + xdp_var * id_var
    block.init_eqs[ed_var] = vd_var
    block.init_eqs[eq_var] = vq_var
    block.init_eqs[te_var] = pg_var / machine_to_system
    block.init_eqs[omega_derivative_var] = sym.Const(0.0)
    block.init_eqs[terminal_current_var] = sym.sqrt(id_var ** two + iq_var ** two)
    block.init_eqs[tm_var] = te_var
    block.init_eqs[efd_var] = (vq_var + xd_var * id_var) / efd_base_ratio
    if field_current_var is not None and field_current_base_ratio_var is not None:
        block.init_eqs[field_current_var] = (
            eq_prime_var + (xd_var - xdp_var) * id_var
        ) * field_current_base_ratio_var
    else:
        pass

    # Bind the block to power-flow device fields and publish its electrical signals for model composition.
    block.external_mapping = dict()
    block.external_mapping[VarPowerFlowReferenceType.Vm] = vm_var
    block.external_mapping[VarPowerFlowReferenceType.Va] = va_var
    block.external_mapping[VarPowerFlowReferenceType.P] = pg_var
    block.external_mapping[VarPowerFlowReferenceType.Q] = qg_var
    block.api_obj_mapping[ParamPowerFlowReferenceType.freq] = frequency_var
    return block
