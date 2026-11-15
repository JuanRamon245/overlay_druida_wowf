"""Feral Companion — Forever Overlay. Punto de entrada."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from content import ContentError, base_dir, load_guide  # noqa: E402
from overlay_window import OverlayWindow  # noqa: E402
from state import load_state  # noqa: E402


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Feral Companion")
    app.setWindowIcon(QIcon(str(base_dir() / "assets" / "icon.svg")))
    try:
        guide = load_guide()
    except (OSError, ValueError, ContentError) as exc:
        QMessageBox.critical(None, "Feral Companion", f"No se pudo cargar la guía:\n\n{exc}")
        return 1
    win = OverlayWindow(guide, load_state())
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
