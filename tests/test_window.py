"""Pruebas de la ventana real. En Windows se usa la plataforma nativa para verificar
el estilo WS_EX_TOPMOST con la API del sistema."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

import winapi  # noqa: E402
from content import load_guide  # noqa: E402
from overlay_window import OverlayWindow  # noqa: E402
from state import MIN_H, MIN_W, WindowState, load_state  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def win(app, tmp_path):
    w = OverlayWindow(load_guide(), WindowState(), state_file=tmp_path / "estado.json")
    w.show()
    app.processEvents()
    yield w
    w.close()
    app.processEvents()


def test_opens_with_all_tabs(win):
    assert win.tabbar.count() == len(win.guide["tabs"]) == win.stack.count()
    for br in win.browsers.values():
        assert len(br.toPlainText()) > 200


def test_tabs_switch_without_losing_text(win, app):
    before = {k: b.toPlainText() for k, b in win.browsers.items()}
    for i in list(range(win.tabbar.count())) + [0, 3]:
        win.tabbar.setCurrentIndex(i)
        app.processEvents()
        assert win.stack.currentIndex() == i
        assert win.state.tab == win.tab_ids[i]
    assert {k: b.toPlainText() for k, b in win.browsers.items()} == before


@pytest.mark.skipif(not winapi.IS_WINDOWS, reason="solo Windows")
def test_pin_toggles_real_topmost(win, app):
    win.set_pinned(True)
    app.processEvents()
    assert win.is_on_top() and win.pin_btn.isChecked()
    win.set_pinned(False)
    app.processEvents()
    assert not win.is_on_top() and not win.pin_btn.isChecked()
    win.toggle_pin()
    assert win.is_on_top()
    geo = win.geometry()
    win.toggle_pin()
    win.toggle_pin()
    assert win.geometry() == geo   # alternar no pierde la geometría


def test_collapse_and_expand(win, app):
    h = win.height()
    win.set_collapsed(True)
    app.processEvents()
    assert win.height() < 60 and not win.body.isVisible()
    win.set_collapsed(False)
    app.processEvents()
    assert win.height() == h and win.body.isVisible()


def test_min_size(win, app):
    win.resize(100, 100)
    app.processEvents()
    assert win.width() >= MIN_W and win.height() >= MIN_H


def test_state_persisted_on_close(app, tmp_path):
    f = tmp_path / "estado.json"
    w = OverlayWindow(load_guide(), WindowState(), state_file=f)
    w.show()
    app.processEvents()
    w.set_pinned(False)
    w.tabbar.setCurrentIndex(w.tab_ids.index("talentos"))
    w.move(150, 160)
    w.resize(420, 540)
    app.processEvents()
    w.close()
    st = load_state(f)
    assert st.pinned is False and st.tab == "talentos"
    assert (st.w, st.h) == (420, 540)
    w2 = OverlayWindow(load_guide(), st, state_file=f)
    assert w2.current_tab_id() == "talentos" and w2.state.pinned is False
    w2.close()


def test_route_anchor_scrolls(win, app):
    idx = win.tab_ids.index("ruta")
    win.tabbar.setCurrentIndex(idx)
    app.processEvents()
    br = win.browsers["ruta"]
    br.scrollToAnchor("r55")
    app.processEvents()
    assert br.verticalScrollBar().value() > 0
    win.scroll_top()
    assert br.verticalScrollBar().value() == 0
