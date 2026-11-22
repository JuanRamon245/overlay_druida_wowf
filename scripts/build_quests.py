"""Genera data/misiones_horda.json a partir de NorgannonDB (vendor/NorgannonDB, GPL-3.0).

Incluye solo las misiones que puede aceptar un TAUREN DRUIDA (Horda), con su nivel mínimo,
la zona y las coordenadas (% del mapa) de quién la da y de quién la recoge.

Uso:  python scripts/build_quests.py
(fetch_blizzard_assets.py lo llama automáticamente; no hace falta ejecutarlo a mano).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lua_table import find_assignment, iter_records, parse_fields  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "vendor" / "NorgannonDB" / "data"
OUT = ROOT / "data" / "misiones_horda.json"

TAUREN = 32          # bit de raza
DRUID = 1024         # bit de clase
MAX_LEVEL = 60
# Categorías de evento que no sirven para subir de nivel: Feria de la Luna Negra, esfuerzo de
# guerra de Ahn'Qiraj, insignias de encomienda e invasión de la Plaga.
EXCLUDE_SORTS = {-364, -365, -367, -368}
EXCLUDE_PREFIXES = ("Craftsman's Writ", "Investigate the Scourge")
EXCLUDE_CONTAINS = ("Commendation Signet",)


def _read(name: str) -> str:
    return (DB / name).read_text(encoding="utf-8")


def _merge(base: dict, override: dict | None) -> dict:
    if not override:
        return base
    out = dict(base)
    for k, v in override.items():
        if v == "NorgannonDB.REMOVED":
            out.pop(k, None)
        else:
            out[k] = v
    return out


def _raw_records(name: str) -> dict[int, tuple[str, str]]:
    return {rid: (n, body) for rid, n, body in iter_records(_read(name))}


def _spawn(rec: dict, prefer_zone: int | None):
    """Primer punto de aparición; prioriza la zona de la misión."""
    spawns = rec.get("spawns") or {}
    if not isinstance(spawns, dict) or not spawns:
        return None
    order = []
    if prefer_zone in spawns:
        order.append(prefer_zone)
    if rec.get("zone") in spawns and rec.get("zone") not in order:
        order.append(rec["zone"])
    order += [a for a in spawns if a not in order]
    for area in order:
        pts = spawns[area]
        if isinstance(pts, list) and pts and isinstance(pts[0], list) and len(pts[0]) >= 2:
            x, y = float(pts[0][0]), float(pts[0][1])
            if x < 0 or y < 0:           # dentro de una mazmorra o banda: sin coordenadas de mapa
                return {"a": int(area)}
            return {"a": int(area), "x": round(x, 2), "y": round(y, 2)}
    return None


class _Lookup:
    """Carga perezosa de PNJ u objetos con las variantes de la Horda aplicadas."""

    def __init__(self, raw: dict, overrides: dict):
        self.raw = raw
        self.over = overrides or {}
        self.cache: dict[int, dict | None] = {}

    def get(self, rid: int) -> dict | None:
        if rid not in self.cache:
            if rid not in self.raw:
                self.cache[rid] = None
            else:
                name, body = self.raw[rid]
                rec = _merge(parse_fields(body), self.over.get(rid))
                rec["name"] = name
                self.cache[rid] = rec
        return self.cache[rid]


def _point(kind: str, ids, npcs: _Lookup, objs: _Lookup, zone: int | None):
    if not ids:
        return None
    look = npcs if kind == "npc" else objs
    best = None
    for rid in ids:
        rec = look.get(int(rid))
        if not rec:
            continue
        if kind == "npc" and rec.get("reaction") == "A":
            continue                    # PNJ solo de la Alianza
        sp = _spawn(rec, zone)
        cand = {"t": kind, "id": int(rid), "n": rec["name"]}
        if sp:
            cand.update(sp)
            return cand
        best = best or cand
    return best


def build() -> dict:
    info = find_assignment(_read("info.lua"), "NorgannonDB.info")
    world = _read("world.lua")
    zones_raw = find_assignment(world, "NorgannonDB.zones")
    variants = find_assignment(_read("variants.lua"), "NorgannonDB.variants")
    horde = (variants.get("faction") or {}).get("Horde") or {}
    druid = ((variants.get("class") or {}).get("DRUID") or {})

    npcs = _Lookup(_raw_records("npcs.lua"), horde.get("npcs"))
    objs = _Lookup(_raw_records("objects.lua"), horde.get("objects"))
    q_over = _merge(horde.get("quests") or {}, {})

    quests = []
    names: dict[int, str] = {}
    for qid, name, body in iter_records(_read("quests.lua")):
        q = parse_fields(body)
        q = _merge(q, q_over.get(qid))
        q = _merge(q, (druid.get("quests") or {}).get(qid))
        names[qid] = name
        if q.get("hidden") or q.get("zoneOrSort") in EXCLUDE_SORTS:
            continue
        if name.startswith(EXCLUDE_PREFIXES) or any(t in name for t in EXCLUDE_CONTAINS):
            continue
        races, classes = q.get("races"), q.get("classes")
        if races and not (int(races) & TAUREN):
            continue
        if classes and not (int(classes) & DRUID):
            continue
        level = int(q.get("level") or 0)
        min_level = int(q.get("minLevel") or 0) or max(level, 1)
        if min_level > MAX_LEVEL:
            continue
        zone = q.get("zoneOrSort") if isinstance(q.get("zoneOrSort"), int) and q["zoneOrSort"] > 0 else None
        st, fi = q.get("starters") or {}, q.get("finishers") or {}
        start = _point("npc", st.get("npcs"), npcs, objs, zone) or _point("obj", st.get("objects"), npcs, objs, zone)
        if start is None and st.get("items"):
            start = {"t": "item", "id": int(st["items"][0])}
        if start is None:
            continue                     # sin forma conocida de conseguirla
        end = _point("npc", fi.get("npcs"), npcs, objs, zone) or _point("obj", fi.get("objects"), npcs, objs, zone)
        pre = q.get("prerequisites") or {}
        pre_ids = []
        if isinstance(pre, dict):
            for key in ("all", "any"):
                pre_ids += [int(p) for p in (pre.get(key) or []) if isinstance(p, int) and p > 0]
        entry = {"id": qid, "n": name, "lv": level, "min": min_level,
                 "zona": zone or start.get("a") or (end or {}).get("a"), "ini": start}
        if end:
            entry["fin"] = end
        if classes:
            entry["clase"] = True
        if pre_ids:
            entry["pre"] = pre_ids[:3]
        quests.append(entry)

    for e in quests:              # nombres de las previas, para mostrarlas
        if "pre" in e:
            e["pre"] = [[p, names.get(p, f"#{p}")] for p in e["pre"]]
    quests.sort(key=lambda e: (e["min"], e["lv"], e["n"]))

    used = {e["zona"] for e in quests if e.get("zona")}
    for e in quests:
        for k in ("ini", "fin"):
            if e.get(k, {}).get("a"):
                used.add(e[k]["a"])
    zones = {}
    for a in sorted(used):
        z = zones_raw.get(a) or {}
        zones[str(a)] = {"n": z.get("name", f"Zona {a}")}
    return {
        "fuente": f"NorgannonDB ({info.get('flavor')} {info.get('build')}, generado {info.get('generated')}) · GPL-3.0",
        "filtro": "Tauren druida (Horda), nivel mínimo 1–60",
        "zonas": zones,
        "misiones": quests,
    }


def main() -> None:
    if not DB.is_dir():
        sys.exit("Falta vendor/NorgannonDB: ejecuta scripts/fetch_blizzard_assets.py")
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n = len(data["misiones"])
    print(f"{n} misiones · {len(data['zonas'])} zonas → {OUT}")


if __name__ == "__main__":
    main()
