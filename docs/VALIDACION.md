# Validación del contenido (15/11/2026)

Juego: World of Warcraft: Forever, lanzamiento el 4/11/2026, cliente 1.60.1, hotfixes revisados hasta el 13/11/2026.
Fuentes completas con fechas en `content/fuentes.json` (también en la pestaña **Fuentes** del overlay).

## Correcciones al borrador

| Tema | Borrador | Corregido | Fuente |
|---|---|---|---|
| Furor | Distinto árbol | En el árbol **Feral**; se intercambió con Corazón de lo Salvaje (Restauración) el 3/11 | Notas de desarrollo Blizzard |
| Mordisco primigenio / Poder cambiante | 40 y 41, sin umbral | Talentos de 31 puntos: el 40 como pronto. Se mantienen al 40 y al 41 | Blizzard + wofwforever |
| Berserk | — | **Eliminado** (3/11); su hueco lo ocupa Mordisco primigenio | Notas Blizzard |
| Furia del tigre | Implícita en rotaciones antiguas | **Eliminada**; la sustituye Poder cambiante. No aparece en ninguna rotación | Deep dive Blizzard |
| Fuego feérico feral | «puede estar eliminado» | El talento desaparece; Fuego feérico se lanza en formas sin coste (TdR 6 s) | Deep dive (sept.) |
| Presagio de claridad | — | Habilidad base al nivel 20 | Deep dive |
| Lacerar | Talento al 25 | Confirmado como talento (umbral de 16 puntos, nv 25). El deep dive de septiembre lo daba como habilidad base al 42, pero el cambio del 3/11 lo convierte en talento. Rangos en instructor: 34/42/50/58 | Notas 3/11 + wofwforever |
| Disciplina depredadora | Nv 26 | Quitada de la build híbrida: comparte hueco de 16 puntos con Lacerar. Aparece como variante «más gato» | Decisión de diseño |
| Instinto feral | 3/3 al 57–59 | Omitido: en Forever ya no da amenaza en oso | Deep dive |
| Reacción natural | 1/5 al 60 | 2/5 al 49–50 | Decisión de diseño |
| Reparto final | 0/41/10 | **Se mantiene 0/41/10 = 51** y el test lo valida nivel a nivel | `tests/test_content.py` |
| XP de mazmorras | «+50 %» | Hotfix del 8/11: del 40 % al **60 %** del valor de Classic Era | Prensa que cita a Blizzard |
| «La Ciudad Sumergida» | Mazmorra 35–40 | **The Drowned City** (Ciudad Anegada), 35–40, al oeste de Grom'gol | Blizzard (20/10) |
| «Bancal del Creador» | 58–60 | **Shaper's Terrace**, 58–60, Un'Goro; requiere cristales de poder | Blizzard |
| «Bastión Faucenegra» | 55–60 | Es **Blackmaw Hold**, 55–60, Azshara | Blizzard |
| Mazmorras nuevas no citadas | — | Añadidas: Sala de los Thanes (13–18) y Excavación (24–29, Los Humedales) | Blizzard |
| Dalaran | «verificar acceso» | Sintonización de Horda en Molino Tarren: Magus Wordeen Voidglare («Key to the City», «Prison Break-In») | Blizzard |
| «Clarofluvial» | Toponimia dudosa | Zona nueva **The Riverglades** (~35–45, 150+ misiones). La traducción oficial al español no está verificada | Blizzard |
| Legado | Desde el 25 | Primer punto normalmente al 25 (o con 150 en una profesión no recolectora, o explorando todo el mapa). 16 puntos gastables por personaje, 65 desafíos | Blizzard Legacy |
| Ventajas de Legado | 4 nombres | Confirmadas y descritas; se añade **Talented** (talentos hasta 5 niveles antes) | Blizzard Legacy |
| Especialización dual | 40–41 | Nivel 40 (coste no publicado) | Deep dive |
| Bandas | 9/12/2026 | Confirmado: Barrow Deeps (10 jugadores), Cumbre Hyjal (20), Guarida de Onyxia | Blizzard (4/11) |
| DPS del arma en formas | Pendiente | **Confirmado**: el ataque automático en forma usa el DPS del arma; los encantamientos y procs funcionan | Deep dive |
| Consumibles en forma | Pendiente | Casi todos se usan en forma; **la mayoría de bombas de Ingeniería no**. Las recetas SAF-T y EZ-Thro sí | Deep dive |
| Pisotón de guerra | — | Usable en forma | Deep dive |
| Acampadas | Efectos sin verificar | Lodestone / Rock Garden / Molten Foundry y Reagent / Repair Bot / Anarchist's Workbench confirmados con origen de los planos. El banco anarquista **no** vende reactivos | Blizzard + wow-professions |

## Sigue siendo orientativo (marcado en la app con ≈ o en ámbar)

- **Pestaña Hechizos** (v1.2): los niveles de cada rango son los del instructor de Classic, con los cambios confirmados de Forever (Revivir al 12, Garras de la naturaleza base al 10, Presagio de claridad base al 20, Lacerar como talento con rangos 34/42/50/58, Mordisco primigenio con rangos 50/60, sin Furia del tigre ni Fuego feérico feral). No se ha podido contrastar con una lista de instructor de Forever. Qué entrenar y qué ignorar es una recomendación de juego feral, no un dato.
- **Pestaña Barras**: disposición habitual de la comunidad feral, redactada como propuesta propia, no copiada de una fuente concreta.

- **Filas exactas del árbol**: Blizzard no publica una tabla en texto y el calculador de Wowhead no se pudo leer (contenido dinámico). Están confirmados los umbrales de 11, 16, 21 y 31 puntos (Carga feral, Lacerar/Disciplina, Líder de la manada, Mordisco primigenio/Poder cambiante); el resto de requisitos se deducen del orden de leveo publicado.
- **Misiones de clase** (oso 10, curar veneno 14, acuática 16, gato 20): Icy Veins devolvió 403. Se usan los nombres de Classic y se marcan como orientativos.
- **Pasiva «Poised» (nv 32)**: no aparece en ninguna fuente, así que no se muestra como hecho.
- **Valor de Robustez tauren**: no publicado.
- **Coste de la equitación y kodo gratuito**: no encontrado.
- **Habilidades de minería por veta, recetas de Ingeniería y umbrales de instructor**: valores de Classic.
- **Rangos de nivel de las mazmorras clásicas**: referencia de Classic. Los de las mazmorras nuevas son oficiales.
- **Objetos opcionales** (Serpent's Shoulders, Ghostshard Talisman, Scavenged Magram Armament, Grimlok's Charge): no se han verificado en la base de datos de Forever.
- **Nombres en español** de las mazmorras y zonas nuevas: traducción propia.

## Pruebas ejecutadas (Windows 11, monitor real al 125 %)

- `pytest`: 51 tests correctos (v1.2 añade los de hechizos y barras) (v1.1 añade los de progreso: guardado, ids únicos, capítulo actual, plegado automático, «Solo el actual», refresco del resumen e iconos). Cubren: contenido, ruta de talentos legal nivel a nivel (51 puntos, 41/10), detección de rutas ilegales, persistencia, recolocación entre monitores y ventana real (pestañas, chincheta, contraer, tamaño mínimo, restauración del estado).
- **Chincheta**: verificada con `GetWindowLongPtr` (WS_EX_TOPMOST se activa y desactiva) en Python y en el `.exe`.
- **Escalado**: 125 % real y 150 % / 200 % simulados con `QT_SCALE_FACTOR` al tamaño mínimo de 320×280. La chincheta y la cabecera se ven bien.
- **`.exe`**: abre la ventana, 0 ms de CPU en 5 s de reposo, ~33 MB de memoria privada, guarda el estado y al cerrar no deja procesos.

### No probado

- Con WoW: Forever abierto en modo ventana sin bordes (en esta sesión no se lanzó el juego). Pruébalo tú: la chincheta usa el mecanismo estándar de Windows, que funciona sobre ventanas sin bordes.
- Escalado de Windows configurado a 150 % / 200 % (solo simulado con Qt).
- Desconexión física de un segundo monitor. La lógica está cubierta por tests unitarios.
- Arrastre y redimensionado con el ratón por una persona (usan las APIs de sistema `startSystemMove` / `startSystemResize`).
