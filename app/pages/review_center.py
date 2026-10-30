"""Review Center with person, page-boundary, and category demo decisions."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import DocumentRecord, ReviewItem, ReviewKind, ReviewStatus
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
    clear_layout,
    category_color,
    category_icon,
    hbox,
    label,
    make_icon_label,
    repolish,
    vbox,
)
from app.widgets.icons import make_avatar_icon, make_icon
from app.widgets.preview import DocumentPreview


REVIEW_META = {
    ReviewKind.PERSON: ("UNKNOWN PERSON", "user", "warning", "Choose an owner"),
    ReviewKind.SEPARATION: ("UNCERTAIN SEPARATION", "documents", "info", "Set a document boundary"),
    ReviewKind.CATEGORY: ("UNKNOWN CATEGORY", "folder", "purple", "Choose a category"),
}


class ReviewQueueItem(QFrame):
    clicked = Signal(str)

    def __init__(
        self,
        item: ReviewItem,
        theme: ThemeManager,
        selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName("ReviewQueueItem")
        self.setProperty("selected", selected)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        type_text, icon_name, tone, _ = REVIEW_META[item.kind]
        layout = hbox(10, (11, 10, 11, 10), self)
        layout.addWidget(IconTile(theme, icon_name, tone, 32, 16), 0, Qt.AlignmentFlag.AlignTop)
        content = vbox(2)
        top = hbox(8)
        top.addWidget(label(type_text, "QueueType"), 1)
        resolved = item.status == ReviewStatus.RESOLVED
        top.addWidget(
            Badge("Resolved", "success") if resolved else Badge("Pending", "warning"),
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        content.addLayout(top)
        title = label(item.filename, "QueueTitle")
        title.setToolTip(item.filename)
        content.addWidget(title)
        pages = max(1, len(item.page_labels))
        meta_text = f"{pluralize(pages, 'page')}  ·  {item.submitted_at}"
        if resolved and item.decision:
            meta_text = f"Decision: {item.decision}"
        meta = label(meta_text, "QueueDecision" if resolved else "QueueMeta")
        meta.setWordWrap(True)
        content.addWidget(meta)
        layout.addLayout(content, 1)
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        repolish(self)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item.id)
        super().mouseReleaseEvent(event)


class ReviewCenterPage(Page):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self.current_review_id: Optional[str] = None
        self._choice_group: QButtonGroup | None = None
        self._choice_map: dict[int, tuple[str, str]] = {}
        self._custom_category: QLineEdit | None = None
        self._validation_label: QWidget | None = None
        self._queue_items: dict[str, ReviewQueueItem] = {}
        self._build()
        self._refresh_queue()
        pending = self.state.pending_reviews()
        if pending:
            self._select_review(pending[0].id)
        else:
            self.current_review_id = None
            self._render_current()

    def on_activated(self) -> None:
        pending = self.state.pending_reviews()
        if self.current_review_id is None and pending:
            self.current_review_id = pending[0].id
        self._refresh_queue()
        self._render_current()

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        intro_right = hbox(8)
        intro_right.addWidget(Badge("Demo decisions only", "warning"))
        self.root.addWidget(
            page_intro(
                "Decisions that need you",
                "DocPilot only asks when a safe automatic decision is not possible.",
                intro_right,
            )
        )

        main = hbox(16)
        queue_card = Card(self.theme, padding=0, spacing=0)
        queue_card.setFixedWidth(326)
        queue_header = QWidget()
        queue_header_layout = hbox(10, (16, 14, 16, 10), queue_header)
        queue_text = vbox(2)
        queue_text.addWidget(label("Review queue", "CardTitle"))
        self.queue_subtitle = label("No pending reviews", "CardSubtitle")
        queue_text.addWidget(self.queue_subtitle)
        queue_header_layout.addLayout(queue_text, 1)
        self.pending_badge = Badge("0", "warning")
        queue_header_layout.addWidget(self.pending_badge, 0, Qt.AlignmentFlag.AlignTop)
        queue_card.body.addWidget(queue_header)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_host = QWidget()
        self.queue_layout = vbox(8, (12, 2, 12, 8), self.queue_host)
        self.queue_scroll.setWidget(self.queue_host)
        queue_card.body.addWidget(self.queue_scroll, 1)

        queue_footer = QWidget()
        queue_footer_layout = hbox(8, (14, 8, 14, 12), queue_footer)
        queue_footer_layout.addWidget(
            make_icon_label("shield-check", self.theme.token("text_muted"), 12)
        )
        queue_footer_layout.addWidget(label("No real documents change", "TableMeta"), 1)
        reset_button = AppButton(
            "Reset demo", "link", self.theme, icon="rotate", icon_size=12
        )
        reset_button.clicked.connect(self._reset_demo)
        queue_footer_layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignVCenter)
        queue_card.body.addWidget(queue_footer)
        main.addWidget(queue_card, 0)

        self.review_card = Card(self.theme, padding=0, spacing=0)
        self.review_card.setMinimumWidth(500)
        self.review_scroll = QScrollArea()
        self.review_scroll.setWidgetResizable(True)
        self.review_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.review_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.review_host = QWidget()
        self.review_body = vbox(13, (22, 18, 22, 18), self.review_host)
        self.review_scroll.setWidget(self.review_host)
        self.review_card.body.addWidget(self.review_scroll, 1)

        self.footer = QFrame()
        self.footer.setObjectName("ReviewFooter")
        self.footer_layout = vbox(6, (22, 10, 22, 12), self.footer)
        self.review_card.body.addWidget(self.footer)
        main.addWidget(self.review_card, 1)

        self.root.addLayout(main, 1)

    # ------------------------------------------------------------------- queue
    def _refresh_queue(self) -> None:
        clear_layout(self.queue_layout)
        self._queue_items = {}
        pending = self.state.pending_reviews()
        resolved_count = len(self.state.reviews) - len(pending)
        self.pending_badge.setText(str(len(pending)))
        self.pending_badge.set_tone("warning" if pending else "success")
        self.queue_subtitle.setText(
            f"{pluralize(len(pending), 'pending review')}  ·  {resolved_count} resolved"
        )
        ordered = sorted(
            self.state.reviews,
            key=lambda review: 0 if review.status == ReviewStatus.PENDING else 1,
        )
        if not ordered:
            empty = EmptyState(
                self.theme,
                "review",
                "Nothing in the queue",
                "Questions will appear here only when a decision is uncertain.",
                tone="neutral",
            )
            self.queue_layout.addWidget(empty)
            self.queue_layout.addStretch(1)
            return
        for item in ordered:
            widget = ReviewQueueItem(
                item,
                self.theme,
                selected=item.id == self.current_review_id,
            )
            widget.clicked.connect(self._select_review)
            self._queue_items[item.id] = widget
            self.queue_layout.addWidget(widget)
        self.queue_layout.addStretch(1)

    def _update_queue_selection(self) -> None:
        for review_id, widget in self._queue_items.items():
            widget.set_selected(review_id == self.current_review_id)

    def _select_review(self, review_id: str) -> None:
        self.current_review_id = review_id
        self._update_queue_selection()
        self._render_current()

    # ------------------------------------------------------------------ render
    def _render_current(self) -> None:
        clear_layout(self.review_body)
        clear_layout(self.footer_layout)
        self._choice_group = None
        self._choice_map = {}
        self._custom_category = None
        self._validation_label = None
        self.footer.setVisible(True)

        review = self.state.review(self.current_review_id or "")
        if review is None:
            self._render_caught_up()
            return

        type_text, icon_name, tone, _ = REVIEW_META[review.kind]
        resolved = review.status == ReviewStatus.RESOLVED
        top = hbox(8)
        top.addWidget(Badge(type_text.title(), tone))
        top.addWidget(label(f"Submitted {review.submitted_at}", "TableMeta"))
        top.addStretch(1)
        if review.confidence is not None:
            top.addWidget(
                Badge(
                    f"{round(review.confidence * 100)}% demo confidence",
                    "warning" if review.confidence < 0.6 else "success",
                )
            )
        self.review_body.addLayout(top)

        self.review_body.addWidget(label(review.title, "ReviewQuestion", wrap=True))
        self.review_body.addWidget(label(review.description, "ReviewDescription", wrap=True))

        if resolved:
            self.review_body.addWidget(
                InfoBanner(
                    self.theme,
                    icon="check-circle",
                    title="Decision saved",
                    text=(
                        f"{review.decision or 'Reviewed'} — applied to in-memory demo data only. "
                        "No source document was changed."
                    ),
                    tone="success",
                )
            )

        if review.kind == ReviewKind.PERSON:
            self._render_person_body(review, resolved)
        elif review.kind == ReviewKind.SEPARATION:
            self._render_separation_body(review, resolved)
        else:
            self._render_category_body(review, resolved)

        if resolved:
            self._render_resolved_footer(review)
        else:
            self._render_pending_footer(review)

    # ------------------------------------------------------------- preview blobs
    def _preview_panel(
        self,
        review: ReviewItem,
        page_index: int = 0,
        *,
        height: int = 250,
    ) -> QFrame:
        doc = self.state.document(review.document_id)
        category = doc.category if doc else "Other"
        if review.kind == ReviewKind.CATEGORY and review.status == ReviewStatus.PENDING:
            category = "Uncategorised"
        pages = max(1, len(review.page_labels), doc.pages if doc else 1)
        frame = QFrame()
        frame.setObjectName("ReviewPreview")
        layout = vbox(5, (10, 10, 10, 10), frame)
        preview = DocumentPreview(self.theme)
        preview.set_document(
            filename=review.filename,
            category=category,
            pages=pages,
            seed=review.preview_seed,
            page_index=page_index,
        )
        preview.setFixedHeight(height)
        layout.addWidget(preview)
        caption = hbox(6)
        page_label = review.page_labels[page_index] if page_index < len(review.page_labels) else f"Page {page_index + 1}"
        caption.addWidget(label(page_label, "PageNumber"))
        caption.addStretch(1)
        caption.addWidget(label("Sample preview", "PageNumber"))
        layout.addLayout(caption)
        return frame

    def _metadata_side(self, review: ReviewItem) -> QWidget:
        doc = self.state.document(review.document_id)
        wrapper = QWidget()
        box = vbox(9, (0, 0, 0, 0), wrapper)
        filename = label(review.filename, "FileName", wrap=True, selectable=True)
        box.addWidget(filename)
        if doc:
            box.addWidget(label(doc.institution, "MutedLabel"))
            pages = pluralize(max(1, len(review.page_labels)), "page")
            detail = hbox(7)
            detail.addWidget(make_icon_label("file-text", self.theme.token("text_muted"), 12))
            detail.addWidget(label(pages, "TableMeta"))
            detail.addSpacing(8)
            detail.addWidget(make_icon_label("calendar", self.theme.token("text_muted"), 12))
            detail.addWidget(label(format_date(doc.doc_date), "TableMeta"))
            box.addLayout(detail)
            if review.kind == ReviewKind.PERSON:
                person = self.state.person(doc.person_id)
                box.addWidget(
                    label(
                        f"Current demo owner: {person.name if person else 'Unassigned'}",
                        "TableMeta",
                    )
                )
        box.addSpacing(2)
        if review.confidence is not None and review.confidence < 0.6:
            box.addWidget(
                InfoBanner(
                    self.theme,
                    icon="info",
                    title="Why DocPilot is asking",
                    text=(
                        "The demo confidence is below the safety threshold. A person "
                        "makes the final call; nothing is filed automatically."
                    ),
                    tone="warning",
                )
            )
        box.addStretch(1)
        return wrapper

    def _render_person_body(self, review: ReviewItem, resolved: bool) -> None:
        row = hbox(15)
        row.addWidget(self._preview_panel(review, height=244), 5)
        row.addWidget(self._metadata_side(review), 4)
        self.review_body.addLayout(row)
        if resolved:
            return
        self.review_body.addWidget(label("Who does this document belong to?", "SectionLabel"))
        options = [
            {
                "key": person.id,
                "label": person.name,
                "icon": make_avatar_icon(person.initials, person.color, 18),
            }
            for person in self.state.people
        ]
        options.append(
            {
                "key": "unassigned",
                "label": "Leave Unassigned",
                "icon": make_icon("user", self.theme.token("text_muted"), 16),
            }
        )
        grid = QGridLayout()
        grid.setSpacing(8)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, option in enumerate(options):
            button = QPushButton(option["label"])
            button.setObjectName("OptionCard")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(option["icon"])
            button.setIconSize(QSize(18, 18))
            button.setMinimumHeight(42)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            group.addButton(button, index)
            self._choice_map[index] = (str(option["key"]), str(option["label"]))
            grid.addWidget(button, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        group.idClicked.connect(self._choice_made)
        self._choice_group = group
        self.review_body.addLayout(grid)

    def _render_separation_body(self, review: ReviewItem, resolved: bool) -> None:
        row = hbox(12)
        row.addWidget(self._preview_panel(review, 0, height=232), 1)
        row.addWidget(self._preview_panel(review, 1, height=232), 1)
        self.review_body.addLayout(row)
        self.review_body.addWidget(
            InfoBanner(
                self.theme,
                icon="info",
                title="Page boundary check",
                text=(
                    "Decide whether these consecutive pages belong together. "
                    "Changing this boundary only affects demo data."
                ),
                tone="neutral",
            )
        )
        if resolved:
            return
        self.review_body.addWidget(label("Choose a document boundary", "SectionLabel"))
        grid = QGridLayout()
        grid.setSpacing(8)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, (key, text, icon) in enumerate(
            (
                ("same", "Same Document", "documents"),
                ("new", "Start New Document", "file-plus"),
            )
        ):
            button = QPushButton(text)
            button.setObjectName("OptionCard")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(make_icon(icon, self.theme.token("text_secondary"), 16))
            button.setIconSize(QSize(16, 16))
            button.setMinimumHeight(42)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            group.addButton(button, index)
            self._choice_map[index] = (key, text)
            grid.addWidget(button, 0, index)
        group.idClicked.connect(self._choice_made)
        self._choice_group = group
        self.review_body.addLayout(grid)

    def _render_category_body(self, review: ReviewItem, resolved: bool) -> None:
        row = hbox(15)
        row.addWidget(self._preview_panel(review, height=222), 5)
        row.addWidget(self._metadata_side(review), 4)
        self.review_body.addLayout(row)
        if resolved:
            return
        self.review_body.addWidget(label("WHAT TYPE OF DOCUMENT IS THIS?", "SectionLabel"))
        grid = QGridLayout()
        grid.setSpacing(8)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, category in enumerate(self.state.categories):
            button = QPushButton(category)
            button.setObjectName("OptionCard")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(
                make_icon(category_icon(category), category_color(category), 16)
            )
            button.setIconSize(QSize(16, 16))
            button.setMinimumHeight(40)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            group.addButton(button, index)
            self._choice_map[index] = (category, category)
            grid.addWidget(button, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        group.idClicked.connect(self._category_choice_made)
        self._choice_group = group
        self.review_body.addLayout(grid)
        self.review_body.addWidget(label("OR ADD A CUSTOM CATEGORY", "SectionLabel"))
        self._custom_category = QLineEdit()
        self._custom_category.setPlaceholderText("e.g. Rent, Contract, Invoice")
        self._custom_category.textEdited.connect(self._custom_category_edited)
        self.review_body.addWidget(self._custom_category)

    # ------------------------------------------------------------------ footer
    def _render_pending_footer(self, review: ReviewItem) -> None:
        self._validation_label = label("", "DangerText", wrap=True)
        self._validation_label.hide()
        self.footer_layout.addWidget(self._validation_label)
        actions = hbox(8)
        actions.addStretch(1)
        skip = AppButton("Skip for Now", "ghost", self.theme)
        skip.clicked.connect(self._skip_review)
        next_button = AppButton("Next Review", "secondary", self.theme, icon="chevron-right", icon_size=13)
        next_button.clicked.connect(self._next_review)
        save = AppButton(
            "Save Decision", "primary", self.theme, icon="check", icon_size=14
        )
        save.setMinimumWidth(128)
        save.clicked.connect(self._save_decision)
        actions.addWidget(skip)
        actions.addWidget(next_button)
        actions.addWidget(save)
        self.footer_layout.addLayout(actions)

    def _render_resolved_footer(self, review: ReviewItem) -> None:
        actions = hbox(8)
        result = hbox(6)
        result.addWidget(make_icon_label("check-circle", self.theme.token("success"), 13))
        result.addWidget(
            label(f"Decision saved in demo · {review.decision or 'Resolved'}", "SuccessText")
        )
        actions.addLayout(result, 1)
        pending = self.state.pending_reviews()
        if pending:
            next_button = AppButton(
                "Next Pending Review", "secondary", self.theme, icon="arrow-right", icon_size=13
            )
            next_button.clicked.connect(self._select_next_pending)
            actions.addWidget(next_button)
        else:
            actions.addWidget(label("Review queue cleared", "MutedLabel"))
        self.footer_layout.addLayout(actions)

    def _render_caught_up(self) -> None:
        clear_layout(self.review_body)
        clear_layout(self.footer_layout)
        self.footer.setVisible(False)
        resolved = [item for item in self.state.reviews if item.status == ReviewStatus.RESOLVED]
        if not self.state.reviews:
            self.review_body.addWidget(
                EmptyState(
                    self.theme,
                    "review",
                    "Nothing to review",
                    "When DocPilot cannot make a safe decision, the question will appear here.",
                    tone="neutral",
                ),
                1,
            )
            return
        done = EmptyState(
            self.theme,
            "check-circle",
            "You're all caught up",
            (
                "Every demo question has been answered locally. "
                "No real documents or source files were modified."
            ),
            action_text="Reset demo queue" if resolved else None,
            action_icon="rotate",
            tone="success",
        )
        if done.action_button and resolved:
            done.action_button.clicked.connect(self._reset_demo)
        self.review_body.addWidget(done)
        if resolved:
            self.review_body.addWidget(label("SAVED DEMO DECISIONS", "SectionLabel"))
            for item in resolved:
                card = QFrame()
                card.setObjectName("SoftCard")
                layout = hbox(10, (12, 9, 12, 9), card)
                layout.addWidget(
                    make_icon_label("check-circle", self.theme.token("success"), 14)
                )
                text = vbox(1)
                text.addWidget(label(item.filename, "FileName"))
                text.addWidget(
                    label(
                        f"{item.decision or 'Resolved'}  ·  in-memory demo only",
                        "FileSub",
                    )
                )
                layout.addLayout(text, 1)
                self.review_body.addWidget(card)
        self.review_body.addStretch(1)

    # --------------------------------------------------------------- behaviors
    def _choice_made(self, _button_id: int) -> None:
        if self._custom_category is not None:
            self._custom_category.blockSignals(True)
            self._custom_category.clear()
            self._custom_category.blockSignals(False)
        if self._validation_label is not None:
            self._validation_label.hide()

    def _category_choice_made(self, _button_id: int) -> None:
        if self._custom_category is not None:
            self._custom_category.blockSignals(True)
            self._custom_category.clear()
            self._custom_category.blockSignals(False)
        if self._validation_label is not None:
            self._validation_label.hide()

    def _custom_category_edited(self, text: str) -> None:
        if text.strip() and self._choice_group is not None:
            self._choice_group.setExclusive(False)
            for button in self._choice_group.buttons():
                button.setChecked(False)
            self._choice_group.setExclusive(True)
        if self._validation_label is not None and text.strip():
            self._validation_label.hide()

    def _current_review(self) -> Optional[ReviewItem]:
        return self.state.review(self.current_review_id or "")

    def _save_decision(self) -> None:
        review = self._current_review()
        if review is None or review.status != ReviewStatus.PENDING:
            return
        custom = self._custom_category.text().strip() if self._custom_category else ""
        selected_id = self._choice_group.checkedId() if self._choice_group else -1
        if review.kind == ReviewKind.CATEGORY:
            if custom:
                choice_key = custom
                choice_label = custom
            elif selected_id >= 0:
                choice_key, choice_label = self._choice_map[selected_id]
            else:
                self._show_validation("Choose or enter a category first.")
                return
        else:
            if selected_id < 0:
                self._show_validation("Select an option first.")
                return
            choice_key, choice_label = self._choice_map[selected_id]

        success = self.state.resolve_review(
            review.id,
            choice_key,
            choice_label,
            custom_category=custom if review.kind == ReviewKind.CATEGORY else "",
        )
        if not success:
            self._show_validation("This demo decision could not be saved. Try again.")
            return
        pending = self.state.pending_reviews()
        self.current_review_id = pending[0].id if pending else None
        self._refresh_queue()
        self._render_current()
        self.show_toast("Demo decision saved locally. No real document was changed.", "success")

    def _show_validation(self, message: str) -> None:
        if self._validation_label is None:
            return
        self._validation_label.setText(message)
        self._validation_label.show()
        picker = self._custom_category
        if picker is not None and not picker.text().strip():
            picker.setFocus()

    def _next_review(self) -> None:
        pending = self.state.pending_reviews()
        if not pending:
            self.current_review_id = None
            self._refresh_queue()
            self._render_current()
            return
        current_index = next(
            (index for index, item in enumerate(pending) if item.id == self.current_review_id),
            -1,
        )
        if len(pending) == 1 and current_index >= 0:
            self.show_toast("There is no other pending review right now.", "info")
            return
        next_item = pending[(current_index + 1) % len(pending)]
        self._select_review(next_item.id)

    def _select_next_pending(self) -> None:
        pending = self.state.pending_reviews()
        if pending:
            self._select_review(pending[0].id)

    def _skip_review(self) -> None:
        pending = self.state.pending_reviews()
        if not pending:
            return
        current_index = next(
            (index for index, item in enumerate(pending) if item.id == self.current_review_id),
            -1,
        )
        if len(pending) > 1:
            next_item = pending[(current_index + 1) % len(pending)]
            self._select_review(next_item.id)
            self.show_toast("Skipped for now — this question stays in the queue.", "info")
        else:
            self.show_toast("Skipped for now — this question stays in the queue.", "info")

    def _reset_demo(self) -> None:
        self.state.reset_demo_reviews()
        self.current_review_id = None
        pending = self.state.pending_reviews()
        if pending:
            self.current_review_id = pending[0].id
        self._refresh_queue()
        self._render_current()
        self.show_toast("Demo review queue reset. No real data was changed.", "info")
