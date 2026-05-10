# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, DeviceType, PrpCat
from VeraGridEngine.basic_structures import CxVec
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp


class LoadParent(InjectionParent):
    """
    Template for objects that behave like loads
    """

    __slots__ = (
        '_P',
        '_P_prof',
        '_Q',
        '_Q_prof',
        '_Pa',
        '_Pa_prof',
        '_Qa',
        '_Qa_prof',
        '_Pb',
        '_Pb_prof',
        '_Qb',
        '_Qb_prof',
        '_Pc',
        '_Pc_prof',
        '_Qc',
        '_Qc_prof',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='P',
            units='MW',
            tpe=float,
            definition='Active power',
            profile_name='P_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Pa',
            units='MW',
            tpe=float,
            definition='Phase A active power',
            profile_name='Pa_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Pb',
            units='MW',
            tpe=float,
            definition='Phase B active power',
            profile_name='Pb_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Pc',
            units='MW',
            tpe=float,
            definition='Phase C active power',
            profile_name='Pc_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Q',
            units='MVAr',
            tpe=float,
            definition='Reactive power',
            profile_name='Q_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Qa',
            units='MVAr',
            tpe=float,
            definition='Phase A reactive power',
            profile_name='Qa_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Qb',
            units='MVAr',
            tpe=float,
            definition='Phase B reactive power',
            profile_name='Qb_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Qc',
            units='MVAr',
            tpe=float,
            definition='Phase C reactive power',
            profile_name='Qc_prof',
            cat=[PrpCat.PF3],
        ),
    )

    def __init__(self,
                 name: str,
                 idtag: Union[str, None],
                 code: str,
                 bus: Union[Bus, None],
                 active: bool,
                 P: float,
                 P1: float,
                 P2: float,
                 P3: float,
                 Q: float,
                 Q1: float,
                 Q2: float,
                 Q3: float,
                 Cost: float,
                 mttf: float,
                 mttr: float,
                 capex: float,
                 opex: float,
                 build_status: BuildStatus,
                 device_type: DeviceType):
        """
        LoadLikeTemplate
        :param name: Name of the device
        :param idtag: unique id of the device (if None or "" a new one is generated)
        :param code: secondary code for compatibility
        :param bus: snapshot bus object
        :param active:active state
        :param P: active power (MW)
        :param P1: phase 1 active power (MW)
        :param P2: phase 2 active power (MW)
        :param P3: phase 3 active power (MW)
        :param Q: reactive power (MVAr)
        :param Q1: phase 1 reactive power (MVAr)
        :param Q2: phase 2 reactive power (MVAr)
        :param Q3: phase 3 reactive power (MVAr)
        :param Cost: cost associated with various actions (dispatch or shedding)
        :param mttf: mean time to failure (h)
        :param mttr: mean time to recovery (h)
        :param capex: capital expenditures (investment cost)
        :param opex: operational expenditures (maintainance cost)
        :param build_status: BuildStatus
        :param device_type: DeviceType
        """

        InjectionParent.__init__(self,
                                 name=name,
                                 idtag=idtag,
                                 code=code,
                                 bus=bus,
                                 active=active,
                                 Cost=Cost,
                                 mttf=mttf,
                                 mttr=mttr,
                                 capex=capex,
                                 opex=opex,
                                 build_status=build_status,
                                 device_type=device_type)

        self.P = float(P)
        self._P_prof = ProfileFloat(default_value=self.P)

        self.Pa = float(P1)
        self._Pa_prof = ProfileFloat(default_value=self.Pa)

        self.Pb = float(P2)
        self._Pb_prof = ProfileFloat(default_value=self.Pb)

        self.Pc = float(P3)
        self._Pc_prof = ProfileFloat(default_value=self.Pc)

        self.Q = float(Q)
        self._Q_prof = ProfileFloat(default_value=self.Q)

        self.Qa = float(Q1)
        self._Qa_prof = ProfileFloat(default_value=self.Qa)

        self.Qb = float(Q2)
        self._Qb_prof = ProfileFloat(default_value=self.Qb)

        self.Qc = float(Q3)
        self._Qc_prof = ProfileFloat(default_value=self.Qc)


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
            raise Exception(str(type(val)) + 'not supported to be set into a pofile')

    def get_P_at(self, t: int | None) -> float:
        """
        Get power at time t
        :param t:
        :return:
        """
        return get_at(self.P, self.P_prof, t)

    @property
    def Pa_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Pa_prof

    @Pa_prof.setter
    def Pa_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pa_prof = val
        elif isinstance(val, np.ndarray):
            self._Pa_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a pofile')

    def get_Pa_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pa, self.Pa_prof, t)

    @property
    def Pb_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Pb_prof

    @Pb_prof.setter
    def Pb_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pb_prof = val
        elif isinstance(val, np.ndarray):
            self._Pb_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a pofile')

    def get_Pb_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pb, self.Pb_prof, t)

    @property
    def Pc_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Pc_prof

    @Pc_prof.setter
    def Pc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pc_prof = val
        elif isinstance(val, np.ndarray):
            self._Pc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a pofile')

    def get_Pc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pc, self.Pc_prof, t)

    @property
    def Q_prof(self) -> ProfileFloat:
        """
        Cost profile
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
    def Qa_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Qa_prof

    @Qa_prof.setter
    def Qa_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qa_prof = val
        elif isinstance(val, np.ndarray):
            self._Qa_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Q1_prof')

    def get_Qa_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qa, self.Qa_prof, t)

    @property
    def Qb_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Qb_prof

    @Qb_prof.setter
    def Qb_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qb_prof = val
        elif isinstance(val, np.ndarray):
            self._Qb_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Q2_prof')

    def get_Qb_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qb, self.Qb_prof, t)

    @property
    def Qc_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Qc_prof

    @Qc_prof.setter
    def Qc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qc_prof = val
        elif isinstance(val, np.ndarray):
            self._Qc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Q3_prof')

    def get_Qc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qc, self.Qc_prof, t)

    def get_S_with_sign(self) -> complex:
        """

        :return:
        """
        return complex(-self.P, -self.Q)

    def get_Sprof_with_sign(self) -> CxVec:
        """

        :return:
        """
        return -self.P_prof.toarray() - 1j * self.Q_prof.toarray()

    def get_S_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_P_at(t), self.get_Q_at(t))

    def get_Sa_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Pa_at(t), self.get_Qa_at(t))

    def get_Sb_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Pb_at(t), self.get_Qb_at(t))

    def get_Sc_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Pc_at(t), self.get_Qc_at(t))

    def get_Pf_at(self, t: int | None) -> float:
        """
        Get power factor
        :param t:
        :return:
        """
        p = self.get_P_at(t)
        q = self.get_Q_at(t)
        s = np.sqrt(p*p + q*q)
        return p / s if s > 0.0 else 0.0

    def split_sequence_load_in_3_phase(self, share_a=1.0, share_b=1.0, share_c=1.0):
        """
        Initializes the 3-phase properties using the positive sequence ones
        """
        self.Pa = self.P * share_a
        self.Pb = self.P * share_b
        self.Pc = self.P * share_c

        self.Qa = self.Q * share_a
        self.Qb = self.Q * share_b
        self.Qc = self.Q * share_c

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

            # Q
            y = self.Q_prof.toarray()
            df = pd.DataFrame(data=y, index=time, columns=[self.name])
            ax_2.set_title('Reactive power', fontsize=14)
            ax_2.set_ylabel('MVAr', fontsize=11)
            df.plot(ax=ax_2)

            plt.legend()
            fig.suptitle(self.name, fontsize=20)

            if show_fig:
                plt.show()

    def __iadd__(self, other: "LoadParent"):
        """
        Add another generator here
        :param other: Generator to add
        """

        self.P += other.P
        self.P_prof = self.P_prof.toarray() + other.P_prof.toarray()

        self.Q += other.Q
        self.Q_prof = self.Q_prof.toarray() + other.Q_prof.toarray()

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def P(self) -> float:
        """
        Get ``P``.

        :return: float
        """
        return self._P

    @P.setter
    def P(self, val: float) -> None:
        """
        Set ``P``.

        :param val: Value to assign.
        :return: None
        """
        self._P = float(val)

    @property
    def Pa(self) -> float:
        """
        Get ``Pa``.

        :return: float
        """
        return self._Pa

    @Pa.setter
    def Pa(self, val: float) -> None:
        """
        Set ``Pa``.

        :param val: Value to assign.
        :return: None
        """
        self._Pa = float(val)

    @property
    def Pb(self) -> float:
        """
        Get ``Pb``.

        :return: float
        """
        return self._Pb

    @Pb.setter
    def Pb(self, val: float) -> None:
        """
        Set ``Pb``.

        :param val: Value to assign.
        :return: None
        """
        self._Pb = float(val)

    @property
    def Pc(self) -> float:
        """
        Get ``Pc``.

        :return: float
        """
        return self._Pc

    @Pc.setter
    def Pc(self, val: float) -> None:
        """
        Set ``Pc``.

        :param val: Value to assign.
        :return: None
        """
        self._Pc = float(val)

    @property
    def Q(self) -> float:
        """
        Get ``Q``.

        :return: float
        """
        return self._Q

    @Q.setter
    def Q(self, val: float) -> None:
        """
        Set ``Q``.

        :param val: Value to assign.
        :return: None
        """
        self._Q = float(val)

    @property
    def Qa(self) -> float:
        """
        Get ``Qa``.

        :return: float
        """
        return self._Qa

    @Qa.setter
    def Qa(self, val: float) -> None:
        """
        Set ``Qa``.

        :param val: Value to assign.
        :return: None
        """
        self._Qa = float(val)

    @property
    def Qb(self) -> float:
        """
        Get ``Qb``.

        :return: float
        """
        return self._Qb

    @Qb.setter
    def Qb(self, val: float) -> None:
        """
        Set ``Qb``.

        :param val: Value to assign.
        :return: None
        """
        self._Qb = float(val)

    @property
    def Qc(self) -> float:
        """
        Get ``Qc``.

        :return: float
        """
        return self._Qc

    @Qc.setter
    def Qc(self, val: float) -> None:
        """
        Set ``Qc``.

        :param val: Value to assign.
        :return: None
        """
        self._Qc = float(val)
