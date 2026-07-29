# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.enumerations import DeviceType, FaultType, MethodShortCircuit, PhasesShortCircuit, PrpCat


class ShortCircuitEvent(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        '_fault_type',
        '_method',
        '_phases',
        '_active',
        '_constz',
        '_r_fault',
        '_x_fault',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='fault_type',
            units='',
            tpe=FaultType,
            definition='Type of short circuit',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='method',
            units='',
            tpe=MethodShortCircuit,
            definition='Method of short circuit',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='phases',
            units='',
            tpe=PhasesShortCircuit,
            definition='Phases involved',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='active',
            units='',
            tpe=bool,
            definition='If true the short-circuit activates when calculated, otherwise is deactivated.',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='constz',
            units='',
            tpe=bool,
            definition='If true the constant power and current loads are linearised.',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='r_fault',
            units='p.u.',
            tpe=float,
            definition='Resistance of the fault.This is used for short circuit studies.',
            profile_name='',
            cat=[PrpCat.REL],
        ),
        GCProp(
            prop_name='x_fault',
            units='p.u.',
            tpe=float,
            definition='Reactance of the fault.This is used for short circuit studies.',
            profile_name='',
            cat=[PrpCat.REL],
        ),
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 idtag: Union[str, None] = None,
                 name="Fault",
                 code='',
                 active: bool = True,
                 constz: bool = True,
                 fault_type: FaultType = FaultType.LLLG,
                 method: MethodShortCircuit = MethodShortCircuit.sequences,
                 phases: PhasesShortCircuit = PhasesShortCircuit.abc,
                 r_fault=0.0,
                 x_fault=0.0,
                 comment: str = ""):
        """
        Short circuit event
        :param device: Some device to point at
        :param idtag: String. Element unique identifier
        :param name: String. Contingency name
        :param code: String. Contingency code name
        :param active: If true the investment activates when applied, otherwise is deactivated
        :param constz: If true the constant power and current loads are linearised.
        :param fault_type: The short-circuit type to be simulated, for instance, SLG means single-line to ground
        :param method: The method used to perform the short-cicuit analysis
        :param phases: The phases involved in the short-circuit, only needed if method = phases
        :param comment: Comment
        :param r_fault: Resistance of the fault in per unit (SC only)
        :param x_fault: Reactance of the fault in per unit (SC only)
        """

        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=device,
                                     code=code,
                                     name=name,
                                     device_type=DeviceType.ShortCircuitEvent,
                                     comment=comment)

        self._fault_type: FaultType = fault_type
        self._method: MethodShortCircuit = method
        self._phases: PhasesShortCircuit = phases
        self.active: bool = active
        self.constz: bool = constz
        # short circuit impedance
        self._r_fault = float(r_fault)
        self._x_fault = float(x_fault)

    def _check(self):

        if self._fault_type == FaultType.LLLG:
            if self._phases != PhasesShortCircuit.abc:
                self._phases = PhasesShortCircuit.abc

    @property
    def fault_type(self) -> FaultType:
        """

        :return:
        """
        return self._fault_type

    @fault_type.setter
    def fault_type(self, val: FaultType):

        if self.auto_update_enabled:
            self._check()
        else:
            self._fault_type = val

    @property
    def phases(self) -> PhasesShortCircuit:
        """

        :return:
        """
        return self._phases

    @phases.setter
    def phases(self, val: PhasesShortCircuit):

        if self.auto_update_enabled:
            self._check()
        else:
            self._phases = val

    @property
    def method(self) -> MethodShortCircuit:
        """

        :return:
        """
        return self._method

    @method.setter
    def method(self, val: MethodShortCircuit):

        if self.auto_update_enabled:
            self._check()
        else:
            self._method = val

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def active(self) -> bool:
        """
        Get ``active``.

        :return: bool
        """
        return self._active

    @active.setter
    def active(self, val: bool) -> None:
        """
        Set ``active``.

        :param val: Value to assign.
        :return: None
        """
        self._active = bool(val)

    @property
    def constz(self) -> bool:
        """
        Get ``constz``.

        :return: bool
        """
        return self._constz

    @constz.setter
    def constz(self, val: bool) -> None:
        """
        Set ``constz``.

        :param val: Value to assign.
        :return: None
        """
        self._constz = bool(val)

    @property
    def r_fault(self) -> float:
        """
        Get ``r_fault``.

        :return: float
        """
        return self._r_fault

    @r_fault.setter
    def r_fault(self, val: float) -> None:
        """
        Set ``r_fault``.

        :param val: Value to assign.
        :return: None
        """
        self._r_fault = float(val)

    @property
    def x_fault(self) -> float:
        """
        Get ``x_fault``.

        :return: float
        """
        return self._x_fault

    @x_fault.setter
    def x_fault(self, val: float) -> None:
        """
        Set ``x_fault``.

        :param val: Value to assign.
        :return: None
        """
        self._x_fault = float(val)

    def get_fault_impedance(self) -> complex:
        """
        Get the fault impedance
        :return: complex value of fault impedance
        """
        return complex(self.r_fault, self.x_fault)