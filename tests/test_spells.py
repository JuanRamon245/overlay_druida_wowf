import pytest

import spells
from content import base_dir, load_guide
from progress import Progress, chapters, current_chapter
from ui.render import render_tab


@pytest.fixture(scope="module")
def guide():
    return load_guide()


@pytest.fixture(scope="module")
def data(guide):
    return guide["_hechizos"]


def test_valid_and_icons_exist(data):
    assert spells.validate(data) == []
    for sid in data["hechizos"]:
        assert (base_dir() / "assets" / "spells" / f"{sid}.svg").is_file(), sid


def test_tabs_inserted_after_talents(guide):
    ids = [t["id"] for t in guide["tabs"]]
    assert ids[ids.index("talentos") + 1: ids.index("talentos") + 3] == ["hechizos", "barras"]


def test_trainer_levels_are_even(data):
    levels = spells.training_levels(data)
    assert levels[0] == 4 and levels[-1] == 60
    assert all(lv % 2 == 0 for lv in levels)


def test_removed_abilities_absent(data):
    names = {sp["en"] for sp in data["hechizos"].values()}
    assert "Tiger's Fury" not in names and "Berserk" not in names and "Faerie Fire (Feral)" not in names


def test_talent_first_rank_not_in_trainer(data):
    lv25 = [e["id"] for e in spells.training_at(data, 25)]
    assert "lacerate" not in lv25
    assert any(e["id"] == "lacerate" and e["rango"] == 2 for e in spells.training_at(data, 34))


def test_skip_rules(data):
    sp = data["hechizos"]
    assert spells.is_trained(sp["wrath"], 6) and not spells.is_trained(sp["wrath"], 14)
    assert not spells.is_trained(sp["starfire"], 20)
    assert all(spells.is_trained(sp["maul"], lv) for lv in sp["maul"]["rangos"])


def test_presets_only_use_available_spells_without_duplicates(data):
    forms = [("Comunes", data["barras"]["comunes"], 1)] + [
        (f["nombre"], f["teclas"], f["desde"]) for f in data["barras"]["formas"]]
    for lv in spells.preset_bands(data):
        for name, keys, desde in forms:
            if lv < desde:
                continue
            picks = [sid for _, sid in spells.preset(data, keys, lv) if sid]
            assert len(picks) == len(set(picks)), (name, lv)
            for sid in picks:
                sp = data["hechizos"][sid]
                assert sp["rangos"][0] <= lv and not sp.get("nunca"), (name, lv, sid)


def test_bear_bar_progression(data):
    bear = next(f for f in data["barras"]["formas"] if f["nombre"] == "Oso")
    at10 = dict(spells.preset(data, bear["teclas"], 10))
    at40 = dict(spells.preset(data, bear["teclas"], 40))
    assert at10["1"] == "maul" and at10["2"] is None
    assert at40["2"] == "lacerate" and at40["6"] == "primal_bite"


def test_render_training_has_color_and_grey(guide):
    tab = next(t for t in guide["tabs"] if t["id"] == "hechizos")
    html = render_tab(guide, tab, Progress())
    assert 'src="spellup:maul"' in html and 'src="spellg:starfire"' in html
    assert "Mordedura f." in html


def test_render_presets_all_bands(guide):
    tab = next(t for t in guide["tabs"] if t["id"] == "barras")
    html = render_tab(guide, tab, Progress())
    for lv in (10, 35, 60):
        assert f'name="b{lv}"' in html
    assert 'src="spell:shifting_power"' in html


def test_training_levels_are_chapters(guide):
    chs = chapters(guide, "hechizos")
    assert chs[0]["ancla"] == "h4"
    assert current_chapter(guide, {"h4"}, "hechizos")["ancla"] == "h6"


def test_bars_follow_route_chapter(guide):
    assert current_chapter(guide, set(), "barras")["ancla"] == "b10"
    route = chapters(guide)
    done = {i["id"] for s in route[:6] for b in s["bloques"] if b["tipo"] == "checklist"
            for i in b["items"]}
    assert current_chapter(guide, done, "barras")["ancla"] == "b35"


def test_spell_image_variants():
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.instance() or QGuiApplication([])
    from overlay_window import resolve_image
    for scheme in ("spell", "spellg", "spellup"):
        img = resolve_image(QUrl(f"{scheme}:maul"))
        assert img is not None and not img.isNull()
    assert resolve_image(QUrl("spell:no_existe")) is None
