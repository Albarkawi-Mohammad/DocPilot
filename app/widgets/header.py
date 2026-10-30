"""Top header with branding, page context, local status, and notifications."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.theme.theme import ThemeManager
from app.widgets.common import hbox, label, vbox
from app.widgets.icons import make_icon, make_logo_pixmap


class Header(QFrame):
    notifications_requested = Signal()
    theme_toggle_requested = Signal()

    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setObjectName("TopHeader")
        self.setFixedHeight(76)

        root = hbox(12, (26, 10, 22, 10), self)

        logo = QLabel()
        logo.setPixmap(make_logo_pixmap(34))
        logo.setFixedSize(34, 34)
        logo.setAccessibleName("DocPilot logo")
        root.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)

        brand = vbox(0)
        brand.addWidget(label("DocPilot", "BrandName"))
        brand.addWidget(label("LOCAL DOCUMENT MANAGER", "BrandSub"))
        root.addLayout(brand)
        root.addSpacing(8)

        divider = QFrame()
        divider.setObjectName("HeaderDivider")
        divider.setFixedSize(1, 32)
        root.addWidget(divider, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addSpacing(6)

        page_text = vbox(1)
        self.page_title = label("Dashboard", "PageTitle")
        self.page_caption = label("Workspace overview", "PageSubtitle")
        page_text.addWidget(self.page_title)
        page_text.addWidget(self.page_caption)
        root.addLayout(page_text, 1)

        status = QFrame()
        status.setObjectName("LocalStatus")
        status.setFixedHeight(38)
        status_layout = hbox(8, (10, 4, 10, 4), status)
        dot = QLabel()
        dot.setObjectName("StatusDot")
        dot.setFixedSize(8, 8)
        status_layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        status_text = vbox(0)
        status_text.addWidget(label("Local system", "StatusText"))
        status_text.addWidget(label("Ready · offline", "StatusCaption"))
        status_layout.addLayout(status_text)
        status.setToolTip("No cloud connection. All demo data is local to this app.")
        root.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addSpacing(2)

        self.notification_button = QToolButton()
        self.notification_button.setObjectName("HeaderIconButton")
        self.notification_button.setFixedSize(38, 38)
        self.notification_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notification_button.setToolTip("Notifications")
        self.notification_button.clicked.connect(self.notifications_requested)
        root.addWidget(self.notification_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.notification_dot = QLabel(self.notification_button)
        self.notification_dot.setObjectName("NotificationDot")
        self.notification_dot.setFixedSize(10, 10)
        self.notification_dot.move(25, 5)
        self.notification_dot.raise_()

        self.theme_button = QToolButton()
        self.theme_button.setObjectName("HeaderThemeButton")
        self.theme_button.setFixedSize(38, 38)
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.clicked.connect(self.theme_toggle_requested)
        root.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set_notification_count(0)
        self._refresh_icons()
        theme.theme_changed.connect(self._on_theme_changed)

    def _refresh_icons(self) -> None:
        self.notification_button.setIcon(
            make_icon("bell", self._theme.token("text_secondary"), 18, 1.8)
        )
        self.notification_button.setIconSize(QSize(18, 18))
        if self._theme.is_dark:
            self.theme_button.setIcon(make_icon("sun", self._theme.token("accent"), 18, 1.8))
            self.theme_button.setToolTip("Switch to light theme")
        else:
            self.theme_button.setIcon(make_icon("moon", self._theme.token("accent"), 18, 1.8))
            self.theme_button.setToolTip("Switch to dark theme")

    def _on_theme_changed(self, _mode: str) -> None:
        self._refresh_icons()

    def set_page(self, title: str, caption: str = "") -> None:
        self.page_title.setText(title)
        self.page_caption.setText(caption)
        self.page_caption.setVisible(bool(caption))

    def set_notification_count(self, count: int) -> None:
        self.notification_dot.setVisible(count > 0)
        self.notification_button.setToolTip(
            f"{count} demo reviews need attention" if count else "No new notifications"
        )
