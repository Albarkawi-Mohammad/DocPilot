"""Table helpers and rich cell widgets."""

from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.models.entities import DocumentStatus, Person
from app.theme.theme import ThemeManager
from app.widgets.common import (
    Badge,
    ElidedLabel,
    IconTile,
    PersonChip,
    category_color,
    category_icon,
    label,
    make_icon_label,
    status_badge,
    hbox,
    vbox,
)
from app.widgets.icons import make_pixmap


def make_mouse_transparent(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    for child in widget.findChildren(QWidget):
        child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)


def configure_table(table: QTableWidget) -> None:
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(52)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setFixedHeight(34)
    table.horizontalHeader().setMinimumSectionSize(44)
    table.horizontalHeader().setStretchLastSection(False)
    table.setFrameShape(QTableWidget.Shape.NoFrame)
    table.setMouseTracking(True)
    table.viewport().setMouseTracking(True)


def make_table(headers: Iterable[str], row_height: int = 52) -> QTableWidget:
    headers = list(headers)
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    configure_table(table)
    table.verticalHeader().setDefaultSectionSize(row_height)
    return table


def text_item(text: str, alignment: Qt.AlignmentFlag | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if alignment is not None:
        item.setTextAlignment(int(alignment))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def _cell_wrapper(layout_owner: QWidget, layout) -> QWidget:
    wrapper = QWidget()
    wrapper.setLayout(layout)
    layout.setContentsMargins(10, 0, 6, 0)
    make_mouse_transparent(wrapper)
    return wrapper


class FileCell(QWidget):
    def __init__(
        self,
        theme: ThemeManager,
        filename: str,
        meta: str = "",
        *,
        icon: str = "file-text",
        tone: str = "accent",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = hbox(9, (0, 0, 0, 0), self)
        layout.addWidget(IconTile(theme, icon, tone, 27, 14))
        text_layout = vbox(1)
        name = ElidedLabel(filename)
        name.setObjectName("FileName")
        name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text_layout.addWidget(name)
        if meta:
            sub = ElidedLabel(meta)
            sub.setObjectName("FileSub")
            sub.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            text_layout.addWidget(sub)
        layout.addLayout(text_layout, 1)
        make_mouse_transparent(self)


def file_cell_widget(
    theme: ThemeManager,
    filename: str,
    meta: str = "",
    *,
    icon: str = "file-text",
    tone: str = "accent",
) -> QWidget:
    return FileCell(theme, filename, meta, icon=icon, tone=tone)


class PersonTableCell(QWidget):
    def __init__(self, person: Optional[Person], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = hbox(0, (0, 0, 0, 0), self)
        chip = PersonChip(person, avatar_size=22)
        layout.addWidget(chip)
        make_mouse_transparent(self)


def person_cell_widget(person: Optional[Person]) -> QWidget:
    return PersonTableCell(person)


class CategoryTableCell(QWidget):
    def __init__(
        self, theme: ThemeManager, category: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        layout = hbox(7, (0, 0, 0, 0), self)
        layout.addWidget(make_icon_label(category_icon(category), category_color(category), 14))
        name = label(category, "FieldValue")
        layout.addWidget(name)
        layout.addStretch(1)
        make_mouse_transparent(self)


def category_cell_widget(theme: ThemeManager, category: str) -> QWidget:
    return CategoryTableCell(theme, category)


class StatusTableCell(QWidget):
    def __init__(
        self, status: DocumentStatus | str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        layout = hbox(0, (0, 0, 0, 0), self)
        layout.addWidget(status_badge(status))
        layout.addStretch(1)
        make_mouse_transparent(self)


def status_cell_widget(status: DocumentStatus | str) -> QWidget:
    return StatusTableCell(status)


def badge_cell(text: str, tone: str) -> QWidget:
    wrapper = QWidget()
    layout = hbox(0, (0, 0, 0, 0), wrapper)
    layout.addWidget(Badge(text, tone))
    layout.addStretch(1)
    make_mouse_transparent(wrapper)
    return wrapper
