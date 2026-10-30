"""Simulated processing pipeline used by the Processing page.

This is a UI demo only. It does not open, read, OCR, classify, copy, rename, or
archive any document. Every log message is clearly marked as simulated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from PySide6.QtCore import QObject, QTimer, Signal

from app.models.entities import SelectedFile


class StageState(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Stage:
    key: str
    title: str
    description: str
    icon: str
    duration_ms: int
    state: StageState = StageState.WAITING


_STAGE_BLUEPRINTS = [
    (
        "import", "Import Documents",
        "Add the selected PDFs to a local, read-only demo work queue.",
        "inbox", 850,
    ),
    (
        "ocr", "Extract Text (OCR)",
        "Simulate text-layer extraction and page-by-page OCR.",
        "scan", 1500,
    ),
    (
        "boundaries", "Detect Document Boundaries",
        "Group scanned pages into logical documents.",
        "documents", 1050,
    ),
    (
        "identity", "Verify Person Identity",
        "Match documents against the three demo person profiles.",
        "user", 950,
    ),
    (
        "classify", "Classify Document Type",
        "Assign a category using sample rules only.",
        "sparkles", 1150,
    ),
    (
        "filename", "Generate Document Filename",
        "Build a filename from demo metadata.",
        "file-plus", 800,
    ),
    (
        "validate", "Validate Results",
        "Check required fields and demo confidence thresholds.",
        "shield-check", 900,
    ),
    (
        "archive", "Archive Document",
        "Simulate a hand-off to the logical archive.",
        "archive", 750,
    ),
]

_STAGE_COMPLETION_LOGS = [
    "Demo import complete. Source files were not copied or changed.",
    "Simulated OCR finished for {pages} pages.",
    "Demo boundary detection found {documents} logical documents.",
    "Sample identity matching finished. One item may need review.",
    "Demo classification finished using sample category rules.",
    "Proposed filenames generated for {documents} documents.",
    "Demo validation complete. Results are ready for a review queue.",
    "Archive step simulated. Nothing was moved or renamed.",
]


class DemoProcessingService(QObject):
    """A timer-driven pipeline that only changes its own in-memory demo state."""

    state_changed = Signal()
    progress_changed = Signal(int)
    log_added = Signal(str, str)  # level, message
    finished = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._on_tick)

        self.stages: list[Stage] = [
            Stage(key, title, description, icon, duration)
            for key, title, description, icon, duration in _STAGE_BLUEPRINTS
        ]
        self._status = ProcessingStatus.IDLE
        self._current_stage = -1
        self._stage_elapsed = 0
        self._elapsed = 0
        self._progress = 0
        self._pages = 0
        self._document_count = 0
        self._file_count = 0

    # --------------------------------------------------------------- properties
    @property
    def status(self) -> ProcessingStatus:
        return self._status

    @property
    def status_label(self) -> str:
        return {
            ProcessingStatus.IDLE: "Ready",
            ProcessingStatus.RUNNING: "Running",
            ProcessingStatus.PAUSED: "Paused",
            ProcessingStatus.COMPLETED: "Completed",
            ProcessingStatus.CANCELLED: "Cancelled",
        }[self._status]

    @property
    def is_running(self) -> bool:
        return self._status == ProcessingStatus.RUNNING

    @property
    def is_paused(self) -> bool:
        return self._status == ProcessingStatus.PAUSED

    @property
    def can_pause(self) -> bool:
        return self._status in (ProcessingStatus.RUNNING, ProcessingStatus.PAUSED)

    @property
    def current_stage_index(self) -> int:
        if self._status in (ProcessingStatus.RUNNING, ProcessingStatus.PAUSED):
            return self._current_stage
        return -1

    @property
    def current_stage_title(self) -> str:
        if self._status == ProcessingStatus.RUNNING and 0 <= self._current_stage < len(self.stages):
            return self.stages[self._current_stage].title
        if self._status == ProcessingStatus.PAUSED:
            return "Paused · demo pipeline"
        if self._status == ProcessingStatus.COMPLETED:
            return "All stages complete"
        if self._status == ProcessingStatus.CANCELLED:
            return "Demo run cancelled"
        return "Ready to start"

    @property
    def progress(self) -> int:
        return self._progress

    @property
    def pages(self) -> int:
        return self._pages

    @property
    def document_count(self) -> int:
        return self._document_count

    @property
    def file_count(self) -> int:
        return self._file_count

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed // 1000

    @property
    def elapsed_label(self) -> str:
        seconds = self.elapsed_seconds
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    # ---------------------------------------------------------------- lifecycle
    def start(self, files: Sequence[SelectedFile] | None = None) -> None:
        self._timer.stop()
        files = list(files or [])
        self._file_count = len(files)
        if files:
            known_pages = [item.pages for item in files if item.pages]
            self._pages = sum(known_pages) if known_pages else max(4, len(files) * 4)
            self._document_count = max(1, len(files))
        else:
            # A clearly labelled demo batch is used when no user files are queued.
            self._pages = 14
            self._document_count = 3

        for stage in self.stages:
            stage.state = StageState.WAITING
        self._status = ProcessingStatus.RUNNING
        self._current_stage = 0
        self._stage_elapsed = 0
        self._elapsed = 0
        self._progress = 0
        self.stages[0].state = StageState.RUNNING

        self.log_added.emit(
            "warning",
            "Demo session started. No OCR, AI, or archiving is performed.",
        )
        source_count = len(files) if files else 3
        source_text = (
            f"{source_count} selected file(s)"
            if files
            else "3-file demo batch (no source files attached)"
        )
        self.log_added.emit("muted", f"Simulated import queue: {source_text}.")
        self.log_added.emit("info", "Stage 1/8 · Import Documents started.")

        self._timer.start()
        self.progress_changed.emit(self._progress)
        self.state_changed.emit()

    def pause(self) -> None:
        if self._status != ProcessingStatus.RUNNING:
            return
        self._timer.stop()
        self._status = ProcessingStatus.PAUSED
        self.log_added.emit("warning", "Demo run paused. No files are being touched.")
        self.state_changed.emit()

    def resume(self) -> None:
        if self._status != ProcessingStatus.PAUSED:
            return
        self._status = ProcessingStatus.RUNNING
        self._timer.start()
        self.log_added.emit("info", "Demo run resumed.")
        self.state_changed.emit()

    def cancel(self) -> None:
        if self._status not in (ProcessingStatus.RUNNING, ProcessingStatus.PAUSED):
            return
        self._timer.stop()
        if 0 <= self._current_stage < len(self.stages):
            if self.stages[self._current_stage].state == StageState.RUNNING:
                self.stages[self._current_stage].state = StageState.WAITING
        self._status = ProcessingStatus.CANCELLED
        self.log_added.emit(
            "error", "Demo run cancelled. No files were modified, moved, or deleted."
        )
        self.state_changed.emit()
        self.finished.emit(False)

    def reset(self) -> None:
        self._timer.stop()
        for stage in self.stages:
            stage.state = StageState.WAITING
        self._status = ProcessingStatus.IDLE
        self._current_stage = -1
        self._stage_elapsed = 0
        self._elapsed = 0
        self._progress = 0
        self._pages = 0
        self._document_count = 0
        self._file_count = 0
        self.progress_changed.emit(self._progress)
        self.state_changed.emit()

    # -------------------------------------------------------------------- timer
    def _on_tick(self) -> None:
        if self._status != ProcessingStatus.RUNNING:
            return
        if not (0 <= self._current_stage < len(self.stages)):
            return

        self._stage_elapsed += self._timer.interval()
        self._elapsed += self._timer.interval()
        stage = self.stages[self._current_stage]

        if self._stage_elapsed >= stage.duration_ms:
            stage.state = StageState.COMPLETED
            completion = _STAGE_COMPLETION_LOGS[self._current_stage].format(
                pages=self._pages, documents=self._document_count
            )
            self.log_added.emit("success", f"Stage {self._current_stage + 1}/8 complete · {completion}")
            self._current_stage += 1
            self._stage_elapsed = 0

            if self._current_stage >= len(self.stages):
                self._timer.stop()
                self._status = ProcessingStatus.COMPLETED
                self._progress = 100
                self.log_added.emit(
                    "success",
                    "Demo run complete. All eight stages were simulated — originals untouched.",
                )
                self.progress_changed.emit(100)
                self.state_changed.emit()
                self.finished.emit(True)
                return

            self.stages[self._current_stage].state = StageState.RUNNING
            self.log_added.emit(
                "info",
                f"Stage {self._current_stage + 1}/8 · {self.stages[self._current_stage].title} started.",
            )

        self._update_progress()
        self.progress_changed.emit(self._progress)
        self.state_changed.emit()

    def _update_progress(self) -> None:
        total = sum(stage.duration_ms for stage in self.stages)
        if total <= 0:
            self._progress = 0
            return
        completed = sum(
            stage.duration_ms
            for stage in self.stages
            if stage.state in (StageState.COMPLETED, StageState.NEEDS_REVIEW)
        )
        value = int((completed + self._stage_elapsed) / total * 100)
        self._progress = max(1, min(99, value))
