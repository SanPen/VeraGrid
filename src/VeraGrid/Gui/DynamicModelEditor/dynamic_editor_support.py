from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode, FmuTemplateDomain


@dataclass(frozen=True)
class DynamicEditorEntry:
    """
    One selectable/openable Dynamic Editor entry.
    """

    api_object: Any
    circuit: Any
    available_modes: tuple[DynamicSimulationMode, ...]
    display_name: str
    type_label: str
    key_base: str

    def session_key(self, mode: DynamicSimulationMode) -> str:
        return f"{self.key_base}:{mode.name}"


def get_available_dynamic_modes(api_object: Any) -> tuple[DynamicSimulationMode, ...]:
    """
    Return the modes that can be opened for one API object.
    """

    device_type = getattr(api_object, "device_type", None)
    modes: list[DynamicSimulationMode] = list()

    if device_type == DeviceType.RmsModelTemplateDevice:
        return (DynamicSimulationMode.RMS,)
    if device_type == DeviceType.EmtModelTemplateDevice:
        return (DynamicSimulationMode.EMT,)

    if hasattr(api_object, "rms_model"):
        modes.append(DynamicSimulationMode.RMS)
    if hasattr(api_object, "emt_model"):
        modes.append(DynamicSimulationMode.EMT)

    return tuple(modes)


def build_dynamic_editor_title(api_object: Any, mode: DynamicSimulationMode) -> str:
    """
    Build the tab/window title for one dynamic editor session.
    """

    return f"{getattr(api_object, 'name', 'Dynamic object')} [{mode.name}]"


def build_dynamic_editor_entry(api_object: Any, circuit: Any) -> DynamicEditorEntry | None:
    """
    Build one dynamic editor picker entry or return None when the object has no dynamic editor.
    """

    available_modes = get_available_dynamic_modes(api_object)
    if len(available_modes) == 0:
        return None

    if isinstance(api_object, EditableDevice):
        key_base = f"{api_object.device_type.value}:{api_object.idtag}"
        type_label = str(api_object.device_type.value)
        display_name = api_object.name
    else:
        key_base = f"dynamic-object:{id(api_object)}"
        type_label = type(api_object).__name__
        display_name = getattr(api_object, "name", type_label)

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
    Yield every circuit object that can be opened in the unified Dynamic Editor.
    """

    seen_keys: set[str] = set()
    api_object: Any
    for api_object in circuit.items():
        entry = build_dynamic_editor_entry(api_object, circuit)
        if entry is None or entry.key_base in seen_keys:
            continue
        seen_keys.add(entry.key_base)
        yield entry


def get_templates_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode) -> list[Any]:
    """
    Return the template list that should be exposed in the editor library for one entry.
    """

    api_object = entry.api_object
    device_type = getattr(api_object, "device_type", None)

    if device_type == DeviceType.RmsModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.RMS))
    if device_type == DeviceType.EmtModelTemplateDevice:
        return list(entry.circuit.get_dynamic_templates_by_domain(FmuTemplateDomain.EMT))

    if mode == DynamicSimulationMode.RMS:
        return list(entry.circuit.get_rms_models_by_device_type(api_object.device_type))
    else:
        return list(entry.circuit.get_emt_models_by_device_type(api_object.device_type))


def get_block_for_entry(entry: DynamicEditorEntry, mode: DynamicSimulationMode):
    """
    Return the block edited by one entry and mode.
    """

    api_object = entry.api_object
    device_type = getattr(api_object, "device_type", None)

    if device_type in {DeviceType.RmsModelTemplateDevice, DeviceType.EmtModelTemplateDevice}:
        return api_object.block
    if mode == DynamicSimulationMode.RMS:
        return api_object.rms_model
    else:
        return api_object.emt_model
