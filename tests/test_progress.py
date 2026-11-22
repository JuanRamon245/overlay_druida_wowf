import pytest

from content import base_dir, load_guide
from progress import (Progress, all_check_ids, chapters, current_chapter, load_progress, save_progress,
                      section_status, summary)
from ui.render import render_tab


@pytest.fixture(scope="module")
def guide():
    return load_guide()


def test_roundtrip_and_corrupt(tmp_path):
    p = tmp_path / "progreso.json"
    pr = Progress({"r01-oso", "t10"}, {"r01"})
    save_progress(pr, p)
    assert load_progress(p) == pr
    p.write_text("no json", encoding="utf-8")
    assert load_progress(p) == Progress()
    assert load_progress(tmp_path / "nada.json") == Progress()


def test_check_ids_unique(guide):
    ids = all_check_ids(guide)
    assert len(ids) == len(set(ids))


def test_every_chapter_has_objectives(guide):
    chs = chapters(guide)
    assert len(chs) == 11
    for ch in chs:
        assert section_status(ch, set())["total"] >= 4, ch["titulo"]


def test_chapter_completion_and_current(guide):
    first, second = chapters(guide)[:2]
    assert current_chapter(guide, set()) is first
    req = {i["id"] for b in first["bloques"] if b["tipo"] == "checklist" for i in b["items"] if not i.get("opcional")}
    assert section_status(first, req)["complete"]
    assert current_chapter(guide, req) is second


def test_optional_items_do_not_block(guide):
    ch = next(c for c in chapters(guide) if c["ancla"] == "r15")
    items = [i for b in ch["bloques"] if b["tipo"] == "checklist" for i in b["items"]]
    req = {i["id"] for i in items if not i.get("opcional")}
    assert any(i.get("opcional") for i in items)
    assert section_status(ch, req)["complete"]


def test_summary_counts_talent_points(guide):
    s = summary(guide, {"t10", "t15"})     # 10–14 (5) + 15–16 (2)
    assert s["talentos"] == (7, 51)


def test_folded_section_hides_content(guide):
    ruta = next(t for t in guide["tabs"] if t["id"] == "ruta")
    open_html = render_tab(guide, ruta, Progress())
    folded_html = render_tab(guide, ruta, Progress(set(), {"r01"}))
    assert "Campamento Narache" in open_html and "Campamento Narache" not in folded_html
    assert 'href="fold:r01"' in folded_html


def test_checked_items_render_checked(guide):
    ruta = next(t for t in guide["tabs"] if t["id"] == "ruta")
    html = render_tab(guide, ruta, Progress({"r01-oso"}))
    assert 'href="check:r01-oso"><img src="icon:check_on"' in html
    assert 'href="check:r01-min"><img src="icon:check_off"' in html


def test_all_referenced_icons_exist(guide):
    icons = {"check_on", "check_off"} | {t["id"] for t in guide["tabs"]}
    for tab in guide["tabs"]:
        for sec in tab["secciones"]:
            if sec.get("icono"):
                icons.add(sec["icono"])
            for b in sec["bloques"]:
                if b["tipo"] == "imagen":
                    assert (base_dir() / b["archivo"]).is_file()
    for name in icons:
        assert (base_dir() / "assets" / "icons" / f"{name}.svg").is_file(), name


# ---------------------------------------------------------------- integración con la ventana
QtWidgets = pytest.importorskip("PySide6.QtWidgets")


@pytest.fixture
def win(tmp_path):
    from overlay_window import OverlayWindow
    from state import WindowState
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    w = OverlayWindow(load_guide(), WindowState(), state_file=tmp_path / "e.json",
                      progress=Progress(), progress_file=tmp_path / "p.json")
    w.show()
    app.processEvents()
    yield w
    w.close()


def test_click_check_saves_and_autofolds(win, tmp_path):
    from PySide6.QtCore import QUrl
    for cid in ["r01-min", "r01-ing", "r01-pico", "r01-bolsas", "r01-oso", "r01-lvl"]:
        win._on_link("ruta", QUrl("check:" + cid))
    assert "r01" in win.progress.folded
    assert win.chapter_lbl.text() == "10–15"
    saved = load_progress(tmp_path / "p.json")
    assert "r01-oso" in saved.checks and "r01" in saved.folded
    win._on_link("ruta", QUrl("check:r01-oso"))            # desmarcar
    assert "r01-oso" not in win.progress.checks
    assert win.chapter_lbl.text() == "01–10"


def test_solo_actual_and_open_all(win):
    from PySide6.QtCore import QUrl
    win._on_link("ruta", QUrl("cmd:solo-actual"))
    ids = {c["ancla"] for c in chapters(win.guide)}
    assert win.progress.folded >= ids - {"r01"} and "r01" not in win.progress.folded
    win._on_link("ruta", QUrl("cmd:desplegar"))
    assert not (win.progress.folded & ids)


def test_inicio_summary_refreshes(win):
    from PySide6.QtCore import QUrl
    win._on_link("talentos", QUrl("check:t10"))
    win.go_to("inicio")
    assert "5/51" in win.browsers["inicio"].toPlainText()


def test_icons_resolve():
    from PySide6.QtCore import QUrl
    from overlay_window import resolve_image
    assert not resolve_image(QUrl("icon:oso")).isNull()
    assert not resolve_image(QUrl("res:assets/banner.svg")).isNull()
    assert resolve_image(QUrl("icon:no_existe")) is None
