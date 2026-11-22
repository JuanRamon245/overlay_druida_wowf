"""Genera los iconos SVG propios de hechizos en assets/spells/ a partir de content/hechizos.json.

Cada icono es un cuadrado redondeado con el color de su grupo y un glifo de trazo blanco.
Ejecutar tras añadir un hechizo: python scripts/make_spell_icons.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COLORS = {  # degradado arriba → abajo
    "oso": ("#a2402a", "#3d1510"),
    "gato": ("#a8821f", "#3e2c08"),
    "equilibrio": ("#4f5db0", "#1a1f46"),
    "restauracion": ("#4f943c", "#18361a"),
    "utilidad": ("#76695a", "#2a241e"),
}

HEART = '<path d="M12 20s-8-4.8-8-10.5A4.5 4.5 0 0 1 12 6.5a4.5 4.5 0 0 1 8 3C20 15.2 12 20 12 20z"/>'
BEAR = ('<circle cx="6" cy="6.5" r="2.6"/><circle cx="18" cy="6.5" r="2.6"/><circle cx="12" cy="13.5" r="7.5"/>'
        '<ellipse cx="12" cy="16.3" rx="3.2" ry="2.4"/><path d="M9 11.5h.01M15 11.5h.01"/>')
JAW = ('<path d="M3 8c3-3 15-3 18 0l-3 3H6z"/><path d="M6 11l1.5 2.5L9 11l1.5 2.5L12 11l1.5 2.5L15 11l1.5 2.5L18 11"/>'
       '<path d="M3 16c3 3 15 3 18 0l-3-2H6z"/>')
ANKH = '<path d="M12 11c-3-2.5-3.5-8 0-8s3 5.5 0 8zM5 11h14M12 11v10"/>'
PAW = ('<circle cx="12" cy="15.5" r="4"/><circle cx="5.5" cy="10" r="2"/><circle cx="9.5" cy="5.8" r="2"/>'
       '<circle cx="14.5" cy="5.8" r="2"/><circle cx="18.5" cy="10" r="2"/>')
BOLT = '<path d="M13 2 6 13h5l-1 9 7-11h-5z"/>'
ROAR = '<path d="M4 9h4l5-4v14l-5-4H4z"/>'

GLYPHS = {
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    "moon": '<path d="M15.5 3.5A8.5 8.5 0 1 0 20.5 17 7 7 0 0 1 15.5 3.5z"/>',
    "star": '<path d="M12 2.5l2.8 6 6.5.7-4.9 4.4 1.4 6.4L12 16.8 6.2 20l1.4-6.4L2.7 9.2l6.5-.7z"/>',
    "tornado": '<path d="M3 5h18M5 9h14M7.5 13h9M10 17h5M11.5 21h2"/>',
    "root": '<path d="M12 3v7c0 3-3 3-5 6s-1 5-1 5M12 10c0 3 3 3 5 6s1 5 1 5M12 13v8"/>',
    "grasp": '<path d="M4 21c0-6 2-9 4-11M12 21V8M20 21c0-6-2-9-4-11M8 10 6 7M12 8V4M16 10l2-3M2 21h20"/>',
    "thorns": '<circle cx="12" cy="12" r="5"/><path d="M12 2v5M12 17v5M2 12h5M17 12h5M5 5l3.5 3.5M15.5 15.5 19 19M5 19l3.5-3.5M15.5 8.5 19 5"/>',
    "sparkle": '<path d="M12 3l2 7 7 2-7 2-2 7-2-7-7-2 7-2z"/><path d="M19 3v3M17.5 4.5h3M5 17v3M3.5 18.5h3"/>',
    "zzz": '<path d="M4 4h6l-6 7h6M13 8h5l-5 6h5M15 16.5h4l-4 4h4"/>',
    "shield": '<path d="M12 2.5l8 3v6.5c0 5-3.5 8-8 9.5-4.5-1.5-8-4.5-8-9.5V5.5z"/><path d="M9 8c1 3-1 5 0 8M15 8c-1 3 1 5 0 8"/>',
    "heart": HEART,
    "heart_plus": HEART + '<path d="M12 9.5v6M9 12.5h6"/>',
    "soothe": '<path d="M12 15s-5-3-5-6.5A2.8 2.8 0 0 1 12 7a2.8 2.8 0 0 1 5 1.5C17 12 12 15 12 15z"/><path d="M4 19c2.5-1.5 5.5-1.5 8 0s5.5 1.5 8 0"/>',
    "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/><path d="M9.5 14.5A2.5 2.5 0 0 0 12 17"/>',
    "rip": '<path d="M12 2.5s7 7.5 7 12.5a7 7 0 0 1-14 0C5 10 12 2.5 12 2.5z"/><path d="M8 11l8 6"/>',
    "leaf": '<path d="M5 19C5 9 11 4 20 4c0 9-5 15-15 15z"/><path d="M5 19 14 10"/>',
    "paw": PAW,
    "paw_double": PAW + '<path d="M20 16v5M17.5 18.5h5"/>',
    "ankh": ANKH,
    "rebirth": ANKH + '<path d="M3 5l3 2.5M21 5l-3 2.5M2 9.5h3M22 9.5h-3"/>',
    "cross": '<path d="M12 4v16M4 12h16"/>',
    "cross_circle": '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M7 12h10"/>',
    "curse": '<circle cx="12" cy="12" r="8"/><path d="M6.5 6.5l11 11M9 10h.01M15 10h.01"/>',
    "lotus": '<path d="M12 19c-3-3-3-8 0-12 3 4 3 9 0 12z"/><path d="M12 19c-4 0-8-3-9-7 4 0 7 2 9 7zM12 19c4 0 8-3 9-7-4 0-7 2-9 7z"/><path d="M4 21h16"/>',
    "bolt": BOLT,
    "portal": '<ellipse cx="12" cy="12" rx="6.5" ry="9.5"/><path d="M14 8a3.5 3.5 0 1 0 0 8 4.5 4.5 0 0 1 0-8z"/>',
    "wave": '<path d="M2 16c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1 5-1M2 21c2.5-2 5-2 7.5 0s5 2 7.5 0"/><path d="M5 9c2-3 6-4 10-2l3-2v6l-3-2c-4 2-8 1-10-2z"/>',
    "omen": '<path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6S2 12 2 12z"/><path d="M12 8.5l1 2.5 2.5 1-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1z"/>',
    "travel": '<path d="M3 15c3-1 5-4 7-8l3 2 4-1 3 3-3 1-1 7M7 20l1-5M14 20l-1-4M9 6l1-3M12 7l2-3"/>',
    "bear": BEAR,
    "dire_bear": BEAR + '<path d="M2 22l3-3M22 22l-3-3"/>',
    "cat": '<path d="M5 20V8.5L6.5 3l4 3.8h3L17.5 3 19 8.5V20z"/><path d="M9.5 12h.01M14.5 12h.01M12 15l-1 1h2z"/>',
    "claw": '<path d="M6 4c3 4 4 10 2.5 16M11 3c3.5 4.5 4.5 11 3 18M16.5 4c3 4 3.5 9 2.5 14"/>',
    "maul": '<circle cx="8" cy="15" r="5"/><path d="M12 4l3 6M16 3l2 7M20 5v6"/>',
    "roar": ROAR + '<path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11"/>',
    "roar_down": ROAR + '<path d="M18 6v10M15 13l3 3 3-3"/>',
    "flame": '<path d="M12 21c-4 0-6.5-2.8-6.5-6.2 0-4.3 4-6 4.5-10.3 3 2 3.3 4.7 3 6.5 1-1 1.7-2.2 2-3.5 2 2 3.5 4.6 3.5 7.2 0 3.6-2.8 6.3-6.5 6.3z"/>',
    "impact": '<path d="M12 2l2 6 6-2-3 5 5 3-6 1 1 6-5-4-5 4 1-6-6-1 5-3-3-5 6 2z"/>',
    "swipe": '<path d="M4 18A11 11 0 0 1 20 6"/><path d="M8 20l2-5M13 19l1-5M18 16l-1-4"/>',
    "lacerate": '<path d="M5 3l10 10M10 2l9 9"/><path d="M8 14s3 3 3 5a3 3 0 0 1-6 0c0-2 3-5 3-5z"/>',
    "jaw": JAW,
    "bite": JAW + '<path d="M12 1v3"/>',
    "ravage": JAW + '<path d="M20 1v4M18 3h4"/>',
    "charge": '<path d="M3 12h13M12 7l5 5-5 5M3 7h5M3 17h5M20 4v16"/>',
    "prowl": '<path d="M2 11c3 4 7 5 10 5s7-1 10-5M5 14l-2 3M9 15.5l-1 3M15 15.5l1 3M19 14l2 3"/>',
    "track": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
    "shred": '<path d="M3 6l4 3 3-4 4 4 3-3 4 3M3 13l4 3 3-4 4 4 3-3 4 3M5 20h14"/>',
    "rake": '<path d="M5 3l5 9M10 3l5 9M15 3l5 9"/><path d="M12 15s3 3 3 4.8a3 3 0 0 1-6 0C9 18 12 15 12 15z"/>',
    "speed": '<path d="M9 5l7 7-7 7M15 5l6 7-6 7M2 8h5M2 12h7M2 16h5"/>',
    "cower": '<path d="M12 3v14M6 11l6 6 6-6M4 21h16"/>',
    "pounce": '<path d="M3 19c3-12 13-14 18-8"/><path d="M17 8l4 3-4 3"/>',
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
  <rect x="1.5" y="1.5" width="61" height="61" rx="11" fill="url(#g)" stroke="#0b0c0e" stroke-width="3"/>
  <rect x="4" y="4" width="56" height="56" rx="9" fill="none" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1.5"/>
  <g transform="translate(8 8) scale(2)" fill="none" stroke="#fff6e6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{glyph}</g>
</svg>
"""


def main() -> None:
    data = json.loads((ROOT / "content" / "hechizos.json").read_text(encoding="utf-8"))
    out = ROOT / "assets" / "spells"
    out.mkdir(parents=True, exist_ok=True)
    for sid, sp in data["hechizos"].items():
        c1, c2 = COLORS[sp["grupo"]]
        svg = TEMPLATE.format(c1=c1, c2=c2, glyph=GLYPHS[sp["glifo"]])
        (out / f"{sid}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"{len(data['hechizos'])} iconos en {out}")


if __name__ == "__main__":
    main()
