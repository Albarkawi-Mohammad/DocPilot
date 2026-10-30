"""Sample data for the DocPilot interface preview.

Everything here is fictional. Names, institutions, dates, and document contents
are placeholders; no files on disk are referenced by these records.
"""

from __future__ import annotations

from app.models.entities import (
    ActivityEntry,
    DocumentRecord,
    DocumentStatus,
    Person,
    ReviewItem,
    ReviewKind,
    SelectedFile,
)


APP_CATEGORIES = [
    "Health Insurance",
    "Car Insurance",
    "Jobcenter",
    "Bank",
    "Tax",
    "Other",
]


def sample_people() -> list[Person]:
    return [
        Person("person-1", "Person 1", "#4F7BF7", "Primary profile"),
        Person("person-2", "Person 2", "#9A7CF8", "Household member"),
        Person("person-3", "Person 3", "#E2A33D", "Household member"),
    ]


def sample_documents() -> list[DocumentRecord]:
    return [
        DocumentRecord(
            "doc-001", "health_insurance_2026_09.pdf", "person-1", "Allianz",
            "Health Insurance", "2026-09-12", DocumentStatus.ARCHIVED, 4,
            "2026-09-12", 0.98, "Scan & Import", 11,
        ),
        DocumentRecord(
            "doc-002", "car_insurance_policy_2026.pdf", "person-1", "HUK-COBURG",
            "Car Insurance", "2026-08-30", DocumentStatus.ARCHIVED, 2,
            "2026-08-30", 0.97, "Scan & Import", 4,
        ),
        DocumentRecord(
            "doc-003", "jobcenter_decision_0826.pdf", "person-2", "Jobcenter Berlin",
            "Jobcenter", "2026-08-21", DocumentStatus.PROCESSED, 1,
            "2026-08-21", 0.94, "PDF import", 2,
        ),
        DocumentRecord(
            "doc-004", "bank_statement_aug_2026.pdf", "person-3", "Sparkasse",
            "Bank", "2026-08-15", DocumentStatus.PROCESSED, 3,
            "2026-08-15", 0.96, "Scan & Import", 7,
        ),
        DocumentRecord(
            "doc-005", "tax_assessment_2025.pdf", "person-1", "Finanzamt Berlin",
            "Other", "2026-07-29", DocumentStatus.NEEDS_REVIEW, 2,
            "2026-07-29", 0.41, "PDF import", 6,
            "Category confidence was below the demo safety threshold.",
        ),
        DocumentRecord(
            "doc-006", "health_insurance_tk_letter.pdf", "person-2", "Techniker Krankenkasse",
            "Health Insurance", "2026-07-11", DocumentStatus.PROCESSED, 1,
            "2026-07-11", 0.95, "Scan & Import", 8,
        ),
        DocumentRecord(
            "doc-007", "unknown_scan_0042.pdf", None, "Unknown institution",
            "Other", "2026-07-08", DocumentStatus.NEEDS_REVIEW, 1,
            "2026-07-08", 0.32, "PDF import", 9,
            "No person match exceeded the demo safety threshold.",
        ),
        DocumentRecord(
            "doc-008", "car_insurance_adac_2026.pdf", "person-3", "ADAC",
            "Car Insurance", "2026-07-01", DocumentStatus.PROCESSED, 2,
            "2026-07-01", 0.93, "Scan & Import", 1,
        ),
        DocumentRecord(
            "doc-009", "jobcenter_letter_july.pdf", "person-1", "Jobcenter München",
            "Jobcenter", "2026-06-24", DocumentStatus.PENDING, 2,
            "2026-06-24", 0.88, "Scan & Import", 12,
        ),
        DocumentRecord(
            "doc-010", "commerzbank_notice.pdf", "person-2", "Commerzbank",
            "Bank", "2026-06-20", DocumentStatus.PENDING, 1,
            "2026-06-20", 0.90, "PDF import", 5,
        ),
        DocumentRecord(
            "doc-011", "aok_member_letter.pdf", "person-3", "AOK",
            "Health Insurance", "2026-06-15", DocumentStatus.PROCESSED, 3,
            "2026-06-15", 0.97, "Scan & Import", 3,
        ),
        DocumentRecord(
            "doc-012", "tax_letter_2024.pdf", "person-3", "Finanzamt Köln",
            "Tax", "2026-05-30", DocumentStatus.ARCHIVED, 2,
            "2026-05-30", 0.96, "PDF import", 13,
        ),
        DocumentRecord(
            "doc-013", "rental_agreement_2026.pdf", "person-1", "Hausverwaltung Nord",
            "Other", "2026-05-18", DocumentStatus.PROCESSED, 5,
            "2026-05-18", 0.89, "PDF import", 14,
        ),
        DocumentRecord(
            "doc-014", "adac_letter_scan.pdf", "person-2", "ADAC",
            "Car Insurance", "2026-05-09", DocumentStatus.NEEDS_REVIEW, 2,
            "2026-05-09", 0.52, "Scan & Import", 15,
            "The page boundary detector was not confident that both pages belong together.",
        ),
        DocumentRecord(
            "doc-015", "jobcenter_confirmation.pdf", "person-3", "Jobcenter Hamburg",
            "Jobcenter", "2026-04-27", DocumentStatus.PROCESSED, 1,
            "2026-04-27", 0.95, "Scan & Import", 16,
        ),
        DocumentRecord(
            "doc-016", "n26_statement_april.pdf", "person-1", "N26",
            "Bank", "2026-04-03", DocumentStatus.PENDING, 4,
            "2026-04-03", 0.93, "PDF import", 17,
        ),
        DocumentRecord(
            "doc-017", "barmer_health_letter.pdf", "person-2", "BARMER",
            "Health Insurance", "2026-03-22", DocumentStatus.PROCESSED, 2,
            "2026-03-22", 0.98, "Scan & Import", 18,
        ),
        DocumentRecord(
            "doc-018", "vattenfall_bill_march.pdf", "person-3", "Vattenfall",
            "Other", "2026-03-05", DocumentStatus.PENDING, 1,
            "2026-03-05", 0.87, "PDF import", 19,
        ),
    ]


def sample_reviews() -> list[ReviewItem]:
    return [
        ReviewItem(
            id="review-person",
            kind=ReviewKind.PERSON,
            title="Who does this document belong to?",
            description=(
                "No person matched with enough confidence. Choose a profile, or leave "
                "the document unassigned until you know more."
            ),
            filename="unknown_scan_0042.pdf",
            document_id="doc-007",
            page_labels=("Page 1",),
            preview_seed=9,
            confidence=0.32,
            submitted_at="2 hours ago",
        ),
        ReviewItem(
            id="review-separation",
            kind=ReviewKind.SEPARATION,
            title="Does the next page belong to the same document?",
            description=(
                "The page-boundary detector was unsure about these two consecutive "
                "pages. Compare them before they are grouped."
            ),
            filename="adac_letter_scan.pdf",
            document_id="doc-014",
            page_labels=("Page 1", "Page 2"),
            preview_seed=15,
            confidence=0.52,
            submitted_at="3 hours ago",
        ),
        ReviewItem(
            id="review-category",
            kind=ReviewKind.CATEGORY,
            title="What type of document is this?",
            description=(
                "This document did not match a category confidently. Choose one of the "
                "existing categories or add your own."
            ),
            filename="tax_assessment_2025.pdf",
            document_id="doc-005",
            page_labels=("Page 1",),
            preview_seed=6,
            confidence=0.41,
            submitted_at="Yesterday",
        ),
    ]


def sample_activity() -> list[ActivityEntry]:
    return [
        ActivityEntry(
            "act-1", "Health insurance filed", "Person 1 · Health Insurance",
            "12 min ago", "check-circle", "success",
        ),
        ActivityEntry(
            "act-2", "PDF pages added to queue", "6 pages from 2 sample files",
            "38 min ago", "upload-cloud", "accent",
        ),
        ActivityEntry(
            "act-3", "Review required", "unknown_scan_0042.pdf · unknown person",
            "2 hours ago", "alert-triangle", "warning",
        ),
        ActivityEntry(
            "act-4", "Archive view updated", "Sample library now shows 18 documents",
            "3 hours ago", "archive", "purple",
        ),
        ActivityEntry(
            "act-5", "Local workspace loaded", "All demo data stays in memory",
            "Today", "shield-check", "info",
        ),
    ]


def sample_selected_files() -> list[SelectedFile]:
    """A demo-only batch used when the import queue is empty."""
    return [
        SelectedFile(r"C:\DemoScan\scan_batch_07.pdf", 2_486_272),
        SelectedFile(r"C:\DemoScan\insurance_letter.pdf", 842_240),
        SelectedFile(r"C:\DemoScan\jobcenter_notice.pdf", 1_114_112),
    ]


def sample_notifications() -> list[tuple[str, str, str, str]]:
    """(icon, title, detail, target page)."""
    return [
        ("review", "3 reviews need a decision", "Open the Review Center to resolve them.", "review"),
        ("processing", "Demo processing is ready", "Run a simulated eight-stage pipeline.", "processing"),
        ("shield-check", "Everything is local", "No network connection is used by this preview.", ""),
    ]
