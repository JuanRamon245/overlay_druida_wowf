"""Estado persistente de la ventana (JSON local en %APPDATA%\\FeralCompanion)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_W, DEFAULT_H = 380, 500
MIN_W, MIN_H = 320, 280


@dataclass
class WindowState:
    x: int | None = None
    y: int | None = None
    w: int = DEFAULT_W
    h: int = DEFAULT_H
    pinned: bool = True
    tab: str = "inicio"
    collapsed: bool = False
    opacity: float = 1.0
    font_pt: float = 9.5
    no_activate: bool = False
    scroll: dict = field(default_factory=dict)


def state_path() -> Path:
    override = os.environ.get("FERAL_COMPANION_STATE")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "FeralCompanion" / "estado.json"


def load_state(path: Path | str | None = None) -> WindowState:
    path = Path(path) if path else state_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return WindowState()
    if not isinstance(raw, dict):
        return WindowState()
    st = WindowState()
    types = {"x": int, "y": int, "w": int, "h": int, "pinned": bool, "tab": str, "collapsed": bool,
             "opacity": (int, float), "font_pt": (int, float), "no_activate": bool, "scroll": dict}
    for key, typ in types.items():
        val = raw.get(key)
        if isinstance(val, typ) and not (typ is int and isinstance(val, bool)):
            setattr(st, key, val)
    st.w = max(MIN_W, int(st.w))
    st.h = max(MIN_H, int(st.h))
    st.opacity = min(1.0, max(0.8, float(st.opacity)))
    st.font_pt = min(13.0, max(8.0, float(st.font_pt)))
    return st


def save_state(st: WindowState, path: Path | str | None = None) -> None:
    path = Path(path) if path else state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(st), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass  # sin permisos: el overlay sigue funcionando, solo no recuerda el estado


Rect = tuple[int, int, int, int]  # x, y, w, h


def ensure_on_screen(rect: Rect, screens: list[Rect], primary: Rect) -> Rect:
    """Si la cabecera de la ventana no es visible en ningún monitor (p. ej. se desconectó
    el segundo monitor), la recoloca en el monitor principal. También ajusta el tamaño."""
    x, y, w, h = rect
    header_h = 28
    for sx, sy, sw, sh in screens:
        # intersección de la franja de cabecera con la pantalla
        ix = min(x + w, sx + sw) - max(x, sx)
        iy = min(y + header_h, sy + sh) - max(y, sy)
        if ix >= 80 and iy >= header_h // 2:
            return (x, y, min(w, sw), min(h, sh))
    px, py, pw, ph = primary
    w, h = min(w, pw), min(h, ph)
    return (px + pw - w - 40, py + 80, w, h)
