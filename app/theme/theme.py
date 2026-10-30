"""Dark/light theme tokens and the application theme manager."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.theme.styles import build_stylesheet

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

DARK = {
    "bg_window": "#0C0F14",
    "bg_sidebar": "#0A0D12",
    "bg_card": "#141920",
    "bg_card_alt": "#19202A",
    "bg_input": "#0F141B",
    "bg_hover": "#1A222D",
    "bg_active": "#202A37",
    "border": "#242D39",
    "border_soft": "#1B232D",
    "border_strong": "#344052",
    "text": "#F2F5F9",
    "text_secondary": "#A8B2C1",
    "text_muted": "#748094",
    "text_on_accent": "#FFFFFF",
    "accent": "#6E8BFF",
    "accent_hover": "#88A0FF",
    "accent_pressed": "#5474EA",
    "accent_soft": "rgba(110, 139, 255, 0.13)",
    "success": "#3DDC97",
    "success_soft": "rgba(61, 220, 151, 0.12)",
    "warning": "#F5C451",
    "warning_soft": "rgba(245, 196, 81, 0.12)",
    "danger": "#FF7A7A",
    "danger_soft": "rgba(255, 122, 122, 0.12)",
    "info": "#6BC8F5",
    "info_soft": "rgba(107, 200, 245, 0.12)",
    "purple": "#B794F6",
    "purple_soft": "rgba(183, 148, 246, 0.12)",
    "neutral_soft": "rgba(255, 255, 255, 0.06)",
    "selection": "rgba(110, 139, 255, 0.16)",
    "scrollbar": "#2A3544",
    "scrollbar_hover": "#3A4759",
    "shadow": "rgba(0, 0, 0, 0.28)",
}

LIGHT = {
    "bg_window": "#F4F6FA",
    "bg_sidebar": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_card_alt": "#F8FAFC",
    "bg_input": "#F4F6FA",
    "bg_hover": "#EFF3F9",
    "bg_active": "#E8EEF8",
    "border": "#E1E7F0",
    "border_soft": "#EBF0F6",
    "border_strong": "#CBD5E1",
    "text": "#111827",
    "text_secondary": "#4B5565",
    "text_muted": "#7A8698",
    "text_on_accent": "#FFFFFF",
    "accent": "#4269E8",
    "accent_hover": "#3157D2",
    "accent_pressed": "#2949B5",
    "accent_soft": "rgba(66, 105, 232, 0.10)",
    "success": "#0E9F6E",
    "success_soft": "rgba(14, 159, 110, 0.10)",
    "warning": "#B7791F",
    "warning_soft": "rgba(183, 121, 31, 0.10)",
    "danger": "#D64545",
    "danger_soft": "rgba(214, 69, 69, 0.10)",
    "info": "#0B82B5",
    "info_soft": "rgba(11, 130, 181, 0.10)",
    "purple": "#7C5CD3",
    "purple_soft": "rgba(124, 92, 211, 0.10)",
    "neutral_soft": "rgba(17, 24, 39, 0.05)",
    "selection": "rgba(66, 105, 232, 0.12)",
    "scrollbar": "#C8D3E1",
    "scrollbar_hover": "#AEBCCE",
    "shadow": "rgba(15, 23, 42, 0.08)",
}

THEMES = {"dark": DARK, "light": LIGHT}


class ThemeManager(QObject):
    """Owns the active color scheme and applies the generated QSS."""

    theme_changed = Signal(str)

    def __init__(self, mode: str = "dark") -> None:
        super().__init__()
        self._mode = mode if mode in THEMES else "dark"
        self._app: QApplication | None = None

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_dark(self) -> bool:
        return self._mode == "dark"

    @property
    def tokens(self) -> dict[str, str]:
        return THEMES[self._mode]

    def token(self, name: str) -> str:
        return self.tokens[name]

    def attach(self, app: QApplication) -> None:
        self._app = app
        self.apply()

    def set_mode(self, mode: str) -> None:
        if mode not in THEMES or mode == self._mode:
            return
        self._mode = mode
        self.apply()
        self.theme_changed.emit(self._mode)

    def toggle(self) -> None:
        self.set_mode("light" if self._mode == "dark" else "dark")

    def apply(self) -> None:
        if self._app is None:
            return
        self._app.setStyleSheet(
            build_stylesheet(self.tokens, str(ASSETS_DIR).replace("\\", "/"))
        )
