"""Parser mínimo de tablas Lua de datos (NorgannonDB). No ejecuta código: solo lee literales.

Soporta: {…}, claves `nombre=`, `[número]=`, `["texto"]=`, cadenas "…" / '…' con escapes,
cadenas largas [[…]] / [==[…]==], números, true/false/nil y referencias tipo NorgannonDB.REMOVED
(se devuelven como el texto "NorgannonDB.REMOVED").
"""
from __future__ import annotations

import re

_NUM = re.compile(r"-?(?:0x[0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_LONG_OPEN = re.compile(r"\[(=*)\[")
_KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)")
_ESC = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "\n": "\n", "a": "\a", "b": "\b",
        "f": "\f", "v": "\v"}


class LuaParseError(ValueError):
    pass


class _P:
    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def ws(self) -> None:
        s, n = self.s, len(self.s)
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n,;":
                self.i += 1
            elif s.startswith("--", self.i):
                if _LONG_OPEN.match(s, self.i + 2):
                    self.i += 2
                    self.long_string()
                else:
                    j = s.find("\n", self.i)
                    self.i = n if j < 0 else j + 1
            else:
                break

    def long_string(self) -> str:
        m = _LONG_OPEN.match(self.s, self.i)
        if not m:
            raise LuaParseError(f"cadena larga mal formada en {self.i}")
        close = "]" + m.group(1) + "]"
        start = m.end()
        if self.s.startswith("\n", start):
            start += 1
        end = self.s.find(close, start)
        if end < 0:
            raise LuaParseError("cadena larga sin cerrar")
        self.i = end + len(close)
        return self.s[start:end]

    def string(self) -> str:
        s = self.s
        q = s[self.i]
        self.i += 1
        out = []
        while True:
            c = s[self.i]
            if c == q:
                self.i += 1
                return "".join(out)
            if c == "\\":
                nxt = s[self.i + 1]
                if nxt.isdigit():
                    m = re.compile(r"\d{1,3}").match(s, self.i + 1)
                    out.append(chr(int(m.group())))
                    self.i = m.end()
                    continue
                out.append(_ESC.get(nxt, nxt))
                self.i += 2
                continue
            out.append(c)
            self.i += 1

    def value(self):
        self.ws()
        s = self.s
        c = s[self.i]
        if c == "{":
            return self.table()
        if c in "\"'":
            return self.string()
        if c == "[" and _LONG_OPEN.match(s, self.i):
            return self.long_string()
        m = _NUM.match(s, self.i)
        if m:
            self.i = m.end()
            t = m.group()
            if t.lower().lstrip("-").startswith("0x"):
                return int(t, 16)
            return float(t) if any(ch in t for ch in ".eE") else int(t)
        m = _NAME.match(s, self.i)
        if m:
            self.i = m.end()
            w = m.group()
            return {"true": True, "false": False, "nil": None}.get(w, w)
        raise LuaParseError(f"valor inesperado {s[self.i:self.i + 30]!r}")

    def table(self):
        self.i += 1  # {
        arr: list = []
        dct: dict = {}
        s = self.s
        while True:
            self.ws()
            if s[self.i] == "}":
                self.i += 1
                break
            if s[self.i] == "[" and not _LONG_OPEN.match(s, self.i):
                self.i += 1
                key = self.value()
                self.ws()
                if s[self.i] != "]":
                    raise LuaParseError("se esperaba ]")
                self.i += 1
                self.ws()
                if s[self.i] != "=":
                    raise LuaParseError("se esperaba =")
                self.i += 1
                dct[key] = self.value()
                continue
            m = _KEY.match(s, self.i)
            if m:
                self.i = m.end()
                dct[m.group(1)] = self.value()
                continue
            arr.append(self.value())
        if dct and arr:
            for k, v in enumerate(arr, 1):
                dct.setdefault(k, v)
            return dct
        return dct if dct else arr


def parse_value(text: str):
    return _P(text).value()


def parse_fields(body: str) -> dict:
    """Cuerpo de tabla sin llaves exteriores, como en R(id,"nombre",[[ … ]])."""
    v = parse_value("{" + body + "}")
    return v if isinstance(v, dict) else {}


_RECORD = re.compile(r'R\((\d+),"((?:[^"\\]|\\.)*)",\[(=*)\[(.*?)\]\3\]\)', re.S)


def iter_records(text: str):
    """Recorre los registros R(id,"nombre",[[campos]]) de un archivo empaquetado de NorgannonDB."""
    for m in _RECORD.finditer(text):
        name = _P('"' + m.group(2) + '"').string()
        yield int(m.group(1)), name, m.group(4)


def find_assignment(text: str, var: str):
    """Valor de `var = {…}` (p. ej. "NorgannonDB.zones") dentro de un archivo Lua."""
    m = re.search(re.escape(var) + r"\s*=\s*\{", text)
    if not m:
        raise LuaParseError(f"no se encontró {var}")
    p = _P(text)
    p.i = m.end() - 1
    return p.table()
