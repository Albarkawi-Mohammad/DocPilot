"""Reusable, theme-aware UI primitives used across DocPilot pages."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import DocumentStatus, Person
from app.theme.theme import ThemeManager
from app.widgets.icons import make_avatar_icon, make_pixmap

TONE_TOKENS = {
    "accent": "accent",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "info": "info",
    "purple": "purple",
    "neutral": "text_muted",
}


def hbox(
    spacing: int = 12,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    parent: QWidget | None = None,
) -> QHBoxLayout:
    layout = QHBoxLayout(parent)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    return layout


def vbox(
    spacing: int = 12,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
    parent: QWidget | None = None,
) -> QVBoxLayout:
    layout = QVBoxLayout(parent)
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    return layout


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        child = item.widget()
        if child is not None:
            child.setParent(None)
            child.deleteLater()
            continue
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)
            child_layout.deleteLater()


def repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def label(
    text: str = "",
    object_name: str = "",
    *,
    wrap: bool = False,
    selectable: bool = False,
    alignment: Qt.AlignmentFlag | None = None,
) -> QLabel:
    widget = QLabel(text)
    if object_name:
        widget.setObjectName(object_name)
    widget.setWordWrap(wrap)
    widget.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
        if selectable
        else Qt.TextInteractionFlag.NoTextInteraction
    )
    if alignment is not None:
        widget.setAlignment(alignment)
    return widget


class ElidedLabel(QLabel):
    """Single-line label that shortens its text with an ellipsis when space is tight."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._full_text = text
        self.setToolTip(text)

    def setText(self, text: str) -> None:  # noqa: N802
        self._full_text = text
        self.setToolTip(text)
        self._apply_elision()

    def fullText(self) -> str:
        return self._full_text

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_elision()

    def _apply_elision(self) -> None:
        width = self.contentsRect().width()
        if width <= 0:
            return
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, width
        )
        if super().text() != elided:
            super().setText(elided)


def divider(object_name: str = "SettingDivider") -> QFrame:
    line = QFrame()
    line.setObjectName(object_name)
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    return line


def tone_color(theme: ThemeManager, tone: str) -> str:
    token = TONE_TOKENS.get(tone, "text_muted")
    return theme.token(token)


def make_icon_label(name: str, color: str, size: int = 18) -> QLabel:
    widget = QLabel()
    widget.setPixmap(make_pixmap(name, color, size))
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    widget.setFixedSize(size, size)
    return widget


class IconTile(QLabel):
    """Rounded, softly tinted square containing a single icon."""

    def __init__(
        self,
        theme: ThemeManager,
        icon: str,
        tone: str = "accent",
        size: int = 36,
        icon_size: int = 18,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("IconTile")
        self.setProperty("tone", tone)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPixmap(make_pixmap(icon, tone_color(theme, tone), icon_size))


class Badge(QLabel):
    def __init__(
        self, text: str, tone: str = "neutral", parent: QWidget | None = None
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName("Badge")
        self.setProperty("tone", tone)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        repolish(self)


STATUS_TONES = {
    DocumentStatus.ARCHIVED: "purple",
    DocumentStatus.PROCESSED: "success",
    DocumentStatus.PENDING: "neutral",
    DocumentStatus.PROCESSING: "info",
    DocumentStatus.NEEDS_REVIEW: "warning",
    DocumentStatus.FAILED: "danger",
}


def status_badge(status: DocumentStatus | str) -> Badge:
    if not isinstance(status, DocumentStatus):
        try:
            status = DocumentStatus(status)
        except ValueError:
            return Badge(str(status), "neutral")
    return Badge(status.value, STATUS_TONES.get(status, "neutral"))


CATEGORY_ICONS = {
    "Health Insurance": "heart-pulse",
    "Car Insurance": "car",
    "Jobcenter": "briefcase",
    "Bank": "landmark",
    "Tax": "receipt",
    "Other": "folder",
}


def category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "folder")


CATEGORY_COLORS = {
    "Health Insurance": "#E64F6B",
    "Car Insurance": "#4F7BF7",
    "Jobcenter": "#24A383",
    "Bank": "#C79A38",
    "Tax": "#8E6DE0",
    "Other": "#778498",
}


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#778498")


class Avatar(QLabel):
    def __init__(
        self,
        person: Optional[Person] = None,
        size: int = 28,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_person(person)

    def set_person(self, person: Optional[Person]) -> None:
        if person is None:
            color = "#556274"
            initials = "—"
            tooltip = "Unassigned"
        else:
            color = person.color
            initials = person.initials
            tooltip = person.name
        self.setText(initials)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            f"background-color: {color}; color: #FFFFFF; border-radius: {self._size // 2}px;"
            f"font-family: 'Segoe UI'; font-size: {max(8, int(self._size * 0.34))}px;"
            "font-weight: 700;"
        )


class PersonChip(QWidget):
    """Compact avatar + name used in tables and metadata blocks."""

    def __init__(
        self,
        person: Optional[Person],
        *,
        avatar_size: int = 24,
        show_subtitle: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = hbox(8 if show_subtitle else 7, parent=self)
        self._avatar = Avatar(person, avatar_size)
        layout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)
        text_layout = vbox(0)
        self._name = label(person.name if person else "Unassigned", "TableTitle")
        self._name.setStyleSheet("font-size: 11px;")
        text_layout.addWidget(self._name)
        self._subtitle = None
        if show_subtitle:
            self._subtitle = label(person.role if person else "No profile", "TableMeta")
            text_layout.addWidget(self._subtitle)
        layout.addLayout(text_layout)
        layout.addStretch(1)

    def set_person(self, person: Optional[Person]) -> None:
        self._avatar.set_person(person)
        self._name.setText(person.name if person else "Unassigned")
        if self._subtitle is not None:
            self._subtitle.setText(person.role if person else "No profile")
