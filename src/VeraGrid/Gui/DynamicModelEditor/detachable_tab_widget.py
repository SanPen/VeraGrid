from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


DYNAMIC_EDITOR_TAB_MIME: str = "application/x-veragrid-dynamic-editor-tab"


class DynamicEditorAddButton(QtWidgets.QToolButton):
    """
    Corner button used as both the add-entry action and a reattach drop target.
    """

    tabWidgetDropRequested = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("+")
        self.setAutoRaise(True)
        self.setToolTip("Open another Dynamic Editor")

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            self.tabWidgetDropRequested.emit(self.mapToGlobal(event.position().toPoint()))
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabBar(QtWidgets.QTabBar):
    """
    Tab bar that supports drag-out detach and drag-in reattach between workspaces.
    """

    detachDragIgnored = QtCore.Signal(QtCore.QPoint)
    tabDropRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_start_pos: Optional[QtCore.QPoint] = None
        self._drag_index: int = -1
        self.setAcceptDrops(True)
        self.setExpanding(False)
        self.setMovable(False)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._drag_index = self.tabAt(event.pos())
        else:
            self._drag_start_pos = None
            self._drag_index = -1

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if (
            self._drag_start_pos is None
            or self._drag_index < 0
            or not (event.buttons() & QtCore.Qt.MouseButton.LeftButton)
        ):
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self._drag_start_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        tab_widget = self.parent()
        if isinstance(tab_widget, DetachableEditorTabWidget):
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            mime.setData(DYNAMIC_EDITOR_TAB_MIME, b"dynamic-editor-tab")
            drag.setMimeData(mime)
            drag.setHotSpot(event.pos() - self.tabRect(self._drag_index).topLeft())
            tab_widget.prepare_tab_drag(self._drag_index)
            result = drag.exec(QtCore.Qt.DropAction.MoveAction)
            tab_widget.finish_tab_drag(result, QtGui.QCursor.pos())
            self._drag_start_pos = None
            self._drag_index = -1
            return
        else:
            super().mouseMoveEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME):
            target_index = self.tabAt(event.position().toPoint())
            self.tabDropRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()


class DetachableEditorTabWidget(QtWidgets.QTabWidget):
    """
    QTabWidget wrapper used by the Dynamic Editor workspace.
    """

    tabDragStarted = QtCore.Signal(int)
    detachRequested = QtCore.Signal(QtCore.QPoint)
    reattachRequested = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._tab_bar = DetachableEditorTabBar(self)
        self._pending_drag_index: int = -1
        self.setTabBar(self._tab_bar)
        self.setAcceptDrops(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setMovable(False)
        self._tab_bar.detachDragIgnored.connect(self._on_detach_drag_ignored)
        self._tab_bar.tabDropRequested.connect(self.reattachRequested.emit)

    def prepare_tab_drag(self, index: int) -> None:
        self._pending_drag_index = index
        self.tabDragStarted.emit(index)

    def finish_tab_drag(self, result: QtCore.Qt.DropAction, global_pos: QtCore.QPoint) -> None:
        if self._pending_drag_index < 0:
            return

        if result != QtCore.Qt.DropAction.MoveAction:
            self.detachRequested.emit(global_pos)
        else:
            pass

        self._pending_drag_index = -1

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasFormat(DYNAMIC_EDITOR_TAB_MIME) and event.position().y() <= self.tabBar().height() + 8:
            target_index = self.tabBar().tabAt(self.tabBar().mapFrom(self, event.position().toPoint()))
            self.reattachRequested.emit(self.mapToGlobal(event.position().toPoint()), target_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_detach_drag_ignored(self, global_pos: QtCore.QPoint) -> None:
        self.detachRequested.emit(global_pos)
