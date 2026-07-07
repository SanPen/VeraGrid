# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple
import numpy as np

from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, DeviceType
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp


class FluidNode(PhysicalDevice):
    __slots__ = (
        '_min_level',
        '_max_level',
        '_max_soc',
        '_min_soc',
        '_initial_level',
        '_spillage_cost',
        '_inflow',
        '_bus',
        'build_status',
        'color',
        '_inflow_prof',
        '_spillage_cost_prof',
        '_max_soc_prof',
        '_min_soc_prof',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='min_level', units='hm3', tpe=float,
                      definition="Minimum amount of fluid at the node/reservoir"),
        GCProp(key='max_level', units='hm3', tpe=float,
                      definition="Maximum amount of fluid at the node/reservoir"),
        GCProp(key='min_soc', units='p.u.', tpe=float,
                      definition="Minimum SOC of fluid at the node/reservoir",
                      profile_name='min_soc_prof'),
        GCProp(key='max_soc', units='p.u.', tpe=float,
                      definition="Maximum SOC of fluid at the node/reservoir",
                      profile_name='max_soc_prof'),
        GCProp(key='initial_level', units='hm3', tpe=float,
                      definition="Initial level of the node/reservoir"),
        GCProp(key='bus', units='', tpe=DeviceType.BusDevice,
                      definition='Electrical bus.', editable=False),
        GCProp(key='spillage_cost', units='e/(m3/s)', tpe=float,
                      definition='Cost of nodal spillage',
                      profile_name='spillage_cost_prof'),
        GCProp(key='inflow', units='m3/s', tpe=float,
                      definition='Flow of fluid coming from the rain',
                      profile_name='inflow_prof'),
        GCProp(key='color', units='', tpe=str, definition='Color to paint the device in the map diagram',
                      is_color=True),
    )

    def __init__(self,
                 name: str = '',
                 idtag: Union[str, None] = None,
                 code: str = '',
                 min_level: float = 0.0,
                 max_level: float = 0.0,
                 min_soc: float = 0.0,
                 max_soc: float = 1.0,
                 current_level: float = 0.0,
                 spillage_cost: float = 1000.0,
                 inflow: float = 0.0,
                 bus: Union[None, Bus] = None,
                 build_status: BuildStatus = BuildStatus.Commissioned,
                 color: str | None = None):
        """
        FluidNode
        :param name: name of the node
        :param idtag: UUID
        :param code: secondary code
        :param min_level: Minimum amount of fluid at the node/reservoir [m3]
        :param max_level: Maximum amount of fluid at the node/reservoir [m3]
        :param current_level: Initial level of the node/reservoir [m3]
        :param spillage_cost: Spillage cost [e/(m3/s)]
        :param inflow: Inflow from the rain [m3/s]
        :param bus: electrical bus they are linked with
        :param build_status
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code=code,
                                device_type=DeviceType.FluidNodeDevice,
                                build_status=build_status)

        self.min_level = float(min_level)  # hm3
        self.max_level = float(max_level)  # hm3
        self.max_soc = float(max_soc)  # p.u.
        self.min_soc = float(min_soc)  # p.u.
        self.initial_level = float(current_level)  # hm3
        self.spillage_cost = float(spillage_cost)  # m3/s
        self.inflow = float(inflow)  # m3/s
        self._bus: Bus | None = bus

        self.color = color if color is not None else "#00aad4"  # nice blue color

        self._inflow_prof = ProfileFloat(default_value=self.inflow)  # m3/s
        self._spillage_cost_prof = ProfileFloat(default_value=self.spillage_cost)  # e/(m3/s)

        self._max_soc_prof = ProfileFloat(default_value=self.max_soc)  # p.u.
        self._min_soc_prof = ProfileFloat(default_value=self.min_soc)  # p.u.










    @property
    def spillage_cost_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._spillage_cost_prof

    @spillage_cost_prof.setter
    def spillage_cost_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._spillage_cost_prof = val
        elif isinstance(val, np.ndarray):
            self._spillage_cost_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a spillage_cost_prof')

    def get_spillage_cost_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.spillage_cost, self.spillage_cost_prof, t)

    @property
    def inflow_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._inflow_prof

    @inflow_prof.setter
    def inflow_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._inflow_prof = val
        elif isinstance(val, np.ndarray):
            self._inflow_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a inflow_prof')

    def get_inflow_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.inflow, self.inflow_prof, t)

    @property
    def max_soc_prof(self) -> ProfileFloat:
        """
        Max soc profile
        :return: Profile
        """
        return self._max_soc_prof

    @max_soc_prof.setter
    def max_soc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._max_soc_prof = val
        elif isinstance(val, np.ndarray):
            self._max_soc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a max soc prof')

    def get_max_soc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.max_soc, self.max_soc_prof, t)

    @property
    def min_soc_prof(self) -> ProfileFloat:
        """
        Min soc profile
        :return: Profile
        """
        return self._min_soc_prof

    @min_soc_prof.setter
    def min_soc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._min_soc_prof = val
        elif isinstance(val, np.ndarray):
            self._min_soc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a min soc prof')

    def get_min_soc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.min_soc, self.min_soc_prof, t)

    def copy(self):
        """
        Make a deep copy of this object
        :return: Copy of this object
        """

        # make a new instance (separated object in memory)
        fluid_node = FluidNode()

        fluid_node.min_level = self.min_level  # hm3
        fluid_node.max_level = self.max_level  # hm3
        fluid_node.min_soc = self.min_soc  # p.u.
        fluid_node.max_soc = self.max_soc  # p.u.
        fluid_node.initial_level = self.initial_level  # hm3
        fluid_node.spillage_cost = self.spillage_cost  # m3/s
        fluid_node.inflow = self.inflow  # m3/s
        fluid_node._bus = self._bus
        fluid_node.build_status = self.build_status

        fluid_node.inflow_prof = self.inflow_prof  # m3/s
        fluid_node.spillage_cost_prof = self.spillage_cost_prof  # e/(m3/s)
        fluid_node.max_soc_prof = self.max_soc_prof  # m3
        fluid_node.min_soc_prof = self.min_soc_prof  # m3

        return fluid_node

    @property
    def bus(self) -> Bus | None:
        """
        Bus getter function
        :return: Bus
        """
        return self._bus

    @bus.setter
    def bus(self, val: Bus):
        """
        bus setter function
        :param val: Bus
        """
        if isinstance(val, Bus):
            self._bus = val
            self._bus.internal = True

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def min_level(self) -> float:
        """
        Get ``min_level``.

        :return: float
        """
        return self._min_level

    @min_level.setter
    def min_level(self, val: float) -> None:
        """
        Set ``min_level``.

        :param val: Value to assign.
        :return: None
        """
        self._min_level = float(val)

    @property
    def max_level(self) -> float:
        """
        Get ``max_level``.

        :return: float
        """
        return self._max_level

    @max_level.setter
    def max_level(self, val: float) -> None:
        """
        Set ``max_level``.

        :param val: Value to assign.
        :return: None
        """
        self._max_level = float(val)

    @property
    def min_soc(self) -> float:
        """
        Get ``min_soc``.

        :return: float
        """
        return self._min_soc

    @min_soc.setter
    def min_soc(self, val: float) -> None:
        """
        Set ``min_soc``.

        :param val: Value to assign.
        :return: None
        """
        self._min_soc = float(val)

    @property
    def max_soc(self) -> float:
        """
        Get ``max_soc``.

        :return: float
        """
        return self._max_soc

    @max_soc.setter
    def max_soc(self, val: float) -> None:
        """
        Set ``max_soc``.

        :param val: Value to assign.
        :return: None
        """
        self._max_soc = float(val)

    @property
    def initial_level(self) -> float:
        """
        Get ``initial_level``.

        :return: float
        """
        return self._initial_level

    @initial_level.setter
    def initial_level(self, val: float) -> None:
        """
        Set ``initial_level``.

        :param val: Value to assign.
        :return: None
        """
        self._initial_level = float(val)

    @property
    def spillage_cost(self) -> float:
        """
        Get ``spillage_cost``.

        :return: float
        """
        return self._spillage_cost

    @spillage_cost.setter
    def spillage_cost(self, val: float) -> None:
        """
        Set ``spillage_cost``.

        :param val: Value to assign.
        :return: None
        """
        self._spillage_cost = float(val)

    @property
    def inflow(self) -> float:
        """
        Get ``inflow``.

        :return: float
        """
        return self._inflow

    @inflow.setter
    def inflow(self, val: float) -> None:
        """
        Set ``inflow``.

        :param val: Value to assign.
        :return: None
        """
        self._inflow = float(val)
