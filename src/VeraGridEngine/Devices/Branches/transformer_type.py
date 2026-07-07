# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple, Union
from numpy import sqrt
from VeraGridEngine.enumerations import TapChangerTypes, WindingType, PrpCat
from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Branches.tap_changer import TapChanger


class TransformerType(DynamicDevice):
    __slots__ = (
        '_HV',
        '_LV',
        '_Sn',
        '_Pcu',
        '_Pfe',
        '_I0',
        '_Vsc',
        'GR_hv1',
        'GX_hv1',
        '_tap_changer',
        'conn_hv',
        'conn_lv',
        '_vector_group_number',
        '_capex',
        '_opex',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='HV',
            units='kV',
            tpe=float,
            definition='Nominal voltage al the high voltage side',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='LV',
            units='kV',
            tpe=float,
            definition='Nominal voltage al the low voltage side',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='Sn',
            units='MVA',
            tpe=float,
            definition='Nominal power',
            old_names=['rating'],
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='Pcu',
            units='kW',
            tpe=float,
            definition='Copper losses',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='Pfe',
            units='kW',
            tpe=float,
            definition='Iron losses',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='I0',
            units='%',
            tpe=float,
            definition='No-load current',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='Vsc',
            units='%',
            tpe=float,
            definition='Short-circuit voltage',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='capex',
            units='currency',
            tpe=float,
            definition='Capital expenditure',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='opex',
            units='currency/MWh',
            tpe=float,
            definition='Operational expenditure',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='tc_type',
            units='',
            tpe=TapChangerTypes,
            definition='Regulation type',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='total_positions',
            units='',
            tpe=int,
            definition='Number of tap positions',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='dV',
            units='p.u.',
            tpe=float,
            definition='Voltage increment per step',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='neutral_position',
            units='',
            tpe=int,
            definition='neutral position counting from zero',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='asymmetry_angle',
            units='deg',
            tpe=float,
            definition='Asymmetry_angle',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='conn_hv',
            units='',
            tpe=WindingType,
            definition='Winding 3 phase connection at the from side',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='conn_lv',
            units='',
            tpe=WindingType,
            definition='Winding 3 phase connection at the to side',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='vector_group_number',
            units='',
            tpe=int,
            definition='Vector group number. It indicates the structural phase:'
                          'phase = vector_group_number · 30º',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='tap_module_min',
            units='p.u.',
            tpe=float,
            definition='Min tap module',
            editable=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_module_max',
            units='p.u.',
            tpe=float,
            definition='Max tap module',
            editable=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase_min',
            units='rad',
            tpe=float,
            definition='Min tap phase',
            editable=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
        GCProp(
            prop_name='tap_phase_max',
            units='rad',
            tpe=float,
            definition='Max tap phase',
            editable=False,
            cat=[PrpCat.PF, PrpCat.OPF],
        ),
    )

    def __init__(self,
                 hv_nominal_voltage: float = 0.0,
                 lv_nominal_voltage: float = 0.0,
                 nominal_power: float = 0.001,
                 copper_losses: float = 0.0,
                 iron_losses: float = 0.0,
                 no_load_current: float = 0.0,
                 short_circuit_voltage: float = 0.0,
                 gr_hv1: float = 0.5,
                 gx_hv1: float = 0.5,
                 total_positions: int = 5,
                 neutral_position: int = 2,
                 dV: float = 0.01,
                 asymmetry_angle: float = 90.0,
                 tc_type: TapChangerTypes = TapChangerTypes.NoRegulation,
                 name: str = 'TransformerType',
                 idtag: Union[None, str] = None,
                 capex: float = 0.0,
                 opex: float = 0.0,
                 vector_group_number: int = 0) -> None:
        """
        Transformer template from the short circuit study
        :param hv_nominal_voltage: Nominal voltage of the high voltage side in kV
        :param lv_nominal_voltage: Nominal voltage of the low voltage side in kV
        :param nominal_power: Nominal power of the machine in MVA
        :param copper_losses: Copper losses in kW
        :param iron_losses: Iron losses in kW
        :param no_load_current: No load current in %
        :param short_circuit_voltage: Short circuit voltage in %
        :param gr_hv1: proportion of the resistance in the HV side (i.e. 0.5)
        :param gx_hv1: proportion of the reactance in the HV side (i.e. 0.5)
        :param total_positions: Total number of positions
        :param neutral_position: Neutral position
        :param dV: per unit of voltage increment
        :param asymmetry_angle: Asymmetry angle (deg)
        :param tc_type: Tap changer type
        :param name: Name of the device template
        :param idtag: device UUID
        :param capex: Capital expenditures
        :param opex: Operating expenditures
        :param vector_group_number: Vector Group Number
        """
        DynamicDevice.__init__(self,
                               name=name,
                               idtag=idtag,
                               code='',
                               device_type=DeviceType.TransformerTypeDevice)

        self.HV = float(hv_nominal_voltage)

        self.LV = float(lv_nominal_voltage)

        self.Sn = float(nominal_power)

        self.Pcu = float(copper_losses)

        self.Pfe = float(iron_losses)

        self.I0 = float(no_load_current)

        self.Vsc = float(short_circuit_voltage)

        self.GR_hv1 = float(gr_hv1)

        self.GX_hv1 = float(gx_hv1)

        self.capex = float(capex)
        self.opex = float(opex)

        self.conn_hv: WindingType = WindingType.GroundedStar
        self.conn_lv: WindingType = WindingType.Delta
        self.vector_group_number: int = vector_group_number

        # The tap changer parameters are stored and used with the help of the TapChanger object
        self._tap_changer = TapChanger(total_positions=total_positions,
                                       neutral_position=neutral_position,
                                       dV=dV,
                                       asymmetry_angle=asymmetry_angle,
                                       tc_type=tc_type)

    @property
    def tap_module_min(self) -> float:
        """
        Min tap module, computed on the fly
        :return: float
        """
        return self._tap_changer.get_tap_module_min()

    @tap_module_min.setter
    def tap_module_min(self, val: float):
        val = float(val)
        # this is a read only property
        pass

    @property
    def tap_module_max(self) -> float:
        """
        Max tap module, computed on the fly
        :return: float
        """
        return self._tap_changer.get_tap_module_max()

    @tap_module_max.setter
    def tap_module_max(self, val: float):
        val = float(val)
        # this is a read only property
        pass

    @property
    def tap_phase_min(self) -> float:
        """
        Min tap phase, cputed on the fly
        :return: float
        """
        return self._tap_changer.get_tap_phase_min()

    @tap_phase_min.setter
    def tap_phase_min(self, val: float):
        val = float(val)
        # this is a read only property
        pass

    @property
    def tap_phase_max(self) -> float:
        """
        Maximum tap phase (calculated)
        :return: float
        """
        return self._tap_changer.get_tap_phase_max()

    @tap_phase_max.setter
    def tap_phase_max(self, val: float):
        val = float(val)
        # this is a read only property
        pass

    @property
    def total_positions(self) -> int:
        """
        Tap changer total number of positions
        :return: int
        """
        return self._tap_changer.total_positions

    @total_positions.setter
    def total_positions(self, value: int):
        value = int(value)
        if isinstance(value, int):
            self._tap_changer.total_positions = value
        else:
            raise TypeError(f'Expected int but got {type(value)}')

    @property
    def neutral_position(self) -> int:
        """
        Tap changer neutral position
        :return: int
        """
        return self._tap_changer.neutral_position

    @neutral_position.setter
    def neutral_position(self, value: int):
        value = int(value)
        if isinstance(value, int):
            if 0 <= value < self._tap_changer.total_positions:
                self._tap_changer.neutral_position = value
            else:
                pass
        else:
            raise TypeError(f'Expected int but got {type(value)}')

    @property
    def dV(self) -> float:
        """
        Tap changer Voltage increment per step (p.u.)
        :return: float
        """
        return self._tap_changer.dV

    @dV.setter
    def dV(self, value: float):
        value = float(value)
        if isinstance(value, float):
            self._tap_changer.dV = value
        else:
            raise TypeError(f'Expected int but got {type(value)}')

    @property
    def asymmetry_angle(self) -> float:
        """
        Tap changer assymetry angle (deg)
        :return: float
        """
        return self._tap_changer.asymmetry_angle

    @asymmetry_angle.setter
    def asymmetry_angle(self, value: float):
        value = float(value)
        if isinstance(value, float):
            self._tap_changer.asymmetry_angle = value
        else:
            raise TypeError(f'Expected float but got {type(value)}')

    @property
    def tc_type(self) -> TapChangerTypes:
        """
        Get the tap changer type
        :return: TapChangerTypes
        """
        return self._tap_changer.tc_type

    @tc_type.setter
    def tc_type(self, value: TapChangerTypes):
        if isinstance(value, TapChangerTypes):
            self._tap_changer.tc_type = value
        else:
            raise TypeError(f'Expected TapChangerTypes but got {type(value)}')

    def get_impedances(self, VH: float, VL: float, Sbase: float):
        """
        Compute the branch parameters of a transformer from the short circuit test
        values.
        :param VH: High voltage bus nominal voltage in kV
        :param VL: Low voltage bus nominal voltage in kV
        :param Sbase: Base power in MVA (normally 100 MVA)
        :return: Zseries and Yshunt in system per unit
        """

        z_series, y_shunt = get_impedances(VH_bus=VH,
                                           VL_bus=VL,
                                           Sn=self.Sn,
                                           HV=self.HV,
                                           LV=self.LV,
                                           Pcu=self.Pcu,
                                           Pfe=self.Pfe,
                                           I0=self.I0,
                                           Vsc=self.Vsc,
                                           Sbase=Sbase,
                                           GR_hv1=self.GR_hv1)

        return z_series, y_shunt

    def get_tap_changer(self) -> TapChanger:
        """
        Get tap changer object
        :return: TapChanger
        """
        return TapChanger(total_positions=self.total_positions,
                          neutral_position=self.neutral_position,
                          dV=self.dV,
                          asymmetry_angle=self.asymmetry_angle,
                          tc_type=self.tc_type)

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def HV(self) -> float:
        """
        Get ``HV``.

        :return: float
        """
        return self._HV

    @HV.setter
    def HV(self, val: float) -> None:
        """
        Set ``HV``.

        :param val: Value to assign.
        :return: None
        """
        self._HV = float(val)

    @property
    def LV(self) -> float:
        """
        Get ``LV``.

        :return: float
        """
        return self._LV

    @LV.setter
    def LV(self, val: float) -> None:
        """
        Set ``LV``.

        :param val: Value to assign.
        :return: None
        """
        self._LV = float(val)

    @property
    def Sn(self) -> float:
        """
        Get ``Sn``.

        :return: float
        """
        return self._Sn

    @Sn.setter
    def Sn(self, val: float) -> None:
        """
        Set ``Sn``.

        :param val: Value to assign.
        :return: None
        """
        self._Sn = float(val)

    @property
    def Pcu(self) -> float:
        """
        Get ``Pcu``.

        :return: float
        """
        return self._Pcu

    @Pcu.setter
    def Pcu(self, val: float) -> None:
        """
        Set ``Pcu``.

        :param val: Value to assign.
        :return: None
        """
        self._Pcu = float(val)

    @property
    def Pfe(self) -> float:
        """
        Get ``Pfe``.

        :return: float
        """
        return self._Pfe

    @Pfe.setter
    def Pfe(self, val: float) -> None:
        """
        Set ``Pfe``.

        :param val: Value to assign.
        :return: None
        """
        self._Pfe = float(val)

    @property
    def I0(self) -> float:
        """
        Get ``I0``.

        :return: float
        """
        return self._I0

    @I0.setter
    def I0(self, val: float) -> None:
        """
        Set ``I0``.

        :param val: Value to assign.
        :return: None
        """
        self._I0 = float(val)

    @property
    def Vsc(self) -> float:
        """
        Get ``Vsc``.

        :return: float
        """
        return self._Vsc

    @Vsc.setter
    def Vsc(self, val: float) -> None:
        """
        Set ``Vsc``.

        :param val: Value to assign.
        :return: None
        """
        self._Vsc = float(val)

    @property
    def capex(self) -> float:
        """
        Get ``capex``.

        :return: float
        """
        return self._capex

    @capex.setter
    def capex(self, val: float) -> None:
        """
        Set ``capex``.

        :param val: Value to assign.
        :return: None
        """
        self._capex = float(val)

    @property
    def opex(self) -> float:
        """
        Get ``opex``.

        :return: float
        """
        return self._opex

    @opex.setter
    def opex(self, val: float) -> None:
        """
        Set ``opex``.

        :param val: Value to assign.
        :return: None
        """
        self._opex = float(val)

    @property
    def vector_group_number(self) -> int:
        """
        Get ``vector_group_number``.

        :return: int
        """
        return self._vector_group_number

    @vector_group_number.setter
    def vector_group_number(self, val: int) -> None:
        """
        Set ``vector_group_number``.

        :param val: Value to assign.
        :return: None
        """
        self._vector_group_number = int(val)


def get_impedances(VH_bus: float, VL_bus: float, Sn: float, HV: float, LV: float,
                   Pcu: float, Pfe: float, I0: float, Vsc: float, Sbase: float,
                   GR_hv1: float) -> Tuple[complex, complex]:
    """
    Compute the branch parameters of a transformer from the short circuit test
    values.
    :param VH_bus: High voltage bus nominal voltage in kV
    :param VL_bus: Low voltage bus nominal voltage in kV
    :param Sn: Nominal power (MVA)
    :param HV: Transformer high voltage nominal voltage in kV
    :param LV: Transformer low voltage nominal voltage in kV
    :param Pcu: Copper losses, AKA resistive losses (kW)
    :param Pfe: Iron losses, AKA magnetic losses (kW)
    :param I0: No-load current (%)
    :param Vsc: Short-circuit voltage (%)
    :param Sbase: Base power in MVA (normally 100 MVA)
    :param GR_hv1: Share of impedance of towards the high voltage side (0 to 1)
    :return: Zseries and Yshunt in system per unit
    """

    # Series impedance -------------------------------------------------------------------------------------------------
    zsc = Vsc / 100.0

    if Sn > 0.0:
        rsc = (Pcu / 1000.0) / Sn
        if rsc < zsc:
            xsc = sqrt(zsc ** 2 - rsc ** 2)
        else:
            xsc = 0.0

        # series impedance in p.u. of the machine
        zs = rsc + 1j * xsc

        # convert impedances from machine per unit to ohms (HV side)
        z_base_hv = (HV * HV) / Sn
        z_series_hv = zs * GR_hv1 * z_base_hv  # Ohm
        z_base_hv_sys = (VH_bus * VH_bus) / Sbase  # convert impedances from ohms to system per unit

        # convert impedances from machine per unit to ohms (LV side)
        z_base_lv = (LV * LV) / Sn
        z_series_lv = zs * (1.0 - GR_hv1) * z_base_lv  # Ohm
        z_base_lv_sys = (VL_bus * VL_bus) / Sbase  # convert impedances from ohms to system per unit

        z_series = (z_series_hv / z_base_hv_sys) + (z_series_lv / z_base_lv_sys)

        # Shunt impedance (leakage) ------------------------------------------------------------------------------------
        if Pfe > 0.0 and I0 > 0.0:

            rm = Sbase / (Pfe / 1000.0)
            zm = (100.0 * Sbase) / (I0 * Sn)

            if zm < rm:  # only with this is possible to perform xm, otherwise we get div0 or sqrt(neg)
                xm = sqrt((-zm ** 2 * rm ** 2) / (zm ** 2 - rm ** 2))
            else:
                xm = 0.0
        else:
            rm = 0.0
            xm = 0.0

        g = 1.0 / rm if rm > 0.0 else 0.0
        b = 1.0 / xm if xm > 0.0 else 0.0

        # observe that we don't need to convert y_shunt to the system base since it is already
        y_shunt = g - 1j * b

    else:

        z_series = 0.0j
        y_shunt = 0.0j

    return z_series, y_shunt


def reverse_transformer_short_circuit_study(R: float, X: float, G: float, B: float, rate: float,
                                            Sbase: float) -> Tuple[float, float, float, float, float]:
    """
    Get the short circuit study values from the impedance values
    :param R:
    :param X:
    :param G:
    :param B:
    :param rate:
    :param Sbase: base power in MVA (100 MVA)
    :return:
    """
    """
    
    :param transformer_obj: Transformer2W
    :param Sbase: 
    :return: Pfe, Pcu, Vsc, I0, Sn
    """

    # Change the impedances to the system base
    base_change = Sbase / (rate + 1e-9)

    R = R / base_change
    X = X / base_change
    G = G / base_change
    B = B / base_change
    Sn = rate

    zsc = sqrt(R * R + X * X)
    Vsc = 100.0 * zsc
    Pcu = R * Sn * 1000.0

    if abs(G) > 0.0 and abs(B) > 0.0:
        zl = 1.0 / complex(G, B)
        rfe = zl.real
        xm = zl.imag

        Pfe = 1000.0 * Sn / rfe

        k = 1 / (rfe * rfe) + 1 / (xm * xm)
        I0 = 100.0 * sqrt(k)
    else:
        Pfe = 0
        I0 = 0

    return Pfe, Pcu, Vsc, I0, Sn
