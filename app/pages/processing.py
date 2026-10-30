"""Processing page — a clearly labelled, timer-driven demo pipeline."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import SelectedFile
from app.pages.base import ScrollablePage, page_intro
from app.services.app_state import AppState
from app.services.demo_processing import (
    DemoProcessingService,
    ProcessingStatus,
    Stage,
    StageState,
)
from app.theme.theme import ThemeManager
from app.utils import pluralize
from app.widgets.buttons import AppButton
from app.widgets.cards import Card, InfoBanner, SectionHeader
from app.widgets.common import (
    Badge,
    clear_layout,
    hbox,
    label,
    repolish,
    tone_color,
    vbox,
)
from app.widgets.icons import make_icon


STAGE_CHIP = {
    StageState.WAITING: ("Waiting", "neutral"),
    StageState.RUNNING: ("Running", "accent"),
    StageState.COMPLETED: ("Completed", "success"),
    StageState.NEEDS_REVIEW: ("Needs review", "warning"),
    StageState.FAILED: ("Failed", "danger"),
}
STAGE_MARK = {
    StageState.WAITING: "",
    StageState.RUNNING: "●",
    StageState.COMPLETED: "✓",
    StageState.NEEDS_REVIEW: "!",
    StageState.FAILED: "×",
}


class StageRow(QWidget):
    def __init__(
        self,
        theme: ThemeManager,
        index: int,
        stage: Stage,
        is_last: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self._stage = stage
        self._last_state: StageState | None = None
        self._badge_state: StageState | None = None
        self.setObjectName("StageRow")
        self.setFixedHeight(49)

        layout = hbox(11, (0, 0, 0, 0), self)
        indicator = vbox(0)
        indicator.setContentsMargins(0, 4, 0, 0)
        self.dot = label(str(index + 1), "StageDot", alignment=Qt.AlignmentFlag.AlignCenter)
        self.dot.setFixedSize(24, 24)
        indicator.addWidget(self.dot, 0, Qt.AlignmentFlag.AlignHCenter)
        self.connector = QFrame()
        self.connector.setObjectName("StageConnector")
        self.connector.setFixedWidth(1)
        if not is_last:
            indicator.addWidget(self.connector, 1, Qt.AlignmentFlag.AlignHCenter)
        else:
            indicator.addStretch(1)
        layout.addLayout(indicator)

        content = vbox(1)
        self.name_label = label(stage.title, "StageName")
        self.description_label = label(stage.description, "StageDescription")
        content.addWidget(self.name_label)
        content.addWidget(self.description_label)
        layout.addLayout(content, 1)
        self.badge = Badge("Waiting", "neutral")
        layout.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self._sync(stage.state)

    def refresh(self, stage: Stage) -> None:
        self._stage = stage
        self._sync(stage.state)

    def _sync(self, state: StageState) -> None:
        if self._last_state == state and self._badge_state == state:
            return
        state_changed = self._last_state != state
        self._last_state = state
        if state_changed:
            self.dot.setProperty("stage", state.value)
            self.dot.setText(STAGE_MARK[state] or str(self._index + 1))
            repolish(self.dot)
            self.connector.setProperty(
                "completed",
                state in (StageState.COMPLETED, StageState.NEEDS_REVIEW),
            )
            repolish(self.connector)
        if self._badge_state != state:
            text, tone = STAGE_CHIP[state]
            self.badge.setText(text)
            self.badge.set_tone(tone)
            self._badge_state = state


class ProcessingPage(ScrollablePage):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self.service = DemoProcessingService(self)
        self._stage_rows: list[StageRow] = []
        self._log_rows: list[QWidget] = []
        self._log_placeholder: QWidget | None = None
        self._build()
        self.service.state_changed.connect(self._sync_ui)
        self.service.progress_changed.connect(self._sync_progress)
        self.service.log_added.connect(self._append_log)
        self.service.finished.connect(self._on_finished)
        self.state.files_changed.connect(self._sync_source)
        self._sync_ui()
        self._sync_source()

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        intro_right = hbox(8)
        intro_right.addWidget(Badge("Demo simulation", "warning"))
        intro_right.addWidget(Badge("Mock data", "neutral"))
        self.body_layout.addWidget(
            page_intro(
                "Processing pipeline",
                "Preview the eight-step workflow. Every stage below is simulated locally.",
                intro_right,
            )
        )
        self.body_layout.addWidget(
            InfoBanner(
                self.theme,
                icon="alert-triangle",
                title="This is not real processing",
                text=(
                    "Progress is driven by a timer. No OCR, AI classification, file "
                    "renaming, or archiving takes place, and source files are never touched."
                ),
                tone="warning",
            )
        )

        # Run overview -----------------------------------------------------
        overview = Card(self.theme, padding=18, spacing=10)
        top = hbox(12)
        title_box = vbox(2)
        title_box.addWidget(label("Demo run", "CardTitle"))
        title_box.addWidget(
            label("Read-only simulation with a mock batch of documents", "CardSubtitle")
        )
        top.addLayout(title_box, 1)
        self.source_badge = Badge("Demo batch", "neutral")
        top.addWidget(self.source_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.status_badge = Badge("Ready", "neutral")
        top.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        overview.body.addLayout(top)

        progress_header = hbox(10)
        current_box = vbox(1)
        current_box.addWidget(label("CURRENT STAGE", "MetricLabel"))
        self.current_stage_label = label("Ready to start", "CurrentStage")
        current_box.addWidget(self.current_stage_label)
        progress_header.addLayout(current_box, 1)
        self.progress_value = label("0%", "BigMetric")
        progress_header.addWidget(self.progress_value, 0, Qt.AlignmentFlag.AlignVCenter)
        overview.body.addLayout(progress_header)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        overview.body.addWidget(self.progress)

        bottom = hbox(18)
        metrics = hbox(0)
        self.metric_pages = self._metric("Pages (demo)", "—", metrics, add_divider=False)
        self.metric_documents = self._metric("Documents detected", "—", metrics)
        self.metric_files = self._metric("Source files", "—", metrics)
        self.metric_elapsed = self._metric("Elapsed", "00:00", metrics)
        bottom.addLayout(metrics, 1)

        self.start_button = AppButton(
            "Start demo", "primary", self.theme, icon="play", icon_size=15
        )
        self.start_button.setMinimumWidth(118)
        self.pause_button = AppButton(
            "Pause", "secondary", self.theme, icon="pause", icon_size=14
        )
        self.pause_button.setMinimumWidth(96)
        self.cancel_button = AppButton(
            "Cancel", "ghost", self.theme, icon="stop", icon_size=13
        )
        self.start_button.clicked.connect(lambda: self.start_demo())
        self.pause_button.clicked.connect(self._toggle_pause)
        self.cancel_button.clicked.connect(self._cancel)
        controls = hbox(8)
        controls.addWidget(self.start_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.cancel_button)
        bottom.addLayout(controls)
        overview.body.addLayout(bottom)
        self.body_layout.addWidget(overview)

        # Pipeline + log ---------------------------------------------------
        split = QHBoxLayout()
        split.setSpacing(16)

        pipeline = Card(self.theme, padding=18, spacing=8)
        pipeline_header = SectionHeader(
            "Processing pipeline",
            "Eight stages · clearly labelled simulation",
            Badge("8 stages", "neutral"),
        )
        pipeline.body.addWidget(pipeline_header)
        pipeline.body.addWidget(self._legend())
        for index, stage in enumerate(self.service.stages):
            row = StageRow(
                self.theme, index, stage, index == len(self.service.stages) - 1
            )
            self._stage_rows.append(row)
            pipeline.body.addWidget(row)
        pipeline_note = label(
            "Stages support waiting, running, completed, needs-review, and failed states.",
            "StageDescription",
        )
        pipeline.body.addWidget(pipeline_note)
        split.addWidget(pipeline, 5)

        log_card = Card(self.theme, padding=0, spacing=0)
        log_header = QWidget()
        log_header_layout = hbox(10, (18, 15, 18, 10), log_header)
        log_text = vbox(2)
        log_text.addWidget(label("Activity log", "CardTitle"))
        log_text.addWidget(label("Simulated events only · nothing is executed", "CardSubtitle"))
        log_header_layout.addLayout(log_text, 1)
        log_header_layout.addWidget(Badge("Local demo", "neutral"), 0, Qt.AlignmentFlag.AlignVCenter)
        log_card.body.addWidget(log_header)
        self.log_scroll = QScrollArea()
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.log_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_host = QWidget()
        self.log_layout = vbox(0, (16, 4, 14, 12), self.log_host)
        self.log_layout.addStretch(1)
        self.log_scroll.setWidget(self.log_host)
        log_card.body.addWidget(self.log_scroll, 1)
        self._show_log_placeholder()
        split.addWidget(log_card, 4)

        self.body_layout.addLayout(split)
        self.body_layout.addStretch(1)

    def _metric(
        self,
        label_text: str,
        value: str,
        parent_layout: QHBoxLayout,
        *,
        add_divider: bool = True,
    ):
        if add_divider:
            line = QFrame()
            line.setObjectName("SettingDivider")
            line.setFixedSize(1, 30)
            parent_layout.addSpacing(12)
            parent_layout.addWidget(line, 0, Qt.AlignmentFlag.AlignVCenter)
            parent_layout.addSpacing(12)
        box = QWidget()
        box_layout = vbox(1, (0, 0, 0, 0), box)
        value_label = label(value, "MetricValue")
        box_layout.addWidget(value_label)
        box_layout.addWidget(label(label_text, "MetricLabel"))
        parent_layout.addWidget(box)
        return value_label

    def _legend(self) -> QWidget:
        wrapper = QWidget()
        layout = hbox(11)
        for state, text, tone in (
            (StageState.WAITING, "Waiting", "neutral"),
            (StageState.RUNNING, "Running", "accent"),
            (StageState.COMPLETED, "Completed", "success"),
            (StageState.NEEDS_REVIEW, "Needs review", "warning"),
            (StageState.FAILED, "Failed", "danger"),
        ):
            dot = QLabel()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(
                f"background-color: {tone_color(self.theme, tone)}; border-radius: 3px;"
            )
            layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(label(text, "TableMeta"))
        layout.addStretch(1)
        return wrapper

    # ----------------------------------------------------------------- actions
    def start_demo(
        self,
        files: list[SelectedFile] | None = None,
        *,
        source_label: str | None = None,
    ) -> None:
        if self.service.status in (ProcessingStatus.RUNNING, ProcessingStatus.PAUSED):
            self.show_toast("A demo run is already in progress.", "info")
            return
        files = list(files if files is not None else self.state.selected_files)
        self._set_source(files, source_label)
        self._clear_logs()
        self.service.start(files)
        self._sync_ui()
        self.show_toast("Simulated pipeline started — no real documents are processed.", "info")

    def _set_source(
        self, files: list[SelectedFile], source_label: str | None = None
    ) -> None:
        if source_label:
            self.source_badge.setText(source_label)
            self.source_badge.setToolTip("\n".join(item.path for item in files))
        elif files:
            first = files[0].filename
            extra = len(files) - 1
            self.source_badge.setText(first + (f"  +{extra} more" if extra else ""))
            self.source_badge.setToolTip("\n".join(item.path for item in files))
        else:
            self.source_badge.setText("Demo batch · no files attached")
            self.source_badge.setToolTip(
                "A mock batch of three files is used until PDFs are selected in Scan & Import."
            )

    def _toggle_pause(self) -> None:
        if self.service.is_running:
            self.service.pause()
            self.show_toast("Demo run paused.", "info")
        elif self.service.is_paused:
            self.service.resume()

    def _cancel(self) -> None:
        if self.service.can_pause:
            self.service.cancel()

    def _on_finished(self, success: bool) -> None:
        if success:
            self.show_toast(
                "Demo pipeline complete. All results are mock data; originals untouched.",
                "success",
            )
        else:
            self.show_toast("Demo run cancelled. No files were changed.", "warning")

    # --------------------------------------------------------------------- sync
    def _sync_source(self) -> None:
        if self.service.status in (
            ProcessingStatus.RUNNING,
            ProcessingStatus.PAUSED,
            ProcessingStatus.COMPLETED,
        ):
            return
        files = self.state.selected_files
        if files:
            first = files[0].filename
            extra = len(files) - 1
            self.source_badge.setText(
                f"{first}" + (f"  +{extra} more" if extra else "")
            )
            self.source_badge.setToolTip("\n".join(item.path for item in files))
        else:
            self.source_badge.setText("Demo batch · no files attached")
            self.source_badge.setToolTip(
                "A mock batch of three files is used until PDFs are selected in Scan & Import."
            )

    def _sync_ui(self) -> None:
        status = self.service.status
        for row, stage in zip(self._stage_rows, self.service.stages):
            row.refresh(stage)

        status_map = {
            ProcessingStatus.IDLE: ("Ready", "neutral"),
            ProcessingStatus.RUNNING: ("Running", "accent"),
            ProcessingStatus.PAUSED: ("Paused", "warning"),
            ProcessingStatus.COMPLETED: ("Completed", "success"),
            ProcessingStatus.CANCELLED: ("Cancelled", "warning"),
        }
        text, tone = status_map[status]
        if self.status_badge.text() != text or self.status_badge.property("tone") != tone:
            self.status_badge.setText(text)
            self.status_badge.set_tone(tone)

        self.current_stage_label.setText(self.service.current_stage_title)
        self.progress_value.setText(f"{self.service.progress}%")
        self.progress.setValue(self.service.progress)
        self.metric_pages.setText(str(self.service.pages) if self.service.pages else "—")
        self.metric_documents.setText(
            str(self.service.document_count) if self.service.document_count else "—"
        )
        if status == ProcessingStatus.RUNNING or status == ProcessingStatus.PAUSED:
            file_count = self.service.file_count
            self.metric_files.setText(str(file_count) if file_count else "Demo")
        elif self.state.selected_files and status in (
            ProcessingStatus.IDLE,
            ProcessingStatus.CANCELLED,
        ):
            self.metric_files.setText(str(len(self.state.selected_files)))
        elif status == ProcessingStatus.COMPLETED:
            self.metric_files.setText(
                str(self.service.file_count) if self.service.file_count else "Demo"
            )
        else:
            self.metric_files.setText("Demo" if not self.state.selected_files else str(len(self.state.selected_files)))
        self.metric_elapsed.setText(self.service.elapsed_label)

        running = status == ProcessingStatus.RUNNING
        paused = status == ProcessingStatus.PAUSED
        busy = running or paused
        self.start_button.setEnabled(not busy)
        self.pause_button.setEnabled(busy)
        self.cancel_button.setEnabled(busy)
        if status == ProcessingStatus.COMPLETED:
            self.start_button.setText("Run demo again")
        elif status == ProcessingStatus.CANCELLED:
            self.start_button.setText("Start demo")
        else:
            self.start_button.setText("Start demo")
        self.pause_button.setText("Resume" if paused else "Pause")
        self.pause_button.setIcon(
            make_icon(
                "play" if paused else "pause",
                self.theme.token("text_secondary"),
                14,
                1.8,
            )
        )

    def _sync_progress(self, value: int) -> None:
        self.progress.setValue(value)
        self.progress_value.setText(f"{value}%")

    # ---------------------------------------------------------------------- log
    def _show_log_placeholder(self) -> None:
        placeholder = label(
            "No activity yet. Start a demo run to see simulated stage events.",
            "EmptyText",
            wrap=True,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        placeholder.setMinimumHeight(140)
        self.log_layout.insertWidget(0, placeholder)
        self._log_placeholder = placeholder

    def _clear_logs(self) -> None:
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._log_rows.clear()
        self._log_placeholder = None
        self._show_log_placeholder()

    def _append_log(self, level: str, message: str) -> None:
        if self._log_placeholder is not None:
            self.log_layout.removeWidget(self._log_placeholder)
            self._log_placeholder.deleteLater()
            self._log_placeholder = None
        row = QWidget()
        row.setObjectName("LogRow")
        layout = hbox(8, (0, 4, 0, 4), row)
        time_label = label(QTime.currentTime().toString("HH:mm:ss"), "LogTime")
        time_label.setFixedWidth(50)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(time_label, 0, Qt.AlignmentFlag.AlignTop)
        dot = QLabel()
        dot.setObjectName("LogDot")
        dot.setProperty("level", level)
        dot.setFixedSize(6, 6)
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        message_label = label(message, "LogMessage", wrap=True)
        layout.addWidget(message_label, 1)
        self.log_layout.insertWidget(self.log_layout.count() - 1, row)
        self._log_rows.append(row)
        if len(self._log_rows) > 80:
            old = self._log_rows.pop(0)
            self.log_layout.removeWidget(old)
            old.deleteLater()
        QTimer.singleShot(10, self._scroll_logs_to_end)

    def _scroll_logs_to_end(self) -> None:
        bar = self.log_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
