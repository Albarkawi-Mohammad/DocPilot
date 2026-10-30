"""Main application shell: sidebar, header, pages, and demo-only wiring."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.pages.archive import ArchivePage
from app.pages.dashboard import DashboardPage
from app.pages.documents import DocumentsPage
from app.pages.processing import ProcessingPage
from app.pages.review_center import ReviewCenterPage
from app.pages.scan_import import ScanImportPage
from app.pages.settings import SettingsPage
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.widgets.header import Header
from app.widgets.icons import make_icon, make_logo_pixmap
from app.widgets.sidebar import Sidebar
from app.widgets.toast import Toast

PAGE_META = {
    "dashboard": ("Dashboard", "Workspace overview"),
    "scan": ("Scan & Import", "Add local PDFs to the demo queue"),
    "processing": ("Processing", "Simulated eight-stage pipeline"),
    "documents": ("Documents", "Local sample document library"),
    "review": ("Review Center", "Demo decisions that need attention"),
    "archive": ("Archive", "Logical person and category view"),
    "settings": ("Settings", "Local preferences and integration placeholders"),
}


class MainWindow(QMainWindow):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__()
        self.state = state
        self.theme = theme
        self._current_page = ""

        self.setWindowTitle("DocPilot — Local Document Manager")
        self.setWindowIcon(QIcon(make_logo_pixmap(64)))
        self.setMinimumSize(1240, 720)
        self._fit_to_screen()
        self._build_shell()
        self._connect_signals()

        self._sync_attention()
        self.navigate("dashboard")

    # ------------------------------------------------------------------- shell
    def _fit_to_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1440, 900)
            return
        available = screen.availableGeometry()
        width = min(1440, max(1240, available.width() - 80))
        height = min(900, max(720, available.height() - 80))
        self.resize(width, height)
        self.move(
            available.center().x() - width // 2,
            available.center().y() - height // 2,
        )

    def _build_shell(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = Sidebar(
            self.theme, pending_reviews=self.state.pending_review_count
        )
        shell.addWidget(self.sidebar, 0)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.header = Header(self.theme)
        right_layout.addWidget(self.header, 0)

        self.pages_stack = QStackedWidget()
        self.pages_stack.setObjectName("PageStack")
        self.pages = {
            "dashboard": DashboardPage(self.state, self.theme),
            "scan": ScanImportPage(self.state, self.theme),
            "processing": ProcessingPage(self.state, self.theme),
            "documents": DocumentsPage(self.state, self.theme),
            "review": ReviewCenterPage(self.state, self.theme),
            "archive": ArchivePage(self.state, self.theme),
            "settings": SettingsPage(self.state, self.theme),
        }
        for page in self.pages.values():
            self.pages_stack.addWidget(page)
        right_layout.addWidget(self.pages_stack, 1)

        shell.addWidget(right, 1)
        self.setCentralWidget(root)
        self.toast = Toast(self.theme, root)

    def _connect_signals(self) -> None:
        self.sidebar.page_selected.connect(self.navigate)
        self.header.notifications_requested.connect(self._show_notifications)
        self.header.theme_toggle_requested.connect(self._toggle_theme)
        self.state.reviews_changed.connect(self._sync_attention)
        self.theme.theme_changed.connect(self._on_theme_changed)

        for page in self.pages.values():
            page.toast_requested.connect(self.show_toast)
            page.navigate_requested.connect(self.navigate)
            page.open_document_requested.connect(self.open_document)

        self.pages["scan"].processing_requested.connect(self._start_processing_from_scan)

    # -------------------------------------------------------------- navigation
    def navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self._current_page = key
        self.pages_stack.setCurrentWidget(page)
        self.sidebar.set_active(key)
        title, caption = PAGE_META.get(key, (key.title(), ""))
        self.header.set_page(title, caption)
        page.on_activated()

    def open_document(self, document_id: str) -> None:
        self.navigate("documents")
        page = self.pages["documents"]
        if isinstance(page, DocumentsPage):
            page.select_document(document_id)

    # ---------------------------------------------------------------- messaging
    def show_toast(self, message: str, tone: str = "info") -> None:
        self.toast.show_message(message, tone)

    def _sync_attention(self) -> None:
        pending = self.state.pending_review_count
        self.sidebar.set_review_count(pending)
        self.header.set_notification_count(pending)

    def _toggle_theme(self) -> None:
        self.theme.toggle()
        self.show_toast(f"{self.theme.mode.title()} theme enabled.", "info")

    def _on_theme_changed(self, _mode: str) -> None:
        self.sidebar.refresh_theme()

    def _show_notifications(self) -> None:
        menu = QMenu(self)
        header_action = QAction("NOTIFICATIONS", menu)
        header_action.setEnabled(False)
        menu.addAction(header_action)

        pending = self.state.pending_review_count
        review_title = (
            f"{pending} demo reviews need a decision"
            if pending
            else "Review queue is clear"
        )
        review_detail = (
            "Open the Review Center to resolve them."
            if pending
            else "No demo questions are pending."
        )
        entries = [
            ("review", review_title, review_detail, "review"),
            (
                "processing",
                "Demo processing is ready",
                "Run a simulated eight-stage pipeline.",
                "processing",
            ),
            (
                "shield-check",
                "Everything is local",
                "No network connection is used by this preview.",
                "",
            ),
        ]
        target_actions: list[tuple[QAction, str]] = []
        for icon_name, title, detail, target in entries:
            action = QAction(
                make_icon(icon_name, self.theme.token("text_secondary"), 15),
                f"{title}  —  {detail}",
                menu,
            )
            menu.addAction(action)
            target_actions.append((action, target))

        menu.addSeparator()
        clear_action = QAction("Close notifications", menu)
        menu.addAction(clear_action)

        for action, target in target_actions:
            action.triggered.connect(
                lambda _checked=False, destination=target: (
                    self.navigate(destination)
                    if destination
                    else self.show_toast(
                        "Everything in this preview stays on this computer.",
                        "info",
                    )
                )
            )

        button = self.header.notification_button
        position = button.mapToGlobal(QPoint(0, button.height() + 8))
        menu.exec(position)

    # ---------------------------------------------------------------- processing
    def _start_processing_from_scan(self) -> None:
        files = list(self.state.selected_files)
        if not files:
            self.show_toast(
                "Select at least one PDF before starting the demo pipeline.",
                "warning",
            )
            return
        self.navigate("processing")
        page = self.pages["processing"]
        if isinstance(page, ProcessingPage):
            page.start_demo(files)

    # -------------------------------------------------------------------- events
    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self.toast.reposition()
