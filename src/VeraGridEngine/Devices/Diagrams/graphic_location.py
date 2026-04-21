# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class GraphicLocation:
    """
    GraphicLocation
    """

    def __init__(self,
                 api_object: ALL_DEV_TYPES,
                 x: float = 0,
                 y: float = 0,
                 h: float = 80,
                 w: float = 80,
                 r: float = 0,
                 poly_line: Union[None, List[Tuple[int, int]]] = None,
                 layout_metadata: Union[None, Dict[str, Any]] = None,
                 draw_labels: bool = True):
        """
        GraphicLocation
        :param x: x position (px)
        :param y: y position (px)
        :param h: height (px)
        :param w: width (px)
        :param r: rotation (deg)
        :param poly_line: List of points to represent a polyline, if this object is to use one
        :param layout_metadata: Backward-compatible envelope for future schematic layout state
        :param draw_labels: Draw labels?
        :param api_object: object to be linked to this representation
        """
        self.x = x
        self.y = y
        self.h = h
        self.w = w
        self.r = r
        self.poly_line = list() if poly_line is None else poly_line
        self.layout_metadata = dict() if layout_metadata is None else dict(layout_metadata)
        self.draw_labels = draw_labels
        self.api_object = api_object

    def get_properties_dict(self) -> Dict[str, Any]:
        """
        get as a dictionary point
        :return:
        """
        return {'x': self.x,
                'y': self.y,
                'h': self.h,
                'w': self.w,
                'r': self.r,
                'poly_line': self.poly_line,
                'layout_metadata': dict(self.layout_metadata),
                'draw_labels': self.draw_labels,
                'api_object': self.api_object.idtag if self.api_object else ''}

    def copy(self, api_object: ALL_DEV_TYPES | None = None) -> "GraphicLocation":
        """
        Return a detached copy so diagrams do not accidentally share mutable layout state.
        """
        return GraphicLocation(x=self.x,
                               y=self.y,
                               h=self.h,
                               w=self.w,
                               r=self.r,
                               poly_line=deepcopy(self.poly_line),
                               layout_metadata=deepcopy(self.layout_metadata),
                               draw_labels=self.draw_labels,
                               api_object=self.api_object if api_object is None else api_object)

    def __deepcopy__(self, memo: Dict[int, Any]) -> "GraphicLocation":
        """
        Deep-copy the location layout while preserving the API object as a pointer.
        """
        if id(self) in memo:
            return memo[id(self)]

        cpy = self.copy()
        memo[id(self)] = cpy
        return cpy
