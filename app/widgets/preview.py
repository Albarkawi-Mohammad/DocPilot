"""Rendered placeholder page previews for the document UI.

These pages are drawn from deterministic sample data. They intentionally contain
a visible "demo preview" marker and never render a real PDF or scanned document.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAbstractTextDocumentLayout, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy, QWidget

from app.theme.theme import ThemeManager
from app.widgets.common import category_color


class DocumentPreview(QWidget):
    def __init__(
        self,
        theme: ThemeManager,
        *,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._compact = compact
        self._filename = "sample_document.pdf"
        self._category = "Other"
        self._pages = 1
        self._page_index = 0
        self._seed = 1
        self.setMinimumSize(150, 190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        theme.theme_changed.connect(self._on_theme_changed)

    def set_document(
        self,
        *,
        filename: str,
        category: str = "Other",
        pages: int = 1,
        seed: int = 1,
        page_index: int = 0,
    ) -> None:
        self._filename = filename
        self._category = category
        self._pages = max(1, pages)
        self._seed = max(1, seed)
        self._page_index = max(0, min(page_index, self._pages - 1))
        self.setAccessibleName(f"Sample preview of {filename}, page {self._page_index + 1}")
        self.update()

    def set_page(self, page_index: int) -> None:
        self._page_index = max(0, min(page_index, self._pages - 1))
        self.update()

    def _on_theme_changed(self, _mode: str) -> None:
        self.update()

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def pages(self) -> int:
        return self._pages

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        area = QRectF(self.rect()).adjusted(7, 7, -7, -7)
        if area.width() < 20 or area.height() < 20:
            return

        ratio = 1.4142
        width = min(area.width(), area.height() / ratio)
        height = width * ratio
        page = QRectF(
            area.center().x() - width / 2,
            area.center().y() - height / 2,
            width,
            height,
        )

        # Soft page shadow.
        shadow = QColor(0, 0, 0, 64 if self._theme.is_dark else 26)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(shadow)
        painter.drawRoundedRect(page.translated(2, 4), 4, 4)

        painter.setBrush(QColor("#FCFBF7"))
        painter.setPen(QPen(QColor("#D8D6CD"), max(0.6, width * 0.003)))
        painter.drawRoundedRect(page, 3.5, 3.5)

        painter.save()
        painter.setClipRect(page.adjusted(1, 1, -1, -1))
        self._paint_page(painter, page)
        painter.restore()

        painter.end()

    def _paint_page(self, painter: QPainter, page: QRectF) -> None:
        width = page.width()
        height = page.height()
        left = page.left() + width * 0.09
        right = page.right() - width * 0.09
        cursor = page.top() + height * 0.065
        accent = QColor(category_color(self._category))

        # Accent rail and demo marker.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(
            QRectF(left, page.top() + height * 0.035, width * 0.075, height * 0.006),
            height * 0.003,
            height * 0.003,
        )

        if width > 150:
            marker_font = QFont("Segoe UI", max(5, int(width * 0.026)))
            marker_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(marker_font)
            painter.setPen(QColor("#9AA1AD"))
            painter.drawText(
                QRectF(page.left(), cursor, width - width * 0.09, height * 0.045),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                "SAMPLE PREVIEW",
            )

        if height > 120:
            # Small category pill.
            pill_w = max(44.0, width * 0.36)
            pill_h = max(10.0, height * 0.026)
            pill = QRectF(left, cursor + height * 0.012, pill_w, pill_h)
            tint = QColor(accent)
            tint.setAlpha(26 if self._theme.is_dark else 30)
            painter.setBrush(tint)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill, pill_h / 2, pill_h / 2)
            painter.setPen(accent)
            category_font = QFont("Segoe UI", max(5, int(width * 0.028)))
            category_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(category_font)
            painter.drawText(
                pill.adjusted(pill_h * 0.55, 0, -2, 0),
                Qt.AlignmentFlag.AlignVCenter,
                self._category.upper(),
            )

            title_size = max(8, int(width * 0.055))
            title_font = QFont("Segoe UI", title_size)
            title_font.setWeight(QFont.Weight.Bold)
            painter.setFont(title_font)
            painter.setPen(QColor("#222733"))
            title = self._filename.rsplit(".", 1)[0].replace("_", " ").title()
            title_rect = QRectF(left, cursor + height * 0.055, right - left, height * 0.085)
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                painter.fontMetrics().elidedText(
                    title, Qt.TextElideMode.ElideRight, int(title_rect.width())
                ),
            )

            meta_font = QFont("Segoe UI", max(5, int(width * 0.026)))
            painter.setFont(meta_font)
            painter.setPen(QColor("#8A8F9B"))
            painter.drawText(
                QRectF(left, page.top() + height * 0.178, right - left, height * 0.03),
                Qt.AlignmentFlag.AlignLeft,
                f"Reference  DP-{self._seed:03d}-{self._page_index + 1:02d}",
            )

            painter.setPen(QPen(QColor("#E5E2D9"), max(0.6, width * 0.003)))
            y = page.top() + height * 0.215
            painter.drawLine(QPointF(left, y), QPointF(right, y))

            content_top = page.top() + height * 0.245
            self._paint_content(painter, QRectF(left, content_top, right - left, height * 0.58))

            # Watermark and footer.
            painter.save()
            painter.translate(page.center())
            painter.rotate(-28)
            watermark_font = QFont("Segoe UI", max(18, int(width * 0.18)))
            watermark_font.setWeight(QFont.Weight.Black)
            painter.setFont(watermark_font)
            painter.setPen(QColor(108, 115, 130, 18))
            painter.drawText(
                QRectF(-width * 0.6, -height * 0.08, width * 1.2, height * 0.16),
                Qt.AlignmentFlag.AlignCenter,
                "SAMPLE",
            )
            painter.restore()

            painter.setPen(QPen(QColor("#E5E2D9"), max(0.6, width * 0.003)))
            footer_y = page.bottom() - height * 0.055
            painter.drawLine(QPointF(left, footer_y), QPointF(right, footer_y))
            footer_font = QFont("Segoe UI", max(5, int(width * 0.024)))
            painter.setFont(footer_font)
            painter.setPen(QColor("#9398A3"))
            painter.drawText(
                QRectF(left, footer_y + height * 0.012, (right - left) * 0.7, height * 0.03),
                Qt.AlignmentFlag.AlignLeft,
                "Demo preview · no real document content",
            )
            painter.drawText(
                QRectF(
                    right - (right - left) * 0.25,
                    footer_y + height * 0.012,
                    (right - left) * 0.25,
                    height * 0.03,
                ),
                Qt.AlignmentFlag.AlignRight,
                f"{self._page_index + 1} / {self._pages}",
            )
        else:
            # Compact tiny fallback.
            painter.setPen(QColor("#9AA1AD"))
            painter.setFont(QFont("Segoe UI", 5))
            painter.drawText(page.adjusted(6, 8, -6, -8), Qt.AlignmentFlag.AlignCenter, "PDF")

    def _paint_content(self, painter: QPainter, area: QRectF) -> None:
        width = area.width()
        height = area.height()
        seed = self._seed + self._page_index * 3
        line_color = QColor("#C9C8C1")
        dark_text = QColor("#4B505C")

        heading_font = QFont("Segoe UI", max(5, int(width * 0.032)))
        heading_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(heading_font)
        painter.setPen(dark_text)
        headings = ["Document details", "Statement overview", "Reference information"]
        painter.drawText(
            QRectF(area.left(), area.top(), width, height * 0.07),
            Qt.AlignmentFlag.AlignLeft,
            headings[seed % len(headings)],
        )

        y = area.top() + height * 0.12
        line_height = max(2.0, height * 0.026)
        painter.setPen(QPen(line_color, max(0.8, width * 0.0045), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for index in range(3):
            line_width = width * (0.56 + ((seed * 11 + index * 17) % 34) / 100)
            painter.drawLine(QPointF(area.left(), y), QPointF(area.left() + line_width, y))
            y += line_height

        # A small two-column summary block.
        block_top = area.top() + height * 0.34
        gap = width * 0.07
        col_width = (width - gap) / 2
        for column in range(2):
            x = area.left() + column * (col_width + gap)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F0EEE6"))
            painter.drawRoundedRect(
                QRectF(x, block_top, col_width, height * 0.25), 2.5, 2.5
            )
            painter.setBrush(QColor("#D8D4C9"))
            painter.drawRoundedRect(
                QRectF(x + col_width * 0.09, block_top + height * 0.055, col_width * 0.52, max(2, height * 0.014)),
                1,
                1,
            )
            for line in range(2):
                painter.setBrush(QColor("#E2DFD5"))
                painter.drawRoundedRect(
                    QRectF(
                        x + col_width * 0.09,
                        block_top + height * 0.13 + line * height * 0.038,
                        col_width * (0.68 - line * 0.13),
                        max(1.8, height * 0.011),
                    ),
                    1,
                    1,
                )

        # Table rows at the bottom.
        table_top = area.top() + height * 0.68
        painter.setPen(QPen(QColor("#DFDCD2"), max(0.6, width * 0.0028)))
        for row in range(3):
            y = table_top + row * height * 0.075
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            painter.setPen(QPen(QColor("#CFCBC0"), max(0.7, width * 0.003)))
            painter.drawLine(
                QPointF(area.left() + width * 0.08, y),
                QPointF(area.left() + width * 0.08, y + height * 0.05),
            )
            painter.setPen(QPen(QColor("#DFDCD2"), max(0.6, width * 0.0028)))
        painter.drawLine(
            QPointF(area.left(), table_top + height * 0.225),
            QPointF(area.right(), table_top + height * 0.225),
        )

        # Demo stamp.
        stamp_r = min(width * 0.115, height * 0.11)
        center = QPointF(area.right() - stamp_r * 1.3, area.top() + height * 0.08)
        stamp_color = QColor("#B36B5F")
        stamp_color.setAlpha(135)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(stamp_color, max(1.0, width * 0.006)))
        painter.drawEllipse(center, stamp_r, stamp_r)
        stamp_font = QFont("Segoe UI", max(5, int(width * 0.034)))
        stamp_font.setWeight(QFont.Weight.Bold)
        painter.setFont(stamp_font)
        painter.drawText(
            QRectF(center.x() - stamp_r, center.y() - stamp_r, stamp_r * 2, stamp_r * 2),
            Qt.AlignmentFlag.AlignCenter,
            "DEMO",
        )


class PageThumbnail(QAbstractButton):
    """Tiny clickable page thumbnail with no real document content."""

    def __init__(
        self,
        theme: ThemeManager,
        page_number: int,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._page_number = page_number
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(46, 60)
        self.setToolTip(f"Preview page {page_number}")
        theme.theme_changed.connect(self._on_theme_changed)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(46, 60)

    def _on_theme_changed(self, _mode: str) -> None:
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        border = QColor(self._theme.token("accent") if self.isChecked() else self._theme.token("border_strong"))
        painter.setPen(QPen(border, 2 if self.isChecked() else 1))
        painter.setBrush(QColor("#FCFBF7"))
        painter.drawRoundedRect(rect, 3, 3)
        painter.setPen(QPen(QColor("#D6D1C5"), 0.8))
        for index in range(4):
            y = rect.top() + 13 + index * 8
            width = rect.width() * (0.55 if index == 3 else 0.7)
            painter.drawLine(
                QPointF(rect.left() + 8, y),
                QPointF(rect.left() + 8 + width, y),
            )
        painter.setPen(QColor("#8B8F99"))
        painter.setFont(QFont("Segoe UI", 6))
        painter.drawText(
            QRectF(rect.left(), rect.bottom() - 12, rect.width(), 10),
            Qt.AlignmentFlag.AlignCenter,
            str(self._page_number),
        )
        painter.end()
