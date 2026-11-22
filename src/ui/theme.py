"""Hoja de estilos QSS: carbón oscuro, bronce/dorado, rojo Horda, verde druida."""

BG = "#15171b"
PANEL = "#1d2025"
HEADER = "#101215"
BORDER = "#4a3d24"
GOLD = "#d4ad62"
TEXT = "#ece7dc"
MUTED = "#a39e92"
HORDE = "#8e2420"
DRUID = "#5f7f43"

QSS = f"""
#root {{ background: {BG}; border: 1px solid {BORDER}; }}
#header {{ background: {HEADER}; border-bottom: 1px solid {BORDER}; }}
#title {{ color: {GOLD}; font-weight: 700; letter-spacing: 0.5px; }}
#chapter {{ color: {TEXT}; background: #2a2e35; border-radius: 3px; padding: 0px 5px; font-size: 8pt; }}
#badge {{ color: {TEXT}; background: {HORDE}; border-radius: 3px; padding: 0px 5px; font-size: 8pt; font-weight: 600; }}
QToolButton {{ color: {MUTED}; background: transparent; border: 1px solid transparent; border-radius: 3px;
              padding: 0px; min-width: 22px; min-height: 20px; }}
QToolButton:hover {{ color: {TEXT}; background: #2a2e35; }}
QToolButton:focus {{ border: 1px solid {GOLD}; }}
#pin {{ border: 1px solid #3a3f47; }}
#pin:checked {{ background: {GOLD}; border: 1px solid {GOLD}; }}
#close:hover {{ background: {HORDE}; color: white; }}
#totop {{ background: #2a2e35; color: {GOLD}; border: 1px solid {BORDER}; border-radius: 13px; }}
QTabBar {{ background: {HEADER}; }}
QTabBar::tab {{ background: {HEADER}; color: {MUTED}; padding: 4px 7px; border: none;
               border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {GOLD}; border-bottom: 2px solid {GOLD}; background: {PANEL}; }}
QTabBar::tab:hover:!selected {{ color: {TEXT}; }}
QTabBar QToolButton {{ background: {HEADER}; color: {GOLD}; border: 1px solid #2a2e35; min-width: 14px; }}
QTextBrowser {{ background: {PANEL}; color: {TEXT}; border: none; padding: 2px 6px; }}
QScrollBar:vertical {{ background: {PANEL}; width: 9px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #4a4f58; border-radius: 4px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {GOLD}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QScrollBar:horizontal {{ height: 0; }}
QMenu {{ background: {PANEL}; color: {TEXT}; border: 1px solid {BORDER}; }}
QMenu::item:selected {{ background: #2f343c; color: {GOLD}; }}
QToolTip {{ background: {PANEL}; color: {TEXT}; border: 1px solid {BORDER}; }}
"""
