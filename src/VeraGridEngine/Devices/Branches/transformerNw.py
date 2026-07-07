# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Sequence, Tuple, Union, List

import numpy as np

from VeraGridEngine.Devices.Branches.transformer_type import get_impedances
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.Devices.Parents.editable_device import GCProp, get_at
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Profiles import ProfileBool
from VeraGridEngine.enumerations import BuildStatus, DeviceType, PrpCat, SubObjectType

class ImpedanceTriplet:
    __slots__ = ("i", "j", "imp")
    def __init__(self, i: int = 0, j: int = 0, imp:complex = complex(0,0)) -> None:
        self.i = i
        self.j = j
        self.imp = imp

    def to_list(self) -> List[int|float]:
        return [self.i, self.j, self.imp.real, self.imp.imag]

    def from_list(self, value: List[int|float]) -> "ImpedanceTriplet":
        self.i = int(value[0])
        self.j = int(value[1])
        self.imp = complex(value[2], value[3])
        return self

class ImpedanceTripletList:
    def __init__(self):
        self.__list = []
    def append(self, imp: ImpedanceTriplet) -> None:
        self.__list.append(imp)
    def to_list(self) -> List[ImpedanceTripletList]:
        return [x.to_list() for x in self.__list]
    def parse(self, data: List[List[int|float]]) -> None:
        for entry in data:
            self.append(ImpedanceTriplet().from_list(entry))



class TransformerNW(PhysicalDevice):
    """
    Generic N-winding transformer represented as a set of windings connected to a
    common internal star bus.

    The leakage data is stored per winding. Shared core-loss data is represented by
    ``Pfe`` and ``I0`` at the transformer level and mapped through ``get_impedances``.
    To avoid counting the magnetizing branch multiple times, the resulting shunt
    admittance is assigned to the first winding only.
    """

    __slots__ = (
        "bus0",
        "cn0",
        "_buses",
        "_windings",
        "_active",
        "_active_prof",
        "_Pfe",
        "_I0",
        "_x",
        "_y",
        "_internal_impedances"
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name="bus0",
            units="",
            tpe=DeviceType.BusDevice,
            definition="Middle point connection bus.",
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name="active",
            units="",
            tpe=bool,
            definition="Is active?",
            profile_name="active_prof",
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name="winding_count",
            units="",
            tpe=int,
            definition="Number of windings.",
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name="Pfe",
            units="kW",
            tpe=float,
            definition="Iron loss",
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name="I0",
            units="%",
            tpe=float,
            definition="No-load current",
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name="x",
            units="px",
            tpe=float,
            definition="x position",
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name="y",
            units="px",
            tpe=float,
            definition="y position",
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name="internal_impedances",
            units="p.u.",
            tpe= SubObjectType.ImpedanceTripletList,
            definition="Internal Impedance List",
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self,
                 idtag: Union[str, None] = None,
                 code: str = "",
                 name: str = "TransformerNW",
                 bus0: Bus | None = None,
                 winding_count: int | None = None,
                 buses: Sequence[Bus | None] | None = None,
                 active: bool = True,
                 Pfe: float = 0.0,
                 I0: float = 0.0,
                 x: float = 0.0,
                 y: float = 0.0,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """
        Constructor
        :param idtag: Unique identifier
        :param code: Secondary identifier
        :param name: Name of the transformer
        :param bus0: Internal star-point bus. If ``None``, an internal bus is created automatically
        :param winding_count: Number of windings to allocate. If ``None``, it is inferred from ``buses`` and
                              falls back to 3
        :param buses: Sequence of terminal buses, one per winding. If provided, those buses are assigned to the
                      first winding slots
        :param active: Is active?
        :param Pfe: Shared iron-core losses in kW for the whole transformer
        :param I0: Shared no-load current in % for the whole transformer
        :param x: Graphical x position (px)
        :param y: Graphical y position (px)
        :param build_status: Device build status
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code=code,
                                device_type=DeviceType.TransformerNwDevice,
                                build_status=build_status)

        if bus0 is None:
            self.bus0 = Bus(name=name + "_bus", Vnom=1.0, xpos=x, ypos=y, is_internal=True)
        else:
            bus0.internal = True
            bus0.Vnom = 1.0
            self.bus0 = bus0
        self.cn0 = None

        self.active = bool(active)
        self._active_prof = ProfileBool(default_value=self.active)

        self._Pfe = float(Pfe)
        self._I0 = float(I0)

        self._buses: list[Bus | None] = list()
        self._windings: list[Winding] = list()

        self.x = float(x)
        self.y = float(y)

        self._internal_impedances = ImpedanceTripletList()

        self.initialize_windings(winding_count=winding_count, buses=buses)



    @property
    def active_prof(self) -> ProfileBool:
        """
        Cost profile
        :return: Profile
        """
        return self._active_prof

    @active_prof.setter
    def active_prof(self, val: Union[ProfileBool, np.ndarray]):
        if isinstance(val, ProfileBool):
            self._active_prof = val
        elif isinstance(val, np.ndarray):
            self._active_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + "not supported to be set into a active_prof")

    def get_active_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.active, self.active_prof, t)

    @property
    def winding_count(self) -> int:
        """
        Number of windings in the transformer.
        """
        return len(self._windings)

    @winding_count.setter
    def winding_count(self, val: int) -> None:
        self.set_winding_count(count=int(val))

    @property
    def buses(self) -> Tuple[Bus | None, ...]:
        """
        Terminal buses attached to the windings.
        """
        return tuple(self._buses)

    @property
    def windings(self) -> Tuple[Winding, ...]:
        """
        Winding objects connected to the internal bus.
        """
        return tuple(self._windings)

    @property
    def internal_impedances(self) -> ImpedanceTripletList:
        """
        Internal impedances of transformer model
        """
        return self._internal_impedances

    @internal_impedances.setter
    def internal_impedances(self, val: ImpedanceTripletList):
        if isinstance(val, ImpedanceTripletList):
            self._internal_impedances = val
        else:
            raise ValueError("Internal impedances in incorrect format")

    def all_connected(self) -> bool:
        """
        Check that all windings are connected to a terminal bus.
        """
        return bool(self._buses) and all(bus is not None for bus in self._buses)

    def get_bus(self, i: int) -> Bus | None:
        """
        Get terminal bus from an integer index.
        """
        return self._buses[i]

    def get_winding(self, i: int) -> Winding:
        """
        Get winding from an integer index.
        """
        return self._windings[i]

    def _prepare_winding(self, winding: Winding, bus: Bus | None, index: int) -> Winding:
        winding.bus_from = bus
        winding.bus_to = self.bus0

        if winding.name == "Winding":
            winding.name = f"{self.name}_W{index + 1}"

        hv = winding.HV
        lv = winding.LV

        if hv is None and bus is not None:
            hv = bus.Vnom
        elif hv is None:
            hv = 1.0

        if lv is None or lv <= 0.0:
            lv = 1.0

        if bus is None:
            winding.HV = hv
            winding.LV = lv
        else:
            winding.set_hv_and_lv(HV=hv, LV=lv)

        if winding.Sn <= 0.0 < winding.rate:
            winding.Sn = winding.rate
        elif winding.rate <= 0.0 < winding.Sn:
            winding.rate = winding.Sn

        return winding

    def set_bus(self, i: int, bus: Bus | None) -> None:
        """
        Set terminal bus and keep the associated winding in sync.
        """
        self._buses[i] = bus
        winding = self._windings[i]
        winding.bus_from = bus
        winding.bus_to = self.bus0

        if bus is not None:
            winding.set_hv_and_lv(HV=winding.HV, LV=winding.LV)

    def set_winding(self, i: int, winding: Winding, bus: Bus | None = None) -> None:
        """
        Replace a winding at position ``i``.
        """
        target_bus = winding.bus_from if bus is None else bus
        prepared = self._prepare_winding(winding=winding, bus=target_bus, index=i)
        self._windings[i] = prepared
        self._buses[i] = target_bus

    def add_winding(self,
                    bus: Bus | None = None,
                    winding: Winding | None = None,
                    w_idtag: Union[str, None] = None,
                    nominal_voltage: float | None = None,
                    nominal_power: float = 0.0) -> Winding:
        """
        Add a winding to the transformer.
        """
        index = len(self._windings)

        if winding is None:
            hv = nominal_voltage if nominal_voltage is not None else (bus.Vnom if bus is not None else 1.0)
            rate = nominal_power if nominal_power > 0.0 else 1.0
            sn = nominal_power if nominal_power > 0.0 else 0.001
            winding = Winding(bus_from=bus,
                              bus_to=self.bus0,
                              name=f"{self.name}_W{index + 1}",
                              idtag=w_idtag,
                              HV=hv,
                              LV=1.0,
                              nominal_power=sn,
                              rate=rate,
                              active=self.active)

        prepared = self._prepare_winding(winding=winding,
                                         bus=bus if bus is not None else winding.bus_from,
                                         index=index)
        self._windings.append(prepared)
        self._buses.append(prepared.bus_from)
        return prepared

    def delete_winding(self, i: int) -> Winding:
        """
        Delete a winding by index and return it.
        """
        self._buses.pop(i)
        return self._windings.pop(i)

    def initialize_windings(self,
                            winding_count: int | None = None,
                            buses: Sequence[Bus | None] | None = None) -> None:
        """
        Initialize the transformer winding set from a winding count and optional buses.
        """
        self._buses = list()
        self._windings = list()

        buses_list = list(buses) if buses is not None else list()
        if winding_count is None:
            target_count = len(buses_list) if len(buses_list) > 0 else 3
        else:
            target_count = max(int(winding_count), len(buses_list))

        for i in range(target_count):
            bus = buses_list[i] if i < len(buses_list) else None
            nominal_voltage = bus.Vnom if bus is not None else 1.0
            self.add_winding(bus=bus, nominal_voltage=nominal_voltage, nominal_power=0.0)

    def set_winding_count(self, count: int) -> None:
        """
        Resize the winding list preserving existing winding objects when possible.
        """
        target_count = max(int(count), 1)
        current_count = len(self._windings)

        if target_count == current_count:
            return

        if target_count < current_count:
            del self._buses[target_count:]
            del self._windings[target_count:]
            return

        for _ in range(current_count, target_count):
            self.add_winding(bus=None, nominal_voltage=1.0, nominal_power=0.0)

    def recalculate_windings_from_definition(self, Sbase: float = 100.0) -> None:
        """
        Recompute the winding per-unit values from the design data stored in each
        winding plus the shared core-loss values stored at the transformer level.
        """
        for i, winding in enumerate(self._windings):
            nominal_power = winding.Sn if winding.Sn > 0.0 else winding.rate
            if nominal_power <= 0.0:
                nominal_power = 1.0

            winding.Sn = nominal_power
            if winding.rate <= 0.0:
                winding.rate = nominal_power

            hv = winding.HV if winding.HV is not None else (winding.bus_from.Vnom if winding.bus_from is not None else 1.0)
            lv = winding.LV if winding.LV is not None and winding.LV > 0.0 else 1.0

            z_series, y_shunt = get_impedances(
                VH_bus=hv,
                VL_bus=lv,
                Sn=nominal_power,
                HV=hv,
                LV=lv,
                Pcu=winding.Pcu,
                Pfe=self.Pfe if i == 0 else 0.0,
                I0=self.I0 if i == 0 else 0.0,
                Vsc=winding.Vsc,
                Sbase=Sbase,
                GR_hv1=0.5,
            )

            winding.R = np.round(z_series.real, 6)
            winding.X = np.round(z_series.imag, 6)

            if i == 0:
                winding.G = np.round(y_shunt.real, 6)
                winding.B = np.round(y_shunt.imag, 6)
            else:
                winding.G = 0.0
                winding.B = 0.0

    def fill_from_design_values(self, Pfe: float, I0: float, Sbase: float) -> None:
        """
        Fill winding per-unit values from each winding's design data and the shared
        transformer core-loss data.
        """
        self._Pfe = float(Pfe)
        self._I0 = float(I0)
        self.recalculate_windings_from_definition(Sbase=Sbase)

    @property
    def Pfe(self) -> float:
        """
        Shared iron loss in kW.
        """
        return self._Pfe

    @Pfe.setter
    def Pfe(self, value: float) -> None:
        self._Pfe = float(value)
        self.recalculate_windings_from_definition(Sbase=100.0)

    @property
    def I0(self) -> float:
        """
        Shared no-load current in %.
        """
        return self._I0

    @I0.setter
    def I0(self, value: float) -> None:
        self._I0 = float(value)
        self.recalculate_windings_from_definition(Sbase=100.0)

    @property
    def active(self) -> bool:
        """
        Get ``active``.
        """
        return self._active

    @active.setter
    def active(self, val: bool) -> None:
        """
        Set ``active``.
        """
        self._active = bool(val)

    @property
    def x(self) -> float:
        """
        Get ``x``.
        """
        return self._x

    @x.setter
    def x(self, val: float) -> None:
        """
        Set ``x``.
        """
        self._x = float(val)

    @property
    def y(self) -> float:
        """
        Get ``y``.
        """
        return self._y

    @y.setter
    def y(self, val: float) -> None:
        """
        Set ``y``.
        """
        self._y = float(val)
