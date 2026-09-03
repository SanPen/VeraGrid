# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple
import numpy as np
from VeraGridEngine.Devices.Parents.editable_device import DeviceType, GCProp
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Branches.sequence_line_type import sequence_to_phase_matrix
from VeraGridEngine.enumerations import PrpCat


class UndergroundLineType(DynamicDevice):
    __slots__ = (
        '_Imax',
        '_Vnom',
        '_freq',
        '_R',
        '_X',
        '_B',
        '_C',
        '_R0',
        '_X0',
        '_B0',
        '_C0',
        '_n_circuits',
        '_capex',
        '_opex',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='Imax',
            units='kA',
            tpe=float,
            definition='Current rating of the line',
            old_names=['rating'],
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Vnom',
            units='kV',
            tpe=float,
            definition='Voltage rating of the line',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='freq',
            units='Hz',
            tpe=float,
            definition='Cable frequency',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='R',
            units='Ohm/km',
            tpe=float,
            definition='Positive-sequence resistance per km',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='X',
            units='Ohm/km',
            tpe=float,
            definition='Positive-sequence reactance per km',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='B',
            units='uS/km',
            tpe=float,
            definition='Positive-sequence shunt susceptance per km',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='C',
            units='uF/km',
            tpe=float,
            definition='Positive-sequence shunt capacitance per km (alternative to B',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='R0',
            units='Ohm/km',
            tpe=float,
            definition='Zero-sequence resistance per km',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='X0',
            units='Ohm/km',
            tpe=float,
            definition='Zero-sequence reactance per km',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='B0',
            units='uS/km',
            tpe=float,
            definition='Zero-sequence shunt susceptance per km',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='C0',
            units='uF/km',
            tpe=float,
            definition='Zero-sequence shunt capacitance per km (alternative to B0',
            cat=[PrpCat.SC, PrpCat.PF3],
        ),
        GCProp(
            prop_name='n_circuits',
            units='',
            tpe=int,
            definition='number of circuits',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='capex',
            units='currency/km',
            tpe=float,
            definition='Capital expenditure per km',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='opex',
            units='currency/MWh',
            tpe=float,
            definition='Operational expenditure',
            cat=[PrpCat.INV],
        ),
    )

    def __init__(self, name: str = 'UndergroundLine', idtag: None | str = None, Imax: float = 1.0,
                 Vnom: float = 1.0, R: float = 0.0, X: float = 0.0, B: float = 0.0, C: float = 0.0,
                 R0: float = 0.0, X0: float = 0.0, B0: float = 0.0, C0: float = 0.0,
                 freq: float = 50.0,
                 capex: float = 0.0, opex: float = 0.0) -> None:
        """
        Constructor
        :param name: name of the device
        :param Imax: rating in kA
        :param R: Resistance of positive sequence in Ohm/km
        :param X: Reactance of positive sequence in Ohm/km
        :param B: Susceptance of positive sequence in uS/km
        :param C: Capacitance of positive sequence in uF/km (alternative to B)
        :param R0: Resistance of zero sequence in Ohm/km
        :param X0: Reactance of zero sequence in Ohm/km
        :param B0: Susceptance of zero sequence in uS/km
        :param C0: Capacitance of zero sequence in uF/km (alternative to B0)
        :param freq: Frequency of underground line (Hz)
        :param capex: Capital expenditures
        :param opex: Operating expenditures
        """
        DynamicDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.UnderGroundLineDevice)

        self.Imax = float(Imax)
        self.Vnom = float(Vnom)
        self._freq = float(freq)

        # impudence and admittance per unit of length
        self.R = float(R)
        self.X = float(X)
        self.B = float(B)
        self._C = float(C)

        self.R0 = float(R0)
        self.X0 = float(X0)
        self.B0 = float(B0)
        self._C0 = float(C0)

        self.n_circuits = 1

        self.capex = float(capex)
        self.opex = float(opex)

    def get_values(self, Sbase: float, length: float):
        """
        Get the per-unit values
        :param Sbase: Base power (MVA, always use 100MVA)
        :param length: length in km
        :return: R (p.u.), x(p.u.), B(p.u.), Rate (MVA)
        """
        Vn = self.Vnom
        Zbase = (Vn * Vn) / Sbase
        Ybase = 1.0 / Zbase

        R = np.round(self.R * length / Zbase, 6)
        X = np.round(self.X * length / Zbase, 6)
        B = np.round(self.B * 1e-6 * length / Ybase, 6)

        R0 = np.round(self.R0 * length / Zbase, 6)
        X0 = np.round(self.X0 * length / Zbase, 6)
        B0 = np.round(self.B0 * 1e-6 * length / Ybase, 6)

        # get the rating in MVA = kA * kV
        rate = self.Imax * Vn * np.sqrt(3)

        return R, X, B, R0, X0, B0, rate

    def z_series(self):
        """
        positive sequence series impedance in Ohm per unit of length
        """
        return self.R + 1j * self.X

    def y_shunt(self):
        """
        positive sequence shunt admittance in S per unit of length
        """
        return 1j * self.B

    @property
    def z_nabc(self) -> np.ndarray:
        """Return the physical ABC series-impedance matrix in Ohm/km."""
        return sequence_to_phase_matrix(
            positive_sequence_value=self.R + 1j * self.X,
            zero_sequence_value=self.R0 + 1j * self.X0,
        )

    @property
    def y_nabc(self) -> np.ndarray:
        """Return the physical ABC shunt-admittance matrix in S/km."""
        if abs(self.C) > 0.0 or abs(self.C0) > 0.0:
            positive_susceptance = 2.0 * np.pi * self.freq * self.C * 1.0e-6
            zero_susceptance = 2.0 * np.pi * self.freq * self.C0 * 1.0e-6
        else:
            positive_susceptance = self.B * 1.0e-6
            zero_susceptance = self.B0 * 1.0e-6

        return sequence_to_phase_matrix(
            positive_sequence_value=1j * positive_susceptance,
            zero_sequence_value=1j * zero_susceptance,
        )

    @property
    def z_phases_nabc(self) -> np.ndarray:
        """Return the phase indices corresponding to ``z_nabc``."""
        return np.array([1, 2, 3], dtype=int)

    @property
    def y_phases_nabc(self) -> np.ndarray:
        """Return the phase indices corresponding to ``y_nabc``."""
        return np.array([1, 2, 3], dtype=int)

    @property
    def C(self) -> float:
        return self._C

    @C.setter
    def C(self, C: float):
        self._C = float(C)

        if self.auto_update_enabled:
            self.B = 2 * np.pi * self._freq * self._C

    @property
    def C0(self) -> float:
        return self._C0

    @C0.setter
    def C0(self, C0: float):
        self._C0 = float(C0)

        if self.auto_update_enabled:
            self.B0 = 2 * np.pi * self._freq * self._C0

    @property
    def freq(self) -> float:
        return self._freq

    @freq.setter
    def freq(self, freq: float):
        self._freq = float(freq)

        if self.auto_update_enabled:
            self.B = 2 * np.pi * self._freq * self._C
            self.B0 = 2 * np.pi * self._freq * self._C0

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def Imax(self) -> float:
        """
        Get ``Imax``.

        :return: float
        """
        return self._Imax

    @Imax.setter
    def Imax(self, val: float) -> None:
        """
        Set ``Imax``.

        :param val: Value to assign.
        :return: None
        """
        self._Imax = float(val)

    @property
    def Vnom(self) -> float:
        """
        Get ``Vnom``.

        :return: float
        """
        return self._Vnom

    @Vnom.setter
    def Vnom(self, val: float) -> None:
        """
        Set ``Vnom``.

        :param val: Value to assign.
        :return: None
        """
        self._Vnom = float(val)

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
    def n_circuits(self) -> int:
        """
        Get ``n_circuits``.

        :return: int
        """
        return self._n_circuits

    @n_circuits.setter
    def n_circuits(self, val: int) -> None:
        """
        Set ``n_circuits``.

        :param val: Value to assign.
        :return: None
        """
        self._n_circuits = int(val)

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
