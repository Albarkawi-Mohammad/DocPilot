"""Small painted charts for the dashboard."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.theme.theme import ThemeManager


class ProcessingChart(QWidget):
    """A lightweight, dependency-free demo bar chart."""

    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._data = [12, 18, 9, 24, 17, 26, 21]
        self._labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Today"]
        self.setMinimumHeight(150)
        self.setMaximumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        theme.theme_changed.connect(lambda _mode: self.update())

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        area = QRectF(self.rect()).adjusted(2, 12, -2, -4)
        chart_height = area.height() - 26
        baseline = area.top() + chart_height
        if chart_height <= 10:
            return

        value_font = QFont("Segoe UI", 7)
        value_font.setWeight(QFont.Weight.DemiBold)
        day_font = QFont("Segoe UI", 7)
        painter.setFont(day_font)

        border = QColor(self._theme.token("border_soft"))
        muted = QColor(self._theme.token("text_muted"))
        max_value = max(self._data) or 1

        # Dotted horizontal guides.
        painter.setPen(QPen(QColor(border.red(), border.green(), border.blue(), 120), 1, Qt.PenStyle.DashLine))
        for step in range(1, 4):
            y = baseline - chart_height * step / 3
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))

        count = len(self._data)
        slot = area.width() / count
        bar_width = min(26.0, slot * 0.42)
        accent = QColor(self._theme.token("accent"))
        track = QColor(self._theme.token("bg_input"))

        for index, value in enumerate(self._data):
            center_x = area.left() + slot * index + slot / 2
            bar_height = max(6.0, chart_height * value / max_value)
            bar_rect = QRectF(center_x - bar_width / 2, baseline - bar_height, bar_width, bar_height)
            track_rect = QRectF(center_x - bar_width / 2, area.top(), bar_width, chart_height)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(track)
            painter.drawRoundedRect(track_rect, 4, 4)

            fill = QColor(accent)
            fill.setAlpha(255 if index == count - 1 else 135)
            painter.setBrush(fill)
            painter.drawRoundedRect(bar_rect, 4, 4)

            painter.setFont(value_font)
            painter.setPen(QColor(self._theme.token("text_secondary")))
            painter.drawText(
                QRectF(center_x - slot / 2, bar_rect.top() - 15, slot, 12),
                Qt.AlignmentFlag.AlignCenter,
                str(value),
            )

            painter.setFont(day_font)
            painter.setPen(muted)
            painter.drawText(
                QRectF(center_x - slot / 2, baseline + 8, slot, 14),
                Qt.AlignmentFlag.AlignCenter,
                self._labels[index],
            )

        painter.setPen(QPen(QColor(self._theme.token("border")), 1))
        painter.drawLine(QPointF(area.left(), baseline + 1), QPointF(area.right(), baseline + 1))
        painter.end()
