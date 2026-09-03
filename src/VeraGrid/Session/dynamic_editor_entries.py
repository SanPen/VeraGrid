from __future__ import annotations

from itertools import chain
from typing import Any, Iterable

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, FmuTemplateDomain


def get_available_dynamic_modes(api_object: Any) -> tuple[DynamicSimulationMode, ...]:
    """
    Return the modes that can be opened for one API object.

    :param api_object: Device or template candidate.
    :return: Tuple of supported dynamic simulation modes.
    """
    modes: list[DynamicSimulationMode] = list()

    device_type = api_object.device_type

    if device_type == DeviceType.RmsModelTemplateDevice:
        return (DynamicSimulationMode.RMS,)
    if device_type == DeviceType.EmtModelTemplateDevice:
        return (DynamicSimulationMode.EMT,)

    try:
        if api_object.rms_model is not None:
            modes.append(DynamicSimulationMode.RMS)
        if api_object.emt_model is not None:
            modes.append(DynamicSimulationMode.EMT)
    except Exception:
        pass

    return tuple(modes)


def build_dynamic_editor_title(api_object: Any, mode: DynamicSimulationMode) -> str:
    """
    Build the tab or window title for one dynamic editor session.

    :param api_object: Device or template being edited.
    :param mode: Opened dynamic simulation mode.
    :return: User-facing editor title.
    """
    return f"{api_object.name} [{mode.name}]"


def build_dynamic_editor_entry(api_object: Any, circuit: Any) -> DynamicEditorEntry | None:
    """
    Build one dynamic editor entry or return ``None`` when unsupported.

    :param api_object: Device or template candidate.
    :param circuit: Circuit that owns the candidate object.
    :return: Resolved editor entry or ``None``.
    """
    available_modes: tuple[DynamicSimulationMode, ...] = get_available_dynamic_modes(api_object)
    if len(available_modes) == 0:
        return None
    else:
        pass

    if isinstance(api_object, EditableDevice):
        key_base: str = f"{api_object.device_type.value}:{api_object.idtag}"
        type_label: str = str(api_object.device_type.value)
        display_name: str = api_object.name
    else:
        key_base = f"dynamic-object:{id(api_object)}"
        api_object_class_name: str = api_object.__class__.__name__
        type_label = api_object_class_name
        display_name = api_object.name

    return DynamicEditorEntry(
        api_object=api_object,
        circuit=circuit,
        available_modes=available_modes,
        display_name=display_name,
        type_label=type_label,
        key_base=key_base,
    )


def iter_dynamic_editor_entries(circuit: Any) -> Iterable[DynamicEditorEntry]:
    """
    Yield every circuit object that can be opened in the dynamic editor.

    :param circuit: Circuit whose devices will be scanned.
    :return: Iterable of unique editor entries.
    """
    seen_keys: set[str] = set()
    branch_objects: list[Any] = list(circuit.get_branches(add_vsc=True, add_hvdc=True, add_switch=True))
    injection_objects: list[Any] = list(circuit.get_injection_devices())
    scanned_objects: Iterable[Any] = chain(injection_objects, branch_objects)
    api_object: Any
    entry: DynamicEditorEntry | None

    # The tree must list every branch-like device that can own one dynamic
    # editor model. The default branch collector excludes VSC and HVDC objects,
    # so request the full branch family explicitly before deduplicating entries.
    # The algorithm scans injections and branch-like devices in one pass, then
    # filters unsupported objects and duplicate mode keys before yielding them
    # to the workspace tree builder.
    for api_object in scanned_objects:
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None:
            pass
        else:
            if entry.key_base in seen_keys:
                pass
            else:
                seen_keys.add(entry.key_base)
                yield entry


def get_templates_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> list[Any]:
    """
    Return the template list exposed in the editor library for one entry.

    :param entry: Entry being edited.
    :param mode: Dynamic simulation mode being opened.
    :return: Template list for the editor library.
    """
    api_object = entry.api_object
    device_type = api_object.device_type

    if device_type == DeviceType.RmsModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.RMS))
    if device_type == DeviceType.EmtModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.EMT))

    if mode == DynamicSimulationMode.RMS:
        return list(entry.circuit.get_rms_templates_for_editor(api_object.device_type))
    else:
        return list(entry.circuit.get_emt_templates_for_editor(api_object.device_type))


def get_block_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> Any:
    """
    Return the block edited by one entry and mode.

    :param entry: Entry being edited.
    :param mode: Dynamic simulation mode being opened.
    :return: Backing block object for the editor page.
    """
    api_object = entry.api_object
    device_type = api_object.device_type

    if device_type in {DeviceType.RmsModelTemplateDevice, DeviceType.EmtModelTemplateDevice}:
        return api_object.block
    if mode == DynamicSimulationMode.RMS:
        return api_object.rms_model
    return api_object.emt_model


class DynamicEditorEntry:
    """
    One selectable and openable dynamic editor entry.
    """

    def __init__(
        self,
        api_object: Any,
        circuit: Any,
        available_modes: tuple[DynamicSimulationMode, ...],
        display_name: str,
        type_label: str,
        key_base: str,
    ) -> None:
        """
        Initialize one dynamic editor entry.

        :param api_object: Device or template being referenced.
        :param circuit: Circuit that owns the object.
        :param available_modes: Supported dynamic simulation modes.
        :param display_name: User-facing device name.
        :param type_label: User-facing device type label.
        :param key_base: Stable key shared by both modes of the same object.
        :return: None.
        """
        self.api_object = api_object
        self.circuit = circuit
        self.available_modes = available_modes
        self.display_name = display_name
        self.type_label = type_label
        self.key_base = key_base

    def session_key(self, mode: DynamicSimulationMode) -> str:
        """
        Build the unique session key for one entry-mode pair.

        :param mode: Dynamic simulation mode to encode.
        :return: Unique session key.
        """
        return f"{self.key_base}:{mode.name}"
