# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Generate packaged AI knowledge assets for VeraGrid.

This script converts selected repository sources into markdown knowledge files
that ship with the AI agent. The generated files are written under
``VeraGrid/Gui/AiAgent/knowledge`` so the retrieval layer can load them through
package resources in production builds.
"""

from __future__ import annotations

import ast
import os
import re
import xml.etree.ElementTree as ET
from typing import Optional


class KnowledgeAsset:
    """
    One generated markdown knowledge asset.

    :param output_name: Output filename relative to the knowledge directory.
    :param content: Markdown content to write.
    """

    __slots__ = (
        "output_name",
        "content",
    )

    def __init__(self, output_name: str, content: str) -> None:
        """
        Store the generated asset payload.

        :param output_name: Output filename relative to the knowledge directory.
        :param content: Markdown content to write.
        """
        self.output_name: str = output_name
        self.content: str = content


def build_repository_root() -> str:
    """
    Locate the repository root from this script location.

    :returns: Absolute repository root path.
    """
    script_dir: str = os.path.abspath(os.path.dirname(__file__))
    repository_root: str = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    return repository_root


def build_knowledge_directory(repository_root: str) -> str:
    """
    Build the packaged knowledge directory path.

    :param repository_root: Repository root path.
    :returns: Absolute knowledge directory path.
    """
    knowledge_directory: str = os.path.join(
        repository_root,
        "src",
        "VeraGrid",
        "Gui",
        "AiAgent",
        "knowledge",
    )
    return knowledge_directory


def normalize_generated_filename(prefix: str, relative_path: str) -> str:
    """
    Build a filesystem-safe generated filename for one source path.

    :param prefix: Filename prefix.
    :param relative_path: Source path relative to the repository root.
    :returns: Generated markdown filename.
    """
    normalized_name: str = relative_path.replace(os.sep, "__")
    normalized_name = normalized_name.replace("/", "__")
    normalized_name = re.sub(r"[^A-Za-z0-9_\.]+", "_", normalized_name)
    normalized_name = normalized_name.replace(".", "_")
    return f"{prefix}__{normalized_name}.md"


def read_text_file(path: str) -> str:
    """
    Read one UTF-8 text file.

    :param path: Absolute file path.
    :returns: File text.
    """
    with open(path, "r", encoding="utf-8") as file_pointer:
        return file_pointer.read()


def write_text_file(path: str, content: str) -> None:
    """
    Write one UTF-8 text file.

    :param path: Absolute file path.
    :param content: File text.
    :returns: Nothing.
    """
    with open(path, "w", encoding="utf-8") as file_pointer:
        file_pointer.write(content)


def list_markdown_document_paths(repository_root: str) -> list[str]:
    """
    List source markdown documents to package for static RAG.

    :param repository_root: Repository root path.
    :returns: Absolute markdown source paths.
    """
    source_directory: str = os.path.join(repository_root, "doc", "md_source")
    collected_paths: list[str] = list()

    for root_path, _, file_names in os.walk(source_directory):
        for file_name in sorted(file_names):
            if file_name.endswith(".md"):
                collected_paths.append(os.path.join(root_path, file_name))
            else:
                pass

    collected_paths.sort()
    return collected_paths


def list_gui_main_source_paths(repository_root: str) -> list[str]:
    """
    List ``Gui/Main`` sources to package for static RAG.

    :param repository_root: Repository root path.
    :returns: Absolute GUI/Main source paths.
    """
    source_directory: str = os.path.join(repository_root, "src", "VeraGrid", "Gui", "Main")
    collected_paths: list[str] = list()

    for root_path, _, file_names in os.walk(source_directory):
        for file_name in sorted(file_names):
            if file_name.endswith(".py"):
                collected_paths.append(os.path.join(root_path, file_name))
            else:
                if file_name.endswith(".ui"):
                    collected_paths.append(os.path.join(root_path, file_name))
                else:
                    if file_name.endswith(".txt"):
                        collected_paths.append(os.path.join(root_path, file_name))
                    else:
                        pass

    collected_paths.sort()
    return collected_paths


def list_veragrid_engine_source_paths(repository_root: str) -> list[str]:
    """
    List ``src/VeraGridEngine`` sources to package for static RAG.

    :param repository_root: Repository root path.
    :returns: Absolute VeraGridEngine source paths.
    """
    source_directory: str = os.path.join(repository_root, "src", "VeraGridEngine")
    collected_paths: list[str] = list()

    for root_path, _, file_names in os.walk(source_directory):
        for file_name in sorted(file_names):
            if file_name.endswith(".py"):
                collected_paths.append(os.path.join(root_path, file_name))
            else:
                if file_name.endswith(".md"):
                    collected_paths.append(os.path.join(root_path, file_name))
                else:
                    if file_name.endswith(".txt"):
                        collected_paths.append(os.path.join(root_path, file_name))
                    else:
                        pass

    collected_paths.sort()
    return collected_paths


def make_relative_repository_path(repository_root: str, source_path: str) -> str:
    """
    Build a repository-relative path for one source file.

    :param repository_root: Repository root path.
    :param source_path: Absolute source path.
    :returns: Repository-relative path.
    """
    relative_path: str = os.path.relpath(source_path, repository_root)
    return relative_path.replace(os.sep, "/")


def normalize_markdown_source_text(source_text: str) -> str:
    """
    Normalize one markdown document for packaged retrieval.

    :param source_text: Raw markdown text.
    :returns: Normalized markdown text.
    """
    normalized_lines: list[str] = list()
    lines: list[str] = source_text.splitlines()
    index: int = 0

    while index < len(lines):
        line_text: str = lines[index]

        # Remove noisy image references because they help the docs visually but
        # add low-signal tokens to retrieval.
        if line_text.lstrip().startswith("!["):
            pass
        else:
            normalized_lines.append(line_text.rstrip())

        index += 1

    normalized_text: str = "\n".join(normalized_lines).strip()
    return normalized_text + "\n"


def summarize_doc_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a VeraGrid markdown document.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_doc", relative_path)
    source_text: str = read_text_file(source_path)
    normalized_text: str = normalize_markdown_source_text(source_text)
    title_text: str = os.path.splitext(os.path.basename(source_path))[0].replace("_", " ").strip().title()
    content_lines: list[str] = list()

    content_lines.append(f"# Official VeraGrid Doc: {title_text}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: official documentation")
    content_lines.append("")
    content_lines.append("## Document Content")
    content_lines.append("")
    content_lines.append(normalized_text.rstrip())
    content_lines.append("")

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def extract_docstring_summary(docstring_text: Optional[str]) -> str:
    """
    Extract the first meaningful line from a docstring.

    :param docstring_text: Raw docstring text.
    :returns: Summary line.
    """
    if docstring_text is None:
        return "No docstring provided."
    else:
        pass

    lines: list[str] = docstring_text.strip().splitlines()
    index: int = 0

    while index < len(lines):
        stripped_text: str = lines[index].strip()
        if len(stripped_text) > 0:
            return stripped_text
        else:
            pass
        index += 1

    return "No docstring provided."


def build_argument_signature(arguments: ast.arguments) -> str:
    """
    Build a compact signature string from AST arguments.

    :param arguments: AST arguments object.
    :returns: Signature text.
    """
    parts: list[str] = list()
    positional_arguments: list[ast.arg] = list(arguments.posonlyargs) + list(arguments.args)
    index: int = 0

    while index < len(positional_arguments):
        parts.append(positional_arguments[index].arg)
        index += 1

    if arguments.vararg is None:
        pass
    else:
        parts.append("*" + arguments.vararg.arg)

    index = 0
    while index < len(arguments.kwonlyargs):
        parts.append(arguments.kwonlyargs[index].arg)
        index += 1

    if arguments.kwarg is None:
        pass
    else:
        parts.append("**" + arguments.kwarg.arg)

    return ", ".join(parts)


def build_function_heading(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """
    Build a readable heading for one function or method.

    :param function_node: AST function node.
    :returns: Heading text.
    """
    signature_text: str = build_argument_signature(function_node.args)
    return f"{function_node.name}({signature_text})"


def build_class_method_lines(class_node: ast.ClassDef) -> list[str]:
    """
    Build markdown bullet lines for one class method list.

    :param class_node: AST class node.
    :returns: Markdown bullet lines.
    """
    lines: list[str] = list()

    for child_node in class_node.body:
        if isinstance(child_node, ast.FunctionDef) or isinstance(child_node, ast.AsyncFunctionDef):
            if child_node.name.startswith("__") and child_node.name.endswith("__"):
                pass
            else:
                method_summary: str = extract_docstring_summary(ast.get_docstring(child_node))
                lines.append(f"- `{build_function_heading(child_node)}`")
                lines.append(f"  Summary: {method_summary}")
        else:
            pass

    if len(lines) == 0:
        lines.append("- No methods detected.")
    else:
        pass

    return lines


def build_base_class_names(class_node: ast.ClassDef) -> list[str]:
    """
    Build readable base-class names for one AST class.

    :param class_node: AST class node.
    :returns: Base-class name list.
    """
    base_names: list[str] = list()

    for base_node in class_node.bases:
        if isinstance(base_node, ast.Name):
            base_names.append(base_node.id)
        else:
            if isinstance(base_node, ast.Attribute):
                attribute_parts: list[str] = list()
                current_node: ast.AST = base_node

                while isinstance(current_node, ast.Attribute):
                    attribute_parts.append(current_node.attr)
                    current_node = current_node.value

                if isinstance(current_node, ast.Name):
                    attribute_parts.append(current_node.id)
                else:
                    pass

                attribute_parts.reverse()
                base_names.append(".".join(attribute_parts))
            else:
                base_names.append(ast.unparse(base_node))

    return base_names


def summarize_python_module_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a Python module.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_gui_main", relative_path)
    module_text: str = read_text_file(source_path)
    module_ast: ast.Module = ast.parse(module_text)
    module_docstring: Optional[str] = ast.get_docstring(module_ast)
    content_lines: list[str] = list()
    class_count: int = 0
    function_count: int = 0

    content_lines.append(f"# VeraGrid GUI Main Module: {relative_path}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated GUI/Main code summary")
    content_lines.append("")
    content_lines.append("## Module Summary")
    content_lines.append("")
    content_lines.append(extract_docstring_summary(module_docstring))
    content_lines.append("")

    for node in module_ast.body:
        if isinstance(node, ast.ClassDef):
            class_count += 1
        else:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                function_count += 1
            else:
                pass

    content_lines.append("## Module Surface")
    content_lines.append("")
    content_lines.append(f"- Class count: {class_count}")
    content_lines.append(f"- Top-level function count: {function_count}")
    content_lines.append("")

    for node in module_ast.body:
        if isinstance(node, ast.ClassDef):
            base_names: list[str] = build_base_class_names(node)
            content_lines.append(f"## Class: {node.name}")
            content_lines.append("")

            if len(base_names) > 0:
                content_lines.append("- Bases: " + ", ".join(base_names))
            else:
                content_lines.append("- Bases: none")

            content_lines.append("- Summary: " + extract_docstring_summary(ast.get_docstring(node)))
            content_lines.append("")
            content_lines.append("### Methods")
            content_lines.append("")
            content_lines.extend(build_class_method_lines(node))
            content_lines.append("")
        else:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                content_lines.append(f"## Function: {build_function_heading(node)}")
                content_lines.append("")
                content_lines.append(extract_docstring_summary(ast.get_docstring(node)))
                content_lines.append("")
            else:
                pass

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def summarize_ui_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a Qt Designer ``.ui`` file.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_gui_main", relative_path)
    source_text: str = read_text_file(source_path)
    root_element: ET.Element = ET.fromstring(source_text)
    class_name_element: Optional[ET.Element] = root_element.find("class")
    widget_element: Optional[ET.Element] = root_element.find("widget")
    action_names: list[str] = list()
    widget_names: list[str] = list()
    menu_names: list[str] = list()
    content_lines: list[str] = list()

    for element in root_element.iter():
        element_tag: str = str(element.tag)

        if element_tag == "action":
            action_name: str = str(element.attrib.get("name", "")).strip()
            if len(action_name) > 0:
                action_names.append(action_name)
            else:
                pass
        else:
            if element_tag == "widget":
                widget_name: str = str(element.attrib.get("name", "")).strip()
                widget_class_name: str = str(element.attrib.get("class", "")).strip()
                if len(widget_name) > 0:
                    widget_names.append(f"{widget_class_name}:{widget_name}")
                else:
                    pass
            else:
                if element_tag == "addaction":
                    menu_name: str = str(element.attrib.get("name", "")).strip()
                    if len(menu_name) > 0:
                        menu_names.append(menu_name)
                    else:
                        pass
                else:
                    pass

    content_lines.append(f"# VeraGrid GUI Main UI: {relative_path}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated Qt Designer UI summary")
    content_lines.append("")
    content_lines.append("## UI Summary")
    content_lines.append("")

    if class_name_element is None:
        content_lines.append("- Form class: unknown")
    else:
        content_lines.append(f"- Form class: {str(class_name_element.text).strip()}")

    if widget_element is None:
        content_lines.append("- Root widget: unknown")
    else:
        content_lines.append(
            "- Root widget: "
            + str(widget_element.attrib.get("class", "")).strip()
            + ":"
            + str(widget_element.attrib.get("name", "")).strip()
        )

    content_lines.append(f"- Declared widget count: {len(widget_names)}")
    content_lines.append(f"- Declared action count: {len(action_names)}")
    content_lines.append("")

    content_lines.append("## Representative Widgets")
    content_lines.append("")
    if len(widget_names) == 0:
        content_lines.append("- No widgets detected.")
    else:
        index: int = 0

        while index < min(len(widget_names), 120):
            content_lines.append(f"- {widget_names[index]}")
            index += 1

    content_lines.append("")
    content_lines.append("## Actions And Menus")
    content_lines.append("")

    if len(action_names) == 0 and len(menu_names) == 0:
        content_lines.append("- No actions detected.")
    else:
        index = 0
        while index < min(len(action_names), 120):
            content_lines.append(f"- action: {action_names[index]}")
            index += 1

        index = 0
        while index < min(len(menu_names), 120):
            content_lines.append(f"- menu/action reference: {menu_names[index]}")
            index += 1

    content_lines.append("")
    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def summarize_plain_text_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a plain text file.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_gui_main", relative_path)
    source_text: str = read_text_file(source_path).strip()
    content_lines: list[str] = list()

    content_lines.append(f"# VeraGrid GUI Main Text Resource: {relative_path}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated plain text resource summary")
    content_lines.append("")
    content_lines.append("## Resource Content")
    content_lines.append("")
    content_lines.append(source_text)
    content_lines.append("")

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def summarize_engine_markdown_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a VeraGridEngine markdown document.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_engine", relative_path)
    source_text: str = read_text_file(source_path)
    normalized_text: str = normalize_markdown_source_text(source_text)
    title_text: str = os.path.splitext(os.path.basename(source_path))[0].replace("_", " ").strip().title()
    content_lines: list[str] = list()

    content_lines.append(f"# VeraGridEngine Doc: {title_text}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated VeraGridEngine documentation")
    content_lines.append("")
    content_lines.append("## Document Content")
    content_lines.append("")
    content_lines.append(normalized_text.rstrip())
    content_lines.append("")

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def summarize_engine_python_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a VeraGridEngine Python module.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_engine", relative_path)
    module_text: str = read_text_file(source_path)
    module_ast: ast.Module = ast.parse(module_text)
    module_docstring: Optional[str] = ast.get_docstring(module_ast)
    content_lines: list[str] = list()
    class_count: int = 0
    function_count: int = 0
    import_lines: list[str] = list()

    content_lines.append(f"# VeraGridEngine Module: {relative_path}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated VeraGridEngine code summary")
    content_lines.append("")
    content_lines.append("## Module Summary")
    content_lines.append("")
    content_lines.append(extract_docstring_summary(module_docstring))
    content_lines.append("")

    for node in module_ast.body:
        if isinstance(node, ast.ClassDef):
            class_count += 1
        else:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                function_count += 1
            else:
                if isinstance(node, ast.Import):
                    for alias_node in node.names:
                        import_lines.append(alias_node.name)
                else:
                    if isinstance(node, ast.ImportFrom):
                        module_name: str = "" if node.module is None else node.module
                        import_lines.append(module_name)
                    else:
                        pass

    content_lines.append("## Module Surface")
    content_lines.append("")
    content_lines.append(f"- Class count: {class_count}")
    content_lines.append(f"- Top-level function count: {function_count}")

    if len(import_lines) > 0:
        content_lines.append("- Representative imports: " + ", ".join(import_lines[:16]))
    else:
        content_lines.append("- Representative imports: none")

    content_lines.append("")

    for node in module_ast.body:
        if isinstance(node, ast.ClassDef):
            base_names: list[str] = build_base_class_names(node)
            content_lines.append(f"## Class: {node.name}")
            content_lines.append("")

            if len(base_names) > 0:
                content_lines.append("- Bases: " + ", ".join(base_names))
            else:
                content_lines.append("- Bases: none")

            content_lines.append("- Summary: " + extract_docstring_summary(ast.get_docstring(node)))
            content_lines.append("")
            content_lines.append("### Methods")
            content_lines.append("")
            content_lines.extend(build_class_method_lines(node))
            content_lines.append("")
        else:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                content_lines.append(f"## Function: {build_function_heading(node)}")
                content_lines.append("")
                content_lines.append(extract_docstring_summary(ast.get_docstring(node)))
                content_lines.append("")
            else:
                pass

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def summarize_engine_plain_text_asset(repository_root: str, source_path: str) -> KnowledgeAsset:
    """
    Build one packaged knowledge asset from a VeraGridEngine plain text file.

    :param repository_root: Repository root path.
    :param source_path: Absolute source file path.
    :returns: Generated markdown asset.
    """
    relative_path: str = make_relative_repository_path(repository_root, source_path)
    output_name: str = normalize_generated_filename("generated_engine", relative_path)
    source_text: str = read_text_file(source_path).strip()
    content_lines: list[str] = list()

    content_lines.append(f"# VeraGridEngine Text Resource: {relative_path}")
    content_lines.append("")
    content_lines.append(f"- Original source path: `{relative_path}`")
    content_lines.append("- Knowledge kind: generated VeraGridEngine text resource")
    content_lines.append("")
    content_lines.append("## Resource Content")
    content_lines.append("")
    content_lines.append(source_text)
    content_lines.append("")

    return KnowledgeAsset(output_name=output_name, content="\n".join(content_lines))


def build_catalog_asset(
    repository_root: str,
    doc_assets: list[KnowledgeAsset],
    gui_assets: list[KnowledgeAsset],
    engine_assets: list[KnowledgeAsset],
) -> KnowledgeAsset:
    """
    Build a catalog asset describing the generated static RAG corpus.

    :param repository_root: Repository root path.
    :param doc_assets: Generated documentation assets.
    :param gui_assets: Generated GUI/Main assets.
    :returns: Generated catalog asset.
    """
    content_lines: list[str] = list()
    index: int = 0

    content_lines.append("# Generated VeraGrid AI Knowledge Catalog")
    content_lines.append("")
    content_lines.append("- Knowledge kind: generated asset catalog")
    content_lines.append(f"- Repository root: `{repository_root}`")
    content_lines.append(f"- Documentation asset count: {len(doc_assets)}")
    content_lines.append(f"- GUI/Main asset count: {len(gui_assets)}")
    content_lines.append(f"- VeraGridEngine asset count: {len(engine_assets)}")
    content_lines.append("")
    content_lines.append("## Documentation Assets")
    content_lines.append("")

    while index < len(doc_assets):
        content_lines.append(f"- `{doc_assets[index].output_name}`")
        index += 1

    content_lines.append("")
    content_lines.append("## GUI/Main Assets")
    content_lines.append("")

    index = 0
    while index < len(gui_assets):
        content_lines.append(f"- `{gui_assets[index].output_name}`")
        index += 1

    content_lines.append("")
    content_lines.append("## VeraGridEngine Assets")
    content_lines.append("")

    index = 0
    while index < len(engine_assets):
        content_lines.append(f"- `{engine_assets[index].output_name}`")
        index += 1

    content_lines.append("")
    return KnowledgeAsset(output_name="generated_knowledge_catalog.md", content="\n".join(content_lines))


def remove_stale_generated_assets(knowledge_directory: str) -> None:
    """
    Delete previously generated markdown assets from the knowledge directory.

    :param knowledge_directory: Absolute knowledge directory path.
    :returns: Nothing.
    """
    file_names: list[str] = sorted(os.listdir(knowledge_directory))

    for file_name in file_names:
        if file_name.startswith("generated_") and file_name.endswith(".md"):
            os.remove(os.path.join(knowledge_directory, file_name))
        else:
            pass


def build_doc_assets(repository_root: str) -> list[KnowledgeAsset]:
    """
    Generate packaged assets from ``doc/md_source``.

    :param repository_root: Repository root path.
    :returns: Generated documentation assets.
    """
    assets: list[KnowledgeAsset] = list()
    source_paths: list[str] = list_markdown_document_paths(repository_root)

    for source_path in source_paths:
        assets.append(summarize_doc_asset(repository_root, source_path))

    return assets


def build_gui_main_assets(repository_root: str) -> list[KnowledgeAsset]:
    """
    Generate packaged assets from ``src/VeraGrid/Gui/Main``.

    :param repository_root: Repository root path.
    :returns: Generated GUI/Main assets.
    """
    assets: list[KnowledgeAsset] = list()
    source_paths: list[str] = list_gui_main_source_paths(repository_root)

    for source_path in source_paths:
        if source_path.endswith(".py"):
            assets.append(summarize_python_module_asset(repository_root, source_path))
        else:
            if source_path.endswith(".ui"):
                assets.append(summarize_ui_asset(repository_root, source_path))
            else:
                assets.append(summarize_plain_text_asset(repository_root, source_path))

    return assets


def build_veragrid_engine_assets(repository_root: str) -> list[KnowledgeAsset]:
    """
    Generate packaged assets from ``src/VeraGridEngine``.

    :param repository_root: Repository root path.
    :returns: Generated VeraGridEngine assets.
    """
    assets: list[KnowledgeAsset] = list()
    source_paths: list[str] = list_veragrid_engine_source_paths(repository_root)

    for source_path in source_paths:
        if source_path.endswith(".py"):
            assets.append(summarize_engine_python_asset(repository_root, source_path))
        else:
            if source_path.endswith(".md"):
                assets.append(summarize_engine_markdown_asset(repository_root, source_path))
            else:
                assets.append(summarize_engine_plain_text_asset(repository_root, source_path))

    return assets


def write_assets(knowledge_directory: str, assets: list[KnowledgeAsset]) -> None:
    """
    Write generated assets into the packaged knowledge directory.

    :param knowledge_directory: Absolute knowledge directory path.
    :param assets: Assets to write.
    :returns: Nothing.
    """
    for asset in assets:
        output_path: str = os.path.join(knowledge_directory, asset.output_name)

        # Write each generated asset deterministically so the packaged corpus is
        # stable and versionable.
        write_text_file(output_path, asset.content)


def run_generation() -> None:
    """
    Run the packaged knowledge generation workflow.

    :returns: Nothing.
    """
    repository_root: str = build_repository_root()
    knowledge_directory: str = build_knowledge_directory(repository_root)
    doc_assets: list[KnowledgeAsset] = build_doc_assets(repository_root)
    gui_assets: list[KnowledgeAsset] = build_gui_main_assets(repository_root)
    engine_assets: list[KnowledgeAsset] = build_veragrid_engine_assets(repository_root)
    catalog_asset: KnowledgeAsset = build_catalog_asset(repository_root, doc_assets, gui_assets, engine_assets)
    assets_to_write: list[KnowledgeAsset] = list(doc_assets)
    assets_to_write.extend(gui_assets)
    assets_to_write.extend(engine_assets)
    assets_to_write.append(catalog_asset)

    # Remove the older generated corpus first so deleted sources do not leave
    # stale retrieval entries behind.
    remove_stale_generated_assets(knowledge_directory)

    # Write the regenerated corpus in one pass.
    write_assets(knowledge_directory, assets_to_write)


if __name__ == "__main__":
    run_generation()
