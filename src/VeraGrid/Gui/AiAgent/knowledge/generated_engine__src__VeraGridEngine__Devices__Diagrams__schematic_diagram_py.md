# VeraGridEngine Module: src/VeraGridEngine/Devices/Diagrams/schematic_diagram.py

- Original source path: `src/VeraGridEngine/Devices/Diagrams/schematic_diagram.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 1
- Top-level function count: 4
- Representative imports: __future__, typing, VeraGridEngine.Devices.Diagrams.base_diagram, VeraGridEngine.Devices.Diagrams.graphic_location, VeraGridEngine.Devices.Diagrams.schematic_layout, VeraGridEngine.enumerations

## Function: get_attachment_owner_kind(owner_device)

Map node device types to persisted attachment slot prefixes.

## Function: get_default_attachment_side(owner_kind, endpoint)

Choose the compatibility default side for one endpoint.

## Function: get_side_from_slot_tuple(slot_tuple)

Convert one explicit slot tuple into a typed compatibility side.

## Function: build_explicit_attachment_slot(owner_kind, side, order)

Build one typed explicit attachment slot for runtime use.

## Class: SchematicDiagram

- Bases: BaseDiagram
- Summary: Diagram

### Methods

- `update_xy(self, api_object, x, y)`
  Summary: Update the element xy position
- `update_graphic_location(self, api_object, x, y, w, h, r, draw_labels)`
  Summary: Update basic schematic geometry while preserving any route and attachment metadata already persisted.
- `copy_layout_state(self, source_api_object, target_api_object, include_geometry)`
  Summary: Copy persisted schematic route and attachment state from one device to another.
- `_get_or_create_graphic_location(self, api_object)`
  Summary: Return an existing schematic location or create a placeholder entry for compatibility-layer updates.
- `get_layout_metadata(self, api_object)`
  Summary: Return a defensive copy of the persisted schematic layout metadata for this device.
- `get_branch_route_points(self, api_object)`
  Summary: Return route points using the compatibility layer that understands both legacy and structured storage.
- `should_preserve_branch_route_shape(self, api_object)`
  Summary: Determine whether a branch should keep its persisted interior route elbows.
- `set_branch_route_points(self, api_object, points, kind, locked, route_style)`
  Summary: Persist route points through the compatibility layer while keeping legacy polyline storage in sync.
- `sync_branch_route_points(self, api_object, points)`
  Summary: Update route points while preserving existing route kind and lock state.
- `get_branch_route_record(self, api_object)`
  Summary: Return the typed route record for one branch.
- `get_branch_auto_route_style(self, api_object)`
  Summary: Return the persisted automatic route style for one branch.
- `set_branch_auto_route_style(self, api_object, route_style)`
  Summary: Persist the automatic route style for one branch.
- `upgrade_legacy_branch_layout(self, api_object, start, end)`
  Summary: Fill missing structured branch layout metadata for legacy diagrams.
- `get_attachment_record(self, api_object, endpoint)`
  Summary: Return one typed attachment record for runtime logic.
- `set_attachment_record(self, api_object, endpoint, attachment_record)`
  Summary: Persist one typed attachment record through the compatibility layer.
- `get_attachment(self, api_object, endpoint)`
  Summary: Return persisted attachment metadata for a branch endpoint or dockable child.
- `set_attachment(self, api_object, endpoint, attachment)`
  Summary: Persist attachment metadata through the compatibility layer.
- `get_dock_record(self, api_object)`
  Summary: Return one typed dock record for runtime logic.
- `set_dock_record(self, api_object, dock_record)`
  Summary: Persist one typed dock record through the compatibility layer.
- `get_dock(self, api_object)`
  Summary: Return persisted dock metadata for a bus-connected child device.
- `set_dock(self, api_object, dock)`
  Summary: Persist dock metadata through the compatibility layer.
- `sync_attachment(self, api_object, endpoint, owner_device)`
  Summary: Update endpoint ownership metadata while preserving any future slot-routing fields already stored.
- `sync_attachment_record(self, api_object, endpoint, owner_device)`
  Summary: Update one typed endpoint attachment record for runtime logic.
- `sync_branch_attachments(self, api_object)`
  Summary: Synchronize the standard 'from' and 'to' attachment ownership records for branch-like devices.
- `sync_branch_attachment_records(self, api_object)`
  Summary: Synchronize the standard typed attachment records for branch-like devices.
- `sync_injection_dock(self, api_object, owner_device, side)`
  Summary: Synchronize dock metadata for a bus-connected child while preserving future docking fields.
- `sync_injection_dock_record(self, api_object, owner_device, side)`
  Summary: Synchronize one typed dock record for runtime logic.
