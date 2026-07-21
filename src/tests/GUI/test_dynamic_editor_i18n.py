from PySide6 import QtCore

from VeraGrid.Gui.DynamicModelEditor.detachable_editor_tabs_widget import (
    DynamicEditorAddButton,
    DynamicEditorPickerDialog,
)


class FakeTranslator(QtCore.QTranslator):
    """
    Tiny translator used to verify runtime-created widget text honors Qt translation lookups.
    """

    def translate(
        self,
        context: str,
        source_text: str,
        disambiguation: str | None = None,
        n: int = -1,
    ) -> str:
        _unused_disambiguation = disambiguation
        _unused_n = n
        translations: dict[tuple[str, str], str] = {
            ("DynamicEditorPickerDialog", "Quick Open"): "Apertura rapida",
            ("DynamicEditorPickerDialog", "Search dynamic editors"): "Buscar editores dinamicos",
            ("DynamicEditorPickerDialog", "Mode"): "Modo",
            ("DynamicEditorPickerDialog", "Name"): "Nombre",
            ("DynamicEditorPickerDialog", "Type"): "Tipo",
            ("DynamicEditorPickerDialog", "Modes"): "Modos",
            ("DynamicEditorPickerDialog", "Open the current block in the other mode."): "Abrir el bloque actual en el otro modo.",
            ("DynamicEditorAddButton", "Open another Dynamic Editor"): "Abrir otro editor dinamico",
        }
        return translations.get((context, source_text), "")


def test_dynamic_editor_runtime_widgets_refresh_translations(qt_app: object) -> None:
    """
    Runtime-created dynamic-editor widgets should refresh their labels and tooltips on language changes.
    """
    picker = DynamicEditorPickerDialog(entries=[])
    add_button = DynamicEditorAddButton()
    translator = FakeTranslator()

    qt_app.installTranslator(translator)
    language_event = QtCore.QEvent(QtCore.QEvent.Type.LanguageChange)
    QtCore.QCoreApplication.sendEvent(picker, language_event)
    QtCore.QCoreApplication.sendEvent(add_button, language_event)

    assert picker.quickOpenGroupBox.title() == "Apertura rapida"
    assert picker.searchLineEdit.placeholderText() == "Buscar editores dinamicos"
    assert picker.modeLabel.text() == "Modo"
    assert picker.entriesTableWidget.horizontalHeaderItem(0).text() == "Nombre"
    assert picker.entriesTableWidget.horizontalHeaderItem(1).text() == "Tipo"
    assert picker.entriesTableWidget.horizontalHeaderItem(2).text() == "Modos"
    assert picker.quickOpenLabel.text() == "Abrir el bloque actual en el otro modo."
    assert add_button.toolTip() == "Abrir otro editor dinamico"

    qt_app.removeTranslator(translator)
