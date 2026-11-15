"""Carga y validación del contenido de la guía (archivos JSON locales)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BLOCK_TYPES = {"texto", "lista", "tabla", "aviso", "tarjeta", "talentos", "indice", "fuentes"}


def base_dir() -> Path:
    """Raíz del proyecto, o la carpeta temporal de PyInstaller si está empaquetado."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def content_dir() -> Path:
    # Permite editar la guía junto al .exe: si existe ./content al lado del ejecutable, se usa.
    if getattr(sys, "frozen", False):
        beside = Path(sys.executable).parent / "content"
        if (beside / "guia_es.json").exists():
            return beside
    return base_dir() / "content"


class ContentError(ValueError):
    pass


def load_json(name: str, folder: Path | None = None) -> dict:
    path = (folder or content_dir()) / name
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_guide(folder: Path | None = None) -> dict:
    guide = load_json("guia_es.json", folder)
    validate_guide(guide)
    try:
        guide["_fuentes"] = load_json("fuentes.json", folder)
    except FileNotFoundError:
        guide["_fuentes"] = {"fuentes": []}
    return guide


def validate_guide(guide: dict) -> None:
    for key in ("meta", "tabs", "talentos"):
        if key not in guide:
            raise ContentError(f"Falta la clave '{key}' en guia_es.json")
    ids = set()
    for tab in guide["tabs"]:
        if not tab.get("id") or not tab.get("titulo"):
            raise ContentError("Cada pestaña necesita 'id' y 'titulo'")
        if tab["id"] in ids:
            raise ContentError(f"Pestaña duplicada: {tab['id']}")
        ids.add(tab["id"])
        for sec in tab.get("secciones", []):
            for blk in sec.get("bloques", []):
                if blk.get("tipo") not in BLOCK_TYPES:
                    raise ContentError(f"Bloque desconocido '{blk.get('tipo')}' en {tab['id']}")
    errors = check_talent_route(guide["talentos"])
    if errors:
        raise ContentError("Ruta de talentos inválida:\n" + "\n".join(errors))


def expand_route(talentos: dict) -> list[dict]:
    """Devuelve una entrada por nivel: {nivel, talento, arbol, rango, funcion}."""
    out: list[dict] = []
    ranks: dict[str, int] = {}
    for step in talentos["ruta"]:
        for lvl in range(step["desde"], step["hasta"] + 1):
            ranks[step["talento"]] = ranks.get(step["talento"], 0) + 1
            out.append({"nivel": lvl, "talento": step["talento"], "arbol": step["arbol"],
                        "rango": ranks[step["talento"]], "funcion": step.get("funcion", "")})
    return out


def check_talent_route(talentos: dict) -> list[str]:
    """Comprueba legalidad nivel a nivel: 1 punto/nivel desde el 10, rangos máximos,
    puntos requeridos en el árbol y prerrequisitos. Devuelve lista de errores."""
    trees = talentos["arboles"]
    errors: list[str] = []
    spent_tree: dict[str, int] = {t: 0 for t in trees}
    ranks: dict[str, int] = {}
    expected_level = 10
    for entry in expand_route(talentos):
        lvl, name, tree = entry["nivel"], entry["talento"], entry["arbol"]
        if lvl != expected_level:
            errors.append(f"Nivel {lvl}: se esperaba el nivel {expected_level} (1 punto por nivel)")
        expected_level = lvl + 1
        info = trees.get(tree, {}).get(name)
        if info is None:
            errors.append(f"Nivel {lvl}: '{name}' no existe en el árbol '{tree}'")
            continue
        if spent_tree[tree] < info["req"]:
            errors.append(f"Nivel {lvl}: '{name}' requiere {info['req']} puntos en {tree} (hay {spent_tree[tree]})")
        pre = info.get("prereq")
        if pre and ranks.get(pre[0], 0) < pre[1]:
            errors.append(f"Nivel {lvl}: '{name}' requiere {pre[0]} {pre[1]}")
        ranks[name] = ranks.get(name, 0) + 1
        if ranks[name] > info["max"]:
            errors.append(f"Nivel {lvl}: '{name}' supera su máximo ({info['max']})")
        spent_tree[tree] += 1
    if expected_level != 61:
        errors.append(f"La ruta termina en el nivel {expected_level - 1}, no en el 60")
    return errors


def tree_totals(talentos: dict) -> dict[str, int]:
    totals: dict[str, int] = {t: 0 for t in talentos["arboles"]}
    for e in expand_route(talentos):
        totals[e["arbol"]] += 1
    return totals
