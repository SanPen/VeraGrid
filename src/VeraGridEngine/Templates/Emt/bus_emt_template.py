# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple, Optional, TYPE_CHECKING

from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Utils.Symbolic.block import Block, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class BusEmtTemplate(EmtModelTemplate):
    __slots__ = (
        "tpe",
        "_block",
        "v_DC",
        "v_N",
        "v_A",
        "v_B",
        "v_C",
    )

    def __init__(self,
                 vf: VarFactory,
                 mask: list[bool],
                 is_dc: bool = False,
                 name: str = "emt_bus_template"):
        """
        Created the EMT Template of a Bus
        :param vf: VarFactory
        :param mask: list[bool] with true if the phase exist and false if it doesn't in the order [N,A,B,C]
        :param name: Name of the EMT Model
        """
        super().__init__(name=name)

        self.tpe: DeviceType = DeviceType.BusDevice
        self._block.name = name
        if is_dc:
            # For a DC bus in EMT, we track the instantaneous DC voltage.
            self.v_DC = vf.add_var(name=f"v_DC_{name}", reference=VarPowerFlowRefferenceType.Vdc)

            self._block = Block(
                algebraic_vars=[self.v_DC],
                out_vars=[self.v_DC]
            )

            # Map the instantaneous DC voltage. P and Q are None because
            # EMT simulations compute power implicitly from v(t) and i(t).
            # Include v_N, v_A, v_B, v_C as None so that the loop in emt_problem_dae
            # can iterate over all phases without errors.
            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vdc: self.v_DC,
                VarPowerFlowRefferenceType.v_N: None,
                VarPowerFlowRefferenceType.v_A: None,
                VarPowerFlowRefferenceType.v_B: None,
                VarPowerFlowRefferenceType.v_C: None,
                VarPowerFlowRefferenceType.P: None,
                VarPowerFlowRefferenceType.Q: None
            }

        else:
            self.v_N = vf.add_var(name=f"v_N_{name}", reference=VarPowerFlowRefferenceType.v_N) if mask[0] else None
            self.v_A = vf.add_var(name=f"v_A_{name}", reference=VarPowerFlowRefferenceType.v_A) if mask[1] else None
            self.v_B = vf.add_var(name=f"v_B_{name}", reference=VarPowerFlowRefferenceType.v_B) if mask[2] else None
            self.v_C = vf.add_var(name=f"v_C_{name}", reference=VarPowerFlowRefferenceType.v_C) if mask[3] else None

            v_list = [v for v in (self.v_N, self.v_A, self.v_B, self.v_C) if v is not None]
            if not v_list:
                raise ValueError("Bus has no enabled phases")

            self._block = Block(
                algebraic_vars=v_list,
                out_vars=v_list
            )

            self._block.external_mapping = {
                VarPowerFlowRefferenceType.Vdc: None,
                VarPowerFlowRefferenceType.v_N: self.v_N,
                VarPowerFlowRefferenceType.v_A: self.v_A,
                VarPowerFlowRefferenceType.v_B: self.v_B,
                VarPowerFlowRefferenceType.v_C: self.v_C,
                VarPowerFlowRefferenceType.P: None,
                VarPowerFlowRefferenceType.Q: None
            }

    @property
    def block(self) -> Block:
        """
        block
        :return: Block
        """
        return self._block


def get_bus_emt_template(grid: MultiCircuit,
                         bus: Bus):
    """
    Initialize 3ph bus block
    A bus will have the phases of the branches connected to it
    :param grid: Multicircuit
    :param bus: Bus
    :param vf: VarFactory
    :param is_dc: Whether this is a DC bus
    :return:
    """

    vf = grid.var_factory
    mask = [False, False, False, False]  # [N, A, B, C]
    if not bus.is_dc:
        ys_phase_device_types = {
            DeviceType.LineDevice,
        }
        transformer_phase_device_types = {
            DeviceType.Transformer2WDevice,
            DeviceType.WindingDevice,
        }
        abc_phase_device_types = {
            DeviceType.VscDevice,
            DeviceType.SeriesReactanceDevice,
            DeviceType.UpfcDevice,
            DeviceType.SwitchDevice,
            DeviceType.HVDCLineDevice,
            DeviceType.DCLineDevice,
        }

        for branch in grid.get_branches_iter(add_vsc=True, add_switch=True, add_hvdc=True):
            if bus == branch.bus_from or bus == branch.bus_to:
                if branch.device_type in ys_phase_device_types and branch.ys is not None:
                    mask[0] |= bool(branch.ys.phN)
                    mask[1] |= bool(branch.ys.phA)
                    mask[2] |= bool(branch.ys.phB)
                    mask[3] |= bool(branch.ys.phC)
                elif branch.device_type in transformer_phase_device_types:
                    mask[1] = True
                    mask[2] = True
                    mask[3] = True
                elif branch.device_type in abc_phase_device_types:
                    mask[1] = True
                    mask[2] = True
                    mask[3] = True
                else:
                    mask[1] = True
                    mask[2] = True
                    mask[3] = True

        if not any(mask):
            # The dynamic editor can open EMT templates before the network has any EMT-aware branches.
            # In that case we expose a default ABC shell so the user can still build and attach EMT models.
            mask[0] = True
            mask[1] = True
            mask[2] = True
            mask[3] = True
        else:
            pass

    # choose template depending on the number of phases
    bus.emt_model = BusEmtTemplate(vf=vf, mask=mask, is_dc=bus.is_dc, name=f"{bus.name}_emt_template").block


def get_bus_emt_algebraic_vars(bus_emt_model: Block) -> Tuple[
    Optional[Var], Optional[Var], Optional[Var], Optional[Var]]:
    """
    Return the EMT bus algebraic voltage variables.

    For AC buses:
        returns (v_N, v_A, v_B, v_C)
        Missing phases are returned as None.

    For DC buses:
        returns (Vdc, None, None, None)

    :param bus_emt_model: EMT bus block
    :return: Tuple with four positions to preserve a stable API
    """
    external_mapping = bus_emt_model.external_mapping

    # DC bus
    vdc = external_mapping.get(VarPowerFlowRefferenceType.Vdc, None)
    if vdc is not None:
        return vdc, None, None, None

    # AC bus
    v_n = external_mapping.get(VarPowerFlowRefferenceType.v_N, None)
    v_a = external_mapping.get(VarPowerFlowRefferenceType.v_A, None)
    v_b = external_mapping.get(VarPowerFlowRefferenceType.v_B, None)
    v_c = external_mapping.get(VarPowerFlowRefferenceType.v_C, None)

    if v_n is None and v_a is None and v_b is None and v_c is None:
        raise ValueError("Invalid EMT bus model: no voltage algebraic variables found")

    return v_n, v_a, v_b, v_c
