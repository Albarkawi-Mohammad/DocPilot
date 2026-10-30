"""Generate the application-wide Qt stylesheet from theme tokens."""

from __future__ import annotations


def build_stylesheet(tokens: dict[str, str], assets: str) -> str:
    qss = r"""
/* ============================== BASE ============================== */
* {
    outline: none;
}
QWidget {
    color: @text;
    font-family: "Segoe UI Variable Text", "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QWidget:disabled {
    color: @text_muted;
}
QMainWindow {
    background-color: @bg_window;
}
QWidget#AppRoot, QWidget#Page, QWidget#PageBody, QWidget#SettingsBody,
QStackedWidget#PageStack {
    background-color: transparent;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QLabel {
    background: transparent;
}
QFrame#HeaderDivider {
    background-color: @border;
    border: none;
    min-width: 1px;
    max-width: 1px;
}
QToolTip {
    background-color: @bg_card_alt;
    color: @text;
    border: 1px solid @border_strong;
    border-radius: 6px;
    padding: 6px 9px;
    font-size: 11px;
}

/* ============================== SIDEBAR ============================== */
QFrame#Sidebar {
    background-color: @bg_sidebar;
    border: none;
    border-right: 1px solid @border_soft;
}
QLabel#SidebarSectionLabel {
    color: @text_muted;
    font-size: 9px;
    font-weight: 700;
    padding-left: 11px;
}
QFrame#WorkspaceCard {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 11px;
}
QLabel#WorkspaceTitle {
    color: @text;
    font-size: 12px;
    font-weight: 600;
}
QLabel#WorkspaceSubtitle {
    color: @text_muted;
    font-size: 10px;
}
QFrame#SidebarFooter {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 12px;
}
QLabel#SidebarFooterTitle {
    color: @text_secondary;
    font-size: 11px;
    font-weight: 600;
}
QLabel#SidebarFooterText {
    color: @text_muted;
    font-size: 10px;
}
QLabel#SidebarVersion {
    color: @text_muted;
    font-size: 9px;
}
QPushButton#SidebarNav {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    color: @text_muted;
    text-align: left;
    padding: 0 14px 0 46px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#SidebarNav:hover {
    background-color: @bg_hover;
    color: @text_secondary;
}
QPushButton#SidebarNav:checked {
    background-color: @accent_soft;
    color: @accent;
    font-weight: 600;
}
QLabel#NavIcon {
    background: transparent;
}
QLabel#NavBadge {
    background-color: @accent;
    color: #FFFFFF;
    border-radius: 8px;
    min-width: 17px;
    max-height: 17px;
    min-height: 17px;
    padding: 0 4px;
    font-size: 9px;
    font-weight: 700;
}
QLabel#NavBadge[quiet="true"] {
    background-color: @neutral_soft;
    color: @text_secondary;
}
QLabel#SidebarStatusDot {
    background-color: @success;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}

/* ============================== HEADER ============================== */
QFrame#TopHeader {
    background-color: @bg_sidebar;
    border: none;
    border-bottom: 1px solid @border_soft;
}
QLabel#BrandName {
    color: @text;
    font-size: 17px;
    font-weight: 700;
}
QLabel#BrandSub {
    color: @text_muted;
    font-size: 9px;
    font-weight: 500;
}
QLabel#PageTitle {
    color: @text;
    font-size: 17px;
    font-weight: 600;
}
QLabel#PageSubtitle {
    color: @text_muted;
    font-size: 10px;
}
QFrame#LocalStatus {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 9px;
}
QLabel#StatusDot {
    background-color: @success;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}
QLabel#StatusText {
    color: @text_secondary;
    font-size: 10px;
    font-weight: 600;
}
QLabel#StatusCaption {
    color: @text_muted;
    font-size: 9px;
}
QToolButton#HeaderIconButton {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 9px;
    padding: 0;
}
QToolButton#HeaderIconButton:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}
QToolButton#HeaderIconButton:pressed {
    background-color: @bg_active;
}
QLabel#NotificationDot {
    background-color: @danger;
    border: 2px solid @bg_sidebar;
    border-radius: 5px;
    min-width: 10px;
    max-width: 10px;
    min-height: 10px;
    max-height: 10px;
}
QToolButton#HeaderThemeButton {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 9px;
    padding: 0;
}
QToolButton#HeaderThemeButton:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}

/* ============================== CARDS ============================== */
QFrame#Card {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 14px;
}
QFrame#SoftCard {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 12px;
}
QFrame#InnerCard {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 10px;
}
QFrame#PreviewStage {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 10px;
}
QFrame#DropZone {
    background-color: @bg_card;
    border: 1.5px dashed @border_strong;
    border-radius: 16px;
}
QFrame#DropZone[dragActive="true"] {
    background-color: @accent_soft;
    border: 1.5px dashed @accent;
}
QFrame#InfoBanner {
    background-color: @accent_soft;
    border: 1px solid transparent;
    border-radius: 10px;
}
QFrame#InfoBanner[tone="warning"] {
    background-color: @warning_soft;
}
QFrame#InfoBanner[tone="success"] {
    background-color: @success_soft;
}
QFrame#InfoBanner[tone="neutral"] {
    background-color: @neutral_soft;
}
QFrame#ActivityRow {
    background: transparent;
    border: none;
}
QFrame#QueueDivider {
    background-color: @border_soft;
    border: none;
    min-height: 1px;
    max-height: 1px;
}
QFrame#SettingRow {
    background: transparent;
    border: none;
}
QFrame#SettingDivider {
    background-color: @border_soft;
    border: none;
    min-height: 1px;
    max-height: 1px;
}

/* ============================== TYPOGRAPHY ============================== */
QLabel#ContentTitle {
    color: @text;
    font-size: 22px;
    font-weight: 700;
}
QLabel#ContentSubtitle {
    color: @text_muted;
    font-size: 12px;
}
QLabel#CardTitle {
    color: @text;
    font-size: 14px;
    font-weight: 600;
}
QLabel#CardSubtitle {
    color: @text_muted;
    font-size: 11px;
}
QLabel#SectionLabel {
    color: @text_muted;
    font-size: 9px;
    font-weight: 700;
}
QLabel#StatLabel {
    color: @text_secondary;
    font-size: 11px;
    font-weight: 500;
}
QLabel#StatValue {
    color: @text;
    font-size: 29px;
    font-weight: 700;
}
QLabel#StatFootnote {
    color: @text_muted;
    font-size: 10px;
}
QLabel#StatDelta {
    color: @success;
    font-size: 10px;
    font-weight: 600;
}
QLabel#BigMetric {
    color: @text;
    font-size: 21px;
    font-weight: 700;
}
QLabel#MetricValue {
    color: @text;
    font-size: 19px;
    font-weight: 650;
}
QLabel#MetricLabel {
    color: @text_muted;
    font-size: 9px;
    font-weight: 600;
}
QLabel#MutedLabel {
    color: @text_muted;
    font-size: 11px;
}
QLabel#TableTitle {
    color: @text;
    font-size: 12px;
    font-weight: 600;
}
QLabel#TableMeta {
    color: @text_muted;
    font-size: 10px;
}
QLabel#EmptyTitle {
    color: @text;
    font-size: 16px;
    font-weight: 600;
}
QLabel#EmptyText {
    color: @text_muted;
    font-size: 11px;
}
QLabel#EmptyIcon {
    color: @text_muted;
}
QLabel#BannerTitle {
    color: @text;
    font-size: 11px;
    font-weight: 600;
}
QLabel#BannerText {
    color: @text_secondary;
    font-size: 10px;
}
QLabel#ReviewQuestion {
    color: @text;
    font-size: 20px;
    font-weight: 700;
}
QLabel#ReviewDescription {
    color: @text_secondary;
    font-size: 11px;
}
QLabel#QueueType {
    color: @text_muted;
    font-size: 9px;
    font-weight: 700;
}
QLabel#QueueTitle {
    color: @text;
    font-size: 12px;
    font-weight: 600;
}
QLabel#QueueMeta {
    color: @text_muted;
    font-size: 10px;
}
QLabel#QueueDecision {
    color: @success;
    font-size: 10px;
    font-weight: 600;
}
QLabel#FieldLabel {
    color: @text_muted;
    font-size: 10px;
}
QLabel#FieldValue {
    color: @text_secondary;
    font-size: 11px;
    font-weight: 500;
}
QLabel#FileName {
    color: @text;
    font-size: 11px;
    font-weight: 600;
}
QLabel#FileSub {
    color: @text_muted;
    font-size: 10px;
}
QLabel#PreviewPath {
    color: @text_secondary;
    font-size: 10px;
}
QLabel#LinkLabel {
    color: @accent;
    font-size: 11px;
    font-weight: 600;
}
QLabel#SettingsTitle {
    color: @text;
    font-size: 18px;
    font-weight: 650;
}
QLabel#SettingsDescription {
    color: @text_muted;
    font-size: 11px;
}
QLabel#SettingTitle {
    color: @text;
    font-size: 12px;
    font-weight: 600;
}
QLabel#SettingDescription {
    color: @text_muted;
    font-size: 10px;
}
QLabel#DangerText {
    color: @danger;
}
QLabel#SuccessText {
    color: @success;
}
QLabel#LogTime {
    color: @text_muted;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 9px;
}
QLabel#LogMessage {
    color: @text_secondary;
    font-size: 10px;
}
QLabel#LogLevel {
    color: @text_muted;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 8px;
    font-weight: 600;
}
QLabel#StageName {
    color: @text;
    font-size: 12px;
    font-weight: 600;
}
QLabel#StageDescription {
    color: @text_muted;
    font-size: 10px;
}
QLabel#CurrentStage {
    color: @text_secondary;
    font-size: 11px;
}
QLabel#IntegrationMeta {
    color: @text_muted;
    font-size: 10px;
}
QLabel#PageNumber {
    color: @text_muted;
    font-size: 9px;
}
QLabel#CategoryName {
    color: @text;
    font-size: 12px;
    font-weight: 500;
}
QLabel#CategoryCount {
    color: @text_muted;
    font-size: 10px;
}

/* ============================== BADGES ============================== */
QLabel#Badge {
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 9px;
    font-weight: 650;
    background-color: @neutral_soft;
    color: @text_secondary;
}
QLabel#Badge[tone="accent"] {
    background-color: @accent_soft;
    color: @accent;
}
QLabel#Badge[tone="success"] {
    background-color: @success_soft;
    color: @success;
}
QLabel#Badge[tone="warning"] {
    background-color: @warning_soft;
    color: @warning;
}
QLabel#Badge[tone="danger"] {
    background-color: @danger_soft;
    color: @danger;
}
QLabel#Badge[tone="info"] {
    background-color: @info_soft;
    color: @info;
}
QLabel#Badge[tone="purple"] {
    background-color: @purple_soft;
    color: @purple;
}
QLabel#Badge[tone="neutral"] {
    background-color: @neutral_soft;
    color: @text_secondary;
}
QLabel#IconTile {
    border-radius: 10px;
    background-color: @neutral_soft;
}
QLabel#IconTile[tone="accent"] { background-color: @accent_soft; }
QLabel#IconTile[tone="success"] { background-color: @success_soft; }
QLabel#IconTile[tone="warning"] { background-color: @warning_soft; }
QLabel#IconTile[tone="danger"] { background-color: @danger_soft; }
QLabel#IconTile[tone="info"] { background-color: @info_soft; }
QLabel#IconTile[tone="purple"] { background-color: @purple_soft; }

/* ============================== BUTTONS ============================== */
QPushButton {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 18px;
}
QPushButton#PrimaryButton {
    background-color: @accent;
    color: #FFFFFF;
    border: 1px solid @accent;
}
QPushButton#PrimaryButton:hover {
    background-color: @accent_hover;
    border-color: @accent_hover;
}
QPushButton#PrimaryButton:pressed {
    background-color: @accent_pressed;
    border-color: @accent_pressed;
}
QPushButton#PrimaryButton:disabled {
    background-color: @neutral_soft;
    color: @text_muted;
    border-color: transparent;
}
QPushButton#SecondaryButton {
    background-color: @bg_card;
    color: @text_secondary;
    border: 1px solid @border;
}
QPushButton#SecondaryButton:hover {
    background-color: @bg_hover;
    color: @text;
    border-color: @border_strong;
}
QPushButton#SecondaryButton:disabled {
    background-color: transparent;
    color: @text_muted;
    border-color: @border_soft;
}
QPushButton#GhostButton {
    background: transparent;
    color: @text_secondary;
    border: 1px solid transparent;
    padding: 7px 11px;
}
QPushButton#GhostButton:hover {
    background-color: @bg_hover;
    color: @text;
}
QPushButton#GhostButton:disabled {
    color: @text_muted;
    background: transparent;
}
QPushButton#DangerButton {
    background-color: @danger_soft;
    color: @danger;
    border: 1px solid transparent;
}
QPushButton#DangerButton:hover {
    border-color: @danger;
}
QPushButton#LinkButton {
    background: transparent;
    color: @accent;
    border: none;
    padding: 4px 2px;
    font-weight: 600;
}
QPushButton#LinkButton:hover {
    color: @accent_hover;
    text-decoration: underline;
}
QPushButton#QuickAction {
    background-color: @bg_card_alt;
    color: @text;
    border: 1px solid @border_soft;
    border-radius: 9px;
    text-align: left;
    padding: 10px 13px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#QuickAction:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}
QPushButton#QuickActionPrimary {
    background-color: @accent;
    color: #FFFFFF;
    border: 1px solid @accent;
    border-radius: 9px;
    text-align: left;
    padding: 10px 13px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#QuickActionPrimary:hover {
    background-color: @accent_hover;
    border-color: @accent_hover;
}
QPushButton#OptionCard {
    background-color: @bg_input;
    color: @text_secondary;
    border: 1px solid @border;
    border-radius: 10px;
    text-align: left;
    padding: 11px 13px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#OptionCard:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
    color: @text;
}
QPushButton#OptionCard:checked {
    background-color: @accent_soft;
    border-color: @accent;
    color: @text;
    font-weight: 600;
}
QPushButton#PageThumb {
    background-color: #F7F5EE;
    color: #5C6676;
    border: 1px solid @border;
    border-radius: 4px;
    padding: 2px;
    font-size: 8px;
    font-weight: 600;
}
QPushButton#PageThumb:checked {
    border: 2px solid @accent;
}
QPushButton#PageThumb:hover {
    border-color: @accent;
}
QToolButton#IconButton {
    background-color: transparent;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 5px;
}
QToolButton#IconButton:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}
QToolButton#BareIconButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 4px;
}
QToolButton#BareIconButton:hover {
    background-color: @bg_hover;
}
QPushButton#SettingsNavButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: @text_muted;
    text-align: left;
    padding: 0 12px 0 40px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#SettingsNavButton:hover {
    background-color: @bg_hover;
    color: @text_secondary;
}
QPushButton#SettingsNavButton:checked {
    background-color: @accent_soft;
    color: @accent;
    font-weight: 600;
}

/* ============================== INPUTS ============================== */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: @bg_input;
    color: @text;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 7px 10px;
    min-height: 20px;
    selection-background-color: @accent;
    selection-color: #FFFFFF;
    font-size: 12px;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: @border_strong;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: @accent;
    background-color: @bg_card;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: @bg_card_alt;
    color: @text_muted;
    border-color: @border_soft;
}
QLineEdit#SearchInput {
    padding-left: 9px;
}
QComboBox {
    padding-right: 28px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 26px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: url("@ASSETS/chevron_down.svg");
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background-color: @bg_card_alt;
    color: @text;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 5px;
    selection-background-color: @accent_soft;
    selection-color: @text;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 3px 8px;
    border-radius: 5px;
}
QCheckBox {
    color: @text_secondary;
    font-size: 11px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 1px solid @border_strong;
    border-radius: 5px;
    background-color: @bg_input;
}
QCheckBox::indicator:hover {
    border-color: @accent;
}
QCheckBox::indicator:checked {
    background-color: @accent;
    border-color: @accent;
    image: url("@ASSETS/check.svg");
}
QCheckBox::indicator:disabled {
    background-color: @bg_card_alt;
    border-color: @border;
}
QRadioButton {
    color: @text_secondary;
    font-size: 11px;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid @border_strong;
    border-radius: 8px;
    background-color: @bg_input;
}
QRadioButton::indicator:checked {
    background-color: @accent;
    border: 4px solid @bg_card;
    image: url("@ASSETS/radio_dot.svg");
}

/* ============================== TABLES / TREES ============================== */
QTableWidget, QTableView {
    background-color: transparent;
    alternate-background-color: transparent;
    border: none;
    gridline-color: transparent;
    color: @text_secondary;
    selection-background-color: @selection;
    selection-color: @text;
    outline: 0;
}
QTableWidget::item, QTableView::item {
    border: none;
    border-bottom: 1px solid @border_soft;
    padding-left: 10px;
    padding-right: 8px;
    color: @text_secondary;
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: @bg_hover;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: @selection;
    color: @text;
}
QHeaderView {
    background: transparent;
    border: none;
}
QHeaderView::section {
    background-color: transparent;
    color: @text_muted;
    border: none;
    border-bottom: 1px solid @border_soft;
    padding: 8px 8px;
    font-size: 9px;
    font-weight: 650;
}
QHeaderView::section:first {
    padding-left: 10px;
}
QTableCornerButton::section {
    background: transparent;
    border: none;
}
QTreeWidget, QTreeView {
    background-color: transparent;
    border: none;
    outline: 0;
    color: @text_secondary;
    show-decoration-selected: 0;
}
QTreeWidget::item, QTreeView::item {
    min-height: 31px;
    padding: 2px 5px;
    border-radius: 7px;
    border: none;
}
QTreeWidget::item:hover, QTreeView::item:hover {
    background-color: @bg_hover;
}
QTreeWidget::item:selected, QTreeView::item:selected {
    background-color: @accent_soft;
    color: @text;
}
QTreeWidget::branch, QTreeView::branch {
    background: transparent;
}
QTreeWidget::branch:has-children:closed, QTreeView::branch:has-children:closed {
    image: url("@ASSETS/chevron_right.svg");
}
QTreeWidget::branch:has-children:open, QTreeView::branch:has-children:open {
    image: url("@ASSETS/chevron_down.svg");
}
QListWidget, QListView {
    background: transparent;
    border: none;
    outline: 0;
}

/* ============================== QUEUE ITEMS ============================== */
QFrame#ReviewQueueItem {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 11px;
}
QFrame#ReviewQueueItem:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}
QFrame#ReviewQueueItem[selected="true"] {
    background-color: @accent_soft;
    border-color: @accent;
}
QFrame#FileRow {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 10px;
}
QFrame#FileRow:hover {
    border-color: @border_strong;
}
QFrame#ArchiveDocRow {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 10px;
}
QFrame#ArchiveDocRow:hover {
    background-color: @bg_hover;
    border-color: @border_strong;
}
QFrame#ArchiveDocRow[selected="true"] {
    background-color: @accent_soft;
    border-color: @accent;
}
QFrame#ReviewPreview {
    background-color: @bg_card_alt;
    border: 1px solid @border_soft;
    border-radius: 11px;
}
QFrame#StageRow {
    background: transparent;
    border: none;
}
QLabel#StageDot {
    border-radius: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    font-size: 10px;
    font-weight: 700;
    border: 1px solid @border_strong;
    background-color: @bg_input;
    color: @text_muted;
}
QLabel#StageDot[stage="running"] {
    background-color: @accent_soft;
    border: 2px solid @accent;
    color: @accent;
}
QLabel#StageDot[stage="completed"] {
    background-color: @success_soft;
    border: 1px solid @success;
    color: @success;
}
QLabel#StageDot[stage="needs_review"] {
    background-color: @warning_soft;
    border: 1px solid @warning;
    color: @warning;
}
QLabel#StageDot[stage="failed"] {
    background-color: @danger_soft;
    border: 1px solid @danger;
    color: @danger;
}
QFrame#StageConnector {
    background-color: @border;
    border: none;
    min-width: 1px;
    max-width: 1px;
}
QFrame#StageConnector[completed="true"] {
    background-color: @success;
}
QFrame#LogRow {
    background: transparent;
    border: none;
}
QLabel#LogDot {
    border-radius: 3px;
    min-width: 6px;
    max-width: 6px;
    min-height: 6px;
    max-height: 6px;
    background-color: @accent;
}
QLabel#LogDot[level="success"] { background-color: @success; }
QLabel#LogDot[level="warning"] { background-color: @warning; }
QLabel#LogDot[level="error"] { background-color: @danger; }
QLabel#LogDot[level="muted"] { background-color: @text_muted; }

/* ============================== PROGRESS ============================== */
QProgressBar {
    background-color: @bg_input;
    border: none;
    border-radius: 4px;
    min-height: 7px;
    max-height: 7px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: @accent;
    border-radius: 4px;
}
QProgressBar#SuccessProgress::chunk {
    background-color: @success;
}
QProgressBar#ThinProgress {
    min-height: 4px;
    max-height: 4px;
}
QProgressBar#ThinProgress::chunk {
    border-radius: 2px;
}
QProgressBar#StageSweep {
    min-height: 2px;
    max-height: 2px;
}
QProgressBar#StageSweep::chunk {
    background-color: @accent;
    border-radius: 1px;
}

/* ============================== SCROLLBARS ============================== */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: @scrollbar;
    min-height: 28px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background-color: @scrollbar_hover;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: @scrollbar;
    min-width: 28px;
    border-radius: 3px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: transparent;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ============================== SPLITTER / MENU / MISC ============================== */
QSplitter::handle {
    background-color: transparent;
    width: 14px;
    height: 14px;
}
QSplitter::handle:hover {
    background-color: transparent;
}
QMenu {
    background-color: @bg_card_alt;
    border: 1px solid @border;
    border-radius: 10px;
    padding: 6px;
    color: @text;
}
QMenu::item {
    background: transparent;
    padding: 7px 22px 7px 10px;
    border-radius: 6px;
    font-size: 11px;
}
QMenu::item:selected {
    background-color: @bg_hover;
    color: @text;
}
QMenu::separator {
    height: 1px;
    background-color: @border_soft;
    margin: 5px 8px;
}
QFrame#Toast {
    background-color: @bg_card_alt;
    border: 1px solid @border_strong;
    border-radius: 10px;
}
QLabel#ToastText {
    color: @text;
    font-size: 11px;
    font-weight: 500;
}
QFrame#SettingsNav {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 14px;
}
QFrame#SettingsSection {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 14px;
}
QFrame#ReviewFooter {
    background-color: @bg_card;
    border: none;
    border-top: 1px solid @border_soft;
}
QFrame#QueuePanel {
    background-color: @bg_card;
    border: 1px solid @border;
    border-radius: 14px;
}
"""
    for key, value in tokens.items():
        qss = qss.replace(f"@{key}", value)
    qss = qss.replace("@ASSETS", assets)
    return qss
