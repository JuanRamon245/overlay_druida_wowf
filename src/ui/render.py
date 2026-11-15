"""Convierte el contenido JSON de una pestaña en HTML compacto para QTextBrowser."""
from __future__ import annotations

import html
import re

from content import expand_route, tree_totals

# Paleta (se repite en theme.py para QSS)
GOLD = "#d4ad62"
TEXT = "#ece7dc"
MUTED = "#a39e92"
ROW_A = "#22262c"
ROW_B = "#1b1e23"
LINE = "#343941"
GREEN = "#8fb86a"
AMBER = "#e0b24a"
RED = "#c8504a"

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_TAGS = [
    (re.compile(r"\b(orientativos?|orientativas?|sin confirmar|sin verificar)\b", re.I), AMBER),
    (re.compile(r"\b(confirmado)\b", re.I), GREEN),
]
ESTADO = {
    "confirmado": (GREEN, "✔ CONFIRMADO"),
    "orientativo": (AMBER, "≈ ORIENTATIVO"),
    "pendiente": (RED, "? PENDIENTE"),
}


def inline(text: str) -> str:
    """Escapa HTML y aplica **negrita** y resaltado de etiquetas de certeza."""
    out = html.escape(str(text), quote=False)
    out = _BOLD.sub(lambda m: f'<b style="color:{TEXT}">{m.group(1)}</b>', out)
    for rx, color in _TAGS:
        out = rx.sub(lambda m, c=color: f'<span style="color:{c}">{m.group(1)}</span>', out)
    return out


def _table(header: list[str] | None, rows: list[list[str]], first_col_gold: bool = True) -> str:
    parts = ['<table width="100%" cellspacing="0" cellpadding="3" '
             'style="border-collapse:collapse; margin-top:2px; margin-bottom:6px;">']
    if header:
        parts.append("<tr>" + "".join(
            f'<th align="left" style="background:{LINE}; color:{GOLD}; font-weight:600;">{inline(h)}</th>'
            for h in header) + "</tr>")
    for i, row in enumerate(rows):
        bg = ROW_A if i % 2 == 0 else ROW_B
        cells = []
        for j, cell in enumerate(row):
            style = f"background:{bg};"
            if j == 0 and first_col_gold:
                style += f" color:{GOLD}; white-space:nowrap;"
            cells.append(f'<td valign="top" style="{style}">{inline(cell)}</td>')
        parts.append("<tr>" + "".join(cells) + "</tr>")
    parts.append("</table>")
    return "".join(parts)


def _list(items: list[str], numbered: bool) -> str:
    tag = "ol" if numbered else "ul"
    lis = "".join(f'<li style="margin-bottom:2px;">{inline(i)}</li>' for i in items)
    return f'<{tag} style="margin-top:0px; margin-bottom:6px; margin-left:-18px;">{lis}</{tag}>'


def _aviso(estado: str, texto: str) -> str:
    color, label = ESTADO.get(estado, ESTADO["orientativo"])
    return ('<table width="100%" cellspacing="0" cellpadding="4" style="margin-bottom:6px;">'
            f'<tr><td width="3" style="background:{color};"></td>'
            f'<td style="background:{ROW_B};"><span style="color:{color}; font-size:small; font-weight:600;">'
            f'{label}</span><br>{inline(texto)}</td></tr></table>')


def _talents(guide: dict) -> str:
    tal = guide["talentos"]
    trees = tal["arboles"]
    expanded = expand_route(tal)
    rows = []
    for step in tal["ruta"]:
        info = trees[step["arbol"]][step["talento"]]
        lv = str(step["desde"]) if step["desde"] == step["hasta"] else f"{step['desde']}–{step['hasta']}"
        reached = max(e["rango"] for e in expanded
                      if e["talento"] == step["talento"] and e["nivel"] <= step["hasta"])
        tree_tag = "" if step["arbol"] == "Combate feral" else f' <span style="color:{GREEN}">[Resto]</span>'
        name = (f'<b style="color:{TEXT}">{html.escape(info["es"])}</b>{tree_tag}<br>'
                f'<span style="color:{MUTED}">({html.escape(step["talento"])})</span>')
        flag = "" if info["certeza"] == "confirmado" else f' <span style="color:{AMBER}">≈</span>'
        rows.append((lv, name, f"{reached}/{info['max']}{flag}", inline(step["funcion"])))
    parts = ['<table width="100%" cellspacing="0" cellpadding="3" style="border-collapse:collapse;">',
             "<tr>" + "".join(f'<th align="left" style="background:{LINE}; color:{GOLD};">{h}</th>'
                              for h in ("Nv", "Talento", "Rango", "Función")) + "</tr>"]
    for i, (lv, name, rk, fn) in enumerate(rows):
        bg = ROW_A if i % 2 == 0 else ROW_B
        parts.append(f'<tr><td valign="top" style="background:{bg}; color:{GOLD}; white-space:nowrap;">{lv}</td>'
                     f'<td valign="top" style="background:{bg};">{name}</td>'
                     f'<td valign="top" style="background:{bg}; white-space:nowrap;">{rk}</td>'
                     f'<td valign="top" style="background:{bg};">{fn}</td></tr>')
    parts.append("</table>")
    totals = tree_totals(tal)
    total = sum(totals.values())
    parts.append(f'<p style="margin-top:4px; color:{MUTED};">Total: <b style="color:{GOLD}">'
                 f'0 / {totals.get("Combate feral", 0)} / {totals.get("Restauración", 0)} = {total} puntos</b> '
                 f'(sumado automáticamente) · <span style="color:{AMBER}">≈</span> = fila/requisito orientativo.<br>'
                 f'Validado con: {html.escape(tal["validado_con"])}.</p>')
    return "".join(parts)


def _index(tab: dict) -> str:
    links = [f'<a href="#{s["ancla"]}" style="color:{GOLD}; text-decoration:none;">'
             f'{html.escape(s["titulo"].split(" · ")[0])}</a>'
             for s in tab["secciones"] if s.get("ancla")]
    return f'<p style="margin-bottom:6px;">{" &nbsp;·&nbsp; ".join(links)}</p>'


def _fuentes(guide: dict) -> str:
    meta = guide["meta"]
    out = [_table(None, [
        ["Juego", meta["juego"]],
        ["Cliente", meta["cliente_revisado"]],
        ["Revisado", meta["fecha_revision"]],
        ["Contenido", "v" + meta["version_contenido"]],
    ])]
    rows = []
    for f in guide.get("_fuentes", {}).get("fuentes", []):
        rows.append(f'<a href="{html.escape(f["url"])}" style="color:{GOLD};">{html.escape(f["titulo"])}</a>'
                    f'<br><span style="color:{MUTED}">{html.escape(f["fecha"])} · {html.escape(f["estado"])}</span>'
                    f'<br>{html.escape(f["uso"])}')
    out.append('<table width="100%" cellspacing="0" cellpadding="3">' + "".join(
        f'<tr><td style="background:{ROW_A if i % 2 == 0 else ROW_B};">{r}</td></tr>'
        for i, r in enumerate(rows)) + "</table>")
    out.append(f'<p style="color:{MUTED};">Los enlaces abren tu navegador solo si haces clic. '
               'La guía funciona sin conexión. Correcciones detalladas: docs/VALIDACION.md.</p>')
    return "".join(out)


def render_block(guide: dict, tab: dict, blk: dict) -> str:
    t = blk["tipo"]
    if t == "texto":
        return f'<p style="margin-top:0px; margin-bottom:6px;">{inline(blk["texto"])}</p>'
    if t == "lista":
        return _list(blk["items"], blk.get("numerada", False))
    if t == "tabla":
        return _table(blk.get("cabecera"), blk["filas"])
    if t == "tarjeta":
        return _table(None, blk["campos"])
    if t == "aviso":
        return _aviso(blk.get("estado", "orientativo"), blk["texto"])
    if t == "talentos":
        return _talents(guide)
    if t == "indice":
        return _index(tab)
    if t == "fuentes":
        return _fuentes(guide)
    return ""


def render_tab(guide: dict, tab: dict) -> str:
    parts = [f'<html><body style="color:{TEXT};">']
    if tab["id"] == "inicio":
        meta = guide["meta"]
        parts.append(f'<p style="color:{MUTED}; font-size:small; margin-bottom:4px;">{html.escape(meta["subtitulo"])}'
                     f' · revisado {html.escape(meta["fecha_revision"])}'
                     f' · cliente {html.escape(meta["cliente_revisado"].split(" ")[0])}</p>')
    for sec in tab.get("secciones", []):
        anchor = f'<a name="{sec["ancla"]}"></a>' if sec.get("ancla") else ""
        parts.append(f'<h3 style="color:{GOLD}; margin-top:8px; margin-bottom:3px; font-size:medium;">'
                     f'{anchor}{html.escape(sec["titulo"])}</h3>')
        for blk in sec.get("bloques", []):
            parts.append(render_block(guide, tab, blk))
    parts.append("</body></html>")
    return "".join(parts)
