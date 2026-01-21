# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import re
from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
)


class PythonHighlighter(QSyntaxHighlighter):
    """
    High-quality Python syntax highlighter for interactive consoles.
    """

    NORMAL = 0
    TRIPLE_SINGLE = 1
    TRIPLE_DOUBLE = 2

    def __init__(self, document):
        super().__init__(document)

        # ----------------------------
        # Formats (created ONCE)
        # ----------------------------

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            return f

        self.formats = {
            "prompt": fmt("#64B5F6", True),
            "keyword": fmt("#82AAFF", True),
            "builtin": fmt("#FFCB6B"),
            "number": fmt("#C3E88D"),
            "string": fmt("#F07178"),
            "comment": fmt("#546E7A"),
            "operator": fmt("#89DDFF"),
            "identifier": fmt("#FFFFFF"),
            "defclass": fmt("#C792EA", True),
        }

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
