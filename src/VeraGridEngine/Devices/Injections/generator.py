# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Union, Tuple
from matplotlib import pyplot as plt

from VeraGridEngine.basic_structures import Logger, CxVec
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import DeviceType, BuildStatus, SubObjectType, GeneratorType
from VeraGridEngine.Devices.Associations.association import Associations
from VeraGridEngine.Devices.Injections.generator_q_curve import GeneratorQCurve
from VeraGridEngine.Devices.Profiles import ProfileBool, ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent


def compute_q(p: float, pf: float) -> float:
    """
    Compute the reactive power from p and the power factor
    :param p: Active power
    :param pf: power factor
    :return: Reactive power
    """
    sign = 1.0 if pf >= 0.0 else -1.0
    if -1.0 <= pf <= 1.0:
        return sign * p * np.sqrt(1.0 / (pf * pf) - 1.0)
    else:
        return sign * p


def compute_pf(p: float, q: float) -> float:
    """
    Compute the power factor from p and q
    :param p: Active power
    :param q: Reactive power
    :return: Power factor
    """
    s = np.sqrt(p * p + q * q)
    sign = 1.0 if q >= 0.0 else -1.0
    if s > 0:
        return sign * p / s
    else:
        return sign


class Generator(InjectionParent):
    __slots__ = (
        'control_bus',
        'control_cn',
        '_P',
        '_P_prof',
        '_Pmax',
        '_Pmax_prof',
        '_Pmin',
        '_Pmin_prof',
        '_Q',
        '_Q_prof',
        '_Qmin_prof',
        '_Qmax_prof',
        'qmin_set',
        'qmax_set',
        '_srap_enabled',
        '_srap_enabled_prof',
        '_enabled_dispatch',
        '_enabled_dispatch_prof',
        '_R1',
        '_X1',
        '_R0',
        '_X0',
        '_R2',
        '_X2',
        '_Rs',
        '_Xs',
        '_Xm',
        '_Rr',
        '_Xr',
        '_Pf',
        '_Pf_prof',
        '_is_controlled',
        '_Snom',
        '_Vset',
        '_Vset_prof',
        '_use_reactive_power_curve',
        'q_curve',
        'custom_q_points',
        '_Cost2',
        '_Cost0',
        '_StartupCost',
        '_ShutdownCost',
        '_MinTimeUp',
        '_MinTimeDown',
        '_RampUp',
        '_RampDown',
        '_Cost2_prof',
        '_Cost0_prof',
        'emissions',
        'fuels',
        'Sbase',
        'freq',
        '_must_run',
        '_must_run_prof',
        'tpe'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (

        GCProp(key='P', units='MW', tpe=float, definition='Active power', profile_name='P_prof'),
        GCProp(key='Pmin', units='MW', tpe=float, definition='Minimum active power. Used in OPF.',
               profile_name='Pmin_prof'),
        GCProp(key='Pmax', units='MW', tpe=float, definition='Maximum active power. Used in OPF.',
               profile_name='Pmax_prof'),
        GCProp(key='Q', units='MVAr', tpe=float, definition='Reactive power', profile_name='Q_prof'),
        GCProp(key='Qmin', units='MVAr', tpe=float, definition='Minimum reactive power.',
               profile_name='Qmin_prof'),
        GCProp(key='Qmax', units='MVAr', tpe=float, definition='Maximum reactive power.',
               profile_name='Qmax_prof'),
        GCProp(key='is_controlled', units='', tpe=bool, definition='Is this generator voltage-controlled?'),
        GCProp(key='control_bus', units='', tpe=DeviceType.BusDevice, definition='Control bus',
               editable=True),
        GCProp(key='Pf', units='', tpe=float,
               definition='Power factor (cos(phi)). This is used for non-controlled generators.',
               profile_name='Pf_prof'),
        GCProp(key='Vset', units='p.u.', tpe=float,
               definition='Set voltage. This is used for controlled generators.', profile_name='Vset_prof'),
        GCProp(key='Snom', units='MVA', tpe=float, definition='Nominal power.'),

        GCProp(key='use_reactive_power_curve', units='', tpe=bool,
               definition='Use the reactive power capability curve?'),
        GCProp(key='q_curve', units='MVAr', tpe=SubObjectType.GeneratorQCurve,
               definition='Capability curve data (double click on the generator to edit)',
               editable=False, display=False),
        GCProp(key='R1', units='p.u.', tpe=float, definition='Total positive sequence resistance.'),
        GCProp(key='X1', units='p.u.', tpe=float, definition='Total positive sequence reactance.'),
        GCProp(key='R0', units='p.u.', tpe=float, definition='Total zero sequence resistance.'),
        GCProp(key='X0', units='p.u.', tpe=float, definition='Total zero sequence reactance.'),
        GCProp(key='R2', units='p.u.', tpe=float, definition='Total negative sequence resistance.'),
        GCProp(key='X2', units='p.u.', tpe=float, definition='Total negative sequence reactance.'),
        GCProp(key='Rs', units='p.u.', tpe=float, definition='Stator winding resistance (AG).'),
        GCProp(key='Xs', units='p.u.', tpe=float, definition='Stator leakage reactance (AG).'),
        GCProp(key='Xm', units='p.u.', tpe=float, definition='Magnetizing reactance (AG).'),
        GCProp(key='Rr', units='p.u.', tpe=float, definition='Rotor resistance (AG).'),
        GCProp(key='Xr', units='p.u.', tpe=float, definition='Rotor reactance (AG).'),
        GCProp(key='Cost2', units='e/MW²/h', tpe=float, definition='Generation quadratic cost. Used in OPF.',
               profile_name='Cost2_prof'),
        GCProp(key='Cost0', units='e/h', tpe=float, definition='Generation constant cost. Used in OPF.',
               profile_name='Cost0_prof'),
        GCProp(key='startup_cost', units='e/h', tpe=float, definition='Generation start-up cost. Used in OPF.',
               old_names=["StartupCost"]),
        GCProp(key='shutdown_cost', units='e/h', tpe=float, definition='Generation shut-down cost. Used in OPF.',
               old_names=["ShutdownCost"]),
        GCProp(key='min_time_up', units='h', tpe=float,
               definition='Minimum time that the generator has to be on when started. Used in OPF.',
               old_names=["MinTimeUp"]),
        GCProp(key='min_time_down', units='h', tpe=float,
               definition='Minimum time that the generator has to be off when shut down. Used in OPF.',
               old_names=["MinTimeDown"]),
        GCProp(key='ramp_up', units='MW/h', tpe=float,
               definition='Maximum amount of generation increase per hour.',
               old_names=["RampUp"]),
        GCProp(key='ramp_down', units='MW/h', tpe=float,
               definition='Maximum amount of generation decrease per hour.',
               old_names=["RampDown"]),
        GCProp(key='enabled_dispatch', units='', tpe=bool, profile_name="enabled_dispatch_prof",
               definition='Enabled for dispatch? Used in OPF.'),
        GCProp(key='must_run', units='', tpe=bool, profile_name="must_run_prof",
               definition='P >= Pmin constraint. Used in OPF with unit commitment active.'),
        GCProp(key='emissions', units='t/MWh', tpe=SubObjectType.Associations,
               definition='List of emissions', display=False),
        GCProp(key='fuels', units='t/MWh', tpe=SubObjectType.Associations,
               definition='List of fuels', display=False),
        GCProp(key='srap_enabled', units='', tpe=bool,
               definition='Is the unit available for SRAP participation?',
               editable=True, profile_name="srap_enabled_prof"),
        GCProp(key='tpe', units='', tpe=GeneratorType, definition='Machine type of the generator.'),
    )

    def __init__(self,
                 name='gen',
                 idtag: Union[str, None] = None,
                 code: str = '',
                 P: float = 0.0,
                 Q: float = 0.0,
                 power_factor: float = 0.8,
                 vset: float = 1.0,
                 is_controlled=True,
                 Qmin: float = -9999,
                 Qmax: float = 9999,
                 Snom: float = 9999,
                 active: bool = True,
                 Pmin: float = 0.0,
                 Pmax: float = 9999.0,
                 Cost: float = 1.0,
                 Cost2: float = 0.0,
                 Cost0: float = 0.0,
                 Sbase: float = 100,
                 enabled_dispatch=True,
                 mttf: float = 0.0,
                 mttr: float = 0.0,
                 q_points=None,
                 use_reactive_power_curve=False,
                 r1: float = 1e-20,
                 x1: float = 1e-20,
                 r0: float = 1e-20,
                 x0: float = 1e-20,
                 r2: float = 1e-20,
                 x2: float = 1e-20,
                 Rs: float = 1e-20,
                 Xs: float = 1e-20,
                 Xm: float = 1e-20,
                 Rr: float = 1e-20,
                 Xr: float = 1e-20,
                 freq=60.0,
                 capex: float = 0,
                 opex: float = 0,
                 srap_enabled: bool = True,
                 build_status: BuildStatus = BuildStatus.Commissioned,
                 must_run: bool = False,
                 startup_cost=0.0,
                 shutdown_cost=0.0,
                 min_time_up=0.0,
                 min_time_down=0.0,
                 ramp_up=1e20,
                 ramp_down=1e20,
                 tpe: GeneratorType = GeneratorType.Synchronous):
        """

        :param name: Name of the generator
        :param idtag: UUID code
        :param code: secondary code
        :param P: Active power in MW
        :param power_factor: Power factor
        :param vset: Voltage set point in per unit
        :param is_controlled: Is the generator voltage controlled?
        :param Qmin: Minimum reactive power in MVAr
        :param Qmax: Maximum reactive power in MVAr
        :param Snom: Nominal apparent power in MVA
        :param active: Is the generator active?
        :param Pmin: Minimum active power
        :param Pmax: Maximum active power
        :param Cost: Proportional cost [e/MWh]
        :param Cost2: Quadratic cost [e/MWh^2]
        :param Cost0: Fixed cost [e]
        :param Sbase: Nominal apparent power in MVA
        :param enabled_dispatch: Is the generator enabled for OPF?
        :param mttf: Mean time to failure [h]
        :param mttr: Mean time to recovery [h]
        :param q_points: list of reactive capability curve points [(P1, Qmin1, Qmax1), (P2, Qmin2, Qmax2), ...]
        :param use_reactive_power_curve: Use the reactive power curve? otherwise use the plain old limits
        :param r1:
        :param x1:
        :param r0:
        :param x0:
        :param r2:
        :param x2:
        :param Rs: Stator winding resistance [pu]
        :param Xs: Stator leakage reactance [pu]
        :param Xm: Magnetising reactance [pu]
        :param Rr: Rotor resistance [pu]
        :param Xr: Rotor reactance [pu]
        :param freq:
        :param capex:
        :param opex:
        :param srap_enabled:
        :param build_status:
        :param must_run:
        :param tpe: Machine type of the generator, as it can be synchronous or asynchronous
        """
        InjectionParent.__init__(self,
                                 name=name,
                                 idtag=idtag,
                                 code=code,
                                 bus=None,
                                 active=active,
                                 Cost=Cost,
                                 mttf=mttf,
                                 mttr=mttr,
                                 capex=capex,
                                 opex=opex,
                                 build_status=build_status,
                                 device_type=DeviceType.GeneratorDevice)

        self.control_bus: Bus | None = None
        self.control_cn = None

        self._P = float(P)
        self._P_prof = ProfileFloat(default_value=self.P)

        self.Pmax = float(Pmax)
        self._Pmax_prof = ProfileFloat(default_value=self.Pmax)

        self.Pmin = float(Pmin)
        self._Pmin_prof = ProfileFloat(default_value=self.Pmin)

        self._Q = float(Q)
        self._Q_prof = ProfileFloat(default_value=self.Q)

        self._Qmin_prof = ProfileFloat(default_value=Qmin)
        self._Qmax_prof = ProfileFloat(default_value=Qmax)

        self.qmin_set = float(Qmin)
        self.qmax_set = float(Qmax)

        self.srap_enabled = bool(srap_enabled)
        self._srap_enabled_prof = ProfileBool(default_value=self.srap_enabled)

        # is the device active for active power dispatch?
        self.enabled_dispatch = bool(enabled_dispatch)
        self._enabled_dispatch_prof = ProfileBool(default_value=self.enabled_dispatch)

        self.must_run = bool(must_run)
        self._must_run_prof = ProfileBool(default_value=self.must_run)

        # positive sequence resistance
        self.R1 = float(r1)

        # positive sequence reactance
        self.X1 = float(x1)

        # zero sequence resistance
        self.R0 = float(r0)

        # zero sequence reactance
        self.X0 = float(x0)

        # negative sequence resistance
        self.R2 = float(r2)

        # negative sequence reactance
        self.X2 = float(x2)

        # stator winding resistance
        self.Rs = float(Rs)

        # stator leakage reactance
        self.Xs = float(Xs)

        # magnetizing reactance
        self.Xm = float(Xm)

        # rotor resistance
        self.Rr = float(Rr)

        # rotor reactance
        self.Xr = float(Xr)

        # Power factor
        self._Pf = float(power_factor)

        # voltage set profile for this load in p.u.
        self._Pf_prof = ProfileFloat(default_value=self.Pf)

        # If this generator is voltage controlled it produces a PV node, otherwise the node remains as PQ
        self.is_controlled = bool(is_controlled)

        # Nominal power in MVA (also the machine base)
        self._Snom = float(Snom)

        # Voltage module set point (p.u.)
        self.Vset = float(vset)

        # voltage set profile for this load in p.u.
        self._Vset_prof = ProfileFloat(default_value=self.Vset)

        self.use_reactive_power_curve = bool(use_reactive_power_curve)

        # declare the generation curve
        self.q_curve = GeneratorQCurve()

        if q_points is not None:
            self.q_curve.set(np.array(q_points))
            self.custom_q_points = True
        else:
            self.q_curve.make_default_q_curve(self.Snom, self.qmin_set, self.qmax_set, n=1)
            self.custom_q_points = False

        self.Cost2 = float(Cost2)  # Cost of operation e/MW²
        self.Cost0 = float(Cost0)  # Cost of operation e

        self.startup_cost = startup_cost
        self.shutdown_cost = shutdown_cost
        self.min_time_up = min_time_up
        self.min_time_down = min_time_down
        self.ramp_up = ramp_up
        self.ramp_down = ramp_down

        self._Cost2_prof = ProfileFloat(default_value=self.Cost2)
        self._Cost0_prof = ProfileFloat(default_value=self.Cost0)

        self.emissions: Associations = Associations(device_type=DeviceType.EmissionGasDevice)
        self.fuels: Associations = Associations(device_type=DeviceType.FuelDevice)

        # system base power MVA
        self.Sbase = float(Sbase)

        self.freq = freq

        self.tpe: GeneratorType = tpe


    @property
    def P(self) -> float:
        """
        Get the active power value
        :return: float
        """
        return self._P

    @P.setter
    def P(self, val: float):
        """
        Set active power value
        :param val: some float
        """
        val = float(val)
        try:
            self._P = float(val)
        except ValueError:
            print("The value you're trying to set into P is not a float :(")

    @property
    def P_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._P_prof

    @P_prof.setter
    def P_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._P_prof = val
        elif isinstance(val, np.ndarray):
            self._P_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a P_prof')

    def get_P_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.P, self.P_prof, t)

    @property
    def Q(self) -> float:
        """
        Get the active power value
        :return: float
        """
        return self._Q

    @Q.setter
    def Q(self, val: float):
        """
        Set active power value
        :param val: some float
        """
        val = float(val)
        try:
            self._Q = float(val)
        except ValueError:
            print("The value you're trying to set into Q is not a float :(")

    @property
    def Q_prof(self) -> ProfileFloat:
        """
        Q profile
        :return: Profile
        """
        return self._Q_prof

    @Q_prof.setter
    def Q_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Q_prof = val
        elif isinstance(val, np.ndarray):
            self._Q_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Q_prof')

    def get_Q_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Q, self.Q_prof, t)

    @property
    def Qmin(self):
        """
        Return the reactive power lower limit
        :return: value
        """
        return self.qmin_set

    @Qmin.setter
    def Qmin(self, val):
        val = float(val)
        self.qmin_set = val

    @property
    def Qmin_prof(self) -> ProfileFloat:
        """
        Qmin profile
        :return: Profile
        """
        return self._Qmin_prof

    @Qmin_prof.setter
    def Qmin_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qmin_prof = val
        elif isinstance(val, np.ndarray):
            self._Qmin_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Qmin_prof')

    def get_Qmin_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qmin, self.Qmin_prof, t)

    @property
    def Qmax(self):
        """
        Return the reactive power upper limit
        :return: value
        """
        return self.qmax_set

    @Qmax.setter
    def Qmax(self, val):
        val = float(val)
        self.qmax_set = val

    @property
    def Qmax_prof(self) -> ProfileFloat:
        """
        Qmax profile
        :return: Profile
        """
        return self._Qmax_prof

    @Qmax_prof.setter
    def Qmax_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qmax_prof = val
        elif isinstance(val, np.ndarray):
            self._Qmax_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Qmax_prof')

    def get_Qmax_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qmax, self.Qmax_prof, t)

    @property
    def srap_enabled_prof(self) -> ProfileBool:
        """
        Control bus profile
        :return: Profile
        """
        return self._srap_enabled_prof

    @srap_enabled_prof.setter
    def srap_enabled_prof(self, val: Union[ProfileBool, np.ndarray]):
        if isinstance(val, ProfileBool):
            self._srap_enabled_prof = val
        elif isinstance(val, np.ndarray):
            self._srap_enabled_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into srap_enabled_prof')

    def get_srap_enabled_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.srap_enabled, self.srap_enabled_prof, t)

    @property
    def Pmax_prof(self) -> ProfileFloat:
        """
        Pmax profile
        :return: Profile
        """
        return self._Pmax_prof

    @Pmax_prof.setter
    def Pmax_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pmax_prof = val
        elif isinstance(val, np.ndarray):
            self._Pmax_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Pmax_prof')

    def get_Pmax_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pmax, self.Pmax_prof, t)

    @property
    def Pmin_prof(self) -> ProfileFloat:
        """
        Pmin profile
        :return: Profile
        """
        return self._Pmin_prof

    @Pmin_prof.setter
    def Pmin_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pmin_prof = val
        elif isinstance(val, np.ndarray):
            self._Pmin_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Pmin_prof')

    def get_Pmin_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pmin, self.Pmin_prof, t)

    def get_S_with_sign(self) -> complex:
        """

        :return:
        """
        return complex(self.P, 0.0)

    def get_Sprof_with_sign(self) -> CxVec:
        """

        :return:
        """
        return self.P_prof.toarray().astype(complex)

    @property
    def Pmin(self) -> float:
        """
        Get ``Pmin``.

        :return: float
        """
        return self._Pmin

    @Pmin.setter
    def Pmin(self, val: float) -> None:
        """
        Set ``Pmin``.

        :param val: Value to assign.
        :return: None
        """
        self._Pmin = float(val)

    @property
    def Pmax(self) -> float:
        """
        Get ``Pmax``.

        :return: float
        """
        return self._Pmax

    @Pmax.setter
    def Pmax(self, val: float) -> None:
        """
        Set ``Pmax``.

        :param val: Value to assign.
        :return: None
        """
        self._Pmax = float(val)

    @property
    def srap_enabled(self) -> bool:
        """
        Get ``srap_enabled``.

        :return: bool
        """
        return self._srap_enabled

    @srap_enabled.setter
    def srap_enabled(self, val: bool) -> None:
        """
        Set ``srap_enabled``.

        :param val: Value to assign.
        :return: None
        """
        self._srap_enabled = bool(val)

    @property
    def Vset_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Vset_prof

    @Vset_prof.setter
    def Vset_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Vset_prof = val
        elif isinstance(val, np.ndarray):
            self._Vset_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Vset_prof')

    def get_Vset_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Vset, self.Vset_prof, t)

    @property
    def Cost2_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Cost2_prof

    @Cost2_prof.setter
    def Cost2_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Cost2_prof = val
        elif isinstance(val, np.ndarray):
            self._Cost2_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Cost2_prof')

    def get_Cost2_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Cost2, self.Cost2_prof, t)

    @property
    def Cost0_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Cost0_prof

    @Cost0_prof.setter
    def Cost0_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Cost0_prof = val
        elif isinstance(val, np.ndarray):
            self._Cost0_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Cost0_prof')

    def get_Cost0_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Cost0, self.Cost0_prof, t)

    @property
    def enabled_dispatch_prof(self) -> ProfileBool:
        """
        Cost profile
        :return: Profile
        """
        return self._enabled_dispatch_prof

    @enabled_dispatch_prof.setter
    def enabled_dispatch_prof(self, val: Union[ProfileBool, np.ndarray]):
        if isinstance(val, ProfileBool):
            self._enabled_dispatch_prof = val
        elif isinstance(val, np.ndarray):
            self._enabled_dispatch_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Cost0_prof')

    def get_enabled_dispatch_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.enabled_dispatch, self.enabled_dispatch_prof, t)

    @property
    def must_run_prof(self) -> ProfileBool:
        """
        Cost profile
        :return: Profile
        """
        return self._must_run_prof

    @must_run_prof.setter
    def must_run_prof(self, val: Union[ProfileBool, np.ndarray]):
        if isinstance(val, ProfileBool):
            self._must_run_prof = val
        elif isinstance(val, np.ndarray):
            self._must_run_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Cost0_prof')

    def get_must_run_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.must_run, self.must_run_prof, t)

    def plot_profiles(self, time=None, show_fig=True):
        """
        Plot the time series results of this object
        :param time: array of time values
        :param show_fig: Show the figure?
        """

        if time is not None:
            fig = plt.figure(figsize=(12, 8))

            ax_1 = fig.add_subplot(211)
            ax_2 = fig.add_subplot(212, sharex=ax_1)

            # P
            y = self.P_prof.toarray()
            df = pd.DataFrame(data=y, index=time, columns=[self.name])
            ax_1.set_title('Active power', fontsize=14)
            ax_1.set_ylabel('MW', fontsize=11)
            df.plot(ax=ax_1)

            # V
            y = self.Vset_prof.toarray()
            df = pd.DataFrame(data=y, index=time, columns=[self.name])
            ax_2.set_title('Voltage Set point', fontsize=14)
            ax_2.set_ylabel('p.u.', fontsize=11)
            df.plot(ax=ax_2)

            plt.legend()
            fig.suptitle(self.name, fontsize=20)

            if show_fig:
                plt.show()

    def fix_inconsistencies(self, logger: Logger, min_vset=0.98, max_vset=1.02):
        """
        Correct the voltage set points
        :param logger: logger to store the events
        :param min_vset: minimum voltage set point (p.u.)
        :param max_vset: maximum voltage set point (p.u.)
        :return: True if any correction happened
        """
        errors = False

        if self.Vset > max_vset:
            logger.add_warning("Corrected generator set point", self.name, self.Vset, max_vset)
            self.Vset = max_vset
            errors = True

        elif self.Vset < min_vset:
            logger.add_warning("Corrected generator set point", self.name, self.Vset, min_vset)
            self.Vset = min_vset
            errors = True

        return errors

    @property
    def Snom(self):
        """
        Return the reactive power lower limit
        :return: value
        """
        return self._Snom

    @Snom.setter
    def Snom(self, val):
        """
        Set the generator nominal power
        if the reactive power curve was generated automatically, then it is refreshed
        :param val: float value
        """
        val = float(val)
        self._Snom = val

    def __iadd__(self, other: "Generator"):
        """
        Add another generator here
        :param other: Generator to add
        """

        self.P += other.P
        self.P_prof = self.P_prof.toarray() + other.P_prof.toarray()

        self.Pmax += other.Pmax
        self.Pmin += other.Pmin

        self.Qmax += other.Qmax
        self.Qmin += other.Qmin

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def is_controlled(self) -> bool:
        """
        Get ``is_controlled``.

        :return: bool
        """
        return self._is_controlled

    @is_controlled.setter
    def is_controlled(self, val: bool) -> None:
        """
        Set ``is_controlled``.

        :param val: Value to assign.
        :return: None
        """
        self._is_controlled = bool(val)

    @property
    def Pf(self) -> float:
        """
        Get ``Pf``.

        :return: float
        """
        return self._Pf

    @Pf.setter
    def Pf(self, val: float) -> None:
        """
        Set ``Pf``.

        :param val: Value to assign.
        :return: None
        """
        self._Pf = float(val)

        if self.auto_update_enabled:
            self.Q = compute_q(p=self.P, pf=self._Pf)

    @property
    def Pf_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Pf_prof

    @Pf_prof.setter
    def Pf_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pf_prof = val
        elif isinstance(val, np.ndarray):
            self._Pf_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Pf_prof')

    def get_Pf_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pf, self.Pf_prof, t)

    @property
    def Vset(self) -> float:
        """
        Get ``Vset``.

        :return: float
        """
        return self._Vset

    @Vset.setter
    def Vset(self, val: float) -> None:
        """
        Set ``Vset``.

        :param val: Value to assign.
        :return: None
        """
        self._Vset = float(val)

    @property
    def use_reactive_power_curve(self) -> bool:
        """
        Get ``use_reactive_power_curve``.

        :return: bool
        """
        return self._use_reactive_power_curve

    @use_reactive_power_curve.setter
    def use_reactive_power_curve(self, val: bool) -> None:
        """
        Set ``use_reactive_power_curve``.

        :param val: Value to assign.
        :return: None
        """
        self._use_reactive_power_curve = bool(val)

    @property
    def R1(self) -> float:
        """
        Get ``R1``.

        :return: float
        """
        return self._R1

    @R1.setter
    def R1(self, val: float) -> None:
        """
        Set ``R1``.

        :param val: Value to assign.
        :return: None
        """
        self._R1 = float(val)

    @property
    def X1(self) -> float:
        """
        Get ``X1``.

        :return: float
        """
        return self._X1

    @X1.setter
    def X1(self, val: float) -> None:
        """
        Set ``X1``.

        :param val: Value to assign.
        :return: None
        """
        self._X1 = float(val)

    @property
    def R0(self) -> float:
        """
        Get ``R0``.

        :return: float
        """
        return self._R0

    @R0.setter
    def R0(self, val: float) -> None:
        """
        Set ``R0``.

        :param val: Value to assign.
        :return: None
        """
        self._R0 = float(val)

    @property
    def X0(self) -> float:
        """
        Get ``X0``.

        :return: float
        """
        return self._X0

    @X0.setter
    def X0(self, val: float) -> None:
        """
        Set ``X0``.

        :param val: Value to assign.
        :return: None
        """
        self._X0 = float(val)

    @property
    def R2(self) -> float:
        """
        Get ``R2``.

        :return: float
        """
        return self._R2

    @R2.setter
    def R2(self, val: float) -> None:
        """
        Set ``R2``.

        :param val: Value to assign.
        :return: None
        """
        self._R2 = float(val)

    @property
    def X2(self) -> float:
        """
        Get ``X2``.

        :return: float
        """
        return self._X2

    @X2.setter
    def X2(self, val: float) -> None:
        """
        Set ``X2``.

        :param val: Value to assign.
        :return: None
        """
        self._X2 = float(val)

    @property
    def Rs(self) -> float:
        """
        Get ``Rs``.

        :return: float
        """
        return self._Rs

    @Rs.setter
    def Rs(self, val: float) -> None:
        """
        Set ``Rs``.

        :param val: Value to assign.
        :return: None
        """
        self._Rs = float(val)

    @property
    def Xs(self) -> float:
        """
        Get ``Xs``.

        :return: float
        """
        return self._Xs

    @Xs.setter
    def Xs(self, val: float) -> None:
        """
        Set ``Xs``.

        :param val: Value to assign.
        :return: None
        """
        self._Xs = float(val)

    @property
    def Xm(self) -> float:
        """
        Get ``Xm``.

        :return: float
        """
        return self._Xm

    @Xm.setter
    def Xm(self, val: float) -> None:
        """
        Set ``Xm``.

        :param val: Value to assign.
        :return: None
        """
        self._Xm = float(val)

    @property
    def Rr(self) -> float:
        """
        Get ``Rr``.

        :return: float
        """
        return self._Rr

    @Rr.setter
    def Rr(self, val: float) -> None:
        """
        Set ``Rr``.

        :param val: Value to assign.
        :return: None
        """
        self._Rr = float(val)

    @property
    def Xr(self) -> float:
        """
        Get ``Xr``.

        :return: float
        """
        return self._Xr

    @Xr.setter
    def Xr(self, val: float) -> None:
        """
        Set ``Xr``.

        :param val: Value to assign.
        :return: None
        """
        self._Xr = float(val)

    @property
    def Cost2(self) -> float:
        """
        Get ``Cost2``.

        :return: float
        """
        return self._Cost2

    @Cost2.setter
    def Cost2(self, val: float) -> None:
        """
        Set ``Cost2``.

        :param val: Value to assign.
        :return: None
        """
        self._Cost2 = float(val)

    @property
    def Cost0(self) -> float:
        """
        Get ``Cost0``.

        :return: float
        """
        return self._Cost0

    @Cost0.setter
    def Cost0(self, val: float) -> None:
        """
        Set ``Cost0``.

        :param val: Value to assign.
        :return: None
        """
        self._Cost0 = float(val)

    @property
    def startup_cost(self) -> float:
        """
        Get ``StartupCost``.

        :return: float
        """
        return self._StartupCost

    @startup_cost.setter
    def startup_cost(self, val: float) -> None:
        """
        Set ``StartupCost``.

        :param val: Value to assign.
        :return: None
        """
        self._StartupCost = float(val)

    @property
    def shutdown_cost(self) -> float:
        """
        Get ``ShutdownCost``.

        :return: float
        """
        return self._ShutdownCost

    @shutdown_cost.setter
    def shutdown_cost(self, val: float) -> None:
        """
        Set ``ShutdownCost``.

        :param val: Value to assign.
        :return: None
        """
        self._ShutdownCost = float(val)

    @property
    def min_time_up(self) -> float:
        """
        Get ``MinTimeUp``.

        :return: float
        """
        return self._MinTimeUp

    @min_time_up.setter
    def min_time_up(self, val: float) -> None:
        """
        Set ``MinTimeUp``.

        :param val: Value to assign.
        :return: None
        """
        self._MinTimeUp = float(val)

    @property
    def min_time_down(self) -> float:
        """
        Get ``MinTimeDown``.

        :return: float
        """
        return self._MinTimeDown

    @min_time_down.setter
    def min_time_down(self, val: float) -> None:
        """
        Set ``MinTimeDown``.

        :param val: Value to assign.
        :return: None
        """
        self._MinTimeDown = float(val)

    @property
    def ramp_up(self) -> float:
        """
        Get ``RampUp``.

        :return: float
        """
        return self._RampUp

    @ramp_up.setter
    def ramp_up(self, val: float) -> None:
        """
        Set ``RampUp``.

        :param val: Value to assign.
        :return: None
        """
        self._RampUp = float(val)

    @property
    def ramp_down(self) -> float:
        """
        Get ``RampDown``.

        :return: float
        """
        return self._RampDown

    @ramp_down.setter
    def ramp_down(self, val: float) -> None:
        """
        Set ``RampDown``.

        :param val: Value to assign.
        :return: None
        """
        self._RampDown = float(val)

    @property
    def enabled_dispatch(self) -> bool:
        """
        Get ``enabled_dispatch``.

        :return: bool
        """
        return self._enabled_dispatch

    @enabled_dispatch.setter
    def enabled_dispatch(self, val: bool) -> None:
        """
        Set ``enabled_dispatch``.

        :param val: Value to assign.
        :return: None
        """
        self._enabled_dispatch = bool(val)

    @property
    def must_run(self) -> bool:
        """
        Get ``must_run``.

        :return: bool
        """
        return self._must_run

    @must_run.setter
    def must_run(self, val: bool) -> None:
        """
        Set ``must_run``.

        :param val: Value to assign.
        :return: None
        """
        self._must_run = bool(val)

