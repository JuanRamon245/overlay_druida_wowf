"""Convierte el contenido JSON de una pestaña en HTML compacto para QTextBrowser.

Enlaces especiales que gestiona la ventana:
  check:<id>        marcar / desmarcar un objetivo
  fold:<id>         plegar / desplegar una sección
  cmd:<orden>       solo-actual · plegar-completados · desplegar
  goto:<tab>#<ancla> ir a otra pestaña
Imágenes: icon:<nombre> (assets/icons/<nombre>.svg) y res:<ruta> (imagen de la guía).
"""
from __future__ import annotations

import html
import re

import spells
from content import expand_route, tree_totals
from progress import (Progress, chapter_label, chapters, current_chapter, section_id, section_status,
                      summary, talent_check_id)

# Paleta (se repite en theme.py para QSS)
GOLD = "#d4ad62"
TEXT = "#ece7dc"
MUTED = "#a39e92"
DONE = "#7d8a70"
ROW_A = "#22262c"
ROW_B = "#1b1e23"
LINE = "#343941"
GREEN = "#8fb86a"
AMBER = "#e0b24a"
RED = "#c8504a"
HORDE = "#8e2420"

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
MAX_IMG_W = 300   # cabe en la anchura mínima de la ventana


def inline(text: str, bold_color: str = TEXT) -> str:
    """Escapa HTML y aplica **negrita** y resaltado de etiquetas de certeza."""
    out = html.escape(str(text), quote=False)
    out = _BOLD.sub(lambda m: f'<b style="color:{bold_color}">{m.group(1)}</b>', out)
    for rx, color in _TAGS:
        out = rx.sub(lambda m, c=color: f'<span style="color:{c}">{m.group(1)}</span>', out)
    return out


def icon(name: str, size: int = 16) -> str:
    return f'<img src="icon:{html.escape(name)}" width="{size}" height="{size}" style="vertical-align:middle">'


def checkbox(cid: str, checked: bool, size: int = 15) -> str:
    return f'<a href="check:{html.escape(cid)}">{icon("check_on" if checked else "check_off", size)}</a>'


def _bar(done: int, total: int, color: str = GREEN) -> str:
    pct = 0 if total == 0 else round(100 * done / total)
    cells = ""
    if pct > 0:
        cells += f'<td width="{pct}%" style="background:{color}; font-size:3px;">&nbsp;</td>'
    if pct < 100:
        cells += f'<td style="background:{LINE}; font-size:3px;">&nbsp;</td>'
    return f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:4px;"><tr>{cells}</tr></table>'


def _table(header, rows, first_col_gold=True, ids=None, checks=frozenset()):
    parts = ['<table width="100%" cellspacing="0" cellpadding="3" '
             'style="border-collapse:collapse; margin-top:2px; margin-bottom:6px;">']
    if header:
        heads = ([""] if ids else []) + list(header)
        parts.append("<tr>" + "".join(
            f'<th align="left" style="background:{LINE}; color:{GOLD}; font-weight:600;">{inline(h)}</th>'
            for h in heads) + "</tr>")
    for i, row in enumerate(rows):
        bg = ROW_A if i % 2 == 0 else ROW_B
        done = bool(ids) and ids[i] in checks
        cells = []
        if ids:
            cells.append(f'<td valign="top" width="18" style="background:{bg};">{checkbox(ids[i], done)}</td>')
        for j, cell in enumerate(row):
            style = f"background:{bg};"
            if done:
                style += f" color:{DONE};"
            elif j == 0 and first_col_gold:
                style += f" color:{GOLD}; white-space:nowrap;"
            cells.append(f'<td valign="top" style="{style}">{inline(cell, DONE if done else TEXT)}</td>')
        parts.append("<tr>" + "".join(cells) + "</tr>")
    parts.append("</table>")
    return "".join(parts)


def _list(items, numbered):
    tag = "ol" if numbered else "ul"
    lis = "".join(f'<li style="margin-bottom:2px;">{inline(i)}</li>' for i in items)
    return f'<{tag} style="margin-top:0px; margin-bottom:6px; margin-left:-18px;">{lis}</{tag}>'


def _checklist(items, checks):
    rows = []
    for it in items:
        done = it["id"] in checks
        color = DONE if done else TEXT
        extra = f' <span style="color:{MUTED}; font-size:small;">(opcional)</span>' if it.get("opcional") else ""
        rows.append(f'<tr><td width="20" valign="top">{checkbox(it["id"], done)}</td>'
                    f'<td valign="middle"><a href="check:{html.escape(it["id"])}" '
                    f'style="color:{color}; text-decoration:none;">{inline(it["texto"], color)}</a>{extra}</td></tr>')
    return ('<table width="100%" cellspacing="0" cellpadding="2" style="margin-bottom:6px;">'
            + "".join(rows) + "</table>")


def _aviso(estado, texto):
    color, label = ESTADO.get(estado, ESTADO["orientativo"])
    return ('<table width="100%" cellspacing="0" cellpadding="4" style="margin-bottom:6px;">'
            f'<tr><td width="3" style="background:{color};"></td>'
            f'<td style="background:{ROW_B};"><span style="color:{color}; font-size:small; font-weight:600;">'
            f'{label}</span><br>{inline(texto)}</td></tr></table>')


def _talents(guide, checks):
    tal = guide["talentos"]
    trees = tal["arboles"]
    expanded = expand_route(tal)
    parts = ['<table width="100%" cellspacing="0" cellpadding="3" style="border-collapse:collapse;">',
             "<tr>" + "".join(f'<th align="left" style="background:{LINE}; color:{GOLD};">{h}</th>'
                              for h in ("", "Nv", "Talento", "Rango", "Función")) + "</tr>"]
    for i, step in enumerate(tal["ruta"]):
        info = trees[step["arbol"]][step["talento"]]
        lv = str(step["desde"]) if step["desde"] == step["hasta"] else f"{step['desde']}–{step['hasta']}"
        reached = max(e["rango"] for e in expanded
                      if e["talento"] == step["talento"] and e["nivel"] <= step["hasta"])
        cid = talent_check_id(step)
        done = cid in checks
        bg = ROW_A if i % 2 == 0 else ROW_B
        tc = DONE if done else TEXT
        tree_tag = "" if step["arbol"] == "Combate feral" else f' <span style="color:{GREEN}">[Resto]</span>'
        name = (f'<b style="color:{tc}">{html.escape(info["es"])}</b>{tree_tag}<br>'
                f'<span style="color:{MUTED}">({html.escape(step["talento"])})</span>')
        flag = "" if info["certeza"] == "confirmado" else f' <span style="color:{AMBER}">≈</span>'
        lvc = DONE if done else GOLD
        parts.append(f'<tr><td valign="top" width="18" style="background:{bg};">{checkbox(cid, done)}</td>'
                     f'<td valign="top" style="background:{bg}; color:{lvc}; white-space:nowrap;">{lv}</td>'
                     f'<td valign="top" style="background:{bg};">{name}</td>'
                     f'<td valign="top" style="background:{bg}; color:{tc}; white-space:nowrap;">{reached}/{info["max"]}{flag}</td>'
                     f'<td valign="top" style="background:{bg}; color:{tc};">{inline(step["funcion"], tc)}</td></tr>')
    parts.append("</table>")
    totals = tree_totals(tal)
    total = sum(totals.values())
    parts.append(f'<p style="margin-top:4px; color:{MUTED};">Total: <b style="color:{GOLD}">'
                 f'0 / {totals.get("Combate feral", 0)} / {totals.get("Restauración", 0)} = {total} puntos</b> '
                 f'(sumado automáticamente) · <span style="color:{AMBER}">≈</span> = fila/requisito orientativo.<br>'
                 f'Validado con: {html.escape(tal["validado_con"])}.</p>')
    return "".join(parts)


def _index(guide, tab, checks):
    cur = current_chapter(guide, checks, tab["id"])
    links = []
    for s in tab["secciones"]:
        if not s.get("ancla"):
            continue
        label = html.escape(s.get("corto") or s["titulo"].split(" · ")[0])
        if section_status(s, checks)["complete"]:
            links.append(f'<a href="#{s["ancla"]}" style="color:{DONE}; text-decoration:none;">✓{label}</a>')
        elif s is cur:
            links.append(f'<a href="#{s["ancla"]}" style="color:white; background:{HORDE}; '
                         f'text-decoration:none;">&nbsp;{label}&nbsp;</a>')
        else:
            links.append(f'<a href="#{s["ancla"]}" style="color:{GOLD}; text-decoration:none;">{label}</a>')
    return f'<p style="margin-bottom:6px;">{" &nbsp;·&nbsp; ".join(links)}</p>'


def _controles():
    btn = (lambda cmd, txt: f'<a href="cmd:{cmd}" style="color:{TEXT}; background:{LINE}; '
                            f'text-decoration:none;">&nbsp;{txt}&nbsp;</a>')
    return (f'<p style="margin-bottom:6px;">{btn("solo-actual", "◎ Solo el actual")} &nbsp;'
            f'{btn("plegar-completados", "✓ Plegar hechos")} &nbsp;{btn("desplegar", "▾ Abrir todo")}</p>')


def _progreso(guide, checks):
    s = summary(guide, checks)
    cur = s["actual"]
    if cur is None:
        head = f'<p style="color:{GREEN}; font-weight:600;">¡Todos los capítulos completados! Rumbo a las bandas.</p>'
    else:
        st = section_status(cur, checks)
        head = (f'<p style="margin-bottom:2px;">Capítulo actual: '
                f'<a href="goto:ruta#{cur["ancla"]}" style="color:{GOLD}; font-weight:600;">'
                f'{html.escape(cur["titulo"])}</a> '
                f'<span style="color:{MUTED};">({st["done"]}/{st["total"]})</span></p>')
    rows = []
    bars = [("Capítulos", s["capitulos"], GOLD), ("Objetivos", s["objetivos"], GREEN),
            ("Talentos", s["talentos"], AMBER)]
    if s["entrenamientos"][1]:
        bars.append(("Instructor", s["entrenamientos"], "#7f9fd8"))
    for label, (d, t), color in bars:
        rows.append(f'<tr><td width="72" style="color:{MUTED};">{label}</td>'
                    f'<td>{_bar(d, t, color)}</td>'
                    f'<td width="52" align="right" style="color:{TEXT};">{d}/{t}</td></tr>')
    return head + ('<table width="100%" cellspacing="0" cellpadding="1" style="margin-bottom:6px;">'
                   + "".join(rows) + "</table>")


def _imagen(blk):
    w, h = int(blk.get("ancho", MAX_IMG_W)), int(blk.get("alto", 0) or 0)
    if w > MAX_IMG_W:
        h = round(h * MAX_IMG_W / w) if h else 0
        w = MAX_IMG_W
    hattr = f' height="{h}"' if h else ""
    img = f'<img src="res:{html.escape(blk["archivo"])}" width="{w}"{hattr}>'
    pie = (f'<br><span style="color:{MUTED}; font-size:small;">{inline(blk["pie"])}</span>'
           if blk.get("pie") else "")
    return f'<p align="center" style="margin-bottom:6px;">{img}{pie}</p>'


def _fuentes(guide):
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


def render_block(guide, tab, blk, checks=frozenset()):
    t = blk["tipo"]
    if t == "texto":
        return f'<p style="margin-top:0px; margin-bottom:6px;">{inline(blk["texto"])}</p>'
    if t == "lista":
        return _list(blk["items"], blk.get("numerada", False))
    if t == "tabla":
        return _table(blk.get("cabecera"), blk["filas"], ids=blk.get("ids"), checks=checks)
    if t == "tarjeta":
        return _table(None, blk["campos"])
    if t == "aviso":
        return _aviso(blk.get("estado", "orientativo"), blk["texto"])
    if t == "checklist":
        return _checklist(blk["items"], checks)
    if t == "talentos":
        return _talents(guide, checks)
    if t == "indice":
        return _index(guide, tab, checks)
    if t == "controles":
        return _controles()
    if t == "progreso":
        return _progreso(guide, checks)
    if t == "imagen":
        return _imagen(blk)
    if t == "fuentes":
        return _fuentes(guide)
    if t == "entrenamiento":
        return _training(guide, blk["nivel"])
    if t == "presets":
        return _presets(guide, blk["nivel"])
    if t == "hechizos_todos":
        return _all_spells(guide)
    if t == "leyenda_hechizos":
        return _spell_legend()
    return ""


# ---------------------------------------------------------------- hechizos y barras
GREY_TXT = "#6f6b64"


def _spell_name(sp):
    return html.escape(sp.get("corto") or sp["es"])


def _training(guide, level):
    data = guide.get("_hechizos")
    if not data:
        return ""
    entries = spells.training_at(data, level)
    n_up = sum(1 for e in entries if e["entrenar"])
    n_skip = len(entries) - n_up
    head = (f'<p style="margin-top:0px; margin-bottom:3px;"><b style="color:{GREEN}">+{n_up}</b> a entrenar'
            + (f' · <span style="color:{GREY_TXT}">{n_skip} ignorado{"s" if n_skip != 1 else ""}</span>' if n_skip else "")
            + "</p>")
    cells = []
    for e in entries:
        sp = e["sp"]
        src = f'spellup:{e["id"]}' if e["entrenar"] else f'spellg:{e["id"]}'
        color = TEXT if e["entrenar"] else GREY_TXT
        if e["origen"] == "mision":
            tag = f'<span style="color:{AMBER}">misión</span>'
        elif e["nuevo"]:
            tag = f'<span style="color:{GOLD}">nuevo</span>'
        else:
            tag = f'<span style="color:{MUTED if e["entrenar"] else GREY_TXT}">R{e["rango"]}</span>'
        cells.append(f'<td align="center" valign="top" width="25%" style="padding-bottom:4px;">'
                     f'<img src="{src}" width="34" height="34"><br>'
                     f'<span style="color:{color}; font-size:small;">{_spell_name(sp)}</span><br>'
                     f'<span style="font-size:small;">{tag}</span></td>')
    return head + _grid(cells, 4)


def _grid(cells, cols):
    rows = []
    for i in range(0, len(cells), cols):
        chunk = cells[i:i + cols]
        chunk += [f'<td width="{100 // cols}%"></td>'] * (cols - len(chunk))
        rows.append("<tr>" + "".join(chunk) + "</tr>")
    return ('<table width="100%" cellspacing="0" cellpadding="2" style="margin-bottom:6px;">'
            + "".join(rows) + "</table>")


def _spell_legend():
    return (f'<table cellspacing="0" cellpadding="2" style="margin-bottom:6px;"><tr>'
            f'<td><img src="spellup:maul" width="26" height="26"></td>'
            f'<td style="color:{TEXT};">Color con <b style="color:{GREEN}">+1</b>: entrénalo</td></tr><tr>'
            f'<td><img src="spellg:starfire" width="26" height="26"></td>'
            f'<td style="color:{GREY_TXT};">Gris: puedes ignorarlo (ahorra oro)</td></tr></table>'
            f'<p style="margin-top:0px; margin-bottom:6px;">Una sección por cada visita al instructor. '
            f'Marca «Entrenado» y se pliega sola. Los rangos que llegan por <b>talento</b> '
            f'(Lacerar, Mordisco primigenio…) se eligen en el árbol; aquí solo salen sus rangos de instructor.</p>')


def _presets(guide, level):
    data = guide.get("_hechizos")
    if not data:
        return ""
    bands = spells.preset_bands(data)
    i = bands.index(level)
    prev_level = bands[i - 1] if i > 0 else None
    bars = data["barras"]
    rows = [("Comunes", "omen", bars["comunes"], 1)]
    rows += [(f["nombre"], f["icono"], f["teclas"], f["desde"]) for f in bars["formas"]]
    out = []
    for name, icon_id, keys, desde in rows:
        label = (f'<p style="margin-top:4px; margin-bottom:1px;"><img src="spell:{icon_id}" width="16" height="16" '
                 f'style="vertical-align:middle"> <b style="color:{GOLD}">{html.escape(name)}</b>')
        if level < desde:
            out.append(label + f' <span style="color:{GREY_TXT}">— disponible al nivel {desde}</span></p>')
            continue
        out.append(label + "</p>")
        now = spells.preset(data, keys, level)
        before = dict(spells.preset(data, keys, prev_level)) if prev_level and prev_level >= desde else {}
        cells = []
        for key, sid in now:
            if sid is None:
                cells.append(f'<td align="center" valign="top" width="16%"><span style="color:#3d4148;">▢</span><br>'
                             f'<span style="color:{GREY_TXT}; font-size:small;">{html.escape(key)}</span></td>')
                continue
            sp = data["hechizos"][sid]
            new = before.get(key) != sid
            kc = GREEN if new else MUTED
            cells.append(f'<td align="center" valign="top" width="16%">'
                         f'<img src="spell:{sid}" width="28" height="28"><br>'
                         f'<span style="color:{kc}; font-size:small; font-weight:600;">{html.escape(key)}</span><br>'
                         f'<span style="color:{GREEN if new else MUTED}; font-size:7pt;">{_spell_name(sp)}</span></td>')
        out.append(_grid(cells, 6))
    return "".join(out)


def _all_spells(guide):
    data = guide.get("_hechizos")
    if not data:
        return ""
    out = [f'<p style="margin-top:0px; color:{MUTED};">Cada número es el nivel de un rango: '
           f'<span style="color:{GOLD}">dorado</span> = entrenar, <span style="color:{GREY_TXT}">gris</span> = ignorar, '
           f'<span style="color:{GREEN}">T</span> = talento, <span style="color:{AMBER}">M</span> = misión.</p>']
    for gid, gname in data["grupos"]:
        out.append(f'<p style="margin-top:6px; margin-bottom:2px;"><b style="color:{GOLD}">{html.escape(gname)}</b></p>')
        rows = []
        for i, (sid, sp) in enumerate((k, v) for k, v in data["hechizos"].items() if v["grupo"] == gid):
            bg = ROW_A if i % 2 == 0 else ROW_B
            never = sp.get("nunca")
            levels = []
            for r, lv in enumerate(sp["rangos"], 1):
                org = spells.origin(sp, r)
                if org == "talento":
                    levels.append(f'<span style="color:{GREEN}">T{lv}</span>')
                elif org == "mision":
                    levels.append(f'<span style="color:{AMBER}">M{lv}</span>')
                elif spells.is_trained(sp, lv):
                    levels.append(f'<span style="color:{GOLD}">{lv}</span>')
                else:
                    levels.append(f'<span style="color:{GREY_TXT}">{lv}</span>')
            nota = (f'<br><span style="color:{MUTED}; font-size:small;">{inline(sp["nota"])}</span>'
                    if sp.get("nota") else "")
            nc = GREY_TXT if never else TEXT
            rows.append(f'<tr><td width="26" valign="top" style="background:{bg};">'
                        f'<img src="{"spellg" if never else "spell"}:{sid}" width="24" height="24"></td>'
                        f'<td valign="top" style="background:{bg};"><b style="color:{nc}">{html.escape(sp["es"])}</b> '
                        f'<span style="color:{MUTED}">({html.escape(sp["en"])})</span><br>'
                        f'{" · ".join(levels)}{nota}</td></tr>')
        out.append('<table width="100%" cellspacing="0" cellpadding="2" style="margin-bottom:4px;">'
                   + "".join(rows) + "</table>")
    return "".join(out)


def _section_header(sec, sid, folded, st, is_current):
    complete = st["complete"]
    color = GREEN if complete else GOLD
    arrow = "▸" if folded else "▾"
    ic = (icon(sec["icono"]) + "&nbsp;") if sec.get("icono") else ""
    extra = ""
    if st["total"] or st["opt_total"]:
        if complete:
            extra = f' <span style="color:{GREEN}; font-size:small;">✓ COMPLETADO</span>'
        elif st["total"]:
            extra = f' <span style="color:{MUTED}; font-size:small;">{st["done"]}/{st["total"]}</span>'
        else:
            extra = f' <span style="color:{MUTED}; font-size:small;">{st["opt_done"]}/{st["opt_total"]}</span>'
    if is_current:
        extra += (f' <span style="color:white; background:{HORDE}; font-size:small; font-weight:600;">'
                  f'&nbsp;ACTUAL&nbsp;</span>')
    anchor = f'<a name="{sec["ancla"]}"></a>' if sec.get("ancla") else ""
    return (f'<h3 style="margin-top:8px; margin-bottom:3px; font-size:medium;">{anchor}'
            f'<a href="fold:{html.escape(sid)}" style="color:{color}; text-decoration:none;">'
            f'<span style="color:{MUTED};">{arrow}</span> {ic}{html.escape(sec["titulo"])}</a>{extra}</h3>')


def render_tab(guide: dict, tab: dict, progress: Progress | None = None) -> str:
    checks = progress.checks if progress else set()
    folded = progress.folded if progress else set()
    cur = current_chapter(guide, checks, tab["id"]) if tab["id"] in ("ruta", "hechizos", "barras") else None
    parts = [f'<html><body style="color:{TEXT};">']
    if tab["id"] == "inicio":
        meta = guide["meta"]
        parts.append(f'<p style="color:{MUTED}; font-size:small; margin-bottom:4px;">{html.escape(meta["subtitulo"])}'
                     f' · revisado {html.escape(meta["fecha_revision"])}'
                     f' · cliente {html.escape(meta["cliente_revisado"].split(" ")[0])}</p>')
    for i, sec in enumerate(tab.get("secciones", [])):
        sid = section_id(tab, i, sec)
        is_folded = sid in folded
        parts.append(_section_header(sec, sid, is_folded, section_status(sec, checks), sec is cur))
        if is_folded:
            continue
        for blk in sec.get("bloques", []):
            parts.append(render_block(guide, tab, blk, checks))
    parts.append("</body></html>")
    return "".join(parts)


__all__ = ["render_tab", "render_block", "inline", "chapter_label", "chapters"]
