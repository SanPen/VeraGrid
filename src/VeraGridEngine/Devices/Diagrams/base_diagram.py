# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import sys
import uuid
import networkx as nx
from typing import Any, Dict, Union, List, Tuple, TYPE_CHECKING

from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
from VeraGridEngine.Devices.Diagrams.map_location import MapLocation
from VeraGridEngine.enumerations import DiagramType, DeviceType, BusGraphicType
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import Colormaps

if TYPE_CHECKING:
    from VeraGridEngine.Devices.types import ALL_DEV_TYPES
    from VeraGridEngine.Devices.Substation.bus import Bus
    from VeraGridEngine.Devices.Substation.busbar import BusBar
    from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
    from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
    from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
    from VeraGridEngine.Devices.Branches.transformerNw import TransformerNW


def get_layout_anchor(api_object: ALL_DEV_TYPES) -> ALL_DEV_TYPES:
    """
    Return the electrical anchor used to infer schematic layout metadata.

    :param api_object: Diagram node API object.
    :return: Anchor object carrying the electrical metadata for layout purposes.
    """
    anchor: ALL_DEV_TYPES = api_object

    # Fluid nodes are placed using the electrical bus they are attached to.
    if api_object.device_type == DeviceType.FluidNodeDevice:
        if api_object.bus is not None:
            anchor = api_object.bus
        else:
            anchor = api_object

    # Multi-winding transformers are placed using their internal anchor bus.
    elif api_object.device_type == DeviceType.Transformer3WDevice:
        if api_object.bus0 is not None:
            anchor = api_object.bus0
        else:
            anchor = api_object
    elif api_object.device_type == DeviceType.TransformerNwDevice:
        if api_object.bus0 is not None:
            anchor = api_object.bus0
        else:
            anchor = api_object

    # All other devices already expose the relevant electrical metadata directly.
    else:
        anchor = api_object

    return anchor


def get_layout_voltage_kv(api_object: ALL_DEV_TYPES) -> float:
    """
    Get the voltage used to assign schematic layers.

    :param api_object: Diagram node API object.
    :return: Voltage in kV used by the automatic layout.
    """
    anchor: ALL_DEV_TYPES = get_layout_anchor(api_object=api_object)
    voltage_kv: float = 0.0

    # Buses already expose the nominal voltage directly.
    if anchor.device_type == DeviceType.BusDevice:
        voltage_kv = float(anchor.Vnom)

    # Bus bars obtain the voltage from their voltage level when that data exists.
    elif anchor.device_type == DeviceType.BusBarDevice:
        if anchor.voltage_level is not None:
            voltage_kv = float(anchor.voltage_level.Vnom)
        else:
            voltage_kv = 0.0

    # All remaining node types fall back to zero when there is no electrical level.
    else:
        voltage_kv = 0.0

    return voltage_kv


def get_layout_is_slack(api_object: ALL_DEV_TYPES) -> bool:
    """
    Determine whether one diagram node should be treated as the island root candidate.

    :param api_object: Diagram node API object.
    :return: ``True`` when the node is electrically slack.
    """
    anchor: ALL_DEV_TYPES = get_layout_anchor(api_object=api_object)
    is_slack: bool = False

    if anchor.device_type == DeviceType.BusDevice:
        is_slack = bool(anchor.is_slack)
    else:
        is_slack = False

    return is_slack


def get_layout_is_dc(api_object: ALL_DEV_TYPES) -> bool:
    """
    Determine whether one diagram node belongs to the DC side of the network.

    :param api_object: Diagram node API object.
    :return: ``True`` when the node is DC.
    """
    anchor: ALL_DEV_TYPES = get_layout_anchor(api_object=api_object)
    is_dc: bool = False

    if anchor.device_type == DeviceType.BusDevice:
        is_dc = bool(anchor.is_dc)
    else:
        is_dc = False

    return is_dc


def get_layout_substation_name(api_object: ALL_DEV_TYPES) -> str:
    """
    Get the substation name used to stabilize the ordering inside one layer.

    :param api_object: Diagram node API object.
    :return: Substation name or an empty string.
    """
    anchor: ALL_DEV_TYPES = get_layout_anchor(api_object=api_object)
    substation_name: str = ""

    if anchor.device_type == DeviceType.BusDevice:
        if anchor.substation is not None:
            substation_name = anchor.substation.name
        else:
            substation_name = ""
    elif anchor.device_type == DeviceType.BusBarDevice:
        if anchor.voltage_level is not None and anchor.voltage_level.substation is not None:
            substation_name = anchor.voltage_level.substation.name
        else:
            substation_name = ""
    else:
        substation_name = ""

    return substation_name


def add_node_layout_data(graph: nx.MultiDiGraph, node_index: int, api_object: ALL_DEV_TYPES) -> None:
    """
    Add one node together with the electrical metadata needed by the schematic layouts.

    :param graph: Diagram graph under construction.
    :param node_index: Integer node identifier.
    :param api_object: Diagram node API object.
    """
    device_tpe: str = api_object.device_type.value
    voltage_kv: float = get_layout_voltage_kv(api_object=api_object)
    is_slack: bool = get_layout_is_slack(api_object=api_object)
    is_dc: bool = get_layout_is_dc(api_object=api_object)
    substation_name: str = get_layout_substation_name(api_object=api_object)
    node_name: str = api_object.name

    # The graph keeps the original API object together with the explicit metadata
    # required by the layout stage so the GUI does not need to infer it again.
    graph.add_node(node_index,
                   api_object=api_object,
                   device_tpe=device_tpe,
                   voltage_kv=voltage_kv,
                   is_slack=is_slack,
                   is_dc=is_dc,
                   substation=substation_name,
                   name=node_name)


def get_branch_endpoint_voltages(branch: ALL_DEV_TYPES) -> Tuple[float, float]:
    """
    Get the endpoint voltages used to detect inter-level links.

    :param branch: Branch API object.
    :return: Pair of endpoint voltages in kV.
    """
    source_voltage_kv: float = 0.0
    target_voltage_kv: float = 0.0

    # Fluid links use fluid nodes as endpoints, which in turn derive the voltage from their bus.
    if branch.device_type == DeviceType.FluidPathDevice:
        source_voltage_kv = get_layout_voltage_kv(api_object=branch.source)
        target_voltage_kv = get_layout_voltage_kv(api_object=branch.target)

    # Electrical branches expose bus_from and bus_to directly.
    else:
        source_voltage_kv = get_layout_voltage_kv(api_object=branch.bus_from)
        target_voltage_kv = get_layout_voltage_kv(api_object=branch.bus_to)

    return source_voltage_kv, target_voltage_kv


def add_branch_layout_edge(graph: nx.MultiDiGraph,
                           from_idx: int,
                           to_idx: int,
                           branch: ALL_DEV_TYPES,
                           dev_tpe: DeviceType,
                           raw_impedance: float) -> None:
    """
    Add one branch edge with both physical distance and spring attraction metadata.

    :param graph: Diagram graph under construction.
    :param from_idx: Source node index.
    :param to_idx: Target node index.
    :param branch: Branch API object.
    :param dev_tpe: Branch device type.
    :param raw_impedance: Physical distance surrogate for impedance-aware layouts.
    """
    impedance: float = max(abs(float(raw_impedance)), 1e-6)
    strength: float = min(1.0 / impedance, 50.0)
    source_voltage_kv: float
    target_voltage_kv: float
    source_voltage_kv, target_voltage_kv = get_branch_endpoint_voltages(branch=branch)

    # The edge stores two different magnitudes because impedance-based layouts
    # and spring-based layouts interpret edge lengths in opposite directions.
    graph.add_edge(from_idx,
                   to_idx,
                   key=branch.idtag,
                   branch_id=branch.idtag,
                   kind=dev_tpe.value,
                   impedance=impedance,
                   strength=strength,
                   weight=strength,
                   voltage_delta_kv=abs(source_voltage_kv - target_voltage_kv))


class PointsGroup:
    """
    Diagram
    """

    def __init__(self, name: str = '') -> None:
        """

        :param name: Diagram name
        """
        self.name = name

        # device_type: {device uuid: {x, y, h, w, r}}
        self.locations: Dict[str, Union[GraphicLocation, MapLocation]] = dict()

    def set_point(self, device: ALL_DEV_TYPES, location: Union[GraphicLocation, MapLocation]):
        """

        :param device:
        :param location:
        :return:
        """
        self.locations[device.idtag] = location

    def delete_device(self, device: ALL_DEV_TYPES):
        """
        Delete location
        :param device:
        :return:
        """
        loc = self.query_point(device)

        if loc:
            del self.locations[device.idtag]
        else:
            return None

    def query_point(self, device: ALL_DEV_TYPES) -> Union[GraphicLocation, MapLocation, None]:
        """

        :param device:
        :return:
        """
        return self.locations.get(device.idtag, None)

    def get_dict(self) -> Dict[str, Union[GraphicLocation, MapLocation]]:
        """

        :return:
        """
        points = {idtag: location.get_properties_dict() for idtag, location in self.locations.items()}

        return points

    def parse_data(self,
                   data: Dict[str, Dict[str, Any]],
                   obj_dict: Dict[str, ALL_DEV_TYPES],
                   logger: Logger,
                   category: str = "") -> None:
        """
        Parse file data ito this class
        :param data: json dictionary
        :param obj_dict: dictionary of relevant objects (idtag, object)
        :param logger: Logger
        :param category: category
        """
        self.locations = dict()

        for idtag, location in data.items():

            api_object = obj_dict.get(idtag, None)

            if api_object is None:
                # locations with no API object are not created
                logger.add_error("Diagram location could not find API object",
                                 device_class=category,
                                 device=idtag, )
            else:
                if 'x' in location:
                    self.locations[idtag] = GraphicLocation(x=location['x'],
                                                            y=location['y'],
                                                            w=location['w'],
                                                            h=location['h'],
                                                            r=location['r'],
                                                            poly_line=location.get('poly_line', list()),
                                                            layout_metadata=location.get('layout_metadata', dict()),
                                                            draw_labels=location.get('draw_labels', True),
                                                            api_object=api_object)
                if 'latitude' in location:
                    self.locations[idtag] = MapLocation(latitude=location['latitude'],
                                                        longitude=location['longitude'],
                                                        altitude=location['altitude'],
                                                        api_object=api_object)


class BaseDiagram:
    """
    Diagram
    """

    def __init__(self,
                 idtag: Union[str, None],
                 name: str,
                 diagram_type: DiagramType = DiagramType,
                 use_flow_based_width: bool = False,
                 min_branch_width: int = 1.0,
                 max_branch_width=5,
                 min_bus_width=1.0,
                 max_bus_width=20,
                 arrow_size=20,
                 palette: Colormaps = Colormaps.VeraGrid,
                 default_bus_voltage: float = 10):
        """

        :param idtag:
        :param name:
        :param diagram_type:
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :param arrow_size:
        :param palette:
        :param default_bus_voltage:
        """
        if idtag is None:
            self.idtag = uuid.uuid4().hex
        else:
            self.idtag = idtag.replace('_', '').replace('-', '')

        self.name = name

        # device_type: {device uuid: {x, y, h, w, r}}
        self.data: Dict[str, PointsGroup] = dict()

        # diagram type: Map or Schematic, ...
        self.diagram_type: DiagramType = diagram_type

        # sizes
        self._use_flow_based_width: bool = use_flow_based_width
        self._min_branch_width: float = min_branch_width
        self._max_branch_width: float = max_branch_width
        self._min_bus_width: float = min_bus_width
        self._max_bus_width: float = max_bus_width
        self._arrow_size: float = arrow_size
        self._use_api_colors: bool = False

        self._palette = palette
        self._default_bus_voltage: float = default_bus_voltage

    @property
    def use_flow_based_width(self) -> bool:
        """

        :return:
        """
        return self._use_flow_based_width

    @use_flow_based_width.setter
    def use_flow_based_width(self, value: bool):
        self._use_flow_based_width = value

    # min_branch_width property
    @property
    def min_branch_width(self) -> float:
        """

        :return:
        """
        return self._min_branch_width

    @min_branch_width.setter
    def min_branch_width(self, value: float):
        self._min_branch_width = value

    # max_branch_width property
    @property
    def max_branch_width(self) -> float:
        """

        :return:
        """
        return self._max_branch_width

    @max_branch_width.setter
    def max_branch_width(self, value: float):
        self._max_branch_width = value

    # min_bus_width property
    @property
    def min_bus_width(self) -> float:
        """

        :return:
        """
        return self._min_bus_width

    @min_bus_width.setter
    def min_bus_width(self, value: float):
        self._min_bus_width = value


    @property
    def max_bus_width(self) -> float:
        """

        :return:
        """
        return self._max_bus_width

    @max_bus_width.setter
    def max_bus_width(self, value: float):
        self._max_bus_width = value

    @property
    def arrow_size(self) -> float:
        """

        :return:
        """
        return self._arrow_size

    @arrow_size.setter
    def arrow_size(self, value: float):
        self._arrow_size = value

    # palette property
    @property
    def palette(self) -> Colormaps:
        """

        :return:
        """
        return self._palette

    @palette.setter
    def palette(self, value: Colormaps):
        assert isinstance(value, Colormaps)
        self._palette = value

    # default_bus_voltage property
    @property
    def default_bus_voltage(self) -> float:
        """

        :return:
        """
        return self._default_bus_voltage

    @default_bus_voltage.setter
    def default_bus_voltage(self, value: float):
        self._default_bus_voltage = value

    @property
    def use_api_colors(self) -> bool:
        return self._use_api_colors

    @use_api_colors.setter
    def use_api_colors(self, value: bool):
        self._use_api_colors = value

    def set_point(self, device: ALL_DEV_TYPES, location: Union[GraphicLocation, MapLocation]):
        """

        :param device:
        :param location:
        :return:
        """
        # check if the category exists ...
        d = self.data.get(str(device.device_type.value), None)

        if location.api_object is None:
            location.api_object = device

        if d is None:
            # the category does not exist, create it
            group = PointsGroup(name=str(device.device_type.value))
            group.set_point(device, location)
            self.data[str(device.device_type.value)] = group
        else:
            # the category does exist, add point
            d.set_point(device, location)  # the category, exists, just add

    def delete_device(self, device: ALL_DEV_TYPES) -> Union[object, None]:
        """

        :param device:
        :return:
        """
        if device is not None:
            # check if the category exists ...
            d = self.data.get(str(device.device_type.value), None)

            if d:
                # the category does exist, delete_with_dialogue from it
                return d.delete_device(device=device)
            else:
                # not found so we're ok
                return None
        else:
            return None

    def query_point(self, device: ALL_DEV_TYPES) -> Union[GraphicLocation, MapLocation, None]:
        """

        :param device:
        :return:
        """
        # check if the category exists ...
        group = self.data.get(str(device.device_type.value), None)

        if group is None:
            return None  # the category did not exist
        else:
            # search for the device idtag and return the location, if not found return None
            return group.query_point(device)

    def query_by_type(self, device_type: DeviceType) -> Union[PointsGroup, None]:
        """
        Query diagram by device type
        :param device_type: DeviceType
        :return: PointsGroup
        """
        # check if the category exists ...
        group = self.data.get(device_type.value, None)

        return group

    def get_data_dict(self) -> Dict[str, Union[str, int, float, Dict[str, Union[GraphicLocation, MapLocation]]]]:
        """
        get the properties dictionary to save
        :return: dictionary to serialize
        """
        data = {category: group.get_dict() for category, group in self.data.items()}

        return {'type': self.diagram_type.value,
                'idtag': self.idtag,
                'name': self.name,
                "use_flow_based_width": self.use_flow_based_width,
                "min_branch_width": self.min_branch_width,
                "max_branch_width": self.max_branch_width,
                "min_bus_width": self.min_bus_width,
                "max_bus_width": self.max_bus_width,
                "arrow_size": self.arrow_size,
                "use_api_colors": self.use_api_colors,
                "palette": self.palette.value,
                "default_bus_voltage": self.default_bus_voltage,
                'data': data}

    def parse_data(self,
                   data: Dict[str, Dict[str, Dict[str, Union[int, float, bool, List[Tuple[float, float]]]]]],
                   obj_dict: Dict[str, Dict[str, ALL_DEV_TYPES]],
                   logger: Logger):
        """
        Parse file data ito this class
        :param data: json dictionary
        :param obj_dict: dictionary of circuit objects by type to fincd the api objects back from file loading
        :param logger: logger
        """
        self.data = dict()

        self.name = data['name']

        self.use_flow_based_width: bool = data.get("use_flow_based_width", False)
        self.min_branch_width: float = data.get("min_branch_width", 1)
        self.max_branch_width: float = data.get("max_branch_width", 5)
        self.min_bus_width: float = data.get("min_bus_width", 1)
        self.max_bus_width: float = data.get("max_bus_width", 20)
        self.arrow_size: float = data.get("arrow_size", 1)

        palette_name: str = data.get("palette", 'VeraGrid')
        if palette_name in [a.value for a in Colormaps]:
            self.palette = Colormaps(palette_name)
        else:
            self.palette = Colormaps.VeraGrid

        self.default_bus_voltage = data.get("default_bus_voltage", 10)
        self.use_api_colors = data.get("use_api_colors", False)

        if data['type'] == 'bus-branch':
            self.diagram_type = DiagramType.Schematic
        else:
            self.diagram_type = DiagramType(data['type'])

        for category, loc_dict in data['data'].items():
            points_group = PointsGroup(name=category)
            points_group.parse_data(data=loc_dict,
                                    obj_dict=obj_dict.get(category, dict()),
                                    logger=logger,
                                    category=category)
            self.data[category] = points_group

    def build_graph(self) -> Tuple[nx.MultiDiGraph, List[Bus | FluidNode | Transformer3W | TransformerNW]]:
        """
        Returns a networkx MultiDiGraph object of the grid.
        return MultiDiGraph, List[BusGraphicObject
        """
        graph = nx.MultiDiGraph()

        node_devices = list()  # visible node-like diagram anchors

        # Add buses, cn, bus-bars --------------------------------------------------------------------------------------
        node_count = 0
        graph_node_dictionary = dict()

        for dev_tpe in [DeviceType.BusDevice, DeviceType.BusBarDevice]:

            device_groups = self.data.get(dev_tpe.value, None)

            if device_groups:

                for i, (idtag, location) in enumerate(device_groups.locations.items()):
                    api_object: ALL_DEV_TYPES = location.api_object
                    skip_internal_bus: bool = dev_tpe == DeviceType.BusDevice and api_object.graphic_type == BusGraphicType.Internal

                    # Internal anchor buses such as Transformer3W.bus0 and TransformerNW.bus0 are not visible nodes in the
                    # schematic. They must be skipped here so later remapping can bind their idtag to
                    # the owning visible device instead of leaving an isolated dead node in the graph.
                    if skip_internal_bus:
                        skip_internal_bus = skip_internal_bus
                    else:
                        # Each node receives explicit electrical metadata so the GUI layout
                        # can build stable hierarchical placements without re-inferring state.
                        add_node_layout_data(graph=graph, node_index=node_count, api_object=api_object)
                        graph_node_dictionary[idtag] = node_count
                        node_devices.append(api_object)
                        node_count += 1

        # Add fluid nodes ----------------------------------------------------------------------------------------------
        fluid_node_groups = self.data.get(DeviceType.FluidNodeDevice.value, None)
        if fluid_node_groups:
            for i, (idtag, location) in enumerate(fluid_node_groups.locations.items()):
                # Fluid nodes share the electrical layer of the bus they are attached to.
                add_node_layout_data(graph=graph, node_index=node_count, api_object=location.api_object)
                graph_node_dictionary[idtag] = node_count

                if location.api_object.bus is not None:
                    # the electrical bus location is the same
                    graph_node_dictionary[location.api_object.bus.idtag] = node_count

                node_devices.append(location.api_object)
                node_count += 1

        # Add multi-winding transformers ------------------------------------------------------------------------------
        tr3_groups = self.data.get(DeviceType.Transformer3WDevice.value, None)
        if tr3_groups:
            for i, (idtag, location) in enumerate(tr3_groups.locations.items()):
                # The internal transformer bus defines the voltage layer for the device symbol.
                add_node_layout_data(graph=graph, node_index=node_count, api_object=location.api_object)
                graph_node_dictionary[idtag] = node_count

                if location.api_object.bus0 is not None:
                    # the electrical bus location is the same
                    graph_node_dictionary[location.api_object.bus0.idtag] = node_count

                node_devices.append(location.api_object)
                node_count += 1

        tr_nw_groups = self.data.get(DeviceType.TransformerNwDevice.value, None)
        if tr_nw_groups:
            for i, (idtag, location) in enumerate(tr_nw_groups.locations.items()):
                # The internal transformer bus defines the voltage layer for the device symbol.
                add_node_layout_data(graph=graph, node_index=node_count, api_object=location.api_object)
                graph_node_dictionary[idtag] = node_count

                if location.api_object.bus0 is not None:
                    # the electrical bus location is the same
                    graph_node_dictionary[location.api_object.bus0.idtag] = node_count

                node_devices.append(location.api_object)
                node_count += 1

        # Add the electrical branches ----------------------------------------------------------------------------------
        for dev_type in [DeviceType.LineDevice,
                         DeviceType.Transformer2WDevice,
                         DeviceType.WindingDevice,
                         DeviceType.UpfcDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.bus_from.idtag, None)
                    t = graph_node_dictionary.get(branch.bus_to.idtag, None)

                    if f is not None and t is not None:
                        impedance = branch.get_weight()
                        if dev_type == DeviceType.Transformer2WDevice or dev_type == DeviceType.WindingDevice:
                            impedance *= 1e-3
                        else:
                            impedance = impedance
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=impedance)

        for dev_type in [DeviceType.DCLineDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.bus_from.idtag, None)
                    t = graph_node_dictionary.get(branch.bus_to.idtag, None)

                    if f is not None and t is not None:
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=branch.get_weight())

        for dev_type in [DeviceType.HVDCLineDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.bus_from.idtag, None)
                    t = graph_node_dictionary.get(branch.bus_to.idtag, None)

                    if f is not None and t is not None:
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=max(branch.get_weight(), 0.01))

        for dev_type in [DeviceType.VscDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.bus_from.idtag, None)
                    t = graph_node_dictionary.get(branch.bus_to.idtag, None)

                    if f is not None and t is not None:
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=max(branch.get_weight(), 0.01))

        for dev_type in [DeviceType.SwitchDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.bus_from.idtag, None)
                    t = graph_node_dictionary.get(branch.bus_to.idtag, None)

                    if f is not None and t is not None:
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=max(branch.get_weight(), 0.001))

        # Add fluid branches -------------------------------------------------------------------------------------------
        for dev_type in [DeviceType.FluidPathDevice]:

            groups = self.data.get(dev_type.value, None)

            if groups:
                for i, (idtag, location) in enumerate(groups.locations.items()):
                    branch = location.api_object
                    f = graph_node_dictionary.get(branch.source.idtag, None)
                    t = graph_node_dictionary.get(branch.target.idtag, None)

                    if f is not None and t is not None:
                        add_branch_layout_edge(graph=graph,
                                               from_idx=f,
                                               to_idx=t,
                                               branch=branch,
                                               dev_tpe=dev_type,
                                               raw_impedance=0.01)

        return graph, node_devices

    def get_boundaries(self):
        """
        Get the graphic representation boundaries
        :return: min_x, max_x, min_y, max_y
        """
        min_x = sys.maxsize
        min_y = sys.maxsize
        max_x = -sys.maxsize
        max_y = -sys.maxsize

        # shrink selection only
        for tpe, group in self.data.items():
            for key, location in group.locations.items():
                x = location.x
                y = location.y
                max_x = max(max_x, x)
                min_x = min(min_x, x)
                max_y = max(max_y, y)
                min_y = min(min_y, y)

        return min_x, max_x, min_y, max_y

    def set_size_constraints(self,
                             use_flow_based_width: bool = False,
                             min_branch_width: int = 5,
                             max_branch_width=5,
                             min_bus_width=20,
                             max_bus_width=20,
                             arrow_size=20):
        """
        Set the size constraints
        :param use_flow_based_width:
        :param min_branch_width:
        :param max_branch_width:
        :param min_bus_width:
        :param max_bus_width:
        :param arrow_size:
        """
        self.use_flow_based_width: bool = use_flow_based_width
        self.min_branch_width: float = min_branch_width
        self.max_branch_width: float = max_branch_width
        self.min_bus_width: float = min_bus_width
        self.max_bus_width: float = max_bus_width
        self.arrow_size = arrow_size
