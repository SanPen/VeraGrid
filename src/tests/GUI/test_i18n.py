import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from pathlib import Path
import xml.etree.ElementTree as ET

from VeraGrid.Gui.ShortCircuitEditor.short_circuit_selector import ShortCircuitSelector
from VeraGrid.Gui.AboutDialogue.about_dialogue import translate_about_dialog
from VeraGrid.Gui.Analysis.AnalysisDialogue import translate_analysis_dialog
from VeraGrid.Gui.Main.MainWindow import Ui_mainWindow
from VeraGrid.Gui.i18n import (
    collect_action_shortcut_states,
    ApplicationLanguage,
    ApplicationTranslator,
    LEGACY_LANGUAGE_ALIASES,
    build_language_candidates,
    get_language_display_text,
    get_language_flag_icon_path,
    get_requested_language_code,
    language_from_name,
    restore_action_shortcut_states,
)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGridEngine.enumerations import FaultType, MethodShortCircuit, PhasesShortCircuit


def get_ts_translation(locale_language: ApplicationLanguage, context_name: str, source_text: str) -> str:
    """
    Read one expected translation directly from the shipped TS source file.
    """
    locale_candidates: list[str] = build_language_candidates(str(locale_language.value))
    ts_path: Path = Path(__file__).resolve().parents[2] / "VeraGrid" / "Gui" / "translations" / f"veragrid_{locale_candidates[-1]}.ts"
    root = ET.parse(ts_path).getroot()

    context: object
    message: object

    for context in root.findall("context"):
        if context.findtext("name") != context_name:
            continue
        for message in context.findall("message"):
            if message.findtext("source") == source_text:
                return (message.findtext("translation") or "").strip()

    return ""


def test_requested_language_prefers_first_ui_language() -> None:
    """
    The translation loader should normalize the first usable UI language code.
    """
    language_code: str = get_requested_language_code(
        language=ApplicationLanguage.SYSTEM,
        ui_languages=["es-ES", "en-US"],
    )

    assert language_code == "es_ES"
    assert build_language_candidates(language_code) == ["es_ES", "es"]


@pytest.mark.parametrize(
    ("saved_name", "expected_language"),
    [
        ("HINDI", ApplicationLanguage.HINDI),
        ("हिंदी", ApplicationLanguage.HINDI),
        ("Japanese", ApplicationLanguage.JAPANESE),
        ("日本語", ApplicationLanguage.JAPANESE),
        ("Korean", ApplicationLanguage.KOREAN),
        ("한국어", ApplicationLanguage.KOREAN),
        ("Mandarin", ApplicationLanguage.CHINESE),
        ("普通话", ApplicationLanguage.CHINESE),
        ("Español", ApplicationLanguage.SPANISH),
        ("Portuguese", ApplicationLanguage.PORTUGUESE),
    ],
)
def test_language_from_name_accepts_legacy_selector_labels(
    saved_name: str,
    expected_language: ApplicationLanguage,
) -> None:
    """
    Saved GUI configs should keep working whether they stored enum names or selector labels.
    """
    assert language_from_name(saved_name) == expected_language


@pytest.mark.parametrize(
    ("expected_language", "saved_name"),
    [
        (language, alias)
        for language, aliases in LEGACY_LANGUAGE_ALIASES.items()
        for alias in sorted(aliases)
    ],
)
def test_language_from_name_accepts_all_shipped_legacy_translations(
    expected_language: ApplicationLanguage,
    saved_name: str,
) -> None:
    """
    Any language label previously shipped in the selector should still round-trip from config.
    """
    assert language_from_name(saved_name) == expected_language


def test_short_circuit_selector_uses_combo_data_not_display_text(qt_app: object) -> None:
    """
    The selector should keep working after translated labels replace the enum text.
    """
    _unused_app: object = qt_app
    dialog = ShortCircuitSelector()

    dialog.ui.cb_fault.setCurrentIndex(0)
    dialog.ui.cb_method.setCurrentIndex(0)
    dialog.update_logic()
    dialog.update_view()
    dialog.ui.cb_fault.setItemText(dialog.ui.cb_fault.currentIndex(), "Falla traducida")
    dialog.ui.cb_method.setItemText(dialog.ui.cb_method.currentIndex(), "Metodo traducido")
    dialog.ui.cb_phases.setItemText(dialog.ui.cb_phases.currentIndex(), "Fase traducida")

    fault, method, phase = dialog.get_selection()

    assert isinstance(fault, FaultType)
    assert isinstance(method, MethodShortCircuit)
    assert isinstance(phase, PhasesShortCircuit)


def test_install_translators_loads_spanish_catalog(qt_app: object) -> None:
    """
    The startup loader should install the compiled VeraGrid translation catalog.
    """
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(ApplicationLanguage.SPANISH)

    assert QtCore.QCoreApplication.translate("messages", "Information") == "Información"
    assert QtCore.QCoreApplication.translate("mainWindow", "File") == "Archivo"
    assert QtCore.QCoreApplication.translate("mainWindow", "Model") == "Modelo"
    assert QtCore.QCoreApplication.translate("BlockEditorWindow", "Library") == "Biblioteca"
    assert QtCore.QCoreApplication.translate("CatalogueElementsDialog", "Select all") == "Seleccionar todo"
    assert QtCore.QCoreApplication.translate("CgmesImportDialog", "CGMES Import") == "Importación CGMES"
    assert QtCore.QCoreApplication.translate("DgsImportDialog", "DGS Import") == "Importación DGS"
    assert QtCore.QCoreApplication.translate("DynamicEditorWorkspaceWindow", "Delete all") == "Eliminar todo"
    assert QtCore.QCoreApplication.translate("ExcelSelectionDialog", "Excel sheet selection") == "Selección de hoja de Excel"
    assert QtCore.QCoreApplication.translate("LineEditorDialog", "Available templates") == "Plantillas disponibles"
    assert QtCore.QCoreApplication.translate("MainWindow", "Copy sigma table") == "Copiar tabla sigma"
    assert QtCore.QCoreApplication.translate("MainWindow", "How To Use This Dashboard") == "Cómo usar este panel"
    assert QtCore.QCoreApplication.translate("MainWindow", "Contingency planner") == "Planificador de contingencias"
    assert QtCore.QCoreApplication.translate("MainWindow", "Wind power wizard") == "Asistente de potencia eólica"
    assert QtCore.QCoreApplication.translate("MainWindow", "Insert Catalogue Component") == "Insertar componente de catálogo"
    assert QtCore.QCoreApplication.translate("MainWindow", "Number of nodes") == "Número de nodos"


@pytest.mark.parametrize(
    ("language", "file_text", "selector_text"),
    [
        (
            ApplicationLanguage.JAPANESE,
            "ファイル",
            "日本語",
        ),
        (
            ApplicationLanguage.KOREAN,
            "파일",
            "한국어",
        ),
        (
            ApplicationLanguage.BASQUE,
            "Fitxategia",
            "Euskara",
        ),
        (
            ApplicationLanguage.FRENCH,
            "Fichier",
            "Français",
        ),
        (
            ApplicationLanguage.GALICIAN,
            "Arquivo",
            "Galego",
        ),
        (
            ApplicationLanguage.CATALAN,
            "Fitxer",
            "Català",
        ),
        (
            ApplicationLanguage.ARABIC,
            "ملف",
            "عربي",
        ),
        (
            ApplicationLanguage.ITALIAN,
            "File",
            "Italiano",
        ),
        (
            ApplicationLanguage.GREEK,
            "Αρχείο",
            "Ελληνικά",
        ),
        (
            ApplicationLanguage.DUTCH,
            "Bestand",
            "Nederlands",
        ),
        (
            ApplicationLanguage.PORTUGUESE,
            "Arquivo",
            "Português",
        ),
        (
            ApplicationLanguage.GERMAN,
            "Datei",
            "Deutsch",
        ),
        (
            ApplicationLanguage.CHINESE,
            "文件",
            "普通话",
        ),
        (
            ApplicationLanguage.HINDI,
            "फ़ाइल",
            "हिंदी",
        ),
        (
            ApplicationLanguage.CANTONESE,
            "檔案",
            "廣東話",
        ),
    ],
)
def test_install_translators_load_additional_catalogs(
    qt_app: object,
    language: ApplicationLanguage,
    file_text: str,
    selector_text: str,
) -> None:
    """
    The additional compiled catalogs should expose menu and message strings,
    while the selector keeps stable endonyms for each language row.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(language)

    assert QtCore.QCoreApplication.translate("mainWindow", "File") == file_text
    assert get_language_display_text(language, lambda text: QtCore.QCoreApplication.translate("ConfigurationMain", text)) == selector_text


@pytest.mark.parametrize(
    "language",
    [
        ApplicationLanguage.SYSTEM,
        ApplicationLanguage.ENGLISH,
        ApplicationLanguage.JAPANESE,
        ApplicationLanguage.KOREAN,
        ApplicationLanguage.BASQUE,
        ApplicationLanguage.GALICIAN,
        ApplicationLanguage.ARABIC,
        ApplicationLanguage.ITALIAN,
        ApplicationLanguage.GREEK,
        ApplicationLanguage.DUTCH,
        ApplicationLanguage.CATALAN,
        ApplicationLanguage.CHINESE,
        ApplicationLanguage.HINDI,
        ApplicationLanguage.CANTONESE,
        ApplicationLanguage.GERMAN,
        ApplicationLanguage.FRENCH,
        ApplicationLanguage.PORTUGUESE,
        ApplicationLanguage.SPANISH,
    ],
)
def test_language_flag_icons_are_registered(language: ApplicationLanguage) -> None:
    """
    The language selector flag icons should be available through the Qt resource system.
    """
    icon_path: str = get_language_flag_icon_path(language)
    icon: QtGui.QIcon = QtGui.QIcon(icon_path)

    assert icon.isNull() is False


def test_translated_ui_shortcuts_can_be_restored_to_source_sequences(qt_app: object) -> None:
    """
    The source-defined QAction shortcuts should remain stable after a language change.
    """
    _unused_app: object = qt_app
    window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    ui: Ui_mainWindow = Ui_mainWindow()
    ui.setupUi(window)

    shortcut_states = collect_action_shortcut_states(window)
    original_shortcut: str = ui.actionAdd_circuit.shortcut().toString(QtGui.QKeySequence.SequenceFormat.PortableText)
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translated_shortcut: str
    restored_shortcut: str

    translator.set_language(ApplicationLanguage.CHINESE)
    ui.retranslateUi(window)
    translated_shortcut = ui.actionAdd_circuit.shortcut().toString(QtGui.QKeySequence.SequenceFormat.PortableText)

    restore_action_shortcut_states(window, shortcut_states)
    restored_shortcut = ui.actionAdd_circuit.shortcut().toString(QtGui.QKeySequence.SequenceFormat.PortableText)

    assert original_shortcut == "Ctrl+N, Ctrl+O"
    assert translated_shortcut == ""
    assert restored_shortcut == original_shortcut


def test_hindi_main_window_menu_titles_render_in_ui(qt_app: object) -> None:
    """
    The compiled Hindi catalog should translate the actual main-window menu titles.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(ApplicationLanguage.HINDI)

    window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    ui: Ui_mainWindow = Ui_mainWindow()
    ui.setupUi(window)

    assert ui.menuProject.title() == "फ़ाइल"
    assert ui.menuActions.title() == "क्रियाएँ"
    assert ui.menuSimulations.title() == "सिमुलेशन"
    assert ui.menuModel.title() == "मॉडल"
    assert ui.menuDiagrams.title() == "आरेख"
    assert ui.menuEvents.title() == "घटनाएँ"
    assert ui.menuAbout.title() == "मदद"


@pytest.mark.parametrize(
    "language",
    [
        ApplicationLanguage.JAPANESE,
        ApplicationLanguage.KOREAN,
        ApplicationLanguage.BASQUE,
        ApplicationLanguage.GALICIAN,
        ApplicationLanguage.ARABIC,
        ApplicationLanguage.ITALIAN,
        ApplicationLanguage.GREEK,
        ApplicationLanguage.DUTCH,
        ApplicationLanguage.CATALAN,
        ApplicationLanguage.CHINESE,
        ApplicationLanguage.HINDI,
        ApplicationLanguage.CANTONESE,
        ApplicationLanguage.GERMAN,
        ApplicationLanguage.FRENCH,
        ApplicationLanguage.PORTUGUESE,
        ApplicationLanguage.SPANISH,
    ],
)
def test_plugin_reload_action_translation_exists(
    qt_app: object,
    language: ApplicationLanguage,
) -> None:
    """
    The plugin reload action should resolve through the shared ContextMenu catalog.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(language)

    expected_text: str = get_ts_translation(language, "ContextMenu", "Reload")

    assert expected_text != ""
    assert QtCore.QCoreApplication.translate("ContextMenu", "Reload") == expected_text


@pytest.mark.parametrize(
    ("language", "about_text", "dashboard_text"),
    [
        (ApplicationLanguage.HINDI, "VeraGrid के बारे में", "ग्रिड स्वास्थ्य डैशबोर्ड"),
        (ApplicationLanguage.KOREAN, "VeraGrid 소개", "그리드 상태 대시보드"),
        (ApplicationLanguage.SPANISH, "Acerca de VeraGrid", "Panel de salud de la red"),
    ],
)
def test_runtime_translation_helpers_use_existing_catalog_contexts(
    qt_app: object,
    language: ApplicationLanguage,
    about_text: str,
    dashboard_text: str,
) -> None:
    """
    Runtime-only dialogs should translate through the same contexts as their generated UI files.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(language)

    assert translate_about_dialog("About VeraGrid") == about_text
    assert translate_analysis_dialog("Grid Health Dashboard") == dashboard_text


@pytest.mark.parametrize(
    ("source_text", "expected_text"),
    [
        ("Model v. {model_version}", "मॉडल सं. {model_version}"),
        ("idtag. {idtag}", "आईडीटैग. {idtag}"),
        ("User: {user_name}", "उपयोगकर्ता: {user_name}"),
        ("Compiling the grid...", "ग्रिड को संकलित किया जा रहा है..."),
        ("Running power flow...", "पावर फ्लो चल रहा है..."),
    ],
)
def test_hindi_simulation_runtime_strings_use_simulations_context(
    qt_app: object,
    source_text: str,
    expected_text: str,
) -> None:
    """
    Runtime simulation labels should resolve through the shared SimulationsMain context.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(ApplicationLanguage.HINDI)

    assert QtCore.QCoreApplication.translate("SimulationsMain", source_text) == expected_text


@pytest.mark.parametrize(
    ("language", "expected_text"),
    [
        (ApplicationLanguage.ENGLISH, "English"),
        (ApplicationLanguage.JAPANESE, "日本語"),
        (ApplicationLanguage.KOREAN, "한국어"),
        (ApplicationLanguage.HINDI, "हिंदी"),
        (ApplicationLanguage.CANTONESE, "廣東話"),
        (ApplicationLanguage.SPANISH, "Español"),
    ],
)
def test_language_selector_uses_stable_endonyms(
    qt_app: object,
    language: ApplicationLanguage,
    expected_text: str,
) -> None:
    """
    Language selector labels should stay readable even when locale catalogs are incomplete.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(ApplicationLanguage.HINDI)

    assert get_language_display_text(language, lambda text: QtCore.QCoreApplication.translate("ConfigurationMain", text)) == expected_text


@pytest.mark.parametrize(
    ("active_language", "selector_language", "selector_text"),
    [
        (ApplicationLanguage.SPANISH, ApplicationLanguage.JAPANESE, "日本語"),
        (ApplicationLanguage.KOREAN, ApplicationLanguage.KOREAN, "한국어"),
        (ApplicationLanguage.CATALAN, ApplicationLanguage.FRENCH, "Français"),
        (ApplicationLanguage.GERMAN, ApplicationLanguage.GREEK, "Ελληνικά"),
        (ApplicationLanguage.ITALIAN, ApplicationLanguage.JAPANESE, "日本語"),
        (ApplicationLanguage.PORTUGUESE, ApplicationLanguage.JAPANESE, "日本語"),
        (ApplicationLanguage.CHINESE, ApplicationLanguage.CHINESE, "普通话"),
        (ApplicationLanguage.HINDI, ApplicationLanguage.HINDI, "हिंदी"),
        (ApplicationLanguage.CANTONESE, ApplicationLanguage.CANTONESE, "廣東話"),
    ],
)
def test_language_selector_names_start_with_capitals(
    qt_app: object,
    active_language: ApplicationLanguage,
    selector_language: ApplicationLanguage,
    selector_text: str,
) -> None:
    """
    The selector should keep stable endonyms instead of depending on catalog coverage.
    """
    _unused_app: object = qt_app
    translator: ApplicationTranslator = ApplicationTranslator(qt_app)
    translator.set_language(active_language)

    assert get_language_display_text(selector_language, lambda text: QtCore.QCoreApplication.translate("ConfigurationMain", text)) == selector_text
