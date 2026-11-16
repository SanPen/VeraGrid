# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES generic non-linear load template implementations."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import GenericNonLinearLoadModelKind
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.enumerations import (
    DeviceType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_load_generic_non_linear_template(
        vfactory: VarFactory,
        name: str | None = None,
        model_kind: GenericNonLinearLoadModelKind | None = None,
        tp_value: float = 1.0,
        tq_value: float = 1.0,
        initial_voltage: float = 1.0,
) -> RmsModelTemplate:
    """Build the selected CGMES generic nonlinear load equations.

    :param vfactory: Factory used to allocate the equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param model_kind: Parsed CGMES model-kind enumeration.
    :param tp_value: Construction value selecting active recovery topology.
    :param tq_value: Construction value selecting reactive recovery topology.
    :param initial_voltage: Solved steady-state voltage magnitude used as V0.
    :return: Equation-backed recovery/adaptive model.
    :raises TypeError: The mandatory CGMES model kind is absent or unsupported.
    :raises ValueError: Recovery times are negative or non-finite.
    """
    template_name: str = "LoadGenericNonLinear" if name is None else name
    if isinstance(model_kind, GenericNonLinearLoadModelKind):
        pass
    else:
        raise TypeError("CGMES LoadGenericNonLinear requires a canonical model kind")
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = DeviceType.LoadDevice
    parameter_block: Block = Block(name=f"{template_name}_CGMES_parameters")

    # These parameter symbols retain their RDF property names so the common
    # importer can replace each placeholder with the parsed scalar value.
    tp: Var = vfactory.add_var(f"LoadGenericNonLinear.tp_{template_name}")
    tq: Var = vfactory.add_var(f"LoadGenericNonLinear.tq_{template_name}")
    ls: Var = vfactory.add_var(f"LoadGenericNonLinear.ls_{template_name}")
    lt: Var = vfactory.add_var(f"LoadGenericNonLinear.lt_{template_name}")
    bs: Var = vfactory.add_var(f"LoadGenericNonLinear.bs_{template_name}")
    bt: Var = vfactory.add_var(f"LoadGenericNonLinear.bt_{template_name}")
    parameter_block.event_dict[tp] = vfactory.add_const(value=None, name=tp.name)
    parameter_block.event_dict[tq] = vfactory.add_const(value=None, name=tq.name)
    parameter_block.event_dict[ls] = vfactory.add_const(value=None, name=ls.name)
    parameter_block.event_dict[lt] = vfactory.add_const(value=None, name=lt.name)
    parameter_block.event_dict[bs] = vfactory.add_const(value=None, name=bs.name)
    parameter_block.event_dict[bt] = vfactory.add_const(value=None, name=bt.name)

    if model_kind in (
            GenericNonLinearLoadModelKind.exponentialRecovery,
            GenericNonLinearLoadModelKind.loadAdaptive,
    ):
        if math.isfinite(tp_value) and math.isfinite(tq_value):
            pass
        else:
            raise ValueError("CGMES load recovery times must be finite")
        if tp_value >= 0.0 and tq_value >= 0.0:
            pass
        else:
            raise ValueError("CGMES load recovery times must be nonnegative")
        if math.isfinite(initial_voltage) and initial_voltage > 0.0:
            pass
        else:
            raise ValueError("CGMES nonlinear load requires positive initial voltage V0")

        # Normalize voltage against the solved operating point used by the standard equations.
        v0: Var = vfactory.add_var(f"LoadGenericNonLinear.V0_{template_name}")
        parameter_block.event_dict[v0] = vfactory.add_const(value=initial_voltage, name=v0.name)
        voltage_ratio: Var = vfactory.add_var(f"LoadGenericNonLinear.Vratio_{template_name}")

        # P0 and Q0 are the associated EnergyConsumer's nominal powers; the
        # dynamic load starts at its steady-state voltage response.
        p0: Var = vfactory.add_var(f"LoadGenericNonLinear.P0_{template_name}")
        q0: Var = vfactory.add_var(f"LoadGenericNonLinear.Q0_{template_name}")
        parameter_block.event_dict[p0] = vfactory.add_const(value=None, name=p0.name)
        parameter_block.event_dict[q0] = vfactory.add_const(value=None, name=q0.name)
        parameter_block.api_obj_mapping[ParamPowerFlowReferenceType.Pl0] = p0
        parameter_block.api_obj_mapping[ParamPowerFlowReferenceType.Ql0] = q0

        runtime_block: Block = Block(name=template_name)
        voltage: Var = vfactory.add_var(
            "Vm",
            reference=VarPowerFlowReferenceType.Vm,
        )
        active_power: Var = vfactory.add_var(
            "P",
            reference=VarPowerFlowReferenceType.P,
        )
        reactive_power: Var = vfactory.add_var(
            "Q",
            reference=VarPowerFlowReferenceType.Q,
        )
        runtime_block.in_vars = list((voltage,))
        runtime_block.algebraic_vars = list((active_power, reactive_power))
        runtime_block.out_vars = list((active_power, reactive_power))
        runtime_block.algebraic_vars.append(voltage_ratio)
        runtime_block.algebraic_eqs.append(voltage_ratio - voltage / v0)

        if tp_value > 0.0:
            active_recovery: Var = vfactory.add_var(f"ActiveRecovery_{template_name}")
            active_derivative: Var = vfactory.add_diff_var(
                name=f"d_ActiveRecovery_{template_name}",
                base_var=active_recovery,
            )
            runtime_block.state_vars.append(active_recovery)
            runtime_block.diff_vars.append(active_derivative)
            if model_kind is GenericNonLinearLoadModelKind.exponentialRecovery:
                active_recovery_sign: float = 1.0
            else:
                active_recovery_sign = -1.0
            active_static_power: Var = vfactory.add_var(
                f"LoadGenericNonLinear.Pstatic_{template_name}"
            )
            active_dynamic_target: Var = vfactory.add_var(
                f"LoadGenericNonLinear.Ptarget_{template_name}"
            )
            runtime_block.algebraic_vars.extend((active_static_power, active_dynamic_target))
            runtime_block.algebraic_eqs.extend((
                active_static_power - p0 * (voltage_ratio ** lt),
                active_dynamic_target - p0 * (voltage_ratio ** ls),
            ))
            runtime_block.state_eqs.append(
                (active_dynamic_target - active_static_power
                 - active_recovery_sign * active_recovery) / tp
            )
            runtime_block.init_eqs[active_recovery] = (
                Const(0.0)
            )
            runtime_block.algebraic_eqs.append(
                active_power - (active_static_power + active_recovery_sign * active_recovery)
            )
            runtime_block.init_eqs[active_power] = p0
        else:
            runtime_block.algebraic_eqs.append(
                active_power - p0 * (voltage_ratio ** ls)
            )
            runtime_block.init_eqs[active_power] = p0

        if tq_value > 0.0:
            reactive_recovery: Var = vfactory.add_var(f"ReactiveRecovery_{template_name}")
            reactive_derivative: Var = vfactory.add_diff_var(
                name=f"d_ReactiveRecovery_{template_name}",
                base_var=reactive_recovery,
            )
            runtime_block.state_vars.append(reactive_recovery)
            runtime_block.diff_vars.append(reactive_derivative)
            if model_kind is GenericNonLinearLoadModelKind.exponentialRecovery:
                reactive_recovery_sign: float = 1.0
            else:
                reactive_recovery_sign = -1.0
            reactive_static_power: Var = vfactory.add_var(
                f"LoadGenericNonLinear.Qstatic_{template_name}"
            )
            reactive_dynamic_target: Var = vfactory.add_var(
                f"LoadGenericNonLinear.Qtarget_{template_name}"
            )
            runtime_block.algebraic_vars.extend((reactive_static_power, reactive_dynamic_target))
            runtime_block.algebraic_eqs.extend((
                reactive_static_power - q0 * (voltage_ratio ** bt),
                reactive_dynamic_target - q0 * (voltage_ratio ** bs),
            ))
            runtime_block.state_eqs.append(
                (reactive_dynamic_target - reactive_static_power
                 - reactive_recovery_sign * reactive_recovery) / tq
            )
            runtime_block.init_eqs[reactive_recovery] = (
                Const(0.0)
            )
            runtime_block.algebraic_eqs.append(
                reactive_power - (
                    reactive_static_power + reactive_recovery_sign * reactive_recovery
                )
            )
            runtime_block.init_eqs[reactive_power] = q0
        else:
            runtime_block.algebraic_eqs.append(
                reactive_power - q0 * (voltage_ratio ** bs)
            )
            runtime_block.init_eqs[reactive_power] = q0

        # Publish network ports and parameter bindings on the template root.
        runtime_block.external_mapping[VarPowerFlowReferenceType.Vm] = voltage
        runtime_block.external_mapping[VarPowerFlowReferenceType.P] = active_power
        runtime_block.external_mapping[VarPowerFlowReferenceType.Q] = reactive_power
        template.block.children.append(parameter_block)
        template.block.children.append(runtime_block)
        template.block.in_vars = list((voltage,))
        template.block.out_vars = list((active_power, reactive_power))
        template.block.external_mapping.update(runtime_block.external_mapping)
        template.comment = f"CGMES LoadGenericNonLinear {model_kind.name} equations."
    else:
        raise TypeError("Unsupported CGMES LoadGenericNonLinear model kind")

    template.block.name = template_name
    return template
