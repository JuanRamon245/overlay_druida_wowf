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

## Progreso y capítulos

- **Casillas ☐**: márcalas con un clic en los objetivos de cada capítulo de la Ruta, en los talentos (cada fila), en las mazmorras, en los hitos de Minería, Ingeniería y acampadas, en las ventajas de Legado y en la preparación del 60. Los objetivos *(opcional)* no bloquean el capítulo.
- **Capítulos plegables**: haz clic en el título de cualquier sección (▾ / ▸) para plegarla o desplegarla. Al marcar todos los objetivos obligatorios de un capítulo, este se marca ✓ COMPLETADO y se pliega solo.
- **Capítulo actual**: es el primero sin completar. Lleva la etiqueta ACTUAL y aparece en la cabecera, también con la ventana contraída a una tira.
- Botones de la Ruta: **◎ Solo el actual** (pliega el resto), **✓ Plegar hechos** y **▾ Abrir todo**.
- **Inicio → Tu progreso**: barras de capítulos, objetivos y puntos de talento, con un enlace directo al capítulo actual.
- El progreso se guarda al momento en `%APPDATA%\FeralCompanion\progreso.json`. Para empezar de cero: clic derecho en la cabecera → «Reiniciar progreso…».

El progreso lo marcas tú a mano: el overlay no lee nada del juego.

## Hechizos y barras

- **Hechizos**: una sección por cada visita al instructor (niveles pares). Cada hechizo aparece con su icono: **en color con «+1»** si conviene entrenarlo y **en gris** si puedes ignorarlo para ahorrar oro (Cólera y Fuego lunar altos, Fuego estelar, Huracán, Tranquilidad…). Marca «Entrenado» y la sección se pliega sola; «Solo el actual» funciona igual que en la Ruta. Al final, **Todos los hechizos** muestra el árbol completo con cada rango (dorado = entrenar, gris = ignorar, T = talento, M = misión) y el motivo.
- **Barras**: un preset de teclas cada 5 niveles (10, 15… 60) para **Oso, Gato, Humanoide** y las teclas comunes (formas, viaje, Marca, Renacer). En verde lo nuevo respecto al tramo anterior. El tramo ACTUAL sigue a tu capítulo de la Ruta.
- Datos en **`content/hechizos.json`**: `rangos` (nivel de cada rango), `omitir_desde` (a partir de qué nivel se deja de entrenar), `nunca`, `talento`, `origen: "mision"` y `nota`. Las barras se definen por tecla con una lista de candidatos: se usa el primero disponible a ese nivel. Si añades un hechizo, genera su icono con `python scripts/make_spell_icons.py`.

## Misiones con mapa

- Pestaña **Misiones**: las **2.527 misiones** que puede aceptar un tauren druida, agrupadas por **nivel mínimo para aceptarlas** (1–60). Cada nivel es una sección plegable; empiezan todas plegadas y el nivel ACTUAL sigue a tu capítulo de la Ruta.
- Clic en una misión: aparece el **mapa real de la zona** con **!** amarillo donde se coge y **?** azul donde se entrega, más quién la da, coordenadas, misiones previas y un enlace a Wowhead. Las misiones de clase llevan la etiqueta **[druida]**.
- Casillas ☐ para marcar las que completes (se guardan con el resto del progreso).
- Datos: [NorgannonDB](https://github.com/zmarotrix/NorgannonDB) (Forever 1.60.1, GPL-3.0). Filtro: raza tauren + clase druida; se excluyen eventos (Luna Negra, esfuerzo de guerra, invasión de la Plaga, «Craftsman's Writ», insignias).

## Recursos de Blizzard (uso personal)

Los **iconos de hechizos** y los **mapas de zona** son los reales de Blizzard, descargados del CDN de Wowhead, y las misiones salen de NorgannonDB. **No están en el repositorio** (ver `.gitignore`): se descargan en tu equipo con

```
.venv\Scripts\python scripts\fetch_blizzard_assets.py
```

(`scripts\build_windows.bat` lo hace solo; `--update` actualiza la base de datos de misiones). Se guardan en `assets/blizzard/`, `data/` y `vendor/` y se meten dentro de tu `.exe`. Si faltan, la app usa iconos propios de respaldo y la pestaña Misiones explica cómo descargarlos.

## Imágenes propias

Los iconos de pestañas y zonas y el banner son SVG propios, en `assets/icons/` y `assets/banner.svg`. Para añadir tus propias imágenes (capturas de mapas, por ejemplo), cópialas en `content/img/` y añade este bloque en `guia_es.json`:

```json
{"tipo": "imagen", "archivo": "img/mapa_baldios.png", "ancho": 300, "pie": "Ruta por Los Baldíos"}
```

Para poner un icono en el título de una sección, añade `"icono": "<nombre>"` con el nombre de un SVG de `assets/icons/`.

## Editar la guía tras un parche

Todo el texto está en **`content/guia_es.json`**. No hay que tocar código.

- Cada pestaña tiene `secciones` con `bloques` de tipo `texto`, `lista`, `tabla`, `tarjeta` o `aviso` (con `estado`: `confirmado`, `orientativo` o `pendiente`). Usa `**negrita**` para resaltar.
- Objetivos marcables: bloque `{"tipo": "checklist", "items": [{"id": "r20-algo", "texto": "…", "opcional": true}]}`. Una `tabla` con `"ids"` (uno por fila) también se puede marcar. Los `id` deben ser únicos y no conviene renombrarlos: el progreso guardado se asocia a ellos.
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
src/progress.py        objetivos marcados, plegado y capítulo actual
src/spells.py          qué entrenar en cada nivel y presets de barras
src/ui/render.py       JSON → HTML compacto · src/ui/theme.py  estilos
assets/icons/          iconos SVG propios · assets/banner.svg
content/               guía y fuentes (editables)
src/quests.py          pestaña Misiones (data/misiones_horda.json)
scripts/fetch_blizzard_assets.py  descarga iconos, mapas y NorgannonDB; build_quests.py genera las misiones
tests/                 59 tests (contenido, talentos, progreso, hechizos, misiones, estado, ventana real)
docs/VALIDACION.md     correcciones al borrador y fuentes revisadas
```

## Versión del contenido

Revisado el **15/11/2026** contra Forever 1.60.1 (hotfixes hasta el 13/11). Ver [docs/VALIDACION.md](docs/VALIDACION.md).
