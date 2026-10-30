"""Dashboard page with statistics, overview, recent documents, and activity."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import DocumentRecord
from app.pages.base import ScrollablePage, page_intro
from app.theme.theme import ThemeManager
from app.utils import format_date
from app.widgets.buttons import AppButton
from app.widgets.cards import ActivityRow, Card, SectionHeader, StatCard, meta_block
from app.widgets.chart import ProcessingChart
from app.widgets.common import Badge, clear_layout, hbox, label, make_icon_label, vbox
from app.widgets.table import (
    category_cell_widget,
    configure_table,
    file_cell_widget,
    make_table,
    person_cell_widget,
    status_cell_widget,
    text_item,
)


class DashboardPage(ScrollablePage):
    def __init__(self, state, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self._build()
        self._connect_state()
        self.refresh_all()

    def _build(self) -> None:
        today = QDate.currentDate().toString("dddd, d MMMM")
        intro_right = hbox(8)
        intro_right.addWidget(label(today, "MutedLabel"))
        intro_right.addWidget(Badge("Demo data", "warning"))
        self.body_layout.addWidget(
            page_intro(
                "Workspace overview",
                "Here's what is happening in your local document library.",
                intro_right,
            )
        )

        # Stat cards -------------------------------------------------------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self.card_total = StatCard(
            self.theme, "documents", "Total documents", "0",
            "Across 3 local profiles", "accent",
        )
        self.card_processed = StatCard(
            self.theme, "check-circle", "Processed documents", "0",
            "Filed in the demo archive", "success",
        )
        self.card_pending = StatCard(
            self.theme, "clock", "Pending documents", "0",
            "Waiting for the demo queue", "warning",
        )
        self.card_review = StatCard(
            self.theme, "alert-triangle", "Needs review", "0",
            "Questions waiting for you", "danger",
        )
        for card in (self.card_total, self.card_processed, self.card_pending, self.card_review):
            stats_row.addWidget(card, 1)
        self.body_layout.addLayout(stats_row)

        # Main two-column dashboard ---------------------------------------
        columns = QHBoxLayout()
        columns.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(16)
        right = QVBoxLayout()
        right.setSpacing(16)

        # Processing overview
        overview = Card(self.theme, padding=18, spacing=8)
        overview_header = SectionHeader(
            "Processing overview",
            "Pages processed in the last seven days · sample metrics",
            Badge("This week", "accent"),
        )
        overview.body.addWidget(overview_header)
        summary = hbox(9)
        summary.addWidget(label("127", "BigMetric"))
        summary.addWidget(label("pages processed", "MutedLabel"), 0, Qt.AlignmentFlag.AlignBottom)
        summary.addStretch(1)
        summary.addWidget(Badge("↗ 18% vs last week", "success"))
        overview.body.addLayout(summary)
        self.chart = ProcessingChart(self.theme)
        overview.body.addWidget(self.chart)
        overview.setMinimumHeight(272)
        left.addWidget(overview)

        # Recent documents
        recent_card = Card(self.theme, padding=0, spacing=0)
        self.recent_table = make_table(
            ["Document", "Person", "Category", "Status", "Date"], row_height=50
        )
        self.recent_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recent_table.setFixedHeight(34 + 6 * 50)
        header = QWidget()
        header_layout = hbox(12, (18, 15, 18, 10), header)
        header_text = vbox(2)
        header_text.addWidget(label("Recent documents", "CardTitle"))
        header_text.addWidget(label("Latest items in the demo library", "CardSubtitle"))
        header_layout.addLayout(header_text, 1)
        view_all = AppButton("View all", "link", self.theme, icon="arrow-right", icon_size=13)
        view_all.clicked.connect(lambda: self.navigate_requested.emit("documents"))
        header_layout.addWidget(view_all, 0, Qt.AlignmentFlag.AlignVCenter)
        recent_card.body.addWidget(header)
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in ((1, 128), (2, 132), (3, 98), (4, 80)):
            self.recent_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.recent_table.setColumnWidth(column, width)
        self.recent_table.cellClicked.connect(self._open_recent)
        recent_card.body.addWidget(self.recent_table)
        left.addWidget(recent_card)
        left.addStretch(1)

        # Quick actions
        quick = Card(self.theme, padding=18, spacing=9)
        quick.body.addWidget(SectionHeader("Quick actions", "Demo shortcuts — no files are changed"))
        import_button = AppButton(
            "Import PDF files", "quick_primary", self.theme, icon="file-plus", icon_size=16
        )
        import_button.clicked.connect(lambda: self.navigate_requested.emit("scan"))
        processing_button = AppButton(
            "Start processing", "quick", self.theme, icon="play", icon_size=16
        )
        processing_button.clicked.connect(lambda: self.navigate_requested.emit("processing"))
        self.review_button = AppButton(
            "Open Review Center", "quick", self.theme, icon="review", icon_size=16
        )
        self.review_button.clicked.connect(lambda: self.navigate_requested.emit("review"))
        quick.body.addWidget(import_button)
        quick.body.addWidget(processing_button)
        quick.body.addWidget(self.review_button)
        quick.body.addSpacing(2)
        local_note = hbox(7)
        local_note.addWidget(make_icon_label("lock", self.theme.token("text_muted"), 13))
        local_note.addWidget(label("Everything stays on this computer", "TableMeta"), 1)
        quick.body.addLayout(local_note)
        right.addWidget(quick)

        # Activity
        activity = Card(self.theme, padding=18, spacing=10)
        activity.body.addWidget(
            SectionHeader("Recent activity", "Latest local demo events", Badge("Live demo", "neutral"))
        )
        self.activity_layout = vbox(0)
        activity.body.addLayout(self.activity_layout)
        activity.body.addStretch(1)
        activity.setMinimumHeight(330)
        right.addWidget(activity, 1)

        columns.addLayout(left, 5)
        columns.addLayout(right, 3)
        self.body_layout.addLayout(columns)
        self.body_layout.addStretch(1)

    def _connect_state(self) -> None:
        self.state.documents_changed.connect(self._refresh_document_views)
        self.state.reviews_changed.connect(self._refresh_stats)
        self.state.people_changed.connect(self._refresh_document_views)
        self.state.activity_changed.connect(self._refresh_activity)

    def refresh_all(self) -> None:
        self._refresh_stats()
        self._refresh_document_views()
        self._refresh_activity()

    def _refresh_stats(self) -> None:
        total = self.state.total_documents
        processed = self.state.processed_documents
        pending = self.state.pending_documents
        reviews = self.state.pending_review_count
        active_people = len([person for person in self.state.people if person.active])
        percentage = round(processed / total * 100) if total else 0
        self.card_total.update_value(total, f"Across {active_people} local profiles")
        self.card_processed.update_value(processed, f"{percentage}% of all documents")
        self.card_pending.update_value(pending, "Waiting for the demo queue")
        self.card_review.update_value(reviews, "Questions waiting for you")
        badge_text = f"Open Review Center  ·  {reviews}" if reviews else "Open Review Center"
        self.review_button.setText(badge_text)

    def _refresh_document_views(self) -> None:
        self._rebuild_recent()
        self._refresh_stats()

    def _rebuild_recent(self) -> None:
        docs = sorted(self.state.documents, key=lambda doc: doc.doc_date, reverse=True)[:6]
        self.recent_table.setRowCount(0)
        self.recent_table.setRowCount(len(docs))
        for row, doc in enumerate(docs):
            filename_item = text_item("")
            filename_item.setData(Qt.ItemDataRole.UserRole, doc.id)
            filename_item.setToolTip(doc.filename)
            self.recent_table.setItem(row, 0, filename_item)
            self.recent_table.setCellWidget(
                row, 0, file_cell_widget(self.theme, doc.filename, doc.institution)
            )
            person = self.state.person(doc.person_id)
            self.recent_table.setCellWidget(row, 1, person_cell_widget(person))
            self.recent_table.setCellWidget(
                row, 2, category_cell_widget(self.theme, doc.category)
            )
            self.recent_table.setCellWidget(row, 3, status_cell_widget(doc.status))
            date_item = text_item(format_date(doc.doc_date, short=True))
            self.recent_table.setItem(row, 4, date_item)
            self.recent_table.setRowHeight(row, 50)
        self.recent_table.setCursor(Qt.CursorShape.PointingHandCursor)

    def _open_recent(self, row: int, _column: int) -> None:
        item = self.recent_table.item(row, 0)
        if item:
            document_id = item.data(Qt.ItemDataRole.UserRole)
            if document_id:
                self.open_document_requested.emit(str(document_id))

    def _refresh_activity(self) -> None:
        clear_layout(self.activity_layout)
        for index, entry in enumerate(self.state.activity[:5]):
            self.activity_layout.addWidget(ActivityRow(self.theme, entry))
            if index < min(4, len(self.state.activity) - 1):
                divider = QFrame()
                divider.setObjectName("QueueDivider")
                divider.setFixedHeight(1)
                self.activity_layout.addWidget(divider)
