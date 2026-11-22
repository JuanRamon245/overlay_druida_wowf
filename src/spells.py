"""Hechizos del instructor (qué entrenar en cada nivel) y presets de barras por tramo de nivel.

Los datos están en content/hechizos.json. Este módulo calcula, sin interfaz:
  - qué rangos aparecen en cada nivel y si conviene entrenarlos (color +1) o ignorarlos (gris),
  - qué hechizo va en cada tecla de cada forma cada 5 niveles,
  - las pestañas «Hechizos» y «Barras» que se insertan en la guía.
"""
from __future__ import annotations


def is_trained(sp: dict, level: int) -> bool:
    """¿Merece la pena entrenar el rango de este nivel?"""
    if sp.get("nunca"):
        return False
    od = sp.get("omitir_desde")
    return od is None or level < od


def available(sp: dict, level: int) -> bool:
    """¿Lo tienes a ese nivel siguiendo la guía (entrenado, por misión o por talento)?"""
    return not sp.get("nunca") and sp["rangos"][0] <= level


def origin(sp: dict, rank: int) -> str:
    if rank == 1 and sp.get("talento"):
        return "talento"
    if rank == 1 and sp.get("origen") == "mision":
        return "mision"
    return "instructor"


def training_at(data: dict, level: int) -> list[dict]:
    """Rangos que se consiguen en el instructor (o por misión) a ese nivel.
    El primer rango de un talento se elige en el árbol, así que no aparece aquí."""
    out = []
    for sid, sp in data["hechizos"].items():
        for i, lv in enumerate(sp["rangos"]):
            if lv != level:
                continue
            rank = i + 1
            org = origin(sp, rank)
            if org == "talento":
                continue
            out.append({"id": sid, "sp": sp, "rango": rank, "entrenar": is_trained(sp, level),
                        "nuevo": rank == 1, "origen": org})
    out.sort(key=lambda e: (not e["entrenar"], not e["nuevo"]))
    return out


def training_levels(data: dict) -> list[int]:
    levels = {lv for sp in data["hechizos"].values() for lv in sp["rangos"] if lv > 1}
    return sorted(lv for lv in levels if training_at(data, lv))


def preset(data: dict, keys: list, level: int) -> list[tuple[str, str | None]]:
    """Para cada tecla, el primer candidato disponible a ese nivel que no esté ya en la barra."""
    used: set[str] = set()
    out = []
    for key, cands in keys:
        pick = next((c for c in cands if c not in used and available(data["hechizos"][c], level)), None)
        if pick:
            used.add(pick)
        out.append((key, pick))
    return out


def preset_bands(data: dict) -> list[int]:
    return list(data["barras"]["niveles"])


def band_label(data: dict, level: int) -> str:
    bands = preset_bands(data)
    i = bands.index(level)
    if i + 1 < len(bands):
        return f"Nivel {level}–{bands[i + 1] - 1}"
    return f"Nivel {level}"


def validate(data: dict) -> list[str]:
    errors = []
    spells = data["hechizos"]
    groups = {g for g, _ in data["grupos"]}
    for sid, sp in spells.items():
        r = sp.get("rangos", [])
        if not r or r != sorted(r) or len(set(r)) != len(r) or not all(1 <= x <= 60 for x in r):
            errors.append(f"Hechizo '{sid}': rangos inválidos {r}")
        if sp.get("grupo") not in groups:
            errors.append(f"Hechizo '{sid}': grupo desconocido")
    bars = data["barras"]
    for key, cands in bars["comunes"]:
        errors += [f"Barra común {key}: '{c}' no existe" for c in cands if c not in spells]
    for form in bars["formas"]:
        if form["icono"] not in spells:
            errors.append(f"Forma {form['nombre']}: icono '{form['icono']}' no existe")
        for key, cands in form["teclas"]:
            errors += [f"{form['nombre']} {key}: '{c}' no existe" for c in cands if c not in spells]
    return errors


def build_tabs(data: dict) -> list[dict]:
    """Pestañas generadas: «Hechizos» (una sección por nivel de instructor) y «Barras»."""
    levels = training_levels(data)
    sections = [{"titulo": "Cómo leerlo", "icono": "hechizos", "bloques": [
        {"tipo": "leyenda_hechizos"},
        {"tipo": "controles"},
        {"tipo": "indice"},
        {"tipo": "aviso", "estado": "orientativo", "texto": data["validado_con"]},
    ]}]
    for lv in levels:
        sections.append({"titulo": f"Nivel {lv}", "corto": str(lv), "ancla": f"h{lv}", "icono": "hechizos",
                         "bloques": [{"tipo": "entrenamiento", "nivel": lv},
                                     {"tipo": "checklist", "items": [
                                         {"id": f"h{lv}", "texto": f"Entrenado en el instructor (nv {lv})"}]}]})
    sections.append({"titulo": "Todos los hechizos (árbol completo)", "icono": "talentos",
                     "bloques": [{"tipo": "hechizos_todos"}]})

    bars = [{"titulo": "Cómo usar estas barras", "icono": "barras", "bloques": [
        {"tipo": "texto", "texto": data["barras"]["nota"]},
        {"tipo": "texto", "texto": "Cada tramo muestra la barra de **cada forma**. En **verde** lo que es nuevo "
                                   "respecto al tramo anterior. Las casillas vacías aún no están disponibles. "
                                   "El tramo marcado **ACTUAL** sigue a tu capítulo de la Ruta."},
        {"tipo": "indice"},
    ]}]
    for lv in preset_bands(data):
        bars.append({"titulo": band_label(data, lv), "corto": str(lv), "ancla": f"b{lv}", "icono": "barras",
                     "bloques": [{"tipo": "presets", "nivel": lv}]})
    return [
        {"id": "hechizos", "titulo": "Hechizos", "secciones": sections},
        {"id": "barras", "titulo": "Barras", "secciones": bars},
    ]
