# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
import webbrowser
from typing import TYPE_CHECKING, List, Union

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsItemGroup, QMenu
from VeraGrid.Gui.Diagrams.MapWidget.Branches.map_line_polyline import MapLinePolyline
from VeraGrid.Gui.Diagrams.MapWidget.Branches.map_line_segment import MapLineSegment
from VeraGridEngine.Devices.Branches.line_locations import LineLocation
from VeraGridEngine.Devices.types import BRANCH_TYPES, FluidPath
from VeraGridEngine.enumerations import DeviceType
from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, DEACTIVATED
from VeraGrid.Gui.Diagrams.generic_graphics import GenericDiagramWidget
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.DeviceEditors.device_editor_factory import build_device_editor_dialog
from VeraGrid.Gui.messages import error_msg
from VeraGrid.Gui.messages import yes_no_question

if TYPE_CHECKING:
    from VeraGrid.Gui.Diagrams.MapWidget.Branches.line_location_graphic_item import LineLocationGraphicItem
    from VeraGrid.Gui.Diagrams.MapWidget.Substation.substation_graphic_item import SubstationGraphicItem
    from VeraGrid.Gui.Diagrams.MapWidget.Substation.voltage_level_graphic_item import VoltageLevelGraphicItem
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapLineContainer(GenericDiagramWidget, QGraphicsItemGroup):
    """
    Represents a polyline in the map
    """

    def __init__(self,
                 editor: GridMapWidget,
                 api_object: Union[BRANCH_TYPES, FluidPath],
                 draw_labels: bool = True):
        """

        :param editor:
        :param api_object:
        """
        GenericDiagramWidget.__init__(self,
                                      parent=None,
                                      api_object=api_object,
                                      editor=editor,
                                      draw_labels=draw_labels)
        QGraphicsItemGroup.__init__(self)

        self.nodes_list: List[LineLocationGraphicItem] = list()
        self.segments_list: List[MapLineSegment] = list()
        self.polyline: MapLinePolyline | None = None
        self.enabled = True
        self.draw_labels: bool = draw_labels
        self.style: Qt.PenStyle = Qt.PenStyle.SolidLine
        self.color: QColor = QColor(self.api_object.color)
        self.color.setAlpha(128)
        self.width: float = self.editor.diagram.min_branch_width
        self.arrow_width: float = self.editor.diagram.arrow_size
        self.segments_drawn: bool = False
        self._context_lat: float | None = None
        self._context_lon: float | None = None
        self._context_scene_pos: QPointF | None = None
        self._last_export_color: QColor | None = None
        self._last_export_style: Qt.PenStyle | None = None
        self._last_export_power_from: complex | None = None
        self._last_export_power_to: complex | None = None
        self._last_export_hvdc_power_from: float | None = None
        self._last_export_hvdc_power_to: float | None = None

    @property
    def api_object(self) -> Union[BRANCH_TYPES, FluidPath]:
        return self._api_object

    @property
    def editor(self) -> GridMapWidget:
        return self._editor

    def _ensure_polyline(self) -> None:
        """
        Create the polyline item if needed and add it to the scene.
        """
        if self.polyline is None:
            self.polyline = MapLinePolyline(container=self, width=self.width)
            self.editor.add_to_scene(graphic_object=self.polyline)

    def clean_polyline(self) -> None:
        """
        Remove the polyline item from the scene.
        """
        if self.polyline is not None:
            self.editor.diagram_scene.removeItem(self.polyline)
            self.polyline = None

    def update_polyline_path(self) -> None:
        """
        Rebuild the polyline geometry from segment endpoints.
        """
        if len(self.segments_list) == 0:
            if self.polyline is not None:
                self.polyline.set_path_points(list())
                self.polyline.setVisible(False)
            return

        self._ensure_polyline()

        points: List[QPointF] = list()
        points.append(self.segments_list[0].pos1)
        for segment in self.segments_list:
            points.append(segment.pos2)

        if self.polyline is not None:
            self.polyline.set_path_points(points)
            self.polyline.setVisible(True)

    def set_handles_visible(self, is_visible: bool) -> None:
        """
        Show or hide waypoint handles for this line.

        :param is_visible: visibility flag
        """
        if is_visible:
            self._attach_segments_to_scene()
        else:
            self._detach_segments_from_scene()

        for node in self.nodes_list:
            if not is_visible and node.isSelected():
                node.setSelected(False)
            node.setVisible(is_visible)
            node.setEnabled(is_visible)

    def on_polyline_mouse_press(self, event) -> None:
        """
        Handle clicks on the line polyline.
        """
        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)

    def set_width_scale(self, width: float, arrow_width: float):
        """
        Set the width scale of the line
        :param width:
        :param arrow_width:
        """
        if self.width == width and self.arrow_width == arrow_width:
            return
        else:
            pass

        self.width = width
        self.arrow_width = arrow_width
        for segment in self.segments_list:
            # pen = segment.pen()  # get the current pen
            # pen.setWidthF(val * segment.width)  # Set the fractional thickness of the line
            segment.set_width(width)  # Assign the pen to the line item
            segment.set_arrow_sizes(arrow_width)
        if self.polyline is not None:
            self.polyline.set_width(width)
        # self.setScale(branch_scale)

    def clean_segments(self) -> None:
        """
        Remove all segments from the scene
        """
        for segment in self.segments_list:
            if segment.scene() is not None:
                self.editor.diagram_scene.removeItem(segment)
            else:
                pass

        self.segments_list = list()
        self.segments_drawn = False

    def _attach_segments_to_scene(self) -> None:
        """
        Add all segment graphics to the scene for edit mode rendering.
        """
        if self.segments_drawn:
            return
        else:
            pass

        for segment in self.segments_list:
            if segment.scene() is None:
                self.editor.add_to_scene(graphic_object=segment)
            else:
                pass
            segment.set_stroke_visible(True)

        self.segments_drawn = True

    def _detach_segments_from_scene(self) -> None:
        """
        Remove segment graphics from the scene when not editing.
        """
        if not self.segments_drawn:
            return
        else:
            pass

        for segment in self.segments_list:
            segment.set_stroke_visible(False)
            if segment.scene() is not None:
                self.editor.diagram_scene.removeItem(segment)
            else:
                pass

        self.segments_drawn = False

    def clean_nodes(self) -> None:
        """
        Remove all the nodes from the scene
        """
        for node in self.nodes_list:
            self.editor._remove_from_scene(node)

        self.nodes_list = list()

    def clean(self) -> None:
        """
        Clean all graphic elements from the scene
        """
        self.clean_segments()
        self.clean_polyline()
        self.clean_nodes()

    def number_of_nodes(self) -> int:
        """

        :return:
        """
        return len(self.nodes_list)

    def register_new_node(self, node: LineLocationGraphicItem):
        """
        Add node
        :param node: NodeGraphicItem
        """
        self.nodes_list.append(node)

    def add_segment(self, segment: MapLineSegment):
        """
        Add segment
        :param segment: Connector
        """
        self.segments_list.append(segment)
        self.addToGroup(segment)

    def set_colour(self, color: QColor, style: Qt.PenStyle, tool_tip: str = '') -> None:
        """
        Set color and style
        :param color: QColor instance
        :param style: PenStyle instance
        :param tool_tip: tool tip text
        :return:
        """
        export_mode: bool = self.editor.is_video_export_active()
        update_hidden_segments: bool = not export_mode or self.segments_drawn

        # During export, avoid repainting the full line hierarchy when the visible state is unchanged.
        if export_mode:
            if self._last_export_color is not None and self._last_export_style is not None:
                if self._last_export_color == color and self._last_export_style == style:
                    return
                else:
                    pass
            else:
                pass
        else:
            pass

        self.color = QColor(color)
        self.style = style

        # When the map is not in edit mode the visible representation is the polyline, not the hidden segments.
        # Export can therefore skip touching every hidden segment without changing the rendered output.
        if update_hidden_segments:
            for segment in self.segments_list:
                if export_mode:
                    pass
                else:
                    segment.setToolTip(tool_tip)
                segment.set_colour(color=color, style=style)
        else:
            pass

        if self.polyline is not None:
            if export_mode:
                pass
            else:
                self.polyline.setToolTip(tool_tip)
            polyline_pen = QPen(self.color,
                                self.width,
                                self.style,
                                Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin)
            self.polyline.set_pen(polyline_pen)
        else:
            pass

        if export_mode:
            self._last_export_color = QColor(self.color)
            self._last_export_style = self.style
        else:
            self._last_export_color = None
            self._last_export_style = None

    def update_connectors(self) -> None:
        """

        :return:
        """
        for connector in self.segments_list:
            # Avoid rebuilding the same polyline path for every connector.
            connector.update_endings(force=True)
        self.update_polyline_path()

    def end_update(self) -> None:
        """

        :return:
        """

        for segment in self.segments_list:
            segment.end_update()

    def draw_all(self) -> None:
        """

        :return:
        """
        self.clean()

        # get the diagram line locations
        line_locs_info = self.editor.diagram.query_by_type(device_type=DeviceType.LineLocation)

        # draw line locations
        for elm in self.api_object.locations.data:

            if line_locs_info is not None:
                loc_data = line_locs_info.locations.get(elm.idtag, None)
            else:
                loc_data = None

            graphic_obj = self.editor.create_line_location_graphic(line_container=self,
                                                                    api_object=elm,
                                                                    lat=elm.lat if loc_data is None else loc_data.latitude,
                                                                    lon=elm.long if loc_data is None else loc_data.longitude,
                                                                    index=self.number_of_nodes())  # 2.7 ...

            self.register_new_node(node=graphic_obj)

        # second pass: create the segments
        self.redraw_segments()
        self.set_handles_visible(False)

    def remove_node(self, node: LineLocationGraphicItem):
        """

        :param node:
        :return:
        """
        for seg in self.segments_list:
            if seg.first.api_object == node.api_object or seg.second.api_object == node.api_object:
                self.editor.map.diagram_scene.removeItem(seg)

        self.nodes_list.remove(node)
        self.api_object.locations.remove(node.api_object)

        for nod in self.nodes_list:
            if nod.index > node.index:
                nod.index = nod.index - 1

        self.editor.remove_line_location_graphic(node)
        self.redraw_segments()

    def redraw_segments(self) -> None:
        """
        Draw all segments in the line
        If there were previous segments, those are deleted
        """
        segments_were_drawn = self.segments_drawn
        self.clean_segments()
        self._ensure_polyline()

        connection_elements: List[
            Union[LineLocationGraphicItem, SubstationGraphicItem, VoltageLevelGraphicItem]] = list()

        # add the substation from
        substation_from_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_from())
        if substation_from_graphics is not None:
            if substation_from_graphics.valid_coordinates():
                connection_elements.append(substation_from_graphics)
                substation_from_graphics.line_container = self

        # add all the intermediate positions
        connection_elements += self.nodes_list

        # add the substation to
        substation_to_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_to())
        if substation_to_graphics is not None:
            if substation_to_graphics.valid_coordinates():
                connection_elements.append(substation_to_graphics)
                substation_to_graphics.line_container = self

        # br_scale = self.editor.get_branch_width()
        # arrow_scale = self.editor.get_arrow_scale()

        # second pass: create the segments
        for i in range(1, len(connection_elements)):
            elm1 = connection_elements[i - 1]
            elm2 = connection_elements[i]
            # Assuming Connector takes (scene, node1, node2) as arguments
            segment_graphic_object = MapLineSegment(first=elm1,
                                                    second=elm2,
                                                    container=self,
                                                    width=self.editor.diagram.min_branch_width)
            segment_graphic_object.set_stroke_visible(False)

            elm2.needsUpdate = True
            segment_graphic_object.needsUpdate = True

            # register the segment in the line
            self.add_segment(segment=segment_graphic_object)

        self.update_connectors()
        self.set_colour(color=self.color, style=self.style)

        if segments_were_drawn:
            self._attach_segments_to_scene()
        else:
            pass

    def _distance_to_segment(self, point: QPointF, first: QPointF, second: QPointF) -> float:
        """
        Compute the euclidean distance from a point to one segment.
        """
        dx = second.x() - first.x()
        dy = second.y() - first.y()
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            return math.hypot(point.x() - first.x(), point.y() - first.y())

        numerator = ((point.x() - first.x()) * dx) + ((point.y() - first.y()) * dy)
        denominator = (dx * dx) + (dy * dy)
        factor = max(0.0, min(1.0, numerator / denominator))

        projection_x = first.x() + factor * dx
        projection_y = first.y() + factor * dy
        return math.hypot(point.x() - projection_x, point.y() - projection_y)

    def add_node_at_scene_position(self, scene_pos: QPointF) -> None:
        """
        Insert a new waypoint in the nearest line segment to a clicked point.

        :param scene_pos: click position in scene coordinates
        """
        if len(self.segments_list) == 0:
            self.insert_new_node_at_position(0)
            return

        closest_segment_index = 0
        closest_distance = float("inf")

        for i, segment in enumerate(self.segments_list):
            dist = self._distance_to_segment(scene_pos, segment.pos1, segment.pos2)
            if dist < closest_distance:
                closest_distance = dist
                closest_segment_index = i

        self.insert_new_node_at_position(closest_segment_index)

    def _open_street_view_context(self) -> None:
        """
        Open Google Maps for the latest context-menu click location.
        """
        if self._context_lat is not None and self._context_lon is not None:
            url = f"https://www.google.com/maps/?q={self._context_lat},{self._context_lon}"
            webbrowser.open(url)

    def _add_point_from_context(self) -> None:
        """
        Insert one waypoint at the latest context-menu click location.
        """
        if self._context_scene_pos is not None:
            self.add_node_at_scene_position(self._context_scene_pos)

    def _ensure_line_selected_for_actions(self) -> None:
        """
        Ensure this line is present in the current selection for editor actions.
        """
        if self.polyline is not None and not self.polyline.isSelected():
            self.polyline.setSelected(True)

    def _run_merge_selected_lines(self) -> None:
        """
        Run merge operation preserving the clicked line in selection.
        """
        self._ensure_line_selected_for_actions()
        self.editor.merge_selected_lines()

    def _run_split_line_to_substation(self) -> None:
        """
        Run split-to-substation operation preserving the clicked line in selection.
        """
        self._ensure_line_selected_for_actions()
        self.editor.split_line_to_substation()

    def _run_change_line_connection(self) -> None:
        """
        Run line connection change operation preserving the clicked line in selection.
        """
        self._ensure_line_selected_for_actions()
        self.editor.change_line_connection()

    def show_context_menu(self, scene_pos: QPointF, screen_pos: QPoint) -> None:
        """
        Show the line context menu for the given click position.
        """
        menu = QMenu()
        menu.addSection(translate_context_menu_text("Line"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Active"),
                       function_ptr=self.enable_disable_toggle,
                       checkeable=True,
                       checked_value=self.api_object.active)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Draw labels"),
                       function_ptr=self.enable_disable_label_drawing,
                       checkeable=True,
                       checked_value=self.draw_labels)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Editor"),
                       function_ptr=self.call_editor,
                       icon_path=":/Icons/icons/edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Calculate total length"),
                       function_ptr=self.calculate_total_length_toast,
                       icon_path=":/Icons/icons/ruler.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Consolidate selected objects coordinates"),
                       function_ptr=self.editor.consolidate_object_coordinates,
                       icon_path=":/Icons/icons/assign_to_profile.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Merge selected lines"),
                       function_ptr=self._run_merge_selected_lines,
                       icon_path=":/Icons/icons/fusion.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Split line to selected substation (In-Out)"),
                       function_ptr=self._run_split_line_to_substation,
                       icon_path=":/Icons/icons/divide.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Change substation connection of the line"),
                       function_ptr=self._run_change_line_connection,
                       icon_path=":/Icons/icons/move_bus.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot profiles"),
                       function_ptr=self.plot_profiles,
                       icon_path=":/Icons/icons/plot.png")

        self._context_scene_pos = scene_pos
        self._context_lat, self._context_lon = self.editor.to_lat_lon(x=scene_pos.x(), y=scene_pos.y())
        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Open in Street view"),
                       function_ptr=self._open_street_view_context,
                       icon_path=":/Icons/icons/map.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Assign rate to profile"),
                       function_ptr=self.assign_rate_to_profile,
                       icon_path=":/Icons/icons/assign_to_profile.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Assign active state to profile"),
                       function_ptr=self.assign_status_to_profile,
                       icon_path=":/Icons/icons/assign_to_profile.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Add point"),
                       function_ptr=self._add_point_from_context,
                       icon_path=":/Icons/icons/cn_icon.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Delete"),
                       function_ptr=self.delete,
                       icon_path=":/Icons/icons/delete_schematic.png")

        menu.exec_(screen_pos)

    def enable_disable_toggle(self) -> None:
        """
        Toggle line active state and optionally propagate to profiles.
        """
        if self.api_object.active:
            self.set_enable(False)
        else:
            self.set_enable(True)

        if self.editor.circuit.get_time_number() > 0:
            ok = yes_no_question('Do you want to update the time series active status accordingly?',
                                 'Update time series active status')
            if ok:
                self.editor.set_active_status_to_profile(self.api_object, override_question=True)

    def set_enable(self, val: bool = True) -> None:
        """
        Set the enabled state both graphically and in the API object.

        :param val: target state
        """
        self.api_object.active = val
        if self.api_object.active:
            self.style = ACTIVE['style']
            self.color = ACTIVE['color']
        else:
            self.style = DEACTIVATED['style']
            self.color = DEACTIVATED['color']
        self.set_colour(self.color, self.style)

    def enable_disable_label_drawing(self) -> None:
        """
        Toggle arrow label rendering state.
        """
        self.draw_labels = not self.draw_labels
        for segment in self.segments_list:
            segment.draw_labels = self.draw_labels

    def open_device_editor(self) -> bool:
        """
        Open the editor for this map branch.

        :return: ``True`` when an editor was opened.
        """
        dialog = build_device_editor_dialog(api_object=self.api_object, circuit=self.editor.circuit)
        dialog.exec()
        return True

    def call_editor(self) -> None:
        """
        Open the specific branch editor dialogue.
        """
        self.open_device_editor()

    def plot_profiles(self) -> None:
        """
        Plot branch time series profiles.
        """
        i = self.editor.circuit.get_branches().index(self.api_object)
        self.editor.plot_branch(i, self.api_object)

    def assign_rate_to_profile(self) -> None:
        """
        Assign snapshot rating to the profile.
        """
        self.editor.set_rate_to_profile(self.api_object)

    def assign_status_to_profile(self) -> None:
        """
        Assign snapshot active state to the profile.
        """
        self.editor.set_active_status_to_profile(self.api_object)

    def calculate_total_length_toast(self) -> None:
        """
        Recalculate length and show user feedback.
        """
        total_length = self.calculate_total_length()
        self.editor.gui.show_info_toast(
            message=f"Line length calculated: {total_length:.2f} km. The length property of line "
                    f"{self.api_object.name} has been updated.")

    def substation_to(self):
        """

        :return:
        """
        return self.editor.graphics_manager.query(elm=self.api_object.get_substation_to())

    def substation_from(self):
        """

        :return:
        """
        return self.editor.graphics_manager.query(elm=self.api_object.get_substation_from())

    def insert_new_node_at_position(self, index: int):
        """
        Creates a new node in the list at the given position
        :param index:
        :return:
        """

        # Check if the index is valid
        if 1 <= index < len(self.api_object.locations.data) and len(self.api_object.locations.data) > 1:

            nd1 = self.nodes_list[index]
            nd2 = self.nodes_list[index - 1]

            # Create a new API object for the node. Assuming `api_object.locations.data` holds coordinates or similar data
            new_api_node_data = self.api_object.locations.data[index]

            new_lat = ((nd2.lat + nd1.lat) / 2)
            new_long = ((nd2.lon + nd1.lon) / 2)

            new_api_object = LineLocation(lat=new_lat,
                                          lon=new_long,
                                          z=new_api_node_data.alt,
                                          seq=new_api_node_data.seq,
                                          name=new_api_node_data.name,
                                          idtag=None,  # generates new UUID
                                          code=new_api_node_data.code)

            self.api_object.locations.data.insert(index, new_api_object)

            # Create a new graphical node item

            graphic_obj = self.editor.create_line_location_graphic(line_container=self,
                                                                    api_object=new_api_object,
                                                                    lat=new_api_object.lat,
                                                                    lon=new_api_object.long,
                                                                    index=index)

            idx = 0

            for nod in self.nodes_list:

                if idx >= index:
                    nod.index = nod.index + 1

                idx = idx + 1

            # Add the node to the nodes list
            self.nodes_list.insert(index, graphic_obj)

            graphic_obj.update_position()

            # Update connectors if necessary
            self.redraw_segments()

            # Return the newly created node
            return graphic_obj

        elif len(self.api_object.locations.data) == 0:

            substation_from_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_from())
            substation_to_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_to())

            nd1 = substation_from_graphics
            nd2 = substation_to_graphics

            new_lat = ((nd2.lat + nd1.lat) / 2)
            new_long = ((nd2.lon + nd1.lon) / 2)

            new_api_object = LineLocation(lat=new_lat,
                                          lon=new_long,
                                          z=0,
                                          seq=0,
                                          name="New node",
                                          idtag="",
                                          code="")

            self.api_object.locations.data.insert(0, new_api_object)

            # Create a new graphical node item

            graphic_obj = self.editor.create_line_location_graphic(line_container=self,
                                                                    api_object=new_api_object,
                                                                    lat=new_api_object.lat,
                                                                    lon=new_api_object.long,
                                                                    index=0)

            # Add the node to the nodes list
            self.nodes_list.insert(0, graphic_obj)

            graphic_obj.update_position()

            # Update connectors if necessary
            self.redraw_segments()

            # Return the newly created node
            return graphic_obj

        elif 0 == index or index >= len(self.api_object.locations.data) - 1:

            substation_from_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_from())
            substation_to_graphics = self.editor.graphics_manager.query(elm=self.api_object.get_substation_to())

            nd1 = substation_from_graphics
            nd2 = substation_to_graphics

            if index == 0:
                nd2 = self.nodes_list[0]

            if index >= len(self.nodes_list):
                nd1 = self.nodes_list[len(self.nodes_list) - 1]

            new_lat = ((nd2.lat + nd1.lat) / 2)
            new_long = ((nd2.lon + nd1.lon) / 2)

            new_api_object = LineLocation(lat=new_lat,
                                          lon=new_long,
                                          z=0,
                                          seq=0,
                                          name="New node",
                                          idtag="",
                                          code="")

            self.api_object.locations.data.insert(index, new_api_object)

            # Create a new graphical node item

            graphic_obj = self.editor.create_line_location_graphic(line_container=self,
                                                                    api_object=new_api_object,
                                                                    lat=new_api_object.lat,
                                                                    lon=new_api_object.long,
                                                                    index=index)

            idx = 0

            for nod in self.nodes_list:

                if idx >= index:
                    nod.index = nod.index + 1

                idx = idx + 1

            # Add the node to the nodes list
            self.nodes_list.insert(index, graphic_obj)

            graphic_obj.update_position()

            # Update connectors if necessary
            self.redraw_segments()

            # Return the newly created node
            return graphic_obj

        else:
            #     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
            #     logging.info("Invalid node index")
            return None

    def split_line(self, index):
        """
        Split Line
        :param index:
        :return:
        """
        # TODO: Review this and possibly link to existing functions
        if 0 < index < len(self.api_object.locations.data) and len(self.api_object.locations.data) > 3:

            # ln1 = Line()
            # ln1.set_data_from(self.api_object)
            ln1 = self.api_object.copy()

            # ln2 = Line()
            # ln2.set_data_from(self.api_object)
            ln2 = self.api_object.copy()

            first_list = self.api_object.locations.data[:index]
            second_list = self.api_object.locations.data[index:]

            ln1.locations.data = first_list
            ln2.locations.data = second_list

            idx = 0
            for api_obj in first_list:
                api_obj.lat = self.nodes_list[idx].lat
                api_obj.long = self.nodes_list[idx].lon
                idx = idx + 1

            for api_obj in second_list:
                api_obj.lat = self.nodes_list[idx].lat
                api_obj.long = self.nodes_list[idx].lon
                idx = idx + 1

            ln1.bus_from = self.api_object.bus_from
            ln2.bus_to = self.api_object.bus_to

            # l1 = self.editor.add_api_line(ln1, original=False)
            # l2 = self.editor.add_api_line(ln2, original=False)

            self.disable_line()

            return first_list, second_list
        else:
            # Handle invalid index
            error_msg("Index out of range or invalid", "split line")
            return list(), list()

    def disable_line(self):
        """

        :return:
        """
        self.enabled = False
        for node in self.nodes_list:
            node.enabled = False

        for line in self.segments_list:
            line.set_enable(val=False)

    def set_arrows_with_power(self, Sf: complex | None, St: complex | None) -> None:
        """

        :param Sf:
        :param St:
        :return:
        """
        export_mode: bool = self.editor.is_video_export_active()
        update_hidden_segments: bool = not export_mode or self.segments_drawn

        # During export, skip rebuilding arrow geometry when the flow values are identical.
        if export_mode:
            if self._last_export_power_from == Sf and self._last_export_power_to == St:
                return
            else:
                pass
        else:
            pass

        # Hidden segments do not contribute to the exported image, so avoid updating their arrow items.
        if update_hidden_segments:
            for segment in self.segments_list:
                segment.set_arrows_with_power(Sf=Sf, St=St)
        else:
            pass

        self._last_export_power_from = Sf
        self._last_export_power_to = St

    def set_arrows_with_hvdc_power(self, Pf: float, Pt: float) -> None:
        """

        :param Pf:
        :param Pt:
        :return:
        """
        export_mode: bool = self.editor.is_video_export_active()
        update_hidden_segments: bool = not export_mode or self.segments_drawn

        # During export, skip rebuilding arrow geometry when the HVDC flow values are identical.
        if export_mode:
            if self._last_export_hvdc_power_from == Pf and self._last_export_hvdc_power_to == Pt:
                return
            else:
                pass
        else:
            pass

        # Hidden segments do not contribute to the exported image, so avoid updating their arrow items.
        if update_hidden_segments:
            for segment in self.segments_list:
                segment.set_arrows_with_hvdc_power(Pf=Pf, Pt=Pt)
        else:
            pass

        self._last_export_hvdc_power_from = Pf
        self._last_export_hvdc_power_to = Pt

    def calculate_total_length(self) -> float:
        """
        Calculate the total length of the line by summing the distances between all waypoints
        using the haversine formula, and update the line's length property. The coordiates used are the
        ones from the api_object, not the graphic objects, in order to avoid undesired recalculations. Issue #23
        
        :return: Total length in kilometers
        """
        from VeraGridEngine.Utils.GeographicalMethods.haversine_distance import haversine_distance

        # Get all connection points (substations and intermediate points)
        connection_points = []
        
        # Add the substation from
        substation_from = self.substation_from()
        if substation_from is not None:
            connection_points.append((substation_from.api_object.latitude, substation_from.api_object.longitude))

        # Add all intermediate points
        for node in self.nodes_list:
            connection_points.append((node.api_object.lat, node.api_object.long))
        
        # Add the substation to
        substation_to = self.substation_to()

        if substation_to is not None:
            connection_points.append((substation_to.api_object.latitude, substation_to.api_object.longitude))

        # Calculate total length by summing distances between consecutive points
        total_length = 0.0
        for i in range(len(connection_points) - 1):
            lat1, lon1 = connection_points[i]
            lat2, lon2 = connection_points[i + 1]
            segment_length = haversine_distance(lat1, lon1, lat2, lon2)
            total_length += segment_length
        
        # Update the line's length property
        if total_length > 0.0:
            self.api_object.length = total_length

        return total_length

    def get_extra_graphics(self):
        """
        This function gets the graphic objects associated to a MapLineContainer
        return: The list of the associated graphic objects, which are the nodes, segments and polyline of the line.
        """
        extra_graphics = self.segments_list + self.nodes_list
        if self.polyline is not None:
            extra_graphics.append(self.polyline)
        return extra_graphics

    def delete(self):
        """
        Delete this object and all the other objects
        """
        for segment in self.segments_list:
            segment.delete_from_associations()

        self.editor.delete_with_dialogue(selected=[self], delete_from_db=False)
