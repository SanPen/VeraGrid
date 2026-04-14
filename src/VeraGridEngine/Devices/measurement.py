# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union
import numpy as np
from VeraGridEngine.Devices.Parents.editable_device import get_at
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.Devices.Branches.switch import Switch
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from VeraGridEngine.Devices.Branches.upfc import UPFC
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.profile import Profile
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.basic_structures import Vec

# NOTE: These area here because this object loads first than the types file with the types aggregations

SE_BRANCH_TYPES = Union[
    Line,
    DcLine,
    Transformer2W,
    UPFC,
    Winding,
    Switch,
    SeriesReactance,
    Generator
]
MEASURABLE_OBJECT = Union[Bus, SE_BRANCH_TYPES]


class MeasurementTemplate(PointerDeviceParent):
    """
    Measurement class
    """

    __slots__ = (
        'value',
        '_value_prof',
        'sigma',
        '_sigma_prof',
    )

    def __init__(self, value: float,
                 uncertainty: float,
                 api_obj: MEASURABLE_OBJECT,
                 name: str,
                 idtag: Union[str, None],
                 device_type: DeviceType):
        """
        Constructor
        :param value: value
        :param uncertainty: uncertainty (standard deviation)
        :param api_obj:
        :param name:
        :param idtag:
        """

        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=api_obj,
                                     code="",
                                     name=name,
                                     device_type=device_type,
                                     comment="")

        self.value = float(value)
        self.sigma = float(uncertainty)

        self._value_prof = Profile(default_value=self.value, data_type=float)
        self._sigma_prof = Profile(default_value=self.sigma, data_type=float)

        self.register("value", tpe=float, profile_name="value_prof",
                      definition="Value of the measurement")
        self.register("sigma", tpe=float, profile_name="sigma_prof",
                      definition="Uncertainty of the measurement")

    @property
    def value_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._value_prof

    @value_prof.setter
    def value_prof(self, val: Union[Profile, Vec]):
        if isinstance(val, Profile):
            self._value_prof = val
        elif isinstance(val, np.ndarray):
            self._value_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a value_prof')

    def get_value_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.value, self.value_prof, t)

    @property
    def sigma_prof(self) -> Profile:
        """
        Cost profile
        :return: Profile
        """
        return self._sigma_prof

    @sigma_prof.setter
    def sigma_prof(self, val: Union[Profile, np.ndarray]):
        if isinstance(val, Profile):
            self._sigma_prof = val
        elif isinstance(val, np.ndarray):
            self._sigma_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a sigma_prof')

    def get_sigma_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.sigma, self.sigma_prof, t)

    def get_value_pu_at(self, t: int | None, Sbase: float):
        """
        Get measurement per-unit value at a given point
        :param t: None for snapshot, integer for time point
        :param Sbase: Base power (100 MVA)
        :return: value in p.u.
        """
        return self.get_value_at(t) / Sbase

    def get_standard_deviation_pu_at(self, t: int | None, Sbase: float):
        """
        Get measurement per-unit standard deviation at a given point
        :param t: None for snapshot, integer for time point
        :param Sbase: Base power (100 MVA)
        :return: value in p.u.
        """
        return self.get_sigma_at(t) / Sbase


class PiMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Bus | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        Bus active power injection measurement
        :param value: value in MW
        :param uncertainty: standard deviation in MW
        :param api_obj: bus object
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.PMeasurementDevice)


class QiMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Bus | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        Bus reactive power injection measurement
        :param value: value in MVAr
        :param uncertainty: standard deviation in MVAr
        :param api_obj: bus object
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.QMeasurementDevice)


class PgMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Generator | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        Generator active power injection measurement
        :param value: value in MW
        :param uncertainty: standard deviation in MW
        :param api_obj: bus object
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.PgMeasurementDevice)


class QgMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Generator | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        Generator reactive power injection measurement
        :param value: value in MVAr
        :param uncertainty: standard deviation in MVAr
        :param api_obj: bus object
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.QgMeasurementDevice)


class VmMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Bus | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.VmMeasurementDevice)


class VaMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: Bus | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.VaMeasurementDevice)


class PfMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        PfMeasurement
        :param value: Power flow in MW
        :param uncertainty: standard deviation in MW
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.PfMeasurementDevice)


class QfMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        QfMeasurement
        :param value: Power flow in MVAr
        :param uncertainty: standard deviation in MVAr
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.QfMeasurementDevice)


class PtMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        PtMeasurement
        :param value: Power flow in MW
        :param uncertainty: standard deviation in MW
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.PtMeasurementDevice)


class QtMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        QtMeasurement
        :param value: Power flow in MVAr
        :param uncertainty: standard deviation in MVAr
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.QtMeasurementDevice)


def get_i_base(Sbase, Vbase):
    return Sbase / (Vbase * 1.732050808)


class IfMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        IfMeasurement
        :param value: current flow in kA, note this is the absolute value
        :param uncertainty: standard deviation in kA
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.IfMeasurementDevice)

    def get_value_pu_at(self, t: int | None, Sbase: float):
        return self.get_value_at(t) / get_i_base(Sbase, Vbase=self.api_object.bus_from.Vnom)

    def get_standard_deviation_pu_at(self, t: int | None, Sbase: float):
        return self.get_sigma_at(t) / get_i_base(Sbase, Vbase=self.api_object.bus_from.Vnom)


class ItMeasurement(MeasurementTemplate):
    """
    Measurement class
    """

    def __init__(self,
                 value: float = 0.0,
                 uncertainty: float = 0.0,
                 api_obj: SE_BRANCH_TYPES | None = None,
                 name="",
                 idtag: Union[str, None] = None):
        """
        ItMeasurement
        :param value: current flow in kA, note this is the absolute value
        :param uncertainty: standard deviation in kA
        :param api_obj: a branch
        :param name: name
        :param idtag: idtag
        """
        MeasurementTemplate.__init__(self,
                                     value=value,
                                     uncertainty=uncertainty,
                                     api_obj=api_obj,
                                     name=name,
                                     idtag=idtag,
                                     device_type=DeviceType.ItMeasurementDevice)

    @property
    def device(self) -> SE_BRANCH_TYPES:
        """
        device getter
        :return:
        """
        return self._device

    def get_value_pu_at(self, t: int | None, Sbase: float):
        return self.value / get_i_base(Sbase, Vbase=self.device.bus_to.Vnom)

    def get_standard_deviation_pu_at(self, t: int | None, Sbase: float):
        return self.sigma / get_i_base(Sbase, Vbase=self.device.bus_to.Vnom)
