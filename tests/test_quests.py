import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lua_table import iter_records, parse_fields, parse_value  # noqa: E402
import quests  # noqa: E402
from content import base_dir, check_talent_route, load_guide  # noqa: E402
from progress import Progress, is_folded  # noqa: E402
from ui.render import render_tab  # noqa: E402

HAS_DATA = quests.data_path().is_file()
need_data = pytest.mark.skipif(not HAS_DATA, reason="ejecuta scripts/fetch_blizzard_assets.py")


# ---------------------------------------------------------------- parser Lua (sin ejecutar código)
def test_lua_parser_literals():
    v = parse_value('{a=1,b="x\\"y",[215]={{44.47,77.5}},c={1,2},d=true,e=NorgannonDB.REMOVED,f=[[lar\nga]]}')
    assert v["a"] == 1 and v["b"] == 'x"y' and v[215] == [[44.47, 77.5]]
    assert v["c"] == [1, 2] and v["d"] is True and v["e"] == "NorgannonDB.REMOVED" and v["f"] == "lar\nga"


def test_lua_records():
    text = 'R(747,"The Hunt Begins",[[level=2,minLevel=1,races=8589934770,starters={npcs={2980}}]])\n' \
           'R(5,"Multi",[[text={description="a$B\nb"},level=20]])'
    recs = list(iter_records(text))
    assert [r[0] for r in recs] == [747, 5]
    f = parse_fields(recs[0][2])
    assert f["starters"]["npcs"] == [2980] and f["races"] & 32


# ---------------------------------------------------------------- datos y pestaña
def test_inverted_fold():
    sec = {"plegado_inicial": True}
    assert is_folded(sec, "m5", set()) and not is_folded(sec, "m5", {"m5"})
    assert not is_folded({}, "r01", set()) and is_folded({}, "r01", {"r01"})


@need_data
def test_quest_data_tauren_druid():
    data = quests.load_quests()
    assert len(data["misiones"]) > 1500
    assert all(1 <= q["min"] <= 60 for q in data["misiones"])
    names = {q["n"] for q in data["misiones"]}
    for n in ("The Hunt Begins", "Heeding the Call", "A Lesson to Learn", "The Great Cat Spirit"):
        assert n in names
    assert not any(n.startswith("Craftsman's Writ") for n in names)
    bear = next(q for q in data["misiones"] if q["id"] == 5928)
    assert bear["min"] == 10 and bear["ini"]["n"] == "Gennia Runetotem" and bear["ini"]["a"] == 215
    assert any(q["zona"] == 16591 for q in data["misiones"])          # Riverglades (zona nueva)


@need_data
def test_tab_has_level_sections_folded():
    guide = load_guide()
    tab = next(t for t in guide["tabs"] if t["id"] == "misiones")
    lv = [s for s in tab["secciones"] if s.get("ancla")]
    assert lv[0]["ancla"] == "m1" and lv[-1]["ancla"] == "m60"
    html = render_tab(guide, tab, Progress())
    assert "Hunt Begins" not in html                                    # todo plegado al principio
    html = render_tab(guide, tab, Progress(set(), {"m10"}), {"quest": 5928})
    assert "Heeding the Call" in html and 'src="qmap:5928:ini"' in html and "Gennia Runetotem" in html


@need_data
def test_quest_map_and_real_icon():
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.instance() or QGuiApplication([])
    from overlay_window import register_guide, resolve_image
    register_guide(load_guide())
    img = resolve_image(QUrl("qmap:5928:ini"))
    if (base_dir() / "assets" / "blizzard" / "maps" / "215.jpg").is_file():
        assert img is not None and img.width() > 500
    if (base_dir() / "assets" / "blizzard" / "icons" / "ability_racial_bearform.jpg").is_file():
        assert resolve_image(QUrl("spell:bear_form")).width() == 56   # icono real (56 px), no el SVG


@need_data
def test_select_quest_toggles(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    from overlay_window import OverlayWindow
    from state import WindowState
    w = OverlayWindow(load_guide(), WindowState(), state_file=tmp_path / "e.json",
                      progress=Progress(), progress_file=tmp_path / "p.json")
    w.go_to("misiones", "m10")
    w.select_quest(5928)
    assert w.view["quest"] == 5928 and "Gennia Runetotem" in w.browsers["misiones"].toPlainText()
    w.select_quest(5928)
    assert w.view["quest"] is None
    w.close()


def test_talent_route_matches_live_tree():
    g = load_guide()
    assert check_talent_route(g["talentos"]) == []
    tree = g["talentos"]["arboles"]["Combate feral"]
    assert tree["Shifting Power"]["prereq"] == ["Predatory Discipline", 1]
    assert tree["Primal Bite"]["prereq"] == ["Leader of the Pack", 1]
    assert "Improved Shifting Power" not in tree
