# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0


import numpy as np
import pandas as pd
from typing import Union
from matplotlib import pyplot as plt
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DeviceType, BuildStatus, SubObjectType
from VeraGridEngine.Devices.Associations.association import Associations
from VeraGridEngine.Devices.Parents.generator_parent import GeneratorParent
from VeraGridEngine.Devices.Injections.generator_q_curve import GeneratorQCurve
from VeraGridEngine.Devices.profile import Profile
from VeraGridEngine.Utils.Symbolic.block import Block, Var, Const, VarPowerFlowRefferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import cos, sin, real, imag, conj, angle, exp, log, abs, UndefinedConst
from VeraGridEngine.Devices.Parents.editable_device import get_at


class Generator(GeneratorParent):
    __slots__ = (
        'enabled_dispatch',
        '_enabled_dispatch_prof',
        'R1', 'X1', 'R0', 'X0', 'R2', 'X2',
        'Pf',
        '_Pf_prof',
        'is_controlled',
        '_Snom',
        'Vset',
        '_Vset_prof',
        'use_reactive_power_curve',
        'qmin_set',
        'qmax_set',
        'q_curve',
        'custom_q_points',
        'Cost2',
        'Cost0',
        'StartupCost',
        'ShutdownCost',
        'MinTimeUp',
        'MinTimeDown',
        'RampUp',
        'RampDown',
        '_Qmin_prof',
        '_Qmax_prof',
        '_Cost2_prof',
        '_Cost0_prof',
        'emissions',
        'fuels',
        'Sbase',
        'freq',
        'M',
        'D',
        'tm0',
        'omega_ref',
        'vf',
        'Kp',
        'Ki',
        'Kw',
        'init_params',
        'P_g',
        'Q_g',
        'must_run',
        '_must_run_prof'
    )

    def __init__(self,
                 name='gen',
                 idtag: Union[str, None] = None,
                 code: str = '',
                 P: float = 0.0,
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
                 freq=60.0,
                 tm0=0.0750281479189543,
                 M=1.0 / 100.0 * 900.0,  # from Machine to System base
                 D=4.0 / 100.0 * 900.0,  # from Machine to System base
                 omega_ref=1.0,
                 vf=0.9967798127873505,
                 Kp=0.0,
                 Ki=0.0,
                 capex: float = 0,
                 opex: float = 0,
                 srap_enabled: bool = True,
                 init_params: dict[str, float] = {"tm0": 0.0, "vf0": 0.0},  ###
                 build_status: BuildStatus = BuildStatus.Commissioned,
                 must_run: bool = False):
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
        :param freq:
        :param tm0:
        :param M:
        :param D:
        :param omega_ref:
        :param vf:
        :param Kp:
        :param Ki:
        :param capex:
        :param opex:
        :param srap_enabled:
        :param init_params:
        :param build_status:
        :param must_run:
        """
        GeneratorParent.__init__(self,
                                 name=name,
                                 idtag=idtag,
                                 code=code,
                                 bus=None,
                                 control_bus=None,
                                 active=active,
                                 P=P,
                                 Pmin=Pmin,
                                 Pmax=Pmax,
                                 Cost=Cost,
                                 mttf=mttf,
                                 mttr=mttr,
                                 capex=capex,
                                 opex=opex,
                                 srap_enabled=srap_enabled,
                                 build_status=build_status,
                                 device_type=DeviceType.GeneratorDevice)

        # is the device active for active power dispatch?
        self.enabled_dispatch = bool(enabled_dispatch)
        self._enabled_dispatch_prof = Profile(default_value=self.enabled_dispatch, data_type=bool)

        self.must_run = bool(must_run)
        self._must_run_prof = Profile(default_value=self.must_run, data_type=bool)

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

        # Power factor
        self.Pf = float(power_factor)

        # voltage set profile for this load in p.u.
        self._Pf_prof = Profile(default_value=self.Pf, data_type=float)

        # If this generator is voltage controlled it produces a PV node, otherwise the node remains as PQ
        self.is_controlled = bool(is_controlled)

        # Nominal power in MVA (also the machine base)
        self._Snom = float(Snom)

        # Voltage module set point (p.u.)
        self.Vset = float(vset)

        # voltage set profile for this load in p.u.
        self._Vset_prof = Profile(default_value=self.Vset, data_type=float)

        self.use_reactive_power_curve = bool(use_reactive_power_curve)

        # minimum reactive power in MVAr
        self.qmin_set = float(Qmin)

        # Maximum reactive power in MVAr
        self.qmax_set = float(Qmax)

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

        self.StartupCost = 0.0
        self.ShutdownCost = 0.0
        self.MinTimeUp = 0.0
        self.MinTimeDown = 0.0
        self.RampUp = 1e20
        self.RampDown = 1e20

        self._Qmin_prof = Profile(default_value=Qmin, data_type=float)
        self._Qmax_prof = Profile(default_value=Qmax, data_type=float)

        self._Cost2_prof = Profile(default_value=self.Cost2, data_type=float)
        self._Cost0_prof = Profile(default_value=self.Cost0, data_type=float)

        self.emissions: Associations = Associations(device_type=DeviceType.EmissionGasDevice)
        self.fuels: Associations = Associations(device_type=DeviceType.FuelDevice)

        # system base power MVA
        self.Sbase = float(Sbase)

        self.freq = freq
        self.tm0 = tm0
        self.M = M
        self.D = D
        self.omega_ref = omega_ref
        self.vf = vf
        self.Kp = Kp
        self.Ki = Ki
        self.init_params = init_params
        self.P_g = Var("P_g")
        self.Q_g = Var("Q_g")

        self.register(key='is_controlled', units='', tpe=bool, definition='Is this generator voltage-controlled?')

        self.register(key='Pf', units='', tpe=float,
                      definition='Power factor (cos(phi)). This is used for non-controlled generators.',
                      profile_name='Pf_prof')
        self.register(key='Vset', units='p.u.', tpe=float,
                      definition='Set voltage. This is used for controlled generators.', profile_name='Vset_prof')
        self.register(key='Snom', units='MVA', tpe=float, definition='Nominal power.')
        self.register(key='Qmin', units='MVAr', tpe=float, definition='Minimum reactive power.',
                      profile_name='Qmin_prof')
        self.register(key='Qmax', units='MVAr', tpe=float, definition='Maximum reactive power.',
                      profile_name='Qmax_prof')
        self.register(key='use_reactive_power_curve', units='', tpe=bool,
                      definition='Use the reactive power capability curve?')
        self.register(key='q_curve', units='MVAr', tpe=SubObjectType.GeneratorQCurve,
                      definition='Capability curve data (double click on the generator to edit)',
                      editable=False, display=False)

        self.register(key='R1', units='p.u.', tpe=float, definition='Total positive sequence resistance.')
        self.register(key='X1', units='p.u.', tpe=float, definition='Total positive sequence reactance.')
        self.register(key='R0', units='p.u.', tpe=float, definition='Total zero sequence resistance.')
        self.register(key='X0', units='p.u.', tpe=float, definition='Total zero sequence reactance.')
        self.register(key='R2', units='p.u.', tpe=float, definition='Total negative sequence resistance.')
        self.register(key='X2', units='p.u.', tpe=float, definition='Total negative sequence reactance.')
        self.register(key='Cost2', units='e/MW²/h', tpe=float, definition='Generation quadratic cost. Used in OPF.',
                      profile_name='Cost2_prof')

        self.register(key='Cost0', units='e/h', tpe=float, definition='Generation constant cost. Used in OPF.',
                      profile_name='Cost0_prof')
        self.register(key='StartupCost', units='e/h', tpe=float, definition='Generation start-up cost. Used in OPF.')
        self.register(key='ShutdownCost', units='e/h', tpe=float, definition='Generation shut-down cost. Used in OPF.')
        self.register(key='MinTimeUp', units='h', tpe=float,
                      definition='Minimum time that the generator has to be on when started. Used in OPF.')
        self.register(key='MinTimeDown', units='h', tpe=float,
                      definition='Minimum time that the generator has to be off when shut down. Used in OPF.')
        self.register(key='RampUp', units='MW/h', tpe=float,
                      definition='Maximum amount of generation increase per hour.')
        self.register(key='RampDown', units='MW/h', tpe=float,
                      definition='Maximum amount of generation decrease per hour.')

        self.register(key='enabled_dispatch', units='', tpe=bool, profile_name="enabled_dispatch_prof",
                      definition='Enabled for dispatch? Used in OPF.')
        self.register(key='must_run', units='', tpe=bool, profile_name="must_run_prof",
                      definition='P >= Pmin constraint. Used in OPF with unit commitment active.')

        self.register(key='emissions', units='t/MWh', tpe=SubObjectType.Associations,
                      definition='List of emissions', display=False)

        self.register(key='fuels', units='t/MWh', tpe=SubObjectType.Associations,
                      definition='List of fuels', display=False)

    @property
    def Pf_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._Pf_prof

    @Pf_prof.setter
    def Pf_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Vset_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._Vset_prof

    @Vset_prof.setter
    def Vset_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Qmin_prof(self) -> Profile:
        """
        Qmin profile
        :return: Profile
        """
        return self._Qmin_prof

    @Qmin_prof.setter
    def Qmin_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Qmax_prof(self) -> Profile:
        """
        Qmax profile
        :return: Profile
        """
        return self._Qmax_prof

    @Qmax_prof.setter
    def Qmax_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Cost2_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._Cost2_prof

    @Cost2_prof.setter
    def Cost2_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Cost0_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._Cost0_prof

    @Cost0_prof.setter
    def Cost0_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def enabled_dispatch_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._enabled_dispatch_prof

    @enabled_dispatch_prof.setter
    def enabled_dispatch_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def must_run_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._must_run_prof

    @must_run_prof.setter
    def must_run_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
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
    def Qmax(self):
        """
        Return the reactive power upper limit
        :return: value
        """
        return self.qmax_set

    @Qmax.setter
    def Qmax(self, val):
        self.qmax_set = val

    @property
    def Qmin(self):
        """
        Return the reactive power lower limit
        :return: value
        """
        return self.qmin_set

    @Qmin.setter
    def Qmin(self, val):
        self.qmin_set = val

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

    def initialize_rms(self, rms_event=False):
        """
        Initialize the RMS model
        """


        empty = self.rms_model.empty()
        if self.rms_model.empty():
            empty = True
            delta = Var("delta")
            omega = Var("omega")
            psid = Var("psid")
            psiq = Var("psiq")
            i_d = Var("i_d")
            i_q = Var("i_q")
            v_d = Var("v_d")
            v_q = Var("v_q")
            te = Var("te")
            et = Var("et")
            tm = Var("tm")
            P_g = Var("P_g", pf_ref=VarPowerFlowRefferenceType.P)
            Q_g = Var("Q_g", pf_ref=VarPowerFlowRefferenceType.Q)

            R1 = Var("R1")
            X1 = Var("X1")
            freq = Var("frequ")
            M = Var("M")
            D = Var("D")
            omega_ref = Var("omega_ref")
            Kp = Var("Kp")
            Ki = Var("Ki")

            vf = UndefinedConst()
            tm0 = UndefinedConst()

            Vm = self.bus.rms_model.model.E(VarPowerFlowRefferenceType.Vm)
            Va = self.bus.rms_model.model.E(VarPowerFlowRefferenceType.Va)

            block = Block(
                state_vars=[delta, omega],
                state_eqs=[
                    (2 * np.pi * freq) * (omega - omega_ref),
                    (tm - te - D * (omega - omega_ref)) / M,
                ],
                algebraic_vars=[P_g, Q_g, v_d, v_q, i_d, i_q, psid, psiq,
                                te, tm, et],
                algebraic_eqs=[
                    psid - (R1 * i_q + v_q),
                    psiq + (R1 * i_d + v_d),
                    0 - (psid + X1 * i_d - vf),
                    0 - (psiq + X1 * i_q),
                    v_d - (Vm * sin(delta - Va)),
                    v_q - (Vm * cos(delta - Va)),
                    te - (psid * i_q - psiq * i_d),
                    P_g - (v_d * i_d + v_q * i_q),
                    Q_g - (v_q * i_d - v_d * i_q),
                    tm - (self.tm0 + Kp * (omega - omega_ref) + Ki * et),
                    2 * np.pi * freq * et - delta,
                ],

                init_eqs={
                    delta: imag(
                        log((Vm * exp(1j * Va) + (R1 + 1j * X1) * (
                            conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))))) / (
                                abs(Vm * exp(1j * Va) + (R1 + 1j * X1) * (
                                    conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va)))))))),
                    omega: omega_ref,
                    v_d: real((Vm * exp(1j * Va)) * exp(-1j * (delta - np.pi / 2))),
                    v_q: imag((Vm * exp(1j * Va)) * exp(-1j * (delta - np.pi / 2))),
                    i_d: real(
                        conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))) * exp(
                            -1j * (delta - np.pi / 2))),
                    i_q: imag(
                        conj((P_g + 1j * Q_g) / (Vm * exp(1j * Va))) * exp(
                            -1j * (delta - np.pi / 2))),
                    psid: R1 * i_q + v_q,
                    psiq: -R1 * i_d - v_d,
                    te: psid * i_q - psiq * i_d,
                    tm: te,
                    et: Const(0),
                })

            block.fix_vars = [tm0, vf]
            block.fix_vars_eqs = {tm0.uid: tm,
                                  vf.uid: psid + X1 * i_d}

            block.external_mapping = {
                VarPowerFlowRefferenceType.P: P_g,
                VarPowerFlowRefferenceType.Q: Q_g
            }

            block.event_dict = {R1: Const(self.R1),
                                X1: Const(self.X1),
                                freq: Const(self.freq),
                                M: Const(self.M),
                                D: Const(self.D),
                                omega_ref: Const(self.omega_ref),
                                Kp: Const(self.Kp),
                                Ki: Const(self.Ki)}

            self.rms_model.model = block
