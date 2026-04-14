# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0


from typing import Tuple

from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp
from VeraGridEngine.Devices.Injections.generator import Generator, BuildStatus


class Battery(Generator):
    """
    Battery
    """
    __slots__ = (
        'device_type',
        '_charge_efficiency',
        '_discharge_efficiency',
        '_max_soc',
        '_min_soc',
        'min_soc_charge',
        'charge_per_cycle',
        '_discharge_per_cycle',
        '_Enom',
        '_soc_0',
        'soc',
        'min_energy',
        'energy',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='Enom', units='MWh', tpe=float, definition='Nominal energy capacity.'),
        GCProp(key='max_soc', units='p.u.', tpe=float, definition='Minimum state of charge.'),
        GCProp(key='min_soc', units='p.u.', tpe=float, definition='Maximum state of charge.'),
        GCProp(key='soc_0', units='p.u.', tpe=float, definition='Initial state of charge.'),
        GCProp(key='charge_efficiency', units='p.u.', tpe=float, definition='Charging efficiency.'),
        GCProp(key='discharge_efficiency', units='p.u.', tpe=float, definition='Discharge efficiency.'),
        GCProp(key='discharge_per_cycle', units='p.u.', tpe=float, definition=''),
    )

    def __init__(self,
                 name='batt',
                 idtag=None,
                 code="",
                 P=0.0,
                 Pmin=-9999,
                 Pmax=9999,
                 Q=0.0,
                 Qmin=-9999,
                 Qmax=9999,
                 power_factor=0.8,
                 vset=1.0,
                 is_controlled=True,
                 Snom=9999,
                 Enom=9999,
                 Cost=1.0,
                 active=True,
                 Sbase=100,
                 enabled_dispatch=True,
                 mttf=0.0, mttr=0.0,
                 charge_efficiency=0.9,
                 discharge_efficiency=0.9,
                 max_soc=0.99, min_soc=0.3, soc=0.8,
                 charge_per_cycle=0.1, discharge_per_cycle=0.1,
                 r1=1e-20, x1=1e-20,
                 r0=1e-20, x0=1e-20,
                 r2=1e-20, x2=1e-20,
                 capex=0, opex=0,
                 srap_enabled: bool = True,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """
        :ref:`Battery<battery>` (voltage controlled and dispatchable).
        :param name: Name of the battery
        :param idtag:
        :param P: Active power in MW
        :param power_factor: Power factor
        :param vset: Voltage setpoint in per unit
        :param is_controlled: Is the unit voltage controlled (if so, the connection bus becomes a PV bus)
        :param Qmin: Minimum reactive power in MVAr
        :param Qmax: Maximum reactive power in MVAr
        :param Snom: Nominal apparent power in MVA
        :param Enom: Nominal energy capacity in MWh
        :param Pmin: Minimum dispatchable power in MW
        :param Pmax: Maximum dispatchable power in MW
        :param Cost: Operational cost in Eur (or other e) per MW
        :param active: Is the battery active?
        :param Sbase: Base apparent power in MVA
        :param enabled_dispatch: Is the battery enabled for OPF?
        :param mttf: Mean time to failure in hours
        :param mttr: Mean time to recovery in hours
        :param charge_efficiency: Efficiency when charging
        :param discharge_efficiency: Efficiency when discharging
        :param max_soc: Maximum state of charge
        :param min_soc: Minimum state of charge
        :param soc: Current state of charge
        :param charge_per_cycle: Per unit of power to take per cycle when charging
        :param discharge_per_cycle: Per unit of power to deliver per cycle when discharging
        :param r1:
        :param x1:
        :param r0:
        :param x0:
        :param r2:
        :param x2:
        :param capex:
        :param opex:
        :param build_status:
        """
        Generator.__init__(self, name=name,
                           idtag=idtag,
                           code=code,
                           P=P,
                           Pmin=Pmin, Pmax=Pmax,
                           Q=Q,
                           Qmin=Qmin, Qmax=Qmax, Snom=Snom,
                           power_factor=power_factor,
                           vset=vset,
                           is_controlled=is_controlled,
                           active=active,
                           Cost=Cost,
                           Sbase=Sbase,
                           enabled_dispatch=enabled_dispatch,
                           mttf=mttf,
                           mttr=mttr,
                           r1=r1, x1=x1,
                           r0=r0, x0=x0,
                           r2=r2, x2=x2,
                           capex=capex,
                           opex=opex,
                           srap_enabled=srap_enabled,
                           build_status=build_status)

        # type of this device
        self.device_type = DeviceType.BatteryDevice

        self.charge_efficiency = float(charge_efficiency)

        self.discharge_efficiency = float(discharge_efficiency)

        self.max_soc = float(max_soc)

        self.min_soc = float(min_soc)

        self.min_soc_charge = (self.max_soc + self.min_soc) / 2  # SoC state to force the battery charge

        self.charge_per_cycle = float(charge_per_cycle)  # charge 10% per cycle

        self.discharge_per_cycle = float(discharge_per_cycle)

        self.Enom = float(Enom)

        self.soc_0 = float(soc)

        self.soc = float(soc)

        self.min_energy = self.Enom * self.min_soc

        self.energy = self.Enom * self.soc


    def __iadd__(self, other: "Battery"):
        """
        Add another generator here
        :param other: Generator to add
        """
        super().__iadd__(other)
        self.Enom += other.Enom

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def Enom(self) -> float:
        """
        Get ``Enom``.

        :return: float
        """
        return self._Enom

    @Enom.setter
    def Enom(self, val: float) -> None:
        """
        Set ``Enom``.

        :param val: Value to assign.
        :return: None
        """
        self._Enom = float(val)

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
    def soc_0(self) -> float:
        """
        Get ``soc_0``.

        :return: float
        """
        return self._soc_0

    @soc_0.setter
    def soc_0(self, val: float) -> None:
        """
        Set ``soc_0``.

        :param val: Value to assign.
        :return: None
        """
        self._soc_0 = float(val)

    @property
    def charge_efficiency(self) -> float:
        """
        Get ``charge_efficiency``.

        :return: float
        """
        return self._charge_efficiency

    @charge_efficiency.setter
    def charge_efficiency(self, val: float) -> None:
        """
        Set ``charge_efficiency``.

        :param val: Value to assign.
        :return: None
        """
        self._charge_efficiency = float(val)

    @property
    def discharge_efficiency(self) -> float:
        """
        Get ``discharge_efficiency``.

        :return: float
        """
        return self._discharge_efficiency

    @discharge_efficiency.setter
    def discharge_efficiency(self, val: float) -> None:
        """
        Set ``discharge_efficiency``.

        :param val: Value to assign.
        :return: None
        """
        self._discharge_efficiency = float(val)

    @property
    def discharge_per_cycle(self) -> float:
        """
        Get ``discharge_per_cycle``.

        :return: float
        """
        return self._discharge_per_cycle

    @discharge_per_cycle.setter
    def discharge_per_cycle(self, val: float) -> None:
        """
        Set ``discharge_per_cycle``.

        :param val: Value to assign.
        :return: None
        """
        self._discharge_per_cycle = float(val)
