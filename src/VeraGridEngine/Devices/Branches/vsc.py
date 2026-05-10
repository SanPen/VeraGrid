# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from typing import List, Tuple, TYPE_CHECKING
from VeraGridEngine.Devices.Profiles import ProfileDevice, ProfileEnum, ProfileFloat
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, ConverterControlType, ConverterFaultControlType, PrpCat
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp
from VeraGridEngine.Devices.Parents.editable_device import get_at

if TYPE_CHECKING:
    from VeraGridEngine.Devices.types import BRANCH_TYPES


class VSC(BranchParent):
    __slots__ = (
        '_u_setpoint_min',
        '_u_setpoint_max',
        '_u_setpoint',
        '_du_setpoint',
        '_Q_min',
        '_Q_max',
        '_alpha1',
        '_alpha2',
        '_alpha3',
        '_control1',
        '_control1_prof',
        '_control1_dev',
        '_control1_dev_prof',
        '_control1_val',
        '_control1_val_prof',
        '_control1_val_min',
        '_control1_val_max',
        '_control1_droop',
        '_control1_droop_prof',
        '_control1_droop_val',
        '_control1_droop_val_prof',
        '_control1_droop_val_min',
        '_control1_droop_val_max',

        '_control2',
        '_control2_prof',
        '_control2_dev',
        '_control2_dev_prof',
        '_control2_val',
        '_control2_val_prof',
        '_control2_val_min',
        '_control2_val_max',
        '_control2_val_droop',
        '_control2_val_droop_prof',
        '_control2_droop_val',
        '_control2_droop_val_prof',
        '_control2_droop_val_min',
        '_control2_droop_val_max',

        '_fault_control',
        '_fault_control_prof',
        '_bus_dc_n',
        '_min_ac_voltage',
        '_ysvs',
        '_x',
        '_y',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='bus_dc_n',
            units="",
            tpe=DeviceType.BusDevice,
            definition='DC negative bus',
            editable=False,
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='alpha1',
            units='',
            tpe=float,
            definition='Losses constant parameter (IEC 62751-2 loss Correction, idle loss).',
        ),
        GCProp(
            prop_name='alpha2',
            units='',
            tpe=float,
            definition='Losses linear parameter (IEC 62751-2 loss Correction, Switching loss).',
        ),
        GCProp(
            prop_name='alpha3',
            units='',
            tpe=float,
            definition='Losses quadratic parameter (IEC 62751-2 loss Correction, resistive loss).',
        ),


        GCProp(
            prop_name='control1',
            units='',
            tpe=ConverterControlType,
            profile_name="control1_prof",
            definition='Control mode 1.',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_dev',
            units="",
            tpe=DeviceType.BusOrBranch,
            profile_name="control1_dev_prof",
            definition='Controlled device, None to apply to this converter',
            editable=False,
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='control1_val',
            units='',
            tpe=float,
            profile_name="control1_val_prof",
            definition='Control value 1.'
                          'p.u. for voltage\n'
                          'rad for angles\n'
                          'MW for P\n'
                          'MVAr for Q',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='control1_val_min',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_val_max',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_droop',
            units='',
            tpe=float,
            profile_name="control1_droop_prof",
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_droop_val',
            units='',
            tpe=float,
            profile_name="control1_droop_val_prof",
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_droop_val_min',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control1_droop_val_max',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),

        GCProp(
            prop_name='control2',
            units='',
            tpe=ConverterControlType,
            profile_name="control2_prof",
            definition='Control mode 2.',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_dev',
            units="",
            tpe=DeviceType.BusOrBranch,
            profile_name="control2_dev_prof",
            definition='Controlled device, None to apply to this converter',
            editable=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_val',
            units='',
            tpe=float,
            profile_name="control2_val_prof",
            definition='Control value 2.'
                                 'p.u. for voltage\n'
                                 'rad for angles\n'
                                 'MW for P\n'
                                 'MVAr for Q',
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_val_min',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_val_max',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_val_droop',
            units='',
            tpe=float,
            profile_name="control2_val_droop_prof",
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_droop_val',
            units='',
            tpe=float,
            profile_name="control2_droop_val_prof",
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_droop_val_min',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='control2_droop_val_max',
            units='',
            tpe=float,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),

        GCProp(
            prop_name='fault_control',
            units='',
            tpe=ConverterFaultControlType,
            profile_name="fault_control_prof",
            definition='VSC control system during a short-circuit event.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='min_ac_voltage',
            units='p.u.',
            tpe=float,
            definition='Minimum AC voltage threshold. '
                                 'If the AC bus voltage drops below this value, the VSC is disconnected.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='ysvs',
            units='p.u.',
            tpe=float,
            definition='Admittance of non-controlled Static Var Systems.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='x',
            units='px',
            tpe=float,
            definition='x position',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='y',
            units='px',
            tpe=float,
            definition='y position',
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self,
                 bus_from: Bus | None = None,
                 bus_to: Bus | None = None,
                 bus_dc_n: Bus | None = None,
                 name='VSC',
                 idtag: str | None = None,
                 code='',
                 active=True,
                 rate: float = 100.0,
                 alpha1=0.0001,
                 alpha2=0.015,
                 alpha3=0.2,
                 mttf=0.0,
                 mttr=0.0,
                 cost=100,
                 contingency_factor=1.0,
                 protection_rating_factor: float = 1.4,
                 contingency_enabled=True,
                 monitor_loading=True,
                 capex=0.0,
                 opex=0.0,
                 build_status: BuildStatus = BuildStatus.Commissioned,

                 control1: ConverterControlType = ConverterControlType.Q_droop,
                 control1_dev: Bus | BRANCH_TYPES | None = None,
                 control1_val: float = 1.0,
                 control1_val_min: float = -9999.0,
                 control1_val_max: float = 9999.0,
                 control1_droop: float = 0.1,
                 control1_droop_val: float = 1.0,
                 control1_droop_val_min: float = 0.9,
                 control1_droop_val_max: float = 1.1,

                 control2: ConverterControlType = ConverterControlType.Vm_dc,
                 control2_dev: Bus | BRANCH_TYPES | None = None,
                 control2_val: float = 0.0,
                 control2_val_min: float = -9999.0,
                 control2_val_max: float = 9999.0,
                 control2_droop: float = 0.1,
                 control2_droop_val: float = 1.0,
                 control2_droop_val_min: float = 0.9,
                 control2_droop_val_max: float = 1.1,

                 fault_control: ConverterFaultControlType = ConverterFaultControlType.Standard,

                 min_ac_voltage: float = 0.1,
                 ysvs: float = 0.0,
                 x: float = 0.0,
                 y: float = 0.0):
        """
        Voltage source converter (VSC) with 3 terminals
        :param bus_from: bus_dc_p
        :param bus_to: bus_ac
        :param bus_dc_n:
        :param bus_from:
        :param bus_to:
        :param name:
        :param idtag:
        :param code:
        :param active:
        :param rate:
        :param alpha1:
        :param alpha2:
        :param alpha3:
        :param mttf:
        :param mttr:
        :param cost:
        :param contingency_factor:
        :param protection_rating_factor:
        :param contingency_enabled:
        :param monitor_loading:
        :param capex:
        :param opex:
        :param build_status:
        :param control1:
        :param control2:
        :param fault_control:
        :param min_ac_voltage: Voltage threshold below which the converter is disconnected
        :param ysvs: Admittance of Static Var Systems
        :param x: graphical x position (px)
        :param y: graphical y position (px)
        """

        BranchParent.__init__(self,
                              name=name,
                              idtag=idtag,
                              code=code,
                              bus_from=bus_from,
                              bus_to=bus_to,
                              active=active,
                              reducible=False,
                              rate=rate,
                              cost=cost,
                              mttf=mttf,
                              mttr=mttr,
                              contingency_factor=contingency_factor,
                              protection_rating_factor=protection_rating_factor,
                              contingency_enabled=contingency_enabled,
                              monitor_loading=monitor_loading,
                              capex=capex,
                              opex=opex,
                              build_status=build_status,
                              temp_base=25,
                              temp_oper=25,
                              alpha=0.0033,
                              device_type=DeviceType.VscDevice)

        # TODO SANPEN: this is making the ntc test fail
        # if bus_from is not None and bus_dc_n is not None and bus_to is not None:
        #     if bus_from.is_dc and bus_dc_n.is_dc and not bus_to.is_dc:
        #         # self._bus_dc_p = bus_dc_p
        #         # self._bus_dc_n = bus_dc_n
        #         # self._bus_ac = bus_ac
        #
        #         # self._cn_dc_p = cn_dc_p
        #         # self._cn_dc_n = cn_dc_n
        #         # self._cn_ac = cn_ac
        #
        #         self._bus_from = bus_from
        #         self._bus_dc_n = bus_dc_n
        #         self._bus_to = bus_to
        #
        #     else:
        #         raise Exception('Impossible connecting a VSC device here. '
        #                         'VSC devices must be connected between 1 AC and 2 DC buses')
        # else:
        #     # self._bus_dc_p = None
        #     # self._bus_dc_n = None
        #     # self._bus_ac = None
        #
        #     # self._cn_dc_p = None
        #     # self._cn_dc_n = None
        #     # self._cn_ac = None
        #
        #     self._bus_from = None
        #     self._bus_dc_n = None
        #     self._bus_to = None

        # the VSC must only connect from an DC to a AC bus
        # this connectivity sense is done to keep track with the articles that set it
        # from -> DC
        # to   -> AC
        # assert(bus_from.is_dc != bus_to.is_dc)
        if bus_to is not None and bus_from is not None:
            # connectivity:
            # for the later primitives to make sense, the "bus from" must be AC and the "bus to" must be DC
            if bus_from.is_dc and not bus_to.is_dc:  # this is the correct sense
                self.bus_from = bus_from
                self.bus_to = bus_to
            elif not bus_from.is_dc and bus_to.is_dc:  # opposite sense, revert
                self.bus_from = bus_to
                self.bus_to = bus_from
                print('Corrected the connection direction of the VSC device:', self.name)
            else:
                raise Exception('Impossible connecting a VSC device here. '
                                'VSC devices must be connected between AC and DC buses')
        else:
            self.bus_from = None
            self.bus_to = None

        # self._bus_from = bus_from
        self._bus_dc_n = bus_dc_n
        # self._bus_to = bus_to

        self.alpha1 = float(alpha1)
        self.alpha2 = float(alpha2)
        self.alpha3 = float(alpha3)

        # u_setpoint_min: float = 0.9, -> min_val
        # u_setpoint_max: float = 1.1, -> max_val
        # u_setpoint: float = 1.0,  -> val
        # Q_min: float = -999.0,
        # Q_max: float = 999.0,

        self._control1: ConverterControlType = control1
        self._control1_prof: ProfileEnum = ProfileEnum(default_value=control1, enum_type=ConverterControlType)
        self._control1_dev: Bus | BRANCH_TYPES | None = control1_dev
        self._control1_dev_prof: ProfileDevice = ProfileDevice(default_value=control1_dev,
                                                               device_type=DeviceType.BusOrBranch)
        self._control1_val = float(control1_val)
        self._control1_val_prof: ProfileFloat = ProfileFloat(default_value=self._control1_val)
        self._control1_val_min = float(control1_val_min)
        self._control1_val_max = float(control1_val_max)
        self._control1_droop = float(control1_droop)
        self._control1_droop_prof: ProfileFloat = ProfileFloat(default_value=self._control1_droop)
        self._control1_droop_val = float(control1_droop_val)
        self._control1_droop_val_prof: ProfileFloat = ProfileFloat(default_value=self._control1_droop_val)
        self._control1_droop_val_min = float(control1_droop_val_min)
        self._control1_droop_val_max = float(control1_droop_val_max)

        self._control2: ConverterControlType = control2
        self._control2_prof: ProfileEnum = ProfileEnum(default_value=control2, enum_type=ConverterControlType)
        self._control2_dev: Bus | BRANCH_TYPES | None = control2_dev
        self._control2_dev_prof: ProfileDevice = ProfileDevice(default_value=control2_dev,
                                                               device_type=DeviceType.BusOrBranch)
        self._control2_val = float(control2_val)
        self._control2_val_prof: ProfileFloat = ProfileFloat(default_value=self._control2_val)
        self._control2_val_min = float(control2_val_min)
        self._control2_val_max = float(control2_val_max)
        self._control2_val_droop = float(control2_droop)
        self._control2_val_droop_prof: ProfileFloat = ProfileFloat(default_value=self._control2_val_droop)
        self._control2_droop_val = float(control2_droop_val)
        self._control2_droop_val_prof: ProfileFloat = ProfileFloat(default_value=self._control2_droop_val)
        self._control2_droop_val_min = float(control2_droop_val_min)
        self._control2_droop_val_max = float(control2_droop_val_max)

        self._fault_control: ConverterFaultControlType = fault_control
        self._fault_control_prof: ProfileEnum = ProfileEnum(default_value=fault_control,
                                                            enum_type=ConverterFaultControlType)

        self.min_ac_voltage = float(min_ac_voltage)

        self._ysvs = float(ysvs)

        self.x = float(x)
        self.y = float(y)

    @property
    def bus_from(self) -> Bus:
        """
        Get the DC positive bus
        """
        return self._bus_from

    @bus_from.setter
    def bus_from(self, value: Bus):
        if value is None:
            self._bus_from = value
        else:
            if isinstance(value, Bus):
                if value.is_dc:
                    self._bus_from = value
                else:
                    raise Exception('This should be a DC bus')
            else:
                raise Exception(str(type(value)) + 'not supported to be set into a _bus_from')

    @property
    def bus_dc_n(self) -> Bus:
        """
        Get the DC negative bus
        """
        return self._bus_dc_n

    @bus_dc_n.setter
    def bus_dc_n(self, value: Bus):
        if value is None:
            self._bus_dc_n = value
        else:
            if isinstance(value, Bus):
                if value.is_dc:
                    self._bus_dc_n = value
                else:
                    raise Exception('This should be a DC bus')
            else:
                raise Exception(str(type(value)) + 'not supported to be set into a _bus_dc_n')

    @property
    def bus_to(self) -> Bus:
        """
        Get the AC bus
        """
        return self._bus_to

    @bus_to.setter
    def bus_to(self, value: Bus):
        if value is None:
            self._bus_to = value
        else:
            if isinstance(value, Bus):
                if not value.is_dc:
                    self._bus_to = value
                else:
                    raise Exception('This should be an AC bus')
            else:
                raise Exception(str(type(value)) + 'not supported to be set into a _bus_to')

    # @property
    # def cn_dc_p(self) -> ConnectivityNode:
    #     """
    #     Get the DC positive connectivity node
    #     """
    #     return self._cn_dc_p

    # @cn_dc_p.setter
    # def cn_dc_p(self, val: ConnectivityNode):
    #     if val is None:
    #         self._cn_dc_p = val
    #     else:
    #         if isinstance(val, ConnectivityNode):
    #             self._cn_dc_p = val

    #             if self.bus_dc_p is None:
    #                 self.bus_dc_p = self._cn_dc_p.bus
    #         else:
    #             raise Exception(str(type(val)) + 'not supported to be set into a connectivity node from')

    @property
    def control1(self):
        """

        :return:
        """
        return self._control1

    @control1.setter
    def control1(self, value: ConverterControlType):
        if self.auto_update_enabled:
            if value != self.control2:
                self._control1 = value

                # Revert the control in range
                if (value in (ConverterControlType.Vm_dc, ConverterControlType.Vm_ac) and
                        not (0.9 < self.control1_val <= 1.1)):
                    self.control1_val = 1.0
        else:
            self._control1 = value

    @property
    def control1_prof(self) -> ProfileEnum:
        """
        Cost profile
        :return: Profile
        """
        return self._control1_prof

    @control1_prof.setter
    def control1_prof(self, val: ProfileEnum | np.ndarray):
        if isinstance(val, ProfileEnum):
            self._control1_prof = val
        elif isinstance(val, np.ndarray):
            self._control1_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control1_at(self, t: int | None) -> ConverterControlType:
        """
        :param t:
        :return:
        """
        return get_at(self.control1, self.control1_prof, t)

    @property
    def control2(self):
        """

        :return:
        """
        return self._control2

    @control2.setter
    def control2(self, value: ConverterControlType):
        if self.auto_update_enabled:
            if value != self.control1:
                self._control2 = value

                # Revert the control in range
                if (value in (ConverterControlType.Vm_dc, ConverterControlType.Vm_ac) and
                        not (0.9 < self.control2_val <= 1.1)):
                    self.control2_val = 1.0
        else:
            self._control2 = value

    @property
    def control2_prof(self) -> ProfileEnum:
        """
        Cost profile
        :return: Profile
        """
        return self._control2_prof

    @control2_prof.setter
    def control2_prof(self, val: ProfileEnum | np.ndarray):
        if isinstance(val, ProfileEnum):
            self._control2_prof = val
        elif isinstance(val, np.ndarray):
            self._control2_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control2_at(self, t: int | None) -> ConverterControlType:
        """
        :param t:
        :return:
        """
        return get_at(self.control2, self.control2_prof, t)

    @property
    def fault_control(self):
        """

        :return:
        """
        return self._fault_control

    @fault_control.setter
    def fault_control(self, value: ConverterFaultControlType):

        self._fault_control = value

    @property
    def fault_control_prof(self) -> ProfileEnum:
        """
        Cost profile
        :return: Profile
        """
        return self._fault_control_prof

    @fault_control_prof.setter
    def fault_control_prof(self, val: ProfileEnum | np.ndarray):
        if isinstance(val, ProfileEnum):
            self._fault_control_prof = val
        elif isinstance(val, np.ndarray):
            self._fault_control_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_fault_control_at(self, t: int | None) -> ConverterControlType:
        """
        :param t:
        :return:
        """
        return get_at(self.fault_control, self.fault_control_prof, t)

    @property
    def control1_val(self):
        """

        :return:
        """
        return self._control1_val

    @control1_val.setter
    def control1_val(self, value: float):
        value = float(value)
        self._control1_val = value

    @property
    def control1_val_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control1_val_prof

    @control1_val_prof.setter
    def control1_val_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control1_val_prof = val
        elif isinstance(val, np.ndarray):
            self._control1_val_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control1_val_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control1_val, self.control1_val_prof, t)

    @property
    def control2_val(self):
        """

        :return:
        """
        return self._control2_val

    @control2_val.setter
    def control2_val(self, value: float):
        value = float(value)
        self._control2_val = value

    @property
    def control2_val_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control2_val_prof

    @control2_val_prof.setter
    def control2_val_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control2_val_prof = val
        elif isinstance(val, np.ndarray):
            self._control2_val_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control2_val_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control2_val, self.control2_val_prof, t)

    @property
    def control1_val_min(self) -> float:
        """
        Get ``control1_val_min``.

        :return: float
        """
        return self._control1_val_min

    @control1_val_min.setter
    def control1_val_min(self, val: float) -> None:
        """
        Set ``control1_val_min``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_val_min = float(val)

    @property
    def control1_val_max(self) -> float:
        """
        Get ``control1_val_max``.

        :return: float
        """
        return self._control1_val_max

    @control1_val_max.setter
    def control1_val_max(self, val: float) -> None:
        """
        Set ``control1_val_max``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_val_max = float(val)

    @property
    def control1_droop(self) -> float:
        """
        Get ``control1_droop``.

        :return: float
        """
        return self._control1_droop

    @control1_droop.setter
    def control1_droop(self, val: float) -> None:
        """
        Set ``control1_droop``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_droop = float(val)

    @property
    def control1_droop_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control1_droop_prof

    @control1_droop_prof.setter
    def control1_droop_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control1_droop_prof = val
        elif isinstance(val, np.ndarray):
            self._control1_droop_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control1_droop_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control1_droop, self.control1_droop_prof, t)

    @property
    def control1_droop_val(self) -> float:
        """
        Get ``control1_droop_val``.

        :return: float
        """
        return self._control1_droop_val

    @control1_droop_val.setter
    def control1_droop_val(self, val: float) -> None:
        """
        Set ``control1_droop_val``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_droop_val = float(val)

    @property
    def control1_droop_val_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control1_droop_val_prof

    @control1_droop_val_prof.setter
    def control1_droop_val_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control1_droop_val_prof = val
        elif isinstance(val, np.ndarray):
            self._control1_droop_val_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control1_droop_val_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control1_droop_val, self.control1_droop_val_prof, t)

    @property
    def control1_droop_val_min(self) -> float:
        """
        Get ``control1_droop_val_min``.

        :return: float
        """
        return self._control1_droop_val_min

    @control1_droop_val_min.setter
    def control1_droop_val_min(self, val: float) -> None:
        """
        Set ``control1_droop_val_min``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_droop_val_min = float(val)

    @property
    def control1_droop_val_max(self) -> float:
        """
        Get ``control1_droop_val_max``.

        :return: float
        """
        return self._control1_droop_val_max

    @control1_droop_val_max.setter
    def control1_droop_val_max(self, val: float) -> None:
        """
        Set ``control1_droop_val_max``.

        :param val: Value to assign.
        :return: None
        """
        self._control1_droop_val_max = float(val)

    @property
    def control2_val_min(self) -> float:
        """
        Get ``control2_val_min``.

        :return: float
        """
        return self._control2_val_min

    @control2_val_min.setter
    def control2_val_min(self, val: float) -> None:
        """
        Set ``control2_val_min``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_val_min = float(val)

    @property
    def control2_val_max(self) -> float:
        """
        Get ``control2_val_max``.

        :return: float
        """
        return self._control2_val_max

    @control2_val_max.setter
    def control2_val_max(self, val: float) -> None:
        """
        Set ``control2_val_max``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_val_max = float(val)

    @property
    def control2_val_droop(self) -> float:
        """
        Get ``control2_val_droop``.

        :return: float
        """
        return self._control2_val_droop

    @control2_val_droop.setter
    def control2_val_droop(self, val: float) -> None:
        """
        Set ``control2_val_droop``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_val_droop = float(val)

    @property
    def control2_val_droop_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control2_val_droop_prof

    @control2_val_droop_prof.setter
    def control2_val_droop_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control2_val_droop_prof = val
        elif isinstance(val, np.ndarray):
            self._control2_val_droop_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control2_val_droop_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control2_val_droop, self.control2_val_droop_prof, t)

    @property
    def control2_droop_val(self) -> float:
        """
        Get ``control2_droop_val``.

        :return: float
        """
        return self._control2_droop_val

    @control2_droop_val.setter
    def control2_droop_val(self, val: float) -> None:
        """
        Set ``control2_droop_val``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_droop_val = float(val)

    @property
    def control2_droop_val_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._control2_droop_val_prof

    @control2_droop_val_prof.setter
    def control2_droop_val_prof(self, val: ProfileFloat | np.ndarray):
        if isinstance(val, ProfileFloat):
            self._control2_droop_val_prof = val
        elif isinstance(val, np.ndarray):
            self._control2_droop_val_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control2_droop_val_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.control2_droop_val, self.control2_droop_val_prof, t)

    @property
    def control2_droop_val_min(self) -> float:
        """
        Get ``control2_droop_val_min``.

        :return: float
        """
        return self._control2_droop_val_min

    @control2_droop_val_min.setter
    def control2_droop_val_min(self, val: float) -> None:
        """
        Set ``control2_droop_val_min``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_droop_val_min = float(val)

    @property
    def control2_droop_val_max(self) -> float:
        """
        Get ``control2_droop_val_max``.

        :return: float
        """
        return self._control2_droop_val_max

    @control2_droop_val_max.setter
    def control2_droop_val_max(self, val: float) -> None:
        """
        Set ``control2_droop_val_max``.

        :param val: Value to assign.
        :return: None
        """
        self._control2_droop_val_max = float(val)

    @property
    def control1_dev(self):
        """

        :return:
        """
        return self._control1_dev

    @control1_dev.setter
    def control1_dev(self, value: Bus | BranchParent | None = None):
        self._control1_dev = value

    @property
    def control1_dev_prof(self) -> ProfileDevice:
        """
        Cost profile
        :return: Profile
        """
        return self._control1_dev_prof

    @control1_dev_prof.setter
    def control1_dev_prof(self, val: ProfileDevice | np.ndarray):
        if isinstance(val, ProfileDevice):
            self._control1_dev_prof = val
        elif isinstance(val, np.ndarray):
            self._control1_dev_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control1_dev_at(self, t: int | None) -> Bus | BranchParent | None:
        """
        :param t:
        :return:
        """
        return get_at(self.control1_dev, self.control1_dev_prof, t)

    @property
    def control2_dev(self):
        """

        :return:
        """
        return self._control2_dev

    @control2_dev.setter
    def control2_dev(self, value: Bus | BranchParent | None = None):
        self._control2_dev = value

    @property
    def control2_dev_prof(self) -> ProfileDevice:
        """
        Cost profile
        :return: Profile
        """
        return self._control2_dev_prof

    @control2_dev_prof.setter
    def control2_dev_prof(self, val: ProfileDevice | np.ndarray):
        if isinstance(val, ProfileDevice):
            self._control2_dev_prof = val
        elif isinstance(val, np.ndarray):
            self._control2_dev_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a profile')

    def get_control2_dev_at(self, t: int | None) -> Bus | BranchParent | None:
        """
        :param t:
        :return:
        """
        return get_at(self.control2_dev, self.control2_dev_prof, t)

    def get_coordinates(self) -> List[Tuple[float, float]]:
        """
        Get the line defining coordinates
        """
        return [self.bus_from.get_coordinates(), self.bus_to.get_coordinates()]


    def plot_profiles(self, time_series=None, my_index=0, show_fig=True):
        """
        Plot the time series results of this object
        :param time_series: TimeSeries Instance
        :param my_index: index of this object in the simulation
        :param show_fig: Show the figure?
        """

        if time_series is not None:
            fig = plt.figure(figsize=(12, 8))

            ax_1 = fig.add_subplot(211)
            ax_2 = fig.add_subplot(212, sharex=ax_1)

            x = time_series.results.time_array

            # loading
            y = time_series.results.loading.real * 100.0
            df = pd.DataFrame(data=y[:, my_index], index=x, columns=[self.name])
            ax_1.set_title('Loading', fontsize=14)
            ax_1.set_ylabel('Loading [%]', fontsize=11)
            df.plot(ax=ax_1)

            # losses
            y = np.abs(time_series.results.losses)
            df = pd.DataFrame(data=y[:, my_index], index=x, columns=[self.name])
            ax_2.set_title('Losses', fontsize=14)
            ax_2.set_ylabel('Losses [MVA]', fontsize=11)
            df.plot(ax=ax_2)

            plt.legend()
            fig.suptitle(self.name, fontsize=20)

        if show_fig:
            plt.show()

    def is_3term(self):
        """
        Is this a 3-terminal VSC?
        """
        return self.bus_from is not None and self.bus_to is not None and self._bus_dc_n is not None

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def alpha1(self) -> float:
        """
        Get ``alpha1``.

        :return: float
        """
        return self._alpha1

    @alpha1.setter
    def alpha1(self, val: float) -> None:
        """
        Set ``alpha1``.

        :param val: Value to assign.
        :return: None
        """
        self._alpha1 = float(val)

    @property
    def alpha2(self) -> float:
        """
        Get ``alpha2``.

        :return: float
        """
        return self._alpha2

    @alpha2.setter
    def alpha2(self, val: float) -> None:
        """
        Set ``alpha2``.

        :param val: Value to assign.
        :return: None
        """
        self._alpha2 = float(val)

    @property
    def alpha3(self) -> float:
        """
        Get ``alpha3``.

        :return: float
        """
        return self._alpha3

    @alpha3.setter
    def alpha3(self, val: float) -> None:
        """
        Set ``alpha3``.

        :param val: Value to assign.
        :return: None
        """
        self._alpha3 = float(val)

    @property
    def min_ac_voltage(self) -> float:
        """
        Get ``min_ac_voltage``.

        :return: float
        """
        return self._min_ac_voltage

    @min_ac_voltage.setter
    def min_ac_voltage(self, val: float) -> None:
        """
        Set ``min_ac_voltage``.

        :param val: Value to assign.
        :return: None
        """
        self._min_ac_voltage = float(val)

    @property
    def ysvs(self) -> float:
        """
        Get ``ysvs``.

        :return: float
        """
        return self._ysvs

    @ysvs.setter
    def ysvs(self, val: float) -> None:
        """
        Set ``ysvs``.

        :param val: Value to assign.
        :return: None
        """
        self._ysvs = float(val)

    @property
    def x(self) -> float:
        """
        Get ``x``.

        :return: float
        """
        return self._x

    @x.setter
    def x(self, val: float) -> None:
        """
        Set ``x``.

        :param val: Value to assign.
        :return: None
        """
        self._x = float(val)

    @property
    def y(self) -> float:
        """
        Get ``y``.

        :return: float
        """
        return self._y

    @y.setter
    def y(self, val: float) -> None:
        """
        Set ``y``.

        :param val: Value to assign.
        :return: None
        """
        self._y = float(val)
