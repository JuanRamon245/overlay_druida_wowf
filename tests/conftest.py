import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(autouse=True)
def _aislar_datos_usuario(tmp_path, monkeypatch):
    """Ningún test lee ni escribe el progreso o el estado reales de %APPDATA%."""
    monkeypatch.setenv("FERAL_COMPANION_PROGRESS", str(tmp_path / "progreso_test.json"))
    monkeypatch.setenv("FERAL_COMPANION_STATE", str(tmp_path / "estado_test.json"))
