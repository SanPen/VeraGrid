# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from typing import Tuple
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BuildStatus, DeviceType, PrpCat
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.editable_device import GCProp


class SeriesReactance(BranchParent):
    __slots__ = (
        '_tolerance',
        '_r_fault',
        '_x_fault',
        '_fault_pos',
        '_R',
        '_X',
        '_R0',
        '_X0',
        '_R2',
        '_X2',
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
            prop_name='R0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence resistance.',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='X0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence reactance.',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='R2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence resistance.',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='X2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence reactance.',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='tolerance',
            units='%',
            tpe=float,
            definition='Tolerance expected for the impedance values % is expected '
                                 'for transformers0% for lines.',
            cat=[PrpCat.PF],
        ),
    )

    def __init__(self,
                 bus_from: Bus = None,
                 bus_to: Bus = None,
                 name='SeriesReactance',
                 idtag=None, code='',
                 r=1e-20, x=1e-5,
                 design_rate: float = 9999.0,
                 rate=9999.0,
                 active=True,
                 tolerance=0,
                 cost=100.0,
                 mttf=0, mttr=0,
                 r_fault=0.0,
                 x_fault=0.0,
                 fault_pos=0.5,
                 temp_base=20,
                 temp_oper=20,
                 alpha=0.00330,
                 contingency_factor=1.0,
                 protection_rating_factor: float = 1.4,
                 contingency_enabled=True,
                 monitor_loading=True,
                 r0=1e-20, x0=1e-20,
                 r2=1e-20, x2=1e-20,
                 capex=0,
                 opex=0,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """
        AC current Line
        :param bus_from: "From" :ref:`bus<Bus>` object
        :param bus_to: "To" :ref:`bus<Bus>` object
        :param name: Name of the branch
        :param idtag: UUID code
        :param code: secondary ID
        :param r: Branch resistance in per unit
        :param x: Branch reactance in per unit
        :param design_rate: Design rate (MVA)
        :param rate: Branch rate in MVA
        :param active: Is the branch active?
        :param tolerance: Tolerance specified for the branch impedance in %
        :param cost: overload cost
        :param mttf: Mean time to failure in hours
        :param mttr: Mean time to recovery in hours
        :param r_fault: Mid-line fault resistance in per unit (SC only)
        :param x_fault: Mid-line fault reactance in per unit (SC only)
        :param fault_pos: Mid-line fault position in per unit (0.0 = `bus_from`, 0.5 = middle, 1.0 = `bus_to`)
        :param temp_base: Base temperature at which `r` is measured in °C
        :param temp_oper: Operating temperature in °C
        :param alpha: Thermal constant of the material in °C
        :param contingency_factor: Rating factor in case of contingency
        :param protection_rating_factor: Rating factor before the protections tripping
        :param contingency_enabled: enabled for contingencies (Legacy)
        :param monitor_loading: monitor the loading (used in OPF)
        :param r0: zero-sequence resistence (p.u.)
        :param x0: zero-sequence reactance (p.u.)
        :param r2: negative-sequence resistence (p.u.)
        :param x2: negative-sequence reactance (p.u.)
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
                              reducible=False,
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
                              device_type=DeviceType.SeriesReactanceDevice)

        # line impedance tolerance
        self.tolerance = tolerance

        # short circuit impedance
        self.r_fault = r_fault
        self.x_fault = x_fault
        self.fault_pos = fault_pos

        # total impedance and admittance in p.u.
        self.R = r
        self.X = x

        self.R0 = r0
        self.X0 = x0

        self.R2 = r2
        self.X2 = x2

    @property
    def R_corrected(self):
        """
        Returns a temperature corrected resistance based on a formula provided by:
        NFPA 70-2005, National Electrical Code, Table 8, footnote #2; and
        https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity#Linear_approximation
        (version of 2019-01-03 at 15:20 EST).
        """
        return self.R * (1 + self.alpha * (self.temp_oper - self.temp_base))

    def change_base(self, Sbase_old, Sbase_new):
        """
        Change the impedance base
        :param Sbase_old: old base (MVA)
        :param Sbase_new: new base (MVA)
        """
        b = Sbase_new / Sbase_old

        self.R *= b
        self.X *= b

    def get_weight(self) -> float:
        """
        Get a weight of this line for graph purposes
        the weight is the impedance module (sqrt(r^2 + x^2))
        :return: weight value
        """
        return np.sqrt(self.R * self.R + self.X * self.X)

    def fix_inconsistencies(self, logger: Logger):
        """
        Fix the inconsistencies
        :param logger:
        :return:
        """
        errors = False

        if self.R < 0.0:
            logger.add_warning("Corrected transformer R<0", self.name, self.R, -self.R)
            self.R = -self.R
            errors = True

        return errors

    def fill_design_properties(self, r_ohm, x_ohm, length, Imax, Sbase):
        """
        Fill R, X, B from not-in-per-unit parameters
        :param r_ohm: Resistance per km in OHM
        :param x_ohm: Reactance per km in OHM
        :param length: length in kn
        :param Imax: Maximum current in kA
        :param Sbase: Base power in MVA (take always 100 MVA)
        """
        R = r_ohm * length
        X = x_ohm * length
        Vf = self.get_max_bus_nominal_voltage()

        Zbase = (Vf * Vf) / Sbase

        self.R = np.round(R / Zbase, 6)
        self.X = np.round(X / Zbase, 6)
        self.rate = np.round(Imax * Vf * 1.73205080757, 6)  # nominal power in MVA = kA * kV * sqrt(3)

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

