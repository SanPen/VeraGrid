# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple

from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, SwitchGraphicType, PrpCat
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp


class Switch(BranchParent):
    """
    The **Switch** class represents the connections between nodes (i.e.
    :ref:`buses<bus>`) in **VeraGrid**. A Switch is a devices that cuts or allows the flow.
    """
    __slots__ = (
        '_R',
        '_X',
        '_retained',
        '_normal_open',
        '_rated_current',
        'graphic_type',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='R',
            units='pu',
            tpe=float,
            definition='Positive-sequence resistance',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='X',
            units='pu',
            tpe=float,
            definition='Positive-sequence reactance',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='retained',
            units="",
            tpe=bool,
            definition='Switch is retained',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='normal_open',
            units="",
            tpe=bool,
            definition='Normal position of the switch',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='rated_current',
            units="kA",
            tpe=float,
            definition='Rated current of the switch device.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='graphic_type',
            units='',
            tpe=SwitchGraphicType,
            definition='Graphic to use in the schematic.',
            cat=[PrpCat.All],
        ),
    )

    def __init__(self,
                 bus_from: Bus = None,
                 bus_to: Bus = None,
                 name='Switch',
                 idtag=None,
                 code='',
                 r=1e-20,
                 x=1e-20,
                 design_rate: float = 9999,
                 rate=9999.0,
                 active=True,
                 contingency_factor=1.0,
                 protection_rating_factor: float = 1.4,
                 retained=False,
                 normal_open=False,
                 rated_current=0.0,
                 graphic_type: SwitchGraphicType = SwitchGraphicType.CircuitBreaker):
        """
        Switch device
        :param bus_from: Bus from
        :param bus_to: Bus to
        :param name: Name of the branch
        :param idtag: UUID code
        :param code: secondary ID
        :param r: resistance in p.u.
        :param x: reactance in p.u.
        :param design_rate: design rate in p.u.
        :param rate: Branch rating (MW)
        :param active: is it active?
        :param contingency_factor: Rating factor in case of contingency
        :param graphic_type: SwitchGraphicType to represent the switch in the schematic
        """
        BranchParent.__init__(self,
                              name=name,
                              idtag=idtag,
                              code=code,
                              bus_from=bus_from,
                              bus_to=bus_to,
                              active=active,
                              reducible=True,
                              design_rate=design_rate,
                              rate=rate,
                              contingency_factor=contingency_factor,
                              protection_rating_factor=protection_rating_factor,
                              contingency_enabled=True,
                              monitor_loading=True,
                              mttf=0.0,
                              mttr=0.0,
                              build_status=BuildStatus.Commissioned,
                              capex=0,
                              opex=0,
                              cost=0,
                              temp_base=25,
                              temp_oper=25,
                              alpha=0.0033,
                              device_type=DeviceType.SwitchDevice)

        # total impedance and admittance in p.u.
        self.R = float(r)
        self.X = float(x)

        # self.is_open = is_open
        self.retained = bool(retained)

        self.normal_open = bool(normal_open)
        self.rated_current = float(rated_current)

        self.graphic_type: SwitchGraphicType = graphic_type

    @property
    def R(self) -> float:
        """
        Get ``R``.

        :return: float
        """
        return self._R

    @R.setter
    def R(self, val: float) -> None:
        """
        Set ``R``.

        :param val: Value to assign.
        :return: None
        """
        self._R = float(val)

    @property
    def X(self) -> float:
        """
        Get ``X``.

        :return: float
        """
        return self._X

    @X.setter
    def X(self, val: float) -> None:
        """
        Set ``X``.

        :param val: Value to assign.
        :return: None
        """
        self._X = float(val)

    @property
    def retained(self) -> bool:
        """
        Get ``retained``.

        :return: bool
        """
        return self._retained

    @retained.setter
    def retained(self, val: bool) -> None:
        """
        Set ``retained``.

        :param val: Value to assign.
        :return: None
        """
        self._retained = bool(val)

    @property
    def normal_open(self) -> bool:
        """
        Get ``normal_open``.

        :return: bool
        """
        return self._normal_open

    @normal_open.setter
    def normal_open(self, val: bool) -> None:
        """
        Set ``normal_open``.

        :param val: Value to assign.
        :return: None
        """
        self._normal_open = bool(val)

    @property
    def rated_current(self) -> float:
        """
        Get ``rated_current``.

        :return: float
        """
        return self._rated_current

    @rated_current.setter
    def rated_current(self, val: float) -> None:
        """
        Set ``rated_current``.

        :param val: Value to assign.
        :return: None
        """
        self._rated_current = float(val)

    def change_base(self, Sbase_old: float, Sbase_new: float):
        """
        Change the impedance base
        :param Sbase_old: old base (MVA)
        :param Sbase_new: new base (MVA)
        """
        b = Sbase_new / Sbase_old

        self.R *= b
        self.X *= b

