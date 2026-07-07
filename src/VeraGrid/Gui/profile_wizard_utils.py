# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union

import numpy as np

from VeraGridEngine.Devices.Profiles import ProfileFloat
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Substation.substation import Substation


def profile_is_missing(profile: ProfileFloat, default_value: float, expected_size: int) -> bool:
    """
    Determine whether a float profile should be considered missing for wizard weather filling.

    :param profile: Profile to inspect.
    :param default_value: Snapshot value associated with the profile.
    :param expected_size: Expected MultiCircuit time profile length.
    :return: True if the profile is missing and can be filled.
    """
    if profile.is_initialized:
        if profile.size() == expected_size:
            profile_array: np.ndarray = profile.toarray()

            if len(profile_array) == expected_size:
                if np.allclose(profile_array, default_value):
                    if np.isclose(default_value, 0.0):
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return True
        else:
            return True
    else:
        return True


def fill_substation_weather_profiles(bus: Bus,
                                     temperature: Union[np.ndarray, None],
                                     wind_speed: Union[np.ndarray, None],
                                     irradiation: Union[np.ndarray, None],
                                     expected_size: int) -> None:
    """
    Fill missing weather profiles on the substation associated with a bus.

    Existing non-empty weather profiles are preserved. The MultiCircuit time profile length is used as the required
    size for all incoming arrays.

    :param bus: Bus associated with the generated profile.
    :param temperature: Air temperature profile in degrees Celsius.
    :param wind_speed: Wind speed profile in m/s.
    :param irradiation: Solar irradiation profile in W/m2.
    :param expected_size: Expected MultiCircuit time profile length.
    :return: Nothing.
    """
    substation: Union[Substation, None] = bus.substation

    if substation is None:
        return
    else:
        if temperature is None:
            pass
        else:
            if len(temperature) == expected_size:
                if profile_is_missing(profile=substation.temperature_prof,
                                      default_value=substation.temperature,
                                      expected_size=expected_size):
                    substation.temperature_prof = np.asarray(temperature, dtype=float)
                    substation.temperature = float(np.asarray(temperature, dtype=float)[0])
                else:
                    pass
            else:
                pass

        if wind_speed is None:
            pass
        else:
            if len(wind_speed) == expected_size:
                if profile_is_missing(profile=substation.wind_speed_prof,
                                      default_value=substation.wind_speed,
                                      expected_size=expected_size):
                    substation.wind_speed_prof = np.asarray(wind_speed, dtype=float)
                    substation.wind_speed = float(np.asarray(wind_speed, dtype=float)[0])
                else:
                    pass
            else:
                pass

        if irradiation is None:
            pass
        else:
            if len(irradiation) == expected_size:
                if profile_is_missing(profile=substation.irradiation_prof,
                                      default_value=substation.irradiation,
                                      expected_size=expected_size):
                    substation.irradiation_prof = np.asarray(irradiation, dtype=float)
                    substation.irradiation = float(np.asarray(irradiation, dtype=float)[0])
                else:
                    pass
            else:
                pass
