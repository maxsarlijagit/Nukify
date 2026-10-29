# S0–S8: implementación y validación 0.5

Fecha: 2026-10-27. Este estado separa entrega de código, QA local y aceptación
de producción. No se cierran todos los criterios del roadmap con fixtures sintéticas.

| Sprint | Entregado en 0.5 | Validación y criterios pendientes |
| --- | --- | --- |
| S0 | Motor incluido, app independiente, proyecto v2 con migración, autosave por sesión, recuperación manual, instalador y desinstalador. | Self-test del ejecutable: live, cache, save y export. Instalación en una segunda máquina limpia y recuperación tras fallos reales aún requieren validación externa. |
| S1 | Categorías laterales, búsqueda Tab, drag de cables, selección/movimiento, pan/zoom, copy/paste/duplicate, bypass, Dot, Backdrop, shortcuts configurables y contexto de viewer. | Prueba Qt de conexión por drag y undo, copia de subgrafos y aislamiento del foco de texto. Falta la inserción automática previsualizada sobre cables y una revisión extensa con artista. |
| S2 | OCIO configurable, display separado, Premult/Unpremult, selección de pases/canales, puente EXR aislado y conservación explícita de canales/metadata/dataWindow en Write. | Roundtrip HDR y dataWindow probado. Contrato flat single-part: no hay propagación implícita de todos los canales por todos los nodos, ni overscan externo, multipart genérico o deep. |
| S3 | Grade con gain/offset/gamma RGB, ColorCorrect por rangos, operaciones RGB, Shuffle/Copy, Merge, transform/pivote, crop/reformat y filtros. | Pruebas de valores RGB/alpha y evaluación real de nodos en Blender. Pendiente comparar todos los filtros y bordes contra tomas reales; no se promete igualdad píxel a píxel con Nuke. |
| S4 | Keyframes, constant/linear/smooth/Bézier con pendientes, tabla/curva, dope sheet, FrameHold, TimeOffset/TimeRemap y Switch. | Pruebas de interpolación, tiempo por rama y caché. Tangentes se editan numéricamente; falta manipulación directa en la curva y editor de expresiones. |
| S5 | Roto Bézier en viewer, capas planas, animación de puntos, feather/invert, combinación de máscaras, ChromaKey/LumaKey/Despill y limpieza de alpha. | Ejemplo sintético incluido. Chroma real con pelo/motion blur pendiente; no hay motion blur de roto ni grupos jerárquicos de capas. |
| S6 | Tracker 1/2 puntos, referencia, forward/backward/stop, controles LK, rechazo de pérdidas, curvas editables, matchmove/stabilize, bake y enlace a Transform/Roto. | Traslación bidireccional y pérdida verificadas; integración Qt analiza 24 cuadros. No hay re-detección automática tras oclusión ni holdout animado. |
| S7 | Homografía planar con features/LK/RANSAC, cuatro esquinas animadas y bake/enlace a CornerPin. | Fixture de perspectiva con error máximo menor a 1 px y ejemplo de 24 cuadros. Falta aprobar reemplazo de pantalla con oclusión real y estabilización planar/inversa específica. |
| S8 | AOVs por Read, selector de manifest Cryptomatte, ZDefocus/VectorBlur nativos, Grain/Regrain y export conservando capas originales. | Cryptomatte extraído de un EXR multilayer generado por Blender; export conserva los canales originales y añade Nukify.Matte. Pendientes beauty reconstruction completa, vectores/profundidad de un render real y revisión del grano por artista. |

## Evidencia local

- `validation/node-results.json`: pruebas de render del catálogo (40 nodos de imagen
  en el barrido; Read y Cryptomatte tienen pruebas específicas; Backdrop es UI).
- `tests/test_*.py`: 24 pruebas de grafo, animación, migración, UI, color y tracking.
- `validation/live-engine.json`, `validation/live-ui.json`: motor persistente y playback.
- `validation/ui-tracking.json`: análisis 2D y planar desde la interfaz Qt, 24 cuadros cada uno.
- `validation/exr/report.json`: HDR/canales/dataWindow/metadata y extracción Cryptomatte.
- `validation/source-selftest.json`: flujo integrado con tracking, crypto y Write.
- `validation/installed-selftest.json`: resultado del QA sobre la instalación final,
  cuando está presente. Sus rutas identifican el motor realmente utilizado.

Los datos de prueba están en assets/production y se generan localmente; no son tomas
de clientes. Se solicitó una carpeta de planos propios para la siguiente validación.
S9 (3D) no forma parte de esta entrega.
