# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import List, Optional

from PySide6 import QtWidgets
from PySide6.QtCore import Signal

from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_preparation import prepare_block_for_editing
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_breadcrumb import DynamicEditorBreadcrumb
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_navigation import DynamicEditorNavigation
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import DynamicSimulationMode
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_models import clone_block_for_editing, copy_block_state

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGrid.Session.dynamic_editor_entries import DynamicEditorEntry


class DynamicEditorDocument:
    """
    Represents a single editing document opened in a tab.

    A document owns exactly two block trees:

    * ``original_root_block`` — the authoritative model as it was when the
      document was opened.  Never mutated during editing.
    * ``working_root_block`` — a deep copy of the original that the editors
      modify directly.  All navigation, scene building, and in-place edits
      operate exclusively on this tree.

    The document also provides lifecycle operations:

    * :meth:`commit` — copy the working tree back into the original tree.
    * :meth:`discard` — throw away the working tree and start fresh from
      the original.
    * :meth:`is_dirty` — whether the working tree has unsaved changes.
    """

    def __init__(self, original_root_block: Block) -> None:
        """
        Create a new document from the original (persistent) block tree.

        A single deep copy is made immediately; all subsequent edits
        target the copy.

        :param original_root_block: The authoritative block tree to edit.
        :return: None.
        """
        self._original_root_block: Block = original_root_block
        self._working_root_block: Block = clone_block_for_editing(original_root_block)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def original_root_block(self) -> Block:
        """Return the original (persistent) block tree."""
        return self._original_root_block

    @property
    def working_root_block(self) -> Block:
        """Return the working (editable) block tree."""
        return self._working_root_block

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def commit(self) -> None:
        """
        Copy the working tree back into the original tree.

        This is the single point where edited state is persisted back
        to the authoritative model.  Call this when the user explicitly
        saves or applies changes.

        :return: None.
        """
        copy_block_state(
            source_block=self._working_root_block,
            target_block=self._original_root_block,
        )

    def discard(self) -> None:
        """
        Discard the current working tree and recreate it from the
        original tree.

        :return: None.
        """
        self._working_root_block = clone_block_for_editing(self._original_root_block)

    def is_dirty(self) -> bool:
        """
        Return whether the working tree has unsaved modifications.

        :return: ``True`` if the document has been modified since the
            last commit.  Currently always returns ``False`` (placeholder).
        """
        return False


class DynamicEditorTab(QtWidgets.QWidget):
    """
    Coordinator widget that replaces a bare :class:`DynamicBlockEditorGUI`
    inside the workspace tab bar.

    It owns:

    * A :class:`DynamicEditorNavigation` (which holds the document).
    * A :class:`DynamicEditorBreadcrumb` at the top.
    * Exactly one :class:`DynamicBlockEditorGUI` below the breadcrumb.

    Navigation (going into a child block) destroys the current editor and
    creates a new one.  There is never more than one editor alive inside
    a tab.  All edits target the single working tree owned by the document.
    """

    dirtyStateChanged = Signal(bool)

    def __init__(
            self,
            var_factory: VarFactory,
            block: Block,
            api_object: ALL_DEV_TYPES,
            circuit: MultiCircuit,
            current_theme: str,
            mode: DynamicSimulationMode,
            templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None,
            parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._var_factory = var_factory
        self._api_object = api_object
        self._circuit = circuit
        self._mode = mode
        self.current_theme = current_theme
        self._templates_list = templates_list if templates_list is not None else list()
        self._dynamic_editor_entry: DynamicEditorEntry | None = None

        # ---- Document + Navigation ----
        document = DynamicEditorDocument(block)
        prepare_block_for_editing(document.working_root_block, var_factory)
        self._navigation = DynamicEditorNavigation(document)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._breadcrumb = DynamicEditorBreadcrumb()
        self._breadcrumb.blockClicked.connect(self._on_breadcrumb_clicked)
        self._layout.addWidget(self._breadcrumb)

        self._editor: DynamicBlockEditorGUI | None = None
        self._create_editor(self._navigation.root_block)

    # ------------------------------------------------------------------
    # Public API — session / workspace compatibility
    # ------------------------------------------------------------------

    def get_dynamic_editor_entry(self) -> DynamicEditorEntry | None:
        return self._dynamic_editor_entry

    def set_dynamic_editor_entry(self, entry: DynamicEditorEntry) -> None:
        self._dynamic_editor_entry = entry

    def get_dynamic_editor_mode(self) -> DynamicSimulationMode:
        return self._mode

    def get_dynamic_editor_display_title(self) -> str:
        object_name = self._api_object.name if self._api_object is not None else "Dynamic object"
        return f"{object_name} [{self._mode.name}]"

    @property
    def has_unapplied_changes(self) -> bool:
        if self._editor is not None:
            return self._editor.has_unapplied_changes
        return False

    def can_close_editor(self, parent: QtWidgets.QWidget | None = None) -> bool:
        if self._editor is not None:
            return self._editor.can_close_editor(parent)
        return True

    def prepare_to_delete(self) -> None:
        if self._editor is not None:
            self._editor.prepare_to_delete()

    def set_dark_mode(self) -> None:
        if self._editor is not None:
            self._editor.set_dark_mode()

    def set_light_mode(self) -> None:
        if self._editor is not None:
            self._editor.set_light_mode()

    # ------------------------------------------------------------------
    # Navigation — always over the working tree
    # ------------------------------------------------------------------

    def navigate_to_block(self, block: Block) -> None:
        """
        Navigate into a child block: prepare it in-place, update state,
        recreate the editor, and refresh the breadcrumb.

        No new copy is created; the block already lives in the working tree.

        :param block: Child block to navigate into.
        :return: None.
        """
        prepare_block_for_editing(block, self._var_factory)
        self._navigation.open_child(block)
        self._replace_editor()

    def navigate_to_breadcrumb_block(self, block: Block) -> None:
        """
        Navigate to a specific ancestor block via breadcrumb click.

        :param block: An ancestor block in the current path.
        :return: None.
        """
        self._navigation.go_to(block)
        self._replace_editor()

    def navigate_to_root(self) -> None:
        """Navigate back to the root block."""
        self._navigation.go_to_root()
        self._replace_editor()

    # ------------------------------------------------------------------
    # Editor delegation — forward commonly accessed attributes
    # ------------------------------------------------------------------

    @property
    def editor(self) -> DynamicBlockEditorGUI | None:
        return self._editor

    @property
    def is_root_editor(self) -> bool:
        return self._navigation.is_root()

    @property
    def root_block(self) -> Block:
        return self._navigation.root_block

    @property
    def current_block(self) -> Block:
        return self._navigation.current_block

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _create_editor(self, block: Block) -> None:
        self._editor = DynamicBlockEditorGUI(
            var_factory=self._var_factory,
            root_block=self._navigation.root_block,
            current_block=block,
            api_object=self._api_object,
            circuit=self._circuit,
            mode=self._mode,
            current_theme = self.current_theme,
            templates_list=self._templates_list,
            is_root_editor=self._navigation.is_root(),
            modal=False,
            workspace_embedded=True,
            document=self._navigation.document,
        )
        if self._editor is not None:
            self._editor.set_navigation_delegate(self)
            self._editor.dirtyStateChanged.connect(self.dirtyStateChanged)
            self._layout.addWidget(self._editor)
            self._refresh_breadcrumb()

    def _replace_editor(self) -> None:
        if self._editor is not None:
            self._editor.prepare_to_delete()
            self._layout.removeWidget(self._editor)
            self._editor.deleteLater()
            self._editor = None

        self._create_editor(self._navigation.current_block)

    def _refresh_breadcrumb(self) -> None:
        path: List[Block] = self._navigation.breadcrumb_path()
        self._breadcrumb.set_path(path)

    def _on_breadcrumb_clicked(self, block: Block) -> None:
        self.navigate_to_breadcrumb_block(block)
