from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import time
import urllib.request
from enum import Enum
from html import escape, unescape
from pathlib import Path

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DeviceType, ResultTypes, SimulationTypes, StudyResultsType


class LocalAiTranslationConfig:
    """
    Local AI translation settings.
    """

    __slots__ = ("base_url", "model_name", "batch_size", "timeout_s")

    def __init__(self, base_url: str, model_name: str, batch_size: int, timeout_s: int) -> None:
        """
        Build the local AI translation settings.

        :param base_url: Local Ollama server base URL.
        :param model_name: Local model name.
        :param batch_size: Maximum source strings per request.
        :param timeout_s: Request timeout in seconds.
        :returns: None.
        """
        self.base_url: str = base_url.rstrip("/")
        self.model_name: str = model_name
        self.batch_size: int = batch_size
        self.timeout_s: int = timeout_s


class PythonTranslationMessageCollector(ast.NodeVisitor):
    """
    Collect literal Qt translation calls from Python GUI source files.
    """

    __slots__ = ("class_contexts", "context_stack", "helper_contexts", "messages")

    def __init__(self, helper_contexts: dict[str, str], class_contexts: dict[str, str]) -> None:
        """
        Build the Python translation message collector.

        :param helper_contexts: Function name to Qt translation context mapping.
        :param class_contexts: Class name to overridden ``tr`` context mapping.
        :returns: None.
        """
        self.helper_contexts: dict[str, str] = helper_contexts
        self.class_contexts: dict[str, str] = class_contexts
        self.context_stack: list[str] = list()
        self.messages: dict[str, set[str]] = dict()

    def _add_message(self, context_name: str, source_text: str) -> None:
        """
        Store one source text in its Qt translation context.

        :param context_name: Qt translation context.
        :param source_text: Source text used by the GUI.
        :returns: Nothing.
        """
        context_messages: set[str] | None = self.messages.get(context_name, None)

        # Contexts group translations exactly as Qt resolves them at runtime.
        if context_messages is None:
            context_messages = set()
            self.messages[context_name] = context_messages
        else:
            pass

        # Empty strings do not need translator work and only add catalog noise.
        if len(source_text) > 0:
            context_messages.add(source_text)
        else:
            pass

    def _get_current_tr_context(self) -> str | None:
        """
        Return the active ``self.tr`` context.

        :returns: Qt translation context or ``None`` outside classes.
        """
        if len(self.context_stack) > 0:
            class_name: str = self.context_stack[-1]
            context_name: str | None = self.class_contexts.get(class_name, None)

            if context_name is None:
                return class_name
            else:
                return context_name
        else:
            return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit one class and use it as the default ``self.tr`` context.

        :param node: Python class definition node.
        :returns: Nothing.
        """
        self.context_stack.append(node.name)

        # The class stack mirrors Qt's default QObject.tr context resolution.
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        """
        Visit one function call and collect supported translation literals.

        :param node: Python call node.
        :returns: Nothing.
        """
        context_name: str | None = None
        source_text: str | None = None
        function_node: ast.expr = node.func
        helper_context: str | None

        # Explicit QCoreApplication.translate-style calls carry their context
        # in the first argument, so they can be added without class inference.
        if isinstance(function_node, ast.Attribute):
            if function_node.attr == "translate" and len(node.args) >= 2:
                context_name = _get_literal_string(node=node.args[0])
                source_text = _get_literal_string(node=node.args[1])
            else:
                if function_node.attr == "tr" and len(node.args) >= 1:
                    context_name = self._get_current_tr_context()
                    source_text = _get_literal_string(node=node.args[0])
                else:
                    pass
        else:
            if isinstance(function_node, ast.Name) and len(node.args) >= 1:
                helper_context = self.helper_contexts.get(function_node.id, None)
                if helper_context is None:
                    pass
                else:
                    context_name = helper_context
                    source_text = _get_literal_string(node=node.args[0])
            else:
                pass

        if context_name is not None and source_text is not None:
            self._add_message(context_name=context_name, source_text=source_text)
        else:
            pass

        # Arguments can contain nested translation calls, so the normal AST
        # traversal still needs to happen after inspecting the current call.
        self.generic_visit(node)


def _find_tool(tool_name: str) -> str:
    """
    Resolve one Qt translation tool from PATH.

    :param tool_name: Executable name.
    :returns: Executable path or the original name.
    """
    resolved_path: str | None = shutil.which(tool_name)
    if resolved_path is None:
        return tool_name
    else:
        return resolved_path


def _run_command(arguments: list[str]) -> None:
    """
    Run one subprocess and fail fast on errors.

    :param arguments: Command arguments.
    :returns: Nothing.
    """
    subprocess.run(arguments, check=True)


def _get_literal_string(node: ast.AST) -> str | None:
    """
    Return a literal string from one AST node.

    :param node: Python AST node.
    :returns: String literal or ``None`` for dynamic expressions.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value
        else:
            return None
    else:
        return None


def _get_translate_context(call_node: ast.Call) -> str | None:
    """
    Return the context from one literal ``translate`` call.

    :param call_node: Python call node.
    :returns: Qt translation context or ``None``.
    """
    function_node: ast.expr = call_node.func

    if isinstance(function_node, ast.Attribute):
        if function_node.attr == "translate" and len(call_node.args) >= 2:
            return _get_literal_string(node=call_node.args[0])
        else:
            return None
    else:
        return None


def _get_function_translate_context(function_node: ast.FunctionDef) -> str | None:
    """
    Return the Qt context wrapped by one helper function.

    :param function_node: Python function definition.
    :returns: Qt translation context or ``None``.
    """
    child_node: ast.AST
    return_node: ast.Return
    context_name: str | None = None

    # Runtime helper wrappers usually return QCoreApplication.translate with a
    # fixed context and a dynamic source_text parameter. Capturing that context
    # lets literal calls to the wrapper land in the same catalog context.
    for child_node in ast.walk(function_node):
        if isinstance(child_node, ast.Return):
            return_node = child_node
            if isinstance(return_node.value, ast.Call):
                context_name = _get_translate_context(call_node=return_node.value)
            else:
                pass
        else:
            pass

    return context_name


def _get_class_tr_context(function_node: ast.FunctionDef, helper_contexts: dict[str, str]) -> str | None:
    """
    Return the Qt context used by one overridden ``tr`` method.

    :param function_node: Python ``tr`` method definition.
    :param helper_contexts: Function name to Qt translation context mapping.
    :returns: Qt translation context or ``None``.
    """
    child_node: ast.AST
    return_node: ast.Return
    call_node: ast.Call
    helper_name: str
    context_name: str | None = None

    # Some dialogs override tr() to route through a generated-UI context such
    # as MainWindow or AboutDialog. Those strings must be cataloged there, not
    # under the Python class name.
    for child_node in ast.walk(function_node):
        if isinstance(child_node, ast.Return):
            return_node = child_node
            if isinstance(return_node.value, ast.Call):
                call_node = return_node.value
                if isinstance(call_node.func, ast.Name):
                    helper_name = call_node.func.id
                    context_name = helper_contexts.get(helper_name, None)
                else:
                    pass
            else:
                pass
        else:
            pass

    return context_name


def _collect_python_helper_contexts(tree: ast.Module) -> dict[str, str]:
    """
    Collect translation helper function contexts from one Python module.

    :param tree: Parsed Python module.
    :returns: Helper function to Qt context mapping.
    """
    helper_contexts: dict[str, str] = dict()
    body_node: ast.stmt
    context_name: str | None

    for body_node in tree.body:
        if isinstance(body_node, ast.FunctionDef):
            context_name = _get_function_translate_context(function_node=body_node)
            if context_name is None:
                pass
            else:
                helper_contexts[body_node.name] = context_name
        else:
            pass

    return helper_contexts


def _collect_python_class_contexts(tree: ast.Module, helper_contexts: dict[str, str]) -> dict[str, str]:
    """
    Collect class-specific ``tr`` override contexts from one Python module.

    :param tree: Parsed Python module.
    :param helper_contexts: Function name to Qt translation context mapping.
    :returns: Class name to Qt context mapping.
    """
    class_contexts: dict[str, str] = dict()
    body_node: ast.stmt
    class_body_node: ast.stmt
    context_name: str | None

    for body_node in tree.body:
        if isinstance(body_node, ast.ClassDef):
            for class_body_node in body_node.body:
                if isinstance(class_body_node, ast.FunctionDef):
                    if class_body_node.name == "tr":
                        context_name = _get_class_tr_context(
                            function_node=class_body_node,
                            helper_contexts=helper_contexts,
                        )
                        if context_name is None:
                            pass
                        else:
                            class_contexts[body_node.name] = context_name
                    else:
                        pass
                else:
                    pass
        else:
            pass

    return class_contexts


def _collect_python_translation_messages(gui_root: Path) -> dict[str, set[str]]:
    """
    Collect literal Python GUI translation messages below the GUI root.

    :param gui_root: GUI package root directory.
    :returns: Qt context to source texts mapping.
    """
    messages: dict[str, set[str]] = dict()
    python_file: Path
    source_code: str
    tree: ast.Module
    helper_contexts: dict[str, str]
    class_contexts: dict[str, str]
    collector: PythonTranslationMessageCollector
    context_name: str
    source_texts: set[str]
    catalog_source_texts: set[str] | None

    for python_file in sorted(gui_root.rglob("*.py")):
        source_code = python_file.read_text(encoding="utf-8")
        tree = ast.parse(source=source_code, filename=str(python_file))
        helper_contexts = _collect_python_helper_contexts(tree=tree)
        class_contexts = _collect_python_class_contexts(tree=tree, helper_contexts=helper_contexts)
        collector = PythonTranslationMessageCollector(
            helper_contexts=helper_contexts,
            class_contexts=class_contexts,
        )
        collector.visit(tree)

        # Merge per-file results so shared UI contexts gather all generated
        # code and runtime Python additions into one catalog context.
        for context_name, source_texts in collector.messages.items():
            catalog_source_texts = messages.get(context_name, None)
            if catalog_source_texts is None:
                messages[context_name] = set(source_texts)
            else:
                catalog_source_texts.update(source_texts)

    return messages


def _get_language_name(locale_code: str) -> str:
    """
    Return the target language name for one shipped VeraGrid catalog.

    :param locale_code: Catalog language suffix.
    :returns: Human-readable target language prompt text.
    """
    language_names: dict[str, str] = dict()

    language_names["ar"] = "Arabic"
    language_names["ca"] = "Catalan"
    language_names["de"] = "German"
    language_names["el"] = "Greek"
    language_names["es"] = "Spanish (Spain)"
    language_names["eu"] = "Basque"
    language_names["fr"] = "French"
    language_names["gl"] = "Galician"
    language_names["hi"] = "Hindi"
    language_names["it"] = "Italian"
    language_names["ja"] = "Japanese"
    language_names["ko"] = "Korean"
    language_names["nl"] = "Dutch"
    language_names["pl"] = "Polish"
    language_names["pt"] = "Portuguese (Portugal)"
    language_names["yue"] = "Cantonese written in Traditional Chinese"
    language_names["zh"] = "Simplified Chinese"

    return language_names.get(locale_code, locale_code)


def _get_translation_source_files(translations_dir: Path) -> list[Path]:
    """
    Return every translation source file stored in the translations directory.

    :param translations_dir: Directory containing ``.ts`` files.
    :returns: Sorted translation source files.
    """
    ts_files: list[Path] = sorted(translations_dir.glob("*.ts"))
    return ts_files


def _get_catalog_locale_code(ts_file: Path) -> str:
    """
    Return the locale suffix from one ``veragrid_xx.ts`` file.

    :param ts_file: Translation source file.
    :returns: Locale suffix.
    """
    stem: str = ts_file.stem
    if stem.startswith("veragrid_"):
        return stem.split("_", 1)[1]
    else:
        return stem


def _escape_ts_text(text: str) -> str:
    """
    Escape one source text for XML ``.ts`` storage.

    :param text: Source text.
    :returns: XML escaped source text.
    """
    return escape(text, quote=False)


def _get_runtime_tree_label_sources() -> list[str]:
    """
    Return every source label used by runtime-built database and results trees.

    :returns: Sorted source labels.
    """
    source_texts: set[str] = set()
    circuit: MultiCircuit = MultiCircuit()
    group_name: str
    enum_classes: list[type[Enum]] = [
        DeviceType,
        ResultTypes,
        SimulationTypes,
        StudyResultsType,
    ]
    enum_class: type[Enum]
    enum_entry: Enum

    source_texts.add("Objects")
    source_texts.add("Results")

    # Database tree group labels come from the circuit template grouping, not from enums.
    for group_name in circuit.get_template_objects_type_dict().keys():
        source_texts.add(str(group_name))

    # Database leaves, result-study rows and result leaves use enum values only for display.
    for enum_class in enum_classes:
        for enum_entry in enum_class:
            source_texts.add(str(enum_entry.value))

    return sorted(source_texts)


def _get_diagram_library_translation_messages() -> dict[str, set[str]]:
    """
    Return runtime-built diagram library labels grouped by their Qt context.

    :returns: Qt context to source texts mapping.
    """
    messages: dict[str, set[str]] = dict()
    schematic_messages: set[str] = set()
    map_messages: set[str] = set()

    # The library models use translated display strings but DeviceType values
    # for drag/drop identity. These labels are runtime-built and must be kept
    # in every catalog even when Qt's source scanner misses them.
    schematic_messages.add("Bus")
    schematic_messages.add("Connectivity bus")
    schematic_messages.add("3W-Transformer")
    schematic_messages.add("NW-Transformer")
    schematic_messages.add("Fluid-node")
    schematic_messages.add("VSC")
    schematic_messages.add("Drag & drop {name} into the schematic")

    map_messages.add("Substation")
    map_messages.add("Drag & drop {name} into the schematic")

    messages["SchematicLibraryModel"] = schematic_messages
    messages["MapLibraryModel"] = map_messages

    return messages


def _build_unfinished_ts_message(source_text: str) -> str:
    """
    Build one untranslated Qt Linguist message block.

    :param source_text: Source text.
    :returns: Message XML block.
    """
    escaped_source_text: str = _escape_ts_text(text=source_text)
    return (
        "    <message>\n"
        f"        <source>{escaped_source_text}</source>\n"
        '        <translation type="unfinished"></translation>\n'
        "    </message>\n"
    )


def _collect_context_source_texts(context_block: str) -> set[str]:
    """
    Collect source texts already present in one Qt Linguist context block.

    :param context_block: Full context XML block.
    :returns: Source texts found in the block.
    """
    source_texts: set[str] = set()
    match: re.Match[str]

    for match in re.finditer(r"<source>(.*?)</source>", context_block, flags=re.DOTALL):
        source_texts.add(unescape(match.group(1)))

    return source_texts


def _reactivate_context_source_texts(context_block: str, source_texts: set[str]) -> str:
    """
    Reactivate required source messages inside one Qt Linguist context block.

    :param context_block: Full context XML block.
    :param source_texts: Source texts that are still used by VeraGrid.
    :returns: Patched context XML block.
    """
    updated_parts: list[str] = list()
    last_index: int = 0
    message_match: re.Match[str]
    message: str
    source_match: re.Match[str] | None
    source_text: str
    updated_message: str

    for message_match in re.finditer(r"<message>.*?</message>", context_block, flags=re.DOTALL):
        message = message_match.group(0)
        source_match = re.search(r"<source>(.*?)</source>", message, flags=re.DOTALL)

        if source_match is not None:
            source_text = unescape(source_match.group(1))
            if source_text in source_texts:
                updated_message = message.replace('<translation type="vanished">', "<translation>")
                updated_message = re.sub(
                    r'<translation type="unfinished">([^<]+)</translation>',
                    r"<translation>\1</translation>",
                    updated_message,
                )
            else:
                updated_message = message
        else:
            updated_message = message

        updated_parts.append(context_block[last_index:message_match.start()])
        updated_parts.append(updated_message)
        last_index = message_match.end()

    updated_parts.append(context_block[last_index:])
    return "".join(updated_parts)


def _sync_context_source_texts(ts_file: Path, context_name: str, source_texts: list[str]) -> None:
    """
    Ensure one Qt Linguist context contains and activates the required sources.

    :param ts_file: Translation source file to patch.
    :param context_name: Qt translation context name.
    :param source_texts: Required source texts.
    :returns: Nothing.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    context_pattern: str = rf"(<context>\s*<name>{re.escape(context_name)}</name>)(.*?)(</context>)"
    context_match: re.Match[str] | None = re.search(context_pattern, contents, flags=re.DOTALL)
    missing_messages: list[str] = list()
    source_text: str
    source_text_set: set[str] = set(source_texts)
    existing_source_texts: set[str]
    context_block: str
    updated_context_block: str

    if context_match is None:
        for source_text in source_texts:
            missing_messages.append(_build_unfinished_ts_message(source_text=source_text))

        context_block = (
            "<context>\n"
            f"    <name>{context_name}</name>\n"
            + "".join(missing_messages)
            + "</context>\n"
        )
        contents = contents.replace("</TS>\n", context_block + "</TS>\n")
    else:
        context_block = context_match.group(0)
        updated_context_block = _reactivate_context_source_texts(
            context_block=context_block,
            source_texts=source_text_set,
        )
        existing_source_texts = _collect_context_source_texts(context_block=updated_context_block)

        for source_text in source_texts:
            if source_text in existing_source_texts:
                pass
            else:
                missing_messages.append(_build_unfinished_ts_message(source_text=source_text))

        if len(missing_messages) > 0:
            updated_context_block = (
                updated_context_block[:updated_context_block.rfind("</context>")]
                + "".join(missing_messages)
                + "</context>"
            )
        else:
            pass

        contents = (
            contents[:context_match.start()]
            + updated_context_block
            + contents[context_match.end():]
        )

    ts_file.write_text(contents, encoding="utf-8")


def _collect_finished_translation_memory(ts_file: Path) -> dict[str, str]:
    """
    Collect finished translations by source text from one catalog.

    :param ts_file: Translation source file.
    :returns: Finished source-to-translation memory.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    memory: dict[str, str] = dict()
    message_match: re.Match[str]

    for message_match in re.finditer(r"<message>.*?</message>", contents, flags=re.DOTALL):
        message: str = message_match.group(0)
        source_match: re.Match[str] | None = re.search(r"<source>(.*?)</source>", message, flags=re.DOTALL)
        translation_match: re.Match[str] | None = re.search(
            r"<translation(?: type=\"([^\"]+)\")?>(.*?)</translation>",
            message,
            flags=re.DOTALL,
        )

        if source_match is not None and translation_match is not None:
            translation_type: str = translation_match.group(1) if translation_match.group(1) is not None else ""
            translated_text: str = unescape(translation_match.group(2))
            source_text: str = unescape(source_match.group(1))

            if len(translated_text) > 0 and translation_type not in {"unfinished", "vanished", "obsolete"}:
                if source_text in memory:
                    pass
                else:
                    memory[source_text] = translated_text
            else:
                pass
        else:
            pass

    return memory


def _collect_empty_unfinished_sources(ts_file: Path) -> list[str]:
    """
    Collect source texts with empty unfinished translations.

    :param ts_file: Translation source file.
    :returns: Unique source texts still needing translation.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    source_texts: list[str] = list()
    seen_texts: set[str] = set()
    message_match: re.Match[str]

    for message_match in re.finditer(r"<message>.*?</message>", contents, flags=re.DOTALL):
        message: str = message_match.group(0)
        source_match: re.Match[str] | None = re.search(r"<source>(.*?)</source>", message, flags=re.DOTALL)
        translation_match: re.Match[str] | None = re.search(
            r"<translation type=\"unfinished\"></translation>",
            message,
        )

        if source_match is not None and translation_match is not None:
            source_text: str = unescape(source_match.group(1))
            if source_text in seen_texts:
                pass
            else:
                seen_texts.add(source_text)
                source_texts.append(source_text)
        else:
            pass

    return source_texts


def _replace_empty_unfinished_translations(ts_file: Path, translations: dict[str, str]) -> int:
    """
    Replace empty unfinished translations with provided translated text.

    :param ts_file: Translation source file.
    :param translations: Source-to-translation mapping.
    :returns: Number of rewritten messages.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    updated_parts: list[str] = list()
    replaced_count: int = 0
    last_index: int = 0
    message_match: re.Match[str]
    message: str
    source_match: re.Match[str] | None
    translation_match: re.Match[str] | None
    source_text: str
    translated_text: str | None
    updated_message: str

    for message_match in re.finditer(r"<message>.*?</message>", contents, flags=re.DOTALL):
        message = message_match.group(0)
        source_match = re.search(r"<source>(.*?)</source>", message, flags=re.DOTALL)
        translation_match = re.search(
            r"<translation type=\"unfinished\"></translation>",
            message,
        )

        if source_match is not None and translation_match is not None:
            source_text = unescape(source_match.group(1))
            translated_text = translations.get(source_text, None)

            if translated_text is not None:
                replaced_count += 1
                updated_message = (
                    message[:translation_match.start()]
                    + f"<translation>{_escape_ts_text(translated_text)}</translation>"
                    + message[translation_match.end():]
                )
            else:
                updated_message = message
        else:
            updated_message = message

        updated_parts.append(contents[last_index:message_match.start()])
        updated_parts.append(updated_message)
        last_index = message_match.end()

    updated_parts.append(contents[last_index:])

    if replaced_count > 0:
        ts_file.write_text("".join(updated_parts), encoding="utf-8")
    else:
        pass

    return replaced_count


def _finish_non_empty_unfinished_translations(ts_file: Path) -> int:
    """
    Mark unfinished translations with non-empty text as finished.

    ``lupdate`` and Qt Linguist same-text heuristics can leave useful text as
    ``type="unfinished"``. The local-AI pass owns those entries after it has
    filled the empty ones, so this function removes the marker before
    ``lrelease`` compiles the catalog.

    :param ts_file: Translation source file.
    :returns: Number of messages marked as finished.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    updated_parts: list[str] = list()
    replaced_count: int = 0
    last_index: int = 0
    message_match: re.Match[str]
    message: str
    translation_match: re.Match[str] | None
    translated_text: str
    updated_message: str

    for message_match in re.finditer(r"<message>.*?</message>", contents, flags=re.DOTALL):
        message = message_match.group(0)
        translation_match = re.search(
            r"<translation type=\"unfinished\">(.*?)</translation>",
            message,
            flags=re.DOTALL,
        )

        if translation_match is not None:
            translated_text = translation_match.group(1)
            if len(translated_text) > 0:
                replaced_count += 1
                updated_message = (
                    message[:translation_match.start()]
                    + f"<translation>{translated_text}</translation>"
                    + message[translation_match.end():]
                )
            else:
                updated_message = message
        else:
            updated_message = message

        updated_parts.append(contents[last_index:message_match.start()])
        updated_parts.append(updated_message)
        last_index = message_match.end()

    updated_parts.append(contents[last_index:])

    if replaced_count > 0:
        ts_file.write_text("".join(updated_parts), encoding="utf-8")
    else:
        pass

    return replaced_count


def _parse_json_object(text: str) -> dict[str, object]:
    """
    Parse one JSON object, tolerating provider text around it.

    :param text: Provider response text.
    :returns: Parsed JSON object or an empty dictionary.
    """
    parsed_data: object
    start_index: int
    end_index: int

    try:
        parsed_data = json.loads(text)
    except json.JSONDecodeError:
        start_index = text.find("{")
        end_index = text.rfind("}")

        if start_index >= 0 and end_index > start_index:
            parsed_data = json.loads(text[start_index:end_index + 1])
        else:
            parsed_data = dict()

    if isinstance(parsed_data, dict):
        return parsed_data
    else:
        return dict()


def _request_local_ai_translations(
    config: LocalAiTranslationConfig,
    target_language: str,
    source_texts: list[str],
) -> dict[str, str]:
    """
    Translate one batch of source strings with the local Ollama API.

    :param config: Local AI translation settings.
    :param target_language: Target language prompt text.
    :param source_texts: Exact source texts to translate.
    :returns: Source-to-translation mapping.
    """
    prompt: str = (
        f"Target language: {target_language}.\n"
        "Translate these Qt GUI labels/tooltips for an electrical power-grid simulation application.\n"
        "Return only one valid JSON object mapping each exact source string to its translated string.\n"
        "Preserve HTML tags/entities, keyboard shortcuts, variable symbols, Greek letters, units, acronyms, "
        "punctuation, emojis, placeholders, and quoted from/to words.\n"
        "For shortcuts such as Ctrl+Shift++, return the same shortcut unchanged.\n"
        f"Sources JSON array:\n{json.dumps(source_texts, ensure_ascii=False)}"
    )
    payload: dict[str, object] = dict()
    message_items: list[dict[str, str]] = list()
    request: urllib.request.Request
    response_payload: dict[str, object]
    response_message: object | None
    response_content: str
    parsed_translations: dict[str, object]
    translations: dict[str, str] = dict()
    source_text: str
    translated_value: object | None

    message_items.append(
        {
            "role": "system",
            "content": "Return only valid JSON. No markdown, no comments.",
        }
    )
    message_items.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload["model"] = config.model_name
    payload["messages"] = message_items
    payload["format"] = "json"
    payload["stream"] = False
    payload["options"] = {"temperature": 0.0}

    request = urllib.request.Request(
        url=f"{config.base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=config.timeout_s) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    response_message = response_payload.get("message", None)
    if isinstance(response_message, dict):
        response_content = str(response_message.get("content", ""))
    else:
        response_content = ""

    parsed_translations = _parse_json_object(response_content)

    for source_text in source_texts:
        translated_value = parsed_translations.get(source_text, None)
        if isinstance(translated_value, str) and len(translated_value.strip()) > 0:
            translations[source_text] = translated_value.strip()
        else:
            translations[source_text] = source_text

    return translations


def _request_local_ai_single_translation(
    config: LocalAiTranslationConfig,
    target_language: str,
    source_text: str,
) -> str | None:
    """
    Translate one source string with a plain-text local AI request.

    This is the last fallback for long HTML-rich entries where JSON mode can
    fail because of escaping. The model is asked for the translated text only.

    :param config: Local AI translation settings.
    :param target_language: Target language prompt text.
    :param source_text: Source text to translate.
    :returns: Translated text, or ``None`` when no usable text was returned.
    """
    prompt: str = (
        f"Translate this Qt GUI text to {target_language}.\n"
        "Return only the translated text. No markdown, no explanation.\n"
        "Preserve all HTML tags, attributes, entities, keyboard shortcuts, package names, license identifiers, "
        "symbols, placeholders, and table layout. Translate only human-readable prose.\n"
        f"Source text:\n{source_text}"
    )
    payload: dict[str, object] = dict()
    message_items: list[dict[str, str]] = list()
    request: urllib.request.Request
    response_payload: dict[str, object]
    response_message: object | None
    response_content: str

    message_items.append(
        {
            "role": "system",
            "content": "Return only the translated text.",
        }
    )
    message_items.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload["model"] = config.model_name
    payload["messages"] = message_items
    payload["stream"] = False
    payload["options"] = {"temperature": 0.0}

    request = urllib.request.Request(
        url=f"{config.base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=config.timeout_s) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    response_message = response_payload.get("message", None)
    if isinstance(response_message, dict):
        response_content = str(response_message.get("content", "")).strip()
    else:
        response_content = ""

    if len(response_content) > 0 and response_content != source_text:
        return response_content
    else:
        return None


def _translate_batch_with_split(
    config: LocalAiTranslationConfig,
    target_language: str,
    source_texts: list[str],
) -> dict[str, str]:
    """
    Translate a batch, splitting recursively when the local model returns invalid JSON.

    :param config: Local AI translation settings.
    :param target_language: Target language prompt text.
    :param source_texts: Source texts to translate.
    :returns: Source-to-translation mapping.
    """
    translations: dict[str, str]
    middle_index: int

    try:
        translations = _request_local_ai_translations(
            config=config,
            target_language=target_language,
            source_texts=source_texts,
        )
    except Exception as exc:
        print(f"  split {len(source_texts)} after {type(exc).__name__}: {exc}", flush=True)

        if len(source_texts) <= 1:
            translated_text: str | None = _request_local_ai_single_translation(
                config=config,
                target_language=target_language,
                source_text=source_texts[0],
            )
            if translated_text is None:
                translations = dict()
            else:
                translations = {source_texts[0]: translated_text}
        else:
            middle_index = len(source_texts) // 2
            translations = _translate_batch_with_split(
                config=config,
                target_language=target_language,
                source_texts=source_texts[:middle_index],
            )
            translations.update(
                _translate_batch_with_split(
                    config=config,
                    target_language=target_language,
                    source_texts=source_texts[middle_index:],
                )
            )

    return translations


def _translate_missing_catalog_entries(ts_files: list[Path], config: LocalAiTranslationConfig) -> None:
    """
    Fill empty unfinished translations using translation memory and local AI.

    Existing finished translations are never overwritten. The AI is only asked
    for strings that remain ``<translation type="unfinished"></translation>``
    after Qt Linguist has updated the catalogs.

    :param ts_files: Translation source files.
    :param config: Local AI translation settings.
    :returns: Nothing.
    """
    ts_file: Path
    source_texts: list[str]
    memory: dict[str, str]
    memory_translations: dict[str, str]
    ai_source_texts: list[str]
    source_text: str
    translated_text: str | None
    locale_code: str
    target_language: str
    start_time: float
    start_index: int
    batch_source_texts: list[str]
    batch_translations: dict[str, str]
    copied_count: int
    replaced_count: int

    for ts_file in ts_files:
        source_texts = _collect_empty_unfinished_sources(ts_file=ts_file)
        memory = _collect_finished_translation_memory(ts_file=ts_file)
        memory_translations = dict()
        ai_source_texts = list()

        for source_text in source_texts:
            translated_text = memory.get(source_text, None)
            if translated_text is None:
                ai_source_texts.append(source_text)
            else:
                memory_translations[source_text] = translated_text

        copied_count = _replace_empty_unfinished_translations(
            ts_file=ts_file,
            translations=memory_translations,
        )

        locale_code = _get_catalog_locale_code(ts_file=ts_file)
        target_language = _get_language_name(locale_code=locale_code)
        print(
            f"{ts_file.name}: copied {copied_count}, local AI {len(ai_source_texts)} -> {target_language}",
            flush=True,
        )

        start_time = time.time()
        for start_index in range(0, len(ai_source_texts), config.batch_size):
            batch_source_texts = ai_source_texts[start_index:start_index + config.batch_size]
            batch_translations = _translate_batch_with_split(
                config=config,
                target_language=target_language,
                source_texts=batch_source_texts,
            )
            replaced_count = _replace_empty_unfinished_translations(
                ts_file=ts_file,
                translations=batch_translations,
            )
            print(
                f"  {start_index + len(batch_source_texts)}/{len(ai_source_texts)} wrote {replaced_count}",
                flush=True,
            )

        replaced_count = _finish_non_empty_unfinished_translations(ts_file=ts_file)
        print(
            f"{ts_file.name}: marked {replaced_count} non-empty unfinished translations as finished",
            flush=True,
        )
        print(f"{ts_file.name}: translation pass done in {time.time() - start_time:.1f}s", flush=True)


def _sync_tree_label_context(ts_file: Path, source_texts: list[str]) -> None:
    """
    Ensure the manual runtime tree-label context contains every enum label.

    :param ts_file: Translation source file to patch.
    :param source_texts: Required tree-label source texts.
    :returns: Nothing.
    """
    _sync_context_source_texts(
        ts_file=ts_file,
        context_name="VeraGridTreeLabels",
        source_texts=source_texts,
    )


def _sync_python_translation_contexts(ts_file: Path, messages: dict[str, set[str]]) -> None:
    """
    Ensure Python-extracted messages are present in one translation file.

    :param ts_file: Translation source file to patch.
    :param messages: Qt context to source texts mapping.
    :returns: Nothing.
    """
    context_name: str
    source_texts: set[str]

    for context_name, source_texts in sorted(messages.items()):
        _sync_context_source_texts(
            ts_file=ts_file,
            context_name=context_name,
            source_texts=sorted(source_texts),
        )


def _reactivate_manual_context_translations(ts_file: Path) -> None:
    """
    Restore manual translation contexts after ``lupdate`` marks them vanished.

    :param ts_file: Translation source file to patch.
    :returns: Nothing.
    """
    contents: str = ts_file.read_text(encoding="utf-8")
    updated_contents: str = contents

    for context_name in ["ContextMenu", "ConfigurationMain", "messages", "SimulationsMain", "VeraGridTreeLabels"]:
        context_pattern: str = rf"(<context>\s*<name>{context_name}</name>.*?</context>)"

        def reactivate_context_block(context_match: re.Match[str]) -> str:
            """
            Remove ``vanished`` and selected ``unfinished`` markers from one runtime context block.

            :param context_match: Regex match containing one whole TS context block.
            :returns: Patched TS context block.
            """
            context_block: str = context_match.group(1)
            reactivated_block: str = context_block.replace(
                '<translation type="vanished">',
                "<translation>",
            )
            reactivated_block = re.sub(
                r'<translation type="unfinished">([^<]+)</translation>',
                r"<translation>\1</translation>",
                reactivated_block,
            )
            return reactivated_block

        updated_contents = re.sub(
            context_pattern,
            reactivate_context_block,
            updated_contents,
            flags=re.DOTALL,
        )

    if updated_contents == contents:
        return
    else:
        pass

    # Only the manual runtime contexts are rewritten so translator-managed
    # formatting outside those catalogs remains untouched.
    ts_file.write_text(updated_contents, encoding="utf-8")


def update_translations(ai_config: LocalAiTranslationConfig | None = None) -> None:
    """
    Refresh every application ``.ts`` file and compile matching ``.qm`` outputs.

    :param ai_config: Local AI translation settings.
    :returns: Nothing.
    """
    gui_root: Path = Path(__file__).resolve().parent
    translations_dir: Path = gui_root / "translations"
    ts_files: list[Path]
    tree_label_sources: list[str] = _get_runtime_tree_label_sources()
    python_messages: dict[str, set[str]]
    diagram_library_messages: dict[str, set[str]]
    context_name: str
    source_texts: set[str]
    catalog_source_texts: set[str] | None

    translations_dir.mkdir(parents=True, exist_ok=True)
    ts_files = _get_translation_source_files(translations_dir=translations_dir)

    if len(ts_files) == 0:
        return
    else:
        pass

    python_messages = _collect_python_translation_messages(gui_root=gui_root)
    diagram_library_messages = _get_diagram_library_translation_messages()

    for context_name, source_texts in diagram_library_messages.items():
        catalog_source_texts = python_messages.get(context_name, None)
        if catalog_source_texts is None:
            python_messages[context_name] = set(source_texts)
        else:
            catalog_source_texts.update(source_texts)

    # Update all catalogs in one lupdate pass so every translation file sees the same source tree.
    _run_command(
        list(
            [
            _find_tool("pyside6-lupdate"),
            str(gui_root),
            "-ts",
            ]
        ) + [str(ts_file) for ts_file in ts_files]
    )

    ts_file: Path
    for ts_file in ts_files:
        _reactivate_manual_context_translations(ts_file=ts_file)
        _sync_python_translation_contexts(ts_file=ts_file, messages=python_messages)
        _sync_tree_label_context(ts_file=ts_file, source_texts=tree_label_sources)

    if ai_config is None:
        ai_config = LocalAiTranslationConfig(
            base_url="http://127.0.0.1:11434",
            model_name="gemma4:e4b",
            batch_size=50,
            timeout_s=600,
        )
    else:
        pass

    _translate_missing_catalog_entries(ts_files=ts_files, config=ai_config)

    # Compile each catalog to the qm file with the same stem in the same folder.
    for ts_file in ts_files:
        qm_file: Path = ts_file.with_suffix(".qm")
        _run_command(
            [
                _find_tool("pyside6-lrelease"),
                str(ts_file),
                "-qm",
                str(qm_file),
            ]
        )


def main() -> None:
    """
    Run the complete translation update pipeline.

    :returns: Nothing.
    """
    update_translations()


if __name__ == "__main__":
    main()
