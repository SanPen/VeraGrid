# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from enum import Enum
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, PrpCat
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Branches.tap_changer import TapChanger
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Profiles import ProfileFloat

from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp

# Global sqrt of 3 (bad practice?)
SQRT3 = np.sqrt(3.0)


"""
NOTE: This device is legacy and unsupported
      It only exists because older VeraGrid versions used it
      Now when this devices is used it is immediately converted 
      to either a line or transformer
"""


class BranchType(Enum):
    Branch = 'branch'
    Line = 'line'
    DCLine = 'DC-line'
    VSC = 'VSC'
    UPFC = 'UPFC'
    Transformer = 'transformer'
    Reactance = 'reactance'
    Switch = 'switch'
    Winding = 'Winding'
    BranchTemplate = 'BranchTemplate'

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return BranchType[s]
        except KeyError:
            return s

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Branch(BranchParent):
    __slots__ = (
        'measurements',
        '_length',
        '_tolerance',
        '_r_fault',
        '_x_fault',
        '_fault_pos',
        '_R',
        '_X',
        '_B',
        '_G',
        'tap_changer',
        '_tap_module',
        '_angle',
        'branch_type',
        'template',
        '_bus_to_regulated',
        '_vset',
        'conv',
        'inv_conv',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='R',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence resistance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='X',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence reactance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='B',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence shunt susceptance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='G',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence shunt conductance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='tolerance',
            units='%',
            tpe=float,
            definition='Tolerance expected for the impedance values % is expected for '
                                 'transformers0% for lines.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='length',
            units='km',
            tpe=float,
            definition='Length of the line (not used for calculation)',
        ),
        GCProp(
            prop_name='tap_module',
            units='',
            tpe=float,
            definition='Tap changer module, it a value close to 1.0',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='angle',
            units='rad',
            tpe=float,
            definition='Angle shift of the tap changer.',
            cat=[PrpCat.PF],
        ),
        # GCProp(
        #     prop_name='template',
        #     units='',
        #     tpe=BranchType,
        #     definition='',
        #     editable=False,
        #     cat=[PrpCat.PF],
        # ),
        GCProp(
            prop_name='bus_to_regulated',
            units='',
            tpe=bool,
            definition='Is the regulation at the bus to?',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='vset',
            units='p.u.',
            tpe=float,
            definition='set control voltage.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='r_fault',
            units='p.u.',
            tpe=float,
            definition='Fault resistance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='x_fault',
            units='p.u.',
            tpe=float,
            definition='Fault reactance.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='fault_pos',
            units='p.u.',
            tpe=float,
            definition='proportion of the fault location measured from the "from" bus.',
            cat=[PrpCat.PF],
        ),
        # GCProp(
        #     prop_name='branch_type',
        #     units='p.u.',
        #     tpe=DeviceType,
        #     definition='Fault resistance.',
        #     cat=[PrpCat.PF],
        # ),
    )

    def __init__(self,
                 bus_from: Bus = None,
                 bus_to: Bus = None,
                 name='Branch',
                 idtag=None,
                 r=1e-20, x=1e-20, g=1e-20, b=1e-20,
                 rate=1.0,
                 tap=1.0,
                 shift_angle=0,
                 active=True,
                 tolerance=0.0,
                 cost=0.0,
                 mttf=0, mttr=0,
                 r_fault=0.0, x_fault=0.0, fault_pos=0.5,
                 branch_type: BranchType = BranchType.Line,
                 length=1.0,
                 vset=1.0,
                 temp_base=20,
                 temp_oper=20,
                 alpha=0.00330,
                 bus_to_regulated=False,
                 template=None):
        """
        This class exists for legacy reasons, use the Line or Transformer2w classes instead! *
        The **Branch** class represents the connections between nodes (i.e.
        :ref:`buses<bus>`) in **VeraGrid**. A branch is an element (cable, line, capacitor,
        transformer, etc.) with an electrical impedance. The basic **Branch** class
        includes basic electrical attributes for most passive elements, but other device
        types may be passed to the **Branch** constructor to configure it as a specific
        type.
        :param bus_from: "From" :ref:`bus<Bus>` object
        :param bus_to: "To" :ref:`bus<Bus>` object
        :param name: Name of the branch
        :param idtag: UUID code
        :param r: Branch resistance in per unit
        :param x: Branch reactance in per unit
        :param g: Branch shunt conductance in per unit
        :param b: Branch shunt susceptance in per unit
        :param rate: Branch rate in MVA
        :param tap: Branch tap module
        :param shift_angle: Tap shift angle in radians
        :param active: Is the branch active?
        :param tolerance: Tolerance specified for the branch impedance in %
        :param cost:
        :param mttf: Mean time to failure in hours
        :param mttr: Mean time to recovery in hours
        :param r_fault: Mid-line fault resistance in per unit (SC only)
        :param x_fault: Mid-line fault reactance in per unit (SC only)
        :param fault_pos: Mid-line fault position in per unit (0.0 = `bus_from`, 0.5 = middle, 1.0 = `bus_to`)
        :param branch_type: Device type enumeration (ex.: :class:`VeraGridEngine.Devices.transformer.TransformerType`)
        :param length: Length of the branch in km
        :param vset: Voltage set-point of the voltage controlled bus in per-unit
        :param temp_base: Base temperature at which `r` is measured in °C
        :param temp_oper: Operating temperature in °C
        :param alpha: Thermal constant of the material in °C
        :param bus_to_regulated:  Is the `bus_to` voltage regulated by this branch?
        :param template: Basic branch template
        """
        BranchParent.__init__(self,
                              name=name,
                              idtag=idtag,
                              code="",
                              bus_from=bus_from,
                              bus_to=bus_to,
                              active=active,
                              reducible=False,
                              rate=rate,
                              contingency_factor=1.0,
                              protection_rating_factor=1.4,
                              contingency_enabled=True,
                              monitor_loading=True,
                              mttf=mttf,
                              mttr=mttr,
                              build_status=BuildStatus.Commissioned,
                              capex=0.0,
                              opex=0.0,
                              cost=cost,
                              temp_base=25,
                              temp_oper=25,
                              alpha=0.0033,
                              device_type=DeviceType.BranchDevice)

        # List of measurements
        self.measurements = list()

        # line length in km
        self.length = length

        # branch impedance tolerance
        self.tolerance = tolerance

        # short circuit impedance
        self.r_fault = r_fault
        self.x_fault = x_fault
        self.fault_pos = fault_pos

        # total impedance and admittance in p.u.
        self.R = r
        self.X = x
        self.G = g
        self.B = b

        # Conductor base and operating temperatures in ºC
        self.temp_base = temp_base
        self.temp_oper = temp_oper
        self._temp_oper_prof = ProfileFloat(default_value=temp_oper)

        # Conductor thermal constant (1/ºC)
        self.alpha = alpha

        # tap changer object
        self.tap_changer = TapChanger()

        # Tap module
        if tap != 0:
            self.tap_module = tap
            self.tap_changer.set_tap_module(self.tap_module)
        else:
            self.tap_module = self.tap_changer.get_tap_module()

        # Tap angle
        self.angle = shift_angle

        # branch rating in MVA
        self.rate = rate
        self._rate_prof = ProfileFloat(default_value=rate)

        # branch type: Line, Transformer, etc...
        self.branch_type = branch_type

        # type template
        self.template = template
        self.bus_to_regulated = bus_to_regulated
        self.vset = vset

        # converter for enumerations
        self.conv = {'branch': BranchType.Branch,
                     'line': BranchType.Line,
                     'transformer': BranchType.Transformer,
                     'switch': BranchType.Switch,
                     'reactance': BranchType.Reactance}

        self.inv_conv = {val: key for key, val in self.conv.items()}





    @property
    def rate_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._rate_prof

    @rate_prof.setter
    def rate_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._rate_prof = val
        elif isinstance(val, np.ndarray):
            self._rate_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a rate_prof')

    @property
    def temp_oper_prof(self) -> ProfileFloat:
        """
        Cost profile
        :return: Profile
        """
        return self._temp_oper_prof

    @temp_oper_prof.setter
    def temp_oper_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._temp_oper_prof = val
        elif isinstance(val, np.ndarray):
            self._temp_oper_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a temp_oper_prof')

    @property
    def R_corrected(self):
        """
        Returns a temperature corrected resistance based on a formula provided by:
        NFPA 70-2005, National Electrical Code, Table 8, footnote #2; and
        https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity#Linear_approximation
        (version of 2019-01-03 at 15:20 EST).
        """
        return self.R * (1 + self.alpha * (self.temp_oper - self.temp_base))

    def get_weight(self):
        return np.sqrt(self.R * self.R + self.X * self.X)

    def branch_type_converter(self, val_string):
        """
        function to convert the branch type string into the BranchType
        :param val_string:
        :return: branch type conversion
        """
        return self.conv[val_string.lower()]

    def copy(self, bus_dict=None):
        """
        Returns a copy of the branch
        @return: A new  with the same content as this
        """

        if bus_dict is None:
            f = self.bus_from
            t = self.bus_to
        else:
            f = bus_dict[self.bus_from]
            t = bus_dict[self.bus_to]

        # z_series = complex(self.R, self.X)
        # y_shunt = complex(self.G, self.B)
        b = Branch(bus_from=f,
                   bus_to=t,
                   name=self.name,
                   r=self.R,
                   x=self.X,
                   g=self.G,
                   b=self.B,
                   rate=self.rate,
                   tap=self.tap_module,
                   shift_angle=self.angle,
                   active=self.active,
                   mttf=self.mttf,
                   mttr=self.mttr,
                   bus_to_regulated=self.bus_to_regulated,
                   vset=self.vset,
                   temp_base=self.temp_base,
                   temp_oper=self.temp_oper,
                   alpha=self.alpha,
                   branch_type=self.branch_type,
                   template=self.template)

        b.measurements = self.measurements

        b.active_prof = self.active_prof

        return b

    def tap_up(self):
        """
        Move the tap changer one position up
        """
        self.tap_changer.tap_up()
        self.tap_module = self.tap_changer.get_tap_module()

    def tap_down(self):
        """
        Move the tap changer one position up
        """
        self.tap_changer.tap_down()
        self.tap_module = self.tap_changer.get_tap_module()

    def apply_tap_changer(self, tap_changer: TapChanger):
        """
        Apply a new tap changer

        Argument:

            **tap_changer** (:class:`VeraGridEngine.Devices.branch.TapChanger`): Tap changer object

        """
        self.tap_changer = tap_changer

        if self.tap_module != 0:
            self.tap_changer.set_tap_module(self.tap_module)
        else:
            self.tap_module = self.tap_changer.get_tap_module()

    def get_save_data(self):
        """
        Return the data that matches the edit_headers
        :return:
        """
        data = list()
        for name, properties in self.registered_properties.items():
            obj = getattr(self, name)

            if properties.tpe == BranchType:
                obj = self.branch_type.value

            elif properties.tpe not in [str, float, int, bool]:
                obj = str(obj)

            data.append(obj)
        return data

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
            y = time_series.results.loading * 100.0
            df = pd.DataFrame(data=y[:, my_index], index=x, columns=[self.name])
            ax_1.set_title('Loading', fontsize=14)
            ax_1.set_ylabel('Loading [%]', fontsize=11)
            df.plot(ax=ax_1)

            # losses
            y = time_series.results.losses
            df = pd.DataFrame(data=y[:, my_index], index=x, columns=[self.name])
            ax_2.set_title('Losses', fontsize=14)
            ax_2.set_ylabel('Losses [MVA]', fontsize=11)
            df.plot(ax=ax_2)

            plt.legend()
            fig.suptitle(self.name, fontsize=20)

        if show_fig:
            plt.show()

    def get_coordinates(self):
        """
        Get the branch defining coordinates
        """
        return [self.bus_from.get_coordinates(), self.bus_to.get_coordinates()]

    def get_equivalent_transformer(self, index: pd.DatetimeIndex | None = None) -> Transformer2W:
        """
        Convert this line into a transformer
        This is necessary if the buses' voltage differ too much
        :return: Transformer2W
        """
        V1 = min(self.bus_to.Vnom, self.bus_from.Vnom)
        V2 = max(self.bus_to.Vnom, self.bus_from.Vnom)
        elm = Transformer2W(bus_from=self.bus_from,
                            bus_to=self.bus_to,
                            name=self.name,
                            r=self.R,
                            x=self.X,
                            b=self.B,
                            rate=self.rate,
                            active=self.active,
                            tolerance=self.tolerance,
                            HV=V2, LV=V1,
                            cost=self.Cost,
                            mttf=self.mttf,
                            mttr=self.mttr,
                            tap_module=self.tap_module,
                            tap_phase=self.angle,
                            vset=self.vset,
                            temp_base=self.temp_base,
                            temp_oper=self.temp_oper,
                            alpha=self.alpha,
                            template=self.template)

        if index is not None:
            elm.ensure_profiles_exist(index=index)
            elm.active_prof = self.active_prof
            elm.rate_prof = self.rate_prof
            elm.contingency_factor_prof = self.contingency_factor_prof
            elm.protection_rating_factor_prof = self.protection_rating_factor_prof
            elm.temp_oper_prof = self.temp_oper_prof
            elm.Cost_prof = self.Cost_prof

        return elm

    def get_equivalent_line(self, index: pd.DatetimeIndex | None = None) -> Line:
        """
        Get the equivalent line object
        :return:
        """
        elm = Line(bus_from=self.bus_from,
                   bus_to=self.bus_to,
                   name=self.name,
                   r=self.R,
                   x=self.X,
                   b=self.B,
                   rate=self.rate,
                   active=self.active,
                   tolerance=self.tolerance,
                   cost=self.Cost,
                   mttf=self.mttf,
                   mttr=self.mttr,
                   r_fault=self.r_fault,
                   x_fault=self.x_fault,
                   fault_pos=self.fault_pos,
                   length=self.length,
                   temp_base=self.temp_base,
                   temp_oper=self.temp_oper,
                   alpha=self.alpha)

        if index is not None:
            elm.ensure_profiles_exist(index=index)
            elm.active_prof = self.active_prof
            elm.rate_prof = self.rate_prof
            elm.contingency_factor_prof = self.contingency_factor_prof
            elm.protection_rating_factor_prof = self.protection_rating_factor_prof
            elm.temp_oper_prof = self.temp_oper_prof
            elm.Cost_prof = self.Cost_prof

        return elm

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
    def length(self) -> float:
        """
        Get ``length``.

        :return: float
        """
        return self._length

    @length.setter
    def length(self, val: float) -> None:
        """
        Set ``length``.

        :param val: Value to assign.
        :return: None
        """
        self._length = float(val)

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
    def angle(self) -> float:
        """
        Get ``angle``.

        :return: float
        """
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        """
        Set ``angle``.

        :param val: Value to assign.
        :return: None
        """
        self._angle = float(val)

    @property
    def bus_to_regulated(self) -> bool:
        """
        Get ``bus_to_regulated``.

        :return: bool
        """
        return self._bus_to_regulated

    @bus_to_regulated.setter
    def bus_to_regulated(self, val: bool) -> None:
        """
        Set ``bus_to_regulated``.

        :param val: Value to assign.
        :return: None
        """
        self._bus_to_regulated = bool(val)

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
    def r_fault(self) -> float:
        """
        Get ``r_fault``.

        :return: float
        """
        return self._r_fault

    @r_fault.setter
    def r_fault(self, val: float) -> None:
        """
        Set ``r_fault``.

        :param val: Value to assign.
        :return: None
        """
        self._r_fault = float(val)

    @property
    def x_fault(self) -> float:
        """
        Get ``x_fault``.

        :return: float
        """
        return self._x_fault

    @x_fault.setter
    def x_fault(self, val: float) -> None:
        """
        Set ``x_fault``.

        :param val: Value to assign.
        :return: None
        """
        self._x_fault = float(val)

    @property
    def fault_pos(self) -> float:
        """
        Get ``fault_pos``.

        :return: float
        """
        return self._fault_pos

    @fault_pos.setter
    def fault_pos(self, val: float) -> None:
        """
        Set ``fault_pos``.

        :param val: Value to assign.
        :return: None
        """
        self._fault_pos = float(val)


def convert_branch(branch: Branch):
    """

    :param branch:
    :return:
    """
    if branch.branch_type == BranchType.Line:

        elm = Line(bus_from=branch.bus_from,
                   bus_to=branch.bus_to,
                   name=branch.name,
                   r=branch.R,
                   x=branch.X,
                   b=branch.B,
                   rate=branch.rate,
                   active=branch.active,
                   tolerance=branch.tolerance,
                   cost=branch.Cost,
                   mttf=branch.mttf,
                   mttr=branch.mttr,
                   r_fault=branch.r_fault,
                   x_fault=branch.x_fault,
                   fault_pos=branch.fault_pos,
                   length=branch.length,
                   temp_base=branch.temp_base,
                   temp_oper=branch.temp_oper,
                   alpha=branch.alpha)

        elm.rate_prof = branch.rate_prof
        elm.Cost_prof = branch.Cost_prof
        elm.active_prof = branch.active_prof
        elm.temp_oper_prof = branch.temp_oper_prof

        return elm

    elif branch.branch_type == BranchType.Transformer:

        elm = Transformer2W(bus_from=branch.bus_from,
                            bus_to=branch.bus_to,
                            name=branch.name,
                            r=branch.R,
                            x=branch.X,
                            b=branch.B,
                            rate=branch.rate,
                            active=branch.active,
                            tolerance=branch.tolerance,
                            cost=branch.Cost,
                            mttf=branch.mttf,
                            mttr=branch.mttr,
                            tap_module=branch.tap_module,
                            tap_phase=branch.angle,
                            vset=branch.vset,
                            temp_base=branch.temp_base,
                            temp_oper=branch.temp_oper,
                            alpha=branch.alpha,
                            template=branch.template)

        elm.rate_prof = branch.rate_prof
        elm.Cost_prof = branch.Cost_prof
        elm.active_prof = branch.active_prof
        elm.temp_oper_prof = branch.temp_oper_prof

        return elm

    else:
        return branch
