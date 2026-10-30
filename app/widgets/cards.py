"""Card containers and other reusable presentation blocks."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import ActivityEntry
from app.theme.theme import ThemeManager
from app.widgets.buttons import AppButton
from app.widgets.common import (
    Badge,
    IconTile,
    hbox,
    label,
    make_icon_label,
    tone_color,
    vbox,
)


class Card(QFrame):
    """Rounded surface with a ready-to-use content layout."""

    def __init__(
        self,
        theme: ThemeManager,
        padding: int = 18,
        spacing: int = 12,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.theme = theme
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)


class SoftCard(QFrame):
    def __init__(
        self,
        theme: ThemeManager,
        padding: int = 14,
        spacing: int = 10,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SoftCard")
        self.theme = theme
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)


class SectionHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        right: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = hbox(10, parent=self)
        text_layout = vbox(2)
        self.title_label = label(title, "CardTitle")
        text_layout.addWidget(self.title_label)
        self.subtitle_label = label(subtitle, "CardSubtitle", wrap=True)
        self.subtitle_label.setVisible(bool(subtitle))
        text_layout.addWidget(self.subtitle_label)
        layout.addLayout(text_layout, 1)
        if right is not None:
            layout.addWidget(right, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))


class StatCard(Card):
    def __init__(
        self,
        theme: ThemeManager,
        icon: str,
        label_text: str,
        value: str,
        footnote: str,
        tone: str = "accent",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(theme, padding=17, spacing=8, parent=parent)
        self.setMinimumHeight(128)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top = hbox(8)
        top.addWidget(label(label_text, "StatLabel"), 1, Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(IconTile(theme, icon, tone, 34, 17), 0, Qt.AlignmentFlag.AlignRight)
        self.body.addLayout(top)
        self.value_label = label(value, "StatValue")
        self.body.addWidget(self.value_label)
        self.footnote_label = label(footnote, "StatFootnote", wrap=True)
        self.body.addWidget(self.footnote_label)
        self.body.addStretch(1)

    def update_value(self, value: str | int, footnote: str | None = None) -> None:
        self.value_label.setText(str(value))
        if footnote is not None:
            self.footnote_label.setText(footnote)


class InfoBanner(QFrame):
    def __init__(
        self,
        theme: ThemeManager,
        *,
        icon: str = "info",
        title: str = "",
        text: str = "",
        tone: str = "accent",
        right: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("InfoBanner")
        self.setProperty("tone", tone)
        layout = hbox(11, (12, 10, 12, 10), self)
        icon_color = tone_color(theme, tone)
        icon_label = make_icon_label(icon, icon_color, 17)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        text_layout = vbox(2)
        if title:
            title_label = label(title, "BannerTitle", wrap=True)
            text_layout.addWidget(title_label)
        if text:
            text_label = label(text, "BannerText", wrap=True)
            text_layout.addWidget(text_label)
        layout.addLayout(text_layout, 1)
        if right is not None:
            layout.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)


class EmptyState(QWidget):
    def __init__(
        self,
        theme: ThemeManager,
        icon: str,
        title: str,
        text: str,
        *,
        action_text: str | None = None,
        action_icon: str | None = None,
        tone: str = "neutral",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setMinimumHeight(160)
        layout = vbox(10, (20, 22, 20, 22), self)
        layout.addStretch(1)
        tile = IconTile(theme, icon, tone, 48, 22)
        layout.addWidget(tile, 0, Qt.AlignmentFlag.AlignHCenter)
        self.title_label = label(title, "EmptyTitle", alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        self.text_label = label(text, "EmptyText", wrap=True, alignment=Qt.AlignmentFlag.AlignCenter)
        self.text_label.setMaximumWidth(380)
        self._text_width = 0
        self._fit_text()
        layout.addWidget(self.text_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.action_button: AppButton | None = None
        if action_text:
            self.action_button = AppButton(
                action_text,
                "secondary",
                theme,
                icon=action_icon,
                icon_size=14,
            )
            layout.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def _fit_text(self) -> None:
        """Keep wrapped empty-state copy fully visible at the current width."""
        available = self.width() - 80 if self.width() > 180 else 380
        target = max(160, min(380, available))
        if target == self._text_width:
            return
        self._text_width = target
        height = self.text_label.heightForWidth(target)
        if height > 0:
            self.text_label.setFixedWidth(target)
            self.text_label.setFixedHeight(height)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._fit_text()


class ActivityRow(QWidget):
    def __init__(
        self,
        theme: ThemeManager,
        entry: ActivityEntry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ActivityRow")
        layout = hbox(10, (0, 5, 0, 5), self)
        tile = IconTile(theme, entry.icon, entry.tone, 30, 15)
        layout.addWidget(tile, 0, Qt.AlignmentFlag.AlignTop)
        text_layout = vbox(2)
        title = label(entry.title, "TableTitle", wrap=True)
        title.setStyleSheet("font-size: 11px;")
        subtitle = label(entry.subtitle, "TableMeta", wrap=True)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        layout.addLayout(text_layout, 1)
        time_label = label(entry.time_label, "TableMeta")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(time_label, 0, Qt.AlignmentFlag.AlignTop)


def make_tag(text: str, tone: str = "neutral") -> Badge:
    return Badge(text, tone)


def meta_block(title: str, value: str, parent: QWidget | None = None) -> QWidget:
    widget = QWidget(parent)
    layout = vbox(2, (0, 0, 0, 0), widget)
    layout.addWidget(label(title, "FieldLabel"))
    value_label = label(value or "—", "FieldValue", wrap=True)
    layout.addWidget(value_label)
    return widget


def empty_placeholder(
    theme: ThemeManager, icon: str, title: str, text: str
) -> QWidget:
    return EmptyState(theme, icon, title, text)
