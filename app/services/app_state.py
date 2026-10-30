"""Central, in-memory demo state shared by every DocPilot page.

This QObject is intentionally the only place the current interface mutates demo
data. A future backend can replace it with repositories and services while the
pages keep listening to the same signals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from PySide6.QtCore import QObject, Signal

from app.data.sample_data import (
    APP_CATEGORIES,
    sample_activity,
    sample_documents,
    sample_people,
    sample_reviews,
)
from app.models.entities import (
    ActivityEntry,
    DocumentRecord,
    DocumentStatus,
    Person,
    ReviewItem,
    ReviewKind,
    ReviewStatus,
    SelectedFile,
)


@dataclass
class ImportSelectionResult:
    added: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)


class AppState(QObject):
    documents_changed = Signal()
    people_changed = Signal()
    categories_changed = Signal()
    reviews_changed = Signal()
    files_changed = Signal()
    activity_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.people: list[Person] = sample_people()
        self.documents: list[DocumentRecord] = sample_documents()
        self.categories: list[str] = list(APP_CATEGORIES)
        self.reviews: list[ReviewItem] = sample_reviews()
        self.activity: list[ActivityEntry] = sample_activity()
        self.selected_files: list[SelectedFile] = []

    # ------------------------------------------------------------------ people
    def person(self, person_id: Optional[str]) -> Optional[Person]:
        if not person_id:
            return None
        return next((item for item in self.people if item.id == person_id), None)

    def person_name(self, person_id: Optional[str]) -> str:
        person = self.person(person_id)
        return person.name if person else "Unassigned"

    def person_color(self, person_id: Optional[str]) -> str:
        person = self.person(person_id)
        return person.color if person else "#6B7280"

    def active_people(self) -> list[Person]:
        return [person for person in self.people if person.active]

    def update_people(self, updates: dict[str, dict]) -> None:
        """Update only display fields. No identifiers are requested or stored."""
        for person in self.people:
            values = updates.get(person.id, {})
            name = str(values.get("name", person.name)).strip()
            role = str(values.get("role", person.role)).strip()
            person.name = name or person.name
            person.role = role or person.role
            person.active = bool(values.get("active", person.active))
        self.people_changed.emit()

    # ------------------------------------------------------------------ counts
    @property
    def total_documents(self) -> int:
        return len(self.documents)

    @property
    def processed_documents(self) -> int:
        return sum(
            1
            for doc in self.documents
            if doc.status in (DocumentStatus.PROCESSED, DocumentStatus.ARCHIVED)
        )

    @property
    def pending_documents(self) -> int:
        return sum(
            1
            for doc in self.documents
            if doc.status in (DocumentStatus.PENDING, DocumentStatus.PROCESSING)
        )

    @property
    def pending_review_count(self) -> int:
        return sum(1 for item in self.reviews if item.status == ReviewStatus.PENDING)

    def documents_needing_review(self) -> list[DocumentRecord]:
        return [
            doc for doc in self.documents if doc.status == DocumentStatus.NEEDS_REVIEW
        ]

    @property
    def needs_review_count(self) -> int:
        return len(self.documents_needing_review())

    # --------------------------------------------------------------- documents
    def document(self, document_id: Optional[str]) -> Optional[DocumentRecord]:
        if not document_id:
            return None
        return next((doc for doc in self.documents if doc.id == document_id), None)

    def documents_for(
        self, person_id: str | None = None, category: str | None = None
    ) -> list[DocumentRecord]:
        docs = list(self.documents)
        if person_id is not None:
            docs = [doc for doc in docs if doc.person_id == person_id]
        if category is not None:
            docs = [doc for doc in docs if doc.category == category]
        return docs

    def category_counts(self) -> dict[str, int]:
        counts = {category: 0 for category in self.categories}
        for doc in self.documents:
            counts[doc.category] = counts.get(doc.category, 0) + 1
        return counts

    def documents_using_category(self, category: str) -> int:
        return sum(1 for doc in self.documents if doc.category == category)

    # ---------------------------------------------------------------- reviews
    def pending_reviews(self) -> list[ReviewItem]:
        return [item for item in self.reviews if item.status == ReviewStatus.PENDING]

    def review(self, review_id: str) -> Optional[ReviewItem]:
        return next((item for item in self.reviews if item.id == review_id), None)

    def resolve_review(
        self,
        review_id: str,
        choice_key: str,
        choice_label: str,
        custom_category: str = "",
    ) -> bool:
        """Apply a demo review decision to in-memory sample data only."""
        item = self.review(review_id)
        if item is None or item.status != ReviewStatus.PENDING:
            return False

        document = self.document(item.document_id)
        category_added = False
        detail = choice_label

        if item.kind == ReviewKind.PERSON:
            chosen_person_id = None if choice_key == "unassigned" else choice_key
            if document:
                document.person_id = chosen_person_id
            detail = "Left unassigned" if not chosen_person_id else choice_label

        elif item.kind == ReviewKind.CATEGORY:
            category = custom_category.strip() or choice_label
            if category and category not in self.categories:
                self.categories.append(category)
                category_added = True
            if document:
                document.category = category
            detail = f"Filed as {category}"

        elif item.kind == ReviewKind.SEPARATION:
            detail = choice_label

        item.status = ReviewStatus.RESOLVED
        item.decision = choice_label if not custom_category else custom_category
        item.decision_detail = detail
        if document:
            document.status = DocumentStatus.PROCESSED
            document.confidence = max(document.confidence, 0.92)
            document.note = "Demo review decision saved locally."

        self.add_activity(
            "Review decision saved",
            f"{item.filename} · {detail}",
            "check-circle",
            "success",
            time_label="Just now",
        )
        self.reviews_changed.emit()
        self.documents_changed.emit()
        if category_added:
            self.categories_changed.emit()
        return True

    def reset_demo_reviews(self) -> None:
        for item in self.reviews:
            item.status = ReviewStatus.PENDING
            item.decision = None
            item.decision_detail = ""

        original = {
            "doc-005": {"category": "Other", "confidence": 0.41},
            "doc-007": {"person_id": None, "confidence": 0.32},
            "doc-014": {"confidence": 0.52},
        }
        for doc_id, values in original.items():
            document = self.document(doc_id)
            if not document:
                continue
            document.status = DocumentStatus.NEEDS_REVIEW
            if "category" in values:
                document.category = str(values["category"])
            if "person_id" in values:
                document.person_id = values["person_id"]
            if "confidence" in values:
                document.confidence = float(values["confidence"])
            document.note = "Waiting for a demo review decision."

        self.reviews_changed.emit()
        self.documents_changed.emit()

    # -------------------------------------------------------------- categories
    def add_category(self, name: str) -> bool:
        clean = " ".join(name.strip().split())
        if not clean:
            return False
        if any(existing.casefold() == clean.casefold() for existing in self.categories):
            return False
        self.categories.append(clean)
        self.categories_changed.emit()
        return True

    def remove_category(self, name: str) -> bool:
        if name not in self.categories:
            return False
        if self.documents_using_category(name) > 0:
            return False
        self.categories.remove(name)
        self.categories_changed.emit()
        return True

    # ----------------------------------------------------------- selected files
    def add_files(self, paths: Iterable[str]) -> ImportSelectionResult:
        """Add PDFs to the import list without reading or changing their contents."""
        result = ImportSelectionResult()
        existing = {
            str(Path(item.path).resolve(strict=False)).casefold()
            for item in self.selected_files
        }
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".pdf":
                result.rejected.append(path.name or str(raw_path))
                continue
            if not path.is_file():
                result.rejected.append(path.name or str(raw_path))
                continue
            try:
                key = str(path.resolve(strict=False)).casefold()
            except OSError:
                key = str(path).casefold()
            if key in existing:
                result.duplicates.append(path.name)
                continue
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            # Read-only metadata for display. The file itself is never changed.
            try:
                from app.services.pdf_metadata import read_pdf_page_count

                page_count = read_pdf_page_count(str(path))
            except Exception:
                page_count = None
            self.selected_files.append(SelectedFile(str(path), size, page_count))
            existing.add(key)
            result.added.append(path.name)
        if result.added:
            self.files_changed.emit()
        return result

    def remove_file(self, path: str) -> None:
        before = len(self.selected_files)
        self.selected_files = [item for item in self.selected_files if item.path != path]
        if len(self.selected_files) != before:
            self.files_changed.emit()

    def clear_files(self) -> None:
        if self.selected_files:
            self.selected_files = []
            self.files_changed.emit()

    @property
    def selected_files_size(self) -> int:
        return sum(item.size_bytes for item in self.selected_files)

    # --------------------------------------------------------------- activity
    def add_activity(
        self,
        title: str,
        subtitle: str,
        icon: str = "activity",
        tone: str = "accent",
        time_label: str = "Just now",
    ) -> None:
        entry = ActivityEntry(
            id=f"activity-{time.time_ns()}",
            title=title,
            subtitle=subtitle,
            time_label=time_label,
            icon=icon,
            tone=tone,
        )
        self.activity.insert(0, entry)
        del self.activity[12:]
        self.activity_changed.emit()
