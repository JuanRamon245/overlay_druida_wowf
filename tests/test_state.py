import json

from state import MIN_H, MIN_W, WindowState, ensure_on_screen, load_state, save_state

PRIMARY = (0, 0, 1920, 1040)


def test_roundtrip(tmp_path):
    p = tmp_path / "estado.json"
    st = WindowState(x=100, y=200, w=400, h=520, pinned=False, tab="ruta", collapsed=True,
                     opacity=0.9, font_pt=11.0, scroll={"ruta": 300})
    save_state(st, p)
    back = load_state(p)
    assert back == st


def test_missing_or_corrupt_file_gives_defaults(tmp_path):
    assert load_state(tmp_path / "no.json") == WindowState()
    bad = tmp_path / "bad.json"
    bad.write_text("{no es json", encoding="utf-8")
    assert load_state(bad) == WindowState()
    bad.write_text("[1, 2]", encoding="utf-8")
    assert load_state(bad) == WindowState()


def test_values_clamped(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(json.dumps({"w": 50, "h": 10, "opacity": 0.1, "font_pt": 40, "pinned": "si", "x": True}),
                 encoding="utf-8")
    st = load_state(p)
    assert st.w == MIN_W and st.h == MIN_H
    assert st.opacity == 0.8 and st.font_pt == 13.0
    assert st.pinned is True       # valor de tipo erróneo ignorado
    assert st.x is None            # bool no cuenta como coordenada


def test_window_on_visible_monitor_kept():
    assert ensure_on_screen((1500, 80, 380, 500), [PRIMARY], PRIMARY) == (1500, 80, 380, 500)


def test_window_on_removed_second_monitor_relocated():
    # estaba en un segundo monitor a la derecha que ya no existe
    x, y, w, h = ensure_on_screen((2400, 100, 380, 500), [PRIMARY], PRIMARY)
    assert 0 <= x <= 1920 - w and 0 <= y <= 1040 - h


def test_window_on_existing_second_monitor_kept():
    screens = [PRIMARY, (1920, 0, 2560, 1400)]
    assert ensure_on_screen((2400, 100, 380, 500), screens, PRIMARY) == (2400, 100, 380, 500)


def test_header_above_screen_relocated():
    x, y, w, h = ensure_on_screen((300, -400, 380, 500), [PRIMARY], PRIMARY)
    assert y >= 0
