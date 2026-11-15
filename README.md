# Feral Companion — Forever Overlay

Ventanita flotante de consulta (380×500 px) con la guía de **druida tauren feral (oso + gato) 1–60** para *World of Warcraft: Forever*. Tiene pestañas de lectura y una **chincheta** que la mantiene por encima del juego. Funciona sin conexión.

No interactúa con WoW de ninguna forma: no lee memoria, archivos, pantalla ni procesos del juego, no envía teclas y no captura atajos globales. No es un addon.

## Ejecutar (Windows 10/11)

1. Abre `dist\FeralCompanion.exe`. Es portable: no necesita instalación ni permisos de administrador.
2. En WoW usa **Pantalla completa (ventana)** o **Ventana sin bordes**. En pantalla completa *exclusiva* Windows no deja que otras ventanas se pinten encima. Es una limitación del sistema y el overlay no intenta saltársela.
3. Coloca la ventanita donde no estorbe. Se quedará fijada.

Desde el código fuente: `scripts\run.bat`. Para recompilar el .exe: `scripts\build_windows.bat` (crea `.venv`, pasa los tests y genera `dist\FeralCompanion.exe`).

## Uso

| Acción | Cómo |
|---|---|
| Fijar / soltar encima | Botón de **chincheta** (dorado = fijado) o `Ctrl+P` con la ventanita enfocada |
| Mover | Arrastra la cabecera |
| Redimensionar | Arrastra cualquier borde o esquina (mínimo 320×280) |
| Contraer a una tira | Botón `▾` o doble clic en la cabecera |
| Cambiar pestaña | Clic, o `Ctrl+Tab` / `Ctrl+Shift+Tab` |
| Volver arriba | Botón `▲` o `Ctrl+Inicio` |
| Opacidad (80–100 %), tamaño de texto, recolocar | **Clic derecho en la cabecera** |
| No quitar el foco al juego | Clic derecho → «No quitar el foco al juego al hacer clic» (opcional) |

Los atajos solo funcionan con el overlay enfocado: nunca se capturan teclas globales.

El estado (posición, tamaño, chincheta, pestaña, scroll, opacidad) se guarda en `%APPDATA%\FeralCompanion\estado.json`. Si el monitor donde estaba la ventana ya no existe, al abrirla vuelve al monitor principal.

## Editar la guía tras un parche

Todo el texto está en **`content/guia_es.json`**. No hay que tocar código.

- Cada pestaña tiene `secciones` con `bloques` de tipo `texto`, `lista`, `tabla`, `tarjeta` o `aviso` (con `estado`: `confirmado`, `orientativo` o `pendiente`). Usa `**negrita**` para resaltar.
- **Talentos**: edita `talentos.ruta` (tramos `desde`/`hasta` con el talento) y, si cambia el árbol, `talentos.arboles` (`max` = rangos, `req` = puntos necesarios en el árbol, `prereq` = talento previo). La app valida la ruta al arrancar: si un talento sería ilegal a ese nivel, muestra el error en lugar de enseñar datos imposibles.
- Fuentes y fechas: `content/fuentes.json`. Fecha visible: `meta.fecha_revision`.
- Con el .exe: crea una carpeta `content` junto a `FeralCompanion.exe` con los JSON editados y se usarán en lugar de los incluidos.

Ejecuta `.venv\Scripts\python -m pytest` para comprobar que todo sigue siendo válido.

## Estructura

```
src/main.py            arranque
src/overlay_window.py  ventana, chincheta, pestañas, persistencia de geometría
src/winapi.py          SetWindowPos (siempre encima) sobre la propia ventana
src/content.py         carga JSON y validación de la ruta de talentos
src/state.py           estado en JSON + recolocación entre monitores
src/ui/render.py       JSON → HTML compacto · src/ui/theme.py  estilos
content/               guía y fuentes (editables)
tests/                 24 tests (contenido, talentos, estado, ventana real)
docs/VALIDACION.md     correcciones al borrador y fuentes revisadas
```

## Versión del contenido

Revisado el **15/11/2026** contra Forever 1.60.1 (hotfixes hasta el 13/11). Ver [docs/VALIDACION.md](docs/VALIDACION.md).
