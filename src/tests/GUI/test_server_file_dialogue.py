from __future__ import annotations

import copy
from typing import Any, Dict, List

from PySide6 import QtCore

from VeraGrid.Gui.FileDialogues.ServerFileDialog.server_file_dialogue_window import ServerFileDialogue


def build_server_files_payload() -> List[Dict[str, Any]]:
    """
    Build one deterministic server file tree payload for dialog tests.

    :return: File payload list.
    """
    model_rows_a: List[Dict[str, Any]] = list()
    model_rows_a.append(
        {
            "idtag": "file-a-base",
            "name": "File A Base",
            "parent_model_idtag": None,
            "is_base_model": True,
        }
    )
    model_rows_a.append(
        {
            "idtag": "file-a-child",
            "name": "File A Child",
            "parent_model_idtag": "file-a-base",
            "is_base_model": False,
        }
    )

    model_rows_b: List[Dict[str, Any]] = list()
    model_rows_b.append(
        {
            "idtag": "file-b-base",
            "name": "File B Base",
            "parent_model_idtag": None,
            "is_base_model": True,
        }
    )

    files_payload: List[Dict[str, Any]] = list()
    files_payload.append(
        {
            "idtag": "file-a",
            "name": "File A",
            "user": "alice",
            "created_at": "2026-07-26T20:00:00Z",
            "models": model_rows_a,
        }
    )
    files_payload.append(
        {
            "idtag": "file-b",
            "name": "File B",
            "user": "bob",
            "created_at": "2026-07-26T21:00:00Z",
            "models": model_rows_b,
        }
    )
    return files_payload


class FakeServerDriver:
    """
    Minimal server driver used to feed deterministic file trees to the dialog.
    """

    __slots__ = ("_files_payload", "list_calls")

    def __init__(self, files_payload: List[Dict[str, Any]]) -> None:
        """
        Build the fake driver with mutable file payload data.

        :param files_payload: Initial server file tree.
        :return: None.
        """
        self._files_payload: List[Dict[str, Any]] = copy.deepcopy(files_payload)
        self.list_calls: int = 0

    def list_database_files_tree(self) -> List[Dict[str, Any]]:
        """
        Return a detached copy of the current server file tree.

        :return: File payload list.
        """
        self.list_calls += 1
        return copy.deepcopy(self._files_payload)

    def delete_file(self, file_idtag: str) -> None:
        """
        Remove one file from the fake server payload.

        :param file_idtag: File identifier.
        :return: None.
        """
        next_payload: List[Dict[str, Any]] = list()
        file_payload: Dict[str, Any]
        for file_payload in self._files_payload:
            # The deletion must remove the full file subtree.
            if str(file_payload["idtag"]) != file_idtag:
                next_payload.append(file_payload)
            else:
                pass
        self._files_payload = next_payload

    def delete_model(self, file_idtag: str, model_idtag: str) -> None:
        """
        Remove one model row from one fake server file payload.

        :param file_idtag: Parent file identifier.
        :param model_idtag: Model identifier.
        :return: None.
        """
        file_payload: Dict[str, Any]
        for file_payload in self._files_payload:
            if str(file_payload["idtag"]) == file_idtag:
                next_models: List[Dict[str, Any]] = list()
                model_payload: Dict[str, Any]
                for model_payload in file_payload["models"]:
                    # The dialog only needs to observe that the selected row vanished.
                    if str(model_payload["idtag"]) != model_idtag:
                        next_models.append(model_payload)
                    else:
                        pass
                file_payload["models"] = next_models
            else:
                pass


class FakeMainApp:
    """
    Minimal GUI app façade used by the server file dialog.
    """

    __slots__ = (
        "server_driver",
        "load_calls",
        "save_calls",
        "delete_file_calls",
        "delete_model_calls",
    )

    def __init__(self, files_payload: List[Dict[str, Any]]) -> None:
        """
        Build the fake GUI app with one fake server driver.

        :param files_payload: Initial server file tree.
        :return: None.
        """
        self.server_driver: FakeServerDriver = FakeServerDriver(files_payload=files_payload)
        self.load_calls: List[Dict[str, Any]] = list()
        self.save_calls: List[Dict[str, Any]] = list()
        self.delete_file_calls: List[str] = list()
        self.delete_model_calls: List[Dict[str, str]] = list()

    def load_remote_database_entry(self,
                                   file_idtag: str,
                                   file_name: str,
                                   model_idtag: str,
                                   base_only: bool) -> None:
        """
        Record one dialog load request.

        :param file_idtag: File identifier.
        :param file_name: File name.
        :param model_idtag: Optional model identifier.
        :param base_only: Whether only the base model is requested.
        :return: None.
        """
        self.load_calls.append(
            {
                "file_idtag": file_idtag,
                "file_name": file_name,
                "model_idtag": model_idtag,
                "base_only": base_only,
            }
        )

    def save_remote_database_entry(self,
                                   file_idtag: str,
                                   file_name: str,
                                   model_idtag: str) -> None:
        """
        Record one dialog save request.

        :param file_idtag: File identifier.
        :param file_name: File name.
        :param model_idtag: Optional target model identifier.
        :return: None.
        """
        self.save_calls.append(
            {
                "file_idtag": file_idtag,
                "file_name": file_name,
                "model_idtag": model_idtag,
            }
        )

    def delete_remote_database_file(self, file_idtag: str) -> None:
        """
        Record and apply one file deletion.

        :param file_idtag: File identifier.
        :return: None.
        """
        self.delete_file_calls.append(file_idtag)
        self.server_driver.delete_file(file_idtag=file_idtag)

    def delete_remote_database_model(self, file_idtag: str, model_idtag: str) -> None:
        """
        Record and apply one model deletion.

        :param file_idtag: Parent file identifier.
        :param model_idtag: Model identifier.
        :return: None.
        """
        self.delete_model_calls.append(
            {
                "file_idtag": file_idtag,
                "model_idtag": model_idtag,
            }
        )
        self.server_driver.delete_model(file_idtag=file_idtag, model_idtag=model_idtag)


class RecordingToastManager:
    """
    Minimal toast manager used to capture dialog notifications in tests.
    """

    __slots__ = ("messages",)

    def __init__(self) -> None:
        """
        Build the recording toast manager.

        :return: None.
        """
        self.messages: List[Dict[str, Any]] = list()

    def show_info_toast(self, message: str, duration: int = 2000) -> None:
        """
        Record one informational toast.

        :param message: Toast message.
        :param duration: Toast duration.
        :return: None.
        """
        self.messages.append({"kind": "info", "message": message, "duration": duration})

    def show_warning_toast(self, message: str, duration: int = 2000) -> None:
        """
        Record one warning toast.

        :param message: Toast message.
        :param duration: Toast duration.
        :return: None.
        """
        self.messages.append({"kind": "warning", "message": message, "duration": duration})


def build_dialog() -> tuple[FakeMainApp, ServerFileDialogue]:
    """
    Build one server file dialog bound to the fake app.

    :return: Fake app and dialog.
    """
    app: FakeMainApp = FakeMainApp(files_payload=build_server_files_payload())
    dialog: ServerFileDialogue = ServerFileDialogue(parent=None, app=app)
    dialog.toast_manager = RecordingToastManager()
    return app, dialog


def select_file_row(dialog: ServerFileDialogue, row: int) -> None:
    """
    Select one top-level file row in the tree view.

    :param dialog: Dialog under test.
    :param row: Top-level file row.
    :return: None.
    """
    index: QtCore.QModelIndex = dialog._model.index(row, 0)

    # The dialog listens to the current selection model to update its controls.
    dialog.ui.filesTreeView.setCurrentIndex(index)
    dialog.update_selection_details()


def select_model_row(dialog: ServerFileDialogue, file_row: int, model_row: int) -> None:
    """
    Select one model child row in the tree view.

    :param dialog: Dialog under test.
    :param file_row: Parent file row.
    :param model_row: Model child row.
    :return: None.
    """
    parent_index: QtCore.QModelIndex = dialog._model.index(file_row, 0)
    index: QtCore.QModelIndex = dialog._model.index(model_row, 0, parent_index)

    # Child selection is enough because each child cell stores both file and model payloads.
    dialog.ui.filesTreeView.setCurrentIndex(index)
    dialog.update_selection_details()


def test_server_file_dialog_refresh_and_selection_details(qt_app: object) -> None:
    """
    Check tree population, detail labels, and enabled actions for file and model rows.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    app: FakeMainApp
    dialog: ServerFileDialogue
    app, dialog = build_dialog()

    assert app.server_driver.list_calls == 1
    assert dialog._model.rowCount() == 2
    assert dialog.ui.actionLoadFile.isEnabled() is False
    assert dialog.ui.actionLoadBase.isEnabled() is False
    assert dialog.ui.actionLoadModel.isEnabled() is False
    assert dialog.ui.actionSaveCurrent.isEnabled() is False
    assert dialog.ui.actionDeleteSelected.isEnabled() is False

    select_file_row(dialog=dialog, row=0)

    assert dialog.ui.kindValueLabel.text() == "File"
    assert dialog.ui.fileNameValueLabel.text() == "File A"
    assert dialog.ui.fileIdValueLabel.text() == "file-a"
    assert dialog.ui.modelNameValueLabel.text() == "-"
    assert dialog.ui.modelIdValueLabel.text() == "-"
    assert dialog.ui.ownerValueLabel.text() == "alice"
    assert dialog.ui.createdValueLabel.text() == "2026-07-26T20:00:00Z"
    assert dialog.ui.actionLoadFile.isEnabled() is True
    assert dialog.ui.actionLoadBase.isEnabled() is True
    assert dialog.ui.actionLoadModel.isEnabled() is False
    assert dialog.ui.actionSaveCurrent.isEnabled() is True
    assert dialog.ui.actionDeleteSelected.isEnabled() is True

    select_model_row(dialog=dialog, file_row=0, model_row=1)

    assert dialog.ui.kindValueLabel.text() == "Delta model"
    assert dialog.ui.fileNameValueLabel.text() == "File A"
    assert dialog.ui.modelNameValueLabel.text() == "File A Child"
    assert dialog.ui.modelIdValueLabel.text() == "file-a-child"
    assert dialog.ui.actionLoadModel.isEnabled() is True

    dialog.close()
    dialog.deleteLater()


def test_server_file_dialog_load_actions_route_expected_requests(qt_app: object) -> None:
    """
    Check file, base-model, and selected-model load operations.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    app: FakeMainApp
    dialog: ServerFileDialogue

    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.load_selected_file()
    assert app.load_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "",
            "base_only": False,
        }
    ]
    assert dialog.result() == int(dialog.DialogCode.Accepted)
    dialog.close()
    dialog.deleteLater()

    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.load_selected_base_model()
    assert app.load_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "",
            "base_only": True,
        }
    ]
    assert dialog.result() == int(dialog.DialogCode.Accepted)
    dialog.close()
    dialog.deleteLater()

    app, dialog = build_dialog()
    select_model_row(dialog=dialog, file_row=0, model_row=1)
    dialog.load_selected_model()
    assert app.load_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "file-a-child",
            "base_only": False,
        }
    ]
    assert dialog.result() == int(dialog.DialogCode.Accepted)
    dialog.close()
    dialog.deleteLater()


def test_server_file_dialog_save_current_project_targets_file_or_model(qt_app: object) -> None:
    """
    Check that save routes to the selected file or selected model and refreshes afterwards.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    app: FakeMainApp
    dialog: ServerFileDialogue

    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.save_current_project()

    assert app.save_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "",
        }
    ]
    assert app.server_driver.list_calls == 2
    assert dialog.toast_manager.messages[-1]["message"] == "Current project uploaded."
    dialog.close()
    dialog.deleteLater()

    app, dialog = build_dialog()
    select_model_row(dialog=dialog, file_row=0, model_row=1)
    dialog.save_current_project()

    assert app.save_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "file-a-child",
        }
    ]
    assert app.server_driver.list_calls == 2
    assert dialog.toast_manager.messages[-1]["message"] == "Current project uploaded."
    dialog.close()
    dialog.deleteLater()


def test_server_file_dialog_delete_selected_item_handles_cancel_and_confirm(qt_app: object,
                                                                            monkeypatch: Any) -> None:
    """
    Check file and model deletion paths, including confirmation cancellation.

    :param qt_app: Shared Qt application fixture.
    :param monkeypatch: Pytest monkeypatch fixture.
    :return: None.
    """
    del qt_app

    app: FakeMainApp
    dialog: ServerFileDialogue

    monkeypatch.setattr(
        "VeraGrid.Gui.FileDialogues.ServerFileDialog.server_file_dialogue_window.yes_no_question",
        lambda text, title: False,
    )
    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.delete_selected_item()

    assert app.delete_file_calls == list()
    assert dialog.toast_manager.messages[-1]["kind"] == "warning"
    assert dialog.toast_manager.messages[-1]["message"] == "Deletion cancelled."
    assert dialog._model.rowCount() == 2
    dialog.close()
    dialog.deleteLater()

    monkeypatch.setattr(
        "VeraGrid.Gui.FileDialogues.ServerFileDialog.server_file_dialogue_window.yes_no_question",
        lambda text, title: True,
    )
    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.delete_selected_item()

    assert app.delete_file_calls == ["file-a"]
    assert app.server_driver.list_calls == 2
    assert dialog._model.rowCount() == 1
    assert dialog._model.item(0, 0).text() == "File B"
    assert dialog.toast_manager.messages[-1]["message"] == "Server file deleted."
    dialog.close()
    dialog.deleteLater()

    app, dialog = build_dialog()
    select_model_row(dialog=dialog, file_row=0, model_row=1)
    dialog.delete_selected_item()

    assert app.delete_model_calls == [
        {
            "file_idtag": "file-a",
            "model_idtag": "file-a-child",
        }
    ]
    assert app.server_driver.list_calls == 2
    assert dialog._model.item(0, 0).rowCount() == 1
    assert dialog._model.item(0, 0).child(0, 0).text() == "File A Base"
    assert dialog.toast_manager.messages[-1]["message"] == "Server model deleted."
    dialog.close()
    dialog.deleteLater()


def test_server_file_dialog_double_click_uses_natural_action(qt_app: object) -> None:
    """
    Check that double-click routes files to full-file load and models to model load.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    del qt_app

    app: FakeMainApp
    dialog: ServerFileDialogue

    app, dialog = build_dialog()
    select_file_row(dialog=dialog, row=0)
    dialog.on_tree_double_clicked()

    assert app.load_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "",
            "base_only": False,
        }
    ]
    dialog.close()
    dialog.deleteLater()

    app, dialog = build_dialog()
    select_model_row(dialog=dialog, file_row=0, model_row=0)
    dialog.on_tree_double_clicked()

    assert app.load_calls == [
        {
            "file_idtag": "file-a",
            "file_name": "File A",
            "model_idtag": "file-a-base",
            "base_only": False,
        }
    ]
    dialog.close()
    dialog.deleteLater()
