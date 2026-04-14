# VeraGridEngine Module: src/VeraGridEngine/Devices/Substation/substation.py

- Original source path: `src/VeraGridEngine/Devices/Substation/substation.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 0
- Representative imports: __future__, typing, datetime, numpy, VeraGridEngine.Devices.Parents.physical_device, VeraGridEngine.Devices.Aggregation.area, VeraGridEngine.Devices.Aggregation.zone, VeraGridEngine.Devices.Aggregation.country, VeraGridEngine.Devices.Aggregation.community, VeraGridEngine.Devices.Aggregation.region, VeraGridEngine.Devices.Aggregation.municipality,  VeraGridEngine.Devices.Parents.editable_device, VeraGridEngine.enumerations

## Class: Substation

- Bases: PhysicalDevice
- Summary: No docstring provided.

### Methods

- `area(self)`
  Summary: area getter
- `area(self, val)`
  Summary: area getter
- `zone(self)`
  Summary: zone getter
- `zone(self, val)`
  Summary: zone getter
- `country(self)`
  Summary: country getter
- `country(self, val)`
  Summary: country getter
- `community(self)`
  Summary: community getter
- `community(self, val)`
  Summary: community getter
- `region(self)`
  Summary: region getter
- `region(self, val)`
  Summary: region getter
- `municipality(self)`
  Summary: municipality getter
- `municipality(self, val)`
  Summary: municipality getter
- `irradiation_prof(self)`
  Summary: Irradiation profile
- `irradiation_prof(self, val)`
  Summary: No docstring provided.
- `get_irradiation_at(self, t)`
  Summary: :param t:
- `temperature_prof(self)`
  Summary: Temperature profile
- `temperature_prof(self, val)`
  Summary: No docstring provided.
- `get_temperature_at(self, t)`
  Summary: :param t:
- `wind_speed_prof(self)`
  Summary: wind_speed_prof profile
- `wind_speed_prof(self, val)`
  Summary: No docstring provided.
- `get_wind_speed_at(self, t)`
  Summary: :param t:
- `commissioned_date(self)`
  Summary: :return:
- `commissioned_date(self, val)`
  Summary: No docstring provided.
- `set_commissioned_year(self, year, month, day)`
  Summary: Helper function to set the commissioning date of the asset
- `get_commissioned_date_as_date(self)`
  Summary: Get the commissioned date as datetime
- `decommissioned_date(self)`
  Summary: :return:
- `decommissioned_date(self, val)`
  Summary: No docstring provided.
- `set_decommissioned_year(self, year, month, day)`
  Summary: Helper function to set the decommissioning date of the asset
- `get_decommissioned_date_as_date(self)`
  Summary: Get the commissioned date as datetime
- `longitude(self)`
  Summary: Get ``longitude``.
- `longitude(self, val)`
  Summary: Set ``longitude``.
- `latitude(self)`
  Summary: Get ``latitude``.
- `latitude(self, val)`
  Summary: Set ``latitude``.
- `irradiation(self)`
  Summary: Get ``irradiation``.
- `irradiation(self, val)`
  Summary: Set ``irradiation``.
- `temperature(self)`
  Summary: Get ``temperature``.
- `temperature(self, val)`
  Summary: Set ``temperature``.
- `wind_speed(self)`
  Summary: Get ``wind_speed``.
- `wind_speed(self, val)`
  Summary: Set ``wind_speed``.
- `terrain_roughness(self)`
  Summary: Get ``terrain_roughness``.
- `terrain_roughness(self, val)`
  Summary: Set ``terrain_roughness``.
