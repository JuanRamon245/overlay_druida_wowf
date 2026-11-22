"""Genera assets/icon.ico a partir de assets/icon.svg (usado por build_windows.bat)."""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parent.parent
app = QGuiApplication(sys.argv)
renderer = QSvgRenderer(str(root / "assets" / "icon.svg"))
img = QImage(256, 256, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
renderer.render(p)
p.end()
out = root / "assets" / "icon.ico"
if not img.save(str(out), "ICO"):
    sys.exit("No se pudo generar icon.ico")
print("Generado", out)
