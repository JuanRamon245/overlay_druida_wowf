"""Misiones de la Horda por nivel (data/misiones_horda.json, generado por scripts/fetch_blizzard_assets.py).

Este módulo no tiene interfaz: carga el JSON, construye la pestaña «Misiones» (una sección por
nivel mínimo, 1–60) y ofrece búsquedas por id para el mapa.
"""
from __future__ import annotations

import json
from pathlib import Path

from content import base_dir, content_dir

# Nombres en español (España) de las zonas más habituales; el resto se muestra en inglés.
ZONAS_ES = {
    "Mulgore": "Mulgore", "Red Cloud Mesa": "Mesa de la Nube Roja", "Thunder Bluff": "Cima del Trueno",
    "Durotar": "Durotar", "Orgrimmar": "Orgrimmar", "Valley of Trials": "Valle de los Retos",
    "The Barrens": "Los Baldíos", "Stonetalon Mountains": "Sierra Espolón", "Ashenvale": "Vallefresno",
    "Thousand Needles": "Las Mil Agujas", "Desolace": "Desolace", "Dustwallow Marsh": "Marjal Revolcafango",
    "Feralas": "Feralas", "Tanaris": "Tanaris", "Azshara": "Azshara", "Felwood": "Frondavil",
    "Un'Goro Crater": "Cráter de Un'Goro", "Winterspring": "Cuna del Invierno", "Silithus": "Silithus",
    "Moonglade": "Claro de la Luna", "Tirisfal Glades": "Claros de Tirisfal", "Undercity": "Entrañas",
    "Silverpine Forest": "Bosque de Argénteos", "Hillsbrad Foothills": "Laderas de Trabalomas",
    "Alterac Mountains": "Montañas de Alterac", "Arathi Highlands": "Tierras Altas de Arathi",
    "Wetlands": "Los Humedales", "Stranglethorn Vale": "Vega de Tuercespina", "Badlands": "Tierras Inhóspitas",
    "Swamp of Sorrows": "Pantano de las Penas", "The Hinterlands": "Tierras del Interior",
    "Searing Gorge": "La Garganta de Fuego", "Burning Steppes": "Las Estepas Ardientes",
    "Blasted Lands": "Las Tierras Devastadas", "Western Plaguelands": "Tierras de la Peste del Oeste",
    "Eastern Plaguelands": "Tierras de la Peste del Este", "Duskwood": "Bosque del Ocaso",
    "Deadwind Pass": "Paso de la Muerte", "Mount Hyjal": "Monte Hyjal", "Deathknell": "Camposanto",
}


def data_path() -> Path:
    for folder in (content_dir().parent / "data", base_dir() / "data"):
        if (folder / "misiones_horda.json").is_file():
            return folder / "misiones_horda.json"
    return base_dir() / "data" / "misiones_horda.json"


def load_quests() -> dict | None:
    path = data_path()
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data["index"] = {q["id"]: q for q in data["misiones"]}
    return data


def zone_name(data: dict, area) -> str:
    if area is None:
        return "—"
    en = (data.get("zonas", {}).get(str(area)) or {}).get("n", f"Zona {area}")
    return ZONAS_ES.get(en, en)


def quest_ids_at(data: dict, level: int) -> list[int]:
    return [q["id"] for q in data["misiones"] if q["min"] == level]


def wowhead_url(qid: int) -> str:
    return f"https://www.wowhead.com/forever/quest={qid}"


def build_tab(data: dict | None) -> dict:
    intro = {"titulo": "Cómo usarla", "icono": "ruta", "bloques": []}
    tab = {"id": "misiones", "titulo": "Misiones", "secciones": [intro]}
    if data is None:
        intro["bloques"].append({"tipo": "aviso", "estado": "pendiente", "texto":
                                 "Faltan los datos de misiones. Ejecuta una vez "
                                 "**python scripts/fetch_blizzard_assets.py** (descarga la base de datos "
                                 "y los mapas) y vuelve a abrir la app."})
        return tab
    total = len(data["misiones"])
    intro["bloques"] += [
        {"tipo": "texto", "texto": f"**{total} misiones** que puede aceptar un tauren druida, agrupadas por el "
                                   "**nivel mínimo para aceptarlas**. Haz clic en una misión para ver en el mapa "
                                   "dónde se coge (**!** amarillo) y dónde se entrega (**?** azul). "
                                   "Marca ☐ las que completes."},
        {"tipo": "indice"},
        {"tipo": "aviso", "estado": "confirmado", "texto": f"Datos: {data.get('fuente', 'NorgannonDB')}. "
                                                          "Mapas reales de Forever (Wowhead). Nombres de misión "
                                                          "en inglés, como en la base de datos."},
    ]
    for lv in range(1, 61):
        ids = quest_ids_at(data, lv)
        if not ids:
            continue
        tab["secciones"].append({
            "titulo": f"Nivel {lv} · {len(ids)} misiones", "corto": str(lv), "ancla": f"m{lv}",
            "icono": "ruta", "plegado_inicial": True,
            "bloques": [{"tipo": "misiones", "nivel": lv, "ids": ids}],
        })
    return tab
