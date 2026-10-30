"""Small button factory with consistent variants and themed icons."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton, QToolButton, QWidget

from app.theme.theme import ThemeManager
from app.widgets.icons import make_icon

BUTTON_OBJECT_NAMES = {
    "primary": "PrimaryButton",
    "secondary": "SecondaryButton",
    "ghost": "GhostButton",
    "danger": "DangerButton",
    "link": "LinkButton",
    "quick": "QuickAction",
    "quick_primary": "QuickActionPrimary",
}


class AppButton(QPushButton):
    def __init__(
        self,
        text: str,
        variant: str = "secondary",
        theme: ThemeManager | None = None,
        icon: str | None = None,
        icon_size: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._theme = theme
        self._variant = variant
        self._icon_name = icon
        self._icon_size = icon_size
        self.setObjectName(BUTTON_OBJECT_NAMES.get(variant, "SecondaryButton"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(icon_size, icon_size))
        if variant in ("primary", "quick_primary"):
            self.setMinimumHeight(36)
        elif variant == "quick":
            self.setMinimumHeight(38)
        else:
            self.setMinimumHeight(32)
        if icon and theme:
            self._apply_icon(theme)

    def _icon_color(self, theme: ThemeManager) -> str:
        if self._variant in ("primary", "quick_primary"):
            return "#FFFFFF"
        if self._variant == "danger":
            return theme.token("danger")
        if self._variant == "link":
            return theme.token("accent")
        if self._variant == "ghost":
            return theme.token("text_muted")
        return theme.token("text_secondary")

    def _apply_icon(self, theme: ThemeManager) -> None:
        if self._icon_name:
            self.setIcon(
                make_icon(
                    self._icon_name,
                    self._icon_color(theme),
                    self._icon_size,
                    1.9,
                )
            )

    def refresh_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        if self._icon_name:
            self._apply_icon(theme)


def make_tool_button(
    theme: ThemeManager,
    icon: str,
    *,
    object_name: str = "IconButton",
    icon_color: str | None = None,
    tooltip: str = "",
    size: int = 32,
    icon_size: int = 16,
    parent: QWidget | None = None,
) -> QToolButton:
    button = QToolButton(parent)
    button.setObjectName(object_name)
    button.setFixedSize(size, size)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setIcon(make_icon(icon, icon_color or theme.token("text_secondary"), icon_size))
    button.setIconSize(QSize(icon_size, icon_size))
    if tooltip:
        button.setToolTip(tooltip)
    return button
