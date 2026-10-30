"""Left navigation sidebar with icon buttons and review badge."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme.theme import ThemeManager
from app.widgets.common import IconTile, hbox, label, vbox
from app.widgets.icons import make_pixmap


class SidebarButton(QPushButton):
    def __init__(
        self,
        key: str,
        text: str,
        icon_name: str,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.key = key
        self._icon_name = icon_name
        self._theme = theme
        self.setObjectName("SidebarNav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._icon_label = QLabel(self)
        self._icon_label.setObjectName("NavIcon")
        self._icon_label.setFixedSize(18, 18)
        self._icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._badge = QLabel(self)
        self._badge.setObjectName("NavBadge")
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._badge.hide()
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        if self.isChecked():
            color = self._theme.token("accent")
        elif self.underMouse():
            color = self._theme.token("text_secondary")
        else:
            color = self._theme.token("text_muted")
        self._icon_label.setPixmap(make_pixmap(self._icon_name, color, 18, 1.8))

    def set_badge(self, count: int) -> None:
        if count <= 0:
            self._badge.hide()
            return
        self._badge.setText(str(count) if count < 100 else "99+")
        self._badge.adjustSize()
        self._badge.setFixedHeight(17)
        self._badge.show()
        self._position_badge()

    def _position_badge(self) -> None:
        if self._badge.isVisible():
            self._badge.adjustSize()
            self._badge.setFixedHeight(17)
            self._badge.move(
                self.width() - self._badge.width() - 10,
                (self.height() - self._badge.height()) // 2,
            )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._icon_label.move(15, (self.height() - self._icon_label.height()) // 2)
        self._position_badge()

    def enterEvent(self, event) -> None:  # noqa: N802
        super().enterEvent(event)
        self._refresh_icon()

    def leaveEvent(self, event) -> None:  # noqa: N802
        super().leaveEvent(event)
        self._refresh_icon()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange:
            self._refresh_icon()

    def refresh_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        self._refresh_icon()


class Sidebar(QFrame):
    page_selected = Signal(str)

    NAV_ITEMS = [
        ("dashboard", "Dashboard", "dashboard"),
        ("scan", "Scan & Import", "scan"),
        ("processing", "Processing", "processing"),
        ("documents", "Documents", "documents"),
        ("review", "Review Center", "review"),
        ("archive", "Archive", "archive"),
    ]
    SYSTEM_ITEMS = [("settings", "Settings", "settings")]

    def __init__(
        self,
        theme: ThemeManager,
        *,
        pending_reviews: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setObjectName("Sidebar")
        self.setFixedWidth(254)
        self._buttons: dict[str, SidebarButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 20, 16, 16)
        root.setSpacing(4)

        workspace = QFrame()
        workspace.setObjectName("WorkspaceCard")
        workspace_layout = hbox(10, (11, 10, 11, 10), workspace)
        workspace_layout.addWidget(IconTile(theme, "shield-check", "accent", 32, 16))
        workspace_text = vbox(1)
        workspace_text.addWidget(label("Local workspace", "WorkspaceTitle"))
        workspace_text.addWidget(label("Sample data · offline", "WorkspaceSubtitle"))
        workspace_layout.addLayout(workspace_text, 1)
        root.addWidget(workspace)
        root.addSpacing(17)

        root.addWidget(label("WORKSPACE", "SidebarSectionLabel"))
        root.addSpacing(4)
        for key, text, icon_name in self.NAV_ITEMS:
            button = SidebarButton(key, text, icon_name, theme)
            self._group.addButton(button, len(self._buttons))
            self._buttons[key] = button
            button.clicked.connect(lambda _checked=False, k=key: self.page_selected.emit(k))
            button.installEventFilter(self)
            root.addWidget(button)
        root.addSpacing(16)

        root.addWidget(label("SYSTEM", "SidebarSectionLabel"))
        root.addSpacing(4)
        for key, text, icon_name in self.SYSTEM_ITEMS:
            button = SidebarButton(key, text, icon_name, theme)
            self._group.addButton(button, len(self._buttons))
            self._buttons[key] = button
            button.clicked.connect(lambda _checked=False, k=key: self.page_selected.emit(k))
            button.installEventFilter(self)
            root.addWidget(button)

        root.addStretch(1)

        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        footer_layout = vbox(7, (12, 12, 12, 12), footer)
        footer_top = hbox(8)
        footer_top.addWidget(IconTile(theme, "lock", "success", 26, 13))
        footer_top.addWidget(label("Private by design", "SidebarFooterTitle"), 1)
        footer_layout.addLayout(footer_top)
        footer_text = label(
            "Original files are never moved, renamed, or uploaded.",
            "SidebarFooterText",
            wrap=True,
        )
        footer_layout.addWidget(footer_text)
        root.addWidget(footer)
        root.addSpacing(9)
        version = label("DocPilot 0.1.0  ·  UI preview", "SidebarVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(version)

        self.set_review_count(pending_reviews)
        self._buttons["dashboard"].setChecked(True)
        self._buttons["dashboard"]._refresh_icon()

    def eventFilter(self, watched, event):  # noqa: N802
        if event.type() in (QEvent.Type.Show, QEvent.Type.Resize):
            if isinstance(watched, SidebarButton):
                watched._position_badge()
        return super().eventFilter(watched, event)

    def set_active(self, key: str) -> None:
        button = self._buttons.get(key)
        if button is not None and not button.isChecked():
            button.setChecked(True)
        for item in self._buttons.values():
            item._refresh_icon()

    def set_review_count(self, count: int) -> None:
        self._buttons["review"].set_badge(count)

    def refresh_theme(self) -> None:
        for button in self._buttons.values():
            button.refresh_theme(self._theme)
