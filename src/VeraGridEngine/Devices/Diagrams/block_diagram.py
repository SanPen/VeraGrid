# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, Any, Sequence, List, Tuple
from dataclasses import dataclass


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
    elbow_points: List[Tuple[float, float]] = None
    
    def __post_init__(self):
        if self.elbow_points is None:
            self.elbow_points = []

    def get_connection_dict(self):
        """
        get as a dictionary point
        :return:
        """
        return {'from_uid': self.from_uid,
                'to_uid': self.to_uid,
                'port_number_from': self.port_number_from,
                'port_number_to': self.port_number_to,
                'color': self.color,
                'elbow_points': self.elbow_points}

    def copy(self):
        return BlockDiagramConnection(
            from_uid=self.from_uid,
            to_uid=self.to_uid,
            port_number_from=self.port_number_from,
            port_number_to=self.port_number_to,
            color=self.color,
            elbow_points=list(self.elbow_points)
        )


class BlockDiagram:
    """
    Diagram
    """

    # Todo: add parse and to_dict functions

    def __init__(self) -> None:
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
        # diag.block_counters = self.block_counters

        diag.node_data = {key: val.copy() for key, val in self.node_data.items()}
        diag.con_data = {key: val.copy() for key, val in self.con_data.items()}

        return diag

    def add_node(self,
                 name: str,
                 x: float,
                 y: float,
                 tpe: str,
                 device_uid: int,
                 api_object_name: str = "",
                 state_ins: int = 0,
                 state_outs: Sequence[str] | None = None,
                 algeb_ins: int = 0,
                 algeb_outs: Sequence[str] | None = None,
                 color=None,
                 subdiagram: BlockDiagram | None = None):
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

        self.node_data[device_uid] = BlockDiagramNode(
            name=name,
            x=x,
            y=y,
            tpe=tpe,
            device_uid=device_uid,
            api_object_name=api_object_name,
            state_ins=state_ins,
            state_outs=list() if state_outs is None else state_outs,
            algeb_ins=algeb_ins,
            algeb_outs=list() if algeb_outs is None else algeb_outs,
            color="#C0C0C0" if color is None else color,  # light blue as default
            sub_diagram=subdiagram
        )

    def add_branch(self,
                   connectionitem_uid: int,
                   device_uid_from: int,
                   device_uid_to: int,
                   port_number_from: int,
                   port_number_to: int,
                   color: str,
                   elbow_points: List[Tuple[float, float]] = None):
        """
        :param connectionitem_uid:
        :param device_uid_from:
        :param device_uid_to:
        :param port_number_from:
        :param port_number_to:
        :param color:
        :param elbow_points:
        :return:
        """

        self.con_data[connectionitem_uid] = BlockDiagramConnection(
            from_uid=device_uid_from,
            to_uid=device_uid_to,
            port_number_from=port_number_from,
            port_number_to=port_number_to,
            color=color,
            elbow_points=elbow_points if elbow_points is not None else []
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

    def to_dict(self):
        """
        to dictionary function
        """
        return {
            "status": self.status,
            # "block_counters": self.block_counters,
            "nodes_data": self.get_node_data_dict(),
            "cons_data": self.get_con_data_dict()
        }


    def parse(self, data: Dict[str, Any]):
        """

        :param data:
        :return:
        """

        self.parse_nodes(data["nodes_data"])
        self.parse_branches(data["cons_data"])
        self.status = data["status"]


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
                elbow_points=con.get('elbow_points', [])
            ))



