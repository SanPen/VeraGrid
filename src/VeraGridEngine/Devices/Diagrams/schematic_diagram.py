# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Any, Dict, Iterable, List, TYPE_CHECKING, Tuple
from VeraGridEngine.Devices.Diagrams.base_diagram import BaseDiagram
from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
from VeraGridEngine.Devices.Diagrams.schematic_layout import (build_default_branch_route,
                                                              build_explicit_attachment_slot_key,
                                                              copy_layout_metadata, get_attachment,
                                                              get_attachment_record,
                                                              get_branch_route_points,
                                                              get_branch_route_record, get_dock,
                                                              get_dock_record,
                                                              is_canonical_attachment_slot,
                                                              parse_schematic_auto_route_style,
                                                              SchematicAttachmentRecord,
                                                              SchematicDockRecord,
                                                              SchematicExplicitAttachmentSlot,
                                                              SchematicRouteRecord,
                                                              parse_schematic_attachment_side,
                                                              parse_schematic_branch_endpoint,
                                                              parse_explicit_attachment_slot_key,
                                                              set_attachment, set_attachment_record,
                                                              set_branch_route_points,
                                                              set_branch_route_record,
                                                              set_dock, set_dock_record,
                                                              should_preserve_route_shape)
from VeraGridEngine.enumerations import (DeviceType,
                                         DiagramType,
                                         SchematicAttachmentOwnerKind,
                                         SchematicAttachmentSide,
                                         SchematicAutoRouteStyle,
                                         SchematicBranchEndpoint,
                                         SchematicRouteKind)

if TYPE_CHECKING:
    from VeraGridEngine.Devices.types import ALL_DEV_TYPES


def get_attachment_owner_kind(owner_device: ALL_DEV_TYPES | None) -> SchematicAttachmentOwnerKind | None:
    """
    Map node device types to persisted attachment slot prefixes.

    :param owner_device: Endpoint owner device.
    :return: Typed slot prefix such as ``BUS`` or ``FLUID``.
    """
    if owner_device is None:
        return None
    elif owner_device.device_type == DeviceType.BusDevice:
        return SchematicAttachmentOwnerKind.BUS
    elif owner_device.device_type == DeviceType.BusBarDevice:
        return SchematicAttachmentOwnerKind.BUS
    elif owner_device.device_type == DeviceType.FluidNodeDevice:
        return SchematicAttachmentOwnerKind.FLUID
    else:
        return None


def get_default_attachment_side(owner_kind: SchematicAttachmentOwnerKind | None,
                                endpoint: SchematicBranchEndpoint) -> SchematicAttachmentSide:
    """
    Choose the compatibility default side for one endpoint.

    :param owner_kind: Typed owner kind.
    :param endpoint: Typed branch endpoint.
    :return: Typed compatibility side.
    """
    if owner_kind == SchematicAttachmentOwnerKind.BUS:
        return SchematicAttachmentSide.BOTTOM
    elif endpoint == SchematicBranchEndpoint.FROM:
        return SchematicAttachmentSide.RIGHT
    elif endpoint == SchematicBranchEndpoint.TO:
        return SchematicAttachmentSide.LEFT
    else:
        return SchematicAttachmentSide.DEFAULT


def get_side_from_slot_tuple(
        slot_tuple: Tuple[SchematicAttachmentOwnerKind, SchematicAttachmentSide, int] | None
) -> SchematicAttachmentSide | None:
    """
    Convert one explicit slot tuple into a typed compatibility side.

    :param slot_tuple: Parsed explicit slot tuple.
    :return: Typed side when the tuple is present and valid.
    """
    if slot_tuple is None:
        return None
    else:
        return slot_tuple[1]


def build_explicit_attachment_slot(owner_kind: SchematicAttachmentOwnerKind,
                                   side: SchematicAttachmentSide,
                                   order: int) -> SchematicExplicitAttachmentSlot:
    """
    Build one typed explicit attachment slot for runtime use.

    :param owner_kind: Typed owner kind.
    :param side: Typed attachment side.
    :param order: One-based slot order.
    :return: Typed explicit attachment slot.
    """
    return SchematicExplicitAttachmentSlot(owner_kind=owner_kind, side=side, order=order)


class SchematicDiagram(BaseDiagram):
    """
    Diagram
    """

    def __init__(self, idtag=None, name=''):
        """

        :param name: Diagram name
        """
        BaseDiagram.__init__(self, idtag=idtag, name=name, diagram_type=DiagramType.Schematic)

    def update_xy(self, api_object: ALL_DEV_TYPES, x: int, y: int) -> None:
        """
        Update the element xy position
        :param api_object: Any DB object
        :param x: x position in px
        :param y: y position in px
        """
        location = self.query_point(api_object)
        if location:
            location.x = x
            location.y = y

    def update_graphic_location(self,
                                api_object: ALL_DEV_TYPES,
                                x: float = 0.0,
                                y: float = 0.0,
                                w: float = 0.0,
                                h: float = 0.0,
                                r: float = 0.0,
                                draw_labels: bool = True) -> GraphicLocation:
        """
        Update basic schematic geometry while preserving any route and attachment metadata already persisted.
        """
        location = self._get_or_create_graphic_location(api_object)
        location.x = x
        location.y = y
        location.w = w
        location.h = h
        location.r = r
        location.draw_labels = draw_labels
        location.api_object = api_object
        return location

    def copy_layout_state(self,
                          source_api_object: ALL_DEV_TYPES,
                          target_api_object: ALL_DEV_TYPES,
                          include_geometry: bool = False) -> GraphicLocation | None:
        """
        Copy persisted schematic route and attachment state from one device to another.
        """
        source_location = self.query_point(source_api_object)

        if source_location is None:
            return None

        copied_location = source_location.copy()
        copied_location.api_object = target_api_object

        if not include_geometry:
            copied_location.x = 0.0
            copied_location.y = 0.0
            copied_location.w = 0.0
            copied_location.h = 0.0
            copied_location.r = 0.0

        self.set_point(device=target_api_object, location=copied_location)
        return copied_location

    def _get_or_create_graphic_location(self, api_object: ALL_DEV_TYPES) -> GraphicLocation:
        """
        Return an existing schematic location or create a placeholder entry for compatibility-layer updates.
        """
        location: GraphicLocation = self.query_point(api_object)

        if location is None:
            location = GraphicLocation(api_object=api_object)
            self.set_point(device=api_object, location=location)

        return location

    def get_layout_metadata(self, api_object: ALL_DEV_TYPES) -> Dict[str, Any]:
        """
        Return a defensive copy of the persisted schematic layout metadata for this device.
        """
        location = self._get_or_create_graphic_location(api_object)
        return copy_layout_metadata(location)

    def get_branch_route_points(self, api_object: ALL_DEV_TYPES) -> List[Tuple[float, float]]:
        """
        Return route points using the compatibility layer that understands both legacy and structured storage.
        """
        location = self._get_or_create_graphic_location(api_object)
        return get_branch_route_points(location)

    def should_preserve_branch_route_shape(self, api_object: ALL_DEV_TYPES) -> bool:
        """
        Determine whether a branch should keep its persisted interior route elbows.

        :param api_object: Branch API object.
        :return: ``True`` when persisted route elbows should be preserved.
        """
        location = self._get_or_create_graphic_location(api_object)
        route_record: SchematicRouteRecord | None = get_branch_route_record(location=location)

        if route_record is None:
            return False
        else:
            route_payload: Dict[str, Any] = {
                "points": list(route_record.points),
                "kind": route_record.kind.value if route_record.kind is not None else "",
                "locked": route_record.locked,
            }
            return should_preserve_route_shape(route=route_payload)

    def set_branch_route_points(self,
                                api_object: ALL_DEV_TYPES,
                                points: Iterable[Tuple[float, float]],
                                kind: SchematicRouteKind | str | None = SchematicRouteKind.AUTO_POLYLINE,
                                locked: bool | None = False,
                                route_style: SchematicAutoRouteStyle | str | None = None) -> Dict[str, Any]:
        """
        Persist route points through the compatibility layer while keeping legacy polyline storage in sync.

        :param api_object: Branch API object.
        :param points: Route points.
        :param kind: Route kind enum.
        :param locked: Locked-state flag.
        :param route_style: Automatic route-style enum.
        :return: Updated layout metadata.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_branch_route_points(location=location,
                                       points=points,
                                       kind=kind,
                                       locked=locked,
                                       route_style=route_style)

    def sync_branch_route_points(self,
                                 api_object: ALL_DEV_TYPES,
                                 points: Iterable[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Update route points while preserving existing route kind and lock state.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_branch_route_points(location=location,
                                       points=points,
                                       kind=None,
                                       locked=None,
                                       route_style=None)

    def get_branch_route_record(self, api_object: ALL_DEV_TYPES) -> SchematicRouteRecord | None:
        """
        Return the typed route record for one branch.

        :param api_object: Branch API object.
        :return: Typed route record or ``None`` when no structured route has been stored.
        """
        location: GraphicLocation = self._get_or_create_graphic_location(api_object)
        return get_branch_route_record(location=location)

    def get_branch_auto_route_style(self, api_object: ALL_DEV_TYPES) -> SchematicAutoRouteStyle:
        """
        Return the persisted automatic route style for one branch.

        :param api_object: Branch API object.
        :return: Branch-specific automatic route-style enum.
        """
        route_record: SchematicRouteRecord | None = self.get_branch_route_record(api_object=api_object)

        if route_record is None:
            return SchematicAutoRouteStyle.STRAIGHT
        elif route_record.route_style is None:
            return SchematicAutoRouteStyle.STRAIGHT
        else:
            return route_record.route_style

    def set_branch_auto_route_style(self,
                                    api_object: ALL_DEV_TYPES,
                                    route_style: SchematicAutoRouteStyle | str | None) -> SchematicAutoRouteStyle:
        """
        Persist the automatic route style for one branch.

        :param api_object: Branch API object.
        :param route_style: Requested route-style enum.
        :return: Effective branch-specific route-style enum.
        """
        location: GraphicLocation = self._get_or_create_graphic_location(api_object)
        route_record: SchematicRouteRecord | None = get_branch_route_record(location=location)

        if route_record is None:
            route_record = SchematicRouteRecord()
        else:
            pass

        route_record.route_style = parse_schematic_auto_route_style(route_style=route_style)

        if route_record.route_style is None:
            route_record.route_style = SchematicAutoRouteStyle.STRAIGHT
        else:
            pass

        set_branch_route_record(location=location, route_record=route_record)
        return route_record.route_style

    def upgrade_legacy_branch_layout(self,
                                     api_object: ALL_DEV_TYPES,
                                     start: Tuple[float, float],
                                     end: Tuple[float, float]) -> Dict[str, Any]:
        """
        Fill missing structured branch layout metadata for legacy diagrams.
        """
        location = self._get_or_create_graphic_location(api_object)
        attachment_records: Dict[SchematicBranchEndpoint, SchematicAttachmentRecord] = (
            self.sync_branch_attachment_records(api_object=api_object)
        )
        route_points: List[Tuple[float, float]] = get_branch_route_points(location=location)
        route_record: SchematicRouteRecord | None = get_branch_route_record(location=location)

        if len(route_points) >= 2:
            if route_record is None:
                self.set_branch_route_points(api_object=api_object,
                                             points=route_points,
                                             kind=SchematicRouteKind.MANUAL_POLYLINE,
                                             locked=False)
            else:
                pass
        else:
            from_order: int | None = None
            to_order: int | None = None

            if SchematicBranchEndpoint.FROM in attachment_records:
                from_order = attachment_records[SchematicBranchEndpoint.FROM].order
            else:
                pass

            if SchematicBranchEndpoint.TO in attachment_records:
                to_order = attachment_records[SchematicBranchEndpoint.TO].order
            else:
                pass

            synthesized_route = build_default_branch_route(start=start,
                                                           end=end,
                                                           start_order=from_order,
                                                           end_order=to_order,
                                                           route_style=self.get_branch_auto_route_style(api_object))
            self.set_branch_route_points(api_object=api_object,
                                         points=synthesized_route,
                                         kind=SchematicRouteKind.AUTO_POLYLINE,
                                         locked=False)

        return self.get_layout_metadata(api_object=api_object)

    def get_attachment_record(self,
                              api_object: ALL_DEV_TYPES,
                              endpoint: SchematicBranchEndpoint | str) -> SchematicAttachmentRecord:
        """
        Return one typed attachment record for runtime logic.

        :param api_object: Branch API object.
        :param endpoint: Runtime endpoint enum or persisted string.
        :return: Typed attachment record.
        """
        location = self._get_or_create_graphic_location(api_object)
        return get_attachment_record(location=location, endpoint=endpoint)

    def set_attachment_record(self,
                              api_object: ALL_DEV_TYPES,
                              endpoint: SchematicBranchEndpoint | str,
                              attachment_record: SchematicAttachmentRecord) -> Dict[str, Any]:
        """
        Persist one typed attachment record through the compatibility layer.

        :param api_object: Branch API object.
        :param endpoint: Runtime endpoint enum or persisted string.
        :param attachment_record: Typed attachment record.
        :return: Updated layout metadata.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_attachment_record(location=location, endpoint=endpoint, attachment_record=attachment_record)

    def get_attachment(self, api_object: ALL_DEV_TYPES, endpoint: str) -> Dict[str, Any]:
        """
        Return persisted attachment metadata for a branch endpoint or dockable child.
        """
        location = self._get_or_create_graphic_location(api_object)
        return get_attachment(location=location, endpoint=endpoint)

    def set_attachment(self, api_object: ALL_DEV_TYPES, endpoint: str, attachment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persist attachment metadata through the compatibility layer.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_attachment(location=location, endpoint=endpoint, attachment=attachment)

    def get_dock_record(self, api_object: ALL_DEV_TYPES) -> SchematicDockRecord:
        """
        Return one typed dock record for runtime logic.

        :param api_object: Injection API object.
        :return: Typed dock record.
        """
        location = self._get_or_create_graphic_location(api_object)
        return get_dock_record(location=location)

    def set_dock_record(self, api_object: ALL_DEV_TYPES, dock_record: SchematicDockRecord) -> Dict[str, Any]:
        """
        Persist one typed dock record through the compatibility layer.

        :param api_object: Injection API object.
        :param dock_record: Typed dock record.
        :return: Updated layout metadata.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_dock_record(location=location, dock_record=dock_record)

    def get_dock(self, api_object: ALL_DEV_TYPES) -> Dict[str, Any]:
        """
        Return persisted dock metadata for a bus-connected child device.
        """
        location = self._get_or_create_graphic_location(api_object)
        return get_dock(location=location)

    def set_dock(self, api_object: ALL_DEV_TYPES, dock: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persist dock metadata through the compatibility layer.
        """
        location = self._get_or_create_graphic_location(api_object)
        return set_dock(location=location, dock=dock)

    def sync_attachment(self,
                        api_object: ALL_DEV_TYPES,
                        endpoint: SchematicBranchEndpoint | str,
                        owner_device: ALL_DEV_TYPES | None) -> Dict[str, Any]:
        """
        Update endpoint ownership metadata while preserving any future slot-routing fields already stored.
        """
        endpoint_value: SchematicBranchEndpoint | None = parse_schematic_branch_endpoint(endpoint=endpoint)

        if endpoint_value is None:
            return dict()
        else:
            self.sync_attachment_record(api_object=api_object,
                                        endpoint=endpoint_value,
                                        owner_device=owner_device)

        return self.get_attachment(api_object=api_object, endpoint=endpoint_value.value)

    def sync_attachment_record(self,
                               api_object: ALL_DEV_TYPES,
                               endpoint: SchematicBranchEndpoint,
                               owner_device: ALL_DEV_TYPES | None) -> SchematicAttachmentRecord:
        """
        Update one typed endpoint attachment record for runtime logic.

        :param api_object: Branch API object.
        :param endpoint: Typed branch endpoint.
        :param owner_device: Endpoint owner device.
        :return: Typed attachment record.
        """
        # Import branch base lazily to keep the diagram layer light and avoid circular imports
        # during module initialization. The check is only needed when attachment metadata is updated.
        from VeraGridEngine.Devices.Parents.branch_parent import BranchParent

        attachment_record: SchematicAttachmentRecord = self.get_attachment_record(api_object=api_object,
                                                                                  endpoint=endpoint)

        # Synchronize owner metadata first so the attachment always follows the connected device.
        if owner_device is None:
            attachment_record.owner_device_id = ""
            attachment_record.owner_device_type = ""
        else:
            attachment_record.owner_device_id = owner_device.idtag
            attachment_record.owner_device_type = owner_device.device_type.value

        if attachment_record.anchor_x is None or attachment_record.anchor_y is None:
            pass
        else:
            self.set_attachment_record(api_object=api_object,
                                       endpoint=endpoint,
                                       attachment_record=attachment_record)
            return self.get_attachment_record(api_object=api_object, endpoint=endpoint)

        # Choose the compatibility side only when no explicit coordinate anchor has been stored yet.
        owner_kind: SchematicAttachmentOwnerKind | None = get_attachment_owner_kind(owner_device=owner_device)
        default_side: SchematicAttachmentSide = get_default_attachment_side(owner_kind=owner_kind, endpoint=endpoint)

        if attachment_record.side is None:
            attachment_record.side = default_side
        else:
            pass

        if attachment_record.slot_side is None and attachment_record.explicit_slot is None:
            attachment_record.slot_side = attachment_record.side
        else:
            pass

        if attachment_record.terminal_side is None and attachment_record.explicit_terminal is None:
            attachment_record.terminal_side = attachment_record.side
        else:
            pass

        if attachment_record.order is not None:
            attachment_record.order = int(attachment_record.order)
        else:
            if isinstance(api_object, BranchParent) and owner_device is not None:
                inferred_order: int = api_object.get_bus_pos(owner_device)

                if inferred_order != 0:
                    attachment_record.order = inferred_order
                else:
                    attachment_record.order = None
            else:
                attachment_record.order = None

        explicit_slot: Tuple[SchematicAttachmentOwnerKind, SchematicAttachmentSide, int] | None = (
            None if attachment_record.explicit_slot is None
            else (attachment_record.explicit_slot.owner_kind,
                  attachment_record.explicit_slot.side,
                  attachment_record.explicit_slot.order)
        )
        explicit_terminal_key: Tuple[SchematicAttachmentOwnerKind, SchematicAttachmentSide, int] | None = (
            None if attachment_record.explicit_terminal is None
            else (attachment_record.explicit_terminal.owner_kind,
                  attachment_record.explicit_terminal.side,
                  attachment_record.explicit_terminal.order)
        )
        explicit_slot_side: SchematicAttachmentSide | None = get_side_from_slot_tuple(slot_tuple=explicit_slot)
        explicit_terminal_side: SchematicAttachmentSide | None = get_side_from_slot_tuple(
            slot_tuple=explicit_terminal_key
        )

        if not attachment_record.auto_slot:
            if explicit_slot_side is not None:
                attachment_record.side = explicit_slot_side
            elif explicit_terminal_side is not None:
                attachment_record.side = explicit_terminal_side
            elif attachment_record.slot_side is not None and is_canonical_attachment_slot(slot_key=attachment_record.slot_side):
                attachment_record.side = attachment_record.slot_side
            elif attachment_record.terminal_side is not None and is_canonical_attachment_slot(slot_key=attachment_record.terminal_side):
                attachment_record.side = attachment_record.terminal_side
            else:
                pass

            if attachment_record.side is None:
                attachment_record.side = default_side
            else:
                pass

            if explicit_slot is None:
                attachment_record.slot_side = attachment_record.side
            else:
                pass

            if explicit_terminal_key is None:
                if explicit_slot is not None and attachment_record.explicit_slot is not None:
                    attachment_record.explicit_terminal = attachment_record.explicit_slot
                else:
                    attachment_record.terminal_side = attachment_record.side
            else:
                pass

            self.set_attachment_record(api_object=api_object,
                                       endpoint=endpoint,
                                       attachment_record=attachment_record)
            return self.get_attachment_record(api_object=api_object, endpoint=endpoint)
        else:
            pass

        if owner_kind is not None and isinstance(attachment_record.order, int) and attachment_record.order > 0:
            if is_canonical_attachment_slot(slot_key=attachment_record.slot_side):
                attachment_record.explicit_slot = None
                attachment_record.slot_side = None
                attachment_record.explicit_slot = build_explicit_attachment_slot(owner_kind=owner_kind,
                                                                                 side=attachment_record.side,
                                                                                 order=attachment_record.order)
            elif explicit_slot is not None:
                attachment_record.explicit_slot = build_explicit_attachment_slot(owner_kind=owner_kind,
                                                                                 side=attachment_record.side,
                                                                                 order=attachment_record.order)
            else:
                pass

            if is_canonical_attachment_slot(slot_key=attachment_record.terminal_side):
                attachment_record.explicit_terminal = build_explicit_attachment_slot(owner_kind=owner_kind,
                                                                                     side=attachment_record.side,
                                                                                     order=attachment_record.order)
                attachment_record.terminal_side = None
            elif explicit_terminal_key is not None:
                attachment_record.explicit_terminal = build_explicit_attachment_slot(owner_kind=owner_kind,
                                                                                     side=attachment_record.side,
                                                                                     order=attachment_record.order)
            else:
                pass
        else:
            if is_canonical_attachment_slot(slot_key=attachment_record.slot_side):
                attachment_record.slot_side = attachment_record.side
                attachment_record.explicit_slot = None
            elif explicit_slot is not None:
                pass
            else:
                pass

            if is_canonical_attachment_slot(slot_key=attachment_record.terminal_side):
                if explicit_slot is not None and attachment_record.explicit_slot is not None:
                    attachment_record.explicit_terminal = attachment_record.explicit_slot
                    attachment_record.terminal_side = None
                else:
                    attachment_record.terminal_side = attachment_record.side
                    attachment_record.explicit_terminal = None
            elif explicit_terminal_key is not None:
                pass
            else:
                pass

        self.set_attachment_record(api_object=api_object,
                                   endpoint=endpoint,
                                   attachment_record=attachment_record)
        return self.get_attachment_record(api_object=api_object, endpoint=endpoint)

    def sync_branch_attachments(self, api_object: ALL_DEV_TYPES) -> Dict[str, Dict[str, Any]]:
        """
        Synchronize the standard 'from' and 'to' attachment ownership records for branch-like devices.
        """
        attachment_records: Dict[SchematicBranchEndpoint, SchematicAttachmentRecord] = (
            self.sync_branch_attachment_records(api_object=api_object)
        )
        attachments: Dict[str, Dict[str, Any]] = dict()
        endpoint_value: SchematicBranchEndpoint

        for endpoint_value in attachment_records:
            attachments[endpoint_value.value] = self.get_attachment(api_object=api_object,
                                                                    endpoint=endpoint_value.value)

        return attachments

    def sync_branch_attachment_records(self,
                                       api_object: ALL_DEV_TYPES) -> Dict[SchematicBranchEndpoint,
                                                                          SchematicAttachmentRecord]:
        """
        Synchronize the standard typed attachment records for branch-like devices.

        :param api_object: Branch API object.
        :return: Typed endpoint attachment records.
        """
        # Import concrete branch families lazily so diagram persistence does not force eager initialization
        # of the full engine graph while tests import isolated schematic modules.
        from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
        from VeraGridEngine.Devices.Parents.branch_parent import BranchParent

        if not isinstance(api_object, (BranchParent, FluidPath)):
            return dict()
        else:
            obj_from, obj_to, ok = api_object.get_from_and_to_objects()

            if not ok:
                return dict()
            else:
                return {
                    SchematicBranchEndpoint.FROM: self.sync_attachment_record(api_object=api_object,
                                                                             endpoint=SchematicBranchEndpoint.FROM,
                                                                             owner_device=obj_from),
                    SchematicBranchEndpoint.TO: self.sync_attachment_record(api_object=api_object,
                                                                           endpoint=SchematicBranchEndpoint.TO,
                                                                           owner_device=obj_to),
                }

    def sync_injection_dock(self,
                            api_object: ALL_DEV_TYPES,
                            owner_device: ALL_DEV_TYPES | None,
                            side: SchematicAttachmentSide | str = SchematicAttachmentSide.BOTTOM) -> Dict[str, Any]:
        """
        Synchronize dock metadata for a bus-connected child while preserving future docking fields.
        """
        self.sync_injection_dock_record(api_object=api_object,
                                        owner_device=owner_device,
                                        side=side)
        return self.get_dock(api_object=api_object)

    def sync_injection_dock_record(self,
                                   api_object: ALL_DEV_TYPES,
                                   owner_device: ALL_DEV_TYPES | None,
                                   side: SchematicAttachmentSide | str = SchematicAttachmentSide.BOTTOM
                                   ) -> SchematicDockRecord:
        """
        Synchronize one typed dock record for runtime logic.

        :param api_object: Injection API object.
        :param owner_device: Owning bus or fluid node.
        :param side: Typed default side.
        :return: Typed dock record.
        """
        dock_record: SchematicDockRecord = self.get_dock_record(api_object=api_object)
        default_side: SchematicAttachmentSide | None = parse_schematic_attachment_side(side=side)

        if default_side is None:
            default_side = SchematicAttachmentSide.BOTTOM
        else:
            pass

        if owner_device is None:
            dock_record.owner_device_id = ""
            dock_record.owner_device_type = ""
        else:
            dock_record.owner_device_id = owner_device.idtag
            dock_record.owner_device_type = owner_device.device_type.value

        if dock_record.side is None:
            dock_record.side = default_side
        else:
            pass

        dock_record.offset = float(dock_record.offset)

        if dock_record.order is None and owner_device is not None:
            dock_record.order = api_object.get_bus_pos(owner_device)
        elif dock_record.order is None:
            dock_record.order = 0
        else:
            dock_record.order = int(dock_record.order)

        self.set_dock_record(api_object=api_object, dock_record=dock_record)
        return self.get_dock_record(api_object=api_object)
