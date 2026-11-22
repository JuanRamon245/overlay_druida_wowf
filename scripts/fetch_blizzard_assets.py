"""Descarga los recursos reales de Blizzard para USO PERSONAL y genera la lista de misiones.

Nada de lo que descarga se sube a git (ver .gitignore):
  vendor/NorgannonDB/        base de datos de misiones de Forever (GPL-3.0, github.com/zmarotrix/NorgannonDB)
  assets/blizzard/icons/     iconos reales de hechizos  (CDN de Wowhead, wow.zamimg.com)
  assets/blizzard/maps/      mapas reales de zona de Forever (CDN de Wowhead, ruta «classicplus»)
  data/misiones_horda.json   misiones para tauren druida (generado con scripts/build_quests.py)

Uso:  python scripts/fetch_blizzard_assets.py        (solo descarga lo que falte)
      python scripts/fetch_blizzard_assets.py --update   (actualiza NorgannonDB y regenera)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

DB_REPO = "https://github.com/zmarotrix/NorgannonDB.git"
ICON_URL = "https://wow.zamimg.com/images/wow/icons/large/{}.jpg"
MAP_URLS = ("https://wow.zamimg.com/images/wow/classicplus/maps/enus/zoom/{}.jpg",
            "https://wow.zamimg.com/images/wow/classic/maps/enus/zoom/{}.jpg")
UA = {"User-Agent": "Mozilla/5.0 (FeralCompanion; uso personal)"}


def _get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            if r.status == 200 and r.headers.get_content_type().startswith("image/"):
                return r.read()
    except Exception:
        return None
    return None


def _download(urls, dest: Path) -> bool:
    if dest.is_file() and dest.stat().st_size > 0:
        return True
    for url in urls:
        data = _get(url)
        if data:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            time.sleep(0.15)            # sin saturar el CDN
            return True
    return False


def ensure_db(update: bool) -> None:
    target = ROOT / "vendor" / "NorgannonDB"
    if not target.is_dir():
        subprocess.run(["git", "clone", "--depth", "1", DB_REPO, str(target)], check=True)
    elif update:
        subprocess.run(["git", "-C", str(target), "pull", "--ff-only"], check=True)


def fetch_icons() -> tuple[int, list[str]]:
    spells = json.loads((ROOT / "content" / "hechizos.json").read_text(encoding="utf-8-sig"))["hechizos"]
    names = sorted({sp["icono_wow"] for sp in spells.values() if sp.get("icono_wow")})
    out = ROOT / "assets" / "blizzard" / "icons"
    missing = [n for n in names if not _download([ICON_URL.format(n)], out / f"{n}.jpg")]
    return len(names) - len(missing), missing


def fetch_maps() -> tuple[int, list[int]]:
    data = json.loads((ROOT / "data" / "misiones_horda.json").read_text(encoding="utf-8"))
    areas = set()
    for q in data["misiones"]:
        for k in ("ini", "fin"):
            if q.get(k, {}).get("a"):
                areas.add(q[k]["a"])
    out = ROOT / "assets" / "blizzard" / "maps"
    missing = [a for a in sorted(areas) if not _download([u.format(a) for u in MAP_URLS], out / f"{a}.jpg")]
    return len(areas) - len(missing), missing


def main() -> None:
    update = "--update" in sys.argv
    print("1/4 Base de datos de misiones (NorgannonDB)…")
    ensure_db(update)
    print("2/4 Generando la lista de misiones…")
    import build_quests
    build_quests.main()
    print("3/4 Iconos de hechizos…")
    ok, miss = fetch_icons()
    print(f"    {ok} iconos" + (f" · sin icono: {', '.join(miss)}" if miss else ""))
    print("4/4 Mapas de zona…")
    ok, miss = fetch_maps()
    print(f"    {ok} mapas" + (f" · sin mapa (mazmorras/subzonas): {miss}" if miss else ""))


if __name__ == "__main__":
    main()
