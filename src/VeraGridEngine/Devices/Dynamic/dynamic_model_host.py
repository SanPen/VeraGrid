# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Dict, Any, Sequence
from dataclasses import dataclass
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.enumerations import DeviceType


@dataclass
class BlockDiagramNode:
    """
    BlockDiagramNode
    """
    name: str
    x: float
    y: float
    tpe: str
    device_uid: int
    api_object_name: str
    state_ins: int
    state_outs: Sequence[str]
    algeb_ins: int
    algeb_outs: Sequence[str]
    color: str
    sub_diagram: "BlockDiagram" = None

    def get_node_dict(self) -> Dict[str, Any]:
        """

        :return:
        """
        data: Dict[str, Any] = {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'tpe': self.tpe,
            'device_uid': self.device_uid,
            'api_object_name': self.api_object_name,
            'state_ins': self.state_ins,
            'state_outs': self.state_outs,
            'algeb_ins': self.algeb_ins,
            'algeb_outs': self.algeb_outs,
            'color': self.color
        }
        if self.sub_diagram is not None:
            data['sub_diagram'] = {
                "nodes": self.sub_diagram.get_node_data_dict(),
                "connections": self.sub_diagram.get_con_data_dict(),
            }
        return data

    def copy(self):
        """
        Deep copy
        :return:
        """
        return BlockDiagramNode(
            name=self.name,
            x=self.x,
            y=self.y,
            tpe=self.tpe,
            device_uid=self.device_uid,
            api_object_name=self.api_object_name,
            state_ins=self.state_ins,
            state_outs=[e for e in self.state_outs],
            algeb_ins=self.algeb_ins,
            algeb_outs=[e for e in self.algeb_outs],
            color=self.color,
            sub_diagram=self.sub_diagram  # should not be a copy but a pointer!
        )


@dataclass
class BlockDiagramConnection:
    """
    BlockDiagramConnection
    """
    from_uid: int
    to_uid: int
    port_number_from: int
    port_number_to: int
    color: str

    def get_connection_dict(self):
        """
        get as a dictionary point
        :return:
        """
        return {'from_uid': self.from_uid,
                'to_uid': self.to_uid,
                'port_number_from': self.port_number_from,
                'port_number_to': self.port_number_to,
                'color': self.color}

    def copy(self):

        return BlockDiagramConnection(
            from_uid=self.from_uid,
            to_uid=self.to_uid,
            port_number_from=self.port_number_from,
            port_number_to=self.port_number_to,
            color=self.color
        )


class BlockDiagram:
    """
    Diagram
    """

    def __init__(self):
        """

        """
        self.status: str | None = None
        self.node_data: Dict[int, BlockDiagramNode] = dict()
        self.con_data: Dict[int, BlockDiagramConnection] = dict()

    def copy(self):
        """
        Deep copy of the block diagram
        :return:
        """
        diag = BlockDiagram()

        diag.status = self.status

        diag.node_data = {key: val.copy() for key, val in self.node_data.items()}
        diag.con_data = {key: val.copy() for key, val in self.con_data.items()}

        return diag

    def add_node(self, name: str, x: float, y: float,
                 tpe: str, device_uid: int, api_object_name: str = "",
                 state_ins: int = 0,
                 state_outs: Sequence[str] = [],
                 algeb_ins: int = 0,
                 algeb_outs: Sequence[str] = [],
                 color=None,
                 subdiagram: BlockDiagram = None):
        """
        :param api_object_name:
        :param state_ins:
        :param state_outs:
        :param algeb_ins:
        :param algeb_outs:
        :param name:
        :param x:
        :param y:
        :param device_uid:
        :param tpe:
        :param color:
        :param subdiagram:
        :return:
        """

        if color is None:
            color = "#C0C0C0"  # light blue
        self.node_data[device_uid] = BlockDiagramNode(
            name=name,
            x=x,
            y=y,
            tpe=tpe,
            device_uid=device_uid,
            api_object_name=api_object_name,
            state_ins=state_ins,
            state_outs=state_outs,
            algeb_ins=algeb_ins,
            algeb_outs=algeb_outs,
            color=color,
            sub_diagram=subdiagram
        )

    def add_branch(self, connectionitem_uid: int, device_uid_from: int, device_uid_to: int,
                   port_number_from: int, port_number_to: int, color: str):
        """
        :param connectionitem_uid:
        :param device_uid_from:
        :param device_uid_to:
        :param port_number_from:
        :param port_number_to:
        :param color:
        :return:
        """

        self.con_data[connectionitem_uid] = BlockDiagramConnection(
            from_uid=device_uid_from,
            to_uid=device_uid_to,
            port_number_from=port_number_from,
            port_number_to=port_number_to,
            color=color
        )

    def get_node_data_dict(self) -> Dict[int, Dict[str, Any]]:
        """

        :return:
        """
        graph_info = {device_uid: node.get_node_dict() for device_uid, node in self.node_data.items()}
        return graph_info

    def get_con_data_dict(self) -> Dict[int, Dict[str, Any]]:
        """

        :return:
        """
        graph_info = {connection_uid: connection.get_connection_dict() for connection_uid, connection in
                      self.con_data.items()}
        return graph_info

    def parse_nodes(self, nodes_data) -> None:
        """
        Parse node data from dictionary
        """
        self.node_data = dict()
        for uid, node in nodes_data.items():
            subdiagram = None
            if "sub_diagram" in node and node["sub_diagram"] is not None:
                subdiagram = BlockDiagram()
                subdiagram.parse_nodes(node["sub_diagram"]["nodes"])
                subdiagram.parse_branches(node["sub_diagram"]["connections"])

            self.node_data[int(uid)] = BlockDiagramNode(
                name=node['name'],
                x=node['x'],
                y=node['y'],
                tpe=node['tpe'],
                device_uid=node['device_uid'],
                api_object_name=node['api_object_name'],
                state_ins=node['state_ins'],
                state_outs=node['state_outs'],
                algeb_ins=node['algeb_ins'],
                algeb_outs=node['algeb_outs'],
                color=node['color'],
                sub_diagram=subdiagram
            )

    def parse_branches(self, con_data) -> None:
        """
        Parse connection data from dictionary
        """
        self.con_data = dict()
        for uid, con in con_data.items():
            self.con_data[int(uid)] = (BlockDiagramConnection(
                from_uid=con['from_uid'],
                to_uid=con['to_uid'],
                port_number_from=con['port_number_from'],
                port_number_to=con['port_number_to'],
                color=con['color'],
            ))


class DynamicModelHost(EditableDevice):
    """
    This class serves to give flexible access to either a template or a custom model
    """

    def __init__(self, name=""):
        """

        :param name:
        """
        super().__init__(name=name,
                         idtag=None,
                         code="",
                         device_type=DeviceType.DynamicModelHostDevice)

        self._template: Block | None = None

        # a custom model always exits although it may be empty
        self._custom_model: Block = Block()
        self._diagram: BlockDiagram = BlockDiagram()

    @property
    def template(self):
        """

        :return:
        """
        return self._template

    @template.setter
    def template(self, val: Block):
        """

        :param val:
        :return:
        """
        if isinstance(val, Block):
            self._template = val
        elif val is None:
            self._template = None
        else:
            raise ValueError(f"Cannot set template with {val}")

    @property
    def custom_model(self):
        """
        Return custom
        :return:
        """
        return self._custom_model

    @custom_model.setter
    def custom_model(self, val: Block):
        """

        :param val:
        :return:
        """
        if isinstance(val, Block):
            self._custom_model = val
        elif val is None:
            self._custom_model = None
        else:
            raise ValueError(f"Cannot set template with {val}")

    @property
    def model(self) -> Block:
        """
        Returns whatever is available with preference to the custom model if any
        :return: DynamicModel (even if it is empty)
        """
        if self.template is None:
            return self.custom_model
        else:
            return self.template

    @model.setter
    def model(self, val: Block):
        if not isinstance(val, Block):
            raise ValueError(f"Cannot set model with {val}")
        self._custom_model = val

    @property
    def diagram(self) -> BlockDiagram:
        """

        :return:
        """
        return self._diagram

    @diagram.setter
    def diagram(self, val: BlockDiagram | Dict[str, Any]):

        if isinstance(val, BlockDiagram):
            self._diagram = val
        elif isinstance(val, dict):
            diagram = BlockDiagram()
            if "nodes" in val:
                diagram.parse_nodes(val["nodes"])
            if "connections" in val:
                diagram.parse_branches(val["connections"])
            self._diagram = diagram
        else:
            raise ValueError(f"Cannot set diagram with {val}")

    def to_dict(self) -> Dict[str, int | Dict[str, List[Dict[str, Any]]]]:
        """
        Generate a dictionary to save
        :return: Data to save
        """
        return {
            "template": self.template.uid if self.template is not None else None,
            "custom_model": self.custom_model.to_dict()
        }

    def parse(self, data: Dict[str, str | Dict[str, List[Dict[str, Any]]]],
              models_dict: Dict[str, RmsModelTemplate]):
        """
        Parse the data
        :param data: data generated by to_dict
        :param models_dict: dictionary of DynamicModel to find the template reference
        """
        template_id = data.get("template", None)
        if template_id is not None:
            self.template = models_dict.get(template_id, None)

        custom_data = data.get("custom_model", None)
        self._custom_model = Block.parse(data=custom_data)

    def empty(self):
        if self._template is None:
            return self._custom_model.empty()
        else:
            return self._template.empty()

    def __eq__(self, other):
        if isinstance(other, DynamicModelHost):

            if self.template is None:
                if other.template is None:
                    return self.custom_model == other.custom_model
                else:
                    return False
            else:
                if other.template is None:
                    return False
                else:
                    return self.template.uid == other.template.uid
        else:
            return False

    def copy(self) -> "DynamicModelHost":
        """
        Deep copy of DynamicModelHost
        :return: DynamicModelHost
        """
        obj = DynamicModelHost()
        obj._custom_model = self._custom_model.copy()
        obj._template = self._template
        return obj
