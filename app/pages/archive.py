"""Logical archive — browse filed demo documents by person and category.

The archive in this preview is a view over in-memory sample records. No folder
is created, no file is moved, and no original document is read or changed.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from app.models.entities import DocumentRecord, DocumentStatus, Person
from app.pages.base import Page, page_intro
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.utils import format_date, pluralize
from app.widgets.buttons import AppButton
from app.widgets.cards import Card, EmptyState, InfoBanner
from app.widgets.common import (
    Badge,
    IconTile,
    PersonChip,
    category_color,
    category_icon,
    clear_layout,
    hbox,
    label,
    make_icon_label,
    repolish,
    status_badge,
    vbox,
)
from app.widgets.icons import make_icon
from app.widgets.preview import DocumentPreview
from app.widgets.table import make_mouse_transparent

FILED_STATUSES = (DocumentStatus.PROCESSED, DocumentStatus.ARCHIVED)
_TREE_KEY_ROLE = Qt.ItemDataRole.UserRole + 1


class ArchiveDocRow(QFrame):
    """Compact, clickable archive list row with demo metadata only."""

    clicked = Signal(str)

    def __init__(
        self,
        theme: ThemeManager,
        document: DocumentRecord,
        person: Optional[Person],
        selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.document = document
        self.setObjectName("ArchiveDocRow")
        self.setProperty("selected", selected)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(document.filename)

        layout = hbox(10, (12, 9, 12, 9), self)
        layout.addWidget(
            IconTile(theme, category_icon(document.category), "neutral", 34, 16),
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        content = vbox(3)
        top = hbox(7)
        name = label(document.filename, "FileName")
        name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        name.setToolTip(document.filename)
        top.addWidget(name, 1)
        top.addWidget(status_badge(document.status), 0, Qt.AlignmentFlag.AlignVCenter)
        content.addLayout(top)

        meta = hbox(5)
        institution = label(document.institution, "FileSub")
        institution.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        institution.setToolTip(document.institution)
        meta.addWidget(institution, 1)
        meta.addWidget(label("·", "FileSub"))
        meta.addWidget(label(format_date(document.doc_date, short=True), "FileSub"))
        meta.addWidget(label("·", "FileSub"))
        meta.addWidget(
            make_icon_label(
                category_icon(document.category),
                category_color(document.category),
                11,
            )
        )
        category = label(document.category, "FileSub")
        category.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        category.setToolTip(document.category)
        meta.addWidget(category)
        meta.addWidget(label("·", "FileSub"))
        meta.addWidget(label(f"{document.pages}p", "FileSub"))
        content.addLayout(meta)
        layout.addLayout(content, 1)

        owner = person.name if person else "Unassigned"
        self.setAccessibleName(
            f"{document.filename}, {owner}, {document.category}, "
            f"{format_date(document.doc_date)}"
        )
        make_mouse_transparent(self)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        repolish(self)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.document.id)
        super().mouseReleaseEvent(event)


class ArchivePage(Page):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self._selected_key = "all"
        self._scope: dict[str, Optional[str]] = {
            "kind": "all",
            "person_id": None,
            "category": None,
            "list_label": "All people",
        }
        self._tree_scopes: dict[str, dict] = {}
        self._tree_items: dict[str, QTreeWidgetItem] = {}
        self._rows: dict[str, ArchiveDocRow] = {}
        self._preview_widget: DocumentPreview | None = None
        self.selected_doc_id: Optional[str] = None

        self._build()
        self._connect_state()
        self._rebuild_tree()
        self._refresh_list()

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        intro_right = hbox(8)
        intro_right.addWidget(Badge("Logical archive", "accent"))
        intro_right.addWidget(Badge("Read-only demo", "neutral"))
        self.root.addWidget(
            page_intro(
                "Your local archive",
                "Browse filed demo documents by person and category. This is a view — not a real folder structure.",
                intro_right,
            )
        )

        self.root.addWidget(
            InfoBanner(
                self.theme,
                icon="shield-check",
                title="No files are moved or reorganized",
                text=(
                    "Archive folders exist only in this interface preview. Only demo documents "
                    "with the status Processed or Archived appear here."
                ),
                tone="accent",
            )
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(14)

        splitter.addWidget(self._build_tree_card())
        splitter.addWidget(self._build_list_card())
        splitter.addWidget(self._build_preview_card())

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([260, 360, 470])
        self.root.addWidget(splitter, 1)

    def _build_tree_card(self) -> Card:
        card = Card(self.theme, padding=0, spacing=0)
        card.setMinimumWidth(222)
        card.setMaximumWidth(306)

        header = QWidget()
        header_layout = hbox(10, (16, 14, 16, 8), header)
        text = vbox(2)
        text.addWidget(label("Archive tree", "CardTitle"))
        self.tree_subtitle = label("Filed demo documents", "CardSubtitle")
        text.addWidget(self.tree_subtitle)
        header_layout.addLayout(text, 1)
        header_layout.addWidget(Badge("Logical", "neutral"), 0, Qt.AlignmentFlag.AlignTop)
        card.body.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree.itemSelectionChanged.connect(self._tree_selection_changed)
        card.body.addWidget(self.tree, 1)

        footer = QWidget()
        footer_layout = hbox(7, (16, 8, 14, 13), footer)
        footer_layout.addWidget(
            make_icon_label("sparkles", self.theme.token("text_muted"), 12)
        )
        footer_layout.addWidget(
            label(
                "Categories appear dynamically as documents are filed.",
                "TableMeta",
                wrap=True,
            ),
            1,
        )
        card.body.addWidget(footer)
        return card

    def _build_list_card(self) -> Card:
        card = Card(self.theme, padding=0, spacing=0)
        card.setMinimumWidth(300)

        header = QWidget()
        header_layout = hbox(12, (17, 14, 17, 8), header)
        text = vbox(2)
        text.addWidget(label("Filed documents", "CardTitle"))
        self.list_subtitle = label("All people · 0 documents", "CardSubtitle")
        text.addWidget(self.list_subtitle)
        header_layout.addLayout(text, 1)
        header_layout.addWidget(Badge("Sample data", "neutral"), 0, Qt.AlignmentFlag.AlignTop)
        card.body.addWidget(header)

        search_wrap = QWidget()
        search_layout = hbox(0, (15, 2, 15, 9), search_wrap)
        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Search filename, institution, category…")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(
            make_icon("search", self.theme.token("text_muted"), 15),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.textChanged.connect(self._refresh_list)
        search_layout.addWidget(self.search)
        card.body.addWidget(search_wrap)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_host = QWidget()
        self.list_layout = vbox(8, (13, 2, 13, 11), self.list_host)
        self.list_scroll.setWidget(self.list_host)
        card.body.addWidget(self.list_scroll, 1)

        footer = QWidget()
        footer_layout = hbox(7, (17, 8, 15, 13), footer)
        footer_layout.addWidget(
            make_icon_label("archive", self.theme.token("text_muted"), 12)
        )
        footer_layout.addWidget(
            label("View only · originals stay where they are.", "TableMeta"), 1
        )
        card.body.addWidget(footer)
        return card

    def _build_preview_card(self) -> Card:
        card = Card(self.theme, padding=0, spacing=0)
        card.setMinimumWidth(296)

        header = QWidget()
        header_layout = hbox(10, (18, 14, 16, 8), header)
        header_layout.addWidget(label("Preview & metadata", "CardTitle"), 1)
        header_layout.addWidget(Badge("Sample preview", "neutral"), 0, Qt.AlignmentFlag.AlignTop)
        card.body.addWidget(header)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.preview_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.preview_host = QWidget()
        self.preview_body = vbox(11, (18, 2, 16, 16), self.preview_host)
        self.preview_scroll.setWidget(self.preview_host)
        card.body.addWidget(self.preview_scroll, 1)
        return card

    # ------------------------------------------------------------------ state
    def _connect_state(self) -> None:
        self.state.documents_changed.connect(self._refresh_all)
        self.state.people_changed.connect(self._refresh_all)
        self.state.categories_changed.connect(self._refresh_all)
        self.theme.theme_changed.connect(self._theme_changed)

    def on_activated(self) -> None:
        self._refresh_all()

    def _theme_changed(self, _mode: str) -> None:
        # Icons are rendered as pixmaps, so rebuild with the new token colors.
        QTimer.singleShot(0, self._refresh_all)

    # ------------------------------------------------------------------- tree
    def _filed_documents(self) -> list[DocumentRecord]:
        return [
            document
            for document in self.state.documents
            if document.status in FILED_STATUSES
        ]

    def _category_sort_key(self, category: str) -> tuple[int, str]:
        try:
            order = self.state.categories.index(category)
        except ValueError:
            order = len(self.state.categories)
        return order, category.casefold()

    def _add_tree_scope(
        self,
        key: str,
        parent: QTreeWidgetItem | None,
        text: str,
        icon_name: str,
        icon_color: str,
        scope: dict,
        *,
        top_level_bold: bool = False,
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([text])
        item.setIcon(0, make_icon(icon_name, icon_color, 15))
        item.setData(0, _TREE_KEY_ROLE, key)
        if top_level_bold:
            font = QFont(item.font(0))
            font.setWeight(QFont.Weight.DemiBold)
            item.setFont(0, font)
        self._tree_scopes[key] = scope
        self._tree_items[key] = item
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        return item

    def _rebuild_tree(self) -> None:
        filed = self._filed_documents()
        self.tree.blockSignals(True)
        self.tree.clear()
        self._tree_scopes = {}
        self._tree_items = {}

        all_scope = {
            "kind": "all",
            "person_id": None,
            "category": None,
            "list_label": "All people",
        }
        self._add_tree_scope(
            "all",
            None,
            f"All filed documents  ({len(filed)})",
            "archive",
            self.theme.token("accent"),
            all_scope,
            top_level_bold=True,
        )

        for person in self.state.people:
            person_docs = [doc for doc in filed if doc.person_id == person.id]
            person_scope = {
                "kind": "person",
                "person_id": person.id,
                "category": None,
                "list_label": person.name,
            }
            key = f"person:{person.id}"
            person_item = self._add_tree_scope(
                key,
                None,
                f"{person.name}  ({len(person_docs)})",
                "user",
                person.color,
                person_scope,
                top_level_bold=True,
            )
            category_counts: dict[str, int] = {}
            for document in person_docs:
                category_counts[document.category] = (
                    category_counts.get(document.category, 0) + 1
                )
            for category in sorted(category_counts, key=self._category_sort_key):
                category_key = f"category:{person.id}:{category}"
                self._add_tree_scope(
                    category_key,
                    person_item,
                    f"{category}  ({category_counts[category]})",
                    category_icon(category),
                    category_color(category),
                    {
                        "kind": "category",
                        "person_id": person.id,
                        "category": category,
                        "list_label": f"{person.name} / {category}",
                    },
                )
            person_item.setExpanded(True)

        unassigned = [doc for doc in filed if not doc.person_id]
        if unassigned:
            unassigned_item = self._add_tree_scope(
                "unassigned",
                None,
                f"Unassigned  ({len(unassigned)})",
                "user",
                self.theme.token("text_muted"),
                {
                    "kind": "unassigned",
                    "person_id": None,
                    "category": None,
                    "list_label": "Unassigned",
                },
                top_level_bold=True,
            )
            unassigned_counts: dict[str, int] = {}
            for document in unassigned:
                unassigned_counts[document.category] = (
                    unassigned_counts.get(document.category, 0) + 1
                )
            for category in sorted(unassigned_counts, key=self._category_sort_key):
                category_key = f"unassigned-category:{category}"
                self._add_tree_scope(
                    category_key,
                    unassigned_item,
                    f"{category}  ({unassigned_counts[category]})",
                    category_icon(category),
                    category_color(category),
                    {
                        "kind": "unassigned_category",
                        "person_id": None,
                        "category": category,
                        "list_label": f"Unassigned / {category}",
                    },
                )
            unassigned_item.setExpanded(True)

        if self._selected_key not in self._tree_items:
            self._selected_key = "all"
        target = self._tree_items.get(self._selected_key, self._tree_items["all"])
        self.tree.setCurrentItem(target)
        self.tree.scrollToItem(target)
        self.tree.blockSignals(False)

        self._scope = self._tree_scopes.get(self._selected_key, all_scope)
        self.tree_subtitle.setText(
            f"{pluralize(len(filed), 'filed document')}  ·  {len(self.state.people)} profiles"
        )

    def _tree_selection_changed(self) -> None:
        item = self.tree.currentItem()
        if item is None:
            return
        key = str(item.data(0, _TREE_KEY_ROLE) or "all")
        scope = self._tree_scopes.get(key)
        if scope is None:
            return
        self._selected_key = key
        self._scope = scope
        self._refresh_list()

    # ------------------------------------------------------------------- list
    def _visible_documents(self) -> list[DocumentRecord]:
        docs = self._filed_documents()
        kind = self._scope.get("kind")
        person_id = self._scope.get("person_id")
        category = self._scope.get("category")

        if kind == "person":
            docs = [doc for doc in docs if doc.person_id == person_id]
        elif kind == "category":
            docs = [
                doc
                for doc in docs
                if doc.person_id == person_id and doc.category == category
            ]
        elif kind == "unassigned":
            docs = [doc for doc in docs if not doc.person_id]
        elif kind == "unassigned_category":
            docs = [
                doc
                for doc in docs
                if not doc.person_id and doc.category == category
            ]

        query = self.search.text().strip().casefold()
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
                        doc.doc_date,
                    )
                ).casefold()
            ]
        return sorted(docs, key=lambda doc: (doc.doc_date, doc.filename), reverse=True)

    def _refresh_list(self) -> None:
        docs = self._visible_documents()
        previous_selection = self.selected_doc_id
        self._rows = {}
        clear_layout(self.list_layout)

        self.list_subtitle.setText(
            f"{self._scope.get('list_label', 'All people')}  ·  "
            f"{pluralize(len(docs), 'document')}"
        )

        if not docs:
            query = self.search.text().strip()
            empty = EmptyState(
                self.theme,
                "search" if query else "archive",
                "No filed documents match" if query else "Nothing filed here yet",
                (
                    "Try a different search term."
                    if query
                    else "Processed or archived demo documents will appear in this logical folder."
                ),
                action_text="Clear search" if query else None,
                action_icon="refresh",
                tone="neutral",
            )
            if empty.action_button is not None:
                empty.action_button.clicked.connect(self._clear_search)
            self.list_layout.addWidget(empty)
            self.list_layout.addStretch(1)
            self._clear_preview()
            self.selected_doc_id = None
            return

        if previous_selection not in {doc.id for doc in docs}:
            previous_selection = docs[0].id

        for document in docs:
            row = ArchiveDocRow(
                self.theme,
                document,
                self.state.person(document.person_id),
                selected=document.id == previous_selection,
            )
            row.clicked.connect(self._select_document)
            self._rows[document.id] = row
            self.list_layout.addWidget(row)
        self.list_layout.addStretch(1)

        self.selected_doc_id = previous_selection
        document = self.state.document(previous_selection)
        if document is not None:
            self._render_preview(document)

    def _clear_search(self) -> None:
        self.search.clear()

    def _select_document(self, document_id: str) -> None:
        document = self.state.document(document_id)
        if document is None:
            return
        self.selected_doc_id = document_id
        for doc_id, row in self._rows.items():
            row.set_selected(doc_id == document_id)
        self._render_preview(document)

    # ---------------------------------------------------------------- preview
    def _clear_preview(self) -> None:
        clear_layout(self.preview_body)
        self._preview_widget = None
        self.preview_body.addWidget(
            EmptyState(
                self.theme,
                "eye",
                "No document selected",
                "Choose a filed document to inspect its sample page and demo metadata.",
                tone="neutral",
            ),
            1,
        )

    def _render_preview(self, document: DocumentRecord) -> None:
        clear_layout(self.preview_body)
        self._preview_widget = None

        preview_frame = QFrame()
        preview_frame.setObjectName("PreviewStage")
        preview_layout = vbox(6, (10, 10, 10, 10), preview_frame)
        preview = DocumentPreview(self.theme)
        preview.set_document(
            filename=document.filename,
            category=document.category,
            pages=document.pages,
            seed=document.preview_seed,
        )
        preview.setFixedHeight(252)
        self._preview_widget = preview
        preview_layout.addWidget(preview)
        caption = hbox(6)
        caption.addWidget(make_icon_label("eye", self.theme.token("text_muted"), 12))
        caption.addWidget(label(f"Page 1 of {document.pages}", "PageNumber"), 1)
        caption.addWidget(label("Placeholder preview", "PageNumber"))
        preview_layout.addLayout(caption)
        self.preview_body.addWidget(preview_frame)

        filename = label(document.filename, "FileName", wrap=True, selectable=True)
        filename.setStyleSheet("font-size: 13px;")
        self.preview_body.addWidget(filename)
        self.preview_body.addWidget(label(document.institution, "MutedLabel"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(
            self._field(
                "ASSIGNED PERSON",
                PersonChip(self.state.person(document.person_id), avatar_size=23),
            ),
            0,
            0,
            1,
            2,
        )

        category_widget = QWidget()
        category_layout = hbox(6, (0, 0, 0, 0), category_widget)
        category_layout.addWidget(
            make_icon_label(
                category_icon(document.category),
                category_color(document.category),
                13,
            )
        )
        category_layout.addWidget(label(document.category, "FieldValue"))
        category_layout.addStretch(1)
        grid.addWidget(self._field("CATEGORY", category_widget), 1, 0)
        grid.addWidget(
            self._field("DOCUMENT DATE", label(format_date(document.doc_date), "FieldValue")),
            1,
            1,
        )
        grid.addWidget(
            self._field("PAGES", label(str(document.pages), "FieldValue")), 2, 0
        )
        grid.addWidget(self._field("STATUS", status_badge(document.status)), 2, 1)
        grid.addWidget(
            self._field(
                "CONFIDENCE",
                Badge(f"{round(document.confidence * 100)}% demo", "accent"),
            ),
            3,
            0,
        )
        grid.addWidget(
            self._field("SOURCE", label(document.source, "FieldValue")), 3, 1
        )
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.preview_body.addLayout(grid)

        self.preview_body.addWidget(
            InfoBanner(
                self.theme,
                icon="archive",
                title="Logical archive entry",
                text=(
                    "This record is shown as filed in the demo library. "
                    "No folder was created and no original PDF was moved."
                ),
                tone="neutral",
            )
        )

        open_button = AppButton(
            "Open in Documents", "secondary", self.theme, icon="documents", icon_size=14
        )
        open_button.clicked.connect(
            lambda _checked=False, doc_id=document.id: self.open_document_requested.emit(doc_id)
        )
        self.preview_body.addWidget(open_button)

        safety = hbox(6)
        safety.addWidget(
            make_icon_label("shield-check", self.theme.token("text_muted"), 12)
        )
        safety.addWidget(
            label(
                "Read-only: originals are never renamed, moved, or deleted.",
                "TableMeta",
                wrap=True,
            ),
            1,
        )
        self.preview_body.addLayout(safety)
        self.preview_body.addStretch(1)

    def _field(self, title: str, value_widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = vbox(2, (0, 0, 0, 0), wrapper)
        layout.addWidget(label(title, "FieldLabel"))
        layout.addWidget(value_widget)
        return wrapper

    # ------------------------------------------------------------------ helpers
    def select_document(self, document_id: str) -> bool:
        document = self.state.document(document_id)
        if document is None or document.status not in FILED_STATUSES:
            return False
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self._selected_key = "all"
        self._rebuild_tree()
        self.selected_doc_id = document_id
        self._refresh_list()
        return True

    def _refresh_all(self) -> None:
        self._rebuild_tree()
        self._refresh_list()
