"""Settings page — session-only preferences and clearly marked placeholders.

Integration panels intentionally stop at "Not configured". No scanner driver,
OCR engine, model runtime, Paperless-ngx server, or backup target is contacted.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import Person
from app.pages.base import Page, page_intro
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.utils import pluralize
from app.widgets.buttons import AppButton, make_tool_button
from app.widgets.cards import InfoBanner
from app.widgets.common import (
    Avatar,
    Badge,
    IconTile,
    category_color,
    category_icon,
    clear_layout,
    divider,
    hbox,
    label,
    make_icon_label,
    vbox,
)
from app.widgets.icons import make_icon, make_pixmap

NAV_SECTIONS = [
    ("general", "General", "sliders"),
    ("appearance", "Appearance", "palette"),
    ("scanner", "Scanner", "scanner"),
    ("ocr", "OCR", "scan"),
    ("ai", "AI Model", "sparkles"),
    ("paperless", "Paperless-ngx", "link"),
    ("people", "Person Management", "users"),
    ("categories", "Document Categories", "folder"),
    ("storage", "Storage & Backup", "database"),
]

THEME_OPTIONS = [("dark", "Dark theme", "moon"), ("light", "Light theme", "sun")]


class SettingsNavButton(QPushButton):
    """Settings navigation button with a separately colored icon."""

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
        self.setObjectName("SettingsNavButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self._icon_label = QLabel(self)
        self._icon_label.setObjectName("NavIcon")
        self._icon_label.setFixedSize(16, 16)
        self._icon_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.toggled.connect(self._on_toggled)
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        if self.isChecked():
            color = self._theme.token("accent")
        elif self.underMouse():
            color = self._theme.token("text_secondary")
        else:
            color = self._theme.token("text_muted")
        self._icon_label.setPixmap(make_pixmap(self._icon_name, color, 16, 1.8))

    def _on_toggled(self, _checked: bool) -> None:
        self._refresh_icon()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._icon_label.move(14, (self.height() - self._icon_label.height()) // 2)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().enterEvent(event)
        self._refresh_icon()

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().leaveEvent(event)
        self._refresh_icon()

    def refresh_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        self._refresh_icon()


class SettingsSection(QFrame):
    """Card container with a section heading and consistent setting rows."""

    def __init__(
        self,
        theme: ThemeManager,
        icon: str,
        title: str,
        description: str,
        badge_text: str = "",
        badge_tone: str = "neutral",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("SettingsSection")
        root = vbox(0, (20, 18, 20, 16), self)

        header = hbox(12)
        header.addWidget(IconTile(theme, icon, "accent", 38, 18), 0, Qt.AlignmentFlag.AlignTop)
        text = vbox(2)
        title_label = label(title, "SettingsTitle")
        title_label.setWordWrap(True)
        text.addWidget(title_label)
        description_label = label(description, "SettingsDescription", wrap=True)
        description_label.setMaximumWidth(650)
        text.addWidget(description_label)
        header.addLayout(text, 1)
        if badge_text:
            header.addWidget(
                Badge(badge_text, badge_tone),
                0,
                Qt.AlignmentFlag.AlignTop,
            )
        root.addLayout(header)
        root.addSpacing(8)

        self.body = vbox(0)
        root.addLayout(self.body)
        self._first = True

    def add_widget(self, widget: QWidget, *, divider_before: bool = True) -> None:
        if not self._first and divider_before:
            self.body.addWidget(divider("SettingDivider"))
        self.body.addWidget(widget)
        self._first = False

    def add_setting(self, title: str, description: str, control: QWidget) -> None:
        self.add_widget(setting_row(title, description, control))


def setting_row(title: str, description: str, control: QWidget) -> QWidget:
    row = QFrame()
    row.setObjectName("SettingRow")
    layout = hbox(18, (0, 12, 0, 12), row)

    text = vbox(3)
    title_label = label(title, "SettingTitle", wrap=True)
    title_label.setMaximumWidth(560)
    description_label = label(description, "SettingDescription", wrap=True)
    description_label.setMaximumWidth(540)
    text.addWidget(title_label)
    text.addWidget(description_label)
    layout.addLayout(text, 1)
    layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
    return row


def compact_combo(items: list[str], width: int = 190) -> QComboBox:
    combo = QComboBox()
    combo.addItems(items)
    combo.setMinimumWidth(width)
    combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return combo


def checkboxes(*items: str) -> QWidget:
    holder = QWidget()
    layout = hbox(14, (0, 0, 0, 0), holder)
    for text in items:
        check = QCheckBox(text)
        layout.addWidget(check)
    layout.addStretch(1)
    return holder


class SettingsPage(Page):
    def __init__(self, state: AppState, theme: ThemeManager) -> None:
        super().__init__(state, theme)
        self.current_section = ""
        self._nav_buttons: dict[str, SettingsNavButton] = {}
        self._nav_group: Optional[QButtonGroup] = None
        self._theme_group: Optional[QButtonGroup] = None
        self._theme_buttons: dict[str, QPushButton] = {}
        self._person_fields: list[tuple[str, QLineEdit, QLineEdit, QCheckBox, Avatar]] = []
        self._category_list_layout: Optional[QVBoxLayout] = None
        self._category_input: Optional[QLineEdit] = None
        self._startup_key = "dashboard"
        self._needs_theme_refresh = False

        self._build()
        self._connect_state()
        self._show_section("general")

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        intro_right = hbox(8)
        intro_right.addWidget(Badge("Session-only preferences", "neutral"))
        intro_right.addWidget(Badge("UI preview", "warning"))
        self.root.addWidget(
            page_intro(
                "Settings",
                "Configure the demo interface. Integrations remain clearly marked as not configured.",
                intro_right,
            )
        )

        main = hbox(16)
        nav = QFrame()
        nav.setObjectName("SettingsNav")
        nav.setFixedWidth(232)
        nav_layout = vbox(4, (10, 14, 10, 14), nav)

        nav_header = hbox(9, (3, 2, 3, 2))
        nav_header.addWidget(IconTile(self.theme, "settings", "accent", 32, 16))
        nav_text = vbox(1)
        nav_text.addWidget(label("Preferences", "WorkspaceTitle"))
        nav_text.addWidget(label("Local workspace", "WorkspaceSubtitle"))
        nav_header.addLayout(nav_text, 1)
        nav_layout.addLayout(nav_header)
        nav_layout.addSpacing(10)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        for index, (key, text, icon_name) in enumerate(NAV_SECTIONS):
            button = SettingsNavButton(key, text, icon_name, self.theme)
            self._nav_group.addButton(button, index)
            self._nav_buttons[key] = button
            button.clicked.connect(
                lambda _checked=False, section=key: self._show_section(section)
            )
            nav_layout.addWidget(button)
        nav_layout.addStretch(1)

        nav_note = QWidget()
        nav_note_layout = hbox(8, (7, 8, 7, 2))
        nav_note_layout.addWidget(
            make_icon_label("shield-check", self.theme.token("text_muted"), 13),
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        nav_note_layout.addWidget(
            label(
                "Nothing on this page is written to disk or sent over a network.",
                "SidebarFooterText",
                wrap=True,
            ),
            1,
        )
        nav_note.setLayout(nav_note_layout)
        nav_layout.addWidget(nav_note)
        main.addWidget(nav, 0)

        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.content_host = QWidget()
        self.content_host.setObjectName("SettingsBody")
        self.content_layout = vbox(16, (0, 0, 4, 0), self.content_host)
        self.content_scroll.setWidget(self.content_host)
        main.addWidget(self.content_scroll, 1)
        self.root.addLayout(main, 1)

    def _connect_state(self) -> None:
        self.state.people_changed.connect(self._people_changed)
        self.state.categories_changed.connect(self._categories_changed)
        self.state.documents_changed.connect(self._documents_changed)
        self.theme.theme_changed.connect(self._theme_changed)

    # -------------------------------------------------------------- navigation
    def _show_section(self, key: str) -> None:
        if key not in self._nav_buttons:
            return
        self.current_section = key
        button = self._nav_buttons[key]
        if not button.isChecked():
            button.setChecked(True)
        self._render_section()

    def _render_section(self) -> None:
        if not self.current_section:
            return
        self._category_list_layout = None
        self._category_input = None
        self._person_fields = []
        clear_layout(self.content_layout)

        builders = {
            "general": self._general_section,
            "appearance": self._appearance_section,
            "scanner": self._scanner_section,
            "ocr": self._ocr_section,
            "ai": self._ai_section,
            "paperless": self._paperless_section,
            "people": self._people_section,
            "categories": self._categories_section,
            "storage": self._storage_section,
        }
        builder = builders.get(self.current_section)
        if builder is None:
            return
        section = builder()
        self.content_layout.addWidget(section)
        self.content_layout.addStretch(1)
        self._needs_theme_refresh = False
        self.content_scroll.verticalScrollBar().setValue(0)

    def on_activated(self) -> None:
        if self._needs_theme_refresh:
            self._render_section()

    # ----------------------------------------------------------------- general
    def _general_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "sliders",
            "General",
            "Workspace behaviour for this local preview. These choices are not persisted.",
            "Local only",
            "neutral",
        )

        startup = compact_combo(
            ["Dashboard", "Scan & Import", "Documents", "Review Center"], 210
        )
        for index, key in enumerate(("dashboard", "scan", "documents", "review")):
            startup.setItemData(index, key)
        index = startup.findData(self._startup_key)
        startup.setCurrentIndex(index if index >= 0 else 0)
        startup.currentIndexChanged.connect(self._startup_changed)
        card.add_setting(
            "Startup view",
            "The page shown after launch. The interface cannot persist this choice, so it applies to the current session only.",
            startup,
        )

        language = compact_combo(["English (UI preview)"], 210)
        language.setEnabled(False)
        language.setToolTip("Only English is included in this interface preview.")
        card.add_setting(
            "Language",
            "Additional interface translations are not included yet.",
            language,
        )

        demo_mode = QCheckBox("Always on in preview")
        demo_mode.setChecked(True)
        demo_mode.setEnabled(False)
        card.add_setting(
            "Demo data",
            "Sample records and simulated processing are always used. No real library is connected.",
            demo_mode,
        )

        reset_button = AppButton(
            "Reset demo reviews", "secondary", self.theme, icon="rotate", icon_size=13
        )
        reset_button.clicked.connect(self._reset_demo_reviews)
        card.add_setting(
            "Demo review queue",
            "Restore the three sample questions and their original in-memory document state.",
            reset_button,
        )

        card.add_widget(
            InfoBanner(
                self.theme,
                icon="info",
                title="Preferences reset when DocPilot closes",
                text=(
                    "Settings, review decisions, custom categories, and imported file "
                    "selections exist only in memory for this session."
                ),
                tone="neutral",
            )
        )
        return card

    def _startup_changed(self, index: int) -> None:
        combo = self.sender()
        if isinstance(combo, QComboBox):
            key = combo.itemData(index)
            if key:
                self._startup_key = str(key)
        self.show_toast(
            "Startup preference kept for this session only (no settings file is written).",
            "info",
        )

    def _reset_demo_reviews(self) -> None:
        self.state.reset_demo_reviews()
        self.show_toast(
            "Demo review queue reset. No real documents or files were changed.",
            "info",
        )

    # -------------------------------------------------------------- appearance
    def _appearance_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "palette",
            "Appearance",
            "The dark and light themes are both fully implemented and switch immediately.",
            "Theme works",
            "success",
        )

        options = QWidget()
        options_layout = hbox(8, (0, 0, 0, 0), options)
        self._theme_group = QButtonGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_buttons = {}
        for index, (mode, text, icon_name) in enumerate(THEME_OPTIONS):
            button = QPushButton(text)
            button.setObjectName("OptionCard")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumSize(132, 40)
            button.setIcon(
                make_icon(icon_name, self.theme.token("accent"), 15, 1.9)
            )
            button.setIconSize(QSize(15, 15))
            button.setChecked(self.theme.mode == mode)
            self._theme_group.addButton(button, index)
            self._theme_buttons[mode] = button
            options_layout.addWidget(button)
        self._theme_group.idClicked.connect(self._theme_selected)
        card.add_setting(
            "Color theme",
            "Switch the entire interface between the dark and light palettes. No restart is needed.",
            options,
        )

        accent = QWidget()
        accent_layout = hbox(8, (0, 0, 0, 0), accent)
        swatch = QLabel()
        swatch.setFixedSize(16, 16)
        swatch.setStyleSheet(
            f"background-color: {self.theme.token('accent')}; border-radius: 8px;"
        )
        accent_layout.addWidget(swatch)
        accent_layout.addWidget(label("Signal Blue", "FieldValue"))
        card.add_setting(
            "Accent color",
            "A single blue accent keeps actions and selections consistent across both themes.",
            accent,
        )

        density = compact_combo(["Comfortable"], 190)
        density.setEnabled(False)
        card.add_setting(
            "Interface density",
            "Compact density is reserved for a future version; the preview uses comfortable spacing.",
            density,
        )

        card.add_widget(
            InfoBanner(
                self.theme,
                icon="palette",
                title="Theme preview",
                text=(
                    "Use the sun or moon button in the header at any time. "
                    "Both palettes use the same layout and sample data."
                ),
                tone="accent",
            )
        )
        return card

    def _theme_selected(self, button_id: int) -> None:
        mode = THEME_OPTIONS[button_id][0]
        if mode == self.theme.mode:
            return
        self.theme.set_mode(mode)
        self.show_toast(f"{mode.title()} theme applied.", "success")

    def _theme_changed(self, _mode: str) -> None:
        for button in self._nav_buttons.values():
            button.refresh_theme(self.theme)
        if self.current_section == "appearance" and self.isVisible():
            QTimer.singleShot(0, self._render_if_current("appearance"))
        else:
            self._needs_theme_refresh = True

    # ----------------------------------------------------------------- scanner
    def _scanner_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "scanner",
            "Scanner",
            "Scanner support is a future local integration. No driver or hardware is accessed.",
            "Not configured",
            "danger",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="scanner",
                title="Scanner integration is not configured",
                text=(
                    "DocPilot does not install or call scanner drivers in this preview. "
                    "Use Scan & Import to select existing PDF files instead."
                ),
                tone="warning",
            ),
            divider_before=False,
        )

        driver = compact_combo(["No scanner connected"], 220)
        driver.setEnabled(False)
        card.add_setting(
            "Scanner driver",
            "No local scanner was detected because detection is not implemented.",
            driver,
        )

        resolution = compact_combo(["300 dpi", "400 dpi", "600 dpi"], 150)
        resolution.setEnabled(False)
        card.add_setting(
            "Scan resolution",
            "Placeholder preference — it is not sent to any device.",
            resolution,
        )

        duplex = QCheckBox("Scan both sides")
        duplex.setEnabled(False)
        card.add_setting(
            "Duplex mode",
            "Hardware-specific options become available only with a real scanner adapter.",
            duplex,
        )

        feed = QCheckBox("Use automatic document feeder")
        feed.setEnabled(False)
        card.add_setting(
            "Document feeder",
            "No paper feed or hardware command is issued by this interface.",
            feed,
        )

        test_button = AppButton(
            "Test scanner", "secondary", self.theme, icon="plug", icon_size=14
        )
        test_button.clicked.connect(
            lambda: self._not_configured("Scanner", "No scanner hardware was accessed.")
        )
        card.add_setting(
            "Connection test",
            "The test action is a placeholder and never opens a device connection.",
            test_button,
        )
        return card

    # --------------------------------------------------------------------- OCR
    def _ocr_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "scan",
            "OCR",
            "Text recognition is deliberately not implemented. These controls are interface placeholders.",
            "Simulation only",
            "warning",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="alert-triangle",
                title="No text is extracted",
                text=(
                    "The demo processing pipeline only simulates OCR. No PDF is opened, "
                    "rendered, or sent to an OCR engine."
                ),
                tone="warning",
            ),
            divider_before=False,
        )

        engine = compact_combo(["Not configured"], 200)
        engine.setEnabled(False)
        card.add_setting(
            "OCR engine",
            "No local OCR engine is installed or started by DocPilot.",
            engine,
        )

        languages = checkboxes("German", "English")
        for check in languages.findChildren(QCheckBox):
            check.setChecked(True)
            check.setEnabled(False)
        card.add_setting(
            "Recognition languages",
            "German and English are shown as future defaults. They do not affect processing.",
            languages,
        )

        threshold = QSpinBox()
        threshold.setRange(1, 100)
        threshold.setValue(75)
        threshold.setSuffix(" %")
        threshold.setFixedWidth(100)
        threshold.setEnabled(False)
        card.add_setting(
            "Confidence threshold",
            "A future real pipeline would route lower-confidence results to the Review Center.",
            threshold,
        )

        handwriting = QCheckBox("Recognize handwriting")
        handwriting.setEnabled(False)
        card.add_setting(
            "Handwriting",
            "Handwriting recognition is not supported in this preview.",
            handwriting,
        )
        return card

    # ---------------------------------------------------------------- AI model
    def _ai_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "sparkles",
            "AI Model",
            "Local model integrations are placeholders. No Ollama or Hermes service is contacted.",
            "Not configured",
            "danger",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="cloud-off",
                title="No local AI runtime is connected",
                text=(
                    "Classification in the demo uses sample rules only. "
                    "No request is sent to localhost or to any external service."
                ),
                tone="warning",
            ),
            divider_before=False,
        )

        provider = compact_combo(["No provider configured"], 210)
        provider.setEnabled(False)
        card.add_setting(
            "Provider",
            "Ollama and Hermes appear as future integration points only.",
            provider,
        )

        model = compact_combo(["No local model selected"], 210)
        model.setEnabled(False)
        card.add_setting(
            "Model",
            "A model name cannot be selected until a real provider is configured.",
            model,
        )

        endpoint = QLineEdit()
        endpoint.setPlaceholderText("http://localhost:11434")
        endpoint.setFixedWidth(230)
        endpoint.setEnabled(False)
        card.add_setting(
            "Local endpoint",
            "Reserved for a future on-device model runtime. It is not contacted.",
            endpoint,
        )

        card.add_setting(
            "Ollama",
            "Future local model provider. Status is manual and shown for layout preview.",
            Badge("Not configured", "danger"),
        )
        card.add_setting(
            "Hermes",
            "Future document assistant integration. It is not installed or contacted.",
            Badge("Not configured", "danger"),
        )

        test_button = AppButton(
            "Test connection", "secondary", self.theme, icon="plug", icon_size=14
        )
        test_button.clicked.connect(
            lambda: self._not_configured(
                "AI model", "No network request or local model call was made."
            )
        )
        card.add_setting(
            "Connection test",
            "This button only displays a demo notification.",
            test_button,
        )
        return card

    # --------------------------------------------------------------- paperless
    def _paperless_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "link",
            "Paperless-ngx",
            "A future archival adapter can map local records to Paperless-ngx. It is not connected here.",
            "Not configured",
            "danger",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="cloud-off",
                title="Paperless-ngx is not configured",
                text=(
                    "No server address is contacted and no API token is stored. "
                    "The logical archive in this preview is entirely local and in memory."
                ),
                tone="warning",
            ),
            divider_before=False,
        )

        url = QLineEdit()
        url.setPlaceholderText("Not configured")
        url.setText("http://localhost:8000")
        url.setMinimumWidth(250)
        url.setEnabled(False)
        card.add_setting(
            "Server URL",
            "Reserved for a future local Paperless-ngx instance.",
            url,
        )

        token = QLineEdit()
        token.setPlaceholderText("Not configured")
        token.setEchoMode(QLineEdit.EchoMode.Password)
        token.setMinimumWidth(250)
        token.setEnabled(False)
        card.add_setting(
            "API token",
            "No credential is requested, stored, or transmitted in this UI preview.",
            token,
        )

        sync_metadata = QCheckBox("Sync document metadata")
        sync_metadata.setEnabled(False)
        card.add_setting(
            "Metadata sync",
            "Unavailable until a real Paperless-ngx adapter is implemented.",
            sync_metadata,
        )

        sync_archive = QCheckBox("Mirror the logical archive")
        sync_archive.setEnabled(False)
        card.add_setting(
            "Archive sync",
            "No archive is mirrored and no file is uploaded.",
            sync_archive,
        )

        test_button = AppButton(
            "Test connection", "secondary", self.theme, icon="plug", icon_size=14
        )
        test_button.clicked.connect(
            lambda: self._not_configured(
                "Paperless-ngx", "No network request was sent and no file was uploaded."
            )
        )
        card.add_setting(
            "Connection test",
            "This action never contacts a Paperless-ngx server.",
            test_button,
        )
        return card

    # ------------------------------------------------------------------ people
    def _people_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "users",
            "Person Management",
            "Configure the three demo profiles used by documents, review questions, and the archive tree.",
            "3 profiles",
            "accent",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="users",
                title="Changes remain in memory",
                text=(
                    "Renaming a profile updates sample documents and filters immediately. "
                    "No file, folder, or personal identifier is changed."
                ),
                tone="accent",
            ),
            divider_before=False,
        )

        for index, person in enumerate(self.state.people):
            editor = self._person_editor(index, person)
            card.add_widget(editor, divider_before=index > 0)

        actions = QWidget()
        actions_layout = hbox(12, (0, 12, 0, 4), actions)
        note = label(
            "Empty display names are not accepted. Every profile can be inactive.",
            "SettingDescription",
            wrap=True,
        )
        note.setMaximumWidth(440)
        actions_layout.addWidget(note, 0)
        actions_layout.addStretch(1)
        save_button = AppButton(
            "Save profiles", "primary", self.theme, icon="check", icon_size=14
        )
        save_button.clicked.connect(self._save_people)
        actions_layout.addWidget(save_button, 0, Qt.AlignmentFlag.AlignVCenter)
        card.add_widget(actions)
        return card

    def _person_editor(self, index: int, person: Person) -> QWidget:
        row = QFrame()
        row.setObjectName("SettingRow")
        layout = hbox(12, (0, 10, 0, 10), row)
        avatar = Avatar(person, 36)
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        fields = vbox(6)
        top = hbox(7)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(
            f"background-color: {person.color}; border-radius: 4px;"
        )
        top.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(label(f"PROFILE {index + 1}", "FieldLabel"))
        top.addStretch(1)
        active = QCheckBox("Active")
        active.setChecked(person.active)
        active.setToolTip("Inactive profiles remain visible in the demo library.")
        top.addWidget(active, 0, Qt.AlignmentFlag.AlignVCenter)
        fields.addLayout(top)

        inputs = hbox(8)
        name_edit = QLineEdit(person.name)
        name_edit.setPlaceholderText("Display name")
        name_edit.setMinimumWidth(150)
        name_edit.setAccessibleName(f"Profile {index + 1} display name")
        role_edit = QLineEdit(person.role)
        role_edit.setPlaceholderText("Role or description")
        role_edit.setMinimumWidth(140)
        role_edit.setAccessibleName(f"Profile {index + 1} role")
        inputs.addWidget(name_edit, 3)
        inputs.addWidget(role_edit, 2)
        fields.addLayout(inputs)
        layout.addLayout(fields, 1)

        name_edit.textChanged.connect(
            lambda text, source=person, image=avatar: image.set_person(
                Person(
                    source.id,
                    text.strip() or source.name,
                    source.color,
                    source.role,
                    source.active,
                )
            )
        )
        self._person_fields.append(
            (person.id, name_edit, role_edit, active, avatar)
        )
        return row

    def _save_people(self) -> None:
        updates: dict[str, dict] = {}
        for person_id, name_edit, role_edit, active, _avatar in self._person_fields:
            name = name_edit.text().strip()
            if not name:
                self.show_toast("Every demo profile needs a display name.", "warning")
                name_edit.setFocus()
                return
            updates[person_id] = {
                "name": name,
                "role": role_edit.text().strip(),
                "active": active.isChecked(),
            }
        self.state.update_people(updates)
        self.show_toast(
            "Demo profiles updated across the in-memory library. No files were changed.",
            "success",
        )

    # -------------------------------------------------------------- categories
    def _categories_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "folder",
            "Document Categories",
            "Categories are shared by the document filters, review choices, and logical archive tree.",
            "Dynamic in memory",
            "neutral",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="folder-plus",
                title="Add categories for the demo library",
                text=(
                    "New categories appear immediately in review choices and filters. "
                    "A category used by a sample document cannot be removed."
                ),
                tone="accent",
            ),
            divider_before=False,
        )

        rows_host = QWidget()
        self._category_list_layout = vbox(0, (0, 2, 0, 0), rows_host)
        card.add_widget(rows_host, divider_before=False)
        self._fill_category_rows()

        composer = QWidget()
        composer_layout = hbox(8, (0, 12, 0, 4), composer)
        self._category_input = QLineEdit()
        self._category_input.setPlaceholderText("New category name…")
        self._category_input.setClearButtonEnabled(True)
        self._category_input.returnPressed.connect(self._add_category)
        add_button = AppButton(
            "Add category", "secondary", self.theme, icon="plus", icon_size=14
        )
        add_button.clicked.connect(self._add_category)
        composer_layout.addWidget(self._category_input, 1)
        composer_layout.addWidget(add_button, 0, Qt.AlignmentFlag.AlignVCenter)
        card.add_widget(composer)

        hint_host = QWidget()
        hint = hbox(7, (0, 4, 0, 3), hint_host)
        hint.addWidget(
            make_icon_label("info", self.theme.token("text_muted"), 12)
        )
        hint.addWidget(
            label(
                "Removal is available only for categories that no sample document uses.",
                "TableMeta",
                wrap=True,
            ),
            1,
        )
        card.add_widget(hint_host, divider_before=False)
        return card

    def _category_row(self, category: str, count: int) -> QWidget:
        row = QFrame()
        row.setObjectName("SettingRow")
        layout = hbox(9, (0, 8, 0, 8), row)
        layout.addWidget(
            make_icon_label(
                category_icon(category), category_color(category), 15
            )
        )
        layout.addWidget(label(category, "CategoryName"), 0)
        layout.addWidget(label(pluralize(count, "document"), "CategoryCount"), 0)
        layout.addStretch(1)

        tooltip = (
            f"{category} is used by {pluralize(count, 'sample document')} and cannot be removed."
            if count
            else f"Remove {category} from the demo category list"
        )
        remove_button = make_tool_button(
            self.theme,
            "trash",
            object_name="BareIconButton",
            icon_color=(
                self.theme.token("text_muted")
                if count
                else self.theme.token("danger")
            ),
            tooltip=tooltip,
            size=28,
            icon_size=14,
        )
        remove_button.setEnabled(count == 0)
        remove_button.clicked.connect(
            lambda _checked=False, name=category: self._remove_category(name)
        )
        layout.addWidget(remove_button, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _fill_category_rows(self) -> None:
        if self._category_list_layout is None:
            return
        clear_layout(self._category_list_layout)
        counts = self.state.category_counts()
        categories = list(self.state.categories)
        if not categories:
            self._category_list_layout.addWidget(
                label("No categories configured.", "MutedLabel")
            )
            return
        for index, category in enumerate(categories):
            self._category_list_layout.addWidget(
                self._category_row(category, counts.get(category, 0))
            )
            if index < len(categories) - 1:
                self._category_list_layout.addWidget(divider("SettingDivider"))

    def _add_category(self) -> None:
        if self._category_input is None:
            return
        name = self._category_input.text().strip()
        if not name:
            self.show_toast("Enter a category name first.", "warning")
            self._category_input.setFocus()
            return
        if self.state.add_category(name):
            self._category_input.clear()
            self.show_toast(
                f"Category “{name}” added to the in-memory demo.", "success"
            )
        else:
            self.show_toast(
                "That category already exists. Choose a different name.", "warning"
            )
            self._category_input.selectAll()
            self._category_input.setFocus()

    def _remove_category(self, category: str) -> None:
        if self.state.remove_category(category):
            self.show_toast(f"Category “{category}” removed from the demo.", "info")
            return
        self.show_toast(
            "This category is used by sample documents and cannot be removed.",
            "warning",
        )

    # ----------------------------------------------------------------- storage
    def _storage_section(self) -> QWidget:
        card = SettingsSection(
            self.theme,
            "database",
            "Storage & Backup",
            "The preview keeps sample data in memory. Storage paths and backups are not configured.",
            "In memory",
            "warning",
        )
        card.add_widget(
            InfoBanner(
                self.theme,
                icon="hard-drive",
                title="Nothing is written to disk",
                text=(
                    "No library folder is created, no settings file is written, and no backup "
                    "is produced. Original PDFs selected in Scan & Import remain untouched."
                ),
                tone="warning",
            ),
            divider_before=False,
        )

        stats = QWidget()
        stats_layout = hbox(9, (0, 12, 0, 2), stats)
        for icon_name, value, caption, tone in (
            ("documents", str(self.state.total_documents), "sample documents", "accent"),
            ("users", str(len(self.state.people)), "demo profiles", "purple"),
            ("folder", str(len(self.state.categories)), "categories", "success"),
            (
                "archive",
                str(sum(1 for doc in self.state.documents if doc.status.value in ("Processed", "Archived"))),
                "filed records",
                "warning",
            ),
        ):
            tile = QFrame()
            tile.setObjectName("InnerCard")
            tile_layout = vbox(4, (12, 10, 12, 10), tile)
            top = hbox(6)
            top.addWidget(make_icon_label(icon_name, self.theme.token(tone), 13))
            top.addWidget(label(caption.upper(), "MetricLabel"), 1)
            tile_layout.addLayout(top)
            tile_layout.addWidget(label(value, "MetricValue"))
            stats_layout.addWidget(tile, 1)
        card.add_widget(stats, divider_before=False)

        card.add_setting(
            "Library location",
            "This preview does not assign a storage folder.",
            Badge("Not configured", "danger"),
        )
        card.add_setting(
            "Original documents",
            "Source PDFs are only referenced by path. They are never copied, renamed, or deleted.",
            Badge("Never modified", "success"),
        )
        card.add_setting(
            "Backup target",
            "A future local backup adapter could write encrypted copies to a chosen folder.",
            Badge("Not configured", "danger"),
        )

        automatic = QCheckBox("Run automatic backups")
        automatic.setChecked(False)
        automatic.setEnabled(False)
        card.add_setting(
            "Automatic backup",
            "Unavailable because no backup location or persistence layer is configured.",
            automatic,
        )

        backup_button = AppButton(
            "Backup now", "secondary", self.theme, icon="hard-drive", icon_size=14
        )
        backup_button.clicked.connect(
            lambda: self._not_configured(
                "Backup", "No files or folders were created, copied, or changed."
            )
        )
        card.add_setting(
            "Manual backup",
            "This action only displays a demo notification.",
            backup_button,
        )

        card.add_widget(
            InfoBanner(
                self.theme,
                icon="lock",
                title="Local and read-only by design",
                text=(
                    "All archive organisation is logical. Original documents stay in their "
                    "existing locations and are never modified by DocPilot."
                ),
                tone="success",
            )
        )
        return card

    # --------------------------------------------------------------- reactions
    def _not_configured(self, name: str, detail: str) -> None:
        self.show_toast(
            f"{name} is not configured in this UI preview. {detail}", "warning"
        )

    def _render_if_current(self, section: str):
        def render() -> None:
            if self.current_section == section and self.isVisible():
                self._render_section()

        return render

    def _people_changed(self) -> None:
        if self.current_section == "people" and self.isVisible():
            QTimer.singleShot(0, self._render_if_current("people"))
        elif self.current_section == "storage" and self.isVisible():
            QTimer.singleShot(0, self._render_if_current("storage"))

    def _categories_changed(self) -> None:
        if self.current_section == "categories":
            self._fill_category_rows()
        elif self.current_section == "storage":
            QTimer.singleShot(0, self._render_if_current("storage"))

    def _documents_changed(self) -> None:
        if self.current_section == "storage" and self.isVisible():
            QTimer.singleShot(0, self._render_if_current("storage"))
