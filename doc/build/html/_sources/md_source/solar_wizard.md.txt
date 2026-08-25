# ☀️ Solar power wizard

The solar power wizard creates an active power time profile for a generator from the bus coordinates, generator peak
power and the circuit time profile. It is intended for planning studies where a weather-based photovoltaic production
profile is needed but no measured plant profile is available.

The wizard is available from the generator context menu in the schematic and map editors. It requires an existing
circuit time profile because the generated photovoltaic power is written into the generator active power profile
(`P_prof`).

## Usage from the graphical interface

1. Create or import the circuit time profile.
2. Place a generator at a bus.
3. Set the bus latitude and longitude.
4. Set the generator maximum active power (`Pmax`) in MW.
5. Right-click the generator.
6. Select the solar photovoltaic wizard.
7. Check or edit the latitude, longitude and power values.
8. Press **Generate**.
9. Inspect the resulting `P (MW)` profile.
10. Press **Accept** to write the generated profile into the generator `P_prof`.

The generated profile must have the same length as the circuit time profile. If the lengths differ, the wizard rejects
the result.

## Inputs

| Input | Meaning | Units | Valid range |
| --- | --- | --- | --- |
| Latitude | Geographic latitude of the site | degrees | `-90` to `90` |
| Longitude | Geographic longitude of the site | degrees | `-180` to `180` |
| Power | Generator photovoltaic peak power | MW | greater than zero |
| Time profile | Circuit timestamps to align the photovoltaic profile to | datetime | sorted oldest to newest |

The wizard maps the requested circuit timestamps to a PVGIS-compatible historical year range, downloads the PVGIS hourly
photovoltaic production data, and interpolates the result to the exact circuit timestamps.

An internet connection is required when generating the profile because the weather and photovoltaic calculation data are
requested from PVGIS through `pvlib`.

## Example Python code

The lower-level helper can be called directly from Python:

```python
from datetime import datetime, timedelta

import pandas as pd

from VeraGrid.Gui.DeviceEditors.GeneratorEditor.SolarPowerWizard import get_pv_lib_weather_df


def main() -> None:
    """
    Generate a photovoltaic profile using the same helper used by the GUI wizard.

    :return: Nothing.
    """
    start_time: datetime = datetime(year=2026, month=1, day=1, hour=0, minute=0)
    time_array: list[datetime] = list()

    for i in range(24 * 7):
        timestamp: datetime = start_time + timedelta(hours=i)
        time_array.append(timestamp)

    latitude: float = 32.2
    longitude: float = -110.9
    peak_power: float = 20.0

    ok: bool
    data_frame: pd.DataFrame
    ok, data_frame = get_pv_lib_weather_df(time_array=time_array,
                                           latitude=latitude,
                                           longitude=longitude,
                                           peak_power=peak_power)

    if ok:
        power_mw = data_frame["P"].to_numpy() / 1e6
        print(power_mw)
    else:
        print("The photovoltaic profile could not be generated")


if __name__ == "__main__":
    main()
```

The PVGIS field `P` is returned in W by `pvlib`. VeraGrid converts it to MW before storing it in the generator profile:

```python
power_mw = data_frame["P"].to_numpy() / 1e6
```

## What the wizard generates

The wizard generates a weather-based modeled photovoltaic production profile. It is not a clear-sky theoretical curve
unless the selected data source and conditions effectively behave that way. PVGIS uses historical or typical
meteorological information and a photovoltaic performance model, so the result normally includes day-night behavior,
seasonal variation and weather-driven variability.

The result should be interpreted as a planning profile, not as measured production from a real plant.

## Theory

Photovoltaic active power depends mainly on irradiance, module temperature, system rating and losses. A simplified
model can be written as:

$$
P_{dc}(t) = P_{rated} \cdot \frac{G_{poa}(t)}{G_{stc}} \cdot f_T(t) \cdot f_{loss}
$$

Where:

- $P_{dc}(t)$ is the DC photovoltaic power at time $t$.
- $P_{rated}$ is the rated photovoltaic peak power.
- $G_{poa}(t)$ is the plane-of-array irradiance.
- $G_{stc}$ is the standard test condition irradiance, commonly $1000\ \text{W}/\text{m}^2$.
- $f_T(t)$ is the module temperature correction factor.
- $f_{loss}$ is the aggregate loss factor.

The final AC power also depends on inverter behavior:

$$
P_{ac}(t) = \eta_{inv}(t) \cdot P_{dc}(t)
$$

In practice, PVGIS and `pvlib` handle these calculations with more detailed assumptions than the equations above.
The important point for VeraGrid is that the resulting time series is an active power injection profile in MW.

## Realistic profiles and limitations

`pvlib` is a physical photovoltaic modeling library. By itself, it does not make production data real. The realism comes
from the weather data, site data and model assumptions used as inputs.

The wizard currently uses PVGIS through `pvlib`, so the result is a realistic estimate when:

- the latitude and longitude are correct,
- the generator peak power is correct,
- the circuit time profile is valid and sorted,
- the PVGIS data source covers the selected location,
- the default PVGIS assumptions are acceptable for the study.

The generated profile does not automatically know:

- local shading from buildings, terrain or vegetation,
- exact panel tilt and azimuth,
- exact module and inverter model,
- soiling, snow, dust or degradation,
- outages, curtailment or maintenance events,
- measured local microclimate effects below the PVGIS resolution.

For operational studies or validation work, prefer measured production profiles when available. For planning studies,
PVGIS-based profiles are usually appropriate if their assumptions are documented and the annual energy and capacity
factor are checked.

## Quality checks

After generating a profile, inspect the following:

- The profile contains no `NaN` values.
- Night values are close to zero.
- The maximum value does not exceed the generator peak power.
- The profile has visible daily and seasonal structure.
- Cloudy or weather-variable periods are not represented as identical clear-sky curves.
- The annual capacity factor is plausible for the location.

The capacity factor can be estimated as:

$$
CF = \frac{\sum_t P(t)\Delta t}{P_{rated} \cdot T}
$$

Where $T$ is the total simulated time in hours and $\Delta t$ is the time-step duration in hours.

## Troubleshooting

### The result is all `NaN`

This usually means the PVGIS timestamps were not aligned correctly with the circuit timestamps. The wizard aligns by
interpolating over the union of PVGIS timestamps and requested circuit timestamps. If this still occurs, check that the
time profile is sorted, valid and within the supported span.

### PVGIS request fails

Check the internet connection, coordinates and PVGIS service availability. Some locations or date ranges may not be
available from the selected PVGIS source.

### The profile is too smooth

The data may represent typical meteorological conditions or the selected source may not capture local cloud variability.
Use measured production or higher-resolution weather data if the study requires site-specific variability.

### The generated power is too high or too low

Check the generator `Pmax`, site coordinates and assumptions. A complete photovoltaic model should include tilt,
azimuth, losses, module temperature and inverter behavior. If those are important for the study, document the PVGIS
defaults or use a more detailed external profile.
