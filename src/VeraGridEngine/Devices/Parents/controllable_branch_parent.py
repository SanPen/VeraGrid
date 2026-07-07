# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from typing import Union, Tuple

from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import (BuildStatus, TapModuleControl, TapPhaseControl, SubObjectType, TapChangerTypes,
                                         PrpCat, ParamPowerFlowReferenceType)
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Branches.tap_changer import TapChanger
from VeraGridEngine.Devices.Parents.editable_device import DeviceType, get_at, GCProp
from VeraGridEngine.Devices.Profiles import ProfileEnum, ProfileFloat


class ControllableBranchParent(BranchParent):
    __slots__ = (
        '_tolerance',
        '_R',
        '_X',
        '_G',
        '_B',
        '_R0',
        '_X0',
        '_G0',
        '_B0',
        '_R2',
        '_X2',
        '_G2',
        '_B2',
        '_tap_changer',
        '_tap_module',
        '_tap_module_prof',
        '_tap_module_max',
        '_tap_module_min',
        '_tap_phase_control_mode',
        '_tap_phase_control_mode_prof',
        '_Pset',
        '_Pset_prof',
        '_Qset',
        '_Qset_prof',
        '_tap_phase',
        '_tap_phase_prof',
        '_tap_phase_max',
        '_tap_phase_min',
        '_tap_module_control_mode',
        '_tap_module_control_mode_prof',
        '_vset',
        '_vset_prof',
        'regulation_branch',
        'regulation_bus',
        'regulation_cn',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='R',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence resistance.',
            old_names=['R1', 'Rl'],
            cat=[PrpCat.PF, PrpCat.PF3],
        ),
        GCProp(
            prop_name='X',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence reactance.',
            old_names=['X1', 'Xl'],
            cat=[PrpCat.PF, PrpCat.PF3],
        ),
        GCProp(
            prop_name='G',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence shunt conductance.',
            cat=[PrpCat.PF, PrpCat.PF3],
            dyn_ref=ParamPowerFlowReferenceType.gFe,
        ),
        GCProp(
            prop_name='B',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence shunt susceptance.',
            cat=[PrpCat.PF, PrpCat.PF3],
            dyn_ref=ParamPowerFlowReferenceType.bsh,
        ),
        GCProp(
            prop_name='R0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence resistance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='X0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence reactance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='G0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence shunt conductance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='B0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence shunt susceptance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='R2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence resistance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='X2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence reactance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='G2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence shunt conductance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='B2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence shunt susceptance.',
            cat=[PrpCat.PF3, PrpCat.SC],
        ),
        GCProp(
            prop_name='tolerance',
            units='%',
            tpe=float,
            definition='Tolerance expected for the impedance values% '
                          'is expected for transformers0% for lines.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='tap_changer',
            units='',
            tpe=SubObjectType.TapChanger,
            definition='Tap changer object',
            editable=False,
            display=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_module',
            units='',
            tpe=float,
            definition='Tap changer module, it a value close to 1.0',
            profile_name='tap_module_prof',
            old_names=['tap', 'm'],
            cat=[PrpCat.PF, PrpCat.OPF],
            dyn_ref=ParamPowerFlowReferenceType.tap_module,
        ),
        GCProp(
            prop_name='tap_module_max',
            units='',
            tpe=float,
            definition='Tap changer module max value',
            old_names=['m_max'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_module_min',
            units='',
            tpe=float,
            definition='Tap changer module min value',
            old_names=['m_min'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_module_control_mode',
            units='',
            tpe=TapModuleControl,
            definition='Control available with the tap module',
            profile_name='tap_module_control_mode_prof',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='vset',
            units='p.u.',
            tpe=float,
            definition='Objective voltage at the "to" side of the bus when regulating the tap.',
            profile_name='vset_prof',
            old_names=['Vdc_set'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Qset',
            units='MVAr',
            tpe=float,
            definition='Objective power at the selected side.',
            profile_name='Qset_prof',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='regulation_bus',
            units='',
            tpe=DeviceType.BusDevice,
            definition='Bus where the regulation is applied.',
            editable=True,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase',
            units='rad',
            tpe=float,
            definition='Angle shift of the tap changer.',
            profile_name='tap_phase_prof',
            old_names=['angle', 'theta'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase_max',
            units='rad',
            tpe=float,
            definition='Max angle.',
            old_names=['angle_max', 'theta_max'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase_min',
            units='rad',
            tpe=float,
            definition='Min angle.',
            old_names=['angle_min', 'theta_min'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase_control_mode',
            units='',
            tpe=TapPhaseControl,
            definition='Control available with the tap angle',
            old_names=['tap_angle_control_mode'],
            profile_name='tap_phase_control_mode_prof',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='Pset',
            units='MW',
            tpe=float,
            definition='Objective power at the selected side.',
            profile_name='Pset_prof',
            old_names=['Pdc_set'],
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
    )

    def __init__(self,
                 bus_from: Bus | None,
                 bus_to: Bus | None,
                 name: str,
                 idtag: str | None,
                 code: str,
                 active: bool,
                 reducible: bool,
                 design_rate: float,
                 rate: float,
                 r: float,
                 x: float,
                 g: float,
                 b: float,
                 tap_module: float,
                 tap_module_max: float,
                 tap_module_min: float,
                 tap_phase: float,
                 tap_phase_max: float,
                 tap_phase_min: float,
                 tolerance: float,
                 vset: float,
                 Pset: float,
                 Qset: float,
                 regulation_branch: BranchParent | None,
                 regulation_bus: Bus | None,
                 temp_base: float,
                 temp_oper: float,
                 alpha: float,
                 tap_module_control_mode: TapModuleControl,
                 tap_phase_control_mode: TapPhaseControl,
                 contingency_factor: float,
                 protection_rating_factor: float,
                 contingency_enabled: bool,
                 monitor_loading: bool,
                 r0: float,
                 x0: float,
                 g0: float,
                 b0: float,
                 r2: float,
                 x2: float,
                 g2: float,
                 b2: float,
                 cost: float,
                 mttf: float,
                 mttr: float,
                 capex: float,
                 opex: float,
                 build_status: BuildStatus,
                 device_type: DeviceType,
                 tc_total_positions: int = 5,
                 tc_neutral_position: int = 2,
                 tc_normal_position: int = 2,
                 tc_dV: float = 0.01,
                 tc_asymmetry_angle=90,
                 tc_type: TapChangerTypes = TapChangerTypes.NoRegulation):
        """
        Transformer constructor
        :param name: Name of the branch
        :param idtag: UUID code
        :param code: secondary id
        :param bus_from: "From" :ref:`bus<Bus>` object
        :param bus_to: "To" :ref:`bus<Bus>` object
        :param r: resistance in per unit
        :param x: reactance in per unit
        :param g: shunt conductance in per unit
        :param b: shunt susceptance in per unit
        :param design_rate: Design rate (MVA)
        :param rate: rate in MVA
        :param tap_module: tap module in p.u.
        :param tap_module_max:
        :param tap_module_min:
        :param tap_phase: phase shift angle (rad)
        :param tap_phase_max:
        :param tap_phase_min:
        :param active: Is the branch active?
        :param tolerance: Tolerance specified for the branch impedance in %
        :param cost: Cost of overload (e/MW)
        :param mttf: Mean time to failure in hours
        :param mttr: Mean time to recovery in hours
        :param vset: Voltage set-point of the voltage controlled bus in per unit
        :param Pset: Power set point
        :param regulation_branch: Branch object where the flow regulation is applied
        :param regulation_bus: Bus object where the regulation is applied
        :param temp_base: Base temperature at which `r` is measured in °C
        :param temp_oper: Operating temperature in °C
        :param alpha: Thermal constant of the material in °C
        :param tap_module_control_mode: Tap module Control model
        :param tap_phase_control_mode: Tap phase Control model
        :param contingency_factor: Rating factor in case of contingency
        :param contingency_enabled: enabled for contingencies (Legacy)
        :param monitor_loading: monitor the loading (used in OPF)
        :param r0: zero-sequence resistence (p.u.)
        :param x0: zero-sequence reactance (p.u.)
        :param g0: zero-sequence conductance (p.u.)
        :param b0: zero-sequence susceptance (p.u.)
        :param r2: negative-sequence resistence (p.u.)
        :param x2: negative-sequence reactance (p.u.)
        :param g2: negative-sequence conductance (p.u.)
        :param b2: negative-sequence susceptance (p.u.)
        :param capex: Cost of investment (e/MW)
        :param opex: Cost of operation (e/MWh)
        :param build_status: build status (now time)
        """

        BranchParent.__init__(self,
                              name=name,
                              idtag=idtag,
                              code=code,
                              bus_from=bus_from,
                              bus_to=bus_to,
                              active=active,
                              reducible=reducible,
                              design_rate=design_rate,
                              rate=rate,
                              contingency_factor=contingency_factor,
                              protection_rating_factor=protection_rating_factor,
                              contingency_enabled=contingency_enabled,
                              monitor_loading=monitor_loading,
                              mttf=mttf,
                              mttr=mttr,
                              build_status=build_status,
                              capex=capex,
                              opex=opex,
                              cost=cost,
                              temp_base=temp_base,
                              temp_oper=temp_oper,
                              alpha=alpha,
                              device_type=device_type)

        # branch impedance tolerance
        self.tolerance = tolerance

        # total impedance and admittance in p.u.
        self.R = float(r)
        self.X = float(x)
        self.G = float(g)
        self.B = float(b)

        self.R0 = float(r0)
        self.X0 = float(x0)
        self.G0 = float(g0)
        self.B0 = float(b0)

        self.R2 = float(r2)
        self.X2 = float(x2)
        self.G2 = float(g2)
        self.B2 = float(b2)

        # tap changer object
        self._tap_changer = TapChanger(total_positions=tc_total_positions,
                                       neutral_position=tc_neutral_position,
                                       normal_position=tc_normal_position,
                                       dV=tc_dV,
                                       asymmetry_angle=tc_asymmetry_angle,
                                       tc_type=tc_type)

        # Tap module
        if tap_module != 0:
            self.tap_module = float(tap_module)
            self._tap_changer.set_tap_module(self.tap_module)
        else:
            self.tap_module = self._tap_changer.get_tap_module()

        self._tap_module_prof = ProfileFloat(default_value=self.tap_module)

        self._tap_module_max = float(tap_module_max)
        self._tap_module_min = float(tap_module_min)

        self._tap_phase_control_mode: TapPhaseControl = tap_phase_control_mode
        self._tap_phase_control_mode_prof = ProfileEnum(default_value=tap_phase_control_mode, enum_type=TapPhaseControl)

        self.Pset = float(Pset)
        self._Pset_prof = ProfileFloat(default_value=self.Pset)

        self.Qset = float(Qset)
        self._Qset_prof = ProfileFloat(default_value=self.Qset)

        # Tap angle
        self.tap_phase = float(tap_phase)
        self._tap_phase_prof = ProfileFloat(default_value=self.tap_phase)

        self._tap_phase_max = float(tap_phase_max)
        self._tap_phase_min = float(tap_phase_min)

        self._tap_module_control_mode: TapModuleControl = tap_module_control_mode
        self._tap_module_control_mode_prof = ProfileEnum(default_value=tap_module_control_mode, enum_type=TapModuleControl)

        self.vset = float(vset)
        self._vset_prof = ProfileFloat(default_value=self.vset)

        self.regulation_branch: BranchParent | None = regulation_branch

        self.regulation_bus: Bus | None = regulation_bus

    @property
    def tap_module_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._tap_module_prof

    @tap_module_prof.setter
    def tap_module_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._tap_module_prof = val
        elif isinstance(val, np.ndarray):
            self._tap_module_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_prof')

    def get_tap_module_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.tap_module, self.tap_module_prof, t)

    @property
    def tap_phase_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._tap_phase_prof

    @tap_phase_prof.setter
    def tap_phase_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._tap_phase_prof = val
        elif isinstance(val, np.ndarray):
            self._tap_phase_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_phase_prof')

    def get_tap_phase_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.tap_phase, self.tap_phase_prof, t)

    @property
    def vset_prof(self) -> ProfileFloat:
        """
        vset profile
        :return: Profile
        """
        return self._vset_prof

    @vset_prof.setter
    def vset_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._vset_prof = val
        elif isinstance(val, np.ndarray):
            self._vset_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a vset_prof')

    def get_vset_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.vset, self.vset_prof, t)

    @property
    def Pset_prof(self) -> ProfileFloat:
        """
        vset profile
        :return: Profile
        """
        return self._Pset_prof

    @Pset_prof.setter
    def Pset_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Pset_prof = val
        elif isinstance(val, np.ndarray):
            self._Pset_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Pset_prof')

    def get_Pset_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Pset, self.Pset_prof, t)

    @property
    def Qset_prof(self) -> ProfileFloat:
        """
        vset profile
        :return: Profile
        """
        return self._Qset_prof

    @Qset_prof.setter
    def Qset_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Qset_prof = val
        elif isinstance(val, np.ndarray):
            self._Qset_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Qset_prof')

    def get_Qset_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Qset, self.Qset_prof, t)

    @property
    def tap_module_control_mode_prof(self) -> ProfileEnum:
        """
        _tap_module_control_mode_prof profile
        :return: Profile
        """
        return self._tap_module_control_mode_prof

    @tap_module_control_mode_prof.setter
    def tap_module_control_mode_prof(self, val: Union[ProfileEnum, np.ndarray]):
        if isinstance(val, ProfileEnum):
            self._tap_module_control_mode_prof = val
        elif isinstance(val, np.ndarray):
            self._tap_module_control_mode_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_control_mode_prof')

    def get_tap_module_control_mode_at(self, t: int | None) -> TapModuleControl:
        """
        :param t:
        :return:
        """
        return get_at(self.tap_module_control_mode, self.tap_module_control_mode_prof, t)

    @property
    def tap_phase_control_mode_prof(self) -> ProfileEnum:
        """
        tap_phase_control_mode_prof profile
        :return: Profile
        """
        return self._tap_phase_control_mode_prof

    @tap_phase_control_mode_prof.setter
    def tap_phase_control_mode_prof(self, val: Union[ProfileEnum, np.ndarray]):
        if isinstance(val, ProfileEnum):
            self._tap_phase_control_mode_prof = val
        elif isinstance(val, np.ndarray):
            self._tap_phase_control_mode_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_phase_control_mode_prof')

    def get_tap_phase_control_mode_at(self, t: int | None) -> TapPhaseControl:
        """
        :param t:
        :return:
        """
        return get_at(self.tap_phase_control_mode, self.tap_phase_control_mode_prof, t)

    @property
    def tap_module_min(self):
        """

        :return:
        """
        return self._tap_module_min

    @tap_module_min.setter
    def tap_module_min(self, val: float):
        val = float(val)
        if isinstance(val, float):
            self._tap_module_min = val
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_min')

    @property
    def tap_module_max(self):
        """

        :return:
        """
        return self._tap_module_max

    @tap_module_max.setter
    def tap_module_max(self, val: float):
        val = float(val)
        if isinstance(val, float):
            self._tap_module_max = val
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_min')

    @property
    def tap_phase_min(self):
        """

        :return:
        """
        return self._tap_phase_min

    @tap_phase_min.setter
    def tap_phase_min(self, val: float):
        val = float(val)
        if isinstance(val, float):
            self._tap_phase_min = val
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_min')

    @property
    def tap_phase_max(self):
        """

        :return:
        """
        return self._tap_phase_max

    @tap_phase_max.setter
    def tap_phase_max(self, val: float):
        val = float(val)
        if isinstance(val, float):
            self._tap_phase_max = val
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_module_min')

    @property
    def tap_changer(self) -> TapChanger:
        """
        Cost profile
        :return: Profile
        """
        return self._tap_changer

    @tap_changer.setter
    def tap_changer(self, val: TapChanger):
        if isinstance(val, TapChanger):
            self._tap_changer = val
            self.tap_module_min = val.get_tap_module_min()
            self.tap_module_max = val.get_tap_module_max()
            self.tap_phase_min = val.get_tap_phase_min()
            self.tap_phase_max = val.get_tap_phase_max()
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a tap_changer')

    @property
    def tap_phase_control_mode(self) -> TapPhaseControl:
        """
        Get the tap phase control mode
        :return: TapPhaseControl
        """
        return self._tap_phase_control_mode

    @tap_phase_control_mode.setter
    def tap_phase_control_mode(self, val: TapPhaseControl):
        assert isinstance(val, TapPhaseControl)
        self._tap_phase_control_mode = val

    @property
    def tap_module_control_mode(self) -> TapModuleControl:
        """
        Get the tap module control mode
        :return: TapPhaseControl
        """
        return self._tap_module_control_mode

    @tap_module_control_mode.setter
    def tap_module_control_mode(self, val: TapModuleControl):
        assert isinstance(val, TapModuleControl)
        self._tap_module_control_mode = val

    @property
    def R_corrected(self):
        """
        Returns a temperature corrected resistance based on a formula provided by:
        NFPA 70-2005, National Electrical Code, Table 8, footnote #2; and
        https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity#Linear_approximation
        (version of 2019-01-03 at 15:20 EST).
        """
        return self.R * (1 + self.alpha * (self.temp_oper - self.temp_base))

    def change_base(self, Sbase_old: float, Sbase_new: float):
        """
        Change the impedance base
        :param Sbase_old: old base (MVA)
        :param Sbase_new: new base (MVA)
        """
        b = Sbase_new / Sbase_old

        self.R *= b
        self.X *= b
        self.G *= b
        self.B *= b

    def get_weight(self):
        """
        Get a weight for the graphs
        :return: sqrt(r^2 + x^2)
        """
        return np.sqrt(self.R * self.R + self.X * self.X)

    def flip(self):
        """
        Change the terminals' positions
        """
        F, T = self.bus_from, self.bus_to
        self.bus_to, self.bus_from = F, T

    def set_tap_controls(self, tap_phase_control_mode: TapPhaseControl, tap_module_control_mode: TapModuleControl):
        """
        Set both tap controls
        :param tap_phase_control_mode: TapPhaseControl
        :param tap_module_control_mode: TapModuleControl
        """
        self.tap_phase_control_mode = tap_phase_control_mode
        self.tap_module_control_mode = tap_module_control_mode

    def tap_up(self):
        """
        Move the tap changer one position up
        """
        self.tap_changer.tap_up()
        self.tap_module = self.tap_changer.get_tap_module()
        self.tap_phase = self.tap_changer.get_tap_phase()

    def tap_down(self):
        """
        Move the tap changer one position up
        """
        self.tap_changer.tap_down()
        self.tap_module = self.tap_changer.get_tap_module()
        self.tap_phase = self.tap_changer.get_tap_phase()

    def apply_tap_changer(self, tap_changer: TapChanger):
        """
        Apply a new tap changer

        Argument:

            **tap_changer** (:class:`VeraGridEngine.Devices.branch.TapChanger`): Tap changer object

        """
        self.tap_changer = tap_changer

        if self.tap_module != 0:
            self.tap_changer.set_tap_module(tap_module=self.tap_module)
        else:
            self.tap_module = self.tap_changer.get_tap_module()
            self.tap_phase = self.tap_changer.get_tap_phase()

    # Scalar property accessors coerce assignments to the declared schema types.

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
    def G2(self) -> float:
        """
        Get ``G2``.

        :return: float
        """
        return self._G2

    @G2.setter
    def G2(self, val: float) -> None:
        """
        Set ``G2``.

        :param val: Value to assign.
        :return: None
        """
        self._G2 = float(val)

    @property
    def B2(self) -> float:
        """
        Get ``B2``.

        :return: float
        """
        return self._B2

    @B2.setter
    def B2(self, val: float) -> None:
        """
        Set ``B2``.

        :param val: Value to assign.
        :return: None
        """
        self._B2 = float(val)

    @property
    def tolerance(self) -> float:
        """
        Get ``tolerance``.

        :return: float
        """
        return self._tolerance

    @tolerance.setter
    def tolerance(self, val: float) -> None:
        """
        Set ``tolerance``.

        :param val: Value to assign.
        :return: None
        """
        self._tolerance = float(val)

    @property
    def tap_module(self) -> float:
        """
        Get ``tap_module``.

        :return: float
        """
        return self._tap_module

    @tap_module.setter
    def tap_module(self, val: float) -> None:
        """
        Set ``tap_module``.

        :param val: Value to assign.
        :return: None
        """
        self._tap_module = float(val)

    @property
    def vset(self) -> float:
        """
        Get ``vset``.

        :return: float
        """
        return self._vset

    @vset.setter
    def vset(self, val: float) -> None:
        """
        Set ``vset``.

        :param val: Value to assign.
        :return: None
        """
        self._vset = float(val)

    @property
    def Qset(self) -> float:
        """
        Get ``Qset``.

        :return: float
        """
        return self._Qset

    @Qset.setter
    def Qset(self, val: float) -> None:
        """
        Set ``Qset``.

        :param val: Value to assign.
        :return: None
        """
        self._Qset = float(val)

    @property
    def tap_phase(self) -> float:
        """
        Get ``tap_phase``.

        :return: float
        """
        return self._tap_phase

    @tap_phase.setter
    def tap_phase(self, val: float) -> None:
        """
        Set ``tap_phase``.

        :param val: Value to assign.
        :return: None
        """
        self._tap_phase = float(val)

    @property
    def Pset(self) -> float:
        """
        Get ``Pset``.

        :return: float
        """
        return self._Pset

    @Pset.setter
    def Pset(self, val: float) -> None:
        """
        Set ``Pset``.

        :param val: Value to assign.
        :return: None
        """
        self._Pset = float(val)
