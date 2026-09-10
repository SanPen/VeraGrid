# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6 import QtCore

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.Events.dynamic_plot_entry import DynamicPlotEntry
from VeraGridEngine.Devices.Events.emt_event import EmtEvent
from VeraGridEngine.Devices.Events.emt_events_group import EmtEventsGroup
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DynamicEventTransitionType, DynamicSimulationMode


class DynamicEventGroupDraft:
    """Editable transaction record for one RMS or EMT events group."""

    __slots__ = (
        "original_group",
        "mode",
        "name",
        "active",
        "is_new",
        "is_removed",
    )

    def __init__(self,
                 original_group: RmsEventsGroup | EmtEventsGroup | None,
                 mode: DynamicSimulationMode,
                 name: str,
                 active: bool,
                 is_new: bool) -> None:
        """Create an editable group transaction record.

        :param original_group: Persisted group represented by the draft, if any.
        :param mode: RMS or EMT family of the group.
        :param name: Editable visible group name.
        :param active: Whether the group is selected for simulation.
        :param is_new: Whether the group only exists in the transaction.
        :return: None.
        """
        self.original_group: RmsEventsGroup | EmtEventsGroup | None = original_group
        self.mode: DynamicSimulationMode = mode
        self.name: str = str(name)
        self.active: bool = bool(active)
        self.is_new: bool = bool(is_new)
        self.is_removed: bool = False

    def get_committed_group(self) -> RmsEventsGroup | EmtEventsGroup | None:
        """Return the persisted group after the transaction creates or reuses it.

        :return: Persisted RMS or EMT events group, if available.
        """
        return self.original_group


class DynamicEventDraft:
    """Editable transaction record for one RMS or EMT event."""

    __slots__ = (
        "original_event",
        "mode",
        "device",
        "parameter",
        "time",
        "end_time",
        "value",
        "group",
        "force_step_alignment",
        "transition_type",
        "is_new",
        "is_removed",
    )

    def __init__(self,
                 original_event: RmsEvent | EmtEvent | None,
                 mode: DynamicSimulationMode,
                 device: EditableDevice | None,
                 parameter: Var | None,
                 time: float,
                 end_time: float | None,
                 value: float,
                 group: DynamicEventGroupDraft | None,
                 force_step_alignment: bool,
                 transition_type: DynamicEventTransitionType,
                 is_new: bool) -> None:
        """Create an editable event transaction record.

        :param original_event: Persisted event represented by the draft, if any.
        :param mode: RMS or EMT family of the event.
        :param device: Static device targeted by the event.
        :param parameter: Runtime parameter changed by the event.
        :param time: Event start time in seconds.
        :param end_time: Ramp end time, or ``None`` for step events.
        :param value: Runtime value applied by the event.
        :param group: Transaction group containing the event.
        :param force_step_alignment: Whether the solver must align a step exactly.
        :param transition_type: Step or ramp transition profile.
        :param is_new: Whether the event only exists in the transaction.
        :return: None.
        """
        self.original_event: RmsEvent | EmtEvent | None = original_event
        self.mode: DynamicSimulationMode = mode
        self.device: EditableDevice | None = device
        self.parameter: Var | None = parameter
        self.time: float = float(time)
        self.end_time: float | None = end_time
        self.value: float = float(value)
        self.group: DynamicEventGroupDraft | None = group
        self.force_step_alignment: bool = bool(force_step_alignment)
        self.transition_type: DynamicEventTransitionType = transition_type
        self.is_new: bool = bool(is_new)
        self.is_removed: bool = False


class DynamicEventsDraftSession(QtCore.QObject):
    """Shared transaction state used by every open dynamic-events page."""

    changed = QtCore.Signal()
    group_changed = QtCore.Signal(object)
    dirty_state_changed = QtCore.Signal(bool)

    __slots__ = (
        "circuit",
        "group_drafts",
        "event_drafts",
        "_dirty",
    )

    def __init__(self,
                 circuit: MultiCircuit,
                 parent: QtCore.QObject | None = None) -> None:
        """Capture the complete dynamic-events state without mutating the circuit.

        :param circuit: Circuit whose event assets are being edited.
        :param parent: Optional Qt owner.
        :return: None.
        """
        QtCore.QObject.__init__(self, parent)
        self.circuit: MultiCircuit = circuit
        self.group_drafts: list[DynamicEventGroupDraft] = list()
        self.event_drafts: list[DynamicEventDraft] = list()
        self._dirty: bool = False
        self._load_groups()
        self._load_events()

    @property
    def has_unapplied_changes(self) -> bool:
        """Return whether the shared event transaction differs from the circuit.

        :return: ``True`` when one or more event edits have not been saved.
        """
        return self._dirty

    def mark_changed(self, rebuild: bool) -> None:
        """Mark the transaction dirty and optionally rebuild every event tree.

        :param rebuild: Whether the shared structural projections must rebuild.
        :return: None.
        """
        if not self._dirty:
            self._dirty = True
            self.dirty_state_changed.emit(True)
        else:
            pass
        if rebuild:
            self.changed.emit()
        else:
            pass

    def reload_from_circuit(self) -> None:
        """Discard the draft and rebuild it from the persistent circuit state.

        :return: None.
        """
        self.group_drafts.clear()
        self.event_drafts.clear()
        self._load_groups()
        self._load_events()
        self._dirty = False
        self.changed.emit()
        self.dirty_state_changed.emit(False)

    def _load_groups(self) -> None:
        """Create transaction records for every persisted RMS and EMT group.

        :return: None.
        """
        rms_group: RmsEventsGroup
        for rms_group in self.circuit.rms_events_groups:
            self.group_drafts.append(
                DynamicEventGroupDraft(
                    original_group=rms_group,
                    mode=DynamicSimulationMode.RMS,
                    name=rms_group.name,
                    active=rms_group.active,
                    is_new=False,
                )
            )

        emt_group: EmtEventsGroup
        for emt_group in self.circuit.emt_events_groups:
            self.group_drafts.append(
                DynamicEventGroupDraft(
                    original_group=emt_group,
                    mode=DynamicSimulationMode.EMT,
                    name=emt_group.name,
                    active=emt_group.active,
                    is_new=False,
                )
            )

    def _load_events(self) -> None:
        """Create transaction records for every persisted RMS and EMT event.

        :return: None.
        """
        rms_event: RmsEvent
        for rms_event in self.circuit.rms_events:
            self.event_drafts.append(
                self._build_existing_event_draft(
                    event=rms_event,
                    mode=DynamicSimulationMode.RMS,
                )
            )

        emt_event: EmtEvent
        for emt_event in self.circuit.emt_events:
            self.event_drafts.append(
                self._build_existing_event_draft(
                    event=emt_event,
                    mode=DynamicSimulationMode.EMT,
                )
            )

    def _build_existing_event_draft(self,
                                    event: RmsEvent | EmtEvent,
                                    mode: DynamicSimulationMode) -> DynamicEventDraft:
        """Build one draft while normalizing step end-time storage.

        :param event: Persisted RMS or EMT event.
        :param mode: Simulation family containing the event.
        :return: Editable event draft.
        """
        group_draft: DynamicEventGroupDraft | None = self.find_group_draft(event.group, mode)
        if event.transition_type == DynamicEventTransitionType.Ramp:
            semantic_end_time: float | None = event.end_time
        else:
            semantic_end_time = None

        if isinstance(event.parameter, Var):
            parameter: Var | None = event.parameter
        else:
            parameter = None
        if isinstance(event.device, EditableDevice):
            device: EditableDevice | None = event.device
        else:
            device = None

        return DynamicEventDraft(
            original_event=event,
            mode=mode,
            device=device,
            parameter=parameter,
            time=float(event.time),
            end_time=semantic_end_time,
            value=float(event.value),
            group=group_draft,
            force_step_alignment=bool(event.force_step_alignment),
            transition_type=event.transition_type,
            is_new=False,
        )

    def find_group_draft(self,
                         group: RmsEventsGroup | EmtEventsGroup | None,
                         mode: DynamicSimulationMode) -> DynamicEventGroupDraft | None:
        """Find the transaction record that owns one persisted group object.

        :param group: Persisted group to resolve.
        :param mode: Expected simulation family.
        :return: Matching transaction group, or ``None``.
        """
        draft: DynamicEventGroupDraft
        for draft in self.group_drafts:
            if draft.mode == mode and draft.original_group is group:
                return draft
            else:
                pass
        return None

    def get_groups(self, mode: DynamicSimulationMode) -> list[DynamicEventGroupDraft]:
        """Return non-removed groups for one simulation family.

        :param mode: RMS or EMT family to select.
        :return: Ordered group draft list.
        """
        groups: list[DynamicEventGroupDraft] = list()
        draft: DynamicEventGroupDraft
        for draft in self.group_drafts:
            if draft.mode == mode and not draft.is_removed:
                groups.append(draft)
            else:
                pass
        return groups

    def get_events_for_device(self,
                              device: EditableDevice,
                              mode: DynamicSimulationMode) -> list[DynamicEventDraft]:
        """Return every non-removed event that targets one device and mode.

        :param device: Static device whose events are requested.
        :param mode: RMS or EMT family to select.
        :return: Ordered event draft list.
        """
        events: list[DynamicEventDraft] = list()
        draft: DynamicEventDraft
        for draft in self.event_drafts:
            if draft.mode == mode and draft.device is device and not draft.is_removed:
                events.append(draft)
            else:
                pass
        return events

    def get_group_events(self,
                         group: DynamicEventGroupDraft,
                         device: EditableDevice | None = None) -> list[DynamicEventDraft]:
        """Return non-removed events contained by one group.

        :param group: Group whose events are requested.
        :param device: Optional device filter.
        :return: Ordered event draft list.
        """
        events: list[DynamicEventDraft] = list()
        draft: DynamicEventDraft
        for draft in self.event_drafts:
            device_matches: bool = device is None or draft.device is device
            if draft.group is group and device_matches and not draft.is_removed:
                events.append(draft)
            else:
                pass
        return events

    def add_group(self,
                  mode: DynamicSimulationMode,
                  name: str) -> DynamicEventGroupDraft | None:
        """Add a new transaction group when its name is valid and unique.

        :param mode: RMS or EMT family of the new group.
        :param name: Requested visible group name.
        :return: Created group draft, or ``None`` when validation fails.
        """
        normalized_name: str = name.strip()
        if normalized_name == "" or self.group_name_exists(mode, normalized_name, None):
            return None
        else:
            pass
        draft: DynamicEventGroupDraft = DynamicEventGroupDraft(
            original_group=None,
            mode=mode,
            name=normalized_name,
            active=True,
            is_new=True,
        )
        self.group_drafts.append(draft)
        self.mark_changed(rebuild=True)
        return draft

    def group_name_exists(self,
                          mode: DynamicSimulationMode,
                          name: str,
                          excluded_group: DynamicEventGroupDraft | None) -> bool:
        """Return whether another visible group already uses a name.

        :param mode: RMS or EMT family to inspect.
        :param name: Normalized candidate name.
        :param excluded_group: Group currently being renamed, if any.
        :return: ``True`` when the candidate is already used.
        """
        candidate_lower: str = name.strip().lower()
        draft: DynamicEventGroupDraft
        for draft in self.group_drafts:
            if (
                draft is not excluded_group
                and not draft.is_removed
                and draft.mode == mode
                and draft.name.strip().lower() == candidate_lower
            ):
                return True
            else:
                pass
        return False

    def rename_group(self,
                     group: DynamicEventGroupDraft,
                     name: str) -> bool:
        """Rename one group inside the transaction after validation.

        :param group: Group draft being renamed.
        :param name: Candidate visible name.
        :return: Whether the rename was accepted.
        """
        normalized_name: str = name.strip()
        if normalized_name == "" or self.group_name_exists(group.mode, normalized_name, group):
            return False
        else:
            group.name = normalized_name
        self.mark_changed(rebuild=False)
        self.group_changed.emit(group)
        return True

    def set_group_active(self,
                         group: DynamicEventGroupDraft,
                         active: bool) -> None:
        """Change the transaction simulation-selection state of one group.

        :param group: Group draft being updated.
        :param active: New simulation-selection state.
        :return: None.
        """
        group.active = bool(active)
        self.mark_changed(rebuild=False)
        self.group_changed.emit(group)

    def add_event(self,
                  device: EditableDevice,
                  mode: DynamicSimulationMode,
                  group: DynamicEventGroupDraft | None,
                  parameters: list[Var],
                  mode_parameter_uids: set[int]) -> DynamicEventDraft | None:
        """Add a new event draft to the selected device and group.

        :param device: Static device targeted by the event.
        :param mode: RMS or EMT family of the page.
        :param group: Initially selected events group, or ``None`` for a new table row.
        :param parameters: Runtime parameters currently available in the model.
        :param mode_parameter_uids: Parameters representing discrete modes.
        :return: Created event draft, or ``None`` when the model is empty.
        """
        invalid_group: bool = group is not None and (group.mode != mode or group.is_removed)
        if len(parameters) == 0 or invalid_group:
            return None
        else:
            parameter: Var = parameters[0]
        draft: DynamicEventDraft = DynamicEventDraft(
            original_event=None,
            mode=mode,
            device=device,
            parameter=parameter,
            time=0.0,
            end_time=None,
            value=0.0,
            group=group,
            force_step_alignment=parameter.uid in mode_parameter_uids,
            transition_type=DynamicEventTransitionType.Step,
            is_new=True,
        )
        self.event_drafts.append(draft)
        self.mark_changed(rebuild=True)
        return draft

    def set_event_group(self,
                        event: DynamicEventDraft,
                        group: DynamicEventGroupDraft) -> bool:
        """Assign one compatible event group to an event draft.

        :param event: Event whose group is being selected in the table.
        :param group: Existing group selected by the user.
        :return: Whether the assignment was accepted.
        """
        event_belongs_to_session: bool = event in self.event_drafts
        group_belongs_to_session: bool = group in self.group_drafts
        valid_assignment: bool = (
            event_belongs_to_session
            and group_belongs_to_session
            and not event.is_removed
            and not group.is_removed
            and event.mode == group.mode
        )
        if valid_assignment:
            event.group = group
            return True
        else:
            return False

    def remove_event(self, event: DynamicEventDraft) -> None:
        """Mark one event as removed from the transaction.

        :param event: Event draft selected by the user.
        :return: None.
        """
        event.is_removed = True
        self.mark_changed(rebuild=True)

    def remove_group(self, group: DynamicEventGroupDraft) -> None:
        """Mark one group and every contained event as removed.

        :param group: Global RMS or EMT events group to remove.
        :return: None.
        """
        group.is_removed = True
        event: DynamicEventDraft
        for event in self.event_drafts:
            if event.group is group:
                event.is_removed = True
            else:
                pass
        self.mark_changed(rebuild=True)

    def reconcile_device_parameters(self,
                                    device: EditableDevice,
                                    mode: DynamicSimulationMode,
                                    parameters: list[Var]) -> int:
        """Rebind valid event parameters and remove events absent from a saved model.

        Logical variable UIDs survive a normal model save even though the save
        replaces the concrete ``Var`` instances. Events whose UIDs disappear
        are removed from the transaction because their target no longer exists.

        :param device: Device whose events are being regenerated.
        :param mode: RMS or EMT model family that was loaded.
        :param parameters: Current event parameters from the saved model.
        :return: Number of events removed during reconciliation.
        """
        removed_count: int = 0
        reference_was_rebound: bool = False
        event: DynamicEventDraft
        for event in self.event_drafts:
            if event.device is device and event.mode == mode and not event.is_removed:
                replacement: Var | None = None
                parameter: Var
                for parameter in parameters:
                    if event.parameter is not None and parameter.uid == event.parameter.uid:
                        replacement = parameter
                    else:
                        pass
                if replacement is not None:
                    if event.parameter is not replacement:
                        reference_was_rebound = True
                    else:
                        pass
                    event.parameter = replacement
                else:
                    event.is_removed = True
                    removed_count += 1
            else:
                pass

        if removed_count > 0 or reference_was_rebound:
            # Reconciliation only changes events owned by this device page.
            # The caller rebuilds that projection explicitly, while the shared
            # dirty signal updates every tab title without rebuilding unrelated
            # device trees.
            self.mark_changed(rebuild=False)
        else:
            pass
        return removed_count

    def count_group_devices(self, group: DynamicEventGroupDraft) -> int:
        """Count distinct devices affected by removing one group.

        :param group: Group whose device impact is requested.
        :return: Number of distinct target-device identities.
        """
        devices: list[EditableDevice] = list()
        event: DynamicEventDraft
        for event in self.get_group_events(group):
            if event.device is not None:
                found: bool = False
                device: EditableDevice
                for device in devices:
                    if device is event.device:
                        found = True
                    else:
                        pass
                if not found:
                    devices.append(event.device)
                else:
                    pass
            else:
                pass
        return len(devices)

    def validate(self) -> str | None:
        """Validate names, fields, intervals and event overlaps prospectively.

        :return: User-facing error message, or ``None`` when valid.
        """
        time_tolerance: float = 1.0e-9
        group: DynamicEventGroupDraft
        for group in self.group_drafts:
            if not group.is_removed:
                if group.name.strip() == "":
                    return self.tr("An events group has an empty name.")
                elif self.group_name_exists(group.mode, group.name, group):
                    return self.tr("The events group name '{name}' is duplicated.").format(name=group.name)
                else:
                    pass
            else:
                pass

        active_events: list[DynamicEventDraft] = list()
        event: DynamicEventDraft
        for event in self.event_drafts:
            if not event.is_removed:
                if event.device is None:
                    return self.tr("An event has no target device.")
                elif event.parameter is None:
                    return self.tr("An event in device '{device}' has no valid parameter.").format(
                        device=event.device.name,
                    )
                elif event.group is None or event.group.is_removed:
                    return self.tr("An event in device '{device}' has no valid events group.").format(
                        device=event.device.name,
                    )
                elif event.group.mode != event.mode:
                    return self.tr("An event and its events group use different simulation modes.")
                elif event.transition_type == DynamicEventTransitionType.Ramp:
                    if event.end_time is None or event.end_time + time_tolerance < event.time:
                        return self.tr(
                            "The ramp event for parameter '{parameter}' has an invalid end time."
                        ).format(parameter=event.parameter.name)
                    else:
                        pass
                else:
                    pass
                active_events.append(event)
            else:
                pass

        # Compare only events that target the same group, device and runtime
        # parameter; independent devices may legitimately change at one time.
        first_index: int = 0
        while first_index < len(active_events):
            first_event: DynamicEventDraft = active_events[first_index]
            second_index: int = first_index + 1
            while second_index < len(active_events):
                second_event: DynamicEventDraft = active_events[second_index]
                same_target: bool = (
                    first_event.mode == second_event.mode
                    and first_event.group is second_event.group
                    and first_event.device is second_event.device
                    and first_event.parameter is second_event.parameter
                )
                if same_target and self._events_overlap(first_event, second_event, time_tolerance):
                    return self.tr(
                        "Events for parameter '{parameter}' overlap in group '{group}' and device '{device}'."
                    ).format(
                        parameter=first_event.parameter.name,
                        group=first_event.group.name,
                        device=first_event.device.name,
                    )
                else:
                    pass
                second_index += 1
            first_index += 1
        return None

    def _events_overlap(self,
                        first_event: DynamicEventDraft,
                        second_event: DynamicEventDraft,
                        tolerance: float) -> bool:
        """Return whether two step/ramp intervals intersect.

        :param first_event: First event interval.
        :param second_event: Second event interval.
        :param tolerance: Numerical time tolerance in seconds.
        :return: Whether the event intervals overlap.
        """
        if first_event.transition_type == DynamicEventTransitionType.Ramp and first_event.end_time is not None:
            first_end: float = first_event.end_time
        else:
            first_end = first_event.time
        if second_event.transition_type == DynamicEventTransitionType.Ramp and second_event.end_time is not None:
            second_end: float = second_event.end_time
        else:
            second_end = second_event.time
        return max(first_event.time, second_event.time) <= min(first_end, second_end) + tolerance

    def commit(self) -> None:
        """Apply the transaction and establish a reusable saved baseline.

        Removed drafts are pruned and surviving drafts are marked as persisted
        after the circuit has been updated. This makes repeated saves safe while
        the editor remains open.

        :return: None.
        """
        group: DynamicEventGroupDraft
        for group in self.group_drafts:
            if not group.is_removed:
                self._commit_group(group)
            else:
                pass

        # Existing and new surviving events are committed before deletions so
        # every reference targets a canonical persisted group.
        event: DynamicEventDraft
        for event in self.event_drafts:
            if not event.is_removed:
                if event.original_event is None:
                    self._commit_new_event(event)
                else:
                    self._commit_existing_event(event)
            else:
                pass

        # Delete standalone events first. Group deletion remains the canonical
        # cascade for every event belonging to a removed global group.
        for event in self.event_drafts:
            if event.is_removed and event.original_event is not None:
                if event.group is None or not event.group.is_removed:
                    if event.mode == DynamicSimulationMode.RMS and isinstance(event.original_event, RmsEvent):
                        self.circuit.delete_rms_event(event.original_event)
                    elif event.mode == DynamicSimulationMode.EMT and isinstance(event.original_event, EmtEvent):
                        self.circuit.delete_emt_event(event.original_event)
                    else:
                        pass
                else:
                    pass
            else:
                pass

        for group in self.group_drafts:
            if group.is_removed and group.original_group is not None:
                if group.mode == DynamicSimulationMode.RMS and isinstance(group.original_group, RmsEventsGroup):
                    self.circuit.delete_rms_events_group(group.original_group)
                elif group.mode == DynamicSimulationMode.EMT and isinstance(group.original_group, EmtEventsGroup):
                    self.circuit.delete_emt_events_group(group.original_group)
                else:
                    pass
            else:
                pass

        # Saving is a checkpoint rather than the end of the editor session.
        # Discard deleted records and normalize surviving records so a later
        # save updates the same canonical objects instead of replaying changes.
        surviving_events: list[DynamicEventDraft] = list()
        for event in self.event_drafts:
            if not event.is_removed:
                event.is_new = False
                surviving_events.append(event)
            else:
                pass
        self.event_drafts = surviving_events

        surviving_groups: list[DynamicEventGroupDraft] = list()
        for group in self.group_drafts:
            if not group.is_removed:
                group.is_new = False
                surviving_groups.append(group)
            else:
                pass
        self.group_drafts = surviving_groups
        self._dirty = False
        self.changed.emit()
        self.dirty_state_changed.emit(False)

    def _commit_group(self, group: DynamicEventGroupDraft) -> None:
        """Create or update one non-removed events group.

        :param group: Group transaction record to persist.
        :return: None.
        """
        old_name: str = ""
        if group.original_group is None:
            if group.mode == DynamicSimulationMode.RMS:
                created_group: RmsEventsGroup | EmtEventsGroup = dev.RmsEventsGroup(
                    idtag=None,
                    name=group.name,
                    active=group.active,
                )
                self.circuit.add_rms_events_group(created_group)
            else:
                created_group = dev.EmtEventsGroup(
                    idtag=None,
                    name=group.name,
                    active=group.active,
                )
                self.circuit.add_emt_events_group(created_group)
            group.original_group = created_group
        else:
            old_name = group.original_group.name
            group.original_group.name = group.name
            group.original_group.active = group.active

        # Dynamic plot entries bind canonically by idtag but also persist a
        # visible name hint that must follow legitimate group renames.
        if group.original_group is not None and old_name != group.name:
            plot_entry: DynamicPlotEntry
            for plot_entry in self.circuit.dynamic_plot_entries:
                if plot_entry.event_group_idtag == str(group.original_group.idtag):
                    plot_entry.event_group_name = group.name
                else:
                    pass
        else:
            pass

    def _commit_existing_event(self, event: DynamicEventDraft) -> None:
        """Update one surviving persisted event without changing its identity.

        :param event: Event transaction record to apply.
        :return: None.
        """
        persisted_group: RmsEventsGroup | EmtEventsGroup | None = (
            event.group.get_committed_group() if event.group is not None else None
        )
        if event.original_event is None or event.parameter is None or persisted_group is None:
            return
        else:
            pass
        event.original_event.parameter = event.parameter
        event.original_event.time = float(event.time)
        event.original_event.value = float(event.value)
        event.original_event.group = persisted_group
        event.original_event.force_step_alignment = bool(event.force_step_alignment)
        event.original_event.transition_type = event.transition_type
        if event.transition_type == DynamicEventTransitionType.Ramp and event.end_time is not None:
            event.original_event.end_time = float(event.end_time)
        else:
            event.original_event.end_time = float(event.time) + 1.0e-20

    def _commit_new_event(self, event: DynamicEventDraft) -> None:
        """Create one surviving transaction event in the canonical circuit.

        :param event: New event transaction record to persist.
        :return: None.
        """
        persisted_group: RmsEventsGroup | EmtEventsGroup | None = (
            event.group.get_committed_group() if event.group is not None else None
        )
        if event.device is None or event.parameter is None or persisted_group is None:
            return
        else:
            pass
        if event.transition_type == DynamicEventTransitionType.Ramp:
            persisted_end_time: float | None = event.end_time
        else:
            persisted_end_time = None

        if event.mode == DynamicSimulationMode.RMS and isinstance(persisted_group, RmsEventsGroup):
            rms_event: RmsEvent = dev.RmsEvent(
                device=event.device,
                parameter=event.parameter,
                time=float(event.time),
                end_time=persisted_end_time,
                value=float(event.value),
                group=persisted_group,
                force_step_alignment=bool(event.force_step_alignment),
                transition_type=event.transition_type,
            )
            self.circuit.add_rms_event(rms_event)
            event.original_event = rms_event
        elif event.mode == DynamicSimulationMode.EMT and isinstance(persisted_group, EmtEventsGroup):
            emt_event: EmtEvent = dev.EmtEvent(
                device=event.device,
                parameter=event.parameter,
                time=float(event.time),
                end_time=persisted_end_time,
                value=float(event.value),
                group=persisted_group,
                force_step_alignment=bool(event.force_step_alignment),
                transition_type=event.transition_type,
            )
            self.circuit.add_emt_event(emt_event)
            event.original_event = emt_event
        else:
            pass
