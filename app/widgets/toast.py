"""Non-blocking toast notifications used for demo actions."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from app.theme.theme import ThemeManager
from app.widgets.common import hbox, label, tone_color
from app.widgets.icons import make_pixmap


class Toast(QFrame):
    def __init__(self, theme: ThemeManager, parent: QWidget) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMaximumWidth(560)
        layout = hbox(9, (13, 9, 15, 9), self)
        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self._text = label("", "ToastText", wrap=False)
        layout.addWidget(self._text, 1)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setDuration(160)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide_animated)
        self.hide()

    def show_message(self, message: str, tone: str = "info", duration: int = 3200) -> None:
        color = tone_color(self._theme, tone)
        self._icon.setPixmap(make_pixmap("check-circle" if tone == "success" else "info", color, 16))
        self.setMinimumWidth(0)
        self.setMaximumWidth(560)
        self._text.setText(message)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._fade.stop()
        self._fade.setStartValue(max(0.0, self._effect.opacity()))
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._timer.start(duration)

    def reposition(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        # Reset any previous fixed size so the toast can grow to fit new text.
        self.setMinimumWidth(0)
        self.setMaximumWidth(560)
        self.adjustSize()
        hint = self.sizeHint()
        available = max(280, parent.width() - 80)
        width = min(560, max(320, hint.width()), available)
        self.setFixedWidth(width)
        self.adjustSize()
        x = max(20, (parent.width() - self.width()) // 2)
        y = parent.height() - self.height() - 24
        self.move(x, y)

    def _hide_animated(self) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._effect.opacity())
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._finish_hide)
        self._fade.start()

    def _finish_hide(self) -> None:
        try:
            self._fade.finished.disconnect(self._finish_hide)
        except (RuntimeError, TypeError):
            pass
        self.hide()
