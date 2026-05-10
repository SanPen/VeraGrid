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
from VeraGridEngine.enumerations import BuildStatus, DeviceType, SubObjectType, PrpCat
from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.admittance_matrix import AdmittanceMatrix
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp


class ShuntParent(InjectionParent):
    """
    Template for objects that behave like shunts
    """

    __slots__ = (
        '_G',
        '_G_prof',
        '_B',
        '_B_prof',
        '_G0',
        '_G0_prof',
        '_B0',
        '_B0_prof',
        '_Ga',
        '_Ga_prof',
        '_Ba',
        '_Ba_prof',
        '_Gb',
        '_Gb_prof',
        '_Bb',
        '_Bb_prof',
        '_Gc',
        '_Gc_prof',
        '_Bc',
        '_Bc_prof',
        '_ysh',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='G',
            units='MW',
            tpe=float,
            definition='Active power',
            profile_name='G_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='G0',
            units='MW',
            tpe=float,
            definition='Zero sequence active power of the impedance component at V=1.0 p.u.',
            profile_name='G0_prof',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='Ga',
            units='MW',
            tpe=float,
            definition='Active power',
            profile_name='Ga_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Gb',
            units='MW',
            tpe=float,
            definition='Active power',
            profile_name='Gb_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Gc',
            units='MW',
            tpe=float,
            definition='Active power',
            profile_name='Gc_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='B',
            units='MVAr',
            tpe=float,
            definition='Reactive power',
            profile_name='B_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='B0',
            units='MVAr',
            tpe=float,
            definition='Zero sequence reactive power of the impedance component at V=1.0 p.u.',
            profile_name='B0_prof',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='Ba',
            units='MVAr',
            tpe=float,
            definition='Reactive power',
            profile_name='Ba_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Bb',
            units='MVAr',
            tpe=float,
            definition='Reactive power',
            profile_name='Bb_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='Bc',
            units='MVAr',
            tpe=float,
            definition='Reactive power',
            profile_name='Bc_prof',
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='ysh',
            units="p.u.",
            tpe=SubObjectType.AdmittanceMatrix,
            definition='Shunt admittance matrix of the branch',
            editable=False,
            display=False,
            cat=[PrpCat.PF],
        ),
    )

    def __init__(self,
                 name: str,
                 idtag: Union[str, None],
                 code: str,
                 bus: Union[Bus, None],
                 active: bool,
                 G: float,
                 G1: float,
                 G2: float,
                 G3: float,
                 B: float,
                 B1: float,
                 B2: float,
                 B3: float,
                 G0: float,
                 B0: float,
                 Cost: float,
                 mttf: float,
                 mttr: float,
                 capex: float,
                 opex: float,
                 build_status: BuildStatus,
                 device_type: DeviceType):
        """
        ShuntLikeTemplate
        :param name: Name of the device
        :param idtag: unique id of the device (if None or "" a new one is generated)
        :param code: secondary code for compatibility
        :param bus: snapshot bus object
        :param active:active state
        :param G: positive conductance (MW @ v=1 p.u.)
        :param G1: positive conductance (MW @ v=1 p.u.)
        :param G2: positive conductance (MW @ v=1 p.u.)
        :param G3: positive conductance (MW @ v=1 p.u.)
        :param B: positive conductance (MVAr @ v=1 p.u.)
        :param B1: positive conductance (MVAr @ v=1 p.u.)
        :param B2: positive conductance (MVAr @ v=1 p.u.)
        :param B3: positive conductance (MVAr @ v=1 p.u.)
        :param G0: zero-sequence conductance (MW @ v=1 p.u.)
        :param B0: zero-sequence conductance (MVAr @ v=1 p.u.)
        :param Cost: cost associated with various actions (dispatch or shedding)
        :param mttf: mean time to failure (h)
        :param mttr: mean time to recovery (h)
        :param capex: capital expenditures (investment cost)
        :param opex: operational expenditures (maintenance cost)
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

        self.G = float(G)
        self._G_prof = ProfileFloat(default_value=self.G)

        self.B = float(B)
        self._B_prof = ProfileFloat(default_value=self.B)

        self.G0 = float(G0)
        self._G0_prof = ProfileFloat(default_value=self.G0)

        self.B0 = float(B0)
        self._B0_prof = ProfileFloat(default_value=self.B0)

        self.Ga = float(G1)
        self._Ga_prof = ProfileFloat(default_value=self.Ga)

        self.Gb = float(G2)
        self._Gb_prof = ProfileFloat(default_value=self.Gb)

        self.Gc = float(G3)
        self._Gc_prof = ProfileFloat(default_value=self.Gc)

        self.Ba = float(B1)
        self._Ba_prof = ProfileFloat(default_value=self.Ba)

        self.Bb = float(B2)
        self._Bb_prof = ProfileFloat(default_value=self.Bb)

        self.Bc = float(B3)
        self._Bc_prof = ProfileFloat(default_value=self.Bc)

        self._ysh = AdmittanceMatrix()

    @property
    def G_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._G_prof

    @G_prof.setter
    def G_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._G_prof = val
        elif isinstance(val, np.ndarray):
            self._G_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a G_prof')

    def get_G_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.G, self.G_prof, t)

    @property
    def Ga_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Ga_prof

    @Ga_prof.setter
    def Ga_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Ga_prof = val
        elif isinstance(val, np.ndarray):
            self._Ga_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Ga_prof')

    def get_Ga_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Ga, self.Ga_prof, t)

    @property
    def Gb_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Gb_prof

    @Gb_prof.setter
    def Gb_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Gb_prof = val
        elif isinstance(val, np.ndarray):
            self._Gb_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Gb_prof')

    def get_Gb_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Gb, self.Gb_prof, t)

    @property
    def Gc_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Gc_prof

    @Gc_prof.setter
    def Gc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Gc_prof = val
        elif isinstance(val, np.ndarray):
            self._Gc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Gc_prof')

    def get_Gc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Gc, self.Gc_prof, t)

    @property
    def B_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._B_prof

    @B_prof.setter
    def B_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._B_prof = val
        elif isinstance(val, np.ndarray):
            self._B_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a B_prof')

    def get_B_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.B, self.B_prof, t)

    @property
    def Ba_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Ba_prof

    @Ba_prof.setter
    def Ba_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Ba_prof = val
        elif isinstance(val, np.ndarray):
            self._Ba_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Ba_prof')

    def get_Ba_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Ba, self.Ba_prof, t)

    @property
    def Bb_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Bb_prof

    @Bb_prof.setter
    def Bb_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Bb_prof = val
        elif isinstance(val, np.ndarray):
            self._Bb_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Bb_prof')

    def get_Bb_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Bb, self.Bb_prof, t)

    @property
    def Bc_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._Bc_prof

    @Bc_prof.setter
    def Bc_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Bc_prof = val
        elif isinstance(val, np.ndarray):
            self._Bc_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Bc_prof')

    def get_Bc_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Bc, self.Bc_prof, t)

    @property
    def G0_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._G0_prof

    @G0_prof.setter
    def G0_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._G0_prof = val
        elif isinstance(val, np.ndarray):
            self._G0_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a G_prof')

    def get_G0_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.G0, self.G0_prof, t)

    @property
    def B0_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._B0_prof

    @B0_prof.setter
    def B0_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._B0_prof = val
        elif isinstance(val, np.ndarray):
            self._B0_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a B_prof')

    def get_B0_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.B0, self.B0_prof, t)

    @property
    def ysh(self) -> AdmittanceMatrix:
        """
        Shunt admittance matrix (4x4)
        :return:
        """
        if self._ysh.size <= 0:
            self.fill_3_phase_from_sequence()

        return self._ysh

    @ysh.setter
    def ysh(self, val: AdmittanceMatrix):
        if isinstance(val, AdmittanceMatrix):
            self._ysh = val
        else:
            raise ValueError(f'{val} is not a AdmittanceMatrix')

    def get_Y_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_G_at(t), self.get_B_at(t))

    def get_Ya_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Ga_at(t), self.get_Ba_at(t))

    def get_Yb_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Gb_at(t), self.get_Bb_at(t))

    def get_Yc_at(self, t: int | None) -> complex:
        """
        :param t:
        :return:
        """
        return complex(self.get_Gc_at(t), self.get_Bc_at(t))

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

            # G
            y = self.G_prof.toarray()
            df = pd.DataFrame(data=y, index=time, columns=[self.name])
            ax_1.set_title('Conductance power', fontsize=14)
            ax_1.set_ylabel('MW', fontsize=11)
            df.plot(ax=ax_1)

            # B
            y = self.B_prof.toarray()
            df = pd.DataFrame(data=y, index=time, columns=[self.name])
            ax_2.set_title('Susceptance power', fontsize=14)
            ax_2.set_ylabel('MVAr', fontsize=11)
            df.plot(ax=ax_2)

            plt.legend()
            fig.suptitle(self.name, fontsize=20)

            if show_fig:
                plt.show()

    def fill_3_phase_from_sequence(self):
        """
        Fill the admittance
        :return:
        """
        self.ysh = AdmittanceMatrix(size=4)

        y1 = self.G + 1j * self.B
        y0 = self.G0 + 1j * self.B0

        diag = (2.0 * y1 + y0) / 3.0
        off_diag = (y0 - y1) / 3.0

        yabc = np.full((4, 4), off_diag)
        np.fill_diagonal(yabc, diag)

        self.ysh.values = yabc
        self.ysh.phA = 1
        self.ysh.phB = 1
        self.ysh.phC = 1

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def G(self) -> float:
        """
        Get ``G``.

        :return: float
        """
        return self._G

    @G.setter
    def G(self, val: float) -> None:
        """
        Set ``G``.

        :param val: Value to assign.
        :return: None
        """
        self._G = float(val)

    @property
    def G0(self) -> float:
        """
        Get ``G0``.

        :return: float
        """
        return self._G0

    @G0.setter
    def G0(self, val: float) -> None:
        """
        Set ``G0``.

        :param val: Value to assign.
        :return: None
        """
        self._G0 = float(val)

    @property
    def Ga(self) -> float:
        """
        Get ``Ga``.

        :return: float
        """
        return self._Ga

    @Ga.setter
    def Ga(self, val: float) -> None:
        """
        Set ``Ga``.

        :param val: Value to assign.
        :return: None
        """
        self._Ga = float(val)

    @property
    def Gb(self) -> float:
        """
        Get ``Gb``.

        :return: float
        """
        return self._Gb

    @Gb.setter
    def Gb(self, val: float) -> None:
        """
        Set ``Gb``.

        :param val: Value to assign.
        :return: None
        """
        self._Gb = float(val)

    @property
    def Gc(self) -> float:
        """
        Get ``Gc``.

        :return: float
        """
        return self._Gc

    @Gc.setter
    def Gc(self, val: float) -> None:
        """
        Set ``Gc``.

        :param val: Value to assign.
        :return: None
        """
        self._Gc = float(val)

    @property
    def B(self) -> float:
        """
        Get ``B``.

        :return: float
        """
        return self._B

    @B.setter
    def B(self, val: float) -> None:
        """
        Set ``B``.

        :param val: Value to assign.
        :return: None
        """
        self._B = float(val)

    @property
    def B0(self) -> float:
        """
        Get ``B0``.

        :return: float
        """
        return self._B0

    @B0.setter
    def B0(self, val: float) -> None:
        """
        Set ``B0``.

        :param val: Value to assign.
        :return: None
        """
        self._B0 = float(val)

    @property
    def Ba(self) -> float:
        """
        Get ``Ba``.

        :return: float
        """
        return self._Ba

    @Ba.setter
    def Ba(self, val: float) -> None:
        """
        Set ``Ba``.

        :param val: Value to assign.
        :return: None
        """
        self._Ba = float(val)

    @property
    def Bb(self) -> float:
        """
        Get ``Bb``.

        :return: float
        """
        return self._Bb

    @Bb.setter
    def Bb(self, val: float) -> None:
        """
        Set ``Bb``.

        :param val: Value to assign.
        :return: None
        """
        self._Bb = float(val)

    @property
    def Bc(self) -> float:
        """
        Get ``Bc``.

        :return: float
        """
        return self._Bc

    @Bc.setter
    def Bc(self, val: float) -> None:
        """
        Set ``Bc``.

        :param val: Value to assign.
        :return: None
        """
        self._Bc = float(val)
