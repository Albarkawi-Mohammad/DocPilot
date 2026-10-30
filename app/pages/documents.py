"""Documents page with filtering, table, and a read-only details panel."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import DocumentRecord, DocumentStatus
from app.pages.base import Page, page_intro
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.utils import format_date, pluralize
from app.widgets.buttons import AppButton
from app.widgets.cards import Card, EmptyState, InfoBanner
from app.widgets.common import (
    Badge,
    PersonChip,
    clear_layout,
    category_color,
    category_icon,
    hbox,
    label,
    make_icon_label,
    vbox,
)
from app.widgets.icons import make_icon
from app.widgets.preview import DocumentPreview, PageThumbnail
from app.widgets.table import (
    category_cell_widget,
    file_cell_widget,
    make_table,
    person_cell_widget,
    status_cell_widget,
    text_item,
)


class DocumentsPage(Page):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self.selected_doc_id: Optional[str] = None
        self._preview_widget: Optional[DocumentPreview] = None
        self._preview_page_label: QWidget | None = None
        self._thumb_buttons: list[PageThumbnail] = []
        self._build()
        self._connect_state()
        self._refresh_filter_options()
        self._rebuild_table()

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        import_button = AppButton(
            "Import PDFs", "secondary", self.theme, icon="file-plus", icon_size=14
        )
        import_button.clicked.connect(lambda: self.navigate_requested.emit("scan"))
        intro_right = hbox(9)
        intro_right.addWidget(Badge("Read-only demo", "neutral"))
        intro_right.addWidget(import_button)
        self.root.addWidget(
            page_intro(
                "Document library",
                "Browse the sample library and inspect placeholder document previews.",
                intro_right,
            )
        )

        filter_card = Card(self.theme, padding=12, spacing=0)
        filter_layout = hbox(9, (4, 0, 4, 0))
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Search filename, institution, person…")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(210)
        self.search.addAction(
            make_icon("search", self.theme.token("text_muted"), 15),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        filter_layout.addWidget(self.search, 1)
        self.person_filter = QComboBox()
        self.person_filter.setMinimumWidth(132)
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(138)
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(122)
        filter_layout.addWidget(self.person_filter)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(self.status_filter)
        self.reset_button = AppButton("Reset", "ghost", self.theme, icon="refresh", icon_size=13)
        self.reset_button.clicked.connect(self._reset_filters)
        filter_layout.addWidget(self.reset_button)
        filter_card.body.addLayout(filter_layout)
        self.root.addWidget(filter_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(14)

        table_card = Card(self.theme, padding=0, spacing=0)
        table_card.setMinimumWidth(480)
        table_header = QWidget()
        table_header_layout = hbox(12, (18, 14, 18, 10), table_header)
        table_text = vbox(2)
        table_text.addWidget(label("All documents", "CardTitle"))
        self.table_count = label("0 documents", "CardSubtitle")
        table_text.addWidget(self.table_count)
        table_header_layout.addLayout(table_text, 1)
        table_header_layout.addWidget(
            Badge("Sample library", "neutral"), 0, Qt.AlignmentFlag.AlignVCenter
        )
        table_card.body.addWidget(table_header)

        self.table = make_table(
            ["Document", "Person", "Institution", "Category", "Date", "Status", "Pages"],
            row_height=54,
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in (
            (1, 112),
            (2, 118),
            (3, 132),
            (4, 78),
            (5, 106),
            (6, 46),
        ):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(column, width)
        self.table.itemSelectionChanged.connect(self._selection_changed)

        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self.table)
        empty_host = QWidget()
        empty_layout = vbox(0, (0, 0, 0, 0), empty_host)
        self.empty_state = EmptyState(
            self.theme,
            "search",
            "No documents match",
            "Try a different search term or reset the filters.",
            action_text="Clear filters",
            action_icon="refresh",
            tone="neutral",
        )
        self.empty_state.action_button.clicked.connect(self._reset_filters)
        empty_layout.addWidget(self.empty_state, 1)
        self.table_stack.addWidget(empty_host)
        table_card.body.addWidget(self.table_stack, 1)
        splitter.addWidget(table_card)

        # Details card ------------------------------------------------------
        self.details_card = Card(self.theme, padding=0, spacing=0)
        self.details_card.setMinimumWidth(318)
        details_header = QWidget()
        details_header_layout = hbox(10, (17, 14, 15, 10), details_header)
        details_header_layout.addWidget(label("Document details", "CardTitle"), 1)
        details_header_layout.addWidget(
            Badge("Demo preview", "neutral"), 0, Qt.AlignmentFlag.AlignVCenter
        )
        self.details_card.body.addWidget(details_header)

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_host = QWidget()
        self.details_body = vbox(11, (17, 2, 15, 16), self.details_host)
        self.details_scroll.setWidget(self.details_host)
        self.details_card.body.addWidget(self.details_scroll, 1)
        splitter.addWidget(self.details_card)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([820, 345])
        self.root.addWidget(splitter, 1)

    def _connect_state(self) -> None:
        self.state.documents_changed.connect(self._document_data_changed)
        self.state.people_changed.connect(self._people_changed)
        self.state.categories_changed.connect(self._categories_changed)
        self.search.textChanged.connect(self._rebuild_table)
        self.person_filter.currentIndexChanged.connect(self._rebuild_table)
        self.category_filter.currentIndexChanged.connect(self._rebuild_table)
        self.status_filter.currentIndexChanged.connect(self._rebuild_table)

    # ----------------------------------------------------------------- filters
    def _refresh_filter_options(self) -> None:
        current_person = self.person_filter.currentData() if self.person_filter.count() else "__all__"
        current_category = self.category_filter.currentData() if self.category_filter.count() else "__all__"
        current_status = self.status_filter.currentData() if self.status_filter.count() else "__all__"

        self.person_filter.blockSignals(True)
        self.category_filter.blockSignals(True)
        self.status_filter.blockSignals(True)
        self.person_filter.clear()
        self.person_filter.addItem("All people", "__all__")
        for person in self.state.people:
            self.person_filter.addItem(person.name, person.id)
        self.person_filter.addItem("Unassigned", "__none__")

        self.category_filter.clear()
        self.category_filter.addItem("All categories", "__all__")
        for category in self.state.categories:
            self.category_filter.addItem(category, category)

        self.status_filter.clear()
        self.status_filter.addItem("All statuses", "__all__")
        for status in DocumentStatus:
            self.status_filter.addItem(status.value, status.value)

        for combo, previous in (
            (self.person_filter, current_person),
            (self.category_filter, current_category),
            (self.status_filter, current_status),
        ):
            index = combo.findData(previous)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def _reset_filters(self) -> None:
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        for combo in (self.person_filter, self.category_filter, self.status_filter):
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self._rebuild_table()

    def _filtered_documents(self) -> list[DocumentRecord]:
        query = self.search.text().strip().casefold()
        person_id = self.person_filter.currentData()
        category = self.category_filter.currentData()
        status = self.status_filter.currentData()

        docs = list(self.state.documents)
        if person_id == "__none__":
            docs = [doc for doc in docs if not doc.person_id]
        elif person_id and person_id != "__all__":
            docs = [doc for doc in docs if doc.person_id == person_id]
        if category and category != "__all__":
            docs = [doc for doc in docs if doc.category == category]
        if status and status != "__all__":
            docs = [doc for doc in docs if doc.status.value == status]
        if query:
            docs = [
                doc
                for doc in docs
                if query
                in " ".join(
                    (
                        doc.filename,
                        doc.institution,
                        doc.category,
                        self.state.person_name(doc.person_id),
                        doc.status.value,
                        doc.doc_date,
                    )
                ).casefold()
            ]
        return sorted(docs, key=lambda doc: doc.doc_date, reverse=True)

    # ------------------------------------------------------------------- table
    def _rebuild_table(self) -> None:
        selected = self.selected_doc_id
        docs = self._filtered_documents()
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.table.setRowCount(len(docs))
        target_row = 0
        for row, doc in enumerate(docs):
            item = text_item("")
            item.setData(Qt.ItemDataRole.UserRole, doc.id)
            item.setToolTip(doc.filename)
            self.table.setItem(row, 0, item)
            self.table.setCellWidget(
                row, 0, file_cell_widget(self.theme, doc.filename, doc.source)
            )
            self.table.setCellWidget(
                row, 1, person_cell_widget(self.state.person(doc.person_id))
            )
            institution = text_item(doc.institution)
            institution.setToolTip(doc.institution)
            self.table.setItem(row, 2, institution)
            self.table.setCellWidget(row, 3, category_cell_widget(self.theme, doc.category))
            date = text_item(format_date(doc.doc_date, short=True))
            date.setToolTip(format_date(doc.doc_date))
            self.table.setItem(row, 4, date)
            self.table.setCellWidget(row, 5, status_cell_widget(doc.status))
            pages = text_item(str(doc.pages), Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, pages)
            self.table.setRowHeight(row, 54)
            if doc.id == selected:
                target_row = row

        self.table.blockSignals(False)
        self.table.setCursor(Qt.CursorShape.PointingHandCursor)
        total = self.state.total_documents
        if len(docs) == total:
            self.table_count.setText(pluralize(total, "document"))
        else:
            self.table_count.setText(f"{len(docs)} of {total} documents")

        if docs:
            self.table_stack.setCurrentIndex(0)
            self.table.selectRow(target_row)
            self.selected_doc_id = docs[target_row].id
            self._show_details(docs[target_row])
        else:
            self.table.clearSelection()
            self.selected_doc_id = None
            self.table_stack.setCurrentIndex(1)
            self._clear_details()

    def _selection_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        doc = self.state.document(str(doc_id))
        self.selected_doc_id = str(doc_id) if doc_id else None
        if doc:
            self._show_details(doc)

    def _document_data_changed(self) -> None:
        # If the selected document disappeared, fall back to the first result.
        if self.selected_doc_id and not self.state.document(self.selected_doc_id):
            self.selected_doc_id = None
        self._rebuild_table()

    def _people_changed(self) -> None:
        self._refresh_filter_options()
        self._rebuild_table()

    def _categories_changed(self) -> None:
        self._refresh_filter_options()
        self._rebuild_table()

    def select_document(self, document_id: str) -> None:
        self._reset_filters()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == document_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                self.selected_doc_id = document_id
                doc = self.state.document(document_id)
                if doc:
                    self._show_details(doc)
                return

    # ----------------------------------------------------------------- details
    def _clear_details(self) -> None:
        clear_layout(self.details_body)
        self.details_body.addWidget(
            EmptyState(
                self.theme,
                "file-text",
                "No document selected",
                "Choose a document in the table to inspect its demo metadata and page preview.",
                tone="neutral",
            ),
            1,
        )
        self._preview_widget = None
        self._thumb_buttons = []

    def _show_details(self, doc: DocumentRecord) -> None:
        clear_layout(self.details_body)
        self._thumb_buttons = []

        preview_frame = QFrame()
        preview_frame.setObjectName("PreviewStage")
        preview_layout = vbox(6, (10, 10, 10, 10), preview_frame)
        preview = DocumentPreview(self.theme)
        preview.set_document(
            filename=doc.filename,
            category=doc.category,
            pages=doc.pages,
            seed=doc.preview_seed,
        )
        preview.setFixedHeight(238)
        self._preview_widget = preview
        preview_layout.addWidget(preview)
        page_caption = hbox(6)
        page_caption.addWidget(make_icon_label("eye", self.theme.token("text_muted"), 12))
        self._preview_page_label = label(f"Page 1 of {doc.pages}", "PageNumber")
        page_caption.addWidget(self._preview_page_label, 1)
        page_caption.addWidget(label("Placeholder pages", "PageNumber"))
        preview_layout.addLayout(page_caption)
        self.details_body.addWidget(preview_frame)

        thumbnails = hbox(6)
        for index in range(min(doc.pages, 4)):
            button = PageThumbnail(self.theme, index + 1)
            button.setChecked(index == 0)
            button.clicked.connect(
                lambda _checked=False, page=index: self._thumbnail_clicked(page)
            )
            self._thumb_buttons.append(button)
            thumbnails.addWidget(button)
        if doc.pages > 4:
            thumbnails.addWidget(label(f"+{doc.pages - 4}", "PageNumber"))
        thumbnails.addStretch(1)
        self.details_body.addLayout(thumbnails)

        filename = label(doc.filename, "FileName", wrap=True, selectable=True)
        filename.setStyleSheet("font-size: 13px;")
        self.details_body.addWidget(filename)
        institution_line = label(doc.institution, "MutedLabel")
        self.details_body.addWidget(institution_line)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(
            self._field("ASSIGNED PERSON", PersonChip(self.state.person(doc.person_id), avatar_size=23)),
            0, 0, 1, 2,
        )
        category_widget = QWidget()
        category_layout = hbox(6, (0, 0, 0, 0), category_widget)
        category_layout.addWidget(
            make_icon_label(category_icon(doc.category), category_color(doc.category), 13)
        )
        category_layout.addWidget(label(doc.category, "FieldValue"))
        category_layout.addStretch(1)
        grid.addWidget(self._field("CATEGORY", category_widget), 1, 0)
        grid.addWidget(self._field("INSTITUTION", label(doc.institution, "FieldValue")), 1, 1)
        grid.addWidget(self._field("DOCUMENT DATE", label(format_date(doc.doc_date), "FieldValue")), 2, 0)
        grid.addWidget(self._field("PAGES", label(str(doc.pages), "FieldValue")), 2, 1)
        grid.addWidget(self._field("STATUS", status_cell_widget(doc.status)), 3, 0)
        confidence = Badge(f"{round(doc.confidence * 100)}% demo confidence", "accent")
        grid.addWidget(self._field("MATCH", confidence), 3, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.details_body.addLayout(grid)

        if doc.note:
            self.details_body.addWidget(
                InfoBanner(
                    self.theme,
                    icon="info",
                    title="Why this is in the demo review flow",
                    text=doc.note,
                    tone="warning" if doc.status == DocumentStatus.NEEDS_REVIEW else "neutral",
                )
            )

        if doc.status == DocumentStatus.NEEDS_REVIEW:
            action = AppButton(
                "Open in Review Center", "primary", self.theme, icon="review", icon_size=14
            )
            action.clicked.connect(lambda: self.navigate_requested.emit("review"))
        else:
            action = AppButton(
                "View sample preview", "secondary", self.theme, icon="eye", icon_size=14
            )
            action.clicked.connect(
                lambda: self.show_toast(
                    "Placeholder preview only. No original PDF is opened in this UI demo.",
                    "info",
                )
            )
        self.details_body.addWidget(action)
        note = hbox(6)
        note.addWidget(make_icon_label("shield-check", self.theme.token("text_muted"), 12))
        note.addWidget(
            label("Originals are never renamed, moved, or modified.", "TableMeta", wrap=True),
            1,
        )
        self.details_body.addLayout(note)
        self.details_body.addStretch(1)

    def _field(self, title: str, value_widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = vbox(2, (0, 0, 0, 0), wrapper)
        layout.addWidget(label(title, "FieldLabel"))
        layout.addWidget(value_widget)
        return wrapper

    def _thumbnail_clicked(self, index: int) -> None:
        for position, button in enumerate(self._thumb_buttons):
            button.setChecked(position == index)
        if self._preview_widget:
            self._preview_widget.set_page(index)
        if self._preview_page_label:
            total = self._preview_widget.pages if self._preview_widget else index + 1
            self._preview_page_label.setText(f"Page {index + 1} of {total}")
