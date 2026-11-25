# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Native construction, copying and parsing must retain RA conditions."""
import json
from pathlib import Path
from typing import Any, Dict, List
from zipfile import ZipFile

import pandas as pd
import pytest

import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multiverse import MultiVerse
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.file_save import FileSave
from VeraGridEngine.IO.veragrid.pack_unpack import parse_veragrid_data
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    ContingencyOperationTypes, LogSeverity, RemedialActionPropertyEnum)


def circuit_with_conditions() -> dev.MultiCircuit:
    """Build a self-contained circuit with forward group references.

    :return: Circuit containing branch and bus conditions and one action.
    """
    grid: dev.MultiCircuit = dev.MultiCircuit()
    a: dev.Bus = dev.Bus(name='A')
    b: dev.Bus = dev.Bus(name='B')
    grid.add_bus(a)
    grid.add_bus(b)
    line: dev.Line = dev.Line(bus_from=a, bus_to=b, name='Monitored line')
    grid.add_line(line)
    first: dev.RemedialActionGroup = dev.RemedialActionGroup(name='First')
    first.monitored_device = line
    first.property_type = RemedialActionPropertyEnum.Loading
    second: dev.RemedialActionGroup = dev.RemedialActionGroup(name='Second')
    second.monitored_device = a
    second.property_type = RemedialActionPropertyEnum.Vmin
    second.prev_ra = first
    # Forward references must not depend on storage order.
    grid.add_remedial_action_group(second)
    grid.add_remedial_action_group(first)
    action: dev.RemedialAction = dev.RemedialAction(
        device=line, group=first, prop=ContingencyOperationTypes.Active, value=0)
    grid.add_remedial_action(action)
    return grid


def assert_conditions(grid: dev.MultiCircuit) -> None:
    """Check that each condition references this circuit's canonical objects.

    :param grid: Copied or loaded circuit to inspect.
    :return: None.
    """
    groups: Dict[str, dev.RemedialActionGroup] = {
        group.name: group for group in grid.remedial_action_groups}
    assert len(groups) == 2
    assert groups['First'].monitored_device is grid.lines[0]
    assert groups['First'].property_type == RemedialActionPropertyEnum.Loading
    assert groups['Second'].monitored_device is grid.buses[0]
    assert groups['Second'].property_type == RemedialActionPropertyEnum.Vmin
    assert groups['Second'].prev_ra is groups['First']
    assert len(grid.remedial_actions) == 1
    assert grid.remedial_actions[0].device is grid.lines[0]
    assert grid.remedial_actions[0].group is groups['First']


def test_constructor_assigns_explicit_condition() -> None:
    """Preserve constructor arguments and validate the limit after the device.

    :return: None.
    """
    line: dev.Line = dev.Line()
    previous: dev.RemedialActionGroup = dev.RemedialActionGroup()
    contingency: dev.ContingencyGroup = dev.ContingencyGroup()
    group: dev.RemedialActionGroup = dev.RemedialActionGroup(
        monitored_device=line, property_type=RemedialActionPropertyEnum.Loading,
        remedial_action_dependency=previous, conn_group=contingency)
    assert group.monitored_device is line
    assert group.prev_ra is previous
    assert group.conn_group is contingency
    assert group.property_type == RemedialActionPropertyEnum.Loading


def test_constructor_rejects_incompatible_condition() -> None:
    """Keep the existing setter validation when arguments are supplied.

    :return: None.
    """
    with pytest.raises(ValueError, match='property_type is not applicable'):
        dev.RemedialActionGroup(
            monitored_device=dev.Line(),
            property_type=RemedialActionPropertyEnum.Vmin)
    with pytest.raises(ValueError, match='bus, line, or two-winding transformer'):
        dev.RemedialActionGroup(monitored_device=dev.Generator())

def test_snapshot_limit_waits_for_its_monitored_device() -> None:
    """Resolve a deferred limit when auto-updates are disabled without treating it as unconditional.

    :return: None.
    """
    group: dev.RemedialActionGroup = dev.RemedialActionGroup()
    line: dev.Line = dev.Line()
    group.disable_auto_updates()
    group.set_snapshot_value('property_type', RemedialActionPropertyEnum.Loading)
    assert group.property_type == RemedialActionPropertyEnum.Loading
    with pytest.raises(ValueError, match='monitored device is required'):
        group.is_condition_met(observed_value=1.1)
    group.set_snapshot_value('monitored_device', line)
    group.enable_auto_updates()
    assert group.monitored_device is line
    assert group.get_limit_value() == 1.0
    assert group.is_condition_met(observed_value=1.1)


def test_direct_limit_assignment_still_requires_a_device() -> None:
    """Keep deferred loading separate from the strict public setter.

    :return: None.
    """
    group: dev.RemedialActionGroup = dev.RemedialActionGroup()
    with pytest.raises(ValueError, match='property_type is not applicable'):
        group.property_type = RemedialActionPropertyEnum.Loading
    assert group.property_type is None


def test_pending_limit_rejects_incompatible_equipment() -> None:
    """Reject a mismatched target without accepting an unconditional group.

    :return: None.
    """
    group: dev.RemedialActionGroup = dev.RemedialActionGroup()
    bus: dev.Bus = dev.Bus()
    group.disable_auto_updates()
    group.set_snapshot_value('property_type', RemedialActionPropertyEnum.Vmin)
    with pytest.raises(ValueError, match='property_type is not applicable'):
        group.set_snapshot_value('monitored_device', dev.Line())
    assert group.monitored_device is None
    assert group.property_type == RemedialActionPropertyEnum.Vmin
    group.set_snapshot_value('monitored_device', bus)
    group.enable_auto_updates()
    assert group.monitored_device is bus
    assert group.property_type == RemedialActionPropertyEnum.Vmin


@pytest.mark.parametrize('cleared_field', ['property_type', 'monitored_device'])
def test_explicit_clear_discards_a_pending_limit(cleared_field: str) -> None:
    """Prevent a cancelled deferred limit from reappearing on a later target.

    :param cleared_field: Condition field explicitly cleared by the caller.
    :return: None.
    """
    group: dev.RemedialActionGroup = dev.RemedialActionGroup()
    group.disable_auto_updates()
    group.set_snapshot_value('property_type', RemedialActionPropertyEnum.Loading)
    if cleared_field == 'property_type':
        group.property_type = None
        group.enable_auto_updates()
    else:
        group.enable_auto_updates()
        group.monitored_device = None
    group.monitored_device = dev.Line()
    assert group.property_type is None


@pytest.mark.parametrize('operation', ['copy', 'checkout'])
def test_copy_and_server_checkout_preserve_conditions(operation: str) -> None:
    """Preserve conditions while isolating copied mutable assets.

    :param operation: Copy directly or through a multiverse root checkout.
    :return: None.
    """
    original: dev.MultiCircuit = circuit_with_conditions()
    result: dev.MultiCircuit
    if operation == 'copy':
        result = original.copy()
    else:
        multiverse: MultiVerse = MultiVerse(current_model=original)
        result = multiverse.checkout(multiverse.root_nodes[0])
    assert_conditions(result)
    assert result.lines[0] is not original.lines[0]
    result.remedial_action_groups[0].monitored_device = result.buses[1]
    assert_conditions(original)


@pytest.mark.parametrize('storage_format', ['native', 'dataframe'])
def test_parser_resolves_device_before_dependent_limit(
        tmp_path: Path, storage_format: str) -> None:
    """Load a valid limit only after its monitored equipment resolves.

    :param tmp_path: Isolated directory for the generated model.
    :param storage_format: Native JSON or legacy DataFrame parsing path.
    :return: None.
    """
    original: dev.MultiCircuit = circuit_with_conditions()
    path: Path = tmp_path / 'conditions.veragrid'
    FileSave(original, str(path)).save()
    logger: Logger = Logger()
    result: dev.MultiCircuit
    if storage_format == 'native':
        reader: FileOpen = FileOpen(str(path))
        result = reader.open()
        logger = reader.logger
    else:
        with ZipFile(path) as archive:
            records: Dict[str, Any] = {
                name.rsplit('/', 1)[-1][:-6]: json.loads(archive.read(name))
                for name in archive.namelist()
                if name.startswith('model_data/') and name.endswith('.model')}
        # Deliberately put the dependent property before its monitored pointer.
        groups: List[Dict[str, Any]] = records['remedial_action_group']
        columns: List[str] = ['property_type', 'monitored_device'] + [
            key for key in groups[0] if key not in ('property_type', 'monitored_device')]
        data: Dict[str, pd.DataFrame] = {
            key: pd.DataFrame(value).fillna('') for key, value in records.items()
            if isinstance(value, list) and value}
        data['remedial_action_group'] = pd.DataFrame(groups)[columns].fillna('')
        result = parse_veragrid_data(data=data, logger=logger)
    assert_conditions(result)
    assert not any(entry.severity == LogSeverity.Error for entry in logger.entries)


@pytest.mark.parametrize('storage_format', ['native', 'dataframe'])
def test_invalid_serialized_limit_is_reported(storage_format: str) -> None:
    """Keep invalid loaded limits visible and report incompatible references.

    :param storage_format: Native JSON or legacy DataFrame parsing path.
    :return: None.
    """
    records: Dict[str, List[Dict[str, Any]]] = {
        'bus': [{'idtag': 'bus-a'}, {'idtag': 'bus-b'}],
        'line': [{'idtag': 'line-ab', 'bus_from': 'bus-a', 'bus_to': 'bus-b'}],
        'remedial_action_group': [{
            'idtag': 'condition', 'monitored_device': 'line-ab',
            'property_type': RemedialActionPropertyEnum.Vmin.value}],
    }
    data: Dict[str, Any]
    if storage_format == 'native':
        data = {'model_data': records}
    else:
        data = {key: pd.DataFrame(value) for key, value in records.items()}
    logger: Logger = Logger()
    grid: dev.MultiCircuit = parse_veragrid_data(data=data, logger=logger)
    group: dev.RemedialActionGroup = grid.remedial_action_groups[0]
    assert any(entry.severity == LogSeverity.Error for entry in logger.entries)
    assert group.monitored_device is None
    assert group.property_type == RemedialActionPropertyEnum.Vmin
    with pytest.raises(ValueError, match='monitored device is required'):
        group.is_condition_met(observed_value=0.9)
