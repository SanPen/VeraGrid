# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import re
from typing import Dict

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class PythonHighlighter(QSyntaxHighlighter):
    """
    High-quality Python syntax highlighter for interactive consoles.
    """

    NORMAL = 0
    TRIPLE_SINGLE = 1
    TRIPLE_DOUBLE = 2

    def __init__(self, document):
        super().__init__(document)

        self.formats: Dict[str, QTextCharFormat] = dict()

        # ----------------------------
        # Keyword sets
        # ----------------------------

        self.keywords = {
            "and", "as", "assert", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "False",
            "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "None", "nonlocal", "not",
            "or", "pass", "raise", "return", "True", "try",
            "while", "with", "yield",
        }

        self.builtins = {
            "print", "len", "range", "open", "min", "max",
            "sum", "abs", "round", "zip", "enumerate", "sorted",
            "map", "filter", "list", "dict", "set", "tuple",
            "int", "float", "str", "bool",
        }

        # ----------------------------
        # Precompiled regexes
        # ----------------------------

        self.re_prompt = re.compile(r"^(>>> |\.\.\. )")
        self.re_identifier = re.compile(r"\b[A-Za-z_]\w*\b")
        self.re_number = re.compile(r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b")
        self.re_comment = re.compile(r"#.*$")
        self.re_operator = re.compile(r"[+\-*/%=<>!&|^~]+")

        self.re_string_single = re.compile(r"'([^'\\]|\\.)*'")
        self.re_string_double = re.compile(r'"([^"\\]|\\.)*"')

        self.re_triple_single = re.compile(r"'''")
        self.re_triple_double = re.compile(r'"""')
        self.set_light_mode()

    def _make_format(self, color: str, bold: bool = False) -> QTextCharFormat:
        """
        Build one text format used by the syntax highlighter.

        :param color: Hexadecimal text color.
        :param bold: Whether the token must be bold.
        :return: Text format with the requested foreground.
        """
        text_format: QTextCharFormat = QTextCharFormat()
        text_format.setForeground(QColor(color))
        if bold:
            text_format.setFontWeight(QFont.Weight.Bold)
        else:
            pass
        return text_format

    def apply_theme(self, dark_theme: bool) -> None:
        """
        Apply token colors for the current editor theme.

        :param dark_theme: Whether to use the dark token palette.
        :return: None.
        """
        if dark_theme:
            self.formats = {
                "prompt": self._make_format("#64B5F6", True),
                "keyword": self._make_format("#82AAFF", True),
                "builtin": self._make_format("#FFCB6B"),
                "number": self._make_format("#C3E88D"),
                "string": self._make_format("#F07178"),
                "comment": self._make_format("#78909C"),
                "operator": self._make_format("#89DDFF"),
                "identifier": self._make_format("#F5F5F5"),
                "defclass": self._make_format("#C792EA", True),
            }
        else:
            self.formats = {
                "prompt": self._make_format("#1565C0", True),
                "keyword": self._make_format("#5B21B6", True),
                "builtin": self._make_format("#92400E"),
                "number": self._make_format("#166534"),
                "string": self._make_format("#B91C1C"),
                "comment": self._make_format("#64748B"),
                "operator": self._make_format("#0369A1"),
                "identifier": self._make_format("#141414"),
                "defclass": self._make_format("#7E22CE", True),
            }
        self.rehighlight()

    def set_dark_mode(self) -> None:
        """
        Apply dark syntax colors.

        :return: None.
        """
        self.apply_theme(dark_theme=True)

    def set_light_mode(self) -> None:
        """
        Apply light syntax colors.

        :return: None.
        """
        self.apply_theme(dark_theme=False)

    # ----------------------------
    # Core highlighter
    # ----------------------------

    def highlightBlock(self, text):
        self.setCurrentBlockState(self.NORMAL)

        # ---- Prompt ----
        m = self.re_prompt.match(text)
        if m:
            self.setFormat(0, m.end(), self.formats["prompt"])

        # ---- Multiline strings ----
        if self._handle_multiline_strings(text):
            return

        # ---- Comments ----
        for m in self.re_comment.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.formats["comment"])

        # ---- Strings ----
        for rx in (self.re_string_single, self.re_string_double):
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), self.formats["string"])

        # ---- Numbers ----
        for m in self.re_number.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.formats["number"])

        # ---- Operators ----
        for m in self.re_operator.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.formats["operator"])

        # ---- Identifiers, keywords, builtins ----
        for m in self.re_identifier.finditer(text):
            word = m.group()
            if word in self.keywords:
                self.setFormat(m.start(), len(word), self.formats["keyword"])
            elif word in self.builtins:
                self.setFormat(m.start(), len(word), self.formats["builtin"])

    # ----------------------------
    # Multiline string handling
    # ----------------------------

    def _handle_multiline_strings(self, text):
        if self.previousBlockState() == self.TRIPLE_SINGLE:
            end = self.re_triple_single.search(text)
            if end:
                self.setFormat(0, end.end(), self.formats["string"])
                self.setCurrentBlockState(self.NORMAL)
                return False
            else:
                self.setFormat(0, len(text), self.formats["string"])
                self.setCurrentBlockState(self.TRIPLE_SINGLE)
                return True

        if self.previousBlockState() == self.TRIPLE_DOUBLE:
            end = self.re_triple_double.search(text)
            if end:
                self.setFormat(0, end.end(), self.formats["string"])
                self.setCurrentBlockState(self.NORMAL)
                return False
            else:
                self.setFormat(0, len(text), self.formats["string"])
                self.setCurrentBlockState(self.TRIPLE_DOUBLE)
                return True

        start = self.re_triple_single.search(text)
        if start:
            self.setFormat(start.start(), len(text) - start.start(), self.formats["string"])
            self.setCurrentBlockState(self.TRIPLE_SINGLE)
            return True

        start = self.re_triple_double.search(text)
        if start:
            self.setFormat(start.start(), len(text) - start.start(), self.formats["string"])
            self.setCurrentBlockState(self.TRIPLE_DOUBLE)
            return True

        return False
