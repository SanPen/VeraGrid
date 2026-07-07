# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING, Union, List, Any
import numpy as np
import pandas as pd
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType, SimulationTypes
from VeraGridEngine.basic_structures import IntVec

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGridEngine.Devices.Substation.bus import Bus
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults
    from VeraGridEngine.Simulations.OPF.opf_ts_results import OptimalPowerFlowTimeSeriesResults


class InputsAnalysisResults(ResultsTemplate):
    LOCAL_RESULTS_DECLARATIONS = tuple()

    __slots__ = (
        "grid",
        "opf_results",
        "opf_time_series_results",
        "area_names",
        "zone_names",
        "substation_names",
        "voltage_level_names",
        "country_names",
        "community_names",
        "region_names",
        "municipality_names",
        "gen_data",
        "battery_data",
        "load_data",
        "static_gen_data",
        "external_grid_data",
        "current_injection_data",
        "shunt_data",
        "bus_dict",
        "bus_area_indices",
        "bus_zone_indices",
        "bus_substation_indices",
        "bus_voltage_level_indices",
        "bus_country_indices",
        "bus_community_indices",
        "bus_region_indices",
        "bus_municipality_indices",
    )

    tpe = 'Inputs Analysis'

    def __init__(self,
                 grid: MultiCircuit,
                 opf_results: Union[None, OptimalPowerFlowResults] = None,
                 opf_time_series_results: Union[None, OptimalPowerFlowTimeSeriesResults] = None):
        """
        Construct the analysis
        :param grid:
        """
        available_results = self.get_available_results(has_time_series=grid.get_time_number() > 0)

        ResultsTemplate.__init__(self,
                                 name='Inputs analysis',
                                 available_results=available_results,
                                 time_array=None,
                                 clustering_results=None,
                                 study_results_type=StudyResultsType.InputsAnalysis)

        self.grid = grid
        self.opf_results = opf_results
        self.opf_time_series_results = opf_time_series_results

        self.area_names = self.get_collection_names(self.grid.areas)
        self.zone_names = self.get_collection_names(self.grid.zones)
        self.substation_names = self.get_collection_names(self.grid.get_substations())
        self.voltage_level_names = self.get_collection_names(self.grid.get_voltage_levels())
        self.country_names = self.get_collection_names(self.grid.countries)
        self.community_names = self.get_collection_names(self.grid.get_communities())
        self.region_names = self.get_collection_names(self.grid.get_regions())
        self.municipality_names = self.get_collection_names(self.grid.get_municipalities())

        self.gen_data = self.get_generators_df()
        self.battery_data = self.get_batteries_df()
        self.load_data = self.get_loads_df()
        self.static_gen_data = self.get_static_generators_df()
        self.external_grid_data = self.get_external_grids_df()
        self.current_injection_data = self.get_current_injections_df()
        self.shunt_data = self.get_shunts_df()

        self.bus_dict = self.grid.get_bus_index_dict()
        self.bus_area_indices = self.get_bus_area_indices()
        self.bus_zone_indices = self.get_bus_zone_indices()
        self.bus_substation_indices = self.get_bus_substation_indices()
        self.bus_voltage_level_indices = self.get_bus_voltage_level_indices()
        self.bus_country_indices = self.get_bus_country_indices()
        self.bus_community_indices = self.get_bus_community_indices()
        self.bus_region_indices = self.get_bus_region_indices()
        self.bus_municipality_indices = self.get_bus_municipality_indices()

    def get_snapshot_result_types(self) -> List[ResultTypes]:
        """
        Get the available snapshot result types for inputs analysis.

        :return: List of snapshot result types
        """
        return [
            ResultTypes.ZoneAnalysis,
            ResultTypes.AreaAnalysis,
            ResultTypes.SubstationAnalysis,
            ResultTypes.VoltageLevelAnalysis,
            ResultTypes.CountryAnalysis,
            ResultTypes.CommunityAnalysis,
            ResultTypes.RegionAnalysis,
            ResultTypes.MunicipalityAnalysis,
        ]

    def get_available_results(self, has_time_series: bool) -> dict[ResultTypes, List[ResultTypes]]:
        """
        Get the available results grouped by spatial aggregation.

        :param has_time_series: Whether time-series results are available
        :return: Available results grouped by aggregation
        """
        available_results: dict[ResultTypes, List[ResultTypes]] = {
            ResultTypes.AreaResults: [ResultTypes.AreaAnalysis],
            ResultTypes.ZoneResults: [ResultTypes.ZoneAnalysis],
            ResultTypes.SubstationResults: [ResultTypes.SubstationAnalysis],
            ResultTypes.VoltageLevelResults: [ResultTypes.VoltageLevelAnalysis],
            ResultTypes.CountryResults: [ResultTypes.CountryAnalysis],
            ResultTypes.CommunityResults: [ResultTypes.CommunityAnalysis],
            ResultTypes.RegionResults: [ResultTypes.RegionAnalysis],
            ResultTypes.MunicipalityResults: [ResultTypes.MunicipalityAnalysis],
        }

        if has_time_series:
            available_results[ResultTypes.AreaResults].extend([
                ResultTypes.AreaGenerationAnalysis,
                ResultTypes.AreaLoadAnalysis,
                ResultTypes.AreaBalanceAnalysis,
            ])
            available_results[ResultTypes.ZoneResults].extend([
                ResultTypes.ZoneGenerationAnalysis,
                ResultTypes.ZoneLoadAnalysis,
                ResultTypes.ZoneBalanceAnalysis,
            ])
            available_results[ResultTypes.SubstationResults].extend([
                ResultTypes.SubstationGenerationAnalysis,
                ResultTypes.SubstationLoadAnalysis,
                ResultTypes.SubstationBalanceAnalysis,
            ])
            available_results[ResultTypes.VoltageLevelResults].extend([
                ResultTypes.VoltageLevelGenerationAnalysis,
                ResultTypes.VoltageLevelLoadAnalysis,
                ResultTypes.VoltageLevelBalanceAnalysis,
            ])
            available_results[ResultTypes.CountryResults].extend([
                ResultTypes.CountryGenerationAnalysis,
                ResultTypes.CountryLoadAnalysis,
                ResultTypes.CountryBalanceAnalysis,
            ])
            available_results[ResultTypes.CommunityResults].extend([
                ResultTypes.CommunityGenerationAnalysis,
                ResultTypes.CommunityLoadAnalysis,
                ResultTypes.CommunityBalanceAnalysis,
            ])
            available_results[ResultTypes.RegionResults].extend([
                ResultTypes.RegionGenerationAnalysis,
                ResultTypes.RegionLoadAnalysis,
                ResultTypes.RegionBalanceAnalysis,
            ])
            available_results[ResultTypes.MunicipalityResults].extend([
                ResultTypes.MunicipalityGenerationAnalysis,
                ResultTypes.MunicipalityLoadAnalysis,
                ResultTypes.MunicipalityBalanceAnalysis,
            ])
        else:
            pass

        return available_results

    def get_series_result_types(self) -> List[ResultTypes]:
        """
        Get the available time-series result types for inputs analysis.

        :return: List of time-series result types
        """
        return [
            ResultTypes.AreaGenerationAnalysis,
            ResultTypes.ZoneGenerationAnalysis,
            ResultTypes.SubstationGenerationAnalysis,
            ResultTypes.VoltageLevelGenerationAnalysis,
            ResultTypes.CountryGenerationAnalysis,
            ResultTypes.CommunityGenerationAnalysis,
            ResultTypes.RegionGenerationAnalysis,
            ResultTypes.MunicipalityGenerationAnalysis,
            ResultTypes.AreaLoadAnalysis,
            ResultTypes.ZoneLoadAnalysis,
            ResultTypes.SubstationLoadAnalysis,
            ResultTypes.VoltageLevelLoadAnalysis,
            ResultTypes.CountryLoadAnalysis,
            ResultTypes.CommunityLoadAnalysis,
            ResultTypes.RegionLoadAnalysis,
            ResultTypes.MunicipalityLoadAnalysis,
            ResultTypes.AreaBalanceAnalysis,
            ResultTypes.ZoneBalanceAnalysis,
            ResultTypes.SubstationBalanceAnalysis,
            ResultTypes.VoltageLevelBalanceAnalysis,
            ResultTypes.CountryBalanceAnalysis,
            ResultTypes.CommunityBalanceAnalysis,
            ResultTypes.RegionBalanceAnalysis,
            ResultTypes.MunicipalityBalanceAnalysis,
        ]

    def get_collection_names(self, elements: List[Any]) -> List[str]:
        """
        Get the unique names of a collection of aggregation objects.

        :param elements: List of aggregation objects
        :return: Sorted list of names
        """
        names: set[str] = set()
        for element in elements:
            names.add(element.name)
        return sorted(names)

    def get_aggregation_elements(self, aggregation: str) -> List[Any]:
        """
        Get the aggregation objects associated to an aggregation name.

        This method preserves the collection order used by the bus-to-index
        maps so that time-series matrices and index lookups share the same
        coordinate system.

        :param aggregation: Aggregation name
        :return: Ordered list of aggregation objects
        """
        if aggregation == "Area":
            return self.grid.areas
        elif aggregation == "Zone":
            return self.grid.zones
        elif aggregation == "Substation":
            return self.grid.get_substations()
        elif aggregation == "VoltageLevel":
            return self.grid.get_voltage_levels()
        elif aggregation == "Country":
            return self.grid.countries
        elif aggregation == "Community":
            return self.grid.get_communities()
        elif aggregation == "Region":
            return self.grid.get_regions()
        elif aggregation == "Municipality":
            return self.grid.get_municipalities()
        else:
            raise Exception("Unknown aggregation:" + str(aggregation))

    def get_aggregation_headers(self) -> List[str]:
        """
        Get the dataframe aggregation column headers.

        :return: Ordered list of aggregation column names
        """
        return ["Zone", "Area", "Substation", "VoltageLevel", "Country", "Community", "Region", "Municipality"]

    def get_bus_aggregation_values(self, bus: Bus | None) -> List[str]:
        """
        Get the aggregation names associated to a bus.

        The bus getter methods are used so that direct bus assignments have
        priority over values inferred from higher-level structures.

        :param bus: Bus object or ``None``
        :return: Aggregation names in dataframe column order
        """
        values: List[str] = list()
        if bus is None:
            for _ in self.get_aggregation_headers():
                values.append("")
        else:
            zone = bus.get_zone()
            area = bus.get_area()
            substation = bus.get_substation()
            voltage_level = bus.get_voltage_level()
            country = bus.get_country()
            community = bus.get_community()
            region = bus.get_region()
            municipality = bus.get_municipality()
            values.append(zone.name if zone is not None else "")
            values.append(area.name if area is not None else "")
            values.append(substation.name if substation is not None else "")
            values.append(voltage_level.name if voltage_level is not None else "")
            values.append(country.name if country is not None else "")
            values.append(community.name if community is not None else "")
            values.append(region.name if region is not None else "")
            values.append(municipality.name if municipality is not None else "")
        return values

    def get_aggregation_names(self, aggregation: str) -> List[str]:
        """
        Get the names associated to an aggregation type.

        :param aggregation: Aggregation name
        :return: List of aggregation names
        """
        if aggregation == "Area":
            return self.area_names
        elif aggregation == "Zone":
            return self.zone_names
        elif aggregation == "Substation":
            return self.substation_names
        elif aggregation == "VoltageLevel":
            return self.voltage_level_names
        elif aggregation == "Country":
            return self.country_names
        elif aggregation == "Community":
            return self.community_names
        elif aggregation == "Region":
            return self.region_names
        elif aggregation == "Municipality":
            return self.municipality_names
        else:
            raise Exception("Unknown grouping:" + str(aggregation))

    def get_aggregation_device_type(self, aggregation: str) -> DeviceType:
        """
        Get the device type associated to an aggregation.

        :param aggregation: Aggregation name
        :return: Corresponding device type
        """
        if aggregation == "Area":
            return DeviceType.AreaDevice
        elif aggregation == "Zone":
            return DeviceType.ZoneDevice
        elif aggregation == "Substation":
            return DeviceType.SubstationDevice
        elif aggregation == "VoltageLevel":
            return DeviceType.VoltageLevelDevice
        elif aggregation == "Country":
            return DeviceType.CountryDevice
        elif aggregation == "Community":
            return DeviceType.CommunityDevice
        elif aggregation == "Region":
            return DeviceType.RegionDevice
        elif aggregation == "Municipality":
            return DeviceType.MunicipalityDevice
        else:
            raise Exception("Unknown aggregation:" + str(aggregation))

    def get_result_aggregation(self, result_type: ResultTypes) -> str:
        """
        Get the aggregation name corresponding to a result type.

        :param result_type: Result type
        :return: Aggregation name
        """
        if result_type in (ResultTypes.AreaAnalysis,
                           ResultTypes.AreaGenerationAnalysis,
                           ResultTypes.AreaLoadAnalysis,
                           ResultTypes.AreaBalanceAnalysis):
            return "Area"
        elif result_type in (ResultTypes.ZoneAnalysis,
                             ResultTypes.ZoneGenerationAnalysis,
                             ResultTypes.ZoneLoadAnalysis,
                             ResultTypes.ZoneBalanceAnalysis):
            return "Zone"
        elif result_type in (ResultTypes.SubstationAnalysis,
                             ResultTypes.SubstationGenerationAnalysis,
                             ResultTypes.SubstationLoadAnalysis,
                             ResultTypes.SubstationBalanceAnalysis):
            return "Substation"
        elif result_type in (ResultTypes.VoltageLevelAnalysis,
                             ResultTypes.VoltageLevelGenerationAnalysis,
                             ResultTypes.VoltageLevelLoadAnalysis,
                             ResultTypes.VoltageLevelBalanceAnalysis):
            return "VoltageLevel"
        elif result_type in (ResultTypes.CountryAnalysis,
                             ResultTypes.CountryGenerationAnalysis,
                             ResultTypes.CountryLoadAnalysis,
                             ResultTypes.CountryBalanceAnalysis):
            return "Country"
        elif result_type in (ResultTypes.CommunityAnalysis,
                             ResultTypes.CommunityGenerationAnalysis,
                             ResultTypes.CommunityLoadAnalysis,
                             ResultTypes.CommunityBalanceAnalysis):
            return "Community"
        elif result_type in (ResultTypes.RegionAnalysis,
                             ResultTypes.RegionGenerationAnalysis,
                             ResultTypes.RegionLoadAnalysis,
                             ResultTypes.RegionBalanceAnalysis):
            return "Region"
        elif result_type in (ResultTypes.MunicipalityAnalysis,
                             ResultTypes.MunicipalityGenerationAnalysis,
                             ResultTypes.MunicipalityLoadAnalysis,
                             ResultTypes.MunicipalityBalanceAnalysis):
            return "Municipality"
        else:
            raise Exception("Unknown result type:" + str(result_type))

    def get_generators_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for k, elm in enumerate(self.grid.generators):
            if elm is not None:
                if self.opf_results is None:
                    P = elm.P * elm.active
                else:
                    P = self.opf_results.generator_power[k] - self.opf_results.generator_shedding[k]

                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            P,
                            elm.Pf,
                            elm.Snom,
                            elm.Pmin, elm.Pmax,
                            elm.Qmin, elm.Qmax,
                            elm.Vset] + aggregation_values)

        cols = ['Name', 'P', 'Pf',
                'Snom', 'Pmin', 'Pmax',
                'Qmin', 'Qmax', 'Vset'] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_batteries_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_batteries():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.P * elm.active,
                            elm.Pf,
                            elm.Snom,
                            elm.Pmin, elm.Pmax,
                            elm.Qmin, elm.Qmax,
                            elm.Vset] + aggregation_values)

        cols = ['Name', 'P', 'Pf',
                'Snom', 'Pmin', 'Pmax',
                'Qmin', 'Qmax', 'Vset'] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_loads_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_loads():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.P * elm.active,
                            elm.Q * elm.active] + aggregation_values)

        cols = ['Name', 'P', 'Q',
                ] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_static_generators_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_static_generators():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.P * elm.active,
                            elm.Q * elm.active] + aggregation_values)

        cols = ['Name', 'P', 'Q',
                ] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_external_grids_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_external_grids():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.P * elm.active,
                            elm.Q * elm.active] + aggregation_values)

        cols = ['Name', 'P', 'Q',
                ] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_current_injections_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_current_injections():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.Ir * elm.active,
                            elm.Ii * elm.active] + aggregation_values)

        cols = ['Name', 'P', 'Q',
                ] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def get_shunts_df(self) -> pd.DataFrame:
        """

        :return:
        """
        dta = list()
        aggregation_cols: List[str] = self.get_aggregation_headers()
        for elm in self.grid.get_shunts() + self.grid.get_controllable_shunts():
            if elm is not None:
                aggregation_values: List[str] = self.get_bus_aggregation_values(elm.bus)

                dta.append([elm.name,
                            elm.G * elm.active,
                            elm.B * elm.active] + aggregation_values)

        cols = ['Name', 'P', 'Q',
                ] + aggregation_cols
        return pd.DataFrame(data=dta, columns=cols)

    def group_by(self, group: str):
        """
        Return a DataFrame grouped by the requested aggregation.

        :param group: Aggregation name
        :return: Group DataFrame
        """
        labels: List[str] = self.get_aggregation_names(group)

        n = len(labels)
        cols_gen = ['P', 'Pmin', 'Pmax', 'Qmin', 'Qmax']
        cols_load = ['P', 'Q']
        cols = ['P', 'Pgen', 'Pload', 'Pbatt', 'Pstagen', 'Pext', 'Pcur', 'Pshunt', 'Pmin', 'Pmax', 'Q', 'Qmin', 'Qmax']
        df = pd.DataFrame(data=np.zeros((n, len(cols))), columns=cols, index=labels)

        if len(self.gen_data):
            df2 = self.gen_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_gen] = df[cols_gen].add(df2[cols_gen].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pgen'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.battery_data):
            df2 = self.battery_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_gen] = df[cols_gen].add(df2[cols_gen].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pbatt'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.load_data):
            df2 = self.load_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_load] = df[cols_load].sub(df2[cols_load].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pload'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.static_gen_data):
            df2 = self.static_gen_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_load] = df[cols_load].add(df2[cols_load].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pstagen'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.external_grid_data):
            # External grid follows the injection sign convention of LoadParent:
            # positive P behaves as demand and negative P behaves as generation.
            df2 = self.external_grid_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_load] = df[cols_load].sub(df2[cols_load].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pext'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.current_injection_data):
            # CurrentInjection has load-like sign convention in Ir/Ii.
            df2 = self.current_injection_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_load] = df[cols_load].sub(df2[cols_load].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pcur'] = df2['P'].reindex(idx, fill_value=0.0)

        if len(self.shunt_data):
            # Shunt G/B are load-like power terms at V=1.0 p.u.
            df2 = self.shunt_data.groupby(group).sum()
            idx = df.index.union(df2.index)
            df = df.reindex(idx, fill_value=0.0)
            df[cols_load] = df[cols_load].sub(df2[cols_load].reindex(idx, fill_value=0.0), fill_value=0.0)
            df['Pshunt'] = df2['P'].reindex(idx, fill_value=0.0)

        df.fillna(0, inplace=True)

        return df

    def get_bus_zone_indices(self) -> IntVec:
        """
        Get the zone index of each bus.

        A value of ``-1`` means that the bus is not associated to any zone.

        :return: Zone indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.zones)}
        return np.array([d.get(bus.get_zone(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_area_indices(self) -> IntVec:
        """
        Get the area index of each bus.

        A value of ``-1`` means that the bus is not associated to any area.

        :return: Area indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.areas)}
        return np.array([d.get(bus.get_area(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_country_indices(self) -> IntVec:
        """
        Get the country index of each bus.

        A value of ``-1`` means that the bus is not associated to any country.

        :return: Country indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.countries)}
        return np.array([d.get(bus.get_country(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_substation_indices(self) -> IntVec:
        """
        Get the substation index of each bus.

        A value of ``-1`` means that the bus is not associated to any substation.

        :return: Substation indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.get_substations())}
        return np.array([d.get(bus.get_substation(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_voltage_level_indices(self) -> IntVec:
        """
        Get the voltage-level index of each bus.

        A value of ``-1`` means that the bus is not associated to any voltage level.

        :return: Voltage-level indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.get_voltage_levels())}
        return np.array([d.get(bus.get_voltage_level(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_community_indices(self) -> IntVec:
        """
        Get the community index of each bus.

        A value of ``-1`` means that the bus is not associated to any community.

        :return: Community indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.get_communities())}
        return np.array([d.get(bus.get_community(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_region_indices(self) -> IntVec:
        """
        Get the region index of each bus.

        A value of ``-1`` means that the bus is not associated to any region.

        :return: Region indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.get_regions())}
        return np.array([d.get(bus.get_region(), -1) for bus in self.grid.buses], dtype=int)

    def get_bus_municipality_indices(self) -> IntVec:
        """
        Get the municipality index of each bus.

        A value of ``-1`` means that the bus is not associated to any municipality.

        :return: Municipality indices per bus
        """
        d = {elm: i for i, elm in enumerate(self.grid.get_municipalities())}
        return np.array([d.get(bus.get_municipality(), -1) for bus in self.grid.buses], dtype=int)

    def get_collection_attr_series(self, elms, magnitude: str, aggregation="Area"):
        """

        :param elms:
        :param magnitude: Snapshot property name
        :param aggregation:
        :return:
        """
        if aggregation == 'Zone':
            d2 = self.get_bus_zone_indices()
        elif aggregation == 'Area':
            d2 = self.get_bus_area_indices()
        elif aggregation == 'Substation':
            d2 = self.get_bus_substation_indices()
        elif aggregation == 'VoltageLevel':
            d2 = self.get_bus_voltage_level_indices()
        elif aggregation == 'Country':
            d2 = self.get_bus_country_indices()
        elif aggregation == 'Community':
            d2 = self.get_bus_community_indices()
        elif aggregation == 'Region':
            d2 = self.get_bus_region_indices()
        elif aggregation == 'Municipality':
            d2 = self.get_bus_municipality_indices()
        else:
            raise Exception('Unknown Aggregation. Possible aggregations are Zone, Area, Substation, VoltageLevel, Country, Community, Region, Municipality')

        elements: List[Any] = self.get_aggregation_elements(aggregation)
        headers = [element.name for element in elements]
        ne = len(headers)

        nt = self.grid.get_time_number()
        x = np.zeros((nt, ne))

        for elm in elms:
            if elm.bus is not None:
                i = self.bus_dict[elm.bus]
                i2 = d2[i]
                if i2 >= 0:
                    i3 = int(i2)
                    x[:, i3] += elm.get_profile(magnitude=magnitude).toarray()

        return x, headers

    def mdl(self, result_type: ResultTypes) -> "ResultsTable":
        """
        Plot the results
        :param result_type: type of results (string)
        :return: DataFrame of the results
                (or None if the result was not understood)
        """
        if result_type in self.get_snapshot_result_types():
            aggregation: str = self.get_result_aggregation(result_type)
            df = self.group_by(aggregation)
            aggregation_device_type: DeviceType = self.get_aggregation_device_type(aggregation)
            return ResultsTable(data=df.values,
                                index=df.index.values,
                                idx_device_type=aggregation_device_type,
                                columns=df.columns.values,
                                cols_device_type=aggregation_device_type,
                                title=result_type.value)
        elif result_type in (
                ResultTypes.AreaGenerationAnalysis,
                ResultTypes.ZoneGenerationAnalysis,
                ResultTypes.SubstationGenerationAnalysis,
                ResultTypes.VoltageLevelGenerationAnalysis,
                ResultTypes.CountryGenerationAnalysis,
                ResultTypes.CommunityGenerationAnalysis,
                ResultTypes.RegionGenerationAnalysis,
                ResultTypes.MunicipalityGenerationAnalysis):
            aggregation = self.get_result_aggregation(result_type)
            generators = self.grid.get_generators() + self.grid.get_batteries() + self.grid.get_static_generators()
            y, columns = self.get_collection_attr_series(generators, 'P', aggregation)
            return ResultsTable(data=y,
                                index=pd.to_datetime(self.grid.time_profile),
                                idx_device_type=DeviceType.TimeDevice,
                                columns=columns,
                                cols_device_type=self.get_aggregation_device_type(aggregation),
                                title=result_type.value,
                                units="(MW)")
        elif result_type in (
                ResultTypes.AreaLoadAnalysis,
                ResultTypes.ZoneLoadAnalysis,
                ResultTypes.SubstationLoadAnalysis,
                ResultTypes.VoltageLevelLoadAnalysis,
                ResultTypes.CountryLoadAnalysis,
                ResultTypes.CommunityLoadAnalysis,
                ResultTypes.RegionLoadAnalysis,
                ResultTypes.MunicipalityLoadAnalysis):
            aggregation = self.get_result_aggregation(result_type)
            y, columns = self.get_collection_attr_series(self.grid.get_loads(), 'P', aggregation)
            return ResultsTable(data=y,
                                index=pd.to_datetime(self.grid.time_profile),
                                idx_device_type=DeviceType.TimeDevice,
                                columns=columns,
                                cols_device_type=self.get_aggregation_device_type(aggregation),
                                title=result_type.value,
                                units="(MW)")
        elif result_type in (
                ResultTypes.AreaBalanceAnalysis,
                ResultTypes.ZoneBalanceAnalysis,
                ResultTypes.SubstationBalanceAnalysis,
                ResultTypes.VoltageLevelBalanceAnalysis,
                ResultTypes.CountryBalanceAnalysis,
                ResultTypes.CommunityBalanceAnalysis,
                ResultTypes.RegionBalanceAnalysis,
                ResultTypes.MunicipalityBalanceAnalysis):
            aggregation = self.get_result_aggregation(result_type)
            generators = self.grid.get_generators() + self.grid.get_batteries() + self.grid.get_static_generators()
            yg, columns = self.get_collection_attr_series(generators, 'P', aggregation)
            yl, columns = self.get_collection_attr_series(self.grid.get_loads(), 'P', aggregation)
            ye, columns = self.get_collection_attr_series(self.grid.get_external_grids(), 'P', aggregation)
            yci, columns = self.get_collection_attr_series(self.grid.get_current_injections(), 'Ir', aggregation)
            ysh, columns = self.get_collection_attr_series(
                self.grid.get_shunts() + self.grid.get_controllable_shunts(),
                'G',
                aggregation)
            y = yg - yl - ye - yci - ysh
            return ResultsTable(data=y,
                                index=pd.to_datetime(self.grid.time_profile),
                                idx_device_type=DeviceType.TimeDevice,
                                columns=columns,
                                cols_device_type=self.get_aggregation_device_type(aggregation),
                                title=result_type.value,
                                units="(MW)")
        else:
            raise Exception('Result type not understood:' + str(result_type))


class InputsAnalysisDriver(DriverTemplate):
    __slots__ = ()

    name = 'Inputs Analysis'
    tpe = SimulationTypes.InputsAnalysis_run

    def __init__(self, grid: MultiCircuit):
        """
        InputsAnalysisDriver class constructor
        :param grid: MultiCircuit instance
        """
        DriverTemplate.__init__(self, grid=grid)

        self.tic()
        self.results = InputsAnalysisResults(grid=grid)
        self.toc()

    def get_steps(self) -> List[int]:
        """

        :return:
        """
        return list()

    def run(self) -> None:
        """
        Pack run_pf for the QThread
        :return:
        """
        pass

    def cancel(self):
        self.__cancel__ = True
