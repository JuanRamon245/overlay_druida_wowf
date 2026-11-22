"""Progreso del jugador: objetivos marcados y secciones plegadas (JSON local)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Progress:
    checks: set[str] = field(default_factory=set)
    folded: set[str] = field(default_factory=set)

    def toggle_check(self, cid: str) -> bool:
        if cid in self.checks:
            self.checks.discard(cid)
            return False
        self.checks.add(cid)
        return True

    def toggle_fold(self, sid: str) -> None:
        if sid in self.folded:
            self.folded.discard(sid)
        else:
            self.folded.add(sid)


def progress_path() -> Path:
    override = os.environ.get("FERAL_COMPANION_PROGRESS")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "FeralCompanion" / "progreso.json"


def load_progress(path: Path | str | None = None) -> Progress:
    path = Path(path) if path else progress_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return Progress()
    if not isinstance(raw, dict):
        return Progress()
    checks = {c for c in raw.get("checks", []) if isinstance(c, str)}
    folded = {c for c in raw.get("plegados", []) if isinstance(c, str)}
    return Progress(checks, folded)


def save_progress(pr: Progress, path: Path | str | None = None) -> None:
    path = Path(path) if path else progress_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        data = {"version": 1, "checks": sorted(pr.checks), "plegados": sorted(pr.folded)}
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


# ---------------------------------------------------------------- cálculos sobre la guía
def section_id(tab: dict, idx: int, sec: dict) -> str:
    return sec.get("ancla") or f"{tab['id']}-{idx}"


def checklist_items(sec: dict) -> list[dict]:
    out = []
    for blk in sec.get("bloques", []):
        if blk.get("tipo") == "checklist":
            out.extend(blk["items"])
        elif blk.get("tipo") == "tabla" and "ids" in blk:   # filas marcables: siempre opcionales
            out.extend({"id": i, "texto": "", "opcional": True} for i in blk["ids"])
        elif blk.get("tipo") == "misiones":                  # misiones: opcionales, no bloquean nada
            out.extend({"id": f"q{i}", "texto": "", "opcional": True} for i in blk["ids"])
    return out


def is_folded(sec: dict, sid: str, folded: set[str]) -> bool:
    """Las secciones con «plegado_inicial» empiezan plegadas: estar en `folded` significa abierta."""
    return (sid in folded) != bool(sec.get("plegado_inicial"))


def section_status(sec: dict, checks: set[str]) -> dict:
    items = checklist_items(sec)
    req = [i for i in items if not i.get("opcional")]
    opt = [i for i in items if i.get("opcional")]
    done = sum(1 for i in req if i["id"] in checks)
    opt_done = sum(1 for i in opt if i["id"] in checks)
    return {"done": done, "total": len(req), "opt_done": opt_done, "opt_total": len(opt),
            "complete": bool(req) and done == len(req)}


def chapters(guide: dict, tab_id: str = "ruta") -> list[dict]:
    """Secciones con ancla y objetivos obligatorios: se completan y se pliegan solas."""
    for tab in guide["tabs"]:
        if tab["id"] == tab_id:
            return [s for s in tab["secciones"] if s.get("ancla") and section_status(s, set())["total"]]
    return []


def all_chapters(guide: dict) -> list[dict]:
    return [s for tab in guide["tabs"] for s in chapters(guide, tab["id"])]


def _start_level(sec: dict) -> int:
    digits = ""
    for ch in sec["titulo"]:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits or 0)


def current_chapter(guide: dict, checks: set[str], tab_id: str = "ruta") -> dict | None:
    if tab_id in ("barras", "misiones"):   # siguen al capítulo actual de la Ruta
        tab = next((t for t in guide["tabs"] if t["id"] == tab_id), None)
        if tab is None:
            return None
        bands = [s for s in tab["secciones"] if s.get("ancla")]
        route = current_chapter(guide, checks)
        lvl = 60 if route is None else _start_level(route)
        fit = [s for s in bands if _start_level(s) <= lvl]
        return fit[-1] if fit else (bands[0] if bands else None)
    for sec in chapters(guide, tab_id):
        if not section_status(sec, checks)["complete"]:
            return sec
    return None


def talent_check_id(step: dict) -> str:
    return f"t{step['desde']}"


def all_check_ids(guide: dict) -> list[str]:
    ids = []
    for tab in guide["tabs"]:
        for sec in tab.get("secciones", []):
            ids.extend(i["id"] for i in checklist_items(sec))
    ids.extend(talent_check_id(s) for s in guide["talentos"]["ruta"])
    return ids


def summary(guide: dict, checks: set[str]) -> dict:
    chs = chapters(guide)
    ch_done = sum(1 for s in chs if section_status(s, checks)["complete"])
    obj_total = obj_done = 0
    for tab in guide["tabs"]:
        for sec in tab.get("secciones", []):
            st = section_status(sec, checks)
            obj_total += st["total"]
            obj_done += st["done"]
    steps = guide["talentos"]["ruta"]
    t_total = sum(s["hasta"] - s["desde"] + 1 for s in steps)
    t_done = sum(s["hasta"] - s["desde"] + 1 for s in steps if talent_check_id(s) in checks)
    cur = current_chapter(guide, checks)
    trains = chapters(guide, "hechizos")
    tr_done = sum(1 for s in trains if section_status(s, checks)["complete"])
    return {"capitulos": (ch_done, len(chs)), "objetivos": (obj_done, obj_total),
            "talentos": (t_done, t_total), "entrenamientos": (tr_done, len(trains)), "actual": cur}


def chapter_label(sec: dict | None) -> str:
    if sec is None:
        return "¡60!"
    return sec["titulo"].split(" · ")[0]
