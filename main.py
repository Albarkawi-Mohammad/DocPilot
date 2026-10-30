"""DocPilot desktop preview entrypoint.

Launch with:
    .\\.venv\\Scripts\\python.exe main.py

Everything shown is local sample data. No OCR, AI model, scanner, network, or
file organisation backend is implemented in this UI preview.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app import __app_name__, __version__
from app.main_window import MainWindow
from app.services.app_state import AppState
from app.theme.theme import ThemeManager
from app.widgets.icons import make_logo_pixmap


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setOrganizationName("DocPilot Local")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(make_logo_pixmap(64)))

    theme = ThemeManager("dark")
    theme.attach(app)

    state = AppState()
    window = MainWindow(state, theme)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
