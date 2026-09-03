# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable, List, Sequence

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode


def _emit_dynamic_model_import_progress(progress_callback: Callable[[int, str], None] | None,
                                        progress_value: int,
                                        progress_text: str) -> None:
    """
    Emit one dynamic-model import progress update when a callback is available.

    :param progress_callback: Optional UI progress callback.
    :param progress_value: Integer percentage in ``[0, 100]``.
    :param progress_text: User-facing progress label.
    :return: None.
    """
    if progress_callback is None:
        pass
    else:
        progress_callback(progress_value, progress_text)


class DynamicModelImportSource(Enum):
    """
    Source format used by one imported dynamic-model bundle.
    """

    __slots__ = ()

    ModelicaXml = "Modelica XML"
    PowerFactoryDgs = "PowerFactory DGS"


class DynamicModelImportSourceProvenance:
    """
    Typed DGS provenance for one separate dynamic catalogue entry.

    :param root_dgs_id: Owning root ElmComp identifier.
    :param root_name: Owning root ElmComp display name.
    :param root_typ_id: Owning root ElmComp type identifier.
    :param slot_dgs_id: Optional direct slot identifier.
    :param slot_name: Optional direct slot display name.
    :param slot_index: Optional ordinal pblk/pelm index.
    :param slot_element: Optional raw BlkSlot default or prototype element reference.
    :param slot_filter: Optional raw BlkSlot allowed-class filter.
    :param source_element_dgs_id: Optional pElm source identifier.
    :param source_element_name: Optional pElm source display name.
    :param source_element_class: Optional pElm PowerFactory class name.
    """

    __slots__ = (
        "_root_dgs_id",
        "_root_name",
        "_root_typ_id",
        "_slot_dgs_id",
        "_slot_name",
        "_slot_index",
        "_slot_element",
        "_slot_filter",
        "_source_element_dgs_id",
        "_source_element_name",
        "_source_element_class",
    )

    def __init__(
            self,
            root_dgs_id: str,
            root_name: str,
            root_typ_id: str,
            slot_dgs_id: str | None = None,
            slot_name: str | None = None,
            slot_index: int | None = None,
            slot_element: str | None = None,
            slot_filter: str | None = None,
            source_element_dgs_id: str | None = None,
            source_element_name: str | None = None,
            source_element_class: str | None = None,
    ) -> None:
        """
        Store immutable root, slot and source-element fields.

        :param root_dgs_id: Owning root ElmComp identifier.
        :param root_name: Owning root ElmComp display name.
        :param root_typ_id: Owning root ElmComp type identifier.
        :param slot_dgs_id: Optional direct slot identifier.
        :param slot_name: Optional direct slot display name.
        :param slot_index: Optional ordinal pblk/pelm index.
        :param slot_element: Optional raw compatible-element reference.
        :param slot_filter: Optional raw model filter text.
        :param source_element_dgs_id: Optional pElm source identifier.
        :param source_element_name: Optional pElm source display name.
        :param source_element_class: Optional pElm class name.
        :return: None.
        """
        self._root_dgs_id: str = root_dgs_id
        self._root_name: str = root_name
        self._root_typ_id: str = root_typ_id
        self._slot_dgs_id: str | None = slot_dgs_id
        self._slot_name: str | None = slot_name
        self._slot_index: int | None = slot_index
        self._slot_element: str | None = slot_element
        self._slot_filter: str | None = slot_filter
        self._source_element_dgs_id: str | None = source_element_dgs_id
        self._source_element_name: str | None = source_element_name
        self._source_element_class: str | None = source_element_class

    def get_root_dgs_id(self) -> str:
        """Return the owning root ElmComp DGS identifier."""
        return self._root_dgs_id

    def get_root_name(self) -> str:
        """Return the owning root ElmComp display name."""
        return self._root_name

    def get_root_typ_id(self) -> str:
        """Return the owning root ElmComp type identifier."""
        return self._root_typ_id

    def get_slot_dgs_id(self) -> str | None:
        """Return the optional direct slot identifier."""
        return self._slot_dgs_id

    def get_slot_name(self) -> str | None:
        """Return the optional direct slot display name."""
        return self._slot_name

    def get_slot_index(self) -> int | None:
        """Return the optional ordinal pblk/pelm index."""
        return self._slot_index

    def get_slot_element(self) -> str | None:
        """Return the optional raw BlkSlot compatible-element reference."""
        return self._slot_element

    def get_slot_filter(self) -> str | None:
        """Return the optional raw BlkSlot model filter text."""
        return self._slot_filter

    def get_source_element_dgs_id(self) -> str | None:
        """Return the optional pElm element identifier."""
        return self._source_element_dgs_id

    def get_source_element_name(self) -> str | None:
        """Return the optional pElm element display name."""
        return self._source_element_name

    def get_source_element_class(self) -> str | None:
        """Return the optional pElm PowerFactory class name."""
        return self._source_element_class

class DynamicModelImportEntryAvailability(Enum):
    """
    Source availability classification for one catalogue entry.

    Metadata-only nodes preserve PowerFactory hierarchy and association data;
    they are intentionally not reusable templates and are not parser failures.
    """

    __slots__ = ()

    Importable = "Importable"
    MetadataOnly = "Metadata only"
    Failed = "Failed"


class DynamicModelImportEntryStatus(Enum):
    """
    Final processing state for one selected dynamic catalogue entry.
    """

    __slots__ = ()

    Added = "Added"
    Deduplicated = "Deduplicated"
    Renamed = "Renamed"
    Failed = "Failed"
    Skipped = "Skipped"


class DynamicModelImportEntryResult:
    """
    Structured result for one dynamic-model catalogue entry.

    :param unique_key: Stable source catalogue key.
    :param requested_name: Source display name.
    :param final_name: Final circuit template name, when available.
    :param domain: Selected target domain.
    :param status: Explicit processing outcome.
    :param source_provenance: DGS root/slot/element provenance, when available.
    :param message: Human-readable diagnostic.
    """

    __slots__ = (
        "_unique_key",
        "_requested_name",
        "_final_name",
        "_domain",
        "_status",
        "_source_provenance",
        "_persisted_path",
        "_message",
    )

    def __init__(
            self,
            unique_key: str,
            requested_name: str,
            final_name: str | None,
            domain: DynamicSimulationMode,
            status: DynamicModelImportEntryStatus,
            source_provenance: DynamicModelImportSourceProvenance | None,
            message: str,
    ) -> None:
        """
        Store one fixed-size import result.

        :param unique_key: Stable source catalogue key.
        :param requested_name: Source display name.
        :param final_name: Final circuit template name, when available.
        :param domain: Selected target domain.
        :param status: Explicit processing outcome.
        :param source_provenance: DGS root/slot/element provenance, when available.
        :param message: Human-readable diagnostic.
        :return: None.
        """
        self._unique_key: str = unique_key
        self._requested_name: str = requested_name
        self._final_name: str | None = final_name
        self._domain: DynamicSimulationMode = domain
        self._status: DynamicModelImportEntryStatus = status
        self._source_provenance: DynamicModelImportSourceProvenance | None = (
            source_provenance
        )
        self._persisted_path: Path | None = None
        self._message: str = message

    def get_unique_key(self) -> str:
        """Return the stable source key."""
        return self._unique_key

    def get_requested_name(self) -> str:
        """Return the requested source display name."""
        return self._requested_name

    def get_final_name(self) -> str | None:
        """Return the final circuit template name."""
        return self._final_name

    def get_domain(self) -> DynamicSimulationMode:
        """Return the selected target domain."""
        return self._domain

    def get_status(self) -> DynamicModelImportEntryStatus:
        """Return the explicit processing status."""
        return self._status

    def get_source_provenance(self) -> DynamicModelImportSourceProvenance | None:
        """Return the DGS root/slot/element provenance, when available."""
        return self._source_provenance

    def set_persisted_path(self, persisted_path: Path) -> None:
        """
        Store a canonical persisted artefact path for compatibility reporting.

        :param persisted_path: Written non-executable artefact path.
        :return: None.
        """
        self._persisted_path = persisted_path

    def get_persisted_path(self) -> Path | None:
        """Return the persisted artefact path, when one was written."""
        return self._persisted_path

    def set_message(self, message: str) -> None:
        """
        Replace the handled outcome diagnostic.

        :param message: New human-readable diagnostic.
        :return: None.
        """
        self._message = message

    def get_message(self) -> str:
        """Return the handled outcome diagnostic."""
        return self._message


def _count_dynamic_model_import_result_status(
        entry_results: Sequence[DynamicModelImportEntryResult],
        status: DynamicModelImportEntryStatus,
) -> int:
    """
    Count entry results with one explicit processing status.

    :param entry_results: Ordered structured entry results.
    :param status: Status to count.
    :return: Matching result count.
    """
    count: int = 0
    entry_result: DynamicModelImportEntryResult
    for entry_result in entry_results:
        if entry_result.get_status() == status:
            count += 1
        else:
            pass
    return count


def _count_persisted_dynamic_model_import_results(
        entry_results: Sequence[DynamicModelImportEntryResult],
) -> int:
    """
    Count entry results carrying a successfully persisted artefact.

    :param entry_results: Ordered structured entry results.
    :return: Results carrying a persisted artefact path.
    """
    count: int = 0
    entry_result: DynamicModelImportEntryResult
    for entry_result in entry_results:
        if entry_result.get_persisted_path() is None:
            pass
        else:
            count += 1
    return count


def _count_dgs_source_associations(
        entry_results: Sequence[DynamicModelImportEntryResult],
) -> int:
    """
    Count results carrying one exact ElmComp pblk/pelm source relation.

    :param entry_results: Ordered structured entry results.
    :return: Results with a root slot and referenced source element.
    """
    count: int = 0
    entry_result: DynamicModelImportEntryResult
    source_provenance: DynamicModelImportSourceProvenance | None

    for entry_result in entry_results:
        source_provenance = entry_result.get_source_provenance()
        if (source_provenance is not None and
                source_provenance.get_slot_index() is not None and
                source_provenance.get_source_element_dgs_id() is not None):
            count += 1
        else:
            pass

    return count


class DynamicModelImportReport:
    """
    Aggregate structured result for one massive dynamic-model import.

    :param discovered_count: Total source catalogue entries.
    :param importable_count: Entries with a materialized source template.
    """

    __slots__ = (
        "_discovered_count",
        "_importable_count",
        "_entry_results",
        "_activation_report",
    )

    def __init__(self, discovered_count: int, importable_count: int) -> None:
        """
        Initialize one empty report with source catalogue counts.

        :param discovered_count: Total source catalogue entries.
        :param importable_count: Entries with a materialized source template.
        :return: None.
        """
        self._discovered_count: int = discovered_count
        self._importable_count: int = importable_count
        self._entry_results: List[DynamicModelImportEntryResult] = list()
        self._activation_report: DgsDynamicModelActivationReport | None = None

    def add_entry_result(self, entry_result: DynamicModelImportEntryResult) -> None:
        """
        Append one entry result in deterministic catalogue order.

        :param entry_result: Completed entry outcome.
        :return: None.
        """
        self._entry_results.append(entry_result)

    def get_discovered_count(self) -> int:
        """Return the number of source catalogue entries."""
        return self._discovered_count

    def get_importable_count(self) -> int:
        """Return the number of materialized source entries."""
        return self._importable_count

    def get_entry_results(self) -> List[DynamicModelImportEntryResult]:
        """Return a defensive copy of the ordered entry results."""
        return list(self._entry_results)

    def get_added_count(self) -> int:
        """Return added templates, including collision-safe renamed additions."""
        return _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Added,
        ) + _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Renamed,
        )

    def get_deduplicated_count(self) -> int:
        """Return structurally equivalent entries reused from the circuit."""
        return _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Deduplicated,
        )

    def get_renamed_count(self) -> int:
        """Return collisions installed with source-qualified names."""
        return _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Renamed,
        )

    def get_failed_count(self) -> int:
        """Return entries that could not be materialized or installed."""
        return _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Failed,
        )

    def get_skipped_count(self) -> int:
        """Return metadata-only or duplicate entries intentionally not installed."""
        return _count_dynamic_model_import_result_status(
            self._entry_results,
            DynamicModelImportEntryStatus.Skipped,
        )

    def get_persisted_count(self) -> int:
        """Return the number of successfully persisted artefacts."""
        return _count_persisted_dynamic_model_import_results(self._entry_results)

    def get_source_association_count(self) -> int:
        """Return exact DGS root/slot/element relations retained by the report."""
        return _count_dgs_source_associations(self._entry_results)

    def set_activation_report(
            self,
            activation_report: "DgsDynamicModelActivationReport",
    ) -> None:
        """
        Store the explicit DGS host activation outcome.

        :param activation_report: Root-to-device activation report.
        :return: None.
        """
        self._activation_report = activation_report

    def get_activation_report(self) -> "DgsDynamicModelActivationReport | None":
        """
        Return the explicit DGS host activation outcome.

        :return: Activation report or ``None`` for non-DGS imports.
        """
        return self._activation_report

    def get_activated_device_model_count(self) -> int:
        """
        Return the number of device models assigned by exact DGS identity.

        :return: Newly activated device model count.
        """
        if self._activation_report is None:
            result: int = 0
        else:
            result = self._activation_report.get_physical_activated_count()
        return result


class DgsDynamicModelActivationReport:
    """
    Summarize exact DGS composite-root activation on physical devices.

    The counters separate safe assignments from already active, ambiguous,
    unresolved, conflicting and failed roots so partial imports remain
    inspectable without turning one unsupported controller into a file failure.
    """

    __slots__ = (
        "_activated_count",
        "_physical_activated_count",
        "_logical_activated_count",
        "_already_active_count",
        "_ambiguous_count",
        "_unresolved_count",
        "_conflict_count",
        "_failed_count",
    )

    def __init__(self) -> None:
        """
        Initialize an empty fixed-shape activation report.

        :return: None.
        """
        self._activated_count: int = 0
        self._physical_activated_count: int = 0
        self._logical_activated_count: int = 0
        self._already_active_count: int = 0
        self._ambiguous_count: int = 0
        self._unresolved_count: int = 0
        self._conflict_count: int = 0
        self._failed_count: int = 0

    def record_physical_activated(self) -> None:
        """Record one newly assigned physical dynamic host.

        :return: None.
        """
        self._activated_count += 1
        self._physical_activated_count += 1

    def record_logical_activated(self) -> None:
        """Record one newly assigned non-physical composite controller.

        :return: None.
        """
        self._activated_count += 1
        self._logical_activated_count += 1

    def record_already_active(self) -> None:
        """Record one idempotently retained host assignment."""
        self._already_active_count += 1

    def record_ambiguous(self) -> None:
        """Record one root with several possible physical hosts."""
        self._ambiguous_count += 1

    def record_unresolved(self) -> None:
        """Record one exact source host that is absent from the circuit."""
        self._unresolved_count += 1

    def record_conflict(self) -> None:
        """Record one host that already carries another dynamic template."""
        self._conflict_count += 1

    def record_failed(self) -> None:
        """Record one handled template-assignment failure."""
        self._failed_count += 1

    def get_activated_count(self) -> int:
        """Return newly assigned host count."""
        return self._activated_count

    def get_physical_activated_count(self) -> int:
        """Return newly assigned physical-device host count.

        :return: Physical activation count.
        """
        return self._physical_activated_count

    def get_logical_activated_count(self) -> int:
        """Return newly assigned non-physical controller count.

        :return: Logical activation count.
        """
        return self._logical_activated_count

    def get_already_active_count(self) -> int:
        """Return idempotently retained host count."""
        return self._already_active_count

    def get_ambiguous_count(self) -> int:
        """Return ambiguous root count."""
        return self._ambiguous_count

    def get_unresolved_count(self) -> int:
        """Return unresolved exact host count."""
        return self._unresolved_count

    def get_conflict_count(self) -> int:
        """Return conflicting pre-existing assignment count."""
        return self._conflict_count

    def get_failed_count(self) -> int:
        """Return handled assignment failure count."""
        return self._failed_count


class DynamicModelImportSelectionRequest:
    """
    Explicit import request for one selected entry.

    :param entry_key: Stable key of the selected import entry.
    :param target_domain: Selected target reusable-template domain.
    :param device_tpe: Selected supported VeraGrid device type.
    """

    __slots__ = (
        "_entry_key",
        "_target_domain",
        "_device_tpe",
    )

    def __init__(
            self,
            entry_key: str,
            target_domain: DynamicSimulationMode,
            device_tpe: DeviceType,
    ) -> None:
        """
        Build one explicit import request.

        :param entry_key: Stable entry key.
        :param target_domain: Selected reusable-template domain.
        :param device_tpe: Selected supported device type.
        :return: None.
        """
        self._entry_key: str = str(entry_key)
        self._target_domain: DynamicSimulationMode = target_domain
        self._device_tpe: DeviceType = device_tpe

    def get_entry_key(self) -> str:
        """
        Return the selected entry key.

        :return: Stable entry key.
        """
        return self._entry_key

    def get_target_domain(self) -> DynamicSimulationMode:
        """
        Return the selected reusable-template domain.

        :return: Target domain.
        """
        return self._target_domain

    def get_device_tpe(self) -> DeviceType:
        """
        Return the selected supported device type.

        :return: Supported device type.
        """
        return self._device_tpe


class DynamicModelLoadedUserTemplate:
    """
    One persisted user template materialized from the ``user_templates`` folder.

    :param payload_path: Source declarative JSON payload path.
    :param domain: Selected reusable-template domain restored from metadata.
    :param device_tpe: Selected supported device type restored from metadata.
    :param template_obj: Materialized RMS or EMT reusable template.
    """

    __slots__ = (
        "_payload_path",
        "_domain",
        "_device_tpe",
        "_template_obj",
    )

    def __init__(
            self,
            payload_path: Path,
            domain: DynamicSimulationMode,
            device_tpe: DeviceType,
            template_obj: RmsModelTemplate | EmtModelTemplate,
    ) -> None:
        """
        Build one materialized persisted user template descriptor.

        :param payload_path: Source declarative JSON payload path.
        :param domain: Restored reusable-template domain.
        :param device_tpe: Restored supported device type.
        :param template_obj: Materialized RMS or EMT template.
        :return: None.
        """
        self._payload_path: Path = payload_path
        self._domain: DynamicSimulationMode = domain
        self._device_tpe: DeviceType = device_tpe
        self._template_obj: RmsModelTemplate | EmtModelTemplate = template_obj

    def get_payload_path(self) -> Path:
        """
        Return the persisted declarative payload path.

        :return: Persisted JSON payload path.
        """
        return self._payload_path

    def get_domain(self) -> DynamicSimulationMode:
        """
        Return the restored reusable-template domain.

        :return: Restored domain.
        """
        return self._domain

    def get_device_tpe(self) -> DeviceType:
        """
        Return the restored supported device type.

        :return: Restored device type.
        """
        return self._device_tpe

    def get_template_obj(self) -> RmsModelTemplate | EmtModelTemplate:
        """
        Return the materialized reusable template object.

        :return: RMS or EMT template object.
        """
        return self._template_obj

class DynamicModelPersistenceKind(Enum):
    """
    Persistence strategy used for a trusted imported dynamic-model source.
    """

    __slots__ = ()

    ModelicaXml = "Modelica XML"


class DynamicModelPersistenceSpec:
    """
    Typed persistence descriptor used to export one imported entry to Python.

    :param kind: Export strategy.
    :param source_path: Source file path.
    :param template_name: Output template name.
    :param root_name: Optional root ElmComp display name.
    :param root_typ_id: Optional root ElmComp typ_id.
    :param slot_name: Optional root slot name.
    :param block_name: Optional selected block name.
    :param block_id: Optional selected block identifier.
    :param module_stem: Output module stem.
    """

    __slots__ = (
        "_kind",
        "_source_path",
        "_template_name",
        "_root_name",
        "_root_typ_id",
        "_slot_name",
        "_block_name",
        "_block_id",
        "_module_stem",
    )

    def __init__(
            self,
            kind: DynamicModelPersistenceKind,
            source_path: str,
            template_name: str,
            module_stem: str,
            root_name: str | None = None,
            root_typ_id: str | None = None,
            slot_name: str | None = None,
            block_name: str | None = None,
            block_id: str | None = None,
    ) -> None:
        """
        Build one typed persistence descriptor.

        :param kind: Export strategy.
        :param source_path: Source file path.
        :param template_name: Output template name.
        :param module_stem: Output module stem.
        :param root_name: Optional root ElmComp display name.
        :param root_typ_id: Optional root ElmComp typ_id.
        :param slot_name: Optional root slot name.
        :param block_name: Optional selected block name.
        :param block_id: Optional selected block identifier.
        :return: None.
        """
        self._kind: DynamicModelPersistenceKind = kind
        self._source_path: str = str(source_path)
        self._template_name: str = str(template_name)
        self._module_stem: str = str(module_stem)
        self._root_name: str | None = None if root_name is None else str(root_name)
        self._root_typ_id: str | None = None if root_typ_id is None else str(root_typ_id)
        self._slot_name: str | None = None if slot_name is None else str(slot_name)
        self._block_name: str | None = None if block_name is None else str(block_name)
        self._block_id: str | None = None if block_id is None else str(block_id)

    def get_kind(self) -> DynamicModelPersistenceKind:
        """
        Return the export strategy.

        :return: Export strategy.
        """
        return self._kind

    def get_source_path(self) -> str:
        """
        Return the source file path.

        :return: Source path.
        """
        return self._source_path

    def get_template_name(self) -> str:
        """
        Return the output template name.

        :return: Template name.
        """
        return self._template_name

    def get_root_name(self) -> str | None:
        """
        Return the optional root ElmComp name.

        :return: Root name or ``None``.
        """
        return self._root_name

    def get_root_typ_id(self) -> str | None:
        """
        Return the optional root ElmComp typ_id.

        :return: Root typ_id or ``None``.
        """
        return self._root_typ_id

    def get_slot_name(self) -> str | None:
        """
        Return the optional slot name.

        :return: Slot name or ``None``.
        """
        return self._slot_name

    def get_block_name(self) -> str | None:
        """
        Return the optional selected block name.

        :return: Block name or ``None``.
        """
        return self._block_name

    def get_block_id(self) -> str | None:
        """
        Return the optional selected block identifier.

        :return: Block identifier or ``None``.
        """
        return self._block_id

    def get_module_stem(self) -> str:
        """
        Return the output module stem.

        :return: Module stem.
        """
        return self._module_stem


class DynamicModelImportEntry:
    """
    One importable dynamic-model source entry.

    :param unique_key: Stable key used by the GUI selection dialog.
    :param display_name: Human-readable entry label.
    :param source_tpe: Source format used to build this entry.
    :param source_block: Domain-neutral imported block, or ``None`` when the
        source entry could not be materialized.
    :param notes_text: Human-readable warning or support notes.
    """

    __slots__ = (
        "_unique_key",
        "_display_name",
        "_source_tpe",
        "_source_block",
        "_notes_text",
        "_parent_key",
        "_persistence_spec",
        "_source_provenance",
        "_installed_template",
        "_availability",
    )

    def __init__(
            self,
            unique_key: str,
            display_name: str,
            source_tpe: DynamicModelImportSource,
            source_block: Block | None,
            notes_text: str,
            parent_key: str | None = None,
            persistence_spec: DynamicModelPersistenceSpec | None = None,
            source_provenance: DynamicModelImportSourceProvenance | None = None,
            availability: DynamicModelImportEntryAvailability | None = None,
    ) -> None:
        """
        Build one importable dynamic-model entry.

        :param unique_key: Stable selection key.
        :param display_name: Human-readable entry label.
        :param source_tpe: Source format.
        :param source_block: Domain-neutral imported block or ``None``.
        :param notes_text: Human-readable notes.
        :param parent_key: Optional parent catalogue entry key.
        :param persistence_spec: Optional canonical Python persistence specification.
        :param source_provenance: Optional typed DGS origin and host metadata.
        :param availability: Explicit source availability, or automatic
            source-block classification.
        :return: None.
        """
        self._unique_key: str = str(unique_key)
        self._display_name: str = str(display_name)
        self._source_tpe: DynamicModelImportSource = source_tpe
        self._source_block: Block | None = source_block
        self._notes_text: str = str(notes_text)
        self._parent_key: str | None = None if parent_key is None else str(parent_key)
        self._persistence_spec: DynamicModelPersistenceSpec | None = persistence_spec
        self._source_provenance: DynamicModelImportSourceProvenance | None = (
            source_provenance
        )
        self._installed_template: RmsModelTemplate | EmtModelTemplate | None = None
        if availability is None:
            if source_block is None:
                self._availability: DynamicModelImportEntryAvailability = DynamicModelImportEntryAvailability.Failed
            else:
                self._availability = DynamicModelImportEntryAvailability.Importable
        else:
            self._availability = availability

    def get_unique_key(self) -> str:
        """
        Return the stable selection key.

        :return: Stable selection key.
        """
        return self._unique_key

    def get_display_name(self) -> str:
        """
        Return the human-readable display name.

        :return: Entry display name.
        """
        return self._display_name

    def get_source_tpe(self) -> DynamicModelImportSource:
        """
        Return the source format.

        :return: Source format enum.
        """
        return self._source_tpe

    def get_source_block(self) -> Block | None:
        """
        Return the imported domain-neutral symbolic block.

        :return: Imported symbolic block or ``None``.
        """
        return self._source_block

    def get_notes_text(self) -> str:
        """
        Return the import notes string.

        :return: Import notes.
        """
        return self._notes_text

    def get_parent_key(self) -> str | None:
        """
        Return the parent selection key when this entry belongs to a hierarchy.

        :return: Parent entry key or ``None``.
        """
        return self._parent_key

    def get_persistence_spec(self) -> DynamicModelPersistenceSpec | None:
        """
        Return the Python-export persistence descriptor.

        :return: Persistence descriptor or ``None``.
        """
        return self._persistence_spec

    def get_source_provenance(self) -> DynamicModelImportSourceProvenance | None:
        """
        Return typed DGS provenance and host-resolution metadata.

        :return: Source provenance or ``None`` for formats without DGS origin.
        """
        return self._source_provenance

    def get_availability(self) -> DynamicModelImportEntryAvailability:
        """
        Return the explicit source availability classification.

        :return: Importable, metadata-only or failed classification.
        """
        return self._availability

    def set_installed_template(
            self,
            template_obj: RmsModelTemplate | EmtModelTemplate | None,
    ) -> None:
        """
        Store the circuit template selected by add or deduplication processing.

        :param template_obj: Installed or equivalent circuit template, or ``None``.
        :return: None.
        """
        self._installed_template = template_obj

    def get_installed_template(self) -> RmsModelTemplate | EmtModelTemplate | None:
        """
        Return the circuit template produced by the latest import operation.

        :return: Added/equivalent circuit template or ``None``.
        """
        return self._installed_template

    def is_importable(self) -> bool:
        """
        Return whether the entry can be added to the circuit.

        :return: ``True`` when the entry has a materialized source block.
        """
        if (self._availability == DynamicModelImportEntryAvailability.Importable and
                self._source_block is not None):
            return True
        else:
            return False


class DynamicModelImportBundle:
    """
    Group of imported dynamic-model entries built from one source file.

    :param source_tpe: Source format used to build the bundle.
    :param source_path: Source file path.
    :param entries: Importable or non-importable entries discovered in the file.
    """

    __slots__ = (
        "_source_tpe",
        "_source_path",
        "_entries",
    )

    def __init__(
            self,
            source_tpe: DynamicModelImportSource,
            source_path: str,
            entries: List[DynamicModelImportEntry],
    ) -> None:
        """
        Build one imported dynamic-model bundle.

        :param source_tpe: Source format.
        :param source_path: Source file path.
        :param entries: Discovered import entries.
        :return: None.
        """
        self._source_tpe: DynamicModelImportSource = source_tpe
        self._source_path: str = str(source_path)
        self._entries: List[DynamicModelImportEntry] = entries

    def get_source_tpe(self) -> DynamicModelImportSource:
        """
        Return the bundle source format.

        :return: Source format enum.
        """
        return self._source_tpe

    def get_source_path(self) -> str:
        """
        Return the source file path.

        :return: Source file path.
        """
        return self._source_path

    def get_entries(self) -> List[DynamicModelImportEntry]:
        """
        Return the bundle entries.

        :return: Bundle entries.
        """
        return self._entries

    def get_entry_by_key(self, entry_key: str) -> DynamicModelImportEntry | None:
        """
        Resolve one bundle entry by its stable source key.

        :param entry_key: Stable source catalogue key.
        :return: Matching entry or ``None``.
        """
        entry: DynamicModelImportEntry
        for entry in self._entries:
            if entry.get_unique_key() == entry_key:
                return entry
            else:
                pass
        return None
