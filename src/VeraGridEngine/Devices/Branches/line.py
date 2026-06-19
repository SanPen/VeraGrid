# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import Union, Tuple
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import (BuildStatus, SubObjectType, DeviceType, PrpCat,
                                         ParamPowerFlowReferenceType)
from VeraGridEngine.Devices.Branches.underground_line_type import UndergroundLineType
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Branches.sequence_line_type import SequenceLineType, get_line_impedances_with_c
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Associations.association import Associations
from VeraGridEngine.Devices.Branches.line_locations import LineLocations
from VeraGridEngine.Devices.admittance_matrix import AdmittanceMatrix
from VeraGridEngine.Devices.Parents.editable_device import GCProp


def accept_line_connection(V1: float, V2: float, branch_connection_voltage_tolerance=0.1) -> float:
    """
    This function checks if a line can be connected between 2 voltages
    :param V1: Voltage 1
    :param V2: Voltage 2
    :param branch_connection_voltage_tolerance:
    :return: Can be connected?
    """
    if V2 > 0:
        per = V1 / V2

        if per < (1.0 - branch_connection_voltage_tolerance):
            return False
        else:
            return True
    else:
        return V1 == V2


class Line(BranchParent):
    __slots__ = (
        '_length',
        '_tolerance',
        '_r_fault',
        '_x_fault',
        '_fault_pos',
        '_R',
        '_X',
        '_B',
        '_R0',
        '_X0',
        '_B0',
        '_R2',
        '_X2',
        '_B2',
        '_ys',
        '_ysh',
        'temp_base',
        'temp_oper',
        '_temp_oper_prof',
        'alpha',
        '_circuit_idx',
        'template',
        'possible_tower_types',
        'possible_underground_line_types',
        'possible_sequence_line_types',
        '_locations',
        'Vmf',
        'Vmt',
        'Vaf',
        'Vat',
        'Pf',
        'Pt',
        'Qf',
        'Qt',
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
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='B',
            units='p.u.',
            tpe=float,
            definition='Total positive sequence shunt susceptance.',
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
            prop_name='B0',
            units='p.u.',
            tpe=float,
            definition='Total zero sequence shunt susceptance.',
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
            prop_name='B2',
            units='p.u.',
            tpe=float,
            definition='Total negative sequence shunt susceptance.',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='ys',
            units="p.u.",
            tpe=SubObjectType.AdmittanceMatrix,
            definition='Series admittance matrix of the branch',
            editable=False,
            display=False,
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='ysh',
            units="p.u.",
            tpe=SubObjectType.AdmittanceMatrix,
            definition='Shunt admittance matrix of the branch',
            editable=False,
            display=False,
            cat=[PrpCat.PF3],
        ),
        GCProp(
            prop_name='tolerance',
            units='%',
            tpe=float,
            definition='Tolerance expected for the impedance values % is expected '
                          'for transformers0% for lines.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='circuit_idx',
            units='',
            tpe=int,
            definition='Circuit index, used for multiple circuits sharing towers (starts at zero)',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='length',
            units='km',
            tpe=float,
            definition='Length of the line (not used for calculation)',
            cat=[PrpCat.TP],
            dyn_ref=ParamPowerFlowReferenceType.line_length_km,
        ),
        GCProp(
            prop_name='template',
            units='',
            tpe=DeviceType.AnyLineTemplateDevice,
            definition='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='locations',
            units='',
            tpe=SubObjectType.LineLocations,
            definition='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='possible_tower_types',
            units='',
            tpe=SubObjectType.Associations,
            definition='Possible overhead line types (>1 to denote association, cat=[PrpCat.PF]), - to denote no association',
            display=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='possible_underground_line_types',
            units='',
            tpe=SubObjectType.Associations,
            definition='Possible underground line types (>1 to denote association, cat=[PrpCat.PF]), '
                          '- to denote no association',
            display=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='possible_sequence_line_types',
            units='',
            tpe=SubObjectType.Associations,
            definition='Possible sequence line types (>1 to denote association, cat=[PrpCat.PF]), - to denote no association',
            display=False,
            cat=[PrpCat.TP],
        ),

    )

    def __init__(self,
                 bus_from: Bus = None,
                 bus_to: Bus = None,
                 name='Line',
                 idtag=None,
                 code='',
                 r=1e-20, x=0.00001, b=1e-20,
                 design_rate: float = 9999.0,
                 rate=9999.0,
                 active=True,
                 tolerance=0.0,
                 cost=100.0,
                 mttf=0.0,
                 mttr=0,
                 r_fault=0.0,
                 x_fault=0.0,
                 fault_pos=0.5,
                 length=1.0,
                 temp_base=20,
                 temp_oper=20,
                 alpha=0.00330,
                 template=None,
                 contingency_factor=1.0,
                 protection_rating_factor: float = 1.4,
                 contingency_enabled=True,
                 monitor_loading=True,
                 r0=1e-20, x0=1e-20, b0=1e-20,
                 r2=1e-20, x2=1e-20, b2=1e-20,
                 capex=0,
                 opex=0,
                 circuit_idx: int = 1,
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
        :param b: Branch shunt susceptance in per unit
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
        :param length: Length of the branch in km
        :param temp_base: Base temperature at which `r` is measured in °C
        :param temp_oper: Operating temperature in °C
        :param alpha: Thermal constant of the material in °C
        :param template: Basic branch template
        :param contingency_factor: Rating factor in case of contingency
        :param protection_rating_factor: Rating factor before the protections tripping
        :param contingency_enabled: enabled for contingencies (Legacy)
        :param monitor_loading: monitor the loading (used in OPF)
        :param r0: zero-sequence resistence (p.u.)
        :param x0: zero-sequence reactance (p.u.)
        :param b0: zero-sequence susceptance (p.u.)
        :param r2: negative-sequence resistence (p.u.)
        :param x2: negative-sequence reactance (p.u.)
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
                              device_type=DeviceType.LineDevice)

        # line length in km
        self._length = float(length)

        # line impedance tolerance
        self.tolerance = float(tolerance)

        # short circuit impedance
        self.r_fault = float(r_fault)
        self.x_fault = float(x_fault)
        self.fault_pos = float(fault_pos)

        # total impedance and admittance in p.u.
        self._R = float(r)
        self._X = float(x)
        self._B = float(b)

        self._R0 = float(r0)
        self._X0 = float(x0)
        self._B0 = float(b0)

        self._R2 = float(r2)
        self._X2 = float(x2)
        self._B2 = float(b2)

        self._ys = AdmittanceMatrix()
        self._ysh = AdmittanceMatrix()

        self._circuit_idx: int = int(circuit_idx)

        # type template
        self.template: OverheadLineType | SequenceLineType | UndergroundLineType | None = template

        # association with various templates
        self.possible_tower_types: Associations = Associations(device_type=DeviceType.OverheadLineTypeDevice)
        self.possible_underground_line_types: Associations = Associations(device_type=DeviceType.UnderGroundLineDevice)
        self.possible_sequence_line_types: Associations = Associations(device_type=DeviceType.SequenceLineDevice)

        # Line locations
        self._locations: LineLocations = LineLocations()

    @property
    def R(self):
        return self._R

    @R.setter
    def R(self, value):
        self._R = float(value)

    @property
    def X(self):
        return self._X

    @X.setter
    def X(self, value):
        self._X = float(value)

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, value):
        self._B = float(value)

    @property
    def R0(self):
        return self._R0

    @R0.setter
    def R0(self, value):
        self._R0 = float(value)

    @property
    def X0(self):
        return self._X0

    @X0.setter
    def X0(self, value):
        self._X0 = float(value)

    @property
    def B0(self):
        return self._B0

    @B0.setter
    def B0(self, value):
        self._B0 = float(value)

    @property
    def R2(self):
        return self._R2

    @R2.setter
    def R2(self, value):
        self._R2 = float(value)

    @property
    def X2(self):
        return self._X2

    @X2.setter
    def X2(self, value):
        self._X2 = float(value)

    @property
    def B2(self):
        return self._B2

    @B2.setter
    def B2(self, value):
        self._B2 = float(value)

    @property
    def circuit_idx(self):
        """

        :return:
        """
        return self._circuit_idx

    @circuit_idx.setter
    def circuit_idx(self, value):
        value = int(value)
        if value > 0:
            self._circuit_idx = int(value)

            if self.auto_update_enabled:
                print("No impedance updates are being done, "
                      "use the apply_template method to update the impedance values")

    def set_circuit_idx(self, val: int, obj: Union[OverheadLineType, UndergroundLineType, SequenceLineType]):
        """
        Set the circuit_idx with additional behavior based on the is_user_action flag. Ensure that the template exists and is valid.
        :param val: The value to set
        :param obj: Template
        """
        # If the user is setting the circuit index, ensure that the template exists and is valid
        if obj is None:
            raise ValueError("Template must be set before changing the circuit index.")

        if not isinstance(obj, (OverheadLineType, UndergroundLineType, SequenceLineType)):
            raise ValueError(
                "Invalid template type. Must be OverheadLineType, UndergroundLineType, or SequenceLineType."
            )

        if isinstance(obj, OverheadLineType):
            if val > obj.n_circuits:
                raise ValueError("Circuit index exceeds the number of circuits in the template.")

        if val <= 0:
            raise ValueError("Circuit index must be greater than 0.")
        else:
            if val > 0:
                self._circuit_idx = int(val)

    @property
    def length(self) -> float:
        """
        Line length in km
        :return: float
        """
        return self._length

    @length.setter
    def length(self, val: float):
        """
        Set the length of the line, if a valid length is provided, the electric parameters are scaled appropriately
        :param val:
        :return:
        """
        val = float(val)
        self.set_length(val)

    def set_length(self, val: float):
        """
        Set the line length and change the electric parameters of the line as a consequence.
        :param val: value in km
        """
        if isinstance(val, float):
            if val > 0.0:
                if self._length != 0 and self.auto_update_enabled:
                    factor = np.round(val / self._length, 6)  # new length / old length

                    self.R *= factor
                    self.X *= factor
                    self.B *= factor
                    self.R0 *= factor
                    self.X0 *= factor
                    self.B0 *= factor
                    self.R2 *= factor
                    self.X2 *= factor
                    self.B2 *= factor

                # set the value
                self._length = val
            else:
                # print('The length cannot be zero, ignoring value')
                pass
        else:
            raise Exception('The length must be a float value')

    @property
    def locations(self) -> LineLocations:
        """
        Cost profile
        :return: Profile
        """
        return self._locations

    @locations.setter
    def locations(self, val: Union[LineLocations, np.ndarray]):
        if isinstance(val, LineLocations):
            self._locations = val
        elif isinstance(val, np.ndarray):
            self._locations.set(data=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a locations')

    @property
    def R_corrected(self):
        """
        Returns a temperature corrected resistance based on a formula provided by:
        NFPA 70-2005, National Electrical Code, Table 8, footnote #2; and
        https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity#Linear_approximation
        (version of 2019-01-03 at 15:20 EST).
        """
        return self.R * (1 + self.alpha * (self.temp_oper - self.temp_base))

    @property
    def ys(self) -> AdmittanceMatrix:
        """

        :return:
        """
        if self._ys.size <= 0 and self.auto_update_enabled:
            self.fill_3_phase_from_sequence()

        return self._ys

    @ys.setter
    def ys(self, val: AdmittanceMatrix):
        if isinstance(val, AdmittanceMatrix):
            self._ys = val
        else:
            raise ValueError(f'{val} is not a AdmittanceMatrix')

    @property
    def ysh(self) -> AdmittanceMatrix:
        """

        :return:
        """
        if self._ysh.size <= 0 and self.auto_update_enabled:
            self.fill_3_phase_from_sequence()

        return self._ysh

    @ysh.setter
    def ysh(self, val: AdmittanceMatrix):
        if isinstance(val, AdmittanceMatrix):
            self._ysh = val
        else:
            raise ValueError(f'{val} is not a AdmittanceMatrix')

    def change_base(self, Sbase_old: float, Sbase_new: float):
        """
        Change the impedance base
        :param Sbase_old: old base (MVA)
        :param Sbase_new: new base (MVA)
        """
        b = Sbase_new / Sbase_old

        self.R *= b
        self.X *= b
        self.B *= b

    def get_weight(self) -> float:
        """
        Get a weight of this line for graph purposes
        the weight is the impedance module (sqrt(r^2 + x^2))
        :return: weight value
        """
        return np.sqrt(self.R * self.R + self.X * self.X)

    def apply_template(self,
                       obj: Union[OverheadLineType, UndergroundLineType, SequenceLineType],
                       Sbase: float, freq: float,
                       logger=Logger(),
                       decimals_rounding: int = 6):
        """
        Apply a line template to this object
        :param obj: OverheadLineType, UndergroundLineType, SequenceLineType
        :param Sbase: Nominal power in MVA
        :param freq: Frequency in Hz
        :param logger: Logger
        :param decimals_rounding: Number of decimals to round to
        """

        if isinstance(obj, OverheadLineType):
            if not obj.is_computed():
                obj.compute()
                if not obj.is_computed():
                    logger.add_error("No admittance data", device=obj.name)
                    return
            else:
                pass

            template_vn = obj.Vnom
            vn = self.get_max_bus_nominal_voltage()

            if not accept_line_connection(template_vn, vn, 0.1):
                raise Exception('Template voltage differs too much from the line nominal voltage')

            if obj.has_sequence_data():
                (self.R, self.X, self.B,
                 self.R0, self.X0, self.B0,
                 self.rate) = obj.get_values(Sbase=Sbase,
                                             length=self.length,
                                             circuit_index=self.circuit_idx,
                                             Vnom=vn)
            else:
                logger.add_info("No sequence data", device=obj.name)

            self.ys = obj.get_ys(circuit_idx=self.circuit_idx, Sbase=Sbase, length=self.length, Vnom=vn)
            self.ysh = obj.get_ysh(circuit_idx=self.circuit_idx, Sbase=Sbase, length=self.length, Vnom=vn)

            self.template = obj
            self.rms_template = obj.rms_template
            self.emt_template = obj.emt_template

        elif isinstance(obj, UndergroundLineType):
            (self.R, self.X, self.B,
             self.R0, self.X0, self.B0,
             self.rate) = obj.get_values(Sbase=Sbase, length=self.length)

            self.template = obj
            self.rms_template = obj.rms_template
            self.emt_template = obj.emt_template

        elif isinstance(obj, SequenceLineType):
            (self.R, self.X, self.B,
             self.R0, self.X0, self.B0,
             self.rate) = obj.get_values(Sbase=Sbase,
                                         freq=freq,
                                         length=self.length,
                                         line_Vnom=self.get_max_bus_nominal_voltage(),
                                         decimals_rounding=decimals_rounding)

            self.ys = obj.get_ys_nabc()
            self.ysh = obj.get_ysh_nabc()

            self.template = obj
            self.rms_template = obj.rms_template
            self.emt_template = obj.emt_template

        else:
            logger.add_error('Template not recognised', self.name)

    def get_line_type(self) -> SequenceLineType:
        """
        Get the equivalent sequence line type of this line
        :return: SequenceLineType
        """
        if self.length == 0.0:
            raise Exception("Length must be greater than 0")

        return SequenceLineType(name=f"{self.name}_type",
                                Imax=1, Vnom=self.get_max_bus_nominal_voltage(),
                                R=self.R / self.length,
                                X=self.X / self.length,
                                B=self.B / self.length,
                                R0=self.R0 / self.length,
                                X0=self.X0 / self.length,
                                B0=self.B0 / self.length)

    # def get_save_data(self) -> List[str]:
    #     """
    #     Return the data that matches the edit_headers
    #     :return:
    #     """
    #     data = list()
    #     for name, properties in self.registered_properties.items():
    #         obj = getattr(self, name)
    #
    #         if obj is None:
    #             data.append("")
    #         else:
    #
    #             if hasattr(obj, 'idtag'):
    #                 obj = obj.idtag
    #             else:
    #                 if properties.tpe not in [str, float, int, bool]:
    #                     obj = str(obj)
    #                 else:
    #                     obj = str(obj)
    #
    #             data.append(obj)
    #     return data

    def fix_inconsistencies(self, logger: Logger) -> bool:
        """
        Fix the inconsistencies
        :param logger:
        :return: any error
        """
        errors = False

        if self.R < 0.0:
            logger.add_warning("Corrected transformer R<0", self.name, self.R, -self.R)
            self.R = -self.R
            errors = True

        return errors

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
                            idtag=self.idtag,
                            name=self.name,
                            code=self.code,
                            active=self.active,
                            rate=self.rate,
                            HV=V2,
                            LV=V1,
                            r=self.R,
                            x=self.X,
                            b=self.B
                            )
        elm.rms_model = self.rms_model

        if index is not None:
            elm.ensure_profiles_exist(index=index)
            elm.active_prof = self.active_prof
            elm.rate_prof = self.rate_prof
            elm.contingency_factor_prof = self.contingency_factor_prof
            elm.protection_rating_factor_prof = self.protection_rating_factor_prof
            elm.temp_oper_prof = self.temp_oper_prof
            elm.Cost_prof = self.Cost_prof

        return elm

    def fill_design_properties(self,
                               r_ohm: float,
                               x_ohm: float,
                               c_nf: float,
                               length: float,
                               Imax: float,
                               freq: float,
                               Sbase: float,
                               apply_to_profile: bool = True,
                               logger: Logger = Logger()) -> "Line":
        """
        Fill R, X, B from not-in-per-unit parameters
        :param r_ohm: Resistance per km in OHM/km
        :param x_ohm: Reactance per km in OHM/km
        :param c_nf: Capacitance per km in nF/km
        :param length: length in kn
        :param Imax: Maximum current in kA
        :param freq: System frequency in Hz
        :param Sbase: Base power in MVA (take always 100 MVA)
        :param apply_to_profile: modify the ratings profile if checked
        :param logger: Logger
        :return self pointer
        """
        Vnom = self.get_max_bus_nominal_voltage()

        if Vnom > 0:

            self.R, self.X, self.B, new_rate = get_line_impedances_with_c(r_ohm=r_ohm,
                                                                          x_ohm=x_ohm,
                                                                          c_nf=c_nf,
                                                                          length=length,
                                                                          Imax=Imax,
                                                                          freq=freq,
                                                                          Sbase=Sbase,
                                                                          Vnom=Vnom,
                                                                          logger=logger)

            old_rate = float(self.rate)

            self.rate = new_rate
            self._length = length

            if apply_to_profile:
                if old_rate != 0.0:
                    prof_old = self.rate_prof.toarray()
                    self.rate_prof.set(prof_old * new_rate / old_rate)
                else:
                    self.rate_prof.fill(new_rate)
        else:
            logger.add_error("Nominal voltage is zero", device_class="Line", device=self.name)

        return self

    def get_tau(self, w: float) -> float:
        """
        get EMT delay parameter (tau) in seconds
        :param w: 2 * pi * freq
        :return: tau value
        """
        if self.template is None:
            return 0.0
        else:
            # TODO: consider using line.ys and line.ysh instead
            # Physical Parameters from Carson's
            Z = self.template.z_nabc  # from Carson ohm/km
            Y = self.template.y_nabc  # from Carson ohm/km

            Z_phys_m = Z / 1e3  # ohm/m
            Y_phys_m = Y / 1e3  # S/m

            # line parameters / meter
            l_ = np.imag(Z_phys_m) / w  # H/m
            c_ = np.imag(Y_phys_m) / w  # F/m

            # v_wave and tau from the travelling wave are taken only from the diagonal components
            L_w = l_[0, 0]
            C_w = c_[0, 0]
            v_wave = 1 / np.sqrt(L_w * C_w)

            # line time delay (tau) (only relevant for Bergeron and JMartí)
            return self.length * 1e3 / v_wave  # s

    def fill_3_phase_from_sequence(self) -> None:
        """
        Fill the 3x3 from the sequence values
        """
        if self.R0 > 1e-10 and self.X0 > 1e-10:
            obj = SequenceLineType(R=self.R, R0=self.R0, X=self.X, X0=self.X0, B=self.B, B0=self.B0)
        else:
            obj = SequenceLineType(R=self.R, R0=2.0 * self.R, X=self.X, X0=2.0 * self.X, B=self.B * 1e6,
                                   B0=self.B * 1e6)
            obj = SequenceLineType(R=self.R, R0=self.R, X=self.X, X0=self.X, B=self.B * 1e6, B0=self.B * 1e6)
        self.ys = obj.get_ys_nabc()
        self.ysh = obj.get_ysh_nabc()

    # Scalar property accessors coerce assignments to the declared schema types.

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
