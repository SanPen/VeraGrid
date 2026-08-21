"""Tests for the shared Python editor hierarchy used by the GUI."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.base_python_code_editor import BasePythonCodeEditor
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import (
    BlockEquationDraft,
    DaeCodeDiagnostic,
    DaeCodeEditor,
)
from VeraGrid.Gui.python_script_editor import ScriptingPythonEditor
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def get_qt_application() -> QtWidgets.QApplication:
    """Return the process-wide Qt application required by widget tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(list())
    else:
        return application


def test_specialized_python_editors_share_visual_behavior() -> None:
    """Verify both concrete editors inherit indentation and line numbers.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    scripting_editor: ScriptingPythonEditor = ScriptingPythonEditor()
    dae_editor: DaeCodeEditor = DaeCodeEditor()

    assert isinstance(scripting_editor, BasePythonCodeEditor)
    assert isinstance(dae_editor, BasePythonCodeEditor)
    assert scripting_editor.get_line_number_area_width() > 0
    assert dae_editor.get_line_number_area_width() > 0

    tab_event: QtGui.QKeyEvent = QtGui.QKeyEvent(
        QtCore.QEvent.Type.KeyPress,
        QtCore.Qt.Key.Key_Tab,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )
    scripting_editor.keyPressEvent(tab_event)
    dae_editor.keyPressEvent(
        QtGui.QKeyEvent(
            QtCore.QEvent.Type.KeyPress,
            QtCore.Qt.Key.Key_Tab,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )
    )
    assert scripting_editor.toPlainText() == "    "
    assert dae_editor.toPlainText() == "    "

    scripting_editor.deleteLater()
    dae_editor.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()


def test_scripting_editor_owns_completion_namespace() -> None:
    """Verify Scripting variables remain synchronized with completion.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    sentinel: object = object()
    editor: ScriptingPythonEditor = ScriptingPythonEditor(
        vars_dict={"initial_object": sentinel}
    )

    namespace: dict[str, object] = editor.get_execution_namespace()
    assert namespace["initial_object"] is sentinel
    editor.add_var("later_object", sentinel)
    namespace = editor.get_execution_namespace()
    assert namespace["later_object"] is sentinel

    # The public snapshot must not mutate the completion namespace behind the
    # editor's back.
    namespace["outside_change"] = sentinel
    assert "outside_change" not in editor.get_execution_namespace()
    editor.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()


def test_dae_editor_owns_diagnostics_and_search_state() -> None:
    """Verify DAE-only overlays do not leak into the shared base editor.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    symbolic_variable: Var = Var("alpha")
    editor: DaeCodeEditor = DaeCodeEditor(
        symbol_namespace={"alpha": symbolic_variable}
    )
    editor.setPlainText("alpha + beta\nalpha")
    diagnostic: DaeCodeDiagnostic = DaeCodeDiagnostic(1, 0, 5, "Example error")

    editor.set_diagnostics(list([diagnostic]))
    assert editor.get_diagnostics() == list([diagnostic])
    assert editor.set_search_text("alpha") == 2
    assert editor.get_search_position() == (1, 2)
    assert editor.move_to_search_match(1) == (2, 2)

    # The DAE specialization owns safe symbolic parsing; it never executes the
    # Python-looking source as the Scripting specialization does.
    editor.setPlainText(
        "state_vars = []\n"
        "state_eqs = {}\n"
        "algebraic_eqs = [0 = alpha]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )
    assert editor.build_current_diagnostics() == list()
    equation_draft: BlockEquationDraft = editor.parse_current_code()
    assert len(equation_draft.get_algebraic_eqs()) == 1
    assert equation_draft.get_algebraic_eqs()[0] is symbolic_variable
    editor.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()


def test_editor_subclasses_survive_repeated_qt_lifecycles() -> None:
    """Guard against Shiboken corruption in the intermediate widget class.

    :return: None.
    """
    application: QtWidgets.QApplication = get_qt_application()
    editor_index: int
    for editor_index in range(25):
        scripting_editor: ScriptingPythonEditor = ScriptingPythonEditor()
        dae_editor: DaeCodeEditor = DaeCodeEditor()
        scripting_editor.setPlainText(str(editor_index))
        dae_editor.setPlainText(str(editor_index))
        scripting_editor.deleteLater()
        dae_editor.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        application.processEvents()
