# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple
import numpy as np

from VeraGridEngine.enumerations import DeviceType, BuildStatus, SubObjectType, ShuntControlMode, PrpCat
from VeraGridEngine.Devices.Parents.shunt_parent import ShuntParent
from VeraGridEngine.Devices.Profiles import ProfileFloat, ProfileInt
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp
from VeraGridEngine.basic_structures import Vec


class ControllableShunt(ShuntParent):
    """
    Controllable Shunt
    """
    __slots__ = (
        '_Bmin',
        '_Bmax',
        '_Gmin',
        '_Gmax',
        'g_per_step',
        'b_per_step',
        '_active_steps',
        '_g_steps',
        '_b_steps',
        '_step',
        '_step_prof',
        'control_bus',
        '_control_bus_prof',
        '_Vset',
        '_Vmin',
        '_Vmax',
        '_Vset_prof',
        'control_mode',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='control_mode',
            units='',
            tpe=ShuntControlMode,
            definition='Shunt control mode',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='control_bus',
            units='',
            tpe=DeviceType.BusDevice,
            definition='Alternative control bus',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='g_steps',
            units='MW@v=1p.u.',
            tpe=SubObjectType.Array,
            definition='Conductance steps',
            editable=False,
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='b_steps',
            units='MVAr@v=1p.u.',
            tpe=SubObjectType.Array,
            definition='Susceptance steps',
            editable=False,
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Gmax',
            units='MW',
            tpe=float,
            definition='Maximum conductance',
            editable=True,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Gmin',
            units='MW',
            tpe=float,
            definition='Minimum conductance',
            editable=True,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Bmax',
            units='MVAr',
            tpe=float,
            definition='Maximum susceptance',
            editable=True,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Bmin',
            units='MVAr',
            tpe=float,
            definition='Minimum susceptance',
            editable=True,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='active_steps',
            units='',
            tpe=SubObjectType.Array,
            definition='steps active?',
            editable=False,
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='step',
            units='',
            tpe=int,
            definition='Device step position (0~N-1)',
            profile_name='step_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Vmin',
            units='p.u.',
            tpe=float,
            definition='Lower range voltage value when regulating with Discrete mode',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Vset',
            units='p.u.',
            tpe=float,
            definition='Set voltage. This is used for controlled shunts.',
            profile_name='Vset_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Vmax',
            units='p.u.',
            tpe=float,
            definition='Upper range voltage value when regulating with Discrete mode.',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
    )

    def __init__(self,
                 name='Controllable Shunt',
                 idtag: Union[None, str] = None,
                 code: str = '',
                 number_of_steps: int = 1,
                 step: int = 1,
                 g_per_step: float = 0.0,
                 b_per_step: float = 0.0,
                 Bmin: float = -9999.0,
                 Bmax: float = 9999.0,
                 Gmin: float = -9999.0,
                 Gmax: float = 9999.0,
                 Cost: float = 1200.0,
                 active: bool = True,
                 G: float = 1e-20,
                 G1: float = 1e-20,
                 G2: float = 1e-20,
                 G3: float = 1e-20,
                 B: float = 1e-20,
                 B1: float = 1e-20,
                 B2: float = 1e-20,
                 B3: float = 1e-20,
                 G0: float = 1e-20,
                 B0: float = 1e-20,
                 vset: float = 1.0,
                 vmin: float = 0.9,
                 vmax: float = 1.1,
                 mttf: float = 0.0,
                 mttr: float = 0.0,
                 capex: float = 0.0,
                 opex: float = 0.0,
                 control_bus: Bus = None,
                 control_mode: ShuntControlMode = ShuntControlMode.Continuous,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """
        The controllable shunt object implements the so-called ZIP model, in which the load can be
        represented by a combination of power (P), current(I), and impedance (Z).
        The sign convention is: Positive to act as a load, negative to act as a generator.
        :param name: Name of the load
        :param idtag: UUID code
        :param code: secondary ID code
        :param Cost: Cost of load shedding
        :param active: Is the load active?
        :param mttf: Mean time to failure in hours
        :param mttr: Mean time to recovery in hours
        """
        ShuntParent.__init__(self,
                             name=name,
                             idtag=idtag,
                             code=code,
                             bus=None,
                             active=active,
                             G=G,
                             G1=G1,
                             G2=G2,
                             G3=G3,
                             B=B,
                             B1=B1,
                             B2=B2,
                             B3=B3,
                             G0=G0,
                             B0=B0,
                             Cost=Cost,
                             mttf=mttf,
                             mttr=mttr,
                             capex=capex,
                             opex=opex,
                             build_status=build_status,
                             device_type=DeviceType.ControllableShuntDevice)

        self.Bmin = Bmin
        self.Bmax = Bmax

        self.Gmin = Gmin
        self.Gmax = Gmax

        if number_of_steps > 0:
            self.g_per_step = (self.Gmin + self.Gmax) / number_of_steps
            self.b_per_step = (self.Bmin + self.Bmax) / number_of_steps
            self._active_steps = np.ones(number_of_steps, dtype=int)

        else:
            self.g_per_step = 0
            self.b_per_step = 0
            self._active_steps = np.ones(0, dtype=int)

        self._g_steps = np.full(number_of_steps, g_per_step)
        self._b_steps = np.full(number_of_steps, b_per_step)

        self._step = int(step)
        self._step_prof = ProfileInt(default_value=self._step)

        self.control_bus = control_bus

        # Voltage module set point (p.u.)
        self.Vset = float(vset)

        # voltage set profile for this load in p.u.
        self._Vset_prof = ProfileFloat(default_value=self.Vset)

        self.Vmin = float(vmin)
        self.Vmax = float(vmax)

        self.control_mode: ShuntControlMode = control_mode

    @property
    def step(self):
        """
        Step
        :return:
        """
        return self._step

    @step.setter
    def step(self, value: int):
        value = int(value)

        if self.auto_update_enabled:

            if 0 <= value < len(self._b_steps):
                self._step = int(value)

                # override value on change
                self.B = np.sum(self._b_steps[:self._step + 1] * self._active_steps[:self._step + 1])
                self.G = np.sum(self._g_steps[:self._step + 1] * self._active_steps[:self._step + 1])
        else:

            self._step = int(value)

    @property
    def g_steps(self):
        """
        G steps
        :return:
        """
        return self._g_steps

    @g_steps.setter
    def g_steps(self, value: np.ndarray):
        assert isinstance(value, np.ndarray)
        self._g_steps = value

    @property
    def active_steps(self):
        """
        G steps
        :return:
        """
        return self._active_steps

    @active_steps.setter
    def active_steps(self, value: np.ndarray):
        assert isinstance(value, np.ndarray)
        self._active_steps = value.astype(int)

    def set_blocks(self, n_list: list[int], b_list: list[float]):
        """
        Initialize the steps from block data
        :param n_list: list of number of blocks per step
        :param b_list: list of unit impedance block at each step
        """
        assert len(n_list) == len(b_list)
        nn = len(n_list)
        self._active_steps = np.ones(nn, dtype=int)
        self._b_steps = np.zeros(nn)
        self._g_steps = np.zeros(nn)

        for i in range(nn):
            self._b_steps[i] = n_list[i] * b_list[i]

    def get_block_points(self):
        """
        Get B points for CGMES export.
        :return:
        :rtype:
        """
        return self._b_steps, self._g_steps

    def get_cumulative_b(self) -> Vec:
        """
        Get the cumulative B values
        :return:
        """
        return np.cumsum(self._b_steps * self._active_steps).astype(float)

    def get_cumulative_g(self) -> Vec:
        """
        Get the cumulative G values
        :return:
        """
        return np.cumsum(self._g_steps * self._active_steps).astype(float)

    @property
    def b_steps(self):
        """
        B steps
        :return:
        """
        return self._b_steps

    @b_steps.setter
    def b_steps(self, value: np.ndarray):
        assert isinstance(value, np.ndarray)
        self._b_steps = value
        # self.Bmax = value.max()
        # self.Bmin = value.min()

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
    def step_prof(self) -> ProfileInt:
        """
        Cost profile
        :return: Profile
        """
        return self._step_prof

    @step_prof.setter
    def step_prof(self, val: Union[ProfileInt, np.ndarray]):
        if isinstance(val, ProfileInt):
            self._step_prof = val
        elif isinstance(val, np.ndarray):
            self._step_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a step_prof')

    def get_step_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.step, self.step_prof, t)

    def get_linear_g_steps(self):
        """

        :return:
        """
        if len(self._g_steps) == 1:
            return self._g_steps
        else:
            return np.diff(self._g_steps)

    def get_linear_b_steps(self):
        """

        :return:
        """
        if len(self._b_steps) == 1:
            return self._b_steps
        else:
            return np.diff(self._b_steps)

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def Gmax(self) -> float:
        """
        Get ``Gmax``.

        :return: float
        """
        return self._Gmax

    @Gmax.setter
    def Gmax(self, val: float) -> None:
        """
        Set ``Gmax``.

        :param val: Value to assign.
        :return: None
        """
        self._Gmax = float(val)

    @property
    def Gmin(self) -> float:
        """
        Get ``Gmin``.

        :return: float
        """
        return self._Gmin

    @Gmin.setter
    def Gmin(self, val: float) -> None:
        """
        Set ``Gmin``.

        :param val: Value to assign.
        :return: None
        """
        self._Gmin = float(val)

    @property
    def Bmax(self) -> float:
        """
        Get ``Bmax``.

        :return: float
        """
        return self._Bmax

    @Bmax.setter
    def Bmax(self, val: float) -> None:
        """
        Set ``Bmax``.

        :param val: Value to assign.
        :return: None
        """
        self._Bmax = float(val)

    @property
    def Bmin(self) -> float:
        """
        Get ``Bmin``.

        :return: float
        """
        return self._Bmin

    @Bmin.setter
    def Bmin(self, val: float) -> None:
        """
        Set ``Bmin``.

        :param val: Value to assign.
        :return: None
        """
        self._Bmin = float(val)

    @property
    def Vmin(self) -> float:
        """
        Get ``Vmin``.

        :return: float
        """
        return self._Vmin

    @Vmin.setter
    def Vmin(self, val: float) -> None:
        """
        Set ``Vmin``.

        :param val: Value to assign.
        :return: None
        """
        self._Vmin = float(val)

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
    def Vmax(self) -> float:
        """
        Get ``Vmax``.

        :return: float
        """
        return self._Vmax

    @Vmax.setter
    def Vmax(self, val: float) -> None:
        """
        Set ``Vmax``.

        :param val: Value to assign.
        :return: None
        """
        self._Vmax = float(val)
