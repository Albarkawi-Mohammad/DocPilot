"""Base page classes and shared page layout helpers."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.widgets.common import hbox, label, vbox


class Page(QWidget):
    toast_requested = Signal(str, str)
    navigate_requested = Signal(str)
    open_document_requested = Signal(str)

    def __init__(
        self,
        state: AppState,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.theme = theme
        self.setObjectName("Page")
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 22, 28, 24)
        self.root.setSpacing(16)

    def show_toast(self, message: str, tone: str = "info") -> None:
        self.toast_requested.emit(message, tone)

    def on_activated(self) -> None:
        """Called whenever the shell navigates to this page."""


class ScrollablePage(Page):
    def __init__(
        self,
        state: AppState,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(state, theme, parent)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._body = QWidget()
        self._body.setObjectName("PageBody")
        self.body_layout = QVBoxLayout(self._body)
        self.body_layout.setContentsMargins(0, 0, 6, 0)
        self.body_layout.setSpacing(16)
        self.scroll.setWidget(self._body)
        self.root.addWidget(self.scroll)


def page_intro(
    title: str,
    subtitle: str,
    right: QWidget | QLayout | None = None,
) -> QWidget:
    wrapper = QWidget()
    layout = hbox(14, (0, 0, 0, 0), wrapper)
    text = vbox(3)
    text.addWidget(label(title, "ContentTitle"))
    text.addWidget(label(subtitle, "ContentSubtitle", wrap=True))
    layout.addLayout(text, 1)
    if right is not None:
        right_widget = right
        if isinstance(right, QLayout):
            right_widget = QWidget()
            right_widget.setLayout(right)
        layout.addWidget(
            right_widget,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
    return wrapper


def page_heading(title: str, subtitle: str = "") -> QWidget:
    return page_intro(title, subtitle)
