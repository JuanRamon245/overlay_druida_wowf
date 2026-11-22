"""Ventana flotante del overlay: cabecera arrastrable, chincheta, pestañas de lectura."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, QUrl
from PySide6.QtCore import QRectF
from PySide6.QtGui import (QAction, QActionGroup, QColor, QCursor, QDesktopServices, QFont, QGuiApplication, QIcon,
                           QImage, QKeySequence, QPainter, QPainterPath, QPen, QShortcut, QTextDocument)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QStackedWidget, QTabBar,
                               QTextBrowser, QToolButton, QVBoxLayout, QWidget)

import winapi
from content import base_dir, content_dir
from progress import (Progress, all_chapters, chapter_label, chapters, current_chapter, load_progress, save_progress,
                      section_status)
from state import MIN_H, MIN_W, DEFAULT_H, DEFAULT_W, WindowState, ensure_on_screen, save_state
from ui.render import render_tab
from ui.theme import QSS

BORDER = 5          # franja para redimensionar
HEADER_H = 28


def asset(name: str) -> str:
    return str(base_dir() / "assets" / name)


_IMG_CACHE: dict[str, QImage] = {}


def _render_svg(path: Path, scale: int) -> QImage:
    r = QSvgRenderer(str(path))
    size = r.defaultSize()
    img = QImage(size.width() * scale, size.height() * scale, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    r.render(p)
    p.end()
    img.setDevicePixelRatio(scale)   # nítido en pantallas con escalado alto
    return img


def resolve_image(url: QUrl) -> QImage | None:
    """icon:<nombre> → assets/icons/<nombre>.svg · res:<ruta> → assets/… o content/…"""
    key = url.toString()
    if key in _IMG_CACHE:
        return _IMG_CACHE[key]
    scheme, path = url.scheme(), url.path()
    if scheme == "icon":
        file = base_dir() / "assets" / "icons" / f"{path}.svg"
        scale = 4
    elif scheme == "res":
        file = base_dir() / path if path.startswith("assets/") else content_dir() / path
        scale = 3
    elif scheme in ("spell", "spellg", "spellup"):
        file = base_dir() / "assets" / "spells" / f"{path}.svg"
        if not file.is_file():
            return None
        img = _spell_variant(_render_svg(file, 3), scheme)
        _IMG_CACHE[key] = img
        return img
    else:
        return None
    if not file.is_file():
        return None
    img = _render_svg(file, scale) if file.suffix.lower() == ".svg" else QImage(str(file))
    _IMG_CACHE[key] = img
    return img


def _spell_variant(base: QImage, scheme: str) -> QImage:
    """spell: normal · spellg: gris apagado (ignorado) · spellup: con insignia «+1» (entrenar)."""
    if scheme == "spell":
        return base
    dpr = base.devicePixelRatio()
    w, h = base.width(), base.height()
    out = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    raw = QImage(base)
    raw.setDevicePixelRatio(1.0)
    if scheme == "spellg":
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), w * 0.17, h * 0.17)
        p.setClipPath(clip)
        p.setOpacity(0.42)
        p.drawImage(0, 0, raw.convertToFormat(QImage.Format_Grayscale8))
    else:
        p.drawImage(0, 0, raw)
        bw, bh = w * 0.62, h * 0.44
        badge = QRectF(w - bw, 0, bw, bh)
        p.setPen(QPen(QColor("#ffffff"), max(1.0, w / 32)))
        p.setBrush(QColor("#2f8a33"))
        p.drawRoundedRect(badge, bh * 0.45, bh * 0.45)
        f = QFont("Segoe UI")
        f.setPixelSize(int(bh * 0.9))
        f.setBold(True)
        p.setFont(f)
        p.drawText(badge, Qt.AlignCenter, "+1")
    p.end()
    out.setDevicePixelRatio(dpr)
    return out


class GuideBrowser(QTextBrowser):
    """Visor de una pestaña: resuelve iconos/imágenes locales y no navega solo."""

    def loadResource(self, rtype, url):
        if rtype == QTextDocument.ImageResource:
            img = resolve_image(url)
            if img is not None:
                return img
        return super().loadResource(rtype, url)


class OverlayWindow(QWidget):
    def __init__(self, guide: dict, state: WindowState, state_file=None,
                 progress: Progress | None = None, progress_file=None):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.guide = guide
        self.state = state
        self.state_file = state_file
        self.progress_file = progress_file
        self.progress = progress if progress is not None else load_progress(progress_file)
        self._dirty: set[str] = set()
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowTitle("Feral Companion — Forever Overlay")
        self.setWindowIcon(QIcon(asset("icon.svg")))
        self.setMouseTracking(True)
        self.setStyleSheet(QSS)
        self._native_applied = False

        root = QVBoxLayout(self)
        root.setContentsMargins(BORDER, BORDER, BORDER, BORDER)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        self.body = QWidget(self)
        body_l = QVBoxLayout(self.body)
        body_l.setContentsMargins(0, 0, 0, 0)
        body_l.setSpacing(0)
        self.tabbar = QTabBar(self.body)
        self.tabbar.setExpanding(False)
        self.tabbar.setUsesScrollButtons(True)
        self.tabbar.setDrawBase(False)
        self.tabbar.setElideMode(Qt.ElideNone)
        self.stack = QStackedWidget(self.body)
        body_l.addWidget(self.tabbar)
        body_l.addWidget(self.stack, 1)
        root.addWidget(self.body, 1)

        self.browsers: dict[str, QTextBrowser] = {}
        self.tabs_by_id: dict[str, dict] = {}
        self.tab_ids: list[str] = []
        for tab in guide["tabs"]:
            br = GuideBrowser(self.stack)
            br.setOpenLinks(False)
            br.setFrameShape(QFrame.NoFrame)
            br.anchorClicked.connect(lambda url, tid=tab["id"]: self._on_link(tid, url))
            br.verticalScrollBar().valueChanged.connect(self._update_totop)
            self.stack.addWidget(br)
            idx = self.tabbar.addTab(tab["titulo"])
            icon_file = base_dir() / "assets" / "icons" / f"{tab['id']}.svg"
            if icon_file.is_file():
                self.tabbar.setTabIcon(idx, QIcon(str(icon_file)))
            self.browsers[tab["id"]] = br
            self.tabs_by_id[tab["id"]] = tab
            self.tab_ids.append(tab["id"])
            br.setHtml(render_tab(guide, tab, self.progress))
        self.tabbar.setIconSize(QSize(14, 14))
        self.tabbar.currentChanged.connect(self._on_tab)

        self.totop = QToolButton(self.stack)
        self.totop.setObjectName("totop")
        self.totop.setText("▲")
        self.totop.setToolTip("Volver arriba (Ctrl+Inicio)")
        self.totop.setFixedSize(26, 26)
        self.totop.clicked.connect(self.scroll_top)
        self.totop.hide()
        self.stack.installEventFilter(self)

        self._save_timer = QTimer(self, singleShot=True, interval=600, timeout=self.persist)

        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.toggle_pin)
        QShortcut(QKeySequence("Ctrl+Tab"), self, activated=lambda: self._step_tab(1))
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, activated=lambda: self._step_tab(-1))
        QShortcut(QKeySequence("Ctrl+Home"), self, activated=self.scroll_top)

        self.apply_font(state.font_pt)
        self.setWindowOpacity(state.opacity)
        self._restore_geometry()
        idx = self.tab_ids.index(state.tab) if state.tab in self.tab_ids else 0
        self.tabbar.setCurrentIndex(idx)
        self.stack.setCurrentIndex(idx)
        self._update_pin_button()
        if state.collapsed:
            self.set_collapsed(True, initial=True)

    # ------------------------------------------------------------------ construcción
    def _build_header(self) -> QWidget:
        hdr = QFrame(self)
        hdr.setObjectName("header")
        hdr.setFixedHeight(HEADER_H)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(6, 0, 3, 0)
        lay.setSpacing(4)

        icon = QLabel(hdr)
        icon.setPixmap(QIcon(asset("icon.svg")).pixmap(QSize(16, 16)))
        title = QLabel(self.guide["meta"]["titulo"], hdr)
        title.setObjectName("title")
        badge = QLabel("OSO + GATO", hdr)
        badge.setObjectName("badge")
        badge.setFixedHeight(16)
        badge.setToolTip("Feral híbrido: oso (tanque) + gato (DPS)")
        self.chapter_lbl = QLabel(hdr)
        self.chapter_lbl.setObjectName("chapter")
        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addWidget(badge)
        lay.addWidget(self.chapter_lbl)
        lay.addStretch(1)

        self.pin_btn = QToolButton(hdr)
        self.pin_btn.setObjectName("pin")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setIconSize(QSize(15, 15))
        self.pin_btn.setFocusPolicy(Qt.StrongFocus)
        self.pin_btn.clicked.connect(lambda checked: self.set_pinned(checked))

        self.collapse_btn = QToolButton(hdr)
        self.collapse_btn.setText("▾")
        self.collapse_btn.clicked.connect(lambda: self.set_collapsed(not self.state.collapsed))
        min_btn = QToolButton(hdr)
        min_btn.setText("–")
        min_btn.setToolTip("Minimizar")
        min_btn.setAccessibleName("Minimizar")
        min_btn.clicked.connect(self.showMinimized)
        close_btn = QToolButton(hdr)
        close_btn.setObjectName("close")
        close_btn.setText("✕")
        close_btn.setToolTip("Cerrar")
        close_btn.setAccessibleName("Cerrar")
        close_btn.clicked.connect(self.close)
        for b in (self.pin_btn, self.collapse_btn, min_btn, close_btn):
            lay.addWidget(b)

        self.header = hdr
        for w in (hdr, icon, title, badge):
            w.installEventFilter(self)
        hdr.setToolTip("Arrastra para mover · doble clic: contraer · clic derecho: opciones")
        self._update_collapse_button()
        self._update_chapter_label()
        return hdr

    # ------------------------------------------------------------------ progreso
    def _update_chapter_label(self) -> None:
        cur = current_chapter(self.guide, self.progress.checks)
        self.chapter_lbl.setText(chapter_label(cur))
        self.chapter_lbl.setToolTip("Capítulo actual de la ruta" if cur else "Ruta completada")

    def rerender(self, tid: str) -> None:
        br = self.browsers[tid]
        sb = br.verticalScrollBar()
        pos = sb.value()
        br.setHtml(render_tab(self.guide, self.tabs_by_id[tid], self.progress))
        sb.setValue(pos)
        QTimer.singleShot(0, lambda: sb.setValue(pos))
        self._dirty.discard(tid)

    def _progress_changed(self, tid: str) -> None:
        """Re-pinta la pestaña visible y marca las demás para re-pintarlas al abrirlas."""
        save_progress(self.progress, self.progress_file)
        self._dirty.update(self.tab_ids)
        self.rerender(tid)
        self._update_chapter_label()

    def toggle_check(self, cid: str, tid: str | None = None) -> None:
        chs = all_chapters(self.guide)
        before = {c["ancla"] for c in chs if section_status(c, self.progress.checks)["complete"]}
        self.progress.toggle_check(cid)
        for ch in chs:   # al completar un capítulo (o un nivel de instructor) se pliega solo
            if ch["ancla"] not in before and section_status(ch, self.progress.checks)["complete"]:
                self.progress.folded.add(ch["ancla"])
        self._progress_changed(tid or self.current_tab_id())

    def toggle_fold(self, sid: str, tid: str | None = None) -> None:
        self.progress.toggle_fold(sid)
        self._progress_changed(tid or self.current_tab_id())

    def run_command(self, cmd: str, tid: str = "ruta") -> None:
        chs = chapters(self.guide, tid)
        ids = [c["ancla"] for c in chs]
        cur = current_chapter(self.guide, self.progress.checks, tid)
        if cmd == "solo-actual":
            self.progress.folded.update(ids)
            if cur:
                self.progress.folded.discard(cur["ancla"])
        elif cmd == "plegar-completados":
            self.progress.folded.update(c["ancla"] for c in chs
                                        if section_status(c, self.progress.checks)["complete"])
        elif cmd == "desplegar":
            self.progress.folded.difference_update(ids)
        self._progress_changed(tid)
        if cmd == "solo-actual" and cur:
            QTimer.singleShot(0, lambda: self.browsers[tid].scrollToAnchor(cur["ancla"]))

    def go_to(self, tid: str, anchor: str = "") -> None:
        if tid in self.tab_ids:
            self.tabbar.setCurrentIndex(self.tab_ids.index(tid))
            if tid in self._dirty:
                self.rerender(tid)
            if anchor:
                self.progress.folded.discard(anchor)
                self.rerender(tid)
                QTimer.singleShot(0, lambda: self.browsers[tid].scrollToAnchor(anchor))

    def _on_link(self, tid: str, url: QUrl) -> None:
        scheme = url.scheme()
        if scheme == "check":
            self.toggle_check(url.path(), tid)
        elif scheme == "fold":
            self.toggle_fold(url.path(), tid)
        elif scheme == "cmd":
            self.run_command(url.path(), tid)
        elif scheme == "goto":
            self.go_to(url.path(), url.fragment())
        elif scheme in ("http", "https"):
            QDesktopServices.openUrl(url)   # solo si el usuario hace clic en una fuente
        elif url.hasFragment():
            self.browsers[tid].scrollToAnchor(url.fragment())

    def reset_progress(self) -> None:
        ans = QMessageBox.question(self, "Reiniciar progreso",
                                   "¿Borrar todos los objetivos marcados y las secciones plegadas?\n"
                                   "No se puede deshacer.",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.progress.checks.clear()
            self.progress.folded.clear()
            self._progress_changed(self.current_tab_id())

    # ------------------------------------------------------------------ chincheta
    def hwnd(self) -> int:
        return int(self.winId())

    def set_pinned(self, on: bool) -> None:
        self.state.pinned = bool(on)
        if winapi.IS_WINDOWS:
            winapi.set_topmost(self.hwnd(), self.state.pinned)
        else:  # otras plataformas: bandera de Qt (recrea la ventana, conserva geometría)
            geo = self.geometry()
            self.setWindowFlag(Qt.WindowStaysOnTopHint, self.state.pinned)
            self.setGeometry(geo)
            self.show()
        self._update_pin_button()
        self._schedule_save()

    def toggle_pin(self) -> None:
        self.set_pinned(not self.state.pinned)

    def is_on_top(self) -> bool:
        if winapi.IS_WINDOWS:
            return winapi.is_topmost(self.hwnd())
        return bool(self.windowFlags() & Qt.WindowStaysOnTopHint)

    def _update_pin_button(self) -> None:
        on = self.state.pinned
        self.pin_btn.setChecked(on)
        self.pin_btn.setIcon(QIcon(asset("pin_on.svg" if on else "pin_off.svg")))
        text = "Fijado: siempre visible encima (Ctrl+P para soltar)" if on else "No fijado (Ctrl+P para fijar encima)"
        self.pin_btn.setToolTip(text)
        self.pin_btn.setAccessibleName("Chincheta: " + ("fijado" if on else "no fijado"))

    # ------------------------------------------------------------------ contraer
    def set_collapsed(self, on: bool, initial: bool = False) -> None:
        self.state.collapsed = on
        if on:
            if not initial:
                self.state.h = self.height()
            self.body.hide()
            h = HEADER_H + 2 * BORDER
            self.setMinimumSize(MIN_W, h)
            self.setMaximumHeight(h)
            self.resize(self.width(), h)
        else:
            self.setMaximumHeight(16777215)
            self.setMinimumSize(MIN_W, MIN_H)
            self.body.show()
            self.resize(self.width(), max(MIN_H, self.state.h))
        self._update_collapse_button()
        self._schedule_save()

    def _update_collapse_button(self) -> None:
        on = self.state.collapsed
        self.collapse_btn.setText("▸" if on else "▾")
        tip = "Desplegar" if on else "Contraer a una tira"
        self.collapse_btn.setToolTip(tip)
        self.collapse_btn.setAccessibleName(tip)

    # ------------------------------------------------------------------ pestañas / scroll
    def current_tab_id(self) -> str:
        return self.tab_ids[self.stack.currentIndex()]

    def _on_tab(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        self.state.tab = self.tab_ids[idx]
        if self.state.tab in self._dirty:
            self.rerender(self.state.tab)
        self._update_totop()
        self._schedule_save()

    def _step_tab(self, d: int) -> None:
        self.tabbar.setCurrentIndex((self.tabbar.currentIndex() + d) % self.tabbar.count())

    def scroll_top(self) -> None:
        self.browsers[self.current_tab_id()].verticalScrollBar().setValue(0)

    def _update_totop(self, *_):
        br = self.stack.currentWidget()
        self.totop.setVisible(br is not None and br.verticalScrollBar().value() > 150)
        self._place_totop()

    def _place_totop(self) -> None:
        r = self.stack.rect()
        self.totop.move(r.right() - self.totop.width() - 14, r.bottom() - self.totop.height() - 8)
        self.totop.raise_()

    def apply_font(self, pt: float) -> None:
        self.state.font_pt = pt
        f = QFont(self.font())
        f.setPointSizeF(pt)
        for br in self.browsers.values():
            br.setFont(f)
            br.document().setDefaultFont(f)
        self._schedule_save()

    # ------------------------------------------------------------------ geometría
    def _screens(self):
        out = []
        for s in QGuiApplication.screens():
            g = s.availableGeometry()
            out.append((g.x(), g.y(), g.width(), g.height()))
        return out

    def _restore_geometry(self) -> None:
        self.setMinimumSize(MIN_W, MIN_H)
        pg = QGuiApplication.primaryScreen().availableGeometry()
        primary = (pg.x(), pg.y(), pg.width(), pg.height())
        st = self.state
        if st.x is None or st.y is None:
            x, y = pg.x() + pg.width() - st.w - 40, pg.y() + 80
        else:
            x, y = st.x, st.y
        x, y, w, h = ensure_on_screen((x, y, st.w, st.h), self._screens(), primary)
        self.setGeometry(QRect(x, y, w, h))

    def reset_geometry(self) -> None:
        pg = QGuiApplication.primaryScreen().availableGeometry()
        if self.state.collapsed:
            self.set_collapsed(False)
        self.setGeometry(QRect(pg.x() + pg.width() - DEFAULT_W - 40, pg.y() + 80, DEFAULT_W, DEFAULT_H))

    def recenter(self) -> None:
        pg = QGuiApplication.primaryScreen().availableGeometry()
        self.move(pg.x() + pg.width() - self.width() - 40, pg.y() + 80)

    # ------------------------------------------------------------------ eventos
    def showEvent(self, e):
        super().showEvent(e)
        if not self._native_applied:
            self._native_applied = True
            if winapi.IS_WINDOWS:
                winapi.set_topmost(self.hwnd(), self.state.pinned)
                winapi.set_no_activate(self.hwnd(), self.state.no_activate)
            elif self.state.pinned:
                self.set_pinned(True)
            QTimer.singleShot(60, self._restore_scroll)

    def _restore_scroll(self) -> None:
        for tid, val in self.state.scroll.items():
            if tid in self.browsers and isinstance(val, int):
                self.browsers[tid].verticalScrollBar().setValue(val)
        self._update_totop()

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "stack", None) and ev.type() == QEvent.Resize:
            self._place_totop()
        elif hasattr(self, "header") and obj in (self.header, *self.header.findChildren(QLabel)):
            t = ev.type()
            if t == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                wh = self.windowHandle()
                if wh is not None:
                    wh.startSystemMove()
                return True
            if t == QEvent.MouseButtonDblClick and ev.button() == Qt.LeftButton:
                self.set_collapsed(not self.state.collapsed)
                return True
            if t == QEvent.ContextMenu:
                self._context_menu(ev.globalPos())
                return True
        return super().eventFilter(obj, ev)

    def _edges_at(self, p: QPoint):
        edges = Qt.Edges()
        if p.x() <= BORDER:
            edges |= Qt.LeftEdge
        if p.x() >= self.width() - BORDER:
            edges |= Qt.RightEdge
        if not self.state.collapsed:
            if p.y() <= BORDER:
                edges |= Qt.TopEdge
            if p.y() >= self.height() - BORDER:
                edges |= Qt.BottomEdge
        return edges

    def mouseMoveEvent(self, e):
        edges = self._edges_at(e.position().toPoint())
        cursors = {
            Qt.LeftEdge | Qt.TopEdge: Qt.SizeFDiagCursor, Qt.RightEdge | Qt.BottomEdge: Qt.SizeFDiagCursor,
            Qt.RightEdge | Qt.TopEdge: Qt.SizeBDiagCursor, Qt.LeftEdge | Qt.BottomEdge: Qt.SizeBDiagCursor,
            Qt.LeftEdge: Qt.SizeHorCursor, Qt.RightEdge: Qt.SizeHorCursor,
            Qt.TopEdge: Qt.SizeVerCursor, Qt.BottomEdge: Qt.SizeVerCursor,
        }
        self.setCursor(cursors.get(edges, Qt.ArrowCursor))
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        edges = self._edges_at(e.position().toPoint())
        if e.button() == Qt.LeftButton and edges and self.windowHandle():
            self.windowHandle().startSystemResize(edges)
            return
        super().mousePressEvent(e)

    def leaveEvent(self, e):
        self.unsetCursor()
        super().leaveEvent(e)

    def moveEvent(self, e):
        super().moveEvent(e)
        self._schedule_save()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._schedule_save()

    def closeEvent(self, e):
        self.persist()
        save_progress(self.progress, self.progress_file)
        super().closeEvent(e)

    # ------------------------------------------------------------------ menú contextual
    def _context_menu(self, pos) -> None:
        m = QMenu(self)
        op = m.addMenu("Opacidad")
        grp = QActionGroup(op)
        for pct in (100, 95, 90, 85, 80):
            a = QAction(f"{pct} %", op, checkable=True)
            a.setChecked(abs(self.state.opacity * 100 - pct) < 1)
            a.triggered.connect(lambda _=False, v=pct / 100: self._set_opacity(v))
            grp.addAction(a)
            op.addAction(a)
        fs = m.addMenu("Tamaño de texto")
        grp2 = QActionGroup(fs)
        for label, pt in (("Pequeño", 8.5), ("Normal", 9.5), ("Grande", 11.0)):
            a = QAction(label, fs, checkable=True)
            a.setChecked(abs(self.state.font_pt - pt) < 0.1)
            a.triggered.connect(lambda _=False, v=pt: self.apply_font(v))
            grp2.addAction(a)
            fs.addAction(a)
        if winapi.IS_WINDOWS:
            na = QAction("No quitar el foco al juego al hacer clic", m, checkable=True)
            na.setChecked(self.state.no_activate)
            na.triggered.connect(self._set_no_activate)
            m.addAction(na)
        m.addSeparator()
        m.addAction("Fijar / soltar (Ctrl+P)", self.toggle_pin)
        m.addAction("Recolocar en el monitor principal", self.recenter)
        m.addAction("Restablecer tamaño y posición", self.reset_geometry)
        m.addSeparator()
        m.addAction("Reiniciar progreso…", self.reset_progress)
        m.addSeparator()
        m.addAction("Cerrar", self.close)
        m.exec(pos if pos is not None else QCursor.pos())

    def _set_opacity(self, v: float) -> None:
        self.state.opacity = v
        self.setWindowOpacity(v)
        self._schedule_save()

    def _set_no_activate(self, on: bool) -> None:
        self.state.no_activate = on
        winapi.set_no_activate(self.hwnd(), on)
        winapi.set_topmost(self.hwnd(), self.state.pinned)
        self._schedule_save()

    # ------------------------------------------------------------------ persistencia
    def _schedule_save(self) -> None:
        if hasattr(self, "_save_timer"):
            self._save_timer.start()

    def persist(self) -> None:
        if self.isMinimized():
            return
        g = self.geometry()
        self.state.x, self.state.y, self.state.w = g.x(), g.y(), g.width()
        if not self.state.collapsed:
            self.state.h = g.height()
        self.state.scroll = {tid: br.verticalScrollBar().value() for tid, br in self.browsers.items()}
        save_state(self.state, self.state_file)
