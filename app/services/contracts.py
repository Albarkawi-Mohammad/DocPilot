"""Backend boundary interfaces for future DocPilot features.

Nothing in this module talks to the network or starts real processing. The
current interface uses in-memory demo data; a later implementation can provide
concrete adapters for local persistence, OCR, Ollama, or Paperless-ngx without
changing the page layouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence, runtime_checkable

from app.models.entities import DocumentRecord, SelectedFile


class IntegrationState(str, Enum):
    NOT_CONFIGURED = "Not configured"
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    ERROR = "Error"


@dataclass(frozen=True)
class IntegrationInfo:
    name: str
    state: IntegrationState
    detail: str = ""


@dataclass(frozen=True)
class ProcessingOptions:
    ocr_languages: tuple[str, ...] = ("de", "en")
    confidence_threshold: float = 0.75
    keep_originals: bool = True


@runtime_checkable
class DocumentRepository(Protocol):
    """Local document storage read interface, reserved for a later backend."""

    def list_documents(self) -> Sequence[DocumentRecord]: ...

    def get_document(self, document_id: str) -> DocumentRecord | None: ...


@runtime_checkable
class ProcessingBackend(Protocol):
    """Future processing engine contract.

    The UI-facing simulation service implements the same conceptual lifecycle
    (start, pause, resume, cancel) but performs no OCR, classification, or
    archiving.
    """

    def start(self, files: Sequence[SelectedFile], options: ProcessingOptions) -> None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def cancel(self) -> None: ...


@runtime_checkable
class ReviewStore(Protocol):
    """Persistent review queue contract, reserved for a later backend."""

    def pending(self): ...

    def resolve(self, review_id: str, decision: str) -> bool: ...


@runtime_checkable
class ArchiveBackend(Protocol):
    """Logical archive adapter; Paperless-ngx can implement this later."""

    def browse(self, person_id: str | None = None, category: str | None = None): ...

    def status(self) -> IntegrationInfo: ...


@runtime_checkable
class ExternalIntegration(Protocol):
    """Base shape for scanner, OCR, AI, and Paperless-ngx integrations."""

    def status(self) -> IntegrationInfo: ...

    def test_connection(self) -> IntegrationInfo: ...
