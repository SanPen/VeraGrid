# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
import math
import numpy as np
import pandas as pd
from datetime import datetime
from collections.abc import Mapping
from typing import Dict
import pyproj
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Aggregation.branch_group import BranchGroup
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Branches.transformer import TransformerType, Transformer2W
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGridEngine.enumerations import BuildStatus, GeneratorControlMode
from VeraGridEngine.Devices.Branches.line import SequenceLineType, Line
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Aggregation.country import Country
from VeraGridEngine.Devices.Aggregation.investment import Investment
from VeraGridEngine.Devices.Aggregation.investments_group import InvestmentsGroup
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.Associations.emission_gas import EmissionGas
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Fluid.fluid_turbine import FluidTurbine
from VeraGridEngine.Devices.Fluid.fluid_pump import FluidPump
from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.voltage_level import VoltageLevel

from VeraGridEngine.Utils.optional_dependencies import optional_dependency_failure

# PyPSA is optional and can remain stale after a VeraGrid upgrade; validate its entry point here.
try:
    import pypsa
    from pypsa import Network

    PYPSA_AVAILABLE = True
    PYPSA_UNAVAILABLE_REASON: str = ""
except (ImportError, AttributeError, OSError, RuntimeError, ValueError, TypeError) as error:
    PYPSA_AVAILABLE = False
    PYPSA_UNAVAILABLE_REASON = optional_dependency_failure("pypsa", error)


class PyPSAParser:
    """
    PyPSAParser
    """

    __slots__ = (
        "pypsa_grid",
        "grid",
        "logger",
        "nt",
        "srid",
        "to_latlon_converter",
        "to_xy_converter",
        "countries",
        "substations",
        "voltage_levels",
        "technologies",
        "emission_gases",
        "fluid_nodes_by_bus",
        "investment_groups",
        "buses",
        "line_types",
        "transformer_types",
    )

    VIRTUAL_FLUID_VOLUME_PER_MWH: float = 1e6

    def __init__(self, pypsa_grid: 'pypsa.Network', logger: Logger):
        """

        :param pypsa_grid:
        :param logger:
        """
        self.pypsa_grid = pypsa_grid
        self.grid = MultiCircuit(pypsa_grid.name)  # todo: PyPSA doesn't provide f_base
        self.logger = logger

        self.nt = len(pypsa_grid.snapshots)
        # Preserve the source timestamps exactly instead of converting every
        # PyPSA study into an hourly grid. VeraGrid profiles use this index for
        # all imported time-series values.
        if isinstance(pypsa_grid.snapshots, pd.MultiIndex):
            # VeraGrid has one chronological profile index. Retain the snapshot
            # timestamps and preserve PyPSA investment-period semantics through
            # imported Investment records rather than silently inventing dates.
            self.grid.format_profiles(pd.DatetimeIndex(pypsa_grid.snapshots.get_level_values(-1)))
            self.logger.add_warning(msg="PyPSA MultiIndex snapshots flattened to timestamp profile")
        else:
            self.grid.format_profiles(pypsa_grid.snapshots)

        # Snapshot weights affect PyPSA objective and storage-energy equations.
        # VeraGrid profiles retain timestamps but have no import-side weight
        # container, so make a non-uniform source weighting explicit.
        objective_weights: np.ndarray = pypsa_grid.snapshot_weightings['objective'].to_numpy()
        if not np.allclose(objective_weights, objective_weights[0]):
            self.logger.add_warning(msg="PyPSA non-uniform snapshot weights not imported")
        else:
            pass

        self.srid = self.pypsa_grid.srid  # EPSG number

        # geo_crs: EPSG:4326  # general geographic projection, not used for metric measures. "EPSG:4326" is the standard used by OSM and google maps
        # distance_crs: EPSG:3857  # projection for distance measurements only. Possible recommended values are "EPSG:3857" (used by OSM and Google Maps)
        # area_crs: ESRI:54009  # projection for area measurements only. Possible recommended values are Global Mollweide "ESRI:54009"
        self.to_latlon_converter = pyproj.Transformer.from_crs(self.srid, 4326, always_xy=True)
        self.to_xy_converter = pyproj.Transformer.from_crs(self.srid, 3857, always_xy=True)

        self.countries = self._parse_countries()
        self.substations, self.voltage_levels = self._parse_substations()
        self.technologies = dict()
        self.emission_gases = dict()
        self.fluid_nodes_by_bus = dict()
        self.investment_groups = dict()
        self.buses = self._parse_buses()
        self.line_types = self._parse_line_types()
        self.transformer_types = self._parse_transformer_types()

    @staticmethod
    def _parse_date(raw: str) -> datetime:
        return datetime.strptime(raw, '%Y-%m-%d')

    @staticmethod
    def _finite_float(value: object, fallback: float) -> float:
        """
        Convert a PyPSA scalar to a finite float.

        :param value: Value provided by PyPSA.
        :param fallback: Value to use for missing or non-finite data.
        :return: A finite floating-point value.
        """
        try:
            result: float = float(value)
        except (TypeError, ValueError):
            result = fallback
        else:
            if not math.isfinite(result):
                result = fallback
            else:
                pass
        return result

    def _get_time_series(self, time_series: object, device_name: str, field_name: str) -> np.ndarray | None:
        """
        Return one complete PyPSA time-series column when it is available.

        :param time_series: PyPSA component time-series table.
        :param device_name: Name of the component owning the requested series.
        :param field_name: PyPSA field represented by the table.
        :return: Snapshot-aligned values, or ``None`` when PyPSA uses a static value.
        """
        try:
            values: np.ndarray | None = time_series[device_name].to_numpy()
        except (AttributeError, KeyError):
            values = None
        else:
            # A partial profile cannot be assigned because VeraGrid profiles
            # must align with every circuit snapshot.
            if values.size != self.nt:
                self.logger.add_warning(msg=f"Invalid PyPSA {field_name} profile length", device=device_name)
                values = None
            else:
                pass
        return values

    def _apply_soc_targets(self, battery: Battery, energy_targets: np.ndarray,
                           device_name: str) -> None:
        """
        Report PyPSA energy targets unsupported by the static Battery interface.

        :param battery: Imported VeraGrid Battery.
        :param energy_targets: PyPSA energy targets in MWh, with NaN for no target.
        :param device_name: Source device name for logging.
        :return: None.
        """
        if np.any(np.isfinite(energy_targets)):
            # An energy target is not an active-power dispatch schedule. The
            # existing Battery has static limits only, so mapping it to P would
            # make a different model rather than a conservative import.
            self.logger.add_warning(msg="PyPSA time-varying energy targets not imported for Battery",
                                    device=device_name)
        else:
            pass

    def _add_store_fluid_node(self, name: str, data: object, bus: Bus,
                              nominal_energy: float, min_soc: float,
                              max_soc: float, initial_energy: float) -> FluidNode | None:
        """
        Add a physical FluidNode for a Store carrying explicit volume metadata.

        :param name: Source PyPSA Store name.
        :param data: Static PyPSA Store row.
        :param bus: Electrical bus shared with the electrical Store equivalent.
        :param nominal_energy: Store nominal energy in MWh.
        :param min_soc: Store lower per-unit energy bound.
        :param max_soc: Store upper per-unit energy bound.
        :param initial_energy: Store initial energy in MWh.
        :return: FluidNode when physical conversion data exists, otherwise ``None``.
        """
        volume_per_mwh: float = self._finite_float(data.get('fluid_volume_per_mwh', 0.0), 0.0)
        if volume_per_mwh > 0.0:
            # PyPSA Store is energy-based. This custom source field supplies
            # the otherwise unknowable MWh-to-m3 conversion needed by FluidNode.
            # FluidNode stores hm3, hence the 1e6 conversion from cubic metres.
            energy_to_hm3: float = volume_per_mwh / 1e6
            fluid_node = FluidNode(name=f'{name}::fluid state',
                                   min_level=nominal_energy * min_soc * energy_to_hm3,
                                   max_level=nominal_energy * max_soc * energy_to_hm3,
                                   min_soc=min_soc,
                                   max_soc=max_soc,
                                   current_level=initial_energy * energy_to_hm3,
                                   bus=bus)
            self.grid.add_fluid_node(fluid_node)
            self.logger.add_info(msg="Imported PyPSA Store fluid-state representation", device=name)
            return fluid_node
        else:
            # A generic PyPSA Store has no physical volume or hydraulic head.
            # Keep the Battery electrical equivalent rather than fabricating one.
            self.logger.add_info(msg="PyPSA Store retained as Battery; no fluid_volume_per_mwh metadata", device=name)
            return None

    def _add_virtual_fluid_storage(self, name: str, bus: Bus, nominal_energy: float,
                                   min_soc: float, max_soc: float, initial_energy: float,
                                   charge_rate: float, discharge_rate: float,
                                   charge_efficiency: float, discharge_efficiency: float,
                                   active: bool, cost: float) -> tuple[FluidNode, Generator, Generator, FluidTurbine, FluidPump]:
        """
        Build an energy-store equivalent with VeraGrid's native fluid topology.

        :param name: Source PyPSA component name.
        :param bus: Electrical bus hosting the two conversion machines.
        :param nominal_energy: Energy capacity in MWh.
        :param min_soc: Minimum stored-energy fraction.
        :param max_soc: Maximum stored-energy fraction.
        :param initial_energy: Initial energy in MWh.
        :param charge_rate: Maximum charging power in MW.
        :param discharge_rate: Maximum discharging power in MW.
        :param charge_efficiency: PyPSA charging efficiency.
        :param discharge_efficiency: PyPSA discharging efficiency.
        :param active: Source active state.
        :param cost: Marginal electrical output cost.
        :return: Fluid state, conversion generators, turbine, and pump.
        """
        # A virtual fluid is used deliberately: one MWh occupies one hm3. This
        # gives a stable, reversible energy state without claiming that every
        # PyPSA Store is literal water. The factor still lets fluid equations
        # operate in their required cubic-metre-per-second units.
        volume_scale: float = self.VIRTUAL_FLUID_VOLUME_PER_MWH
        energy_to_hm3: float = volume_scale / 1e6
        node = FluidNode(name=f'{name}::energy state',
                         min_level=nominal_energy * min_soc * energy_to_hm3,
                         # FluidNode applies min/max SoC to max_level during
                         # formulation, so max_level must remain the nominal
                         # capacity rather than an already derated bound.
                         max_level=nominal_energy * energy_to_hm3,
                         min_soc=min_soc,
                         max_soc=max_soc,
                         current_level=initial_energy * energy_to_hm3,
                         bus=bus)
        self.grid.add_fluid_node(node)

        discharge_generator = Generator(name=f'{name}::discharge',
                                        P=0.0,
                                        Pmin=0.0,
                                        Pmax=discharge_rate,
                                        Snom=discharge_rate,
                                        active=active,
                                        Cost=cost,
                                        enabled_dispatch=True)
        charge_generator = Generator(name=f'{name}::charge',
                                     P=0.0,
                                     Pmin=-charge_rate,
                                     Pmax=0.0,
                                     Snom=charge_rate,
                                     active=active,
                                     Cost=0.0,
                                     enabled_dispatch=True)
        self.grid.add_generator(bus=bus, api_obj=discharge_generator)
        self.grid.add_generator(bus=bus, api_obj=charge_generator)

        # At rated output, turbine flow removes Pmax / eta MWh per hour.
        # At rated charging, pump flow adds Pmax * eta MWh per hour. Passing
        # each PyPSA efficiency to the native fluid devices preserves both
        # directions of the original storage energy recurrence exactly.
        turbine = FluidTurbine(name=f'{name}::turbine',
                               efficiency=max(discharge_efficiency, 1e-12),
                               max_flow_rate=discharge_rate * volume_scale / 3600.0,
                               plant=node,
                               generator=discharge_generator)
        pump = FluidPump(name=f'{name}::pump',
                         efficiency=max(charge_efficiency, 1e-12),
                         max_flow_rate=charge_rate * volume_scale / 3600.0,
                         reservoir=node,
                         generator=charge_generator)
        self.grid.add_fluid_turbine(node=node, api_obj=turbine)
        self.grid.add_fluid_pump(node=node, api_obj=pump)
        self.logger.add_info(msg="Imported PyPSA storage as virtual FluidNode with pump and turbine", device=name)
        return node, discharge_generator, charge_generator, turbine, pump

    @staticmethod
    def _is_active(data) -> bool:
        """
        Returns whether the given component is active. This feature is only
        supported by some PyPSA networks, e.g. those in the PyPSA-Eur models.
        :param data: the component data.
        """
        try:
            return not data['under_construction']
        except KeyError:
            return True

    def _parse_countries(self) -> "Mapping[str, Country]":
        """
        Parses the country data from the PyPSA network.
        :return: a mapping from country name to VeraGrid `Country` objects.
        """
        by_name: Dict[str, Country] = dict()
        country_names: set[str] = set()
        for name in self.pypsa_grid.meta.get('countries', list()):
            if isinstance(name, str) and name != '':
                country_names.add(name)
            else:
                pass
        for _, data in self.pypsa_grid.buses.iterrows():
            name: object = data.get('country', None)
            if isinstance(name, str) and name != '':
                country_names.add(name)
            else:
                pass
        # Stable ordering keeps imported object identifiers and UI order
        # reproducible across Python processes.
        for name in sorted(country_names):
            country = Country(name)
            self.grid.add_country(country)
            by_name[name] = country
        return by_name

    def _parse_substations(self) -> tuple[Dict[str, Substation], Dict[str, VoltageLevel]]:
        """
        Build VeraGrid substation and voltage-level objects from PyPSA buses.

        :return: Source-name mappings for substations and voltage levels.
        """
        substations: Dict[str, Substation] = dict()
        voltage_levels: Dict[str, VoltageLevel] = dict()
        for bus_name, data in self.pypsa_grid.buses.iterrows():
            substation_name: object = data.get('substation', None)
            if isinstance(substation_name, str) and substation_name != '':
                substation: Substation | None = substations.get(substation_name, None)
                if substation is None:
                    country_name: object = data.get('country', None)
                    country: Country | None = self.countries.get(country_name, None)
                    substation = Substation(name=substation_name,
                                            longitude=self._finite_float(data.get('x', 0.0), 0.0),
                                            latitude=self._finite_float(data.get('y', 0.0), 0.0),
                                            country=country)
                    self.grid.add_substation(substation)
                    substations[substation_name] = substation
                    self.logger.add_info(msg="Imported PyPSA substation", device=substation_name)
                else:
                    pass

                voltage_level_key: str = f'{substation_name}::{data["v_nom"]}'
                voltage_level: VoltageLevel | None = voltage_levels.get(voltage_level_key, None)
                if voltage_level is None:
                    voltage_level = VoltageLevel(name=voltage_level_key,
                                                 Vnom=self._finite_float(data['v_nom'], 0.0),
                                                 substation=substation)
                    self.grid.add_voltage_level(voltage_level)
                    voltage_levels[voltage_level_key] = voltage_level
                else:
                    pass
            else:
                pass
        return substations, voltage_levels

    def _get_technology(self, carrier: object) -> Technology | None:
        """
        Get or create a Technology associated with one PyPSA carrier label.

        :param carrier: PyPSA carrier value.
        :return: Corresponding VeraGrid Technology, or ``None`` for no carrier.
        """
        if isinstance(carrier, str) and carrier != '':
            technology: Technology | None = self.technologies.get(carrier, None)
            if technology is None:
                carrier_data: object | None = self.pypsa_grid.carriers.loc[carrier] \
                    if carrier in self.pypsa_grid.carriers.index else None
                reference_cost: float = 0.0
                color: str | None = None
                nice_name: object | None = None
                if carrier_data is not None:
                    reference_cost = self._finite_float(carrier_data.get('marginal_cost', 0.0), 0.0)
                    raw_color: object = carrier_data.get('color', None)
                    color = raw_color if isinstance(raw_color, str) and raw_color != '' else None
                    nice_name = carrier_data.get('nice_name', None)
                else:
                    pass
                technology = Technology(name=carrier, color=color, reference_cost=reference_cost)
                if isinstance(nice_name, str) and nice_name != '':
                    technology.name2 = nice_name
                else:
                    pass
                self.grid.add_technology(technology)
                self.technologies[carrier] = technology
                self.logger.add_info(msg="Imported PyPSA carrier as technology", device=carrier)
            else:
                pass
            return technology
        else:
            return None

    def _associate_carrier_emission(self, generator: Generator, carrier: object) -> None:
        """Associate PyPSA carrier CO2 intensity with an electrical machine.

        :param generator: VeraGrid generator receiving the emission association.
        :param carrier: PyPSA carrier label.
        :return: None.
        """
        if isinstance(carrier, str) and carrier in self.pypsa_grid.carriers.index:
            carrier_data = self.pypsa_grid.carriers.loc[carrier]
            co2_rate: float = self._finite_float(carrier_data.get('co2_emissions', 0.0), 0.0)
            if co2_rate != 0.0:
                emission: EmissionGas | None = self.emission_gases.get('CO2', None)
                if emission is None:
                    emission = EmissionGas(name='CO2')
                    self.grid.add_emission_gas(emission)
                    self.emission_gases['CO2'] = emission
                else:
                    pass
                generator.emissions.add_object(api_object=emission, val=co2_rate)
                self.logger.add_info(msg="Imported PyPSA carrier CO2 emission rate", device=generator.name)
            else:
                pass
        else:
            pass

    def _get_investment_group(self, component_name: str, discount_rate: object) -> InvestmentsGroup:
        """
        Get the VeraGrid investment group representing one PyPSA component type.

        :param component_name: PyPSA component class name.
        :param discount_rate: PyPSA annual discount rate in per-unit form.
        :return: Native VeraGrid investment group.
        """
        normalized_discount_rate: float = self._finite_float(discount_rate, 0.0)
        # PyPSA permits asset-specific discount rates. Reusing one group per
        # component would silently apply the first asset's rate to every later
        # investment, so the key includes the normalized economic assumption.
        group_key: str = f'{component_name}::{normalized_discount_rate}'
        group: InvestmentsGroup | None = self.investment_groups.get(group_key, None)
        if group is None:
            # PyPSA stores discount rates in per unit while VeraGrid displays
            # them in percent, so the conversion belongs at this boundary.
            group = InvestmentsGroup(name=f'PyPSA {component_name} investments',
                                     category=component_name,
                                     discount_rate=100.0 * normalized_discount_rate)
            self.grid.add_investments_group(group)
            self.investment_groups[group_key] = group
            self.logger.add_info(msg="Created PyPSA investment group", device=component_name)
        else:
            pass
        return group

    def _add_capacity_investment(self, data: object, device: object, component_name: str,
                                 extendable_field: str, nominal_field: str,
                                 optimum_field: str, capacity_property: str,
                                 capacity_scale: float = 1.0, cost_scale: float = 1.0) -> None:
        """
        Import a PyPSA extendable capacity as a VeraGrid investment record.

        :param data: Static PyPSA component row.
        :param device: VeraGrid physical device receiving the capacity property.
        :param component_name: PyPSA component class name.
        :param extendable_field: PyPSA boolean field enabling capacity expansion.
        :param nominal_field: Static PyPSA installed capacity field.
        :param optimum_field: Optimised PyPSA capacity field, when available.
        :param capacity_property: VeraGrid property changed by the investment.
        :param capacity_scale: Conversion from nominal PyPSA capacity to property units.
        :param cost_scale: Share of the source capital cost owned by this device.
        :return: None.
        """
        if bool(data.get(extendable_field, False)):
            nominal_capacity: float = self._finite_float(data.get(nominal_field, 0.0), 0.0)
            optimum_capacity: float = self._finite_float(data.get(optimum_field, nominal_capacity), nominal_capacity)
            target_capacity: float = optimum_capacity * capacity_scale
            capital_cost: float = self._finite_float(data.get('capital_cost', 0.0), 0.0)
            group: InvestmentsGroup = self._get_investment_group(component_name, data.get('discount_rate', 0.0))

            # An imported solved model already contains its selected capacity.
            # The record retains the expansion decision and its source cost so
            # VeraGrid investment workflows can inspect or reapply it.
            investment = Investment(device=device,
                                    name=f'{device.name} PyPSA capacity investment',
                                    CAPEX=capital_cost * optimum_capacity * cost_scale,
                                    status=True,
                                    prop=capacity_property,
                                    value=target_capacity,
                                    group=group,
                                    comment=f'Imported from PyPSA {component_name} {extendable_field}')
            self.grid.add_investment(investment)
        else:
            pass

    def _parse_buses(self) -> Dict[str, Bus]:
        """
        Parses the bus data from the PyPSA network.
        :return: a mapping from bus name to VeraGrid `Bus` objects.
        """

        by_name: Dict[str, Bus] = dict()
        for ix, data in self.pypsa_grid.buses.iterrows():
            active = self._is_active(data)
            is_slack = data['control'] == 'Slack'  # otherwise 'PQ' or 'PV'
            is_dc = data['carrier'] == 'DC'
            country_name = data.get('country', None)
            country = self.countries.get(country_name, None)
            substation_name: object = data.get('substation', None)
            substation: Substation | None = self.substations.get(substation_name, None)
            voltage_level: VoltageLevel | None = None
            if isinstance(substation_name, str) and substation_name != '':
                voltage_level_key: str = f'{substation_name}::{data["v_nom"]}'
                voltage_level = self.voltage_levels.get(voltage_level_key, None)
            else:
                pass

            # the longitude and latitude come stored in x, y depending on the projection (self.srid)
            x = data['x']
            y = data['y']
            lon, lat = self.to_latlon_converter.transform(xx=x, yy=y)
            x2, y2 = self.to_xy_converter.transform(xx=x, yy=y)
            lon = self._finite_float(lon, x)
            lat = self._finite_float(lat, y)
            x2 = self._finite_float(x2, 0.0)
            y2 = self._finite_float(y2, 0.0)

            bus = Bus(name=ix,
                      Vnom=data['v_nom'],
                      vmin=data['v_mag_pu_min'],
                      vmax=data['v_mag_pu_max'],
                      xpos=x2,
                      ypos=y2,
                      longitude=lon,
                      latitude=lat,
                      active=active,
                      is_slack=is_slack,
                      is_dc=is_dc,
                      country=country,
                      substation=substation,
                      voltage_level=voltage_level,
                      Vm0=self._finite_float(data.get('v_mag_pu_set', 1.0), 1.0))
            self.grid.add_bus(bus)
            by_name[ix] = bus

            # PyPSA uses v_mag_pu_set as a scheduled voltage target. VeraGrid
            # stores the corresponding target/initial magnitude in Vm0_prof.
            vm_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.buses_t.v_mag_pu_set,
                                                                    ix, 'bus v_mag_pu_set')
            if vm_profile is not None:
                bus.Vm0_prof.set(vm_profile)
            else:
                pass

        return by_name

    def _parse_generators(self):
        """
        Parses the generator row from the PyPSA network.
        """

        """
        'bus'
        'control'
        'type'
        'p_nom'
        'p_nom_mod'
        'p_nom_extendable'
        'p_nom_min'
        'p_nom_max'
        'p_min_pu'
        'p_max_pu'
        'p_set'
        'e_sum_min'
        'e_sum_max'
        'q_set'
        'sign'
        'carrier'
        'marginal_cost'
        'marginal_cost_quadratic'
        'active'
        'build_year'
        'lifetime'
        'capital_cost'
        'efficiency'
        'committable'
        'start_up_cost'
        'shut_down_cost'
        'stand_by_cost'
        'min_up_time'
        'min_down_time'
        'up_time_before'
        'down_time_before'
        'ramp_limit_up'
        'ramp_limit_down'
        'ramp_limit_start_up'
        'ramp_limit_shut_down'
        'weight'
        'p_nom_opt'        
        """

        for name, row in self.pypsa_grid.generators.iterrows():

            bus = self.buses[row['bus']]

            control_mode=GeneratorControlMode.V if row['control'] == 'PV' else GeneratorControlMode.Q

            # PyPSA's p_nom_min/max constrain investment; dispatch limits use p_*_pu.
            Pmin = row['p_nom'] * row['p_min_pu']
            Pmax = row['p_nom'] * row['p_max_pu']

            elm = Generator(
                name=name,
                # PyPSA uses NaN for an unspecified setpoint. VeraGrid needs a
                # finite snapshot default; the dispatchability flag/profile
                # retains whether OPF may subsequently choose its power.
                P=self._finite_float(row['p_set'], 0.0) * row['sign'],
                Q=self._finite_float(row['q_set'], 0.0) * row['sign'],
                control_mode=control_mode,
                active=row['active'],
                Snom=row['p_nom'],
                Pmin=Pmin,
                Pmax=Pmax,
                opex=row['marginal_cost'],
                Cost=row['marginal_cost'],
                Cost2=row['marginal_cost_quadratic'],
                capex=row['capital_cost'] * row['p_nom'],
                # PyPSA committable enables unit commitment; it does not say
                # whether the generator may dispatch. A finite p_set fixes P,
                # while NaN leaves the OPF dispatch variable available.
                enabled_dispatch=not math.isfinite(self._finite_float(row['p_set'], float('nan'))),
            )

            elm.Cost2 = self._finite_float(row.get('marginal_cost_quadratic', 0.0), 0.0)
            elm.startup_cost = self._finite_float(row.get('start_up_cost', 0.0), 0.0)
            elm.shutdown_cost = self._finite_float(row.get('shut_down_cost', 0.0), 0.0)
            elm.min_time_up = self._finite_float(row.get('min_up_time', 0.0), 0.0)
            elm.min_time_down = self._finite_float(row.get('min_down_time', 0.0), 0.0)
            elm.ramp_up = self._finite_float(row.get('ramp_limit_up', 1e20), 1e20)
            elm.ramp_down = self._finite_float(row.get('ramp_limit_down', 1e20), 1e20)

            self.grid.add_generator(bus=bus, api_obj=elm)
            technology: Technology | None = self._get_technology(row.get('carrier', None))
            if technology is not None:
                elm.associate_technology(technology)
            else:
                pass
            self._associate_carrier_emission(elm, row.get('carrier', None))
            self._add_capacity_investment(data=row,
                                          device=elm,
                                          component_name='Generator',
                                          extendable_field='p_nom_extendable',
                                          nominal_field='p_nom',
                                          optimum_field='p_nom_opt',
                                          capacity_property='Pmax',
                                          capacity_scale=self._finite_float(row['p_max_pu'], 1.0))

            # PyPSA omits a dynamic column when its static component value is
            # valid for every snapshot, so absence is normal and not a warning.
            p_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.p_set,
                                                                       name, 'generator p_set')
            q_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.q_set,
                                                                       name, 'generator q_set')
            p_min_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.p_min_pu,
                                                                       name, 'generator p_min_pu')
            p_max_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.p_max_pu,
                                                                       name, 'generator p_max_pu')
            cost_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.marginal_cost,
                                                                     name, 'generator marginal_cost')
            status_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.generators_t.status,
                                                                        name, 'generator status')
            maintenance_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.generators_t.maintenance, name, 'generator maintenance')

            # Convert per-unit availability into MW on the PyPSA nominal-power base.
            if p_set_profile is not None:
                elm.P_prof.set(p_set_profile * row['sign'])
                # A finite PyPSA p_set[t] fixes net P[t], therefore OPF must
                # not redispatch this device. NaN leaves that snapshot free.
                elm.enabled_dispatch_prof.set(~np.isfinite(p_set_profile))
            else:
                pass
            if q_set_profile is not None:
                elm.Q_prof.set(q_set_profile * row['sign'])
            else:
                pass
            if p_min_profile is not None:
                elm.Pmin_prof.set(p_min_profile * elm.Snom)
            else:
                pass
            if p_max_profile is not None:
                elm.Pmax_prof.set(p_max_profile * elm.Snom)
            else:
                pass
            if cost_profile is not None:
                elm.Cost_prof.set(cost_profile)
            else:
                pass
            if status_profile is not None:
                # A solved PyPSA unit-commitment status is an availability
                # replay signal. It is distinct from p_set, which fixes power.
                elm.active_prof.set(status_profile.astype(bool))
                self.logger.add_info(msg="Imported PyPSA generator commitment status", device=name)
            else:
                pass
            if maintenance_profile is not None:
                maintenance_mask: np.ndarray = maintenance_profile.astype(bool)
                active_profile: np.ndarray = elm.active_prof.toarray()
                active_profile[maintenance_mask] = False
                elm.active_prof.set(active_profile)
                self.logger.add_info(msg="Imported PyPSA generator maintenance status", device=name)
            else:
                pass

    def _parse_storage_units_battery_legacy(self):
        """
        Parses the storage units data from the PyPSA network.
        """

        for name, row in self.pypsa_grid.storage_units.iterrows():

            bus = self.buses[row['bus']]
            p_set: float = self._finite_float(row['p_set'], 0.0)
            q_set: float = self._finite_float(row['q_set'], 0.0)

            if q_set != 0.0 or p_set != 0.0:
                power_factor = p_set / math.sqrt(q_set ** 2 + p_set ** 2)
            else:
                power_factor = 0.8

            control_mode=GeneratorControlMode.V if row['control'] == 'PV' else GeneratorControlMode.Q

            # PyPSA's p_nom_min/max constrain investment; dispatch limits use p_*_pu.
            Pmin = row['p_nom'] * row['p_min_pu']
            Pmax = row['p_nom'] * row['p_max_pu']
            nominal_energy: float = self._finite_float(row.get('p_nom', 0.0), 0.0) \
                                    * self._finite_float(row.get('max_hours', 0.0), 0.0)
            initial_energy: float = self._finite_float(row.get('state_of_charge_initial', 0.0), 0.0)
            if nominal_energy > 0.0:
                initial_soc: float = min(1.0, max(0.0, initial_energy / nominal_energy))
            else:
                initial_soc = 0.8

            elm = Battery(
                name=name,
                P=p_set * row['sign'],
                power_factor=power_factor,
                control_mode=control_mode,
                Snom=row['p_nom'],
                active=row['active'],
                Pmin=Pmin,
                Pmax=Pmax,
                opex=row['marginal_cost'],
                Cost=row['marginal_cost'],
                capex=row['capital_cost'] * row['p_nom'],
                # StorageUnit uses the same static net-power setpoint rule as
                # Generator. Its p_dispatch result column is not an input flag.
                enabled_dispatch=not math.isfinite(self._finite_float(row['p_set'], float('nan'))),
                Enom=self._finite_float(row.get('p_nom', 0.0), 0.0)
                     * self._finite_float(row.get('max_hours', 0.0), 0.0),
                min_soc=0.0,
                max_soc=1.0,
                soc=initial_soc,
                charge_efficiency=self._finite_float(row.get('efficiency_store', 0.9), 0.9),
                discharge_efficiency=self._finite_float(row.get('efficiency_dispatch', 0.9), 0.9),
            )

            elm.Cost2 = row.get('marginal_cost_quadratic', 0.0)
            elm.startup_cost = row.get('start_up_cost', 0.0)
            elm.shutdown_cost = row.get('shut_down_cost', 0.0)
            elm.min_time_up = row.get('min_up_time', 0.0)
            elm.min_time_down = row.get('min_down_time', 0.0)
            elm.ramp_up = row.get('ramp_limit_up', 1e20)
            elm.ramp_down = row.get('ramp_limit_down', 1e20)

            self.grid.add_battery(bus=bus, api_obj=elm)
            # PyPSA StorageUnit inflow changes stored energy, not electrical
            # injection. When the source provides the explicit conversion, its
            # physical counterpart belongs to the existing FluidNode model.
            fluid_node: FluidNode | None = self._add_store_fluid_node(
                name=name,
                data=row,
                bus=bus,
                nominal_energy=nominal_energy,
                min_soc=0.0,
                max_soc=1.0,
                initial_energy=initial_energy,
            )
            technology: Technology | None = self._get_technology(row.get('carrier', None))
            if technology is not None:
                elm.associate_technology(technology)
            else:
                pass
            self._add_capacity_investment(data=row,
                                          device=elm,
                                          component_name='StorageUnit',
                                          extendable_field='p_nom_extendable',
                                          nominal_field='p_nom',
                                          optimum_field='p_nom_opt',
                                          capacity_property='Pmax',
                                          capacity_scale=self._finite_float(row['p_max_pu'], 1.0))

            # StorageUnit power conventions equal Generator conventions, while
            # its energy equation remains represented by the Battery device.
            p_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_set,
                                                                       name, 'storage p_set')
            q_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.q_set,
                                                                       name, 'storage q_set')
            p_min_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_min_pu,
                                                                       name, 'storage p_min_pu')
            p_max_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_max_pu,
                                                                       name, 'storage p_max_pu')
            cost_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.marginal_cost,
                                                                     name, 'storage marginal_cost')
            dispatch_set_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.p_dispatch_set, name, 'storage p_dispatch_set')
            store_set_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.p_store_set, name, 'storage p_store_set')
            inflow_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.inflow, name, 'storage inflow')
            charge_efficiency_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.efficiency_store, name, 'storage charge efficiency')
            discharge_efficiency_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.efficiency_dispatch, name, 'storage discharge efficiency')
            standing_loss_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.standing_loss, name, 'storage standing loss')

            if p_set_profile is not None:
                elm.P_prof.set(p_set_profile * row['sign'])
                # StorageUnit follows Generator's scheduled-versus-free power
                # convention. This is independent of an SoC target: a target
                # constrains energy, while free dispatch chooses the route there.
                elm.enabled_dispatch_prof.set(~np.isfinite(p_set_profile))
            else:
                pass
            if dispatch_set_profile is not None or store_set_profile is not None:
                # PyPSA constrains charge and discharge separately. Battery
                # stores net bus power, so translate their difference only for
                # snapshots where either source schedule is explicitly finite.
                dispatch_values: np.ndarray = np.zeros(self.nt, dtype=float)
                store_values: np.ndarray = np.zeros(self.nt, dtype=float)
                scheduled: np.ndarray = np.zeros(self.nt, dtype=bool)
                if dispatch_set_profile is not None:
                    dispatch_mask: np.ndarray = np.isfinite(dispatch_set_profile)
                    dispatch_values[dispatch_mask] = dispatch_set_profile[dispatch_mask]
                    scheduled |= dispatch_mask
                else:
                    pass
                if store_set_profile is not None:
                    store_mask: np.ndarray = np.isfinite(store_set_profile)
                    store_values[store_mask] = store_set_profile[store_mask]
                    scheduled |= store_mask
                else:
                    pass
                scheduled_power: np.ndarray = dispatch_values - store_values
                base_power: np.ndarray = elm.P_prof.toarray()
                base_power[scheduled] = scheduled_power[scheduled] * row['sign']
                elm.P_prof.set(base_power)
                dispatchable_profile: np.ndarray = elm.enabled_dispatch_prof.toarray()
                dispatchable_profile[scheduled] = False
                elm.enabled_dispatch_prof.set(dispatchable_profile)
                self.logger.add_info(msg="Imported PyPSA separate storage charge/discharge schedule", device=name)
            else:
                pass
            if q_set_profile is not None:
                elm.Q_prof.set(q_set_profile * row['sign'])
            else:
                pass
            if p_min_profile is not None:
                elm.Pmin_prof.set(p_min_profile * elm.Snom)
            else:
                pass
            if p_max_profile is not None:
                elm.Pmax_prof.set(p_max_profile * elm.Snom)
            else:
                pass
            if cost_profile is not None:
                elm.Cost_prof.set(cost_profile)
            else:
                pass
            volume_per_mwh: float = self._finite_float(row.get('fluid_volume_per_mwh', 0.0), 0.0)
            static_inflow: float = self._finite_float(row.get('inflow', 0.0), 0.0)
            if fluid_node is not None:
                # MW is MWh/hour. The source conversion gives m3/MWh, while
                # FluidNode inflow is m3/s, hence the division by 3600.
                fluid_node.inflow = static_inflow * volume_per_mwh / 3600.0
                if inflow_profile is not None:
                    fluid_node.inflow_prof.set(inflow_profile * volume_per_mwh / 3600.0)
                else:
                    pass
                self.logger.add_info(msg="Imported PyPSA StorageUnit inflow as FluidNode inflow", device=name)
                self.logger.add_warning(msg="PyPSA StorageUnit fluid state has no inferred pump/turbine coupling",
                                        device=name)
            elif static_inflow != 0.0 or (inflow_profile is not None and np.any(np.isfinite(inflow_profile))):
                self.logger.add_warning(msg="PyPSA StorageUnit inflow needs fluid_volume_per_mwh for FluidNode import",
                                        device=name)
            else:
                pass
            if charge_efficiency_profile is not None and not np.allclose(
                    charge_efficiency_profile, elm.charge_efficiency, equal_nan=True):
                self.logger.add_warning(msg="PyPSA StorageUnit time-varying charge efficiency not imported",
                                        device=name)
            else:
                pass
            if discharge_efficiency_profile is not None and not np.allclose(
                    discharge_efficiency_profile, elm.discharge_efficiency, equal_nan=True):
                self.logger.add_warning(msg="PyPSA StorageUnit time-varying discharge efficiency not imported",
                                        device=name)
            else:
                pass
            if standing_loss_profile is not None and np.any(np.isfinite(standing_loss_profile) &
                                                             (standing_loss_profile != 0.0)):
                self.logger.add_warning(msg="PyPSA StorageUnit time-varying standing loss not imported", device=name)
            else:
                pass
            if self._finite_float(row.get('standing_loss', 0.0), 0.0) != 0.0:
                self.logger.add_warning(msg="PyPSA StorageUnit standing loss not imported", device=name)
            else:
                pass
            state_of_charge_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.state_of_charge_set, name, 'storage state_of_charge_set')
            if state_of_charge_profile is not None:
                self._apply_soc_targets(elm, state_of_charge_profile, name)
            else:
                pass

    def _parse_stores_battery_legacy(self):
        """
        Parses the stores data from the PyPSA network.
        """
        for name, row in self.pypsa_grid.stores.iterrows():
            bus: Bus = self.buses[row['bus']]
            nominal_energy: float = self._finite_float(row['e_nom'], 0.0)
            min_soc: float = self._finite_float(row['e_min_pu'], 0.0)
            max_soc: float = self._finite_float(row['e_max_pu'], 1.0)
            initial_energy: float = self._finite_float(row['e_initial'], 0.0)

            # Store has energy limits but no converter-power nameplate. A wide
            # dispatch range preserves its energy behaviour without fabricating
            # a physical inverter rating that PyPSA never supplied.
            if nominal_energy > 0.0:
                initial_soc: float = initial_energy / nominal_energy
            else:
                initial_soc = 0.8
            if initial_soc < min_soc:
                initial_soc = min_soc
            elif initial_soc > max_soc:
                initial_soc = max_soc
            else:
                pass

            battery = Battery(name=name,
                              P=self._finite_float(row['p_set'], 0.0) * row['sign'],
                              Q=self._finite_float(row['q_set'], 0.0) * row['sign'],
                              Pmin=-9999.0,
                              Pmax=9999.0,
                              Snom=9999.0,
                              Enom=nominal_energy,
                              min_soc=min_soc,
                              max_soc=max_soc,
                              soc=initial_soc,
                              active=self._is_active(row),
                              Cost=self._finite_float(row['marginal_cost'], 0.0),
                              opex=self._finite_float(row['marginal_cost'], 0.0),
                              capex=self._finite_float(row['capital_cost'], 0.0),
                              enabled_dispatch=not math.isfinite(self._finite_float(row['p_set'], float('nan'))))
            self.grid.add_battery(bus=bus, api_obj=battery)
            fluid_node: FluidNode | None = self._add_store_fluid_node(name=name,
                                                                        data=row,
                                                                        bus=bus,
                                                                        nominal_energy=nominal_energy,
                                                                        min_soc=min_soc,
                                                                        max_soc=max_soc,
                                                                        initial_energy=initial_energy)
            technology: Technology | None = self._get_technology(row.get('carrier', None))
            if technology is not None:
                battery.associate_technology(technology)
            else:
                pass
            self._add_capacity_investment(data=row,
                                          device=battery,
                                          component_name='Store',
                                          extendable_field='e_nom_extendable',
                                          nominal_field='e_nom',
                                          optimum_field='e_nom_opt',
                                          capacity_property='Enom')

            # Scheduled Store injections retain their sign convention and are
            # available to VeraGrid dispatch studies as Battery P/Q profiles.
            p_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.p_set,
                                                                       name, 'store p_set')
            q_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.q_set,
                                                                       name, 'store q_set')
            cost_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.marginal_cost,
                                                                     name, 'store marginal_cost')
            min_energy_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.e_min_pu, name, 'store e_min_pu')
            max_energy_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.e_max_pu, name, 'store e_max_pu')
            standing_loss_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.standing_loss, name, 'store standing loss')
            if p_set_profile is not None:
                battery.P_prof.set(p_set_profile * row['sign'])
                # Store p_set is a net MW schedule. Finite points are fixed;
                # NaN points remain available to dispatch optimisation.
                battery.enabled_dispatch_prof.set(~np.isfinite(p_set_profile))
            else:
                pass
            if q_set_profile is not None:
                battery.Q_prof.set(q_set_profile * row['sign'])
            else:
                pass
            if cost_profile is not None:
                battery.Cost_prof.set(cost_profile)
            else:
                pass

            if min_energy_profile is not None and not np.allclose(min_energy_profile, min_soc, equal_nan=True):
                self.logger.add_warning(msg="PyPSA Store time-varying minimum energy not imported", device=name)
            else:
                pass
            if max_energy_profile is not None and not np.allclose(max_energy_profile, max_soc, equal_nan=True):
                self.logger.add_warning(msg="PyPSA Store time-varying maximum energy not imported", device=name)
            else:
                pass

            # Battery has no standing-loss property. Report the omission rather
            # than interpreting a time-step-dependent loss as cable physics.
            if self._finite_float(row['standing_loss'], 0.0) != 0.0:
                self.logger.add_warning(msg="PyPSA Store standing loss not imported", device=name)
            else:
                pass
            if standing_loss_profile is not None and np.any(np.isfinite(standing_loss_profile) &
                                                             (standing_loss_profile != 0.0)):
                self.logger.add_warning(msg="PyPSA Store time-varying standing loss not imported", device=name)
            else:
                pass
            energy_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.e_set,
                                                                        name, 'store e_set')
            if energy_profile is not None:
                self._apply_soc_targets(battery, energy_profile, name)
                if fluid_node is not None and nominal_energy > 0.0:
                    fluid_target_soc: np.ndarray = energy_profile / nominal_energy
                    fluid_target_mask: np.ndarray = np.isfinite(fluid_target_soc)
                    fluid_min_profile: np.ndarray = np.full(self.nt, fluid_node.min_soc, dtype=float)
                    fluid_max_profile: np.ndarray = np.full(self.nt, fluid_node.max_soc, dtype=float)

                    # The linked representations share the same normalized
                    # target envelope, while their physical units remain local.
                    fluid_min_profile[fluid_target_mask] = fluid_target_soc[fluid_target_mask]
                    fluid_max_profile[fluid_target_mask] = fluid_target_soc[fluid_target_mask]
                    fluid_node.min_soc_prof.set(fluid_min_profile)
                    fluid_node.max_soc_prof.set(fluid_max_profile)
                else:
                    pass
            else:
                pass

    def _apply_virtual_storage_schedule(self, discharge: Generator, charge: Generator,
                                        net_power: np.ndarray, device_name: str) -> None:
        """Split a PyPSA net-power schedule between fluid conversion machines.

        :param discharge: Positive-power turbine generator.
        :param charge: Negative-power pump generator.
        :param net_power: PyPSA net electrical power in MW.
        :param device_name: Source device name for logging.
        :return: None.
        """
        scheduled: np.ndarray = np.isfinite(net_power)
        discharge_power: np.ndarray = np.zeros(self.nt, dtype=float)
        charge_power: np.ndarray = np.zeros(self.nt, dtype=float)
        discharge_power[scheduled] = np.maximum(net_power[scheduled], 0.0)
        charge_power[scheduled] = np.minimum(net_power[scheduled], 0.0)
        discharge.P_prof.set(discharge_power)
        charge.P_prof.set(charge_power)
        discharge.enabled_dispatch_prof.set(~scheduled)
        charge.enabled_dispatch_prof.set(~scheduled)
        self.logger.add_info(msg="Imported PyPSA storage net-power schedule through fluid converters", device=device_name)

    def _register_fluid_node_at_bus(self, source_bus_name: str, node: FluidNode) -> None:
        """Register a virtual-fluid state under its source PyPSA bus.

        :param source_bus_name: PyPSA bus carrying the energy store.
        :param node: Imported VeraGrid FluidNode.
        :return: None.
        """
        nodes: list[FluidNode] | None = self.fluid_nodes_by_bus.get(source_bus_name, None)
        if nodes is None:
            nodes = list()
            self.fluid_nodes_by_bus[source_bus_name] = nodes
        else:
            pass
        nodes.append(node)

    def _apply_fluid_energy_targets(self, node: FluidNode, energy_targets: np.ndarray,
                                    nominal_energy: float, device_name: str) -> None:
        """Turn PyPSA energy targets into native FluidNode bounds.

        :param node: Fluid state to constrain.
        :param energy_targets: MWh targets, with NaN denoting no target.
        :param nominal_energy: Source energy capacity in MWh.
        :param device_name: Source device name for logging.
        :return: None.
        """
        if nominal_energy > 0.0:
            target_soc: np.ndarray = energy_targets / nominal_energy
            target_mask: np.ndarray = np.isfinite(target_soc)
            min_profile: np.ndarray = np.full(self.nt, node.min_soc, dtype=float)
            max_profile: np.ndarray = np.full(self.nt, node.max_soc, dtype=float)
            min_profile[target_mask] = target_soc[target_mask]
            max_profile[target_mask] = target_soc[target_mask]
            node.min_soc_prof.set(min_profile)
            node.max_soc_prof.set(max_profile)
            self.logger.add_info(msg="Imported PyPSA energy targets as FluidNode bounds", device=device_name)
        else:
            self.logger.add_warning(msg="PyPSA energy targets ignored because nominal energy is zero", device=device_name)

    def _parse_storage_units(self) -> None:
        """Parse PyPSA StorageUnits as native fluid energy stores."""
        for name, row in self.pypsa_grid.storage_units.iterrows():
            bus: Bus = self.buses[row['bus']]
            p_nom: float = self._finite_float(row.get('p_nom', 0.0), 0.0)
            p_min: float = p_nom * self._finite_float(row.get('p_min_pu', -1.0), -1.0)
            p_max: float = p_nom * self._finite_float(row.get('p_max_pu', 1.0), 1.0)
            nominal_energy: float = p_nom * self._finite_float(row.get('max_hours', 0.0), 0.0)
            initial_energy: float = self._finite_float(row.get('state_of_charge_initial', 0.0), 0.0)
            discharge_rate: float = max(p_max, 0.0)
            charge_rate: float = max(-p_min, 0.0)
            node, discharge, charge, turbine, pump = self._add_virtual_fluid_storage(
                name=name, bus=bus, nominal_energy=nominal_energy, min_soc=0.0, max_soc=1.0,
                initial_energy=initial_energy, charge_rate=charge_rate, discharge_rate=discharge_rate,
                charge_efficiency=self._finite_float(row.get('efficiency_store', 1.0), 1.0),
                discharge_efficiency=self._finite_float(row.get('efficiency_dispatch', 1.0), 1.0),
                active=self._is_active(row), cost=self._finite_float(row.get('marginal_cost', 0.0), 0.0))
            self._register_fluid_node_at_bus(str(row['bus']), node)
            technology: Technology | None = self._get_technology(row.get('carrier', None))
            if technology is not None:
                discharge.associate_technology(technology)
                charge.associate_technology(technology)
            else:
                pass
            self._associate_carrier_emission(discharge, row.get('carrier', None))
            self._add_capacity_investment(data=row, device=discharge, component_name='StorageUnit',
                                          extendable_field='p_nom_extendable', nominal_field='p_nom',
                                          optimum_field='p_nom_opt', capacity_property='Pmax',
                                          capacity_scale=self._finite_float(row.get('p_max_pu', 1.0), 1.0))
            p_set: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_set, name, 'storage p_set')
            dispatch_set: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_dispatch_set, name, 'storage p_dispatch_set')
            store_set: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.p_store_set, name, 'storage p_store_set')
            if dispatch_set is not None or store_set is not None:
                net_schedule: np.ndarray = np.zeros(self.nt, dtype=float)
                schedule_mask: np.ndarray = np.zeros(self.nt, dtype=bool)
                if dispatch_set is not None:
                    dispatch_mask: np.ndarray = np.isfinite(dispatch_set)
                    net_schedule[dispatch_mask] += dispatch_set[dispatch_mask]
                    schedule_mask |= dispatch_mask
                else:
                    pass
                if store_set is not None:
                    store_mask: np.ndarray = np.isfinite(store_set)
                    net_schedule[store_mask] -= store_set[store_mask]
                    schedule_mask |= store_mask
                else:
                    pass
                net_schedule[~schedule_mask] = np.nan
                self._apply_virtual_storage_schedule(discharge, charge, net_schedule, name)
            elif p_set is not None:
                self._apply_virtual_storage_schedule(discharge, charge, p_set, name)
            else:
                pass
            p_min_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.p_min_pu, name, 'storage p_min_pu')
            p_max_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.p_max_pu, name, 'storage p_max_pu')
            cost_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.marginal_cost, name, 'storage marginal_cost')
            if p_min_profile is not None:
                charge.Pmin_prof.set(p_nom * p_min_profile)
                pump.max_flow_rate_prof.set(-p_nom * p_min_profile * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0)
            else:
                pass
            if p_max_profile is not None:
                discharge.Pmax_prof.set(p_nom * p_max_profile)
                turbine.max_flow_rate_prof.set(p_nom * p_max_profile * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0)
            else:
                pass
            if cost_profile is not None:
                discharge.Cost_prof.set(cost_profile)
            else:
                pass
            inflow: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.inflow, name, 'storage inflow')
            if inflow is not None:
                node.inflow_prof.set(inflow * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0)
            else:
                node.inflow = self._finite_float(row.get('inflow', 0.0), 0.0) * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0
            standing_loss: float = self._finite_float(row.get('standing_loss', 0.0), 0.0)
            node.loss_factor = max(0.0, standing_loss)
            standing_loss_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.standing_loss, name, 'storage standing loss')
            if standing_loss_profile is not None:
                loss_factor_profile: np.ndarray = np.full(self.nt, node.loss_factor, dtype=float)
                valid_loss: np.ndarray = np.isfinite(standing_loss_profile)
                loss_factor_profile[valid_loss] = np.maximum(0.0, standing_loss_profile[valid_loss])
                node.loss_factor_prof.set(loss_factor_profile)
            else:
                pass
            charge_efficiency_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.efficiency_store, name, 'storage charge efficiency')
            discharge_efficiency_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.efficiency_dispatch, name, 'storage discharge efficiency')
            if charge_efficiency_profile is not None and not np.allclose(
                    charge_efficiency_profile, self._finite_float(row.get('efficiency_store', 1.0), 1.0), equal_nan=True):
                pump.efficiency_prof.set(charge_efficiency_profile)
                self.logger.add_info(msg="Imported PyPSA StorageUnit time-varying charge efficiency", device=name)
            else:
                pass
            if discharge_efficiency_profile is not None and not np.allclose(
                    discharge_efficiency_profile, self._finite_float(row.get('efficiency_dispatch', 1.0), 1.0), equal_nan=True):
                turbine.efficiency_prof.set(discharge_efficiency_profile)
                self.logger.add_info(msg="Imported PyPSA StorageUnit time-varying discharge efficiency", device=name)
            else:
                pass
            node.spillage_cost = self._finite_float(row.get('spill_cost', node.spillage_cost), node.spillage_cost)
            spill_cost_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.storage_units_t.spill_cost, name, 'storage spill cost')
            if spill_cost_profile is not None:
                node.spillage_cost_prof.set(spill_cost_profile)
                self.logger.add_info(msg="Imported PyPSA StorageUnit spill-cost profile", device=name)
            else:
                pass
            target: np.ndarray | None = self._get_time_series(self.pypsa_grid.storage_units_t.state_of_charge_set, name, 'storage state_of_charge_set')
            if target is not None:
                self._apply_fluid_energy_targets(node, target, nominal_energy, name)
            else:
                pass

    def _parse_stores(self) -> None:
        """Parse PyPSA Stores as native fluid energy stores."""
        for name, row in self.pypsa_grid.stores.iterrows():
            bus: Bus = self.buses[row['bus']]
            nominal_energy: float = self._finite_float(row.get('e_nom', 0.0), 0.0)
            min_soc: float = self._finite_float(row.get('e_min_pu', 0.0), 0.0)
            max_soc: float = self._finite_float(row.get('e_max_pu', 1.0), 1.0)
            initial_energy: float = self._finite_float(row.get('e_initial', 0.0), 0.0)
            p_set: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.p_set, name, 'store p_set')
            rate: float = 9999.0
            if p_set is not None and np.any(np.isfinite(p_set)):
                rate = max(rate, float(np.nanmax(np.abs(p_set))))
            else:
                pass
            node, discharge, charge, turbine, pump = self._add_virtual_fluid_storage(
                name=name, bus=bus, nominal_energy=nominal_energy, min_soc=min_soc, max_soc=max_soc,
                initial_energy=initial_energy, charge_rate=rate, discharge_rate=rate,
                charge_efficiency=1.0, discharge_efficiency=1.0, active=self._is_active(row),
                cost=self._finite_float(row.get('marginal_cost', 0.0), 0.0))
            self._register_fluid_node_at_bus(str(row['bus']), node)
            technology: Technology | None = self._get_technology(row.get('carrier', None))
            if technology is not None:
                discharge.associate_technology(technology)
                charge.associate_technology(technology)
            else:
                pass
            self._associate_carrier_emission(discharge, row.get('carrier', None))
            self._add_capacity_investment(data=row, device=node, component_name='Store',
                                          extendable_field='e_nom_extendable', nominal_field='e_nom',
                                          optimum_field='e_nom_opt', capacity_property='max_level')
            if p_set is not None:
                self._apply_virtual_storage_schedule(discharge, charge, p_set, name)
            else:
                pass
            standing_loss: float = self._finite_float(row.get('standing_loss', 0.0), 0.0)
            node.loss_factor = max(0.0, standing_loss)
            standing_loss_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.standing_loss, name, 'store standing loss')
            if standing_loss_profile is not None:
                loss_factor_profile: np.ndarray = np.full(self.nt, node.loss_factor, dtype=float)
                valid_loss: np.ndarray = np.isfinite(standing_loss_profile)
                loss_factor_profile[valid_loss] = np.maximum(0.0, standing_loss_profile[valid_loss])
                node.loss_factor_prof.set(loss_factor_profile)
            else:
                pass
            min_soc_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.e_min_pu, name, 'store e_min_pu')
            max_soc_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.stores_t.e_max_pu, name, 'store e_max_pu')
            if min_soc_profile is not None:
                node.min_soc_prof.set(min_soc_profile)
                self.logger.add_info(msg="Imported PyPSA Store minimum-energy profile", device=name)
            else:
                pass
            if max_soc_profile is not None:
                node.max_soc_prof.set(max_soc_profile)
                self.logger.add_info(msg="Imported PyPSA Store maximum-energy profile", device=name)
            else:
                pass
            inflow: np.ndarray | None = self._get_time_series(self.pypsa_grid.stores_t.e_set, name, 'store e_set')
            if inflow is not None:
                self._apply_fluid_energy_targets(node, inflow, nominal_energy, name)
            else:
                pass

    def _parse_global_constraints(self) -> None:
        """
        Report PyPSA global constraints not represented by a circuit device.

        :return: None.
        """
        for name, data in self.pypsa_grid.global_constraints.iterrows():
            # Global optimisation constraints have no physical object to attach
            # to in VeraGrid. A warning keeps the import electrically usable
            # while making the omitted planning semantics explicit.
            self.logger.add_warning(msg=f"PyPSA global constraint not imported: {data['type']}", device=name)

    def _parse_loads(self):
        """
        Parses the load data from the PyPSA network.
        """
        for ix, data in self.pypsa_grid.loads.iterrows():
            bus = self.buses[data['bus']]
            active = self._is_active(data)
            load = Load(name=ix,
                        P=self._finite_float(data['p_set'], 0.0),
                        Q=self._finite_float(data['q_set'], 0.0),
                        active=active)
            self.grid.add_load(bus, load)
            technology: Technology | None = self._get_technology(data.get('carrier', None))
            if technology is not None:
                load.associate_technology(technology)
            else:
                pass
            try:
                P_prof = self.pypsa_grid.loads_t.p_set[ix].to_numpy()
                Q_prof = self.pypsa_grid.loads_t.q_set[ix].to_numpy()
                load.active_prof.set(np.ones(self.nt, dtype=bool))
                load.P_prof.set(P_prof)
                load.Q_prof.set(Q_prof)
            except KeyError:
                pass

    def _parse_line_types(self) -> Dict[str, SequenceLineType]:
        """
        Parses the line type data from the PyPSA network.
        :return: a mapping from type name to VeraGrid `SequenceLineType` objects.
        """
        by_name: Dict[str, SequenceLineType] = dict()
        for ix, data in self.pypsa_grid.line_types.iterrows():
            # Compute shunt susceptance in S/km from shunt capacitance in nF/km.
            omega = 2 * math.pi * data['f_nom']  # Hz
            b = data['c_per_length'] * omega * 1e-3  # in uS
            kind = SequenceLineType(name=ix, Imax=data['i_nom'], R=data['r_per_length'], X=data['x_per_length'], B=b)
            self.grid.add_sequence_line(kind)
            by_name[ix] = kind
        return by_name

    def _parse_lines(self):
        """
        Parses the line data from the PyPSA network.
        """
        w = 2.0 * np.pi * self.grid.fBase
        for ix, row in self.pypsa_grid.lines.iterrows():
            from_bus = self.buses[row['bus0']]
            to_bus = self.buses[row['bus1']]
            parallel_multiplier: float = self._finite_float(row['num_parallel'], 0.0)
            if parallel_multiplier <= 0.0:
                # Zero-capacity type placeholders occur in simplified PyPSA-Eur
                # networks. Do not invent a conducting branch where PyPSA has
                # no parallel conductor at all.
                self.logger.add_info(msg="Skipped PyPSA line with no parallel circuits", device=ix)
                copy_count: int = 0
            elif math.isclose(parallel_multiplier, round(parallel_multiplier)):
                # Integer multiplicity means physically separate identical
                # circuits. Preserve that topology with one Line per circuit.
                copy_count = int(round(parallel_multiplier))
            else:
                # Network reduction can create fractional equivalent circuit
                # counts. One scaled Line is the exact electrical equivalent.
                copy_count = 1
            length = row['length']
            status = BuildStatus.Commissioned
            name = row.get('name', ix)

            if copy_count > 1:
                # More than onle line, make a group for later...
                group = BranchGroup(name=name)
                self.grid.add_branch_group(group)

                rate = row['s_nom'] * row['s_max_pu'] / copy_count
            else:
                group = None
                rate = row['s_nom'] * row['s_max_pu']

            # PyPSA s_max_pu is the operational thermal limit. It belongs in
            # VeraGrid's branch rate, unlike s_nom_min/max investment bounds.
            rate_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.lines_t.s_max_pu,
                                                                      ix, 'line s_max_pu')

            for i in range(copy_count):
                circuit_name: str = f'{name}-{i + 1}' if copy_count > 1 else name
                elm = Line(
                    bus_from=from_bus,
                    bus_to=to_bus,
                    name=circuit_name,
                    code=circuit_name,
                    active=bool(row['active']),
                    length=length,
                    rate=rate,
                    opex=row['capital_cost'],
                    build_status=status
                )

                if group is not None:
                    elm.group = group

                template = self.line_types.get(row['type'], None)
                if template is None:
                    elm.R = row['r']
                    elm.X = row['x']
                    elm.B = row['b']
                    elm.fill_design_properties(
                        r_ohm=row['r'],
                        x_ohm=row['x'],
                        c_nf=row['b'] / w * 1e9,
                        freq=self.grid.fBase,
                        length=length,
                        Imax=0,
                        Sbase=self.grid.Sbase,
                    )
                    elm.rate = rate
                else:
                    elm.apply_template(obj=template, Sbase=self.grid.Sbase, freq=self.grid.fBase)

                    if parallel_multiplier != float(copy_count):
                        # A fractional number of identical circuits has series
                        # impedance inversely proportional to multiplicity and
                        # shunt admittance directly proportional to it.
                        elm.R /= parallel_multiplier
                        elm.X /= parallel_multiplier
                        elm.B *= parallel_multiplier
                        elm.R0 /= parallel_multiplier
                        elm.X0 /= parallel_multiplier
                        elm.B0 *= parallel_multiplier

                # A PyPSA line type supplies impedance, but source-network
                # thermal limits retain precedence over a template ampacity.
                if rate > 0.0:
                    elm.rate = rate
                elif template is not None:
                    elm.rate *= parallel_multiplier / copy_count
                else:
                    elm.rate = rate
                if rate_profile is not None:
                    elm.rate_prof.set(rate_profile * row['s_nom'] / copy_count)
                else:
                    pass

                self.grid.add_line(elm)
                self._add_capacity_investment(data=row,
                                              device=elm,
                                              component_name='Line',
                                              extendable_field='s_nom_extendable',
                                              nominal_field='s_nom',
                                              optimum_field='s_nom_opt',
                                              capacity_property='rate',
                                              capacity_scale=self._finite_float(row['s_max_pu'], 1.0) / copy_count,
                                              cost_scale=1.0 / copy_count)

    def _get_link_output_columns(self, data: object) -> list[str]:
        """
        Find populated PyPSA Link output-bus columns after ``bus1``.

        :param data: Static PyPSA Link row.
        :return: Populated output column names in numerical column order.
        """
        output_columns: list[str] = list()
        for raw_column in data.index:
            column: str = str(raw_column)
            if column.startswith('bus') and column not in ('bus0', 'bus1'):
                bus_name: object = data[column]
                # Checking the parsed bus mapping rejects PyPSA's empty/NaN
                # extension columns without guessing from their string form.
                if bus_name in self.buses:
                    output_columns.append(column)
                else:
                    pass
            else:
                pass
        return output_columns

    def _parse_multi_terminal_hvdc_link(self, name: str, data: object,
                                        extra_output_columns: list[str]) -> None:
        """
        Approximate a multi-output electrical PyPSA Link by an HVDC star.

        :param name: PyPSA Link name.
        :param data: Static PyPSA Link row.
        :param extra_output_columns: Populated PyPSA output columns after ``bus1``.
        :return: None.
        """
        from_bus: Bus = self.buses[data['bus0']]
        nominal_power: float = self._finite_float(data['p_nom'], 0.0)
        p_min: float = nominal_power * self._finite_float(data['p_min_pu'], -1.0)
        p_max: float = nominal_power * self._finite_float(data['p_max_pu'], 1.0)
        input_rate: float = max(abs(p_min), abs(p_max))
        p_set: float = self._finite_float(data['p_set'], 0.0)
        active: bool = self._is_active(data)
        hub_name: str = f'{name}::PyPSA Link hub'

        # The artificial DC bus is an algebraic junction only. It is not a
        # claim that PyPSA provided a physical converter station or cable.
        hub = Bus(name=hub_name,
                  Vnom=from_bus.Vnom,
                  xpos=from_bus.x,
                  ypos=from_bus.y,
                  longitude=from_bus.longitude,
                  latitude=from_bus.latitude,
                  active=active,
                  is_dc=True)
        self.grid.add_bus(hub)
        self.buses[hub_name] = hub

        # The input branch owns PyPSA's single dispatch variable p0. Its rate
        # therefore uses the original p_nom and bidirectional p_*_pu interval.
        input_hvdc = HvdcLine(bus_from=from_bus,
                              bus_to=hub,
                              name=f'{name}::input',
                              active=active,
                              rate=input_rate,
                              Pset=p_set,
                              opex=self._finite_float(data['marginal_cost'], 0.0),
                              capex=self._finite_float(data['capital_cost'], 0.0),
                              length=0.0)
        self.grid.add_hvdc(input_hvdc)

        # PyPSA defines bus1 as the first output. Later busN columns have an
        # efficiencyN companion and are fixed-ratio outputs of the same p0.
        output_columns: list[str] = list()
        output_columns.append('bus1')
        for column in extra_output_columns:
            output_columns.append(column)

        p_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_set,
                                                                   name, 'multi-terminal link p_set')
        p_min_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_min_pu,
                                                                   name, 'multi-terminal link p_min_pu')
        p_max_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_max_pu,
                                                                   name, 'multi-terminal link p_max_pu')
        if p_set_profile is not None:
            input_hvdc.Pset_prof.set(p_set_profile)
        else:
            pass
        if p_min_profile is not None and p_max_profile is not None:
            input_hvdc.rate_prof.set(nominal_power * np.maximum(np.abs(p_min_profile), np.abs(p_max_profile)))
        else:
            pass

        total_efficiency: float = 0.0
        for output_column in output_columns:
            output_bus: Bus = self.buses[data[output_column]]
            suffix: str = output_column.removeprefix('bus')
            efficiency_column: str = 'efficiency' if suffix == '1' else f'efficiency{suffix}'
            efficiency: float = self._finite_float(data[efficiency_column], 1.0)
            total_efficiency += efficiency

            # Scaling Pset and rate by efficiency preserves both the source
            # reference schedule and its relative transfer envelope. The star
            # remains dispatchable because it is an electrical approximation;
            # a fresh OPF can redistribute at the hub, so it is not a replacement
            # for PyPSA's one-variable fixed-ratio process constraint.
            output_hvdc = HvdcLine(bus_from=hub,
                                   bus_to=output_bus,
                                   name=f'{name}::{output_column}',
                                   active=active,
                                   rate=abs(efficiency) * input_rate,
                                   Pset=efficiency * p_set,
                                   length=0.0)
            self.grid.add_hvdc(output_hvdc)
            if p_set_profile is not None:
                output_hvdc.Pset_prof.set(efficiency * p_set_profile)
            else:
                pass
            if p_min_profile is not None and p_max_profile is not None:
                output_hvdc.rate_prof.set(abs(efficiency) * nominal_power
                                          * np.maximum(np.abs(p_min_profile), np.abs(p_max_profile)))
            else:
                pass

        # A physical electrical star requires its output powers to sum to its
        # input power. PyPSA also uses Links for multi-carrier processes, whose
        # efficiencies need not satisfy that condition, so flag the mismatch.
        if not math.isclose(total_efficiency, 1.0):
            self.logger.add_warning(msg="Multi-terminal PyPSA Link efficiency sum is not an electrical HVDC balance",
                                    device=name)
        else:
            pass
        self.logger.add_warning(msg="Multi-terminal PyPSA Link imported as rate-scaled HVDC star", device=name)

    def _parse_fluid_link(self, name: str, data: object) -> bool:
        """Import a non-electric carrier Link between two virtual-fluid states.

        :param name: PyPSA Link name.
        :param data: Static PyPSA Link row.
        :return: ``True`` when a FluidPath was created.
        """
        source_name: str = str(data['bus0'])
        target_name: str = str(data['bus1'])
        source_carrier: str = str(self.pypsa_grid.buses.loc[source_name].get('carrier', '')).lower()
        target_carrier: str = str(self.pypsa_grid.buses.loc[target_name].get('carrier', '')).lower()
        electric_carriers: set[str] = {'', 'ac', 'dc', 'electricity', 'hvdc'}
        if source_carrier in electric_carriers or target_carrier in electric_carriers:
            self.logger.add_warning(msg="PyPSA electrical-to-fluid Link requires P2X or turbine conversion", device=name)
            return False
        else:
            pass
        source_nodes: list[FluidNode] | None = self.fluid_nodes_by_bus.get(source_name, None)
        target_nodes: list[FluidNode] | None = self.fluid_nodes_by_bus.get(target_name, None)
        if source_nodes is not None and target_nodes is not None and len(source_nodes) == 1 and len(target_nodes) == 1:
            nominal_power: float = self._finite_float(data.get('p_nom', 0.0), 0.0)
            min_flow: float = nominal_power * self._finite_float(data.get('p_min_pu', 0.0), 0.0) \
                              * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0
            max_flow: float = nominal_power * self._finite_float(data.get('p_max_pu', 1.0), 1.0) \
                              * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0
            path = FluidPath(name=name,
                             source=source_nodes[0],
                             target=target_nodes[0],
                             min_flow=min_flow,
                             max_flow=max_flow,
                             loss_factor=max(0.0, 1.0 - self._finite_float(data.get('efficiency', 1.0), 1.0)),
                             build_status=BuildStatus.Commissioned)
            self.grid.add_fluid_path(path)
            efficiency_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.links_t.efficiency, name, 'fluid Link efficiency')
            p_min_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.links_t.p_min_pu, name, 'fluid Link p_min_pu')
            p_max_profile: np.ndarray | None = self._get_time_series(
                self.pypsa_grid.links_t.p_max_pu, name, 'fluid Link p_max_pu')
            if efficiency_profile is not None:
                path.loss_factor_prof.set(np.maximum(0.0, 1.0 - efficiency_profile))
            else:
                pass
            if p_min_profile is not None:
                path.min_flow_prof.set(nominal_power * p_min_profile * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0)
            else:
                pass
            if p_max_profile is not None:
                path.max_flow_prof.set(nominal_power * p_max_profile * self.VIRTUAL_FLUID_VOLUME_PER_MWH / 3600.0)
            else:
                pass
            self.logger.add_info(msg="Imported non-electric PyPSA Link as FluidPath", device=name)
            return True
        else:
            self.logger.add_warning(msg="Non-electric PyPSA Link has no unique FluidNode endpoints", device=name)
            return False

    def _parse_hvdc(self):
        """
        Parses the HVDC data from the PyPSA network.
        """
        for ix, data in self.pypsa_grid.links.iterrows():
            from_bus = self.buses[data['bus0']]
            to_bus = self.buses[data['bus1']]
            carrier = str(data['carrier']).lower()
            extra_output_columns: list[str] = self._get_link_output_columns(data)
            if carrier in ['', 'dc', 'hvdc'] and len(extra_output_columns) > 0:
                self._parse_multi_terminal_hvdc_link(ix, data, extra_output_columns)
            elif carrier in ['', 'dc', 'hvdc']:
                active = self._is_active(data)
                nominal_power: float = self._finite_float(data['p_nom'], 0.0)
                p_min: float = nominal_power * self._finite_float(data['p_min_pu'], -1.0)
                p_max: float = nominal_power * self._finite_float(data['p_max_pu'], 1.0)
                rate: float = max(abs(p_min), abs(p_max))

                # HvdcLine has one symmetric rating. Preserve the largest
                # allowed PyPSA transfer and report an asymmetric interval
                # rather than silently claiming an exact representation.
                if not math.isclose(abs(p_min), abs(p_max)):
                    self.logger.add_warning(msg="Asymmetric PyPSA Link limits approximated by HVDC rating", device=ix)
                else:
                    pass
                if not math.isclose(self._finite_float(data['efficiency'], 1.0), 1.0):
                    self.logger.add_warning(msg="PyPSA Link efficiency not converted to cable resistance", device=ix)
                else:
                    pass

                hvdc = HvdcLine(bus_from=from_bus,
                                bus_to=to_bus,
                                name=ix,
                                active=active,
                                rate=rate,
                                Pset=self._finite_float(data['p_set'], 0.0),
                                opex=self._finite_float(data['marginal_cost'], 0.0),
                                capex=self._finite_float(data['capital_cost'], 0.0),
                                length=self._finite_float(data['length'], 0.0))
                self.grid.add_hvdc(hvdc)
                self._add_capacity_investment(data=data,
                                              device=hvdc,
                                              component_name='Link',
                                              extendable_field='p_nom_extendable',
                                              nominal_field='p_nom',
                                              optimum_field='p_nom_opt',
                                              capacity_property='rate',
                                              capacity_scale=max(abs(self._finite_float(data['p_min_pu'], -1.0)),
                                                                 abs(self._finite_float(data['p_max_pu'], 1.0))))

                # Link time-series setpoints and transfer envelopes remain
                # useful despite being an aggregate, not cable-physics model.
                p_set_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_set,
                                                                           ix, 'link p_set')
                p_min_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_min_pu,
                                                                           ix, 'link p_min_pu')
                p_max_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.p_max_pu,
                                                                           ix, 'link p_max_pu')
                cost_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.marginal_cost,
                                                                         ix, 'link marginal_cost')
                status_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.links_t.status,
                                                                           ix, 'link status')
                if p_set_profile is not None:
                    hvdc.Pset_prof.set(p_set_profile)
                else:
                    pass
                if p_min_profile is not None and p_max_profile is not None:
                    hvdc.rate_prof.set(nominal_power * np.maximum(np.abs(p_min_profile), np.abs(p_max_profile)))
                else:
                    pass
                if cost_profile is not None:
                    hvdc.Cost_prof.set(cost_profile)
                else:
                    pass
                if status_profile is not None:
                    hvdc.active_prof.set(status_profile.astype(bool))
                else:
                    pass
            else:
                self._parse_fluid_link(ix, data)

    def _parse_transformer_types(self) -> Dict[str, TransformerType]:
        """
        Parses the transformer type data from the PyPSA network.
        :return: a mapping from type name to VeraGrid `TransformerType` objects.
        """
        by_name: Dict[str, TransformerType] = dict()
        for ix, data in self.pypsa_grid.transformer_types.iterrows():
            kind = TransformerType(name=str(ix),
                                   hv_nominal_voltage=data['v_nom_0'],
                                   lv_nominal_voltage=data['v_nom_1'],
                                   nominal_power=data['s_nom'],
                                   iron_losses=data['pfe'],
                                   no_load_current=data['i0'],
                                   short_circuit_voltage=data['vsc'])
            self.grid.add_transformer_type(kind)
            by_name[ix] = kind
        return by_name

    def _parse_transformers(self):
        """
        Parses the transformer data from the PyPSA network.
        """
        for ix, data in self.pypsa_grid.transformers.iterrows():
            from_bus = self.buses[data['bus0']]
            to_bus = self.buses[data['bus1']]
            proto = Transformer2W(bus_from=from_bus,
                                  bus_to=to_bus,
                                  name=f'{ix}-proto',
                                  tap_module=data['tap_ratio'],
                                  # PyPSA declares phase shifts in degrees;
                                  # VeraGrid controllable phase taps use radians.
                                  tap_phase=math.radians(self._finite_float(data['phase_shift'], 0.0)),
                                  tap_phase_min=math.radians(self._finite_float(data.get('phase_shift_min', -360.0), -360.0)),
                                  tap_phase_max=math.radians(self._finite_float(data.get('phase_shift_max', 360.0), 360.0)),
                                  active=self._is_active(data),
                                  opex=self._finite_float(data.get('capital_cost', 0.0), 0.0))

            copy_count = int(data['num_parallel'])
            rate_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.transformers_t.s_max_pu,
                                                                      ix, 'transformer s_max_pu')
            phase_profile: np.ndarray | None = self._get_time_series(self.pypsa_grid.transformers_t.phase_shift,
                                                                       ix, 'transformer phase_shift')

            template = self.transformer_types.get(data['type'], None)

            if template is not None:
                proto.apply_template(obj=template, Sbase=self.grid.Sbase, logger=self.logger)
            else:
                proto.R = data['r']
                proto.X = data['x']
                proto.G = data['g']
                proto.B = data['b']
                if copy_count:
                    proto.rate = data['s_nom'] / copy_count

            # PyPSA's rating covers the parallel circuits represented by this row.
            if copy_count:
                proto.rate = data['s_nom'] * data['s_max_pu'] / copy_count
            else:
                self.logger.add_warning(msg="Transformer has no parallel circuits", device=ix)
            for i in range(copy_count):
                transformer = proto.copy()
                transformer.name = f'{ix}-{i}'
                # Each parallel transformer receives the same per-unit source
                # limit, scaled to the circuit-level nominal rating.
                if rate_profile is not None:
                    transformer.rate_prof.set(rate_profile * data['s_nom'] / copy_count)
                else:
                    pass
                if phase_profile is not None:
                    # PyPSA time-series phase shifts retain the same degree
                    # convention as their static phase_shift attribute.
                    transformer.tap_phase_prof.set(np.deg2rad(phase_profile))
                else:
                    pass
                self.grid.add_transformer2w(transformer)
                self._add_capacity_investment(data=data,
                                              device=transformer,
                                              component_name='Transformer',
                                              extendable_field='s_nom_extendable',
                                              nominal_field='s_nom',
                                              optimum_field='s_nom_opt',
                                              capacity_property='rate',
                                              capacity_scale=self._finite_float(data['s_max_pu'], 1.0) / copy_count,
                                              cost_scale=1.0 / copy_count)

    def _parse_shunts(self):
        """
        Parses the shunt impedances row from the PyPSA network.
        """
        for name, row in self.pypsa_grid.shunt_impedances.iterrows():
            bus = self.buses[row['bus']]
            V2 = (bus.Vnom * 1e3) ** 2
            g = row['g']  # in Siemens
            b = row['b']  # in Siemens
            G = V2 * g * 1e-6  # in MW
            B = V2 * b * 1e-6  # in MVAr

            elm = Shunt(
                name=row['name'],
                G=G,
                B=B,
                active=bool(row["active"])
            )
            self.grid.add_shunt(bus=bus, api_obj=elm)

    def parse(self) -> MultiCircuit:
        """
        Parses the PyPSA network.
        :return: the VeraGrid circuit object.
        """
        self._parse_generators()
        self._parse_storage_units()
        self._parse_stores()
        self._parse_loads()
        self._parse_lines()
        self._parse_hvdc()
        self._parse_transformers()
        self._parse_shunts()
        self._parse_global_constraints()
        return self.grid


def pypsa2veragrid(network: 'pypsa.Network', logger: Logger) -> MultiCircuit:
    """

    :param network:
    :param logger:
    :return:
    """
    parser = PyPSAParser(network, logger)
    return parser.parse()


def parse_pypsa_netcdf(file_path: str, logger: Logger) -> MultiCircuit:
    """
    Parses the netCDF file using the PyPSA library.
    :param file_path: the file path
    :param logger: a logger to produce warnings and/or errors.
    :return: the VeraGrid circuit object
    """
    if not PYPSA_AVAILABLE:
        logger.add_error(f"PyPSA unavailable: {PYPSA_UNAVAILABLE_REASON}")
        return MultiCircuit('')
    else:
        network = Network()
        # Reader methods and their optional dependencies vary independently of the Network export.
        try:
            network.import_from_netcdf(file_path)
        except (ImportError, AttributeError) as error:
            logger.add_error(optional_dependency_failure("pypsa", error))
            return MultiCircuit('')
        else:
            return pypsa2veragrid(network, logger)


def parse_pypsa_hdf5(file_path: str, logger: Logger) -> MultiCircuit:
    """
    Parses the HDF5 store file using the PyPSA library.
    :param file_path: the file path
    :param logger: a logger to produce warnings and/or errors.
    :return: the VeraGrid circuit object
    """
    if not PYPSA_AVAILABLE:
        logger.add_error(f"PyPSA unavailable: {PYPSA_UNAVAILABLE_REASON}")
        return MultiCircuit('')
    else:
        network = Network()
        # Reader methods and their optional dependencies vary independently of the Network export.
        try:
            network.import_from_hdf5(file_path)
        except (ImportError, AttributeError) as error:
            logger.add_error(optional_dependency_failure("pypsa", error))
            return MultiCircuit('')
        else:
            return pypsa2veragrid(network, logger)
