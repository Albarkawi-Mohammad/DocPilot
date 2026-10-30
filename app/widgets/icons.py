"""Inline SVG icon set and small pixmap helpers.

Keeping icons as SVG markup avoids external image dependencies and lets every
icon be re-colored for the active theme.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer

_ICON_PATHS: dict[str, str] = {
    "dashboard": (
        '<rect width="7" height="7" x="3" y="3" rx="1.6"/>'
        '<rect width="7" height="7" x="14" y="3" rx="1.6"/>'
        '<rect width="7" height="7" x="14" y="14" rx="1.6"/>'
        '<rect width="7" height="7" x="3" y="14" rx="1.6"/>'
    ),
    "scan": (
        '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>'
        '<path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>'
        '<path d="M7 12h10"/>'
    ),
    "processing": (
        '<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/>'
        '<path d="M8.5 19H15a3.5 3.5 0 0 0 0-7H9a3.5 3.5 0 0 1 0-7h6.5"/>'
    ),
    "documents": (
        '<path d="M8 3h8l4 4v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>'
        '<path d="M15 3v5h5"/><path d="M10 13h6"/><path d="M10 17h4"/>'
        '<path d="M5 7v12a2 2 0 0 0 2 2h9"/>'
    ),
    "review": (
        '<rect width="8" height="4" x="8" y="2" rx="1"/>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<path d="m9 14 2 2 4-4"/>'
    ),
    "archive": (
        '<rect width="20" height="5" x="2" y="3" rx="1"/>'
        '<path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/>'
        '<path d="M10 12h4"/>'
    ),
    "settings": (
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "bell": (
        '<path d="M10.268 21a2 2 0 0 0 3.464 0"/>'
        '<path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.41 5.956-2.738 7.326"/>'
    ),
    "sun": (
        '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/>'
        '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
        '<path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/>'
        '<path d="m19.07 4.93-1.41 1.41"/>'
    ),
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "search": '<circle cx="11" cy="11" r="7.5"/><path d="m21 21-4.35-4.35"/>',
    "filter": '<path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "minus": '<path d="M5 12h14"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": (
        '<circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 5-5"/>'
    ),
    "alert-triangle": (
        '<path d="M10.3 3.7 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/>'
        '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    ),
    "alert-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "users": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "calendar": (
        '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/>'
        '<path d="M3 10h18"/>'
    ),
    "building": (
        '<rect x="4" y="2" width="16" height="20" rx="2"/>'
        '<path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/>'
        '<path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M16 10h.01"/><path d="M8 10h.01"/>'
        '<path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/>'
    ),
    "heart-pulse": (
        '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>'
        '<path d="M3.22 12H9.5l.5-1 2 4 .5-3 1.5 2h5.27"/>'
    ),
    "car": (
        '<path d="M19 17h2l.4-2.6c.1-.8-.2-1.5-.8-2l-1.7-1.3-2-3.3A2 2 0 0 0 15.2 7H8.8a2 2 0 0 0-1.7 1L5.1 11.3 3.4 12.6c-.6.5-.9 1.2-.8 2L3 17h2"/>'
        '<circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M9 17h6"/>'
    ),
    "landmark": (
        '<path d="M3 22h18"/><path d="M6 18v-7"/><path d="M10 18v-7"/>'
        '<path d="M14 18v-7"/><path d="M18 18v-7"/><path d="m12 2 8 4H4Z"/>'
    ),
    "receipt": (
        '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/>'
        '<path d="M8 7h8"/><path d="M8 11h8"/><path d="M8 15h5"/>'
    ),
    "briefcase": (
        '<rect width="20" height="14" x="2" y="7" rx="2"/>'
        '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'
    ),
    "folder": (
        '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>'
    ),
    "folder-plus": (
        '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>'
        '<path d="M12 10v6"/><path d="M9 13h6"/>'
    ),
    "file-text": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
    ),
    "file-plus": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M9 15h6"/><path d="M12 12v6"/>'
    ),
    "file-check": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/>'
    ),
    "trash": (
        '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'
        '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
        '<path d="M10 11v6"/><path d="M14 11v6"/>'
    ),
    "upload": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>'
    ),
    "upload-cloud": (
        '<path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>'
        '<path d="M12 12v9"/><path d="m16 16-4-4-4 4"/>'
    ),
    "play": '<path d="M7 4.5v15l13-7.5Z"/>',
    "pause": '<rect x="6" y="4" width="4" height="16" rx="1.2"/><rect x="14" y="4" width="4" height="16" rx="1.2"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "refresh": (
        '<path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"/><path d="M3 3v5h5"/>'
    ),
    "rotate": (
        '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>'
    ),
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "chevron-up": '<path d="m18 15-6-6-6 6"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-up-right": '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
    "shield": (
        '<path d="M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1 1 0 0 1 1.5 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1Z"/>'
    ),
    "shield-check": (
        '<path d="M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1 1 0 0 1 1.5 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1Z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "lock": (
        '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    ),
    "eye": (
        '<path d="M2.06 12.35a1 1 0 0 1 0-.7C3.66 7.6 7.5 4.5 12 4.5s8.34 3.1 9.94 7.15a1 1 0 0 1 0 .7C20.34 16.4 16.5 19.5 12 19.5S3.66 16.4 2.06 12.35Z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>'
        '<path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/>'
    ),
    "hard-drive": (
        '<rect width="20" height="8" x="2" y="2" rx="2"/><rect width="20" height="8" x="2" y="14" rx="2"/>'
        '<path d="M6 6h.01"/><path d="M6 18h.01"/>'
    ),
    "server": (
        '<rect width="20" height="8" x="2" y="2" rx="2"/><rect width="20" height="8" x="2" y="14" rx="2"/>'
        '<path d="M6 6h.01"/><path d="M6 18h.01"/>'
    ),
    "scanner": (
        '<path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>'
        '<rect x="6" y="14" width="12" height="8" rx="1"/>'
    ),
    "cpu": (
        '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>'
        '<path d="M9 2v2"/><path d="M15 2v2"/><path d="M9 20v2"/><path d="M15 20v2"/>'
        '<path d="M2 9h2"/><path d="M2 15h2"/><path d="M20 9h2"/><path d="M20 15h2"/>'
    ),
    "sparkles": (
        '<path d="m12 3-1.9 5.8L4.3 10.7l5.8 1.9L12 18.4l1.9-5.8 5.8-1.9-5.8-1.9Z"/>'
        '<path d="M19 3v4"/><path d="M21 5h-4"/><path d="M5 17v3"/><path d="M6.5 18.5h-3"/>'
    ),
    "languages": (
        '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/>'
        '<path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>'
    ),
    "palette": (
        '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/>'
        '<circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/>'
        '<circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/>'
        '<circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/>'
        '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.44-.16-.86-.46-1.16-.3-.3-.44-.7-.44-1.15a1.64 1.64 0 0 1 1.65-1.63h1.93C19.3 16.37 22 13.65 22 10.2 22 5.66 17.5 2 12 2Z"/>'
    ),
    "sliders": (
        '<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/>'
        '<line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/>'
        '<line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/>'
        '<line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/>'
        '<line x1="18" x2="22" y1="16" y2="16"/>'
    ),
    "link": (
        '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
    ),
    "plug": (
        '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/>'
        '<path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>'
    ),
    "cloud-off": (
        '<path d="m2 2 20 20"/><path d="M5.78 5.78A7 7 0 0 0 4 14.9"/>'
        '<path d="M15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.24"/><path d="M9.5 4.5A7 7 0 0 1 15.2 6"/>'
    ),
    "inbox": (
        '<path d="M22 12h-6l-2 3h-4l-2-3H2"/>'
        '<path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/>'
    ),
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "list": (
        '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/>'
        '<path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>'
    ),
    "external-link": (
        '<path d="M15 3h6v6"/><path d="M10 14 21 3"/>'
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    ),
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "grid": (
        '<rect width="7" height="7" x="3" y="3" rx="1.5"/><rect width="7" height="7" x="14" y="3" rx="1.5"/>'
        '<rect width="7" height="7" x="14" y="14" rx="1.5"/><rect width="7" height="7" x="3" y="14" rx="1.5"/>'
    ),
    "chart": (
        '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>'
    ),
    "hash": (
        '<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/>'
        '<line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>'
    ),
}

_icon_cache: dict[tuple[str, str, int, float], QIcon] = {}
_pixmap_cache: dict[tuple[str, str, int, float], QPixmap] = {}


def make_pixmap(name: str, color: str, size: int = 18, stroke: float = 1.8) -> QPixmap:
    """Render an inline SVG icon at 2x resolution for crisp high-DPI output."""
    key = (name, color, size, stroke)
    cached = _pixmap_cache.get(key)
    if cached is not None:
        return cached

    body = _ICON_PATHS.get(name, _ICON_PATHS["file-text"])
    body = body.replace("currentColor", color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size * 2}" height="{size * 2}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2.0)
    _pixmap_cache[key] = pixmap
    return pixmap


def make_icon(name: str, color: str, size: int = 18, stroke: float = 1.8) -> QIcon:
    key = (name, color, size, stroke)
    cached = _icon_cache.get(key)
    if cached is not None:
        return cached
    icon = QIcon(make_pixmap(name, color, size, stroke))
    _icon_cache[key] = icon
    return icon


def make_avatar_icon(initials: str, color: str, size: int = 28) -> QIcon:
    """Circular initials icon used by option cards and menus."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(0, 0, size * 2, size * 2)
    font = QFont("Segoe UI", max(7, int(size * 0.72)))
    font.setWeight(QFont.Weight.DemiBold)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(
        QRectF(0, 0, size * 2, size * 2), Qt.AlignmentFlag.AlignCenter, initials
    )
    painter.end()
    pixmap.setDevicePixelRatio(2.0)
    return QIcon(pixmap)


def make_logo_pixmap(size: int = 64) -> QPixmap:
    """Paint the DocPilot app mark: a document carrying a pilot arrow."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    s = float(size * 2)

    gradient = QLinearGradient(0, 0, s, s)
    gradient.setColorAt(0.0, QColor("#7F98FF"))
    gradient.setColorAt(1.0, QColor("#4767F2"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.drawRoundedRect(QRectF(0, 0, s, s), s * 0.27, s * 0.27)

    # Soft highlight in the top-left corner.
    painter.setBrush(QColor(255, 255, 255, 22))
    painter.drawEllipse(QPointF(s * 0.24, s * 0.18), s * 0.42, s * 0.3)

    # Document sheet.
    sheet = QPainterPath()
    left, top, width, height = s * 0.27, s * 0.19, s * 0.40, s * 0.55
    fold = width * 0.27
    sheet.moveTo(left, top + s * 0.05)
    sheet.quadTo(left, top, left + s * 0.05, top)
    sheet.lineTo(left + width - fold, top)
    sheet.lineTo(left + width, top + fold)
    sheet.lineTo(left + width, top + height - s * 0.05)
    sheet.quadTo(left + width, top + height, left + width - s * 0.05, top + height)
    sheet.lineTo(left + s * 0.05, top + height)
    sheet.quadTo(left, top + height, left, top + height - s * 0.05)
    sheet.closeSubpath()
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawPath(sheet)

    # Folded corner.
    fold_path = QPainterPath()
    fold_path.moveTo(left + width - fold, top)
    fold_path.lineTo(left + width, top + fold)
    fold_path.lineTo(left + width - fold, top + fold)
    fold_path.closeSubpath()
    painter.setBrush(QColor("#DCE5FF"))
    painter.drawPath(fold_path)

    # Document text lines.
    painter.setPen(QPen(QColor("#7D95F7"), max(1.4, s * 0.022), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for index, line_width in enumerate((0.23, 0.18, 0.21)):
        y = top + height * (0.40 + index * 0.14)
        painter.drawLine(QPointF(left + width * 0.17, y), QPointF(left + width * 0.17 + width * line_width, y))

    # Pilot arrow sweeping out of the document.
    plane = QPainterPath()
    plane.moveTo(s * 0.50, s * 0.58)
    plane.lineTo(s * 0.86, s * 0.43)
    plane.lineTo(s * 0.66, s * 0.82)
    plane.lineTo(s * 0.61, s * 0.67)
    plane.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#8FE3FF"))
    painter.drawPath(plane)
    painter.setBrush(QColor("#FFFFFF"))
    plane_inner = QPainterPath()
    plane_inner.moveTo(s * 0.58, s * 0.61)
    plane_inner.lineTo(s * 0.79, s * 0.52)
    plane_inner.lineTo(s * 0.66, s * 0.73)
    plane_inner.closeSubpath()
    painter.drawPath(plane_inner)

    painter.end()
    pixmap.setDevicePixelRatio(2.0)
    return pixmap
