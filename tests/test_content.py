import copy

import pytest

from content import ContentError, check_talent_route, expand_route, load_guide, tree_totals, validate_guide
from ui.render import render_tab


@pytest.fixture(scope="module")
def guide():
    return load_guide()


def test_tabs_present(guide):
    ids = [t["id"] for t in guide["tabs"]]
    for needed in ("inicio", "ruta", "talentos", "combate", "mazmorras", "profesiones",
                   "equipo", "sistemas", "nivel60", "fuentes"):
        assert needed in ids


def test_talents_51_points_split_0_41_10(guide):
    tal = guide["talentos"]
    assert check_talent_route(tal) == []
    route = expand_route(tal)
    assert [e["nivel"] for e in route] == list(range(10, 61))
    assert len(route) == 51
    assert tree_totals(tal) == {"Combate feral": 41, "Restauración": 10}


def test_every_level_is_legal_when_taken(guide):
    """Repite la comprobación de legalidad para cada prefijo de la ruta (nivel a nivel)."""
    tal = guide["talentos"]
    trees = tal["arboles"]
    spent = {t: 0 for t in trees}
    ranks = {}
    for e in expand_route(tal):
        info = trees[e["arbol"]][e["talento"]]
        assert spent[e["arbol"]] >= info["req"], e
        if "prereq" in info:
            assert ranks.get(info["prereq"][0], 0) >= info["prereq"][1], e
        ranks[e["talento"]] = ranks.get(e["talento"], 0) + 1
        assert ranks[e["talento"]] <= info["max"], e
        spent[e["arbol"]] += 1


def test_gold_medal_talents_not_before_their_level(guide):
    first = {}
    for e in expand_route(guide["talentos"]):
        first.setdefault(e["talento"], e["nivel"])
    assert first["Feral Charge"] >= 20
    assert first["Lacerate"] >= 25
    assert first["Leader of the Pack"] >= 30
    assert first["Primal Bite"] >= 40 and first["Shifting Power"] >= 40


def test_illegal_route_detected(guide):
    tal = copy.deepcopy(guide["talentos"])
    tal["ruta"][0]["talento"] = "Primal Bite"   # 31 puntos al nivel 10: ilegal
    errs = check_talent_route(tal)
    assert any("Primal Bite" in e for e in errs)
    tal = copy.deepcopy(guide["talentos"])
    tal["ruta"][-1]["hasta"] = 61
    assert check_talent_route(tal)


def test_removed_abilities_not_recommended(guide):
    """Furia del tigre y Berserk no existen en Forever: solo pueden aparecer como eliminadas."""
    html = render_tab(guide, next(t for t in guide["tabs"] if t["id"] == "combate"))
    assert "Furia del tigre no existe" in html
    names = {e["talento"] for e in expand_route(guide["talentos"])}
    assert "Berserk" not in names and "Tiger's Fury" not in names


def test_all_tabs_render_and_cover_topics(guide):
    full = ""
    for tab in guide["tabs"]:
        html = render_tab(guide, tab)
        assert len(html) > 500, tab["id"]
        full += html
    for word in ("Forma de oso", "Forma felina", "Lacerar", "Minería", "Ingeniería", "55–60",
                 "Legado", "Barrow Deeps", "Rugido desmoralizador", "Mordedura feroz"):
        assert word in full, word


def test_route_index_anchors_exist(guide):
    ruta = next(t for t in guide["tabs"] if t["id"] == "ruta")
    html = render_tab(guide, ruta)
    for sec in ruta["secciones"]:
        if sec.get("ancla"):
            assert f'href="#{sec["ancla"]}"' in html and f'name="{sec["ancla"]}"' in html


def test_unknown_block_rejected(guide):
    bad = copy.deepcopy({k: v for k, v in guide.items() if not k.startswith("_")})
    bad["tabs"][0]["secciones"][0]["bloques"].append({"tipo": "checklist"})
    with pytest.raises(ContentError):
        validate_guide(bad)


def test_review_date_visible(guide):
    html = render_tab(guide, guide["tabs"][0])
    assert guide["meta"]["fecha_revision"] in html
