from __future__ import annotations

import pytest
from typing import cast
from VeraGrid.Gui.Main.SubClasses import io as io_module
from VeraGrid.Gui.Main.SubClasses.io import IoMain
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType


def _get_transformer_catalogue_stub() -> list[str]:
    return list(["t1", "t2"])


def _get_cables_catalogue_stub() -> list[str]:
    return list(["c1"])


def _get_wires_catalogue_stub() -> list[str]:
    return list(["w1", "w2", "w3"])


def _get_sequence_lines_catalogue_stub() -> list[str]:
    return list(["s1"])


def _get_empty_catalogue_stub() -> list[object]:
    return list()


def _custom_catalogue_dialog_stub(*args, **kwargs) -> tuple[str, str]:
    _unused = (args, kwargs)
    return "custom_catalogue.xlsx", "Catalogue file (*.xlsx)"


def _custom_catalogue_exists_stub(path: str) -> bool:
    return path == "custom_catalogue.xlsx"


class _CircuitStub:
    """
    Minimal circuit stub used to validate default-catalogue loading.
    """

    __slots__ = (
        "transformer_types",
        "underground_cable_types",
        "wire_types",
        "sequence_line_types",
        "rms_models",
        "emt_models",
        "lazy_rms_calls",
        "lazy_emt_calls",
    )

    def __init__(self) -> None:
        self.transformer_types: list[object] = list()
        self.underground_cable_types: list[object] = list()
        self.wire_types: list[object] = list()
        self.sequence_line_types: list[object] = list()
        self.rms_models: list[object] = list()
        self.emt_models: list[object] = list()
        self.lazy_rms_calls: int = 0
        self.lazy_emt_calls: int = 0

    def add_transformer_type(self, obj: object) -> None:
        self.transformer_types.append(obj)

    def add_underground_line(self, obj: object) -> None:
        self.underground_cable_types.append(obj)

    def add_wire(self, obj: object) -> None:
        self.wire_types.append(obj)

    def add_sequence_line(self, obj: object) -> None:
        self.sequence_line_types.append(obj)

    def add_rms_model_catalogue(self) -> None:
        self.rms_models.extend(list([object(), object()]))

    def add_emt_model_catalogue(self) -> None:
        self.emt_models.extend(list([object(), object(), object()]))

    def get_rms_models_number(self) -> int:
        return len(self.rms_models)

    def get_emt_models_number(self) -> int:
        return len(self.emt_models)

    def enable_default_rms_model_catalogue_lazy_loading(self) -> None:
        self.lazy_rms_calls += 1

    def enable_default_emt_model_catalogue_lazy_loading(self) -> None:
        self.lazy_emt_calls += 1


class _IoStub:
    """
    Minimal object exposing the attributes used by `IoMain.add_default_catalogue`.
    """

    __slots__ = ("circuit", "messages")

    def __init__(self) -> None:
        self.circuit: _CircuitStub = _CircuitStub()
        self.messages: list[str] = list()

    def show_info_toast(self, message: str) -> None:
        self.messages.append(message)

    def should_materialize_dynamic_catalogues_for_refresh(self) -> bool:
        return False

    # def materialize_dynamic_catalogues_for_refresh(self) -> None:
    #     _unused = self.circuit

    def materialize_dynamic_catalogues_for_refresh(self) -> None:
        """
        Explicitly load the dynamic model catalogues required by template-dependent GUI views.

        :return: None.
        """
        self.circuit.add_rms_model_catalogue()
        self.circuit.add_emt_model_catalogue()

    def refresh_catalogue_dependent_views(self) -> None:
        _unused = self.messages


class _RefreshingIoStub(_IoStub):
    """
    Minimal GUI-like stub that records catalogue-driven refresh calls.
    """

    __slots__ = ("setup_tree_calls", "view_objects_calls", "update_from_to_calls", "update_date_calls")

    def __init__(self) -> None:
        super().__init__()
        self.setup_tree_calls: int = 0
        self.view_objects_calls: int = 0
        self.update_from_to_calls: int = 0
        self.update_date_calls: int = 0

    def setup_objects_tree(self) -> None:
        self.setup_tree_calls += 1

    def view_objects_data(self) -> None:
        self.view_objects_calls += 1

    def update_from_to_list_views(self) -> None:
        self.update_from_to_calls += 1

    def update_date_dependent_combos(self) -> None:
        self.update_date_calls += 1

    def refresh_catalogue_dependent_views(self) -> None:
        self.setup_objects_tree()
        self.view_objects_data()
        self.update_from_to_list_views()
        self.update_date_dependent_combos()


class _GuiLikeIoStub(_RefreshingIoStub):
    """
    GUI-like stub exposing a minimal ``ui`` attribute for catalogue refresh.
    """

    __slots__ = ("ui",)

    def __init__(self) -> None:
        super().__init__()
        self.circuit = MultiCircuit()
        self.ui = object()

    def should_materialize_dynamic_catalogues_for_refresh(self) -> bool:
        return True

    def materialize_dynamic_catalogues_for_refresh(self) -> None:
        """
        Explicitly load the dynamic model catalogues required by template-dependent GUI views.

        :return: None.
        """
        self.circuit.add_rms_model_catalogue()
        self.circuit.add_emt_model_catalogue()


class _CatalogueLoggerStub:
    """
    Minimal logger stub returned by ``load_catalogue``.
    """

    __slots__ = ("_has_logs",)

    def __init__(self, has_logs: bool = False) -> None:
        self._has_logs: bool = has_logs

    def has_logs(self) -> bool:
        return self._has_logs


class _LoadCatalogueStub:
    """
    Callable ``load_catalogue`` stub with explicit payload storage.
    """

    __slots__ = ("loaded_catalogue", "logger")

    def __init__(self, loaded_catalogue: object, logger: _CatalogueLoggerStub) -> None:
        self.loaded_catalogue: object = loaded_catalogue
        self.logger: _CatalogueLoggerStub = logger

    def __call__(self, fname: str) -> tuple[object, _CatalogueLoggerStub]:
        _unused = fname
        return self.loaded_catalogue, self.logger


class _CustomCatalogueCircuitStub(_CircuitStub):
    """
    Circuit stub that records custom-catalogue additions.
    """

    __slots__ = ("catalogues_added",)

    def __init__(self) -> None:
        super().__init__()
        self.catalogues_added: list[object] = list()

    def add_catalogue(self, data: object) -> None:
        self.catalogues_added.append(data)
        self.rms_models.append(object())
        self.emt_models.append(object())


class _CustomCatalogueIoStub(_RefreshingIoStub):
    """
    GUI-like stub exposing the attributes used by ``load_custom_catalogue``.
    """

    __slots__ = ("ui", "project_directory", "logged_messages")

    def __init__(self) -> None:
        super().__init__()
        self.circuit = _CustomCatalogueCircuitStub()
        self.ui = object()
        self.project_directory = ""
        self.logged_messages: list[tuple[str, object]] = list()

    def show_logs(self, name: str, logger: object) -> None:
        self.logged_messages.append((name, logger))


def test_load_custom_catalogue_refreshes_template_dependent_gui_views(override_attrs) -> None:
    """
    Ensure the custom-catalogue action rebuilds the visible property views immediately.

        :return: None.
    """
    stub = _CustomCatalogueIoStub()
    loaded_catalogue = object()
    logger = _CatalogueLoggerStub(has_logs=False)
    load_catalogue_stub = _LoadCatalogueStub(loaded_catalogue=loaded_catalogue, logger=logger)

    override_attrs.setattr(io_module.QtWidgets.QFileDialog,
                        "getOpenFileName",
                        _custom_catalogue_dialog_stub)
    override_attrs.setattr(io_module.os.path, "exists", _custom_catalogue_exists_stub)
    override_attrs.setattr(io_module, "load_catalogue", load_catalogue_stub)

    IoMain.load_custom_catalogue(stub)

    assert stub.circuit.catalogues_added == list([loaded_catalogue])
    assert stub.setup_tree_calls == 1
    assert stub.view_objects_calls == 1
    assert stub.update_from_to_calls == 1
    assert stub.update_date_calls == 1
    assert stub.messages == list(["Catalogue loaded!"])
    assert stub.logged_messages == list()
    assert stub.circuit.get_rms_models_number() > 0
    assert stub.circuit.get_emt_models_number() > 0
