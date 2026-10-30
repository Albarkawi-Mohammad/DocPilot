"""Core data entities used by the DocPilot interface.

These are deliberately backend-agnostic value objects. A future persistence or
Paperless-ngx adapter can map its own data into these structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class DocumentStatus(str, Enum):
    ARCHIVED = "Archived"
    PROCESSED = "Processed"
    PENDING = "Pending"
    PROCESSING = "Processing"
    NEEDS_REVIEW = "Needs Review"
    FAILED = "Failed"


class ReviewKind(str, Enum):
    PERSON = "person"
    SEPARATION = "separation"
    CATEGORY = "category"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"


@dataclass
class Person:
    id: str
    name: str
    color: str
    role: str = "Household member"
    active: bool = True

    @property
    def initials(self) -> str:
        parts = [part for part in self.name.strip().split() if part]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()


@dataclass
class DocumentRecord:
    """A single logical document in the local demo library."""

    id: str
    filename: str
    person_id: Optional[str]
    institution: str
    category: str
    doc_date: str  # ISO date string
    status: DocumentStatus
    pages: int
    imported_at: str
    confidence: float = 0.9
    source: str = "PDF import"
    preview_seed: int = 0
    note: str = ""


@dataclass
class ReviewItem:
    """A question for the user when the system cannot make a safe decision."""

    id: str
    kind: ReviewKind
    title: str
    description: str
    filename: str
    document_id: Optional[str]
    page_labels: tuple[str, ...] = field(default_factory=tuple)
    preview_seed: int = 1
    status: ReviewStatus = ReviewStatus.PENDING
    decision: Optional[str] = None
    decision_detail: str = ""
    confidence: Optional[float] = None
    submitted_at: str = ""


@dataclass
class SelectedFile:
    """A file selected for the import queue.

    Only metadata is read. DocPilot never moves, renames, modifies, or copies the
    original file in this interface preview.
    """

    path: str
    size_bytes: int = 0
    pages: Optional[int] = None

    @property
    def filename(self) -> str:
        return Path(self.path).name

    @property
    def suffix(self) -> str:
        return Path(self.path).suffix.lower()

    @property
    def directory(self) -> str:
        return str(Path(self.path).parent)


@dataclass
class ActivityEntry:
    id: str
    title: str
    subtitle: str
    time_label: str
    icon: str = "file-text"
    tone: str = "accent"


@dataclass
class ProcessingMetric:
    label: str
    value: str
