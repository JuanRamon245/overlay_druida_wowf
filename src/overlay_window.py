"""Ventana flotante del overlay: cabecera arrastrable, chincheta, pestañas de lectura."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCursor, QFont, QGuiApplication, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMenu, QStackedWidget, QTabBar, QTextBrowser,
                               QToolButton, QVBoxLayout, QWidget)

import winapi
from content import base_dir
from state import MIN_H, MIN_W, DEFAULT_H, DEFAULT_W, WindowState, ensure_on_screen, save_state
from ui.render import render_tab
from ui.theme import QSS

BORDER = 5          # franja para redimensionar
HEADER_H = 28


def asset(name: str) -> str:
    return str(base_dir() / "assets" / name)


class OverlayWindow(QWidget):
    def __init__(self, guide: dict, state: WindowState, state_file=None):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.guide = guide
        self.state = state
        self.state_file = state_file
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
        self.tab_ids: list[str] = []
        for tab in guide["tabs"]:
            br = QTextBrowser(self.stack)
            br.setOpenExternalLinks(True)
            br.setFrameShape(QFrame.NoFrame)
            br.setHtml(render_tab(guide, tab))
            br.verticalScrollBar().valueChanged.connect(self._update_totop)
            self.stack.addWidget(br)
            self.tabbar.addTab(tab["titulo"])
            self.browsers[tab["id"]] = br
            self.tab_ids.append(tab["id"])
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
        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addWidget(badge)
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
        return hdr

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
