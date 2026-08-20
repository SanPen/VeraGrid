from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable

from PySide6.QtCore import QObject, QLibraryInfo, QLocale, QTranslator
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication

from VeraGridEngine.IO.file_system import get_create_veragrid_folder


class ApplicationLanguage(Enum):
    """
    Supported application language selection modes.
    """

    SYSTEM = "system"
    ENGLISH = "en"
    JAPANESE = "ja_JP"
    KOREAN = "ko_KR"
    BASQUE = "eu_ES"
    GALICIAN = "gl_ES"
    ARABIC = "ar"
    ITALIAN = "it_IT"
    GREEK = "el_GR"
    DUTCH = "nl_NL"
    CATALAN = "ca_ES"
    CHINESE = "zh_CN"
    HINDI = "hi_IN"
    CANTONESE = "yue_HK"
    GERMAN = "de_DE"
    FRENCH = "fr_FR"
    PORTUGUESE = "pt_PT"
    SPANISH = "es_ES"
    POLISH = "pl_PL"

    def __str__(self) -> str:
        """
        Return the stable serialized identifier for one language option.

        :returns: Stable language identifier.
        """
        return self.value


class InstalledTranslations:
    """
    Container keeping the installed Qt translators alive for the application lifetime.
    """

    __slots__ = ("app_translator", "qtbase_translator")

    def __init__(self) -> None:
        """
        Build one empty translation container.

        :returns: None.
        """
        self.app_translator: QTranslator | None = None
        self.qtbase_translator: QTranslator | None = None


class ActionShortcutState:
    """
    Stable source-language shortcut snapshot for one QAction.
    """

    __slots__ = ("action_name", "shortcut_texts")

    def __init__(self, action_name: str, shortcut_texts: list[str]) -> None:
        """
        Store one action shortcut definition.

        :param action_name: QObject name of the QAction.
        :param shortcut_texts: Shortcut sequences in portable text form.
        :returns: None.
        """
        self.action_name: str = action_name
        self.shortcut_texts: list[str] = shortcut_texts


class ApplicationTranslator:
    """
    Application-wide translator installer and lifetime owner.
    """

    __slots__ = ("_app", "_current_language", "_installed_translations")

    def __init__(self, app: QApplication) -> None:
        """
        Build one translator controller for the running Qt application.

        :param app: Qt application receiving translator installations.
        :returns: None.
        """
        self._app: QApplication = app
        self._current_language: ApplicationLanguage = ApplicationLanguage.SYSTEM
        self._installed_translations: InstalledTranslations = InstalledTranslations()

    def get_current_language(self) -> ApplicationLanguage:
        """
        Return the currently selected application language.

        :returns: Current application language.
        """
        return self._current_language

    def set_language(self, language: ApplicationLanguage) -> None:
        """
        Apply one language selection to the whole application.

        The method removes any previous translators first because Qt only keeps
        the last installed translation chain consistent when the old instances
        are removed explicitly before the new ones are installed.

        :param language: Requested application language.
        :returns: None.
        """
        requested_language_code: str = get_requested_language_code(language=language)
        candidate_languages: list[str] = build_language_candidates(requested_language_code)

        # Remove the previous translators before installing the new language,
        # otherwise strings from multiple languages can remain active.
        self._clear_translators()

        # Update Qt's default locale so built-in widgets use the same locale
        # rules as the translation catalogs we are about to install.
        if len(requested_language_code) > 0:
            QLocale.setDefault(QLocale(requested_language_code))
        else:
            QLocale.setDefault(QLocale.system())

        # Install the application catalog first so VeraGrid strings resolve
        # before the built-in Qt dialog strings are queried.
        self._installed_translations.app_translator = load_translator(
            prefix="veragrid",
            directory=str(get_translations_directory()),
            candidates=candidate_languages,
        )
        if self._installed_translations.app_translator is not None:
            self._app.installTranslator(self._installed_translations.app_translator)
        else:
            pass

        # Install Qt's own catalog afterwards so stock widgets like file dialogs
        # and message buttons switch to the same language when available.
        self._installed_translations.qtbase_translator = load_translator(
            prefix="qtbase",
            directory=get_qt_translations_directory(),
            candidates=candidate_languages,
        )
        if self._installed_translations.qtbase_translator is not None:
            self._app.installTranslator(self._installed_translations.qtbase_translator)
        else:
            pass

        self._current_language = language

    def _clear_translators(self) -> None:
        """
        Remove any translators currently installed by this controller.

        :returns: None.
        """
        if self._installed_translations.app_translator is not None:
            self._app.removeTranslator(self._installed_translations.app_translator)
            self._installed_translations.app_translator = None
        else:
            pass

        if self._installed_translations.qtbase_translator is not None:
            self._app.removeTranslator(self._installed_translations.qtbase_translator)
            self._installed_translations.qtbase_translator = None
        else:
            pass


def collect_action_shortcut_states(parent: QObject) -> list[ActionShortcutState]:
    """
    Capture the source-defined shortcuts of every named action below one Qt object.

    Qt Designer exports shortcuts as translatable strings. Some translated
    catalogs change the sequence syntax enough for Qt to drop the shortcut on
    retranslation, so the source values are captured once and later restored.

    :param parent: Qt object owning the actions.
    :returns: Saved shortcut states for actions that define shortcuts.
    """
    action_states: list[ActionShortcutState] = list()
    action: QAction

    for action in parent.findChildren(QAction):
        shortcut_texts: list[str] = list()
        shortcut: QKeySequence

        if len(action.objectName()) == 0:
            pass
        else:
            for shortcut in action.shortcuts():
                shortcut_text: str = shortcut.toString(QKeySequence.SequenceFormat.PortableText)
                if len(shortcut_text) > 0:
                    shortcut_texts.append(shortcut_text)
                else:
                    pass

            if len(shortcut_texts) > 0:
                action_states.append(
                    ActionShortcutState(
                        action_name=action.objectName(),
                        shortcut_texts=shortcut_texts,
                    )
                )
            else:
                pass

    return action_states


def restore_action_shortcut_states(
    parent: QObject,
    action_states: list[ActionShortcutState],
) -> None:
    """
    Restore previously captured source shortcuts after a UI retranslation.

    :param parent: Qt object owning the actions.
    :param action_states: Source shortcut states to restore.
    :returns: None.
    """
    action_state: ActionShortcutState

    for action_state in action_states:
        action: QAction | None = parent.findChild(QAction, action_state.action_name)
        shortcut_text: str
        shortcuts: list[QKeySequence] = list()

        if action is None:
            pass
        else:
            for shortcut_text in action_state.shortcut_texts:
                shortcuts.append(
                    QKeySequence.fromString(
                        shortcut_text,
                        QKeySequence.SequenceFormat.PortableText,
                    )
                )

            if len(shortcuts) > 0:
                action.setShortcuts(shortcuts)
            else:
                pass


def get_translations_directory() -> Path:
    """
    Return the VeraGrid translations directory.

    :returns: Application translations directory.
    """
    return Path(__file__).resolve().parent / "translations"


def get_qt_translations_directory() -> str:
    """
    Return the Qt built-in translations directory.

    :returns: Qt translations directory.
    """
    return QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)


def normalize_language_code(language_code: str | None) -> str:
    """
    Normalize one locale string to the ``ll`` or ``ll_CC`` form used by Qt catalogs.

    :param language_code: Raw locale code.
    :returns: Normalized locale code or an empty string.
    """
    raw_text: str = "" if language_code is None else str(language_code).strip()

    if len(raw_text) == 0:
        return ""
    else:
        pass

    locale_text: str = raw_text.split(".", 1)[0].replace("-", "_")
    parts: list[str] = [part for part in locale_text.split("_") if len(part) > 0]

    if len(parts) == 0:
        return ""
    else:
        if len(parts) == 1:
            return parts[0].lower()
        else:
            return parts[0].lower() + "_" + parts[1].upper()


def build_language_candidates(language_code: str | None) -> list[str]:
    """
    Build the locale fallback order used when loading ``.qm`` files.

    :param language_code: Preferred locale code.
    :returns: Locale candidates ordered from most specific to least specific.
    """
    normalized_code: str = normalize_language_code(language_code)

    if len(normalized_code) == 0:
        return list()
    else:
        if "_" in normalized_code:
            base_language: str = normalized_code.split("_", 1)[0]
            return [normalized_code, base_language]
        else:
            return [normalized_code]


def get_system_language_code(ui_languages: Iterable[str] | None = None) -> str:
    """
    Return the first usable language reported by the system locale.

    :param ui_languages: Optional override used by tests.
    :returns: Normalized preferred system language code or an empty string.
    """
    language_items: Iterable[str]

    if ui_languages is None:
        language_items = QLocale.system().uiLanguages()
    else:
        language_items = ui_languages

    language_item: str

    for language_item in language_items:
        normalized_code: str = normalize_language_code(language_item)
        if len(normalized_code) > 0:
            return normalized_code
        else:
            pass

    return ""


def get_requested_language_code(
    language: ApplicationLanguage,
    ui_languages: Iterable[str] | None = None,
) -> str:
    """
    Resolve one application language selection to a concrete locale code.

    :param language: Selected application language.
    :param ui_languages: Optional system-language override used by tests.
    :returns: Concrete locale code or an empty string.
    """
    if language == ApplicationLanguage.SYSTEM:
        return get_system_language_code(ui_languages=ui_languages)
    else:
        return normalize_language_code(str(language.value))


def get_language_display_text(
    language: ApplicationLanguage,
    translate: Callable[[str], str] | None = None,
) -> str:
    """
    Return the visible label for one language selector entry.

    ``SYSTEM`` remains translatable because it describes an application mode.
    Concrete languages use stable endonyms so the selector does not depend on
    per-locale catalog coverage.

    :param language: Language shown in the selector.
    :param translate: Optional callback used for translatable labels.
    :returns: Visible selector text.
    """
    if translate is None:
        translate = lambda source_text: source_text
    else:
        pass

    if language == ApplicationLanguage.SYSTEM:
        return translate("System default")
    else:
        endonyms: dict[ApplicationLanguage, str] = {
            ApplicationLanguage.ENGLISH: "English",
            ApplicationLanguage.JAPANESE: "日本語",
            ApplicationLanguage.KOREAN: "한국어",
            ApplicationLanguage.BASQUE: "Euskara",
            ApplicationLanguage.GALICIAN: "Galego",
            ApplicationLanguage.ARABIC: "عربي",
            ApplicationLanguage.ITALIAN: "Italiano",
            ApplicationLanguage.GREEK: "Ελληνικά",
            ApplicationLanguage.DUTCH: "Nederlands",
            ApplicationLanguage.CATALAN: "Català",
            ApplicationLanguage.CHINESE: "普通话",
            ApplicationLanguage.HINDI: "हिंदी",
            ApplicationLanguage.CANTONESE: "廣東話",
            ApplicationLanguage.GERMAN: "Deutsch",
            ApplicationLanguage.FRENCH: "Français",
            ApplicationLanguage.PORTUGUESE: "Português",
            ApplicationLanguage.SPANISH: "Español",
            ApplicationLanguage.POLISH: "Polski",
        }
        return endonyms.get(language, "English")


def get_language_flag_icon_path(language: ApplicationLanguage) -> str:
    """
    Return the Qt resource path for one language selector flag icon.

    :param language: Language shown in the selector.
    :returns: Qt resource path for the matching flag icon.
    """
    if language == ApplicationLanguage.SYSTEM:
        return ":/Icons/icons/flag_system.png"
    else:
        if language == ApplicationLanguage.ENGLISH:
            return ":/Icons/icons/flag_en.png"
        else:
            if language == ApplicationLanguage.JAPANESE:
                return ":/Icons/icons/flag_ja.png"
            else:
                if language == ApplicationLanguage.KOREAN:
                    return ":/Icons/icons/flag_ko.png"
                else:
                    if language == ApplicationLanguage.BASQUE:
                        return ":/Icons/icons/flag_eu.png"
                    else:
                        if language == ApplicationLanguage.GALICIAN:
                            return ":/Icons/icons/flag_gl.png"
                        else:
                            if language == ApplicationLanguage.ARABIC:
                                return ":/Icons/icons/flag_ar.png"
                            else:
                                if language == ApplicationLanguage.ITALIAN:
                                    return ":/Icons/icons/flag_it.png"
                                else:
                                    if language == ApplicationLanguage.GREEK:
                                        return ":/Icons/icons/flag_el.png"
                                    else:
                                        if language == ApplicationLanguage.DUTCH:
                                            return ":/Icons/icons/flag_nl.png"
                                        else:
                                            if language == ApplicationLanguage.CATALAN:
                                                return ":/Icons/icons/flag_ca.png"
                                            else:
                                                if language == ApplicationLanguage.CHINESE:
                                                    return ":/Icons/icons/flag_zh.png"
                                                else:
                                                    if language == ApplicationLanguage.HINDI:
                                                        return ":/Icons/icons/flag_hi.png"
                                                    else:
                                                        if language == ApplicationLanguage.CANTONESE:
                                                            return ":/Icons/icons/flag_zh.png"
                                                        else:
                                                            if language == ApplicationLanguage.GERMAN:
                                                                return ":/Icons/icons/flag_de.png"
                                                            else:
                                                                if language == ApplicationLanguage.FRENCH:
                                                                    return ":/Icons/icons/flag_fr.png"
                                                                else:
                                                                    if language == ApplicationLanguage.PORTUGUESE:
                                                                        return ":/Icons/icons/flag_pt.png"
                                                                    else:
                                                                        if language == ApplicationLanguage.POLISH:
                                                                            return ":/Icons/icons/flag_pl.png"
                                                                        else:
                                                                            return ":/Icons/icons/flag_es.png"


def load_translator(prefix: str, directory: str, candidates: list[str]) -> QTranslator | None:
    """
    Load one Qt translator by trying each locale candidate in order.

    :param prefix: Translation file prefix.
    :param directory: Directory containing the translation files.
    :param candidates: Ordered locale candidate list.
    :returns: Loaded translator or ``None``.
    """
    locale_candidate: str

    for locale_candidate in candidates:
        translator: QTranslator = QTranslator()
        if translator.load(f"{prefix}_{locale_candidate}", directory):
            return translator
        else:
            pass

    return None


def get_gui_config_file_path() -> Path:
    """
    Return the GUI configuration file path used to persist the language selection.

    :returns: GUI configuration file path.
    """
    return Path(get_create_veragrid_folder()) / "gui_config.json"


LEGACY_LANGUAGE_ALIASES: dict[ApplicationLanguage, set[str]] = {
    ApplicationLanguage.SYSTEM: {
        "الافتراضي للنظام",
        "Sistema predeterminat",
        "Systemstandard",
        "Προεπιλογή συστήματος",
        "Valor predeterminado del sistema",
        "Sistema lehenetsia",
        "Valeur par défaut du système",
        "Sistema predeterminado",
        "Predefinito del sistema",
        "システムのデフォルト",
        "Systeemstandaard",
        "Padrão do sistema",
        "系统默认",
    },
    ApplicationLanguage.ENGLISH: {
        "إنجليزي",
        "Anglès",
        "Englisch",
        "Αγγλικός",
        "Inglés",
        "Ingelesa",
        "Anglais",
        "Inglese",
        "英語",
        "Engels",
        "Inglês",
        "英语",
    },
    ApplicationLanguage.JAPANESE: {
        "يابانية",
        "Japonès",
        "Japanisch",
        "Ιαπωνικά",
        "Japonés",
        "Japoniarra",
        "Japonais",
        "Xaponés",
        "Giapponese",
        "Japanse",
        "Japonês",
    },
    ApplicationLanguage.BASQUE: {
        "الباسك",
        "Basc",
        "Baskisch",
        "Βάσκος",
        "Vasco",
        "Basque",
        "Basco",
        "バスク語",
        "Baskisch",
        "Basco",
        "巴斯克",
    },
    ApplicationLanguage.GALICIAN: {
        "الجاليكية",
        "Gallec",
        "Galizisch",
        "Γαλικιανός",
        "Gallego",
        "Galegoa",
        "Galicien",
        "Galiziano",
        "ガリシア語",
        "Galicisch",
        "加利西亚语",
    },
    ApplicationLanguage.ARABIC: {
        "Àrab",
        "Arabisch",
        "Αραβικός",
        "Árabe",
        "Arabiera",
        "Arabe",
        "Arabo",
        "アラビア語",
        "阿拉伯",
    },
    ApplicationLanguage.ITALIAN: {
        "ايطالي",
        "Italià",
        "Italienisch",
        "Ιταλικά",
        "Italian",
        "Italiarra",
        "Italien",
        "Italiano",
        "イタリア語",
        "Italiaans",
        "意大利语",
    },
    ApplicationLanguage.GREEK: {
        "اليونانية",
        "Grec",
        "Griechisch",
        "Griego",
        "Grekoa",
        "Greco",
        "Grego",
        "ギリシャ語",
        "Grieks",
        "希腊语",
    },
    ApplicationLanguage.DUTCH: {
        "هولندي",
        "Holandès",
        "Ολλανδός",
        "Holandés",
        "Holandarra",
        "Néerlandais",
        "Niederländisch",
        "Olandese",
        "オランダ語",
        "Holandês",
        "荷兰语",
    },
    ApplicationLanguage.CATALAN: {
        "الكاتالونية",
        "Katalanisch",
        "Καταλανικά",
        "Catalán",
        "Katalana",
        "Catalan",
        "Catalano",
        "カタルーニャ語",
        "Catalaans",
        "Catalão",
        "加泰罗尼亚语",
    },
    ApplicationLanguage.CHINESE: {
        "Mandarín",
        "मंदारिन",
        "普通話",
    },
    ApplicationLanguage.HINDI: {
        "印地语",
        "印地語",
    },
    ApplicationLanguage.CANTONESE: {
        "Cantonés",
        "कैंटोनीज़",
    },
    ApplicationLanguage.GERMAN: {
        "الألمانية",
        "Alemany",
        "Γερμανός",
        "Alemán",
        "Alemana",
        "Allemand",
        "Tedesco",
        "ドイツ語",
        "Duits",
        "Alemão",
        "德语",
    },
    ApplicationLanguage.FRENCH: {
        "فرنسي",
        "Französisch",
        "Francès",
        "Francês",
        "Γάλλος",
        "Francés",
        "Frantsesa",
        "Francese",
        "フランス語",
        "Frans",
        "法语",
    },
    ApplicationLanguage.PORTUGUESE: {
        "البرتغالية",
        "Portuguès",
        "Portugiesisch",
        "Πορτογάλος",
        "Portugués",
        "Portugesa",
        "Portugais",
        "Portoghese",
        "ポルトガル語",
        "Portugees",
        "葡萄牙语",
    },
    ApplicationLanguage.SPANISH: {
        "الاسبانية",
        "Espanyol",
        "Spanisch",
        "Espagnol",
        "スペイン語",
        "Spaans",
        "Espanhol",
        "西班牙语",
    },
    ApplicationLanguage.POLISH: {
        "بولندي",
        "Polonès",
        "Polnisch",
        "Πολωνικά",
        "Polaco",
        "Polako",
        "Polonais",
        "Polacco",
        "ポーランド語",
        "Pools",
        "Polonês",
        "波兰语",
    },
}


def language_from_name(name_text: str | None) -> ApplicationLanguage:
    """
    Parse one persisted language name into the corresponding enum value.

    :param name_text: Persisted enum name.
    :returns: Matching application language.
    """
    if name_text is None:
        return ApplicationLanguage.SYSTEM
    else:
        pass

    normalized_name: str = str(name_text).strip()
    english_aliases: dict[ApplicationLanguage, str] = {
        ApplicationLanguage.SYSTEM: "System default",
        ApplicationLanguage.ENGLISH: "English",
        ApplicationLanguage.JAPANESE: "Japanese",
        ApplicationLanguage.KOREAN: "Korean",
        ApplicationLanguage.BASQUE: "Basque",
        ApplicationLanguage.GALICIAN: "Galician",
        ApplicationLanguage.ARABIC: "Arabic",
        ApplicationLanguage.ITALIAN: "Italian",
        ApplicationLanguage.GREEK: "Greek",
        ApplicationLanguage.DUTCH: "Dutch",
        ApplicationLanguage.CATALAN: "Catalan",
        ApplicationLanguage.CHINESE: "Mandarin",
        ApplicationLanguage.HINDI: "Hindi",
        ApplicationLanguage.CANTONESE: "Cantonese",
        ApplicationLanguage.GERMAN: "German",
        ApplicationLanguage.FRENCH: "French",
        ApplicationLanguage.PORTUGUESE: "Portuguese",
        ApplicationLanguage.SPANISH: "Español",
        ApplicationLanguage.POLISH: "Polish",
    }

    language: ApplicationLanguage
    accepted_names: set[str]

    for language in ApplicationLanguage:
        accepted_names = {
            language.name,
            str(language.value),
            get_language_display_text(language),
            english_aliases[language],
        }
        accepted_names.update(LEGACY_LANGUAGE_ALIASES.get(language, set()))
        if normalized_name in accepted_names:
            return language
        else:
            pass

    return ApplicationLanguage.SYSTEM


def read_saved_language() -> ApplicationLanguage:
    """
    Read the last saved language from the GUI configuration file.

    The read path only inspects the small part of the JSON tree that stores the
    language selection so the startup translation choice can happen before the
    main window is created.

    :returns: Saved application language or ``SYSTEM`` when missing.
    """
    config_path: Path = get_gui_config_file_path()

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file_pointer:
            try:
                json_data: object = json.load(file_pointer)
            except json.decoder.JSONDecodeError:
                return ApplicationLanguage.SYSTEM

        if isinstance(json_data, dict):
            graphics_data: object = json_data.get("graphics", None)
            if isinstance(graphics_data, dict):
                saved_language_name: object = graphics_data.get("language", None)
                if isinstance(saved_language_name, str):
                    return language_from_name(saved_language_name)
                else:
                    return ApplicationLanguage.SYSTEM
            else:
                return ApplicationLanguage.SYSTEM
        else:
            return ApplicationLanguage.SYSTEM
    else:
        return ApplicationLanguage.SYSTEM
