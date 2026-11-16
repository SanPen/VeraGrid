# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
from typing import Union, TYPE_CHECKING, Tuple
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.enumerations import DeviceType, SubObjectType, BuildStatus, PrpCat
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Branches.line_locations import LineLocations
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import get_at

if TYPE_CHECKING:
    from VeraGridEngine.Devices.types import CONNECTION_TYPE
    from VeraGridEngine.Devices.Substation.substation import Substation


class FluidPath(PhysicalDevice):
    __slots__ = (
        'source',
        'target',
        '_min_flow',
        '_max_flow',
        '_min_flow_prof',
        '_max_flow_prof',
        '_loss_factor',
        '_loss_factor_prof',
        'color',
        '_locations',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='source',
            units="",
            tpe=DeviceType.FluidNodeDevice,
            definition="Source node",
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='target',
            units="",
            tpe=DeviceType.FluidNodeDevice,
            definition="Target node",
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='min_flow',
            units="m3/s",
            tpe=float,
            definition="Minimum flow",
            profile_name='min_flow_prof',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='max_flow',
            units="m3/s",
            tpe=float,
            definition="Maximum flow",
            profile_name='max_flow_prof',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='loss_factor',
            units='p.u.',
            tpe=float,
            definition='Fraction of forward fluid flow lost during transfer.',
            profile_name='loss_factor_prof',
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='locations',
            units='',
            tpe=SubObjectType.LineLocations,
            definition='Locations',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='color',
            units='',
            tpe=str,
            definition='Color to paint the device in the map diagram',
            is_color=True,
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self,
                 name: str = '',
                 idtag: Union[str, None] = None,
                 code: str = '',
                 source: FluidNode = None,
                 target: FluidNode = None,
                 min_flow: float = 0.0,
                 max_flow: float = 0.0,
                 loss_factor: float = 0.0,
                 color: str | None = None,
                 build_status: BuildStatus = BuildStatus.Commissioned ):
        """
        Fluid path
        :param name:Name of the fluid transporter
        :param idtag: UUID
        :param code: secondary ID
        :param source: source of fluid (direction matters)
        :param target: target for the fluid (direction matters)
        :param min_flow: minimum flow (m3/s)
        :param max_flow: maximum flow (m3/s)
        :param color: color of the fluid
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code=code,
                                device_type=DeviceType.FluidPathDevice,
                                build_status=build_status)

        self.source = source
        self.target = target
        self.min_flow = float(min_flow)
        self.max_flow = float(max_flow)
        self._min_flow_prof = ProfileFloat(default_value=self.min_flow)
        self._max_flow_prof = ProfileFloat(default_value=self.max_flow)
        self.loss_factor = float(loss_factor)
        self._loss_factor_prof = ProfileFloat(default_value=self.loss_factor)

        self.color = color if color is not None else "#00aad4"  # nice blue color

        # Line locations
        self._locations: LineLocations = LineLocations()


    def copy(self):
        """
        Make a deep copy of this object
        :return: Copy of this object
        """

        # make a new instance (separated object in memory)
        fluid_path = FluidPath()

        fluid_path.source = self.source
        fluid_path.target = self.target
        fluid_path.min_flow = self.min_flow
        fluid_path.max_flow = self.max_flow
        fluid_path.loss_factor = self.loss_factor
        fluid_path.min_flow_prof = self.min_flow_prof
        fluid_path.max_flow_prof = self.max_flow_prof
        fluid_path.loss_factor_prof = self.loss_factor_prof

        return fluid_path

    @property
    def loss_factor(self) -> float:
        """Get forward-flow loss factor.

        :return: Fraction of forward flow lost during transfer.
        """
        return self._loss_factor

    @loss_factor.setter
    def loss_factor(self, val: float) -> None:
        """Set forward-flow loss factor.

        :param val: Fraction of forward flow lost during transfer.
        :return: None.
        """
        self._loss_factor = float(val)

    @property
    def loss_factor_prof(self) -> ProfileFloat:
        """Get the forward-flow loss profile.

        :return: Snapshot-aligned loss factors.
        """
        return self._loss_factor_prof

    @loss_factor_prof.setter
    def loss_factor_prof(self, val: Union[ProfileFloat, np.ndarray]) -> None:
        """Set the forward-flow loss profile.

        :param val: Native profile or snapshot-aligned values.
        :return: None.
        """
        if isinstance(val, ProfileFloat):
            self._loss_factor_prof = val
        elif isinstance(val, np.ndarray):
            self._loss_factor_prof.set(arr=val)
        else:
            raise TypeError(f"Unsupported fluid-path loss-factor profile: {type(val)!r}")

    def get_loss_factor_at(self, t: int | None) -> float:
        """Get forward-flow loss at one snapshot.

        :param t: Snapshot index, or ``None`` for the scalar value.
        :return: Fraction of forward flow lost during transfer.
        """
        return get_at(self.loss_factor, self.loss_factor_prof, t)

    @property
    def locations(self) -> LineLocations:
        """
        Cost profile
        :return: Profile
        """
        return self._locations

    @locations.setter
    def locations(self, val: Union[LineLocations, np.ndarray]):
        if isinstance(val, LineLocations):
            self._locations = val
        elif isinstance(val, np.ndarray):
            self._locations.set(data=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a locations')

    def get_from_and_to_objects(self) -> Tuple[CONNECTION_TYPE, CONNECTION_TYPE, bool]:
        """
        Get the from and to connection objects of the branch
        :return: Object from, Object to, is it ok?
        """

        # Pick the right bus
        bus_from = self.source
        bus_to = self.target

        ok = bus_from is not None and bus_to is not None
        return bus_from, bus_to, ok

    def get_substation_from(self) -> Union[Substation, None]:
        """
        Try to get the substation at the source side.

        :return: Source electrical bus substation, or ``None``.
        """
        substation: Union[Substation, None] = None

        # Fluid paths are connected through fluid nodes, which carry the electrical bus.
        if self.source is not None:
            if self.source.bus is not None:
                substation = self.source.bus.substation
            else:
                substation = None
        else:
            substation = None

        return substation

    def get_substation_to(self) -> Union[Substation, None]:
        """
        Try to get the substation at the target side.

        :return: Target electrical bus substation, or ``None``.
        """
        substation: Union[Substation, None] = None

        # Fluid paths are connected through fluid nodes, which carry the electrical bus.
        if self.target is not None:
            if self.target.bus is not None:
                substation = self.target.bus.substation
            else:
                substation = None
        else:
            substation = None

        return substation

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def min_flow(self) -> float:
        """
        Get ``min_flow``.

        :return: float
        """
        return self._min_flow

    @min_flow.setter
    def min_flow(self, val: float) -> None:
        """
        Set ``min_flow``.

        :param val: Value to assign.
        :return: None
        """
        self._min_flow = float(val)

    @property
    def min_flow_prof(self) -> ProfileFloat:
        """Get the minimum-flow profile.

        :return: Snapshot-aligned minimum flow.
        """
        return self._min_flow_prof

    @min_flow_prof.setter
    def min_flow_prof(self, val: Union[ProfileFloat, np.ndarray]) -> None:
        """Set the minimum-flow profile.

        :param val: Native profile or snapshot-aligned values.
        :return: None.
        """
        if isinstance(val, ProfileFloat):
            self._min_flow_prof = val
        elif isinstance(val, np.ndarray):
            self._min_flow_prof.set(arr=val)
        else:
            raise TypeError(f"Unsupported fluid-path minimum-flow profile: {type(val)!r}")

    def get_min_flow_at(self, t: int | None) -> float:
        """Get minimum flow at one snapshot.

        :param t: Snapshot index, or ``None`` for the scalar value.
        :return: Minimum flow in m3/s.
        """
        return get_at(self.min_flow, self.min_flow_prof, t)

    @property
    def max_flow(self) -> float:
        """
        Get ``max_flow``.

        :return: float
        """
        return self._max_flow

    @max_flow.setter
    def max_flow(self, val: float) -> None:
        """
        Set ``max_flow``.

        :param val: Value to assign.
        :return: None
        """
        self._max_flow = float(val)

    @property
    def max_flow_prof(self) -> ProfileFloat:
        """Get the maximum-flow profile.

        :return: Snapshot-aligned maximum flow.
        """
        return self._max_flow_prof

    @max_flow_prof.setter
    def max_flow_prof(self, val: Union[ProfileFloat, np.ndarray]) -> None:
        """Set the maximum-flow profile.

        :param val: Native profile or snapshot-aligned values.
        :return: None.
        """
        if isinstance(val, ProfileFloat):
            self._max_flow_prof = val
        elif isinstance(val, np.ndarray):
            self._max_flow_prof.set(arr=val)
        else:
            raise TypeError(f"Unsupported fluid-path maximum-flow profile: {type(val)!r}")

    def get_max_flow_at(self, t: int | None) -> float:
        """Get maximum flow at one snapshot.

        :param t: Snapshot index, or ``None`` for the scalar value.
        :return: Maximum flow in m3/s.
        """
        return get_at(self.max_flow, self.max_flow_prof, t)
