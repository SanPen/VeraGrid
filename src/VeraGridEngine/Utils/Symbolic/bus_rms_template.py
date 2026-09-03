# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from typing import Tuple, Optional

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var

from VeraGridEngine.Devices.Substation.bus import Bus


def promote_dc_bus_voltage_to_capacitive_state(
        bus_rms_model: Block,
        vf: VarFactory,
        dc_shunt_capacitance_pu_seconds: float,
) -> None:
    """Promote one algebraic DC-bus voltage to its capacitive energy state.

    The bus-local active-power variable bridges the network nodal balance to
    the state equation without persisting a second representation of the
    network. RMS problem builders bind that variable to their final nodal sum.

    :param bus_rms_model: Replaceable algebraic DC-bus block.
    :param vf: Variable factory that owns the bus variables.
    :param dc_shunt_capacitance_pu_seconds: Positive nodal capacitance in p.u. seconds.
    :return: None.
    """
    capacitance_is_valid: bool = (
        math.isfinite(dc_shunt_capacitance_pu_seconds)
        and dc_shunt_capacitance_pu_seconds > 0.0
    )
    vdc: Var | None = bus_rms_model.external_mapping.get(
        VarPowerFlowReferenceType.Vdc,
        None,
    )
    active_power: Var | None = bus_rms_model.external_mapping.get(
        VarPowerFlowReferenceType.P,
        None,
    )
    has_replaceable_topology: bool = (
        isinstance(vdc, Var)
        and isinstance(active_power, Var)
        and len(bus_rms_model.state_vars) == 0
        and len(bus_rms_model.algebraic_vars) == 1
        and bus_rms_model.algebraic_vars[0] is vdc
        and len(bus_rms_model.algebraic_eqs) == 0
        and len(bus_rms_model.children) == 0
    )
    if not capacitance_is_valid:
        raise ValueError("DC bus shunt capacitance must be finite and positive.")
    else:
        pass
    if not has_replaceable_topology or vdc is None or active_power is None:
        raise ValueError("DC bus RMS block cannot be promoted to a capacitive state.")
    else:
        pass

    vdc_derivative: Var = vf.add_diff_var(
        name="dVdc_dt",
        base_var=vdc,
    )
    capacitance: Const = Const(float(dc_shunt_capacitance_pu_seconds))
    bus_rms_model.algebraic_vars = list([active_power])
    bus_rms_model.state_vars = list([vdc])
    bus_rms_model.state_eqs = list([active_power / (capacitance * vdc)])
    bus_rms_model.diff_vars = list([vdc_derivative])
    bus_rms_model.external_mapping[
        VarPowerFlowReferenceType.d_Vdc
    ] = vdc_derivative


def build_dc_bus_nodal_power_equation(
        bus_rms_model: Block,
        nodal_power_balance: Expr | Const,
) -> Expr | Const:
    """Build the algebraic DC nodal equation for one RMS bus topology.

    Algebraic buses retain the historical zero-power balance. Capacitive buses
    instead bind that balance to their local power variable, whose state
    equation advances ``Vdc`` from the same canonical nodal sum.

    :param bus_rms_model: DC-bus RMS block.
    :param nodal_power_balance: Final network active-power sum at the bus.
    :return: Algebraic nodal equation compatible with the bus topology.
    """
    has_capacitive_state: bool = dc_bus_rms_model_has_capacitive_state(
        bus_rms_model=bus_rms_model,
    )
    if has_capacitive_state:
        active_power: Var | None = bus_rms_model.external_mapping.get(
            VarPowerFlowReferenceType.P,
            None,
        )
        has_active_power_variable: bool = (
            active_power is not None
            and len(bus_rms_model.algebraic_vars) == 1
            and bus_rms_model.algebraic_vars[0] is active_power
        )
        if not has_active_power_variable or active_power is None:
            raise ValueError("Capacitive DC bus lacks its nodal active-power variable.")
        else:
            nodal_equation: Expr | Const = active_power - nodal_power_balance
    else:
        nodal_equation = nodal_power_balance
    return nodal_equation


def dc_bus_rms_model_has_capacitive_state(bus_rms_model: Block) -> bool:
    """Return whether one DC-bus RMS block owns a complete voltage state.

    :param bus_rms_model: DC-bus RMS block to inspect.
    :return: Whether ``Vdc`` has a complete capacitive-state topology.
    :raises ValueError: If a mapped derivative has an incomplete topology.
    """
    vdc_derivative: Var | None = bus_rms_model.external_mapping.get(
        VarPowerFlowReferenceType.d_Vdc,
        None,
    )
    if vdc_derivative is None:
        has_capacitive_state: bool = False
    else:
        vdc: Var | None = bus_rms_model.external_mapping.get(
            VarPowerFlowReferenceType.Vdc,
            None,
        )
        active_power: Var | None = bus_rms_model.external_mapping.get(
            VarPowerFlowReferenceType.P,
            None,
        )
        has_complete_topology: bool = (
            isinstance(vdc_derivative, Var)
            and isinstance(vdc, Var)
            and isinstance(active_power, Var)
            and len(bus_rms_model.state_vars) == 1
            and bus_rms_model.state_vars[0] is vdc
            and len(bus_rms_model.state_eqs) == 1
            and len(bus_rms_model.diff_vars) == 1
            and bus_rms_model.diff_vars[0] is vdc_derivative
            and vdc_derivative.base_var is vdc
            and vdc.diff_var is vdc_derivative
            and len(bus_rms_model.algebraic_vars) == 1
            and bus_rms_model.algebraic_vars[0] is active_power
        )
        if has_complete_topology:
            has_capacitive_state = True
        else:
            raise ValueError("DC bus has an incomplete capacitive-state topology.")
    return has_capacitive_state


class BusRmsTemplate(RmsModelTemplate):
    __slots__ = (
        "tpe",
        "_block",
        "Vm",
        "Va",
        "Vdc",
    )

    def __init__(
            self,
            vf: VarFactory,
            is_dc: bool = False,
            name: str = "rms_bus_template",
            dc_shunt_capacitance_pu_seconds: float = 0.0,
    ) -> None:
        """
        Create the RMS template of one AC or DC bus.

        A positive DC shunt-capacitance coefficient promotes ``Vdc`` to a
        state while preserving its canonical variable identity and exposing
        the matching differential variable to connected RMS models.

        :param vf: Variable factory that owns the bus variables.
        :param is_dc: Whether the bus belongs to a DC network.
        :param name: Name of the RMS model.
        :param dc_shunt_capacitance_pu_seconds: DC nodal capacitance in p.u. seconds.
        :return: None.
        """
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice
        capacitance_is_valid: bool = (
            math.isfinite(dc_shunt_capacitance_pu_seconds)
            and dc_shunt_capacitance_pu_seconds >= 0.0
        )
        if not capacitance_is_valid:
            raise ValueError("DC bus shunt capacitance must be finite and non-negative.")
        else:
            pass

        if is_dc:
            vdc: Var = vf.add_var("Vdc", reference=VarPowerFlowReferenceType.Vdc)
            active_power: Var = vf.add_var("P", reference=VarPowerFlowReferenceType.P)
            self._block = Block(
                algebraic_vars=list([vdc]),
                out_vars=list([vdc]),
            )

            self._block.external_mapping = dict()
            self._block.external_mapping[VarPowerFlowReferenceType.Vdc] = vdc
            self._block.external_mapping[VarPowerFlowReferenceType.d_Vdc] = None
            self._block.external_mapping[VarPowerFlowReferenceType.Vm] = None
            self._block.external_mapping[VarPowerFlowReferenceType.Va] = None
            self._block.external_mapping[VarPowerFlowReferenceType.P] = active_power
            self._block.external_mapping[VarPowerFlowReferenceType.Q] = None
            if dc_shunt_capacitance_pu_seconds > 0.0:
                promote_dc_bus_voltage_to_capacitive_state(
                    bus_rms_model=self._block,
                    vf=vf,
                    dc_shunt_capacitance_pu_seconds=dc_shunt_capacitance_pu_seconds,
                )
            else:
                pass

        else:
            if dc_shunt_capacitance_pu_seconds > 0.0:
                raise ValueError("An AC bus cannot own a DC shunt capacitance.")
            else:
                pass
            vm: Var = vf.add_var("Vm", reference=VarPowerFlowReferenceType.Vm)
            va: Var = vf.add_var("Va", reference=VarPowerFlowReferenceType.Va)
            active_power: Var = vf.add_var("P", reference=VarPowerFlowReferenceType.P)
            reactive_power: Var = vf.add_var("Q", reference=VarPowerFlowReferenceType.Q)

            self._block = Block(
                algebraic_vars=list([vm, va]),
                out_vars=list([vm, va]),
            )

            self._block.external_mapping = dict()
            self._block.external_mapping[VarPowerFlowReferenceType.Vdc] = None
            self._block.external_mapping[VarPowerFlowReferenceType.d_Vdc] = None
            self._block.external_mapping[VarPowerFlowReferenceType.Vm] = vm
            self._block.external_mapping[VarPowerFlowReferenceType.Va] = va
            self._block.external_mapping[VarPowerFlowReferenceType.P] = active_power
            self._block.external_mapping[VarPowerFlowReferenceType.Q] = reactive_power


def initialize_bus_rms(
        bus: Bus,
        vf: VarFactory,
        dc_shunt_capacitance_pu_seconds: float = 0.0,
) -> None:
    """
    Initialize the canonical RMS voltage block owned by one bus.

    :param bus: Bus that receives the RMS block.
    :param vf: Variable factory that owns the block variables.
    :param dc_shunt_capacitance_pu_seconds: DC nodal capacitance in p.u. seconds.
    :return: None.
    """
    bus.rms_model = BusRmsTemplate(
        vf=vf,
        is_dc=bus.is_dc,
        dc_shunt_capacitance_pu_seconds=dc_shunt_capacitance_pu_seconds,
    ).block

def get_bus_rms_algebraic_vars(bus_rms_model: Block) ->Tuple[Var | None, Var | None, Var | None]:
    """
    Return the RMS bus algebraic voltage variables.

    For AC buses:
        returns (None, Vm, Va)

    For DC buses:
        returns (Vdc, None, None)

    :param bus_rms_model: RMS bus block
    :return: Tuple with two positions to preserve the project API
    """
    mapping = bus_rms_model.external_mapping
    Vdc = mapping.get(VarPowerFlowReferenceType.Vdc)
    Vm = mapping.get(VarPowerFlowReferenceType.Vm)
    Va = mapping.get(VarPowerFlowReferenceType.Va)
    if Vdc is not None and Vm is None and Va is  None:
        return Vdc, None, None
    elif Vdc is None and Vm is not None and Va is not None:
        return None, Vm, Va
    else:
        raise ValueError("Invalid RMS bus model: expected either (Vdc) or (Vm, Va)")
