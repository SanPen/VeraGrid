# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple

from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.enumerations import DeviceType, PrpCat


class DcCableType(DynamicDevice):
    """
    Physical catalogue definition for a DC cable path.

    The electrical magnitudes are stored per kilometre so the same cable
    construction can be applied to ``DcLine`` instances of different lengths
    and system bases without retaining source-format reactance or susceptance.
    """

    __slots__ = (
        '_Vnom',
        '_Imax',
        '_R',
        '_L',
        '_C',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='Vnom',
            units='kV',
            tpe=float,
            definition='Rated DC voltage of the cable.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Imax',
            units='kA',
            tpe=float,
            definition='Continuous current rating of the represented DC cable path.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='R',
            units='Ohm/km',
            tpe=float,
            definition='Series resistance per kilometre.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='L',
            units='H/km',
            tpe=float,
            definition='Series inductance per kilometre.',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='C',
            units='F/km',
            tpe=float,
            definition='Equivalent shunt capacitance per kilometre of the represented DC cable path.',
            cat=[PrpCat.PF],
        ),
    )

    def __init__(self,
                 name: str = 'DC cable type',
                 idtag: str | None = None,
                 Vnom: float = 1.0,
                 Imax: float = 1.0,
                 R: float = 0.0,
                 L: float = 0.0,
                 C: float = 0.0) -> None:
        """
        Build a reusable physical DC cable definition.

        :param name: Catalogue name.
        :param idtag: Persistent object identifier.
        :param Vnom: Rated DC voltage in kV.
        :param Imax: Continuous current rating in kA for the represented cable path.
        :param R: Series resistance in Ohm/km.
        :param L: Series inductance in H/km.
        :param C: Equivalent shunt capacitance in F/km for the represented cable path.
        :return: None.
        """
        DynamicDevice.__init__(self,
                               name=name,
                               idtag=idtag,
                               code='',
                               device_type=DeviceType.DcCableTypeDevice)

        # Keep the catalogue values in physical units; conversion belongs to
        # the DcLine application boundary where length and system base exist.
        self.Vnom = Vnom
        self.Imax = Imax
        self.R = R
        self.L = L
        self.C = C

    @property
    def Vnom(self) -> float:
        """
        Get the cable rated voltage.

        :return: Rated voltage in kV.
        """
        return self._Vnom

    @Vnom.setter
    def Vnom(self, val: float) -> None:
        """
        Set the cable rated voltage.

        :param val: Rated voltage in kV.
        :return: None.
        """
        self._Vnom = float(val)

    @property
    def Imax(self) -> float:
        """
        Get the continuous cable-path current rating.

        :return: Current rating in kA.
        """
        return self._Imax

    @Imax.setter
    def Imax(self, val: float) -> None:
        """
        Set the continuous conductor current rating.

        :param val: Current rating in kA.
        :return: None.
        """
        self._Imax = float(val)

    @property
    def R(self) -> float:
        """
        Get the resistance per kilometre.

        :return: Resistance in Ohm/km.
        """
        return self._R

    @R.setter
    def R(self, val: float) -> None:
        """
        Set the resistance per kilometre.

        :param val: Resistance in Ohm/km.
        :return: None.
        """
        self._R = float(val)

    @property
    def L(self) -> float:
        """
        Get the inductance per kilometre.

        :return: Inductance in H/km.
        """
        return self._L

    @L.setter
    def L(self, val: float) -> None:
        """
        Set the inductance per kilometre.

        :param val: Inductance in H/km.
        :return: None.
        """
        self._L = float(val)

    @property
    def C(self) -> float:
        """
        Get the equivalent shunt capacitance per kilometre.

        :return: Capacitance in F/km.
        """
        return self._C

    @C.setter
    def C(self, val: float) -> None:
        """
        Set the total shunt capacitance per kilometre.

        :param val: Capacitance in F/km.
        :return: None.
        """
        self._C = float(val)

    def get_values(self,
                   Sbase: float,
                   length: float,
                   line_Vnom: float) -> Tuple[float, float, float]:
        """
        Convert the physical cable data to total per-unit coefficients.

        ``L`` and ``C`` are returned as the frequency-neutral coefficients
        used by the dynamic equations: ``L/Zbase`` and ``C*Zbase``.

        :param Sbase: System power base in MVA.
        :param length: Applied cable length in km.
        :param line_Vnom: DC voltage base of the connected line in kV.
        :return: Resistance in p.u., inductance in p.u. seconds, and
                 capacitance in p.u. seconds.
        """
        z_base: float = line_Vnom * line_Vnom / Sbase
        resistance_pu: float = self.R * length / z_base
        inductance_pu_seconds: float = self.L * length / z_base
        capacitance_pu_seconds: float = self.C * length * z_base
        return resistance_pu, inductance_pu_seconds, capacitance_pu_seconds
