"""Scan & Import page — read-only PDF selection interface."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import SelectedFile
from app.pages.base import ScrollablePage, page_intro
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.utils import format_file_size, pluralize
from app.widgets.buttons import AppButton, make_tool_button
from app.widgets.cards import Card, EmptyState, InfoBanner
from app.widgets.common import (
    Badge,
    IconTile,
    clear_layout,
    hbox,
    label,
    make_icon_label,
    repolish,
    vbox,
)
from app.widgets.icons import make_icon


class DropZone(QFrame):
    files_dropped = Signal(list)
    browse_requested = Signal()

    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_active = False
        self.setObjectName("DropZone")
        self.setProperty("dragActive", False)
        self.setAcceptDrops(True)
        self.setMinimumHeight(236)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = vbox(9, (26, 24, 26, 24), self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_tile = IconTile(theme, "upload-cloud", "accent", 54, 25)
        layout.addWidget(icon_tile, 0, Qt.AlignmentFlag.AlignHCenter)
        title = label("Drop PDF files here", "EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        hint = label(
            "Add documents to the import queue. Original files stay exactly where they are.",
            "EmptyText",
            wrap=True,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        hint.setMinimumWidth(340)
        hint.setMaximumWidth(480)
        hint.setMinimumHeight(34)
        layout.addWidget(hint, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(3)
        button = AppButton(
            "Select PDF files", "primary", theme, icon="file-plus", icon_size=15
        )
        button.clicked.connect(lambda: self.browse_requested.emit())
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        footnote = label("PDF only  ·  nothing is uploaded or copied", "TableMeta")
        footnote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footnote)

    def _set_drag_active(self, active: bool) -> None:
        if active == self._drag_active:
            return
        self._drag_active = active
        self.setProperty("dragActive", active)
        repolish(self)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        self._set_drag_active(False)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and url.toLocalFile()
        ]
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
        else:
            event.ignore()


class SelectedFileRow(QFrame):
    remove_requested = Signal(str)

    def __init__(
        self,
        file: SelectedFile,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._file = file
        self.setObjectName("FileRow")
        layout = hbox(11, (12, 9, 10, 9), self)
        layout.addWidget(IconTile(theme, "file-text", "danger", 36, 18))
        text = vbox(2)
        name = label(file.filename, "FileName")
        name.setToolTip(file.path)
        text.addWidget(name)
        pages = f"{pluralize(file.pages, 'page')}" if file.pages else "Page count unavailable"
        meta = label(
            f"{format_file_size(file.size_bytes)}  ·  PDF  ·  {pages}", "FileSub"
        )
        meta.setToolTip(file.path)
        text.addWidget(meta)
        layout.addLayout(text, 1)
        path_label = label(os.path.dirname(file.path), "FileSub")
        path_label.setToolTip(file.path)
        path_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(path_label, 0)
        remove = make_tool_button(
            theme,
            "x",
            object_name="BareIconButton",
            icon_color=theme.token("text_muted"),
            tooltip="Remove from list (the original PDF is kept)",
            size=28,
            icon_size=14,
        )
        remove.clicked.connect(lambda: self.remove_requested.emit(self._file.path))
        layout.addWidget(remove, 0)


class ScanImportPage(ScrollablePage):
    processing_requested = Signal()

    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self._build()
        self.state.files_changed.connect(self._refresh_files)
        self._refresh_files()

    def _build(self) -> None:
        intro_right = hbox(8)
        intro_right.addWidget(Badge("PDF only", "neutral"))
        intro_right.addWidget(Badge("UI preview", "warning"))
        self.body_layout.addWidget(
            page_intro(
                "Bring documents in",
                "Choose local PDFs for the demo queue. Nothing is uploaded, renamed, moved, or copied.",
                intro_right,
            )
        )
        self.body_layout.addWidget(
            InfoBanner(
                self.theme,
                icon="shield-check",
                title="Selection only — originals stay untouched",
                text=(
                    "Files are held in memory and page counts are read locally. "
                    "OCR and document processing are deliberately not implemented."
                ),
                tone="accent",
            )
        )

        self.drop_zone = DropZone(self.theme)
        self.drop_zone.browse_requested.connect(self._choose_files)
        self.drop_zone.files_dropped.connect(self._files_dropped)
        self.body_layout.addWidget(self.drop_zone)

        file_card = Card(self.theme, padding=0, spacing=0)
        header = QWidget()
        header_layout = hbox(12, (18, 15, 18, 9), header)
        header_text = vbox(2)
        header_text.addWidget(label("Selected files", "CardTitle"))
        self.file_summary = label("No files selected", "CardSubtitle")
        header_text.addWidget(self.file_summary)
        header_layout.addLayout(header_text, 1)
        self.clear_button = AppButton("Clear all", "ghost", self.theme, icon="trash", icon_size=13)
        self.clear_button.clicked.connect(self._clear_files)
        header_layout.addWidget(self.clear_button, 0, Qt.AlignmentFlag.AlignVCenter)
        file_card.body.addWidget(header)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.files_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.files_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.files_scroll.setMinimumHeight(154)
        self.files_scroll.setMaximumHeight(310)
        self.files_host = QWidget()
        self.files_layout = vbox(7, (18, 3, 18, 8), self.files_host)
        self.files_scroll.setWidget(self.files_host)
        file_card.body.addWidget(self.files_scroll)

        footer = QWidget()
        footer_layout = hbox(14, (18, 10, 18, 15), footer)
        totals = vbox(1)
        self.total_label = label("0 files  ·  0 B", "FileName")
        totals.addWidget(self.total_label)
        totals.addWidget(label("Original files are never modified by this screen.", "FileSub"))
        footer_layout.addLayout(totals, 1)
        self.start_button = AppButton(
            "Start processing", "primary", self.theme, icon="play", icon_size=15
        )
        self.start_button.clicked.connect(self._start_processing)
        footer_layout.addWidget(self.start_button, 0, Qt.AlignmentFlag.AlignVCenter)
        file_card.body.addWidget(footer)
        self.body_layout.addWidget(file_card)

        safety = hbox(9)
        safety.addWidget(make_icon_label("lock", self.theme.token("text_muted"), 13))
        safety.addWidget(
            label(
                "DocPilot references file paths only. No document is opened for OCR in this UI preview.",
                "TableMeta",
            ),
            1,
        )
        self.body_layout.addLayout(safety)
        self.body_layout.addStretch(1)

    def _choose_files(self) -> None:
        paths, _filter = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files",
            "",
            "PDF documents (*.pdf)",
        )
        if paths:
            self._add_paths(paths)

    def _files_dropped(self, paths: list[str]) -> None:
        self._add_paths(paths)

    def _add_paths(self, paths: list[str]) -> None:
        result = self.state.add_files(paths)
        if result.added:
            count = len(result.added)
            message = f"{pluralize(count, 'file')} added to the demo queue. Originals untouched."
            tone = "success"
            if result.duplicates:
                message += f" {len(result.duplicates)} duplicate(s) ignored."
                tone = "warning"
            self.show_toast(message, tone)
            return
        if result.rejected:
            self.show_toast(
                "Only local PDF files can be added. No files were changed.",
                "warning",
            )
            return
        if result.duplicates:
            self.show_toast("Those PDFs are already in the queue.", "info")

    def _clear_files(self) -> None:
        if not self.state.selected_files:
            return
        self.state.clear_files()
        self.show_toast("Selection cleared. Original PDFs are untouched.", "info")

    def _start_processing(self) -> None:
        if not self.state.selected_files:
            return
        self.processing_requested.emit()

    def _refresh_files(self) -> None:
        files = list(self.state.selected_files)
        clear_layout(self.files_layout)
        if not files:
            empty = EmptyState(
                self.theme,
                "inbox",
                "No PDFs selected yet",
                "Drop files above or browse your computer. Selections appear here before the demo run.",
                tone="neutral",
            )
            self.files_layout.addWidget(empty)
            self.files_layout.addStretch(1)
            self.files_scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self.files_scroll.setFixedHeight(206)
        else:
            for file in files:
                row = SelectedFileRow(file, self.theme)
                row.remove_requested.connect(self.state.remove_file)
                self.files_layout.addWidget(row)
            self.files_layout.addStretch(1)
            self.files_scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            height = min(300, max(130, len(files) * 61 + 18))
            self.files_scroll.setFixedHeight(height)

        count = len(files)
        self.file_summary.setText(
            f"{pluralize(count, 'file')} in the demo queue"
            if count
            else "No files selected"
        )
        self.total_label.setText(
            f"{count} file{'s' if count != 1 else ''}  ·  {format_file_size(self.state.selected_files_size)}"
            if count
            else "0 files  ·  0 B"
        )
        self.start_button.setEnabled(count > 0)
        self.clear_button.setEnabled(count > 0)
        self.drop_zone.setMinimumHeight(236 if not count else 216)
